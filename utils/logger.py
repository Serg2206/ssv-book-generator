"""Structured logging utilities for SSV-Book-Generator.

This module provides:
- Colored console output with different log levels
- JSON formatted file logging
- Log rotation
- Function call logging decorator
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Callable, Any
import functools

try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("Warning: colorama not installed. Install with: pip install colorama")


# Color mappings for log levels
LOG_COLORS = {
    'DEBUG': Fore.CYAN if COLORAMA_AVAILABLE else '',
    'INFO': Fore.GREEN if COLORAMA_AVAILABLE else '',
    'WARNING': Fore.YELLOW if COLORAMA_AVAILABLE else '',
    'ERROR': Fore.RED if COLORAMA_AVAILABLE else '',
    'CRITICAL': Fore.RED + Back.WHITE if COLORAMA_AVAILABLE else ''
}

RESET = Style.RESET_ALL if COLORAMA_AVAILABLE else ''


class ColoredFormatter(logging.Formatter):
    """Formatter for colored console output."""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in LOG_COLORS:
            record.levelname = f"{LOG_COLORS[levelname]}{levelname}{RESET}"
        
        # Add color to message based on level
        if record.levelno >= logging.ERROR:
            record.msg = f"{Fore.RED if COLORAMA_AVAILABLE else ''}{record.msg}{RESET}"
        elif record.levelno >= logging.WARNING:
            record.msg = f"{Fore.YELLOW if COLORAMA_AVAILABLE else ''}{record.msg}{RESET}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter for JSON file output."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if any
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = 'ssv_book_generator',
    log_dir: str = 'logs',
    log_level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up logger with colored console and JSON file output.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        log_level: Minimum log level
        console_output: Enable console logging
        file_output: Enable file logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colored output
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handlers with JSON format
    if file_output:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Main log file
        main_log_file = log_path / f"{name}.log"
        file_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Error log file
        error_log_file = log_path / f"{name}_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    logger.info(f"Logger '{name}' initialized")
    return logger


def log_function_call(logger: logging.Logger = None) -> Callable:
    """Decorator to log function calls with arguments and execution time.
    
    Args:
        logger: Logger instance to use. If None, uses root logger
    
    Returns:
        Decorated function with logging
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            
            # Log function call
            args_repr = [repr(a) for a in args][:3]  # Limit to first 3 args
            kwargs_repr = [f"{k}={v!r}" for k, v in list(kwargs.items())[:3]]
            signature = ", ".join(args_repr + kwargs_repr)
            if len(args) > 3 or len(kwargs) > 3:
                signature += ", ..."
            
            logger.debug(f"Calling {func.__name__}({signature})")
            
            try:
                result = func(*args, **kwargs)
                
                # Log completion with execution time
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                # Log exception
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"{func.__name__} failed after {elapsed:.3f}s: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Create default logger instance
default_logger = setup_logger()
