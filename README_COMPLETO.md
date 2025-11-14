# MTZ View - Sistema Supervisório Industrial

Sistema de supervisório web completo para monitoramento em tempo real de CLP Schneider TM200CE24R.

## Arquitetura do Sistema

```
┌──────────────┐   Modbus TCP    ┌──────────────┐   HTTP POST   ┌──────────────┐
│     CLP      │ ◄────────────── │  Node-RED    │ ────────────► │   Backend    │
│  Schneider   │                 │              │               │   Express    │
│  TM200CE24R  │                 └──────────────┘               │   + SSE      │
└──────────────┘                                                └──────┬───────┘
                                                                       │
                                                                       │ SSE Stream
                                                                       │
                                                                ┌──────▼───────┐
                                                                │   Frontend   │
                                                                │  React + TS  │
                                                                └──────────────┘
```

## Características

- Real-time via Server-Sent Events (SSE)
- Compatível com Cloudflare Tunnel
- Interface responsiva e moderna
- Alertas visuais e sonoros
- Histórico de dados (24h)
- Modular e extensível
- TypeScript para type-safety
- Backend e Frontend integrados

## Estrutura do Projeto

```
mtzview/
├── backend/                           # Backend Node.js
│   ├── server.js                      # Servidor Express + SSE
│   └── package.json
│
├── src/
│   ├── components/
│   │   ├── Common/                    # Componentes reutilizáveis
│   │   │   ├── Card.tsx
│   │   │   └── Card.css
│   │   │
│   │   └── Supervisorio/              # Componentes específicos
│   │       ├── QuadroGeracao.tsx      # Componente principal
│   │       ├── TemperatureDisplay.tsx
│   │       ├── StatusIndicator.tsx
│   │       └── AlertsList.tsx
│   │
│   ├── contexts/                      # React Context
│   │   └── CLPContext.tsx
│   │
│   ├── services/                      # Serviços de comunicação
│   │   ├── api.service.ts            # HTTP REST API
│   │   └── sse.service.ts            # Server-Sent Events
│   │
│   ├── types/                         # TypeScript Types
│   │   └── clp.types.ts
│   │
│   ├── App.tsx
│   └── main.tsx
│
└── package.json
```

## Instalação

### 1. Instalar dependências

```bash
cd /home/gabriel/Downloads/mtzview

# Instalar frontend
npm install

# Instalar backend
cd backend
npm install
cd ..
```

## Desenvolvimento

### Iniciar em modo desenvolvimento

```bash
# Terminal 1 - Frontend (Vite)
npm run dev

# Terminal 2 - Backend (Express)
npm run dev:backend

# OU iniciar ambos simultaneamente
npm run dev:all
```

Acesse:
- Frontend: http://localhost:5173
- Backend API: http://localhost:3001
- Health check: http://localhost:3001/health

## Produção

### Build do projeto

```bash
# Build completo (frontend + backend)
npm run build:all
```

Isso irá:
1. Compilar TypeScript
2. Build do Vite (gera pasta `dist/`)
3. Instalar dependências do backend

### Iniciar em produção

```bash
npm start
```

O backend irá:
- Servir arquivos estáticos do frontend
- Expor API REST
- Fornecer SSE para tempo real

Acesse: http://localhost:3001

## Configuração

### Backend

Variáveis de ambiente (opcional):

```bash
PORT=3001
NODE_ENV=production
CORS_ORIGIN=*
```

### Frontend

Crie `.env` (desenvolvimento):

```env
VITE_API_URL=http://localhost:3001/api
VITE_SSE_URL=http://localhost:3001/api/clp/stream
```

Para produção, como backend e frontend estão juntos, as URLs relativas funcionam automaticamente.

## Node-RED

### Importar flow

1. Abra Node-RED: http://localhost:1880
2. Menu → Import
3. Cole o conteúdo de: `/home/gabriel/Downloads/PROJETO2/nodered-clp-api-corrigido.json`
4. Deploy

### Configurar

No flow importado:

