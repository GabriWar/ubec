-- Huawei SUN2000 Inverter Tables
-- Extension of MTZ View database for inverter data

-- ============================================================================
-- INVERTER TELEMETRY
-- ============================================================================

-- Main inverter telemetry table
CREATE TABLE IF NOT EXISTS inverter_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,

    -- Power measurements
    input_power DECIMAL(10,2),           -- DC Input Power (W)
    active_power DECIMAL(10,2),          -- AC Active Power (W)
    reactive_power DECIMAL(10,2),        -- Reactive Power (var)
    power_factor DECIMAL(5,4),           -- Power Factor

    -- Voltage measurements (V)
    line_voltage_ab DECIMAL(8,2),
    line_voltage_bc DECIMAL(8,2),
    line_voltage_ca DECIMAL(8,2),
    phase_a_voltage DECIMAL(8,2),
    phase_b_voltage DECIMAL(8,2),
    phase_c_voltage DECIMAL(8,2),

    -- Current measurements (A)
    phase_a_current DECIMAL(8,2),
    phase_b_current DECIMAL(8,2),
    phase_c_current DECIMAL(8,2),

    -- Energy measurements
    daily_yield_energy DECIMAL(12,2),     -- kWh
    accumulated_yield_energy DECIMAL(15,2), -- kWh

    -- Temperature
    internal_temperature DECIMAL(5,2),    -- Celsius

    -- Grid
    grid_frequency DECIMAL(5,2),          -- Hz

    -- Device status (stored as integer code)
    device_status INTEGER,

    -- Alarms (bit flags or JSON)
    alarm_1 INTEGER,
    alarm_2 INTEGER,
    alarm_3 INTEGER,

    -- Metadata
    connection_type VARCHAR(10),          -- 'rtu' or 'tcp'
    data_quality VARCHAR(20),
    read_timestamp TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_inverter_telemetry_timestamp ON inverter_telemetry(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_inverter_telemetry_device_timestamp ON inverter_telemetry(device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_inverter_telemetry_created ON inverter_telemetry(created_at DESC);

-- ============================================================================
-- PV STRINGS DATA
-- ============================================================================

-- PV strings measurements (separate table for normalization)
CREATE TABLE IF NOT EXISTS pv_strings_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inverter_telemetry_id UUID REFERENCES inverter_telemetry(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,

    -- String 1
    pv_01_voltage DECIMAL(8,2),
    pv_01_current DECIMAL(8,2),

    -- String 2
    pv_02_voltage DECIMAL(8,2),
    pv_02_current DECIMAL(8,2),

    -- String 3
    pv_03_voltage DECIMAL(8,2),
    pv_03_current DECIMAL(8,2),

    -- String 4
    pv_04_voltage DECIMAL(8,2),
    pv_04_current DECIMAL(8,2),

    -- Additional strings (for larger inverters)
    pv_05_voltage DECIMAL(8,2),
    pv_05_current DECIMAL(8,2),
    pv_06_voltage DECIMAL(8,2),
    pv_06_current DECIMAL(8,2),
    pv_07_voltage DECIMAL(8,2),
    pv_07_current DECIMAL(8,2),
    pv_08_voltage DECIMAL(8,2),
    pv_08_current DECIMAL(8,2),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pv_strings_telemetry ON pv_strings_data(inverter_telemetry_id);
CREATE INDEX IF NOT EXISTS idx_pv_strings_timestamp ON pv_strings_data(timestamp DESC);

-- ============================================================================
-- INVERTER DEVICE INFO
-- ============================================================================

-- Static device information
CREATE TABLE IF NOT EXISTS inverter_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(50) UNIQUE NOT NULL,

    -- Device info
    model_name VARCHAR(100),
    serial_number VARCHAR(100),
    pn VARCHAR(100),
    model_id INTEGER,
    nb_pv_strings INTEGER,
    rated_power DECIMAL(10,2),          -- kW

    -- Installation info
    location VARCHAR(200),
    installation_date DATE,
    notes TEXT,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_seen TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inverter_devices_device_id ON inverter_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_inverter_devices_active ON inverter_devices(is_active) WHERE is_active = true;

-- ============================================================================
-- INVERTER STATISTICS VIEWS
-- ============================================================================

-- Latest inverter data
CREATE OR REPLACE VIEW latest_inverter_data AS
SELECT DISTINCT ON (device_id)
    *
FROM inverter_telemetry
ORDER BY device_id, timestamp DESC;

-- Hourly averages (last 24 hours)
CREATE OR REPLACE VIEW inverter_hourly_stats AS
SELECT
    device_id,
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(input_power) as avg_input_power,
    AVG(active_power) as avg_active_power,
    MAX(input_power) as max_input_power,
    MAX(active_power) as max_active_power,
    AVG(power_factor) as avg_power_factor,
    AVG(grid_frequency) as avg_grid_frequency,
    AVG(internal_temperature) as avg_temperature,
    MAX(internal_temperature) as max_temperature,
    SUM(daily_yield_energy) as total_energy_hour
FROM inverter_telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY device_id, DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Daily statistics
CREATE OR REPLACE VIEW inverter_daily_stats AS
SELECT
    device_id,
    DATE(timestamp) as date,
    MAX(daily_yield_energy) as total_daily_yield,
    AVG(active_power) as avg_active_power,
    MAX(active_power) as peak_power,
    AVG(power_factor) as avg_power_factor,
    MAX(internal_temperature) as max_temperature,
    COUNT(*) as data_points
FROM inverter_telemetry
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY device_id, DATE(timestamp)
ORDER BY date DESC;

-- PV Strings performance
CREATE OR REPLACE VIEW pv_strings_performance AS
SELECT
    psd.timestamp,
    psd.pv_01_voltage, psd.pv_01_current, (psd.pv_01_voltage * psd.pv_01_current) as pv_01_power,
    psd.pv_02_voltage, psd.pv_02_current, (psd.pv_02_voltage * psd.pv_02_current) as pv_02_power,
    psd.pv_03_voltage, psd.pv_03_current, (psd.pv_03_voltage * psd.pv_03_current) as pv_03_power,
    psd.pv_04_voltage, psd.pv_04_current, (psd.pv_04_voltage * psd.pv_04_current) as pv_04_power
FROM pv_strings_data psd
ORDER BY psd.timestamp DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to cleanup old inverter data (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_inverter_data()
RETURNS void AS $$
BEGIN
    DELETE FROM pv_strings_data
    WHERE timestamp < NOW() - INTERVAL '90 days';

    DELETE FROM inverter_telemetry
    WHERE timestamp < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Function to update last_seen on inverter devices
CREATE OR REPLACE FUNCTION update_inverter_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inverter_devices
    SET last_seen = NEW.timestamp,
        updated_at = NOW()
    WHERE device_id = NEW.device_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_seen
CREATE TRIGGER trg_update_inverter_last_seen
    AFTER INSERT ON inverter_telemetry
    FOR EACH ROW
    EXECUTE FUNCTION update_inverter_last_seen();

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Get latest data from all inverters
-- SELECT * FROM latest_inverter_data;

-- Get hourly statistics for today
-- SELECT * FROM inverter_hourly_stats WHERE hour >= CURRENT_DATE;

-- Get daily yield for last 7 days
-- SELECT * FROM inverter_daily_stats WHERE date >= CURRENT_DATE - INTERVAL '7 days';

-- Get PV strings performance for last hour
-- SELECT * FROM pv_strings_performance WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Get all active inverters
-- SELECT * FROM inverter_devices WHERE is_active = true;

-- Total energy generated today
-- SELECT device_id, MAX(daily_yield_energy) as today_total
-- FROM inverter_telemetry
-- WHERE DATE(timestamp) = CURRENT_DATE
-- GROUP BY device_id;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtzview;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtzview;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO mtzview;
