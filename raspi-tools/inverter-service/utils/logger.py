"""
Logging utility module
Centralized logging configuration
"""
import logging
import colorlog
from config import config


def setup_logger(name: str = None) -> logging.Logger:
    """
    Setup colored logger with consistent formatting
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                config.logging.format,
                datefmt=config.logging.date_format,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        )

        logger.addHandler(handler)
        logger.setLevel(getattr(logging, config.logging.level))

    return logger
