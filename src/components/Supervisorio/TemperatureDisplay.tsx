import { useMemo } from 'react';
import type { Temperature } from '../../types/clp.types';
import './TemperatureDisplay.css';

interface TemperatureDisplayProps {
  label: string;
  temperature: Temperature;
  warning?: number;
  critical?: number;
}

export function TemperatureDisplay({
  label,
  temperature,
  warning = 60,
  critical = 80
}: TemperatureDisplayProps) {
  const status = useMemo(() => {
    if (temperature.value >= critical) return 'critical';
    if (temperature.value >= warning) return 'warning';
    return 'normal';
  }, [temperature.value, warning, critical]);

  const percentage = useMemo(() => {
    const max = critical + 20;
    return Math.min((temperature.value / max) * 100, 100);
  }, [temperature.value, critical]);

  return (
    <div className={`temperature-display ${status}`}>
      <div className="temp-header">
        <span className="temp-label">{label}</span>
        <span className="temp-sensor">{temperature.sensor_type}</span>
      </div>

      <div className="temp-value">
        <span className="temp-number">{temperature.value.toFixed(1)}</span>
        <span className="temp-unit">{temperature.unit}</span>
      </div>

      <div className="temp-bar">
        <div
          className={`temp-bar-fill ${status}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="temp-footer">
        <span className="temp-address">{temperature.address}</span>
        <div className="temp-thresholds">
          <span className="threshold warning">⚠ {warning}°C</span>
          <span className="threshold critical">🔥 {critical}°C</span>
        </div>
      </div>
    </div>
  );
}
