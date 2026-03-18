import logging
import os
from datetime import datetime


def setup_logger(name: str = "veta_strategist", log_file: str | None = None) -> logging.Logger:
    """Configura y retorna un logger para el sistema."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "veta_strategist") -> logging.Logger:
    """Obtiene un logger existente o crea uno nuevo."""
    return logging.getLogger(name)
