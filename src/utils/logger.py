"""Logging utility module."""
import logging
from pathlib import Path
from config.main_config import LOGS_DIR

def get_logger(name: str, log_filename: str = "application.log") -> logging.Logger:
    """Return a configured logger with file and console handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        log_file_path = LOGS_DIR / log_filename
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