1. **Modbus Client**:
   - IP: `192.168.10.1`
   - Port: `502`
   - Unit ID: `1`

2. **HTTP Request** (POST para API):
   - URL: `http://localhost:3001/api/clp/telemetry`
   - Method: POST

3. **Inject nodes**:
   - Ciclo: 30 segundos (ajustável)

## API Endpoints

### POST /api/clp/telemetry
Recebe dados do Node-RED

**Request Body:**
```json
{
  "device_id": "CLP_SCHNEIDER_TM200CE24R",
  "timestamp": "2025-11-14T10:30:00.000Z",
  "location": {
    "site": "Usina Solar",
    "installation": "UBEC Automação"
  },
  "sensors": {
    "temperaturas": {
      "ambiente": {
        "value": 25.3,
        "unit": "celsius",
        "sensor_type": "PT100",
        "address": "%MW36"
      },
      ...
    }
  },
  "status": {
    "operational": { ... },
    "electrical": { ... }
  },
  "alerts": [ ... ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dados recebidos com sucesso",
  "timestamp": "2025-11-14T10:30:00.123Z"
}
```

### GET /api/clp/current
Retorna dados atuais do CLP

**Response:** Mesmo formato do POST acima

### GET /api/clp/history
Histórico de dados

**Query Parameters:**
- `sensor`: `ambiente | quadro | modulo | trafo`
- `start`: ISO timestamp
- `end`: ISO timestamp
- `limit`: número (default: 100)

**Response:**
```json
[
  {
    "timestamp": "2025-11-14T10:00:00.000Z",
    "temperatures": {
      "ambiente": 25.3,
      "quadro": 32.1,
      "modulo": 45.2,
      "trafo": 58.7
    }
  },
  ...
]
```

### GET /api/clp/alerts
Alertas ativos

**Response:**
```json
[
  {
    "type": "TEMPERATURE_HIGH",
    "severity": "high",
    "message": "Temperatura do transformador alta: 85°C",
    "timestamp": "2025-11-14T10:30:00.000Z"
  }
]
```

### GET /api/clp/status
Status da conexão

**Response:**
```json
{
  "connected": true,
  "lastUpdate": "2025-11-14T10:30:00.000Z",
  "clientsConnected": 3,
  "historyCount": 720,
  "activeAlerts": 1
}
```

### GET /api/clp/stream
Server-Sent Events para dados em tempo real

**Headers:**
```
Content-Type: text/event-stream
```

**Event data:** Mesmo formato do GET /api/clp/current

### GET /health
Health check

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-14T10:30:00.000Z",
  "uptime": 3600,
  "memory": { ... },
  "environment": "production"
}
```

## Componentes React

### QuadroGeracao
Componente principal do supervisório

**Features:**
- Grid responsivo
- Status operacional em tempo real
- 4 displays de temperatura
- Indicador de disjuntor
- Lista de alertas
- Status de conexão

### TemperatureDisplay
Display individual de temperatura

**Props:**
```typescript
{
  label: string;
  temperature: Temperature;
  warning?: number;    // Threshold de alerta (default: 60)
  critical?: number;   // Threshold crítico (default: 80)
}
```

**Features:**
- Valor em tempo real
- Barra de progresso
- Código de cores (normal/warning/critical)
- Animação de pulse em estado crítico
- Thresholds configuráveis

### StatusIndicator
Indicador LED de status

**Props:**
```typescript
{
  label: string;
  active: boolean;
  type?: 'success' | 'danger' | 'warning' | 'info';
  size?: 'small' | 'medium' | 'large';
}
```

**Features:**
- Estados on/off
- Glow effect
- Pulse animation
- 4 variantes de cor

### AlertsList
Lista de alertas

**Props:**
```typescript
{
  alerts: Alert[];
}
```

**Features:**
- Ordenação por severidade
- Ícones por tipo
- Badges de severidade
- Animação em alertas críticos

## Cloudflare Tunnel

### Setup

```bash
# Instalar Cloudflare Tunnel
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login
cloudflared tunnel login

