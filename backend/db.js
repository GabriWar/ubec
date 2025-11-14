import pkg from 'pg';
const { Pool } = pkg;

// Database configuration
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'mtzview',
  user: process.env.DB_USER || 'mtzview',
  password: process.env.DB_PASSWORD || 'mtzview_secure_password',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test connection
pool.on('connect', () => {
  console.log('[DB] Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('[DB] Unexpected database error:', err);
  process.exit(-1);
});

// ============================================================================
// TELEMETRY FUNCTIONS
// ============================================================================

/**
 * Insert telemetry data into history
 */
async function insertTelemetry(data) {
  const query = `
    INSERT INTO telemetry_history (
      device_id,
      timestamp,
      temp_ambiente,
      temp_quadro_eletrico,
      temp_modulo_fotovoltaico,
      temp_transformador,
      comunicacao_ok,
      sistema_ativo,
      em_falha,
      alarme_ativo,
      emergencia_ativa,
      disjuntor_geral_status,
      servico_auxiliar_ok,
      reset_rasp,
      reset_link_3g,
      usina_gerando,
      dj_geral_fechado,
      data_quality
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
    RETURNING id
  `;

  const values = [
    data.device_id,
    data.timestamp,
    data.sensors?.temperaturas?.ambiente?.value || null,
    data.sensors?.temperaturas?.quadro_eletrico?.value || null,
    data.sensors?.temperaturas?.modulo_fotovoltaico?.value || null,
    data.sensors?.temperaturas?.transformador?.value || null,
    data.status?.operational?.comunicacao_ok || false,
    data.status?.operational?.sistema_ativo || false,
    data.status?.operational?.em_falha || false,
    data.status?.operational?.alarme_ativo || false,
    data.status?.operational?.emergencia_ativa || false,
    data.status?.electrical?.disjuntor_geral_status || 'ABERTO',
    data.status?.electrical?.servico_auxiliar_ok || false,
    data.status?.outputs?.reset_rasp || false,
    data.status?.outputs?.reset_link_3g || false,
    data.status?.outputs?.usina_gerando || false,
    data.status?.inputs?.dj_geral_fechado || false,
    data.metadata?.data_quality || 'unknown',
  ];

  try {
    const result = await pool.query(query, values);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error inserting telemetry:', error.message);
    throw error;
  }
}

/**
 * Get historical telemetry data
 */
async function getHistoricalTelemetry(deviceId, startTime, endTime, limit = 1000) {
  const query = `
    SELECT * FROM telemetry_history
    WHERE device_id = $1
      AND timestamp >= $2
      AND timestamp <= $3
    ORDER BY timestamp DESC
    LIMIT $4
  `;

  try {
    const result = await pool.query(query, [deviceId, startTime, endTime, limit]);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching historical telemetry:', error.message);
    throw error;
  }
}

/**
 * Get latest telemetry for a device
 */
async function getLatestTelemetry(deviceId) {
  const query = `
    SELECT * FROM latest_telemetry
    WHERE device_id = $1
  `;

  try {
    const result = await pool.query(query, [deviceId]);
    return result.rows[0] || null;
  } catch (error) {
    console.error('[DB] Error fetching latest telemetry:', error.message);
    throw error;
  }
}

// ============================================================================
// ALERT FUNCTIONS
// ============================================================================

/**
 * Get alert preferences
 */
async function getAlertPreferences() {
  const query = 'SELECT * FROM alert_preferences WHERE is_active = true';

  try {
    const result = await pool.query(query);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching alert preferences:', error.message);
    throw error;
  }
}

/**
 * Update alert preferences
 */
async function updateAlertPreferences(sensorName, preferences) {
  const query = `
    UPDATE alert_preferences
    SET
      threshold_hh = COALESCE($2, threshold_hh),
      threshold_h = COALESCE($3, threshold_h),
      threshold_l = COALESCE($4, threshold_l),
      threshold_ll = COALESCE($5, threshold_ll),
      enable_hh = COALESCE($6, enable_hh),
      enable_h = COALESCE($7, enable_h),
      enable_l = COALESCE($8, enable_l),
      enable_ll = COALESCE($9, enable_ll),
      hysteresis = COALESCE($10, hysteresis),
      cooldown_seconds = COALESCE($11, cooldown_seconds),
      is_active = COALESCE($12, is_active)
    WHERE sensor_name = $1
    RETURNING *
  `;

  const values = [
    sensorName,
    preferences.threshold_hh,
    preferences.threshold_h,
    preferences.threshold_l,
    preferences.threshold_ll,
    preferences.enable_hh,
    preferences.enable_h,
    preferences.enable_l,
    preferences.enable_ll,
    preferences.hysteresis,
    preferences.cooldown_seconds,
    preferences.is_active,
  ];

  try {
    const result = await pool.query(query, values);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error updating alert preferences:', error.message);
    throw error;
  }
}

/**
 * Insert alert into history
 */
async function insertAlert(alert) {
  const query = `
    INSERT INTO alert_history (
      device_id,
      sensor_name,
      alert_level,
      severity,
      measured_value,
      threshold_value,
      message,
      triggered_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    RETURNING id
  `;

  const values = [
    alert.device_id,
    alert.sensor_name,
    alert.alert_level,
    alert.severity,
    alert.measured_value,
    alert.threshold_value,
    alert.message,
    alert.triggered_at || new Date(),
  ];

  try {
    const result = await pool.query(query, values);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error inserting alert:', error.message);
    throw error;
  }
}

/**
 * Get active alerts
 */
async function getActiveAlerts() {
  const query = 'SELECT * FROM active_alerts';

  try {
    const result = await pool.query(query);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching active alerts:', error.message);
    throw error;
  }
}

/**
 * Acknowledge alert
 */
async function acknowledgeAlert(alertId) {
  const query = `
    UPDATE alert_history
    SET is_acknowledged = true, acknowledged_at = NOW()
    WHERE id = $1
    RETURNING *
  `;

  try {
    const result = await pool.query(query, [alertId]);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error acknowledging alert:', error.message);
    throw error;
  }
}

/**
 * Resolve alert
 */
async function resolveAlert(alertId) {
  const query = `
    UPDATE alert_history
    SET is_active = false, resolved_at = NOW()
    WHERE id = $1
    RETURNING *
  `;

  try {
    const result = await pool.query(query, [alertId]);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error resolving alert:', error.message);
    throw error;
  }
}

// ============================================================================
// USER PREFERENCES FUNCTIONS
// ============================================================================

/**
 * Get user preference
 */
async function getUserPreference(key) {
  const query = 'SELECT preference_value FROM user_preferences WHERE preference_key = $1';

  try {
    const result = await pool.query(query, [key]);
    return result.rows[0]?.preference_value || null;
  } catch (error) {
    console.error('[DB] Error fetching user preference:', error.message);
    throw error;
  }
}

/**
 * Set user preference
 */
async function setUserPreference(key, value) {
  const query = `
    INSERT INTO user_preferences (preference_key, preference_value)
    VALUES ($1, $2)
    ON CONFLICT (preference_key)
    DO UPDATE SET preference_value = $2
    RETURNING *
  `;

  try {
    const result = await pool.query(query, [key, value]);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error setting user preference:', error.message);
    throw error;
  }
}

/**
 * Get temperature statistics
 */
async function getTemperatureStats() {
  const query = 'SELECT * FROM temperature_stats_24h';

  try {
    const result = await pool.query(query);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching temperature stats:', error.message);
    throw error;
  }
}

// ============================================================================
// CLEANUP FUNCTIONS
// ============================================================================

/**
 * Cleanup old telemetry data (keeps last 90 days)
 */
async function cleanupOldTelemetry() {
  try {
    await pool.query('SELECT cleanup_old_telemetry()');
    console.log('[DB] Old telemetry data cleaned up');
  } catch (error) {
    console.error('[DB] Error cleaning up old telemetry:', error.message);
    throw error;
  }
}

// ============================================================================
// INVERTER FUNCTIONS
// ============================================================================

/**
 * Insert inverter telemetry data
 */
async function insertInverterTelemetry(data) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Insert main telemetry
    const telemetryQuery = `
      INSERT INTO inverter_telemetry (
        device_id, timestamp,
        input_power, active_power, reactive_power, power_factor,
        line_voltage_ab, line_voltage_bc, line_voltage_ca,
        phase_a_voltage, phase_b_voltage, phase_c_voltage,
        phase_a_current, phase_b_current, phase_c_current,
        daily_yield_energy, accumulated_yield_energy,
        internal_temperature, grid_frequency,
        device_status, alarm_1, alarm_2, alarm_3,
        connection_type, data_quality, read_timestamp
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
        $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
      ) RETURNING id
    `;

    const telemetryValues = [
      data.device_id,
      data.timestamp,
      data.power?.input_power?.value || null,
      data.power?.active_power?.value || null,
      data.power?.reactive_power?.value || null,
      data.power?.power_factor?.value || null,
      data.voltage_current?.line_voltage_A_B?.value || null,
      data.voltage_current?.line_voltage_B_C?.value || null,
      data.voltage_current?.line_voltage_C_A?.value || null,
      data.voltage_current?.phase_A_voltage?.value || null,
      data.voltage_current?.phase_B_voltage?.value || null,
      data.voltage_current?.phase_C_voltage?.value || null,
      data.voltage_current?.phase_A_current?.value || null,
      data.voltage_current?.phase_B_current?.value || null,
      data.voltage_current?.phase_C_current?.value || null,
      data.energy?.daily_yield_energy?.value || null,
      data.energy?.accumulated_yield_energy?.value || null,
      data.temperature?.internal_temperature?.value || null,
      data.grid?.grid_frequency?.value || null,
      data.status?.device_status?.value || null,
      data.status?.alarm_1?.value || null,
      data.status?.alarm_2?.value || null,
      data.status?.alarm_3?.value || null,
      data.metadata?.connection_type || null,
      data.metadata?.data_quality || null,
      data.metadata?.read_timestamp || null,
    ];

    const telemetryResult = await client.query(telemetryQuery, telemetryValues);
    const telemetryId = telemetryResult.rows[0].id;

    // Insert PV strings data if available
    if (data.pv_strings) {
      const pvQuery = `
        INSERT INTO pv_strings_data (
          inverter_telemetry_id, timestamp,
          pv_01_voltage, pv_01_current,
          pv_02_voltage, pv_02_current,
          pv_03_voltage, pv_03_current,
          pv_04_voltage, pv_04_current
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      `;

      const pvValues = [
        telemetryId,
        data.timestamp,
        data.pv_strings?.PV_01_voltage?.value || null,
        data.pv_strings?.PV_01_current?.value || null,
        data.pv_strings?.PV_02_voltage?.value || null,
        data.pv_strings?.PV_02_current?.value || null,
        data.pv_strings?.PV_03_voltage?.value || null,
        data.pv_strings?.PV_03_current?.value || null,
        data.pv_strings?.PV_04_voltage?.value || null,
        data.pv_strings?.PV_04_current?.value || null,
      ];

      await client.query(pvQuery, pvValues);
    }

    await client.query('COMMIT');
    return telemetryResult.rows[0];
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('[DB] Error inserting inverter telemetry:', error.message);
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Get latest inverter data
 */
async function getLatestInverterData(deviceId = null) {
  const query = deviceId
    ? 'SELECT * FROM latest_inverter_data WHERE device_id = $1'
    : 'SELECT * FROM latest_inverter_data';

  try {
    const result = await pool.query(query, deviceId ? [deviceId] : []);
    return deviceId ? result.rows[0] : result.rows;
  } catch (error) {
    console.error('[DB] Error fetching latest inverter data:', error.message);
    throw error;
  }
}

/**
 * Get inverter hourly statistics
 */
async function getInverterHourlyStats(deviceId = null, hours = 24) {
  const query = deviceId
    ? `SELECT * FROM inverter_hourly_stats
       WHERE device_id = $1 AND hour >= NOW() - INTERVAL '${hours} hours'
       ORDER BY hour DESC`
    : `SELECT * FROM inverter_hourly_stats
       WHERE hour >= NOW() - INTERVAL '${hours} hours'
       ORDER BY hour DESC`;

  try {
    const result = await pool.query(query, deviceId ? [deviceId] : []);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching inverter hourly stats:', error.message);
    throw error;
  }
}

/**
 * Get inverter daily statistics
 */
async function getInverterDailyStats(deviceId = null, days = 30) {
  const query = deviceId
    ? `SELECT * FROM inverter_daily_stats
       WHERE device_id = $1 AND date >= CURRENT_DATE - INTERVAL '${days} days'
       ORDER BY date DESC`
    : `SELECT * FROM inverter_daily_stats
       WHERE date >= CURRENT_DATE - INTERVAL '${days} days'
       ORDER BY date DESC`;

  try {
    const result = await pool.query(query, deviceId ? [deviceId] : []);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching inverter daily stats:', error.message);
    throw error;
  }
}

/**
 * Get or create inverter device
 */
async function upsertInverterDevice(deviceInfo) {
  const query = `
    INSERT INTO inverter_devices (
      device_id, model_name, serial_number, pn, model_id,
      nb_pv_strings, rated_power, is_active
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, true)
    ON CONFLICT (device_id)
    DO UPDATE SET
      model_name = EXCLUDED.model_name,
      updated_at = NOW()
    RETURNING *
  `;

  const values = [
    deviceInfo.device_id,
    deviceInfo.model_name || null,
    deviceInfo.serial_number || null,
    deviceInfo.pn || null,
    deviceInfo.model_id || null,
    deviceInfo.nb_pv_strings || null,
    deviceInfo.rated_power || null,
  ];

  try {
    const result = await pool.query(query, values);
    return result.rows[0];
  } catch (error) {
    console.error('[DB] Error upserting inverter device:', error.message);
    throw error;
  }
}

/**
 * Get all active inverters
 */
async function getActiveInverters() {
  const query = 'SELECT * FROM inverter_devices WHERE is_active = true ORDER BY device_id';

  try {
    const result = await pool.query(query);
    return result.rows;
  } catch (error) {
    console.error('[DB] Error fetching active inverters:', error.message);
    throw error;
  }
}

/**
 * Cleanup old inverter data
 */
async function cleanupOldInverterData() {
  try {
    await pool.query('SELECT cleanup_old_inverter_data()');
    console.log('[DB] Old inverter data cleaned up');
  } catch (error) {
    console.error('[DB] Error cleaning up old inverter data:', error.message);
    throw error;
  }
}

// ============================================================================
// CONNECTION FUNCTIONS
// ============================================================================

// Test database connection on startup
async function testConnection() {
  try {
    const result = await pool.query('SELECT NOW()');
    console.log('[DB] Database connection test successful:', result.rows[0].now);
    return true;
  } catch (error) {
    console.error('[DB] Database connection test failed:', error.message);
    return false;
  }
}

// Graceful shutdown
async function closePool() {
  try {
    await pool.end();
    console.log('[DB] Database pool closed');
  } catch (error) {
    console.error('[DB] Error closing database pool:', error.message);
  }
}

export {
  pool,
  testConnection,
  closePool,

  // Telemetry
  insertTelemetry,
  getHistoricalTelemetry,
  getLatestTelemetry,
  getTemperatureStats,

  // Alerts
  getAlertPreferences,
  updateAlertPreferences,
  insertAlert,
  getActiveAlerts,
  acknowledgeAlert,
  resolveAlert,

  // User preferences
  getUserPreference,
  setUserPreference,

  // Inverter
  insertInverterTelemetry,
  getLatestInverterData,
  getInverterHourlyStats,
  getInverterDailyStats,
  upsertInverterDevice,
  getActiveInverters,
  cleanupOldInverterData,

  // Cleanup
  cleanupOldTelemetry,
};
