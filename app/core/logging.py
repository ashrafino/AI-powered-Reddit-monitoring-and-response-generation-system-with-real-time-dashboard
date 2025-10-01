import logging
import sys
from typing import Any, Dict
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.app_env == "development" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log errors with context information."""
    logger.error(f"Error: {str(error)}", extra={"context": context or {}})

def log_info(message: str, context: Dict[str, Any] = None):
    """Log info messages with context."""
    logger.info(message, extra={"context": context or {}})

def log_warning(message: str, context: Dict[str, Any] = None):
    """Log warning messages with context."""
    logger.warning(message, extra={"context": context or {}})

