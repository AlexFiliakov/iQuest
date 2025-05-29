"""Utility modules for Apple Health Monitor Dashboard.

This package provides essential utility functions and classes for the Apple Health
Monitor application, including error handling, logging configuration, and XML
validation utilities.

The utilities package includes:

- **Error Handling**: Centralized error handling and exception management
- **Logging Configuration**: Application-wide logging setup and configuration
- **XML Validation**: Apple Health export XML validation and parsing utilities

These utilities provide foundational support for the entire application,
ensuring robust error handling, comprehensive logging, and reliable data
validation across all components.

Example:
    Setting up logging:
    
    >>> from utils.logging_config import setup_logging
    >>> setup_logging(level='INFO', log_file='health_monitor.log')
    
    Error handling:
    
    >>> from utils.error_handler import handle_database_error
    >>> try:
    ...     # database operation
    ...     pass
    ... except Exception as e:
    ...     handle_database_error(e, context="user_data_load")
"""