"""
Configuration module for Huawei Inverter Service
Centralized configuration management with CLI argument support
"""
import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class InverterConfig:
    """Inverter connection configuration"""
    # Connection type: 'rtu' for USB/RS485, 'tcp' for network
    connection_type: str = 'rtu'

    # RTU (USB/RS485) Configuration
    serial_port: str = '/dev/ttyUSB0'
    baudrate: int = 9600
    slave_id: int = 1

    # TCP Configuration (if using network)
    tcp_host: Optional[str] = None
    tcp_port: int = 502

    # Polling interval (seconds)
    poll_interval: int = 30

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5


@dataclass
class BackendConfig:
    """Backend API configuration"""
    base_url: str = 'http://localhost:3001'
    telemetry_endpoint: str = '/api/inverter/telemetry'
    timeout: int = 10

    @property
    def telemetry_url(self) -> str:
        return f"{self.base_url}{self.telemetry_endpoint}"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = 'INFO'
    format: str = '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'


@dataclass
class ServiceConfig:
    """Main service configuration"""
    inverter: InverterConfig
    backend: BackendConfig
    logging: LoggingConfig

    def __init__(self):
        self.inverter = InverterConfig()
        self.backend = BackendConfig()
        self.logging = LoggingConfig()

    def update_from_args(self, args: argparse.Namespace):
        """Update configuration from CLI arguments"""
        # Inverter configuration
        if args.connection_type:
            self.inverter.connection_type = args.connection_type
        if args.serial_port:
            self.inverter.serial_port = args.serial_port
        if args.baudrate:
            self.inverter.baudrate = args.baudrate
        if args.slave_id:
            self.inverter.slave_id = args.slave_id
        if args.tcp_host:
            self.inverter.tcp_host = args.tcp_host
            self.inverter.connection_type = 'tcp'  # Auto-switch to TCP
        if args.tcp_port:
            self.inverter.tcp_port = args.tcp_port
        if args.poll_interval:
            self.inverter.poll_interval = args.poll_interval

        # Backend configuration
        if args.backend_url:
            self.backend.base_url = args.backend_url
        if args.backend_timeout:
            self.backend.timeout = args.backend_timeout

        # Logging configuration
        if args.log_level:
            self.logging.level = args.log_level.upper()


# Global config instance
config = ServiceConfig()
