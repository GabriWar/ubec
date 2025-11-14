import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import * as db from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;
const IS_PRODUCTION = process.env.NODE_ENV === 'production';

// Middleware
app.use(helmet({
  contentSecurityPolicy: IS_PRODUCTION ? undefined : false,
}));
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));
app.use(compression());
app.use(express.json({ limit: '10mb' }));

// Armazenamento em memória
let currentCLPData = null;
let dataHistory = [];
let alerts = [];
const MAX_HISTORY = 1000;

// Clientes SSE conectados
const sseClients = new Set();

// Servir arquivos estáticos do frontend em produção
if (IS_PRODUCTION) {
  const frontendPath = join(__dirname, '../dist');
  app.use(express.static(frontendPath));
}

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Endpoint para Node-RED enviar dados
app.post('/api/clp/telemetry', async (req, res) => {
  try {
    const data = req.body;

    // Validação básica
    if (!data.device_id || !data.timestamp) {
      return res.status(400).json({
        error: 'Dados inválidos',
        message: 'device_id e timestamp são obrigatórios'
      });
    }

    // Atualizar dados atuais
    currentCLPData = data;

    // Adicionar ao histórico em memória
    const historyEntry = {
      timestamp: data.timestamp,
      temperatures: {
        ambiente: data.sensors.temperaturas.ambiente.value,
        quadro: data.sensors.temperaturas.quadro_eletrico.value,
        modulo: data.sensors.temperaturas.modulo_fotovoltaico.value,
        trafo: data.sensors.temperaturas.transformador.value
      },
      status: data.status.operational
    };

    dataHistory.push(historyEntry);
    if (dataHistory.length > MAX_HISTORY) {
      dataHistory.shift();
    }

    // Salvar no banco de dados (async, não bloqueia resposta)
    db.insertTelemetry(data).catch(err => {
      console.error('[DB] Erro ao salvar telemetria:', err.message);
    });

    // Atualizar alertas
    if (data.alerts && data.alerts.length > 0) {
      alerts = data.alerts;
    } else {
      alerts = [];
    }

    // Enviar para todos os clientes SSE
    broadcastToSSEClients(data);

    console.log(`[${new Date().toISOString()}] Dados recebidos do CLP: ${data.device_id}`);

    res.status(201).json({
      success: true,
      message: 'Dados recebidos com sucesso',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Erro ao processar telemetria:', error);
    res.status(500).json({
      error: 'Erro interno do servidor',
      message: error.message
    });
  }
});

// Obter dados atuais
app.get('/api/clp/current', (req, res) => {
  if (!currentCLPData) {
    return res.status(404).json({
      error: 'Nenhum dado disponível',
      message: 'CLP ainda não enviou dados'
    });
  }

  res.json(currentCLPData);
});

// Obter histórico
app.get('/api/clp/history', (req, res) => {
  const { sensor, start, end, limit = 100 } = req.query;

  let filtered = [...dataHistory];

  // Filtrar por timestamp
  if (start) {
    const startTime = new Date(start).getTime();
    filtered = filtered.filter(entry => new Date(entry.timestamp).getTime() >= startTime);
  }

  if (end) {
    const endTime = new Date(end).getTime();
    filtered = filtered.filter(entry => new Date(entry.timestamp).getTime() <= endTime);
  }

  // Filtrar por sensor
  if (sensor) {
    filtered = filtered.map(entry => ({
      timestamp: entry.timestamp,
      value: entry.temperatures[sensor]
    }));
  }

  // Limitar quantidade
  const limitNum = parseInt(limit);
  if (!isNaN(limitNum) && limitNum > 0) {
    filtered = filtered.slice(-limitNum);
  }

  res.json(filtered);
});

// Obter alertas ativos
app.get('/api/clp/alerts', (req, res) => {
  res.json(alerts);
});

// Status da conexão
app.get('/api/clp/status', (req, res) => {
  const isConnected = currentCLPData !== null;
  const lastUpdate = currentCLPData ? currentCLPData.timestamp : null;

  res.json({
    connected: isConnected,
    lastUpdate,
    clientsConnected: sseClients.size,
    historyCount: dataHistory.length,
    activeAlerts: alerts.length
  });
});

// Server-Sent Events (SSE) endpoint
app.get('/api/clp/stream', (req, res) => {
  // Configurar headers SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  // Desabilitar buffering do proxy (importante para Cloudflare)
  res.setHeader('X-Accel-Buffering', 'no');

  // Adicionar cliente
  sseClients.add(res);
  console.log(`[SSE] Cliente conectado. Total: ${sseClients.size}`);

  // Enviar dados iniciais
  if (currentCLPData) {
    res.write(`data: ${JSON.stringify(currentCLPData)}\n\n`);
  }

  // Heartbeat a cada 30 segundos (importante para Cloudflare)
  const heartbeatInterval = setInterval(() => {
    res.write(':heartbeat\n\n');
  }, 30000);

  // Cleanup quando cliente desconectar
  req.on('close', () => {
    clearInterval(heartbeatInterval);
    sseClients.delete(res);
    console.log(`[SSE] Cliente desconectado. Total: ${sseClients.size}`);
  });
});

// Função para broadcast via SSE
function broadcastToSSEClients(data) {
  const message = `data: ${JSON.stringify(data)}\n\n`;

  for (const client of sseClients) {
    try {
      client.write(message);
    } catch (error) {
      console.error('Erro ao enviar para cliente SSE:', error);
      sseClients.delete(client);
    }
  }
}

// ============================================================================
// DATABASE ENDPOINTS - Alert Preferences
// ============================================================================

// Get alert preferences
app.get('/api/alerts/preferences', async (req, res) => {
  try {
    const preferences = await db.getAlertPreferences();
    res.json(preferences);
  } catch (error) {
    console.error('Erro ao buscar preferências de alertas:', error);
    res.status(500).json({ error: 'Erro ao buscar preferências de alertas' });
  }
});

// Update alert preferences for a sensor
app.put('/api/alerts/preferences/:sensor', async (req, res) => {
  try {
    const { sensor } = req.params;
    const preferences = req.body;

    const updated = await db.updateAlertPreferences(sensor, preferences);
    res.json(updated);
  } catch (error) {
    console.error('Erro ao atualizar preferências de alertas:', error);
    res.status(500).json({ error: 'Erro ao atualizar preferências de alertas' });
  }
});

// Get active alerts from database
app.get('/api/alerts/active', async (req, res) => {
  try {
    const activeAlerts = await db.getActiveAlerts();
    res.json(activeAlerts);
  } catch (error) {
    console.error('Erro ao buscar alertas ativos:', error);
    res.status(500).json({ error: 'Erro ao buscar alertas ativos' });
  }
});

// Acknowledge alert
app.post('/api/alerts/:id/acknowledge', async (req, res) => {
  try {
    const { id } = req.params;
    const acknowledged = await db.acknowledgeAlert(id);
    res.json(acknowledged);
  } catch (error) {
    console.error('Erro ao reconhecer alerta:', error);
    res.status(500).json({ error: 'Erro ao reconhecer alerta' });
  }
});

// Resolve alert
app.post('/api/alerts/:id/resolve', async (req, res) => {
  try {
    const { id } = req.params;
    const resolved = await db.resolveAlert(id);
    res.json(resolved);
  } catch (error) {
    console.error('Erro ao resolver alerta:', error);
    res.status(500).json({ error: 'Erro ao resolver alerta' });
  }
});

// ============================================================================
// DATABASE ENDPOINTS - Temperature Stats
// ============================================================================

// Get temperature statistics (24h)
app.get('/api/stats/temperature', async (req, res) => {
  try {
    const stats = await db.getTemperatureStats();
    res.json(stats);
  } catch (error) {
    console.error('Erro ao buscar estatísticas de temperatura:', error);
    res.status(500).json({ error: 'Erro ao buscar estatísticas' });
  }
});

// ============================================================================
// DATABASE ENDPOINTS - User Preferences
// ============================================================================

// Get user preference
app.get('/api/preferences/:key', async (req, res) => {
  try {
    const { key } = req.params;
    const value = await db.getUserPreference(key);

    if (!value) {
      return res.status(404).json({ error: 'Preferência não encontrada' });
    }

    res.json({ key, value });
  } catch (error) {
    console.error('Erro ao buscar preferência:', error);
    res.status(500).json({ error: 'Erro ao buscar preferência' });
  }
});

// Set user preference
app.post('/api/preferences/:key', async (req, res) => {
  try {
    const { key } = req.params;
    const { value } = req.body;

    const updated = await db.setUserPreference(key, value);
    res.json(updated);
  } catch (error) {
    console.error('Erro ao salvar preferência:', error);
    res.status(500).json({ error: 'Erro ao salvar preferência' });
  }
});

// ============================================================================
// INVERTER ENDPOINTS
// ============================================================================

// Receive inverter telemetry from Python service
app.post('/api/inverter/telemetry', async (req, res) => {
  try {
    const data = req.body;

    // Validation
    if (!data.device_id || !data.timestamp) {
      return res.status(400).json({
        error: 'Dados inválidos',
        message: 'device_id e timestamp são obrigatórios'
      });
    }

    // Save to database (async)
    db.insertInverterTelemetry(data).catch(err => {
      console.error('[DB] Erro ao salvar telemetria do inversor:', err.message);
    });

    // Broadcast via SSE
    broadcastToSSEClients({
      type: 'inverter',
      data: data
    });

    console.log(`[${new Date().toISOString()}] Inverter data received: ${data.device_id}`);

    res.status(201).json({
      success: true,
      message: 'Dados do inversor recebidos com sucesso',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Erro ao processar telemetria do inversor:', error);
    res.status(500).json({
      error: 'Erro interno do servidor',
      message: error.message
    });
  }
});

// Get latest inverter data
app.get('/api/inverter/current', async (req, res) => {
  try {
    const { device_id } = req.query;
    const data = await db.getLatestInverterData(device_id || null);

    if (!data || (Array.isArray(data) && data.length === 0)) {
      return res.status(404).json({
        error: 'Nenhum dado disponível',
        message: 'Inversor ainda não enviou dados'
      });
    }

    res.json(data);
  } catch (error) {
    console.error('Erro ao buscar dados atuais do inversor:', error);
    res.status(500).json({ error: 'Erro ao buscar dados do inversor' });
  }
});

// Get inverter hourly statistics
app.get('/api/inverter/stats/hourly', async (req, res) => {
  try {
    const { device_id, hours = 24 } = req.query;
    const stats = await db.getInverterHourlyStats(device_id || null, parseInt(hours));

    res.json(stats);
  } catch (error) {
    console.error('Erro ao buscar estatísticas horárias:', error);
    res.status(500).json({ error: 'Erro ao buscar estatísticas' });
  }
});

// Get inverter daily statistics
app.get('/api/inverter/stats/daily', async (req, res) => {
  try {
    const { device_id, days = 30 } = req.query;
    const stats = await db.getInverterDailyStats(device_id || null, parseInt(days));

    res.json(stats);
  } catch (error) {
    console.error('Erro ao buscar estatísticas diárias:', error);
    res.status(500).json({ error: 'Erro ao buscar estatísticas' });
  }
});

// Get all active inverters
app.get('/api/inverter/devices', async (req, res) => {
  try {
    const devices = await db.getActiveInverters();
    res.json(devices);
  } catch (error) {
    console.error('Erro ao buscar inversores:', error);
    res.status(500).json({ error: 'Erro ao buscar inversores' });
  }
});

// Register or update inverter device
app.post('/api/inverter/device', async (req, res) => {
  try {
    const deviceInfo = req.body;

    if (!deviceInfo.device_id) {
      return res.status(400).json({
        error: 'Dados inválidos',
        message: 'device_id é obrigatório'
      });
    }

    const device = await db.upsertInverterDevice(deviceInfo);
    res.json(device);
  } catch (error) {
    console.error('Erro ao registrar inversor:', error);
    res.status(500).json({ error: 'Erro ao registrar inversor' });
  }
});

// SPA fallback - servir index.html para todas as rotas não-API (produção)
if (IS_PRODUCTION) {
  app.get('*', (req, res) => {
    res.sendFile(join(__dirname, '../dist/index.html'));
  });
}

// Limpar histórico antigo (manter apenas últimas 24h)
setInterval(() => {
  const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
  dataHistory = dataHistory.filter(entry =>
    new Date(entry.timestamp).getTime() > oneDayAgo
  );
}, 60 * 60 * 1000); // Rodar a cada 1 hora

// Tratamento de erros global
app.use((err, req, res, next) => {
  console.error('Erro não tratado:', err);
  res.status(500).json({
    error: 'Erro interno do servidor',
    message: IS_PRODUCTION ? 'Erro desconhecido' : err.message
  });
});

// Iniciar servidor
async function startServer() {
  // Test database connection
  const dbConnected = await db.testConnection();

  if (!dbConnected) {
    console.error('[ERRO] Não foi possível conectar ao banco de dados');
    console.log('[INFO] Servidor continuará em modo somente memória');
  }

  // Start cleanup interval (runs every 24h)
  if (dbConnected) {
    setInterval(async () => {
      try {
        await db.cleanupOldTelemetry();
      } catch (error) {
        console.error('[DB] Erro ao limpar dados antigos:', error.message);
      }
    }, 24 * 60 * 60 * 1000);
  }

  app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════╗
║   MTZ View - Sistema Supervisório         ║
║   Servidor rodando na porta ${PORT}          ║
║   Ambiente: ${IS_PRODUCTION ? 'PRODUCTION' : 'DEVELOPMENT'}             ║
║   Database: ${dbConnected ? 'CONNECTED ✓' : 'DISCONNECTED ✗'}                  ║
║                                            ║
║   Endpoints API:                           ║
║   - POST /api/clp/telemetry               ║
║   - GET  /api/clp/current                 ║
║   - GET  /api/clp/history                 ║
║   - GET  /api/clp/alerts                  ║
║   - GET  /api/clp/status                  ║
║   - GET  /api/clp/stream (SSE)            ║
║   - GET  /health                          ║
║                                            ║
║   Database Endpoints:                      ║
║   - GET  /api/alerts/preferences          ║
║   - PUT  /api/alerts/preferences/:sensor  ║
║   - GET  /api/alerts/active               ║
║   - GET  /api/stats/temperature           ║
║   - GET  /api/preferences/:key            ║
║   - POST /api/preferences/:key            ║
║                                            ║
║   Inverter Endpoints:                      ║
║   - POST /api/inverter/telemetry          ║
║   - GET  /api/inverter/current            ║
║   - GET  /api/inverter/stats/hourly       ║
║   - GET  /api/inverter/stats/daily        ║
║   - GET  /api/inverter/devices            ║
║   - POST /api/inverter/device             ║
║                                            ║
║   ${IS_PRODUCTION ? 'Frontend: http://localhost:' + PORT : 'Dev: Frontend separado'}        ║
╚════════════════════════════════════════════╝
    `);
  });
}

// Graceful shutdown
async function shutdown() {
  console.log('\n[SHUTDOWN] Fechando servidor...');

  // Close database connection
  await db.closePool();

  console.log('[SHUTDOWN] Servidor fechado');
  process.exit(0);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Start the server
startServer().catch(err => {
  console.error('[ERRO] Falha ao iniciar servidor:', err);
  process.exit(1);
});
