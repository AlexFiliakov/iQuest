"""Configuration constants for the Apple Health Monitor Dashboard.

This module contains all configuration constants used throughout the Apple Health
Monitor Dashboard application, including window settings, file handling parameters,
database configuration, and UI timing constants.

Attributes:
    APP_NAME (str): The application name displayed in the UI.
    APP_VERSION (str): Current version of the application.
    ORGANIZATION_NAME (str): Organization name for settings persistence.
    WINDOW_TITLE (str): Default window title.
    WINDOW_MIN_WIDTH (int): Minimum window width in pixels.
    WINDOW_MIN_HEIGHT (int): Minimum window height in pixels.
    WINDOW_DEFAULT_WIDTH (int): Default window width in pixels.
    WINDOW_DEFAULT_HEIGHT (int): Default window height in pixels.
    MAX_CSV_SIZE_MB (int): Maximum allowed CSV file size in megabytes.
    SUPPORTED_FILE_TYPES (List[str]): List of supported file extensions.
    DB_FILE_NAME (str): Default database filename.
    DATA_DIR (str): Directory for storing database and user data.
    BATCH_SIZE (int): Default batch size for database operations.
    REFRESH_INTERVAL_MS (int): UI refresh interval in milliseconds.
    STATUS_MESSAGE_TIMEOUT_MS (int): Status message display timeout in milliseconds.

Example:
    Import and use configuration constants:
    
    >>> from src.config import APP_NAME, WINDOW_DEFAULT_WIDTH
    >>> print(f"Starting {APP_NAME}")
    >>> window.resize(WINDOW_DEFAULT_WIDTH, 600)
"""

# Application metadata
APP_NAME = "Apple Health Monitor Dashboard"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Apple Health Monitor Team"

# Window settings
WINDOW_TITLE = APP_NAME
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 700

# File settings
MAX_CSV_SIZE_MB = 500
SUPPORTED_FILE_TYPES = ["csv", "xml"]

# Database settings
DB_FILE_NAME = "health_monitor.db"  # As per SPECS_DB.md
DATA_DIR = "data"  # Directory for storing database and user data
BATCH_SIZE = 1000

# UI timing
REFRESH_INTERVAL_MS = 200
STATUS_MESSAGE_TIMEOUT_MS = 5000