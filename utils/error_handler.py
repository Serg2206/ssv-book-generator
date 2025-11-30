"""Error handling utilities for SSV-Book-Generator.

This module provides:
- Custom exception classes for different error types
- Retry decorator with exponential backoff
- Error handling decorators for API calls
- Safe execution context manager
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Type, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# Custom Exception Classes
class SSVBookError(Exception):
    """Base exception for SSV-Book-Generator."""
    pass


class APIError(SSVBookError):
    """Exception raised for API-related errors."""
    def __init__(self, message: str, provider: str = None, status_code: int = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)


class ValidationError(SSVBookError):
    """Exception raised for data validation errors."""
    pass


class FileError(SSVBookError):
    """Exception raised for file operation errors."""
    pass


class ConfigError(SSVBookError):
    """Exception raised for configuration errors."""
    pass


# Retry Decorator with Exponential Backoff
def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator to retry function on specified exceptions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# API Error Handler Decorator
def handle_api_errors(provider: str = "Unknown") -> Callable:
    """Decorator to handle API errors consistently.
    
    Args:
        provider: Name of the API provider
    
    Returns:
        Decorated function with API error handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"API error from {provider}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise APIError(error_msg, provider=provider) from e
        
        return wrapper
    return decorator


# Safe Execution Context Manager
@contextmanager
def safe_execute(operation_name: str, fallback_value: Any = None, raise_on_error: bool = False):
    """Context manager for safe execution with error handling.
    
    Args:
        operation_name: Name of the operation for logging
        fallback_value: Value to return if operation fails
        raise_on_error: Whether to raise exception after logging
    
    Yields:
        None
    
    Example:
        with safe_execute("image generation", fallback_value="placeholder.png"):
            result = generate_image()
    """
    try:
        yield
    except SSVBookError as e:
        logger.error(f"{operation_name} failed with SSVBookError: {e}", exc_info=True)
        if raise_on_error:
            raise
        return fallback_value
    except Exception as e:
        logger.error(f"{operation_name} failed with unexpected error: {e}", exc_info=True)
        if raise_on_error:
            raise SSVBookError(f"{operation_name} failed") from e
        return fallback_value
