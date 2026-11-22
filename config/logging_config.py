"""Centralized logging configuration for NeuralShield AI."""

import logging
import sys
from pathlib import Path
from typing import Optional


_INITIALIZED = False


def setup_logger(
    name: str = "neuralshield",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configures and returns a structured logger for the platform.
    
    Args:
        name: Logger name.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
        log_file: Optional file destination for persistent logs.
        
    Returns:
        Configured logging.Logger instance.
    """
    global _INITIALIZED
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # Console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Optional file output
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
    _INITIALIZED = True
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Returns a child logger inheriting root NeuralShield formatting."""
    return logging.getLogger(f"neuralshield.{module_name}")
