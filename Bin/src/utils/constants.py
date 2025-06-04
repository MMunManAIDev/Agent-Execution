"""
Shared constants for the AgentExecutive application.
"""

# Handler status codes
STATUS_CODES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'TIMEOUT': 'timeout',
    'NOT_FOUND': 'not_found',
    'INVALID_INPUT': 'invalid_input',
    'NOT_AUTHORIZED': 'not_authorized',
    'SERVER_ERROR': 'server_error'
}

# URL related constants
URL_SCHEMES = {'http', 'https'}
DEFAULT_SCHEME = 'https'
MAX_URL_LENGTH = 2048

# Threading constants
THREAD_POOL_SIZE = 4
THREAD_TIMEOUT = 30  # seconds

# Logging constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"

# Base exception classes
class UtilityError(Exception):
    """Base class voor utility errors"""
    pass

class URLError(UtilityError):
    """URL gerelateerde errors"""
    pass

class ThreadingError(UtilityError):
    """Threading gerelateerde errors"""
    pass

class LoggingError(UtilityError):
    """Logging gerelateerde errors"""
    pass