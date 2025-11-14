import { useCLP } from '../../contexts/CLPContext';
import { Card } from '../Common/Card';
import { ThemeToggle } from '../Common/ThemeToggle';
import { TemperatureDisplay } from './TemperatureDisplay';
import { StatusIndicator } from './StatusIndicator';
import { AlertsList } from './AlertsList';
import './QuadroGeracao.css';

export function QuadroGeracao() {
  const { data, isConnected, lastUpdate } = useCLP();

  // Dados padrão quando ainda não há dados do CLP
  const defaultData = {
    sensors: {
      temperaturas: {
        ambiente: { value: 0, unit: 'celsius', sensor_type: 'PT100', address: '%MW36' },
        quadro_eletrico: { value: 0, unit: 'celsius', sensor_type: 'PT100', address: '%MW38' },
        modulo_fotovoltaico: { value: 0, unit: 'celsius', sensor_type: 'PT100', address: '%MW40' },
        transformador: { value: 0, unit: 'celsius', sensor_type: 'PT100', address: '%MW42' }
      }
    },
    status: {
      operational: {
        comunicacao_ok: false,
        sistema_ativo: false,
        em_falha: false,
        alarme_ativo: false,
        emergencia_ativa: false
      },
      electrical: {
        disjuntor_geral_status: 'ABERTO' as const,
        servico_auxiliar_ok: false
      },
      outputs: {
        reset_rasp: false,
        reset_link_3g: false,
        comunicacao_ok: false,
        usina_gerando: false,
        falha: false,
        alarme: false,
        emergencia_inversores: false,
        reserva_1: false,
        reserva_2: false,
        reserva_3: false
      },
      inputs: {
        dj_geral_fechado: false
      }
    },
    alerts: []
  };

  const { sensors, status, alerts } = data || defaultData;

  return (
    <div className="quadro-geracao">
      <div className="quadro-header">
        <h1>Quadro de Geração Solar</h1>
        <div className="header-controls">
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
            <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
            {lastUpdate && <span className="last-update">Última atualização: {new Date(lastUpdate).toLocaleTimeString('pt-BR')}</span>}
          </div>
          <ThemeToggle />
        </div>
      </div>

      <div className="quadro-grid">
        {/* Status Operacional */}
        <Card title="Status Operacional" className="status-card">
          <div className="status-grid">
            <StatusIndicator
              label="Comunicação"
              active={status.operational.comunicacao_ok}
              type="success"
            />
            <StatusIndicator
              label="Sistema Ativo"
              active={status.operational.sistema_ativo}
              type="info"
            />
            <StatusIndicator
              label="Falha"
              active={status.operational.em_falha}
              type="danger"
            />
            <StatusIndicator
              label="Alarme"
              active={status.operational.alarme_ativo}
              type="warning"
            />
            <StatusIndicator
              label="Emergência"
              active={status.operational.emergencia_ativa}
              type="danger"
            />
            <StatusIndicator
              label="Serviço Auxiliar"
              active={status.electrical.servico_auxiliar_ok}
              type="success"
            />
          </div>
        </Card>

        {/* Temperaturas */}
        <Card title="Monitoramento de Temperatura" className="temp-card">
          <div className="temp-grid">
            <TemperatureDisplay
              label="Ambiente"
              temperature={sensors.temperaturas.ambiente}
              warning={35}
              critical={40}
            />
            <TemperatureDisplay
              label="Quadro Elétrico"
              temperature={sensors.temperaturas.quadro_eletrico}
              warning={50}
              critical={60}
            />
            <TemperatureDisplay
              label="Módulo Fotovoltaico"
              temperature={sensors.temperaturas.modulo_fotovoltaico}
              warning={70}
              critical={80}
            />
            <TemperatureDisplay
              label="Transformador"
              temperature={sensors.temperaturas.transformador}
              warning={75}
              critical={85}
            />
          </div>
        </Card>

        {/* Disjuntor */}
        <Card title="Disjuntor Geral" className="disjuntor-card">
          <div className="disjuntor-display">
            <div className={`disjuntor-status ${status.electrical.disjuntor_geral_status.toLowerCase()}`}>
              <div className="disjuntor-icon">
                {status.electrical.disjuntor_geral_status === 'FECHADO' ? '⚡' : '⭘'}
              </div>
              <span className="disjuntor-label">{status.electrical.disjuntor_geral_status}</span>
            </div>
          </div>
        </Card>

        {/* Alertas */}
        {alerts.length > 0 && (
          <Card title="Alertas Ativos" className="alerts-card">
            <AlertsList alerts={alerts} />
          </Card>
        )}

        {/* Saídas Digitais */}
        <Card title="Saídas Digitais" className="outputs-card">
          <div className="outputs-grid">
            <StatusIndicator label="Reset RASP" active={status.outputs.reset_rasp} type="info" />
            <StatusIndicator label="Reset Link 3G" active={status.outputs.reset_link_3g} type="info" />
          </div>
        </Card>
      </div>
    </div>
  );
}
