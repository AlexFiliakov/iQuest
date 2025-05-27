"""
Centralized error handling utilities for Apple Health Monitor Dashboard

This module provides error handling decorators, custom exceptions,
and error reporting utilities.
"""

import logging
import functools
import traceback
from typing import Any, Callable, Optional, Type, Union
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


# Custom Exceptions
class AppleHealthError(Exception):
    """Base exception for Apple Health Monitor application"""
    pass


class DataImportError(AppleHealthError):
    """Raised when data import fails"""
    pass


class DataValidationError(AppleHealthError):
    """Raised when data validation fails"""
    pass


class DatabaseError(AppleHealthError):
    """Raised when database operations fail"""
    pass


class ConfigurationError(AppleHealthError):
    """Raised when configuration is invalid"""
    pass


def error_handler(
    exceptions: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_level: str = "ERROR",
    reraise: bool = False,
    message: Optional[str] = None
) -> Callable:
    """
    Decorator for handling errors in functions.
    
    Args:
        exceptions: Exception type(s) to catch
        default_return: Value to return on error
        log_level: Logging level for errors
        reraise: Whether to re-raise the exception after logging
        message: Custom error message
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Build error context
                error_msg = message or f"Error in {func.__name__}"
                error_details = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                # Log the error
                log_method = getattr(logger, log_level.lower())
                log_method(f"{error_msg}: {error_details}")
                
                if reraise:
                    raise
                    
                return default_return
                
        return wrapper
    return decorator


def safe_file_operation(func: Callable) -> Callable:
    """
    Decorator for safe file operations with proper error handling.
    
    Automatically handles common file operation errors and logs them appropriately.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            raise DataImportError(f"File not found: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied in {func.__name__}: {e}")
            raise DataImportError(f"Permission denied: {e}")
        except IOError as e:
            logger.error(f"I/O error in {func.__name__}: {e}")
            raise DataImportError(f"I/O error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
            
    return wrapper


def safe_database_operation(func: Callable) -> Callable:
    """
    Decorator for safe database operations with proper error handling.
    
    Handles SQLite-specific errors and ensures connections are properly closed.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "sqlite3" in str(type(e).__module__):
                logger.error(f"Database error in {func.__name__}: {e}")
                raise DatabaseError(f"Database operation failed: {e}")
            else:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise
                
    return wrapper


class ErrorContext:
    """
    Context manager for error handling with detailed context information.
    
    Usage:
        with ErrorContext("Processing health data", reraise=True):
            # code that might raise exceptions
    """
    
    def __init__(self, 
                 operation: str, 
                 reraise: bool = True,
                 log_level: str = "ERROR"):
        self.operation = operation
        self.reraise = reraise
        self.log_level = log_level
        self.logger = get_logger(self.__class__.__name__)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_details = {
                'operation': self.operation,
                'error_type': exc_type.__name__,
                'error_message': str(exc_val),
                'traceback': ''.join(traceback.format_tb(exc_tb))
            }
            
            log_method = getattr(self.logger, self.log_level.lower())
            log_method(f"Error during {self.operation}: {error_details}")
            
            # Convert to appropriate custom exception if needed
            if not isinstance(exc_val, AppleHealthError):
                if "import" in self.operation.lower():
                    raise DataImportError(f"{self.operation} failed: {exc_val}") from exc_val
                elif "database" in self.operation.lower():
                    raise DatabaseError(f"{self.operation} failed: {exc_val}") from exc_val
                elif "validation" in self.operation.lower():
                    raise DataValidationError(f"{self.operation} failed: {exc_val}") from exc_val
            
            return not self.reraise


def format_error_message(error: Exception, include_traceback: bool = False) -> str:
    """
    Format an error message for user display.
    
    Args:
        error: The exception to format
        include_traceback: Whether to include full traceback
        
    Returns:
        Formatted error message
    """
    message = f"{type(error).__name__}: {str(error)}"
    
    if include_traceback:
        message += f"\n\nTraceback:\n{traceback.format_exc()}"
        
    return message


if __name__ == "__main__":
    # Test error handling
    logger = get_logger("error_handler_test")
    
    @error_handler(exceptions=ValueError, default_return=None)
    def test_function(value):
        if value < 0:
            raise ValueError("Value must be positive")
        return value * 2
    
    # Test with valid value
    result = test_function(5)
    print(f"Valid result: {result}")
    
    # Test with invalid value
    result = test_function(-5)
    print(f"Invalid result: {result}")
    
    # Test ErrorContext
    try:
        with ErrorContext("Testing error context", reraise=True):
            raise ValueError("Test error")
    except DataValidationError as e:
        print(f"Caught custom exception: {e}")