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
    MIN_MEMORY_LIMIT_MB (int): Minimum memory limit for XML streaming processor.
    MAX_MEMORY_LIMIT_MB (int): Maximum memory limit for XML streaming processor.
    DEFAULT_MEMORY_LIMIT_MB (int): Default memory limit for XML streaming processor.
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

# Memory settings for XML streaming processor
MIN_MEMORY_LIMIT_MB = 256  # Minimum memory limit for streaming processor
MAX_MEMORY_LIMIT_MB = 4096  # Maximum memory limit (4GB)
DEFAULT_MEMORY_LIMIT_MB = 1024  # Default memory limit for streaming processor (1GB)

# Database settings
import os
import sys
import tempfile
import shutil

DB_FILE_NAME = "health_monitor.db"  # As per SPECS_DB.md

def is_portable_mode():
    """Check if running in portable mode.
    
    Portable mode is detected by the presence of a 'portable.marker' file
    in the same directory as the executable.
    
    Returns:
        bool: True if running in portable mode, False otherwise.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running from source
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.exists(os.path.join(app_dir, 'portable.marker'))

def get_data_directory():
    """Get appropriate data directory based on mode.
    
    In portable mode, data is stored alongside the executable.
    In normal mode, data is stored in the user's AppData directory.
    
    Returns:
        str: Path to the data directory.
    """
    if is_portable_mode():
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running from source
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        data_dir = os.path.join(app_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    else:
        # Normal installation mode
        if sys.platform == 'win32':
            # Windows: Use AppData/Local
            app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
            if app_data:
                data_dir = os.path.join(app_data, 'AppleHealthMonitor')
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
        
        # Fallback to original logic for development
        _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _ORIGINAL_DATA_DIR = os.path.join(_BASE_DIR, "data")
        
        # Check if we're in OneDrive path
        if "OneDrive" in _ORIGINAL_DATA_DIR:
            # Create a temporary data directory outside OneDrive
            _TEMP_DATA_DIR = os.path.join(tempfile.gettempdir(), "apple_health_monitor_data")
            os.makedirs(_TEMP_DATA_DIR, exist_ok=True)
            
            # Copy database if it exists and needs updating
            _original_db = os.path.join(_ORIGINAL_DATA_DIR, DB_FILE_NAME)
            _temp_db = os.path.join(_TEMP_DATA_DIR, DB_FILE_NAME)
            
            if os.path.exists(_original_db):
                try:
                    # Only copy if temp doesn't exist or is older
                    if not os.path.exists(_temp_db) or os.path.getmtime(_original_db) > os.path.getmtime(_temp_db):
                        print(f"Copying database from OneDrive to temp location: {_temp_db}")
                        shutil.copy2(_original_db, _temp_db)
                except Exception as e:
                    print(f"Warning: Could not copy database: {e}")
            
            return _TEMP_DATA_DIR
        else:
            return _ORIGINAL_DATA_DIR

# Set the DATA_DIR based on the current mode
DATA_DIR = get_data_directory()

BATCH_SIZE = 1000

# UI timing
REFRESH_INTERVAL_MS = 200
STATUS_MESSAGE_TIMEOUT_MS = 5000