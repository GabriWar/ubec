import './StatusIndicator.css';

interface StatusIndicatorProps {
  label: string;
  active: boolean;
  type?: 'success' | 'danger' | 'warning' | 'info';
  size?: 'small' | 'medium' | 'large';
}

export function StatusIndicator({
  label,
  active,
  type = 'info',
  size = 'medium'
}: StatusIndicatorProps) {
  return (
    <div className={`status-indicator ${size} ${active ? 'active' : 'inactive'}`}>
      <div className={`status-led ${type} ${active ? 'on' : 'off'}`}>
        <div className="led-glow" />
        <div className="led-core" />
      </div>
      <span className="status-label">{label}</span>
    </div>
  );
}
