"""
Backend API Client Module
Handles communication with MTZ View backend
"""
import logging
import requests
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from config import config

logger = logging.getLogger(__name__)


class BackendClient:
    """
    Modular client for MTZ View Backend API
    Handles sending inverter data to backend with retry logic
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MTZ-Inverter-Service/1.0'
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """
        Send inverter telemetry data to backend
        Includes automatic retry on failure
        """
        try:
            logger.debug(f"Sending telemetry to {config.backend.telemetry_url}")

            response = self.session.post(
                config.backend.telemetry_url,
                json=data,
                timeout=config.backend.timeout
            )

            response.raise_for_status()

            logger.info(f"Telemetry sent successfully. Status: {response.status_code}")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending telemetry to backend")
            raise

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to backend: {e}")
            raise

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from backend: {e.response.status_code} - {e.response.text}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error sending telemetry: {e}")
            raise

    def ping(self) -> bool:
        """
        Check if backend is reachable
        """
        try:
            response = self.session.get(
                f"{config.backend.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Backend ping failed: {e}")
            return False

    def close(self):
        """Close session"""
        self.session.close()
