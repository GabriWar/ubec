-- MTZ View Database Schema
-- Database: mtzview
-- Description: Stores historical telemetry data and alert preferences

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Alert Level Types
-- HH: Level High-High (Nível Muito Alto) - Crítico
-- H: Level High (Nível Alto) - Aviso
-- L: Level Low (Nível Baixo) - Aviso
-- LL: Level Low-Low (Nível Muito Baixo) - Crítico
CREATE TYPE alert_level AS ENUM ('HH', 'H', 'L', 'LL');

-- Alert severity
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'critical');

-- ============================================================================
-- TELEMETRY HISTORY
-- ============================================================================

-- Main telemetry table - stores all historical data from CLP
CREATE TABLE telemetry_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Temperature sensors (PT100)
    temp_ambiente DECIMAL(5,2),
    temp_quadro_eletrico DECIMAL(5,2),
    temp_modulo_fotovoltaico DECIMAL(5,2),
    temp_transformador DECIMAL(5,2),

    -- Operational status
    comunicacao_ok BOOLEAN,
    sistema_ativo BOOLEAN,
    em_falha BOOLEAN,
    alarme_ativo BOOLEAN,
    emergencia_ativa BOOLEAN,

    -- Electrical status
    disjuntor_geral_status VARCHAR(10),
    servico_auxiliar_ok BOOLEAN,

    -- Digital outputs
    reset_rasp BOOLEAN,
    reset_link_3g BOOLEAN,
    usina_gerando BOOLEAN,

    -- Digital inputs
    dj_geral_fechado BOOLEAN,

    -- Metadata
    data_quality VARCHAR(20),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries by timestamp and device
CREATE INDEX idx_telemetry_timestamp ON telemetry_history(timestamp DESC);
CREATE INDEX idx_telemetry_device_timestamp ON telemetry_history(device_id, timestamp DESC);

-- ============================================================================
-- ALERT PREFERENCES
-- ============================================================================

-- Alert preferences for temperature sensors
CREATE TABLE alert_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_name VARCHAR(100) NOT NULL UNIQUE,
    sensor_address VARCHAR(20) NOT NULL,

    -- Thresholds
    threshold_hh DECIMAL(5,2),  -- High-High (Nível Muito Alto)
    threshold_h DECIMAL(5,2),   -- High (Nível Alto)
    threshold_l DECIMAL(5,2),   -- Low (Nível Baixo)
    threshold_ll DECIMAL(5,2),  -- Low-Low (Nível Muito Baixo)

    -- Enable/disable individual alerts
    enable_hh BOOLEAN DEFAULT true,
    enable_h BOOLEAN DEFAULT true,
    enable_l BOOLEAN DEFAULT true,
    enable_ll BOOLEAN DEFAULT true,

    -- Hysteresis to prevent alert flapping
    hysteresis DECIMAL(5,2) DEFAULT 1.0,

    -- Alert cooldown (seconds) - minimum time between same alerts
    cooldown_seconds INTEGER DEFAULT 300,

    -- Active/inactive
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default alert preferences for the 4 temperature sensors
INSERT INTO alert_preferences (sensor_name, sensor_address, threshold_hh, threshold_h, threshold_l, threshold_ll) VALUES
    ('ambiente', '%MW36', 40.0, 35.0, 10.0, 5.0),
    ('quadro_eletrico', '%MW38', 60.0, 50.0, 15.0, 10.0),
    ('modulo_fotovoltaico', '%MW40', 80.0, 70.0, 5.0, 0.0),
    ('transformador', '%MW42', 85.0, 75.0, 20.0, 15.0);

-- ============================================================================
-- ALERT HISTORY
-- ============================================================================

-- Stores all triggered alerts
CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(50) NOT NULL,
    sensor_name VARCHAR(100) NOT NULL,
    alert_level alert_level NOT NULL,
    severity alert_severity NOT NULL,

    -- Alert details
    measured_value DECIMAL(5,2) NOT NULL,
    threshold_value DECIMAL(5,2) NOT NULL,
    message TEXT NOT NULL,

    -- Alert timing
    triggered_at TIMESTAMPTZ NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_acknowledged BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for alert queries
CREATE INDEX idx_alert_triggered_at ON alert_history(triggered_at DESC);
CREATE INDEX idx_alert_active ON alert_history(is_active) WHERE is_active = true;
CREATE INDEX idx_alert_sensor ON alert_history(sensor_name, triggered_at DESC);
CREATE INDEX idx_alert_level ON alert_history(alert_level, triggered_at DESC);

-- ============================================================================
-- USER PREFERENCES
-- ============================================================================

-- General user preferences (theme, notifications, etc.)
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    preference_key VARCHAR(100) NOT NULL UNIQUE,
    preference_value JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default user preferences
INSERT INTO user_preferences (preference_key, preference_value) VALUES
    ('theme', '{"mode": "light", "auto_switch": false}'::jsonb),
    ('notifications', '{"enabled": true, "sound": true, "desktop": false}'::jsonb),
    ('dashboard', '{"refresh_rate": 30, "show_charts": true}'::jsonb);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for alert_preferences
CREATE TRIGGER update_alert_preferences_updated_at
    BEFORE UPDATE ON alert_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_preferences
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to cleanup old telemetry data (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_telemetry()
RETURNS void AS $$
BEGIN
    DELETE FROM telemetry_history
    WHERE timestamp < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for active alerts with full details
CREATE VIEW active_alerts AS
SELECT
    ah.id,
    ah.device_id,
    ah.sensor_name,
    ah.alert_level,
    ah.severity,
    ah.measured_value,
    ah.threshold_value,
    ah.message,
    ah.triggered_at,
    ap.sensor_address,
    EXTRACT(EPOCH FROM (NOW() - ah.triggered_at)) AS duration_seconds
FROM alert_history ah
LEFT JOIN alert_preferences ap ON ah.sensor_name = ap.sensor_name
WHERE ah.is_active = true
ORDER BY ah.triggered_at DESC;

-- View for latest telemetry
CREATE VIEW latest_telemetry AS
SELECT DISTINCT ON (device_id)
    *
FROM telemetry_history
ORDER BY device_id, timestamp DESC;

-- View for temperature statistics (last 24h)
CREATE VIEW temperature_stats_24h AS
SELECT
    'ambiente' as sensor_name,
    AVG(temp_ambiente) as avg_temp,
    MIN(temp_ambiente) as min_temp,
    MAX(temp_ambiente) as max_temp,
    STDDEV(temp_ambiente) as stddev_temp
FROM telemetry_history
WHERE timestamp > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    'quadro_eletrico',
    AVG(temp_quadro_eletrico),
    MIN(temp_quadro_eletrico),
    MAX(temp_quadro_eletrico),
    STDDEV(temp_quadro_eletrico)
FROM telemetry_history
WHERE timestamp > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    'modulo_fotovoltaico',
    AVG(temp_modulo_fotovoltaico),
    MIN(temp_modulo_fotovoltaico),
    MAX(temp_modulo_fotovoltaico),
    STDDEV(temp_modulo_fotovoltaico)
FROM telemetry_history
WHERE timestamp > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    'transformador',
    AVG(temp_transformador),
    MIN(temp_transformador),
    MAX(temp_transformador),
    STDDEV(temp_transformador)
FROM telemetry_history
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtzview;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtzview;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO mtzview;