# Criar tunnel
cloudflared tunnel create mtzview

# Configurar DNS
cloudflared tunnel route dns mtzview mtzview.your-domain.com
```

### Configuração (`~/.cloudflared/config.yml`)

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/gabriel/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: mtzview.your-domain.com
    service: http://localhost:3001
  - service: http_status:404
```

### Iniciar

```bash
cloudflared tunnel run mtzview
```

## Systemd Service (Produção)

### Backend + Frontend

```bash
sudo nano /etc/systemd/system/mtzview.service
```

```ini
[Unit]
Description=MTZ View Supervisorio
After=network.target

[Service]
Type=simple
User=gabriel
WorkingDirectory=/home/gabriel/Downloads/mtzview
Environment="NODE_ENV=production"
Environment="PORT=3001"
ExecStart=/usr/bin/node backend/server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Node-RED

```ini
[Unit]
Description=Node-RED
After=syslog.target network.target

[Service]
Type=simple
User=gabriel
ExecStart=/usr/bin/node-red
Restart=always

[Install]
WantedBy=multi-user.target
```

### Ativar services

```bash
sudo systemctl daemon-reload
sudo systemctl enable mtzview
sudo systemctl enable node-red
sudo systemctl start mtzview
sudo systemctl start node-red
```

## Monitoramento

### Logs

```bash
# MTZ View
journalctl -u mtzview -f

# Node-RED
journalctl -u node-red -f
```

### Status

```bash
systemctl status mtzview
systemctl status node-red
```

## Desenvolvimento

### Adicionar novo componente

```bash
# Criar arquivos
mkdir src/components/MeuComponente
touch src/components/MeuComponente/MeuComponente.tsx
touch src/components/MeuComponente/MeuComponente.css
```

```typescript
// MeuComponente.tsx
import './MeuComponente.css';

interface MeuComponenteProps {
  prop1: string;
}

export function MeuComponente({ prop1 }: MeuComponenteProps) {
  return (
    <div className="meu-componente">
      {prop1}
    </div>
  );
}
```

### Adicionar novo tipo

```typescript
// src/types/meu-tipo.types.ts
export interface MeuTipo {
  campo1: string;
  campo2: number;
}
```

### Adicionar novo serviço

```typescript
// src/services/meu-servico.service.ts
class MeuServico {
  async fetchData() {
    const response = await fetch('/api/endpoint');
    return response.json();
  }
}

export const meuServico = new MeuServico();
```

## Troubleshooting

### Frontend não conecta ao backend

```bash
# Verificar backend
curl http://localhost:3001/health

# Verificar CORS
curl -H "Origin: http://localhost:5173" http://localhost:3001/api/clp/current

# Logs do backend
npm run dev:backend
```

### SSE não recebe dados

```bash
# Testar SSE manualmente
curl -N http://localhost:3001/api/clp/stream

# Verificar se Node-RED está enviando dados
# Veja debug nodes no Node-RED
```

### Node-RED não envia dados

1. Verificar conexão Modbus com CLP
2. Verificar IP do CLP (192.168.10.1)
3. Verificar flow está deployed
4. Verificar nó HTTP Request URL

### Build falha

```bash
# Limpar cache
rm -rf node_modules dist backend/node_modules
npm install
cd backend && npm install && cd ..

# Build novamente
npm run build:all
```

## Performance

- SSE heartbeat: 30s (otimizado para Cloudflare)
- Histórico: últimas 1000 entradas (24h)
- Compressão HTTP habilitada
- CSS com animações GPU
- Lazy loading de componentes (preparado)

## Segurança

- Helmet.js headers
- CORS configurável
- Input validation
- Error handling
- Rate limiting (pode adicionar)

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- CSS Modules

### Backend
- Node.js 18+
- Express
- Server-Sent Events
- Helmet
- Compression

### Integrações
- Node-RED
- Modbus TCP
- Schneider TM200CE24R

## Licença

Propriedade de UBEC Automação

## Contato

Para suporte, entre em contato.
