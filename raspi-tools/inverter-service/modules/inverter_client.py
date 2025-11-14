"""
Huawei Inverter Client Module
Handles communication with Huawei SUN2000 series inverters
Supports all SUN2000 models via Modbus RTU and TCP
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for huawei_solar import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'huawei-solar-lib' / 'src'))

from huawei_solar import (
    SUN2000Device,
    create_device_instance,
    create_rtu_client,
    create_tcp_client,
)
from huawei_solar import register_names as rn
from huawei_solar.exceptions import HuaweiSolarException

from config import config

logger = logging.getLogger(__name__)


class InverterClient:
    """
    Modular client for Huawei SUN2000 Series Inverters
    Supports all SUN2000 models (3KTL to 100KTL and beyond)
    Handles connection, data reading, and error recovery
    """

    # Register groups for organized data collection
    POWER_REGISTERS = [
        rn.INPUT_POWER,              # DC Input Power
        rn.ACTIVE_POWER,             # AC Active Power
        rn.REACTIVE_POWER,           # Reactive Power
        rn.POWER_FACTOR,             # Power Factor
    ]

    VOLTAGE_CURRENT_REGISTERS = [
        rn.LINE_VOLTAGE_A_B,         # Phase AB Voltage
        rn.LINE_VOLTAGE_B_C,         # Phase BC Voltage
        rn.LINE_VOLTAGE_C_A,         # Phase CA Voltage
        rn.PHASE_A_VOLTAGE,          # Phase A Voltage
        rn.PHASE_B_VOLTAGE,          # Phase B Voltage
        rn.PHASE_C_VOLTAGE,          # Phase C Voltage
        rn.PHASE_A_CURRENT,          # Phase A Current
        rn.PHASE_B_CURRENT,          # Phase B Current
        rn.PHASE_C_CURRENT,          # Phase C Current
    ]

    ENERGY_REGISTERS = [
        rn.DAILY_YIELD_ENERGY,       # Daily Energy Yield
        rn.ACCUMULATED_YIELD_ENERGY, # Total Energy Yield
    ]

    TEMPERATURE_REGISTERS = [
        rn.INTERNAL_TEMPERATURE,     # Internal Temperature
    ]

    GRID_REGISTERS = [
        rn.GRID_FREQUENCY,           # Grid Frequency
    ]

    STATUS_REGISTERS = [
        rn.DEVICE_STATUS,            # Device Status
        rn.ALARM_1,                  # Alarm Status 1
        rn.ALARM_2,                  # Alarm Status 2
        rn.ALARM_3,                  # Alarm Status 3
    ]

    PV_REGISTERS = [
        rn.PV_01_VOLTAGE,            # String 1 Voltage
        rn.PV_01_CURRENT,            # String 1 Current
        rn.PV_02_VOLTAGE,            # String 2 Voltage
        rn.PV_02_CURRENT,            # String 2 Current
        rn.PV_03_VOLTAGE,            # String 3 Voltage
        rn.PV_03_CURRENT,            # String 3 Current
        rn.PV_04_VOLTAGE,            # String 4 Voltage
        rn.PV_04_CURRENT,            # String 4 Current
    ]

    def __init__(self):
        self.client = None
        self.device: Optional[SUN2000Device] = None
        self.connected = False
        self.last_error: Optional[str] = None

    async def connect(self) -> bool:
        """
        Establish connection to inverter
        Supports both RTU (USB/RS485) and TCP connections
        """
        try:
            logger.info(f"Connecting to inverter via {config.inverter.connection_type.upper()}...")

            if config.inverter.connection_type == 'rtu':
                # USB/RS485 Connection
                self.client = create_rtu_client(
                    port=config.inverter.serial_port,
                    baudrate=config.inverter.baudrate,
                    slave_id=config.inverter.slave_id
                )
                logger.info(f"RTU Client created: {config.inverter.serial_port} @ {config.inverter.baudrate}bps")

            elif config.inverter.connection_type == 'tcp':
                # TCP Connection
                if not config.inverter.tcp_host:
                    raise ValueError("TCP host not configured")

                self.client = create_tcp_client(
                    host=config.inverter.tcp_host,
                    port=config.inverter.tcp_port
                )
                logger.info(f"TCP Client created: {config.inverter.tcp_host}:{config.inverter.tcp_port}")

            else:
                raise ValueError(f"Invalid connection type: {config.inverter.connection_type}")

            # Create device instance
            self.device = await create_device_instance(self.client)

            if not isinstance(self.device, SUN2000Device):
                raise HuaweiSolarException("Device is not a SUN2000 inverter")

            self.connected = True
            self.last_error = None
            logger.info("Successfully connected to Huawei SUN2000 inverter")

            # Log device info
            model = await self.device.get(rn.MODEL_NAME)
            serial = await self.device.get(rn.SERIAL_NUMBER)
            logger.info(f"Inverter Model: {model.value}")
            logger.info(f"Serial Number: {serial.value}")

            return True

        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            logger.error(f"Failed to connect to inverter: {e}")
            return False

    async def disconnect(self):
        """Close connection to inverter"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Disconnected from inverter")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            finally:
                self.connected = False
                self.device = None
                self.client = None

    async def read_all_data(self) -> Dict[str, Any]:
        """
        Read all important data from inverter
        Returns organized dictionary with all metrics
        """
        if not self.connected or not self.device:
            raise HuaweiSolarException("Not connected to inverter")

        try:
            # Read all register groups
            power_data = await self.device.batch_update(self.POWER_REGISTERS)
            voltage_current_data = await self.device.batch_update(self.VOLTAGE_CURRENT_REGISTERS)
            energy_data = await self.device.batch_update(self.ENERGY_REGISTERS)
            temperature_data = await self.device.batch_update(self.TEMPERATURE_REGISTERS)
            grid_data = await self.device.batch_update(self.GRID_REGISTERS)
            status_data = await self.device.batch_update(self.STATUS_REGISTERS)
            pv_data = await self.device.batch_update(self.PV_REGISTERS)

            # Get device ID dynamically
            device_model = await self.device.get(rn.MODEL_NAME)
            device_id = f"{device_model.value}"

            # Organize data
            data = {
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'power': self._format_results(power_data),
                'voltage_current': self._format_results(voltage_current_data),
                'energy': self._format_results(energy_data),
                'temperature': self._format_results(temperature_data),
                'grid': self._format_results(grid_data),
                'status': self._format_results(status_data),
                'pv_strings': self._format_results(pv_data),
                'metadata': {
                    'connection_type': config.inverter.connection_type,
                    'data_quality': 'good',
                    'read_timestamp': datetime.now().isoformat(),
                }
            }

            logger.debug(f"Successfully read all data from inverter")
            return data

        except Exception as e:
            logger.error(f"Error reading inverter data: {e}")
            self.last_error = str(e)
            raise

    def _format_results(self, results: Dict) -> Dict[str, Any]:
        """
        Format register results into clean dictionary
        Extracts value and unit from Result objects
        """
        formatted = {}
        for key, result in results.items():
            formatted[key] = {
                'value': result.value,
                'unit': result.unit if hasattr(result, 'unit') else None
            }
        return formatted

    async def health_check(self) -> bool:
        """
        Perform health check on inverter connection
        Returns True if connection is healthy
        """
        if not self.connected or not self.device:
            return False

        try:
            # Try to read device status
            status = await self.device.get(rn.DEVICE_STATUS)
            logger.debug(f"Health check passed. Device status: {status.value}")
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.connected = False
            return False

    async def get_device_info(self) -> Dict[str, Any]:
        """Get static device information"""
        if not self.connected or not self.device:
            raise HuaweiSolarException("Not connected to inverter")

        try:
            info = await self.device.batch_update([
                rn.MODEL_NAME,
                rn.SERIAL_NUMBER,
                rn.PN,
                rn.MODEL_ID,
                rn.NB_PV_STRINGS,
                rn.RATED_POWER,
            ])

            return self._format_results(info)

        except Exception as e:
            logger.error(f"Error reading device info: {e}")
            raise
