"""
AgentExecutive Utilities Package
"""

from .url_utils import clean_url, validate_url, normalize_url, get_domain
from .threading import threaded, run_in_thread, ThreadSafeCounter
from .logging import setup_logging, get_logger
from .constants import (
    STATUS_CODES,
    URL_SCHEMES,
    DEFAULT_SCHEME,
    MAX_URL_LENGTH,
    THREAD_POOL_SIZE,
    THREAD_TIMEOUT,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    DEFAULT_LOG_LEVEL,
    URLError,
    ThreadingError,
    LoggingError,
    UtilityError
)

# Package versie informatie
__utils_version__ = '0.0.4'
__version__ = '0.0.4'

# Type definities voor type hinting
from typing import TypeVar, Callable, Any, Union, Optional

T = TypeVar('T')
UrlType = str
ThreadingFunc = Callable[..., Any]
LogLevel = Union[str, int]

# Expose everything that should be available at package level
__all__ = [
    # URL utilities
    'clean_url',
    'validate_url',
    'normalize_url',
    'get_domain',
    
    # Threading utilities
    'threaded',
    'run_in_thread',
    'ThreadSafeCounter',
    
    # Logging utilities
    'setup_logging',
    'get_logger',
    
    # Constants
    'STATUS_CODES',
    'URL_SCHEMES',
    'DEFAULT_SCHEME',
    'MAX_URL_LENGTH',
    'THREAD_POOL_SIZE',
    'THREAD_TIMEOUT',
    'LOG_FORMAT',
    'LOG_DATE_FORMAT',
    'DEFAULT_LOG_LEVEL',
    
    # Exceptions
    'URLError',
    'ThreadingError',
    'LoggingError',
    'UtilityError'
]

# Helper functies voor error handling
def handle_url_error(error: Exception) -> URLError:
    """Convert URL gerelateerde errors naar URLError"""
    return URLError(f"URL Error: {str(error)}")

def handle_threading_error(error: Exception) -> ThreadingError:
    """Convert threading gerelateerde errors naar ThreadingError"""
    return ThreadingError(f"Threading Error: {str(error)}")

def handle_logging_error(error: Exception) -> LoggingError:
    """Convert logging gerelateerde errors naar LoggingError"""
    return LoggingError(f"Logging Error: {str(error)}")

# Validatie functies
def validate_utils_config():
    """
    Valideer de utility configuratie.
    Returns: (bool, str) - (is_valid, error_message)
    """
    try:
        from ..config import Config
        
        # Controleer logging configuratie
        if not hasattr(Config, 'LOG_LEVEL'):
            return False, "Log level not configured"
            
        if not hasattr(Config, 'LOG_DIR'):
            return False, "Log directory not configured"
            
        # Controleer threading configuratie
        if not hasattr(Config, 'THREAD_POOL_SIZE'):
            return False, "Thread pool size not configured"
            
        return True, None
        
    except ImportError as e:
        return False, f"Configuration error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during utils validation: {str(e)}"

def setup_utils():
    """
    Initialiseer alle utilities.
    Throws: UtilityError als initialisatie faalt
    """
    try:
        is_valid, error = validate_utils_config()
        if not is_valid:
            raise UtilityError(f"Invalid utility configuration: {error}")
            
        setup_logging()
        logger = get_logger(__name__)
        logger.info("Utilities initialized successfully")
        
    except Exception as e:
        raise UtilityError(f"Failed to initialize utilities: {str(e)}")

def cleanup_utils():
    """Cleanup alle utilities."""
    logger = get_logger(__name__)
    try:
        logger.info("Utilities cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to cleanup utilities: {str(e)}")
        raise UtilityError(f"Cleanup failed: {str(e)}")