"""Configuration constants for the Apple Health Monitor Dashboard."""

# Application metadata
APP_NAME = "Apple Health Monitor Dashboard"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Apple Health Monitor Team"

# Window settings
WINDOW_TITLE = APP_NAME
WINDOW_MIN_WIDTH = 1024
WINDOW_MIN_HEIGHT = 768
WINDOW_DEFAULT_WIDTH = 1440
WINDOW_DEFAULT_HEIGHT = 900

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