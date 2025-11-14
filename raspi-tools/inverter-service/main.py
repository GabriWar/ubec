#!/usr/bin/env python3
"""
MTZ View - Huawei Inverter Service
Main service entry point for SUN2000-100KTL-M1 integration
Fully configurable via command-line arguments
"""
import asyncio
import argparse
import signal
import sys
from typing import Optional

from config import config
from modules import InverterClient, BackendClient
from utils import setup_logger


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='MTZ View - Huawei SUN2000 Inverter Service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # USB/RS485 connection (default)
  %(prog)s --serial-port /dev/ttyUSB0 --baudrate 9600

  # TCP connection
  %(prog)s --tcp-host 192.168.1.100 --tcp-port 502

  # Custom polling interval and backend URL
  %(prog)s --poll-interval 60 --backend-url http://192.168.1.50:3001

  # Debug mode
  %(prog)s --log-level DEBUG

  # Full example for Raspberry Pi
  %(prog)s \\
    --serial-port /dev/ttyUSB0 \\
    --baudrate 9600 \\
    --slave-id 1 \\
    --poll-interval 30 \\
    --backend-url http://localhost:3001 \\
    --log-level INFO
        '''
    )

    # Connection group
    conn_group = parser.add_argument_group('Inverter Connection')
    conn_group.add_argument(
        '-t', '--connection-type',
        choices=['rtu', 'tcp'],
        help='Connection type (default: rtu for USB/RS485)'
    )

    # RTU (Serial) arguments
    rtu_group = parser.add_argument_group('RTU/Serial Connection (USB/RS485)')
    rtu_group.add_argument(
        '-p', '--serial-port',
        help='Serial port device (default: /dev/ttyUSB0)'
    )
    rtu_group.add_argument(
        '-b', '--baudrate',
        type=int,
        help='Serial baudrate (default: 9600)'
    )
    rtu_group.add_argument(
        '-s', '--slave-id',
        type=int,
        help='Modbus slave ID (default: 1)'
    )

    # TCP arguments
    tcp_group = parser.add_argument_group('TCP Connection (Network)')
    tcp_group.add_argument(
        '--tcp-host',
        help='TCP host/IP address (auto-enables TCP mode)'
    )
    tcp_group.add_argument(
        '--tcp-port',
        type=int,
        help='TCP port (default: 502)'
    )

    # Polling arguments
    poll_group = parser.add_argument_group('Polling Configuration')
    poll_group.add_argument(
        '-i', '--poll-interval',
        type=int,
        help='Polling interval in seconds (default: 30)'
    )

    # Backend arguments
    backend_group = parser.add_argument_group('Backend Configuration')
    backend_group.add_argument(
        '-u', '--backend-url',
        help='Backend API URL (default: http://localhost:3001)'
    )
    backend_group.add_argument(
        '--backend-timeout',
        type=int,
        help='Backend request timeout in seconds (default: 10)'
    )

    # Logging arguments
    log_group = parser.add_argument_group('Logging')
    log_group.add_argument(
        '-l', '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )

    # Utility arguments
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration and exit'
    )

    return parser.parse_args()


logger = None  # Will be initialized after parsing args


class InverterService:
    """
    Main service class
    Orchestrates inverter reading and backend communication
    """

    def __init__(self):
        self.inverter = InverterClient()
        self.backend = BackendClient()
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the service"""
        logger.info("=" * 60)
        logger.info("MTZ View - Huawei Inverter Service")
        logger.info("SUN2000-100KTL-M1 Integration")
        logger.info("=" * 60)

        # Check backend connectivity
        if self.backend.ping():
            logger.info(f"Backend is reachable at {config.backend.base_url}")
        else:
            logger.warning(f"Backend not reachable at {config.backend.base_url}")
            logger.warning("Service will continue but data may not be sent")

        # Connect to inverter
        connected = await self.inverter.connect()
        if not connected:
            logger.error("Failed to connect to inverter. Retrying in 30 seconds...")
            await asyncio.sleep(30)
            return await self.start()

        # Get and log device info
        try:
            device_info = await self.inverter.get_device_info()
            logger.info("Device Information:")
            for key, value in device_info.items():
                logger.info(f"  {key}: {value['value']} {value['unit'] or ''}")
        except Exception as e:
            logger.warning(f"Could not read device info: {e}")

        # Start polling loop
        self.running = True
        self.task = asyncio.create_task(self._polling_loop())

        logger.info(f"Service started. Polling every {config.inverter.poll_interval}s")
        logger.info("Press Ctrl+C to stop")

    async def _polling_loop(self):
        """Main polling loop"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.running:
            try:
                # Read data from inverter
                logger.debug("Reading data from inverter...")
                data = await self.inverter.read_all_data()

                # Send to backend
                try:
                    self.backend.send_telemetry(data)
                    consecutive_errors = 0  # Reset error counter on success
                except Exception as e:
                    logger.error(f"Failed to send data to backend: {e}")
                    # Continue even if backend is down

                # Wait for next poll
                await asyncio.sleep(config.inverter.poll_interval)

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in polling loop (attempt {consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}). Reconnecting...")

                    # Try to reconnect
                    await self.inverter.disconnect()
                    await asyncio.sleep(10)

                    if await self.inverter.connect():
                        logger.info("Successfully reconnected to inverter")
                        consecutive_errors = 0
                    else:
                        logger.error("Failed to reconnect. Waiting 60s before retry...")
                        await asyncio.sleep(60)
                else:
                    # Wait before retry
                    await asyncio.sleep(config.inverter.retry_delay)

    async def stop(self):
        """Stop the service gracefully"""
        logger.info("Stopping service...")
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        await self.inverter.disconnect()
        self.backend.close()

        logger.info("Service stopped")


# Global service instance
service: Optional[InverterService] = None


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"\nReceived signal {sig}. Shutting down...")
    if service:
        asyncio.create_task(service.stop())


def show_configuration():
    """Display current configuration"""
    print("=" * 70)
    print("MTZ View - Huawei Inverter Service - Configuration")
    print("=" * 70)
    print()
    print("Inverter Connection:")
    print(f"  Type:           {config.inverter.connection_type.upper()}")
    if config.inverter.connection_type == 'rtu':
        print(f"  Serial Port:    {config.inverter.serial_port}")
        print(f"  Baudrate:       {config.inverter.baudrate}")
        print(f"  Slave ID:       {config.inverter.slave_id}")
    else:
        print(f"  TCP Host:       {config.inverter.tcp_host}")
        print(f"  TCP Port:       {config.inverter.tcp_port}")
    print(f"  Poll Interval:  {config.inverter.poll_interval}s")
    print()
    print("Backend:")
    print(f"  URL:            {config.backend.base_url}")
    print(f"  Endpoint:       {config.backend.telemetry_endpoint}")
    print(f"  Timeout:        {config.backend.timeout}s")
    print()
    print("Logging:")
    print(f"  Level:          {config.logging.level}")
    print("=" * 70)


async def main():
    """Main entry point"""
    global service, logger

    # Parse command-line arguments
    args = parse_arguments()

    # Update configuration from arguments
    config.update_from_args(args)

    # Initialize logger after config is updated
    logger = setup_logger(__name__)

    # Show configuration if requested
    if args.show_config:
        show_configuration()
        return 0

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        service = InverterService()
        await service.start()

        # Keep running until stopped
        while service.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1

    finally:
        if service:
            await service.stop()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"CRITICAL: Failed to start service: {e}", file=sys.stderr)
        sys.exit(1)
