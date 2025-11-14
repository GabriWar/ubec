import type { Alert } from '../../types/clp.types';
import './AlertsList.css';

interface AlertsListProps {
  alerts: Alert[];
}

const severityConfig = {
  low: { icon: 'ℹ️', color: '#3b82f6', label: 'Informação' },
  medium: { icon: '⚠️', color: '#f59e0b', label: 'Atenção' },
  high: { icon: '🔴', color: '#ef4444', label: 'Alto' },
  critical: { icon: '🚨', color: '#dc2626', label: 'Crítico' }
};

export function AlertsList({ alerts }: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <div className="alerts-empty">
        <span className="empty-icon">✓</span>
        <p>Nenhum alerta ativo</p>
      </div>
    );
  }

  const sortedAlerts = [...alerts].sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });

  return (
    <div className="alerts-list">
      {sortedAlerts.map((alert, index) => {
        const config = severityConfig[alert.severity];
        return (
          <div
            key={index}
            className={`alert-item severity-${alert.severity}`}
            style={{ borderLeftColor: config.color }}
          >
            <div className="alert-icon">{config.icon}</div>
            <div className="alert-content">
              <div className="alert-header">
                <span className="alert-type">{alert.type.replace(/_/g, ' ')}</span>
                <span className="alert-severity" style={{ backgroundColor: config.color }}>
                  {config.label}
                </span>
              </div>
              <p className="alert-message">{alert.message}</p>
              <span className="alert-timestamp">
                {new Date(alert.timestamp).toLocaleString('pt-BR')}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
