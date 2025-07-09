"""Logging utilities."""

import logging
import sys
import os
from typing import Optional
from datetime import datetime

def get_logger(
    name: str, 
    level: str = "DEBUG", 
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """Get a configured logger with console and file output."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        if log_to_file and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Formatter for detailed logging
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Console handler (terminal output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        
        if log_to_file:
            # File handler for all logs
            log_filename = f"{log_dir}/{name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_filename)
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
            
            # Separate error log file
            error_log_filename = f"{log_dir}/{name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
            error_handler = logging.FileHandler(error_log_filename)
            error_handler.setFormatter(detailed_formatter)
            error_handler.setLevel(logging.ERROR)
            logger.addHandler(error_handler)
        
        # Set logger level to DEBUG to capture everything
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Prevent duplicate logs
        
    return logger

def setup_root_logger(level: str = "DEBUG") -> None:
    """Setup root logger for the entire application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )
