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
        # Normal installation mode - prioritize Windows AppData
        # Check if we're running on Windows (including WSL accessing Windows filesystem)
        current_path = os.path.abspath(__file__)
        
        # Detect if we're in WSL accessing Windows filesystem
        if current_path.startswith('/mnt/c/') or current_path.startswith('/mnt/d/'):
            # Running in WSL but on Windows filesystem
            # Convert WSL path to Windows path and use Windows AppData
            drive_letter = current_path[5]  # Get drive letter from /mnt/X/
            windows_user_path = current_path.split('Users/')[1].split('/')[0] if 'Users/' in current_path else None
            
            if windows_user_path:
                # Construct Windows AppData path
                windows_appdata_path = f"/mnt/{drive_letter}/Users/{windows_user_path}/AppData/Local/AppleHealthMonitor"
                os.makedirs(windows_appdata_path, exist_ok=True)
                return windows_appdata_path
        
        # Pure Windows environment
        if sys.platform == 'win32':
            # Windows: Use AppData/Local
            app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
            if app_data:
                data_dir = os.path.join(app_data, 'AppleHealthMonitor')
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
        
        # Fallback for Linux/Mac or when AppData isn't available
        # Use user's home directory
        home_dir = os.path.expanduser('~')
        data_dir = os.path.join(home_dir, '.apple_health_monitor')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

# Set the DATA_DIR based on the current mode
DATA_DIR = get_data_directory()

BATCH_SIZE = 1000

# UI timing
REFRESH_INTERVAL_MS = 200
STATUS_MESSAGE_TIMEOUT_MS = 5000