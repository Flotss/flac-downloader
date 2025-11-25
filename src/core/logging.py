"""Custom logger with colored console output."""

import os
import sys
import logging
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with ANSI colors and icons for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '💀',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and icons."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        icon = self.ICONS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        formatted = f"{color}[{timestamp}] {icon} {record.getMessage()}{reset}"
        return formatted


def setup_logger(
    name: str = "FlacDownloader",
    level: Optional[int] = None,
    log_dir: str = "data"
) -> logging.Logger:
    """
    Configure and return a logger with colored console and file output.
    
    Args:
        name: Logger name
        level: Logging level (uses settings.LOG_LEVEL if not provided)
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    """
    # Import here to avoid circular imports
    if level is None:
        from src.config import settings
        level = settings.LOG_LEVEL
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # File handler for persistent logs
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get or create the global logger instance."""
    global logger
    if logger is None:
        logger = setup_logger()
    return logger
