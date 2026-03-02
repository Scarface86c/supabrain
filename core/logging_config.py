"""
SupaBrain Logging Configuration
Centralized logging setup with rotation and structured output
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "supabrain.log"

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure logging with file rotation and console output"""
    LOG_DIR.mkdir(exist_ok=True)
    
    # Create formatter with timestamp and context
    formatter: logging.Formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB per file, keep 5 backups)
    file_handler: logging.handlers.RotatingFileHandler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Console handler for errors and warnings
    console_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    
    # Root logger configuration
    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Quiet noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return logging.getLogger('supabrain')

# Module-level logger getter
def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return logging.getLogger(f'supabrain.{name}')
