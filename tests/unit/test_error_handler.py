"""Tests for error handling utilities.

This module contains comprehensive tests for the error handling framework
including custom exceptions, decorators, context managers, and error
formatting utilities.

Test Coverage:
- Custom exception hierarchy functionality
- Error handler decorator with various configurations
- Safe file operation decorator
- Safe database operation decorator
- ErrorContext context manager
- Error message formatting utilities
- Exception re-raising and suppression logic

All tests validate proper error handling, logging, and exception
conversion as specified in the error handling framework.
"""

import unittest
import tempfile
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.error_handler import (
    error_handler, safe_file_operation, safe_database_operation,
    ErrorContext, format_error_message,
    AppleHealthError, DataImportError, DatabaseError, DataValidationError
)


class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality.
    
    This test class validates all components of the error handling framework
    including decorators, context managers, custom exceptions, and utility
    functions. Tests ensure proper error conversion, logging, and handling
    behavior across different scenarios.
    """
    
    def test_error_handler_decorator(self):
        """Test error_handler decorator.
        
        Validates that the error_handler decorator properly catches specified
        exceptions and returns the configured default value while logging
        the error details appropriately.
        """
        @error_handler(exceptions=ValueError, default_return=-1)
        def divide(a, b):
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        
        # Test normal operation
        self.assertEqual(divide(10, 2), 5)
        
        # Test error handling
        self.assertEqual(divide(10, 0), -1)
    
    def test_error_handler_reraise(self):
        """Test error_handler with reraise option."""
        @error_handler(exceptions=ValueError, reraise=True)
        def failing_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
    
    def test_safe_file_operation(self):
        """Test safe_file_operation decorator."""
        @safe_file_operation
        def read_file(path):
            with open(path, 'r') as f:
                return f.read()
        
        # Test with non-existent file
        with self.assertRaises(DataImportError) as context:
            read_file("/non/existent/file.txt")
        self.assertIn("File not found", str(context.exception))
    
    def test_safe_database_operation(self):
        """Test safe_database_operation decorator."""
        @safe_database_operation
        def database_operation():
            # Simulate a database error
            import sqlite3
            raise sqlite3.OperationalError("Database locked")
        
        with self.assertRaises(DatabaseError) as context:
            database_operation()
        self.assertIn("Database operation failed", str(context.exception))
    
    def test_error_context(self):
        """Test ErrorContext context manager."""
        # Test with import operation
        with self.assertRaises(DataImportError):
            with ErrorContext("import operation"):
                raise ValueError("Test import error")
        
        # Test with database operation
        with self.assertRaises(DatabaseError):
            with ErrorContext("database operation"):
                raise RuntimeError("Test database error")
        
        # Test with validation operation
        with self.assertRaises(DataValidationError):
            with ErrorContext("validation operation"):
                raise TypeError("Test validation error")
    
    def test_error_context_no_reraise(self):
        """Test ErrorContext with reraise=False."""
        # This should not raise an exception
        with ErrorContext("test operation", reraise=False):
            raise ValueError("This should be caught")
        
        # Execution should continue here
        self.assertTrue(True)
    
    def test_format_error_message(self):
        """Test error message formatting."""
        error = ValueError("Test error message")
        
        # Test without traceback
        message = format_error_message(error, include_traceback=False)
        self.assertIn("ValueError", message)
        self.assertIn("Test error message", message)
        self.assertNotIn("Traceback", message)
        
        # Test with traceback
        try:
            raise error
        except ValueError as e:
            message = format_error_message(e, include_traceback=True)
            self.assertIn("ValueError", message)
            self.assertIn("Test error message", message)
            self.assertIn("Traceback", message)
    
    def test_custom_exceptions(self):
        """Test custom exception hierarchy."""
        # Test base exception
        error = AppleHealthError("Base error")
        self.assertIsInstance(error, Exception)
        
        # Test derived exceptions
        import_error = DataImportError("Import failed")
        self.assertIsInstance(import_error, AppleHealthError)
        
        db_error = DatabaseError("DB failed")
        self.assertIsInstance(db_error, AppleHealthError)
        
        validation_error = DataValidationError("Validation failed")
        self.assertIsInstance(validation_error, AppleHealthError)


if __name__ == "__main__":
    unittest.main()