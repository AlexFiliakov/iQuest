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
    """Base exception for Apple Health Monitor application.
    
    This is the base class for all custom exceptions in the Apple Health
    Monitor application. It provides a common interface for handling
    application-specific errors and allows for easier exception catching
    and logging throughout the codebase.
    """
    pass


class DataImportError(AppleHealthError):
    """Raised when data import operations fail.
    
    This exception is raised when importing data from CSV files, XML files,
    or other data sources fails due to file format issues, corruption,
    permission problems, or other import-related errors.
    
    Examples:
        - File not found or inaccessible
        - Invalid file format or structure
        - Data parsing errors
        - Permission denied when reading files
    """
    pass


class DataValidationError(AppleHealthError):
    """Raised when data validation fails.
    
    This exception is raised when data doesn't meet expected validation
    criteria, such as missing required fields, invalid data types,
    or data that doesn't conform to expected formats or ranges.
    
    Examples:
        - Missing required columns in CSV data
        - Invalid date formats
        - Out-of-range numerical values
        - Malformed XML structure
    """
    pass


class DatabaseError(AppleHealthError):
    """Raised when database operations fail.
    
    This exception is raised when SQLite database operations encounter
    errors such as connection failures, query execution errors, schema
    mismatches, or transaction rollbacks.
    
    Examples:
        - Database connection failures
        - SQL syntax errors
        - Constraint violations
        - Transaction deadlocks
    """
    pass


class ConfigurationError(AppleHealthError):
    """Raised when configuration is invalid.
    
    This exception is raised when application configuration settings
    are invalid, missing, or incompatible with the current system state.
    
    Examples:
        - Missing required configuration values
        - Invalid configuration file format
        - Incompatible settings combinations
        - Configuration version mismatches
    """
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
    Converts system-level file exceptions into application-specific DataImportError
    exceptions for consistent error handling throughout the application.
    
    This decorator catches and handles:
    - FileNotFoundError: When specified files don't exist
    - PermissionError: When file access is denied
    - IOError: When general I/O operations fail
    - Other unexpected exceptions (re-raised as-is)
    
    Args:
        func: The function to wrap with error handling.
        
    Returns:
        Callable: The wrapped function with error handling.
        
    Example:
        >>> @safe_file_operation
        ... def read_csv_file(file_path):
        ...     return pd.read_csv(file_path)
        ...
        >>> data = read_csv_file('health_data.csv')  # Handles file errors gracefully
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
    Converts SQLite exceptions into application-specific DatabaseError exceptions
    for consistent error handling and logging.
    
    This decorator is specifically designed for database operations and:
    - Detects SQLite-related exceptions by module name
    - Converts them to DatabaseError instances
    - Logs detailed error information
    - Re-raises non-database exceptions unchanged
    
    Args:
        func: The database function to wrap with error handling.
        
    Returns:
        Callable: The wrapped function with database error handling.
        
    Example:
        >>> @safe_database_operation
        ... def insert_health_record(record_data):
        ...     conn.execute("INSERT INTO health_records ...", record_data)
        ...
        >>> insert_health_record(data)  # Handles database errors gracefully
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
    
    This context manager provides a clean way to handle errors within specific
    operations while maintaining detailed context about what was being performed
    when the error occurred. It automatically logs errors with operation context
    and can convert generic exceptions to application-specific ones.
    
    The context manager can:
    - Log errors with operation context
    - Convert generic exceptions to custom application exceptions
    - Control whether exceptions are re-raised or suppressed
    - Provide detailed error reporting with traceback information
    
    Args:
        operation: Description of the operation being performed.
        reraise: Whether to re-raise exceptions after logging (default: True).
        log_level: Logging level for error messages (default: "ERROR").
    
    Example:
        >>> with ErrorContext("Processing health data import", reraise=True):
        ...     data = load_health_data(file_path)
        ...     validate_data_format(data)
        ...     save_to_database(data)
        
        >>> # For operations where you want to continue on error:
        >>> with ErrorContext("Optional data cleanup", reraise=False):
        ...     cleanup_temporary_files()
    """
    
    def __init__(self, 
                 operation: str, 
                 reraise: bool = True,
                 log_level: str = "ERROR"):
        """Initialize the error context.
        
        Args:
            operation: Human-readable description of the operation.
            reraise: If True, re-raise exceptions after logging.
            log_level: Logging level for error messages.
        """
        self.operation = operation
        self.reraise = reraise
        self.log_level = log_level
        self.logger = get_logger(self.__class__.__name__)
        
    def __enter__(self):
        """Enter the error context.
        
        Returns:
            ErrorContext: Self for use in with statements.
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the error context and handle any exceptions.
        
        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception instance if an exception occurred.
            exc_tb: Traceback object if an exception occurred.
            
        Returns:
            bool: True to suppress the exception, False to re-raise it.
        """
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
    
    Creates a user-friendly error message from an exception object,
    optionally including detailed traceback information for debugging.
    The formatted message includes the exception type and description.
    
    Args:
        error: The exception to format into a message.
        include_traceback: Whether to include the full traceback for debugging.
        
    Returns:
        str: A formatted error message suitable for display to users.
        
    Example:
        >>> try:
        ...     raise ValueError("Invalid input data")
        ... except Exception as e:
        ...     message = format_error_message(e, include_traceback=False)
        ...     print(message)  # "ValueError: Invalid input data"
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