"""Centralized logging configuration for Apple Health Monitor Dashboard.

This module provides comprehensive logging infrastructure for the Apple Health Monitor
Dashboard application, featuring structured logging, multiple output handlers, automatic
log rotation, and flexible configuration options for different deployment environments.

Key Features:
    - Unified logging configuration with console and file outputs
    - Structured logging format with detailed context information
    - Automatic log file rotation to prevent disk space issues
    - Separate error logs for critical issue tracking
    - Module-specific logger creation with hierarchical naming
    - Configurable log levels and output destinations
    - UTF-8 encoding support for international characters
    - Production-ready defaults with customization options

Logging Hierarchy:
    - Root logger: apple_health_monitor
    - Module loggers: apple_health_monitor.{module_name}
    - Automatic propagation to parent loggers

Output Destinations:
    - Console: Simple format for immediate feedback (INFO and above)
    - Main log file: Detailed format with full context (DEBUG and above)
    - Error log file: Critical issues only (ERROR and above)

Log Format:
    - Console: timestamp - level - message
    - File: timestamp - logger - level - file:line - function() - message

Example:
    Basic logging setup:
    
    >>> from src.utils.logging_config import setup_logging, get_logger
    >>> 
    >>> # Initialize application logging
    >>> logger = setup_logging(log_level="INFO", app_name="health_monitor")
    >>> 
    >>> # Get module-specific logger
    >>> module_logger = get_logger(__name__)
    >>> module_logger.info("Module initialized successfully")
    
    Advanced configuration:
    
    >>> # Custom log directory and rotation settings
    >>> logger = setup_logging(
    ...     log_level="DEBUG",
    ...     log_dir="/var/log/health_monitor",
    ...     max_bytes=50 * 1024 * 1024,  # 50MB files
    ...     backup_count=10
    ... )
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    app_name: str = "apple_health_monitor",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up centralized logging configuration with console and file outputs.
    
    Configures a comprehensive logging system with multiple handlers for different
    output destinations and log levels. Creates a hierarchical logging structure
    with automatic file rotation and proper formatting for both development and
    production environments.
    
    The function creates three handlers:
    1. Console handler for immediate feedback during development
    2. Main file handler for comprehensive logging with rotation
    3. Error file handler for critical issues that need immediate attention
    
    Args:
        log_level (str): Logging level for the root logger. Valid values are
            'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Defaults to 'INFO'.
        log_dir (Optional[str]): Directory path for log files. If None, defaults
            to 'logs/' directory in the project root.
        app_name (str): Application name used for log file naming and logger
            hierarchy. Defaults to 'apple_health_monitor'.
        max_bytes (int): Maximum size in bytes for each log file before rotation.
            Defaults to 10MB (10 * 1024 * 1024).
        backup_count (int): Number of backup log files to retain during rotation.
            Defaults to 5 files.
        
    Returns:
        logging.Logger: Configured root logger instance with all handlers attached.
        
    Raises:
        OSError: If log directory cannot be created due to permissions.
        ValueError: If log_level is not a valid logging level name.
        
    Example:
        Basic usage with defaults:
        
        >>> logger = setup_logging()
        >>> logger.info("Application started")
        
        Custom configuration for production:
        
        >>> logger = setup_logging(
        ...     log_level="WARNING",
        ...     log_dir="/var/log/health_monitor",
        ...     max_bytes=50 * 1024 * 1024,  # 50MB
        ...     backup_count=10
        ... )
        
        Development setup with debug logging:
        
        >>> logger = setup_logging(log_level="DEBUG", app_name="health_dev")
    """
    # Create logs directory if not specified
    if log_dir is None:
        # Get project root (2 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with detailed format and rotation
    log_file = log_dir / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler for ERROR and CRITICAL only
    error_log_file = log_dir / f"{app_name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Log the initialization
    logger.info(f"Logging initialized - Level: {log_level}, Log directory: {log_dir}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Creates or retrieves a logger instance with a hierarchical name under the
    main application logger. This ensures consistent logging configuration
    across all modules while maintaining proper logger hierarchy for filtering
    and configuration purposes.
    
    The returned logger inherits the configuration from the root 'apple_health_monitor'
    logger, including all handlers, formatters, and log levels. This provides
    consistent logging behavior across the entire application.
    
    Args:
        name (str): Module name for the logger, typically passed as __name__.
            The logger will be created with the name 'apple_health_monitor.{name}'.
        
    Returns:
        logging.Logger: Logger instance configured for the specified module.
        
    Example:
        Using in a module:
        
        >>> # In src/analytics/daily_metrics_calculator.py
        >>> from src.utils.logging_config import get_logger
        >>> 
        >>> logger = get_logger(__name__)
        >>> logger.info("Daily metrics calculator initialized")
        
        Custom module name:
        
        >>> logger = get_logger("data_processing")
        >>> logger.debug("Processing health data batch")
    """
    return logging.getLogger(f"apple_health_monitor.{name}")


# Create a default logger instance
default_logger = setup_logging()


if __name__ == "__main__":
    # Test the logging configuration
    logger = setup_logging(log_level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test module-specific logger
    module_logger = get_logger("test_module")
    module_logger.info("This is from a specific module")
    
    print(f"\nLog files created in: {Path(__file__).parent.parent.parent / 'logs'}")