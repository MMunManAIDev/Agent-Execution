"""
Logging Utilities Module

Configureert en beheert logging voor de hele applicatie.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Direct importeren van constants
from .constants import (
    LoggingError,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    DEFAULT_LOG_LEVEL
)

class CustomFormatter(logging.Formatter):
    """Custom formatter met kleurcodering en extra context"""
    
    # ANSI kleurcodes
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[0;35m', # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__(
            fmt=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format het log record met kleuren en extra context.
        
        Args:
            record: Het log record
            
        Returns:
            Geformatteerde log string
        """
        # Maak kopie om origineel niet aan te passen
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Voeg thread info toe
        thread_name = getattr(record_copy, 'threadName', 'MainThread')
        record_copy.threadInfo = f"[{thread_name}]"
        
        # Voeg extra context toe als aanwezig
        if hasattr(record_copy, 'extra'):
            try:
                extra_str = json.dumps(record_copy.extra)
                record_copy.message = f"{record_copy.message} | Context: {extra_str}"
            except Exception:
                pass
        
        # Format met kleuren indien gewenst
        if self.use_colors:
            level_color = self.COLORS.get(record_copy.levelname, self.COLORS['RESET'])
            record_copy.levelname = f"{level_color}{record_copy.levelname}{self.COLORS['RESET']}"
        
        return super().format(record_copy)

class ContextLogger(logging.Logger):
    """Logger die context data kan meegeven in logs"""
    
    def __init__(self, name: str, level: Union[int, str] = DEFAULT_LOG_LEVEL):
        """
        Initialize context logger.
        
        Args:
            name: Logger naam
            level: Log level
        """
        super().__init__(name, level)
        self._context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs) -> None:
        """
        Set context data voor deze logger.
        
        Args:
            **kwargs: Key-value pairs voor context
        """
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear alle context data"""
        self._context.clear()
    
    def _log(self, level: int, msg: str, args, exc_info=None, extra=None, **kwargs):
        """Override _log om context toe te voegen"""
        if extra is None:
            extra = {}
        if self._context:
            extra['extra'] = {**self._context, **extra.get('extra', {})}
        super()._log(level, msg, args, exc_info, extra, **kwargs)

def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: Union[int, str] = DEFAULT_LOG_LEVEL,
    rotate: bool = True,
    use_colors: bool = True
) -> None:
    """
    Setup logging configuratie voor de applicatie.
    
    Args:
        log_file: Pad naar log file (optional)
        level: Log level
        rotate: Of log rotatie gebruikt moet worden
        use_colors: Of kleuren gebruikt moeten worden
        
    Raises:
        LoggingError: Als logging setup faalt
    """
    try:
        # Converteer level naar int indien nodig
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        # Maak root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Verwijder bestaande handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Maak formatter
        formatter = CustomFormatter(use_colors=use_colors)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler indien gewenst
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            if rotate:
                # Rotating file handler
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=Config.LOG_FILE_MAX_BYTES,
                    backupCount=Config.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
            else:
                # Normale file handler
                file_handler = logging.FileHandler(
                    log_file,
                    encoding='utf-8'
                )
            
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Registreer custom logger class
        logging.setLoggerClass(ContextLogger)
        
        # Log startup
        root_logger.info(
            "Logging initialized",
            extra={'extra': {
                'level': logging.getLevelName(level),
                'log_file': str(log_file) if log_file else None,
                'rotate': rotate
            }}
        )
        
    except Exception as e:
        raise LoggingError(f"Failed to setup logging: {str(e)}")

def get_logger(
    name: str,
    level: Optional[Union[int, str]] = None
) -> ContextLogger:
    """
    Krijg een logger instance.
    
    Args:
        name: Logger naam
        level: Optional specifiek level voor deze logger
        
    Returns:
        ContextLogger instance
    """
    logger = logging.getLogger(name)
    if level:
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        logger.setLevel(level)
    return logger

class LogCapture:
    """Context manager voor het tijdelijk opvangen van logs"""
    
    def __init__(self, logger_name: str = None, level: Union[int, str] = DEFAULT_LOG_LEVEL):
        """
        Initialize log capture.
        
        Args:
            logger_name: Specifieke logger om te vangen (None voor root)
            level: Minimum level om te vangen
        """
        self.logger_name = logger_name
        self.level = level if isinstance(level, int) else getattr(logging, level.upper())
        self.messages = []
        self.handler = None
    
    def __enter__(self):
        """Start log capturing"""
        class MemoryHandler(logging.Handler):
            def __init__(self, messages):
                super().__init__()
                self.messages = messages
            
            def emit(self, record):
                self.messages.append(record)
        
        self.handler = MemoryHandler(self.messages)
        self.handler.setLevel(self.level)
        
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop log capturing"""
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
    
    def get_logs(self, level: Optional[Union[int, str]] = None) -> list:
        """
        Krijg opgevangen log berichten.
        
        Args:
            level: Optional filter op level
            
        Returns:
            Lijst met log records
        """
        if level is None:
            return self.messages
        
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        return [r for r in self.messages if r.levelno >= level]

def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator voor het loggen van executie tijd.
    
    Args:
        logger: Specifieke logger om te gebruiken
        
    Example:
        @log_execution_time()
        def slow_function():
            time.sleep(1)
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.debug(
                    f"Function {func.__name__} took {duration:.2f} seconds",
                    extra={'extra': {
                        'function': func.__name__,
                        'duration': duration
                    }}
                )
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(
                    f"Function {func.__name__} failed after {duration:.2f} seconds: {str(e)}",
                    extra={'extra': {
                        'function': func.__name__,
                        'duration': duration,
                        'error': str(e)
                    }}
                )
                raise
        return wrapper
    return decorator