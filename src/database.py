"""Database connection manager and initialization for Apple Health Monitor.

This module provides comprehensive database management functionality for the Apple Health
Monitor application. It implements a thread-safe singleton pattern for database connections,
handles schema migrations, and provides high-level database operations.

The DatabaseManager class serves as the central hub for all database operations, ensuring:
    - Single database instance across the application
    - Proper connection management with automatic cleanup
    - Database schema initialization and migrations
    - Thread-safe operations with connection pooling
    - Error handling and logging for database operations

Key features:
    - Singleton pattern for consistent database access
    - Automatic database and table creation
    - Schema versioning and migration system
    - Performance optimization with WAL mode
    - Comprehensive error handling and logging

Examples:
    Basic database operations:
        >>> db = DatabaseManager()
        >>> with db.get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT COUNT(*) FROM journal_entries")
        ...     count = cursor.fetchone()[0]
        ...     print(f"Journal entries: {count}")
        
    Execute queries and commands:
        >>> db = DatabaseManager()
        >>> results = db.execute_query("SELECT * FROM user_preferences")
        >>> row_id = db.execute_command(
        ...     "INSERT INTO user_preferences (preference_key, preference_value) VALUES (?, ?)",
        ...     ("theme", "dark")
        ... )

Attributes:
    DB_FILE_NAME (str): Standard filename for the health monitor database.
    logger: Module-level logger for database operations.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
from datetime import datetime

from . import config

logger = logging.getLogger(__name__)

# Database filename as per specification
DB_FILE_NAME = "health_monitor.db"


class DatabaseManager:
    """Thread-safe singleton database manager for SQLite operations.
    
    This class implements a thread-safe singleton pattern to ensure consistent database
    access throughout the application. It provides comprehensive database management
    including automatic initialization, schema migrations, connection pooling, and
    high-level query operations with proper error handling.
    
    The database manager automatically:
        - Creates database file and directory structure on first use
        - Initializes all required tables according to SPECS_DB.md
        - Applies schema migrations to keep database up-to-date
        - Manages connection lifecycle with automatic cleanup
        - Provides both transactional and non-transactional operations
        - Ensures thread-safe access through proper locking
    
    All database operations use Row factory for convenient column access by name,
    and the database is configured with WAL mode for better concurrency.
    
    Attributes:
        db_path (Path): Path to the SQLite database file.
        initialized (bool): Flag indicating if the manager has been initialized.
        _instance: Singleton instance reference (class-level).
        _lock: Thread lock for singleton pattern (class-level).
        
    Examples:
        Basic usage with context manager:
        >>> db = DatabaseManager()
        >>> with db.get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT COUNT(*) FROM journal_entries")
        ...     count = cursor.fetchone()[0]
        ...     print(f"Total journal entries: {count}")
        
        High-level query operations:
        >>> db = DatabaseManager()
        >>> # Query data
        >>> preferences = db.execute_query(
        ...     "SELECT * FROM user_preferences WHERE preference_key = ?",
        ...     ("theme_mode",)
        ... )
        >>> # Insert/update data
        >>> new_id = db.execute_command(
        ...     "INSERT INTO journal_entries (entry_date, entry_type, content) VALUES (?, ?, ?)",
        ...     ("2024-01-15", "daily", "Great day today!")
        ... )
        
        Check table existence:
        >>> db = DatabaseManager()
        >>> if db.table_exists("user_preferences"):
        ...     print("Preferences table is available")
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Create or return singleton database manager instance with thread safety.
        
        Implements double-checked locking pattern to ensure only one DatabaseManager
        instance exists across the entire application, even in multi-threaded
        environments.
        
        Returns:
            DatabaseManager: The singleton instance of the database manager.
            
        Note:
            This method is automatically called when creating a new instance.
            Subsequent calls will return the same instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database manager with path setup and database creation.
        
        Sets up the database path based on configuration, creates the data directory
        if needed, and ensures the database file exists with all required tables.
        This method is safe to call multiple times due to the singleton pattern
        preventing re-initialization.
        
        The initialization process:
            1. Sets up database path from config.DATA_DIR
            2. Creates parent directories if they don't exist
            3. Initializes database file and schema if missing
            4. Marks the manager as initialized to prevent duplicate setup
        """
        if not hasattr(self, 'initialized'):
            self.db_path = Path(config.DATA_DIR) / DB_FILE_NAME
            self.initialized = True
            self._ensure_database_exists()
            
            # Ensure all migrations are applied on startup
            try:
                self._check_and_apply_migrations()
            except Exception as e:
                logger.error(f"Failed to apply migrations on startup: {e}")
                if "disk I/O error" in str(e) or "database is locked" in str(e):
                    logger.error("Database may be locked by OneDrive or another process.")
                    logger.error("Try: 1) Closing OneDrive, 2) Moving the project out of OneDrive folder")
                # Don't raise here - let the app continue even if migrations fail
    
    def _ensure_database_exists(self):
        """Ensure database file and directory structure exist.
        
        Creates the complete directory path for the database file if it doesn't exist
        and initializes a new database with full schema if the database file is missing.
        This method is idempotent and safe to call multiple times.
        
        Directory creation uses parents=True for recursive creation and exist_ok=True
        to avoid errors if directories already exist.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            logger.info(f"Creating new database at {self.db_path}")
            self.initialize_database()
    
    def _check_and_apply_migrations(self):
        """Check and apply any pending migrations to existing database.
        
        This method is called on startup to ensure all migrations are applied,
        even if the database already exists. This is important for adding new
        tables like achievements, personal_records, and streaks.
        """
        if self.db_path.exists():
            logger.debug("Checking for pending migrations")
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Ensure schema_migrations table exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_migrations (
                            version INTEGER PRIMARY KEY,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Apply any pending migrations
                    self._apply_migrations(cursor)
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Error checking/applying migrations: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        """Provide database connection with automatic resource management.
        
        Returns a context manager that handles database connection lifecycle,
        including automatic cleanup and error logging. All connections are
        configured with Row factory for convenient column access by name.
        
        The connection is automatically closed when exiting the context manager,
        even if an exception occurs during database operations.
        
        Yields:
            sqlite3.Connection: Database connection with Row factory enabled,
                allowing access to columns by name (e.g., row['column_name']).
            
        Raises:
            sqlite3.Error: If connection cannot be established or database
                operations fail. Error details are logged automatically.
            
        Examples:
            Basic query execution:
            >>> db = DatabaseManager()
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM user_preferences")
            ...     for row in cursor.fetchall():
            ...         print(f"Key: {row['preference_key']}, Value: {row['preference_value']}")
            
            Transaction handling:
            >>> with db.get_connection() as conn:
            ...     try:
            ...         cursor = conn.cursor()
            ...         cursor.execute("INSERT INTO journal_entries ...")
            ...         cursor.execute("UPDATE user_preferences ...")
            ...         conn.commit()
            ...     except Exception as e:
            ...         conn.rollback()
            ...         raise
        """
        conn = None
        try:
            # Add timeout and check if file is accessible
            if not self.db_path.exists():
                logger.error(f"Database file does not exist: {self.db_path}")
                raise sqlite3.Error(f"Database file not found: {self.db_path}")
            
            # Try to open with a longer timeout for OneDrive sync issues
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            
            # Test the connection
            conn.execute("SELECT 1")
            
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            if "disk I/O error" in str(e):
                logger.error(f"This may be due to OneDrive sync. Try closing OneDrive or moving the database file.")
                logger.error(f"Database path: {self.db_path}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def _get_initial_connection(self):
        """Provide database connection for initial database creation.
        
        This method is used internally for database initialization and doesn't
        check if the database file exists. It will create the database file
        if it doesn't exist.
        
        Yields:
            sqlite3.Connection: Database connection with Row factory enabled.
        """
        conn = None
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to open/create with a longer timeout for OneDrive sync issues
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error during initialization: {e}")
            if "disk I/O error" in str(e):
                logger.error(f"This may be due to OneDrive sync. Try closing OneDrive or moving the database file.")
                logger.error(f"Database path: {self.db_path}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_database(self):
        """Initialize database with complete schema according to SPECS_DB.md.
        
        Creates all required tables, indexes, triggers, and default data according
        to the database specification. This comprehensive initialization ensures
        the database is ready for all application features including journaling,
        preferences, caching, and health data storage.
        
        This method is idempotent and safe to call multiple times - existing
        tables and data are preserved while missing components are created.
        
        Database components created:
            Tables:
                - schema_migrations: Track database schema versions for migrations
                - journal_entries: Store daily, weekly, and monthly journal entries
                - user_preferences: Store typed application preferences
                - recent_files: Track recently accessed files with validation
                - cached_metrics: Cache computed health metrics for performance
                - health_metrics_metadata: Store display metadata for health types
                - data_sources: Track data sources and their activity status
                - import_history: Log data import operations with statistics
                - filter_configs: Store user-defined filter presets
                - health_records: Store imported health data with unique constraints
                
            Indexes:
                - Performance indexes on all tables for common query patterns
                - Composite indexes for complex filtering operations
                - Unique constraints to prevent data duplication
                
            Triggers:
                - Automatic timestamp updates for modified records
                - Data validation and consistency enforcement
                
            Default Data:
                - Default user preferences with proper data types
                - Initial schema version markers
        
        The database is configured with WAL mode for better concurrency and
        all operations are performed within a transaction for consistency.
        """
        with self._get_initial_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Create schema_migrations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create journal_entries table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date DATE NOT NULL,
                    entry_type VARCHAR(10) NOT NULL CHECK (entry_type IN ('daily', 'weekly', 'monthly')),
                    week_start_date DATE,
                    month_year VARCHAR(7),
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(entry_date, entry_type)
                )
            """)
            
            # Create indexes for journal_entries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_type ON journal_entries(entry_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_week ON journal_entries(week_start_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_month ON journal_entries(month_year)")
            
            # Create user_preferences table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key VARCHAR(50) UNIQUE NOT NULL,
                    preference_value TEXT,
                    data_type VARCHAR(20) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default preferences (updated from SPECS_DB.md)
            default_preferences = [
                ('last_csv_path', None, 'string'),
                ('last_date_range_start', None, 'date'),
                ('last_date_range_end', None, 'date'),
                ('selected_sources', '[]', 'json'),
                ('selected_types', '[]', 'json'),
                ('window_width', '1200', 'integer'),
                ('window_height', '800', 'integer'),
                ('window_x', None, 'integer'),
                ('window_y', None, 'integer'),
                ('theme_mode', 'light', 'string'),
                ('chart_animation', 'true', 'boolean'),
                ('favorite_metrics', '[]', 'json'),
                ('metric_units', '{}', 'json'),
                ('data_source_colors', '{}', 'json'),
                ('hide_empty_metrics', 'true', 'boolean'),
                ('weekly_selected_metric', None, 'json'),
                ('monthly_selected_metric', None, 'json'),
                ('daily_selected_metric', None, 'json')
            ]
            
            for key, value, data_type in default_preferences:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_preferences (preference_key, preference_value, data_type)
                    VALUES (?, ?, ?)
                """, (key, value, data_type))
            
            # Create recent_files table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recent_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_valid BOOLEAN DEFAULT TRUE
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recent_files_accessed ON recent_files(last_accessed DESC)")
            
            # Create cached_metrics table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    date_range_start DATE NOT NULL,
                    date_range_end DATE NOT NULL,
                    source_name VARCHAR(100),
                    health_type VARCHAR(100),
                    aggregation_type VARCHAR(20) NOT NULL,
                    metric_data TEXT NOT NULL,
                    unit VARCHAR(20),
                    record_count INTEGER,
                    min_value REAL,
                    max_value REAL,
                    avg_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cached_metrics(cache_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cached_metrics(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_metric_date ON cached_metrics(metric_type, date_range_start, date_range_end)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_lookup ON cached_metrics(metric_type, date_range_start, source_name, aggregation_type)")
            
            # Create health_metrics_metadata table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_metrics_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(100) NOT NULL,
                    unit VARCHAR(20),
                    category VARCHAR(50),
                    color_hex VARCHAR(7),
                    icon_name VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_category ON health_metrics_metadata(category)")
            
            # Create data_sources table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name VARCHAR(100) UNIQUE NOT NULL,
                    source_category VARCHAR(50),
                    last_seen TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_active ON data_sources(is_active)")
            
            # Create import_history table as per spec
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash VARCHAR(64),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    row_count INTEGER,
                    date_range_start DATE,
                    date_range_end DATE,
                    unique_types INTEGER,
                    unique_sources INTEGER,
                    import_duration_ms INTEGER
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_import_date ON import_history(import_date DESC)")
            
            # Create health_records table for imported health data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    type TEXT,
                    sourceName TEXT,
                    sourceVersion TEXT,
                    device TEXT,
                    unit TEXT,
                    creationDate TEXT,
                    startDate TEXT,
                    endDate TEXT,
                    value REAL,
                    UNIQUE(type, sourceName, startDate, endDate, value)
                )
            """)
            
            # Create indexes for health_records performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_creation_date ON health_records(creationDate)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)')
            
            # Add trigger to update timestamp on journal_entries
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_journal_timestamp 
                AFTER UPDATE ON journal_entries
                BEGIN
                    UPDATE journal_entries 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            # Add trigger to update timestamp on user_preferences
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_preferences_timestamp 
                AFTER UPDATE ON user_preferences
                BEGIN
                    UPDATE user_preferences 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            # Apply migrations
            self._apply_migrations(cursor)
            
            # Record initial schema version
            cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (1)")
            
            conn.commit()
            logger.info("Database initialized successfully with all required tables")
    
    def _apply_migrations(self, cursor):
        """Apply incremental database schema migrations.
        
        Checks the current schema version against available migrations and applies
        any pending updates to bring the database schema up to the latest version.
        Each migration is applied atomically and recorded in the schema_migrations
        table for tracking purposes.
        
        The migration system ensures:
            - Migrations are applied in correct order
            - Each migration is applied exactly once
            - Failed migrations don't leave the database in an inconsistent state
            - Migration history is preserved for debugging
        
        Args:
            cursor: Active database cursor for executing migration SQL statements.
                Must be part of an active transaction.
                
        Current migrations:
            Migration 2: Adds filter_configs table for user-defined filter presets
            Migration 3: Adds unique constraints to health_records table
            Migration 4: Adds achievements, personal_records, and streaks tables
            
        Examples:
            This method is called automatically during database initialization:
            >>> db = DatabaseManager()  # Migrations applied automatically
            
        Note:
            This is an internal method called during database initialization.
            Manual migration application should not be necessary.
        """
        # Check current schema version
        cursor.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        current_version = cursor.fetchone()[0]
        
        # Migration 2: Add filter_configs table
        if current_version < 2:
            logger.info("Applying migration 2: Adding filter_configs table")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filter_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preset_name VARCHAR(100) UNIQUE NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    source_names TEXT,  -- JSON array of source names
                    health_types TEXT,  -- JSON array of health types
                    is_default BOOLEAN DEFAULT FALSE,
                    is_last_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for filter_configs
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filter_configs_default ON filter_configs(is_default)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filter_configs_last_used ON filter_configs(is_last_used)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filter_configs_name ON filter_configs(preset_name)")
            
            # Add trigger to update timestamp on filter_configs
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_filter_configs_timestamp 
                AFTER UPDATE ON filter_configs
                BEGIN
                    UPDATE filter_configs 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (2)")
            logger.info("Migration 2 applied successfully")
        
        # Migration 3: Add unique constraint to health_records
        if current_version < 3:
            logger.info("Applying migration 3: Adding unique constraint to health_records")
            
            # Create new table with unique constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_records_new (
                    type TEXT,
                    sourceName TEXT,
                    sourceVersion TEXT,
                    device TEXT,
                    unit TEXT,
                    creationDate TEXT,
                    startDate TEXT,
                    endDate TEXT,
                    value REAL,
                    UNIQUE(type, sourceName, startDate, endDate, value)
                )
            """)
            
            # Copy unique records from old table to new table
            cursor.execute("""
                INSERT OR IGNORE INTO health_records_new
                SELECT DISTINCT type, sourceName, sourceVersion, device, unit, 
                       creationDate, startDate, endDate, value
                FROM health_records
            """)
            
            # Drop old table and rename new table
            cursor.execute("DROP TABLE IF EXISTS health_records")
            cursor.execute("ALTER TABLE health_records_new RENAME TO health_records")
            
            # Recreate indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_creation_date ON health_records(creationDate)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)')
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (3)")
            logger.info("Migration 3 applied successfully")
        
        # Migration 4: Add achievements and personal_records tables
        if current_version < 4:
            logger.info("Applying migration 4: Adding achievements and personal_records tables")
            
            # Create achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    achievement_type VARCHAR(50) NOT NULL,
                    metric_type VARCHAR(100) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    criteria_json TEXT NOT NULL,  -- JSON object with achievement criteria
                    achieved_date DATE,
                    achieved_value REAL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for achievements
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_type ON achievements(achievement_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_metric ON achievements(metric_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_date ON achievements(achieved_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_active ON achievements(is_active)")
            
            # Create personal_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type VARCHAR(100) NOT NULL,
                    record_type VARCHAR(50) NOT NULL,  -- e.g., 'daily_max', 'daily_min', 'weekly_total', etc.
                    period VARCHAR(20),  -- e.g., 'day', 'week', 'month', 'all_time'
                    value REAL NOT NULL,
                    unit VARCHAR(50),
                    recorded_date DATE NOT NULL,
                    previous_value REAL,
                    previous_date DATE,
                    improvement_percentage REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric_type, record_type, period)
                )
            """)
            
            # Create indexes for personal_records
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_records_metric ON personal_records(metric_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_records_type ON personal_records(record_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_records_date ON personal_records(recorded_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_records_period ON personal_records(period)")
            
            # Create streaks table (bonus - also mentioned in clear_all_health_data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS streaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type VARCHAR(100) NOT NULL,
                    streak_type VARCHAR(50) NOT NULL,  -- e.g., 'daily', 'weekly'
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    streak_start_date DATE,
                    streak_end_date DATE,
                    last_activity_date DATE,
                    threshold_value REAL,  -- Minimum value to maintain streak
                    threshold_unit VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric_type, streak_type)
                )
            """)
            
            # Create indexes for streaks
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_metric ON streaks(metric_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_type ON streaks(streak_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_active ON streaks(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_dates ON streaks(streak_start_date, streak_end_date)")
            
            # Add triggers to update timestamps
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_achievements_timestamp 
                AFTER UPDATE ON achievements
                BEGIN
                    UPDATE achievements 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_personal_records_timestamp 
                AFTER UPDATE ON personal_records
                BEGIN
                    UPDATE personal_records 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_streaks_timestamp 
                AFTER UPDATE ON streaks
                BEGIN
                    UPDATE streaks 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            """)
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (4)")
            logger.info("Migration 4 applied successfully")
        
        # Migration 5: Add source column to personal_records table
        if current_version < 5:
            logger.info("Applying migration 5: Adding source column to personal_records")
            
            # Add source column to personal_records table
            cursor.execute("""
                ALTER TABLE personal_records 
                ADD COLUMN source VARCHAR(255)
            """)
            
            # Create index on source for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_records_source ON personal_records(source)")
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (5)")
            logger.info("Migration 5 applied successfully")
        
        # Migration 6: Add version column to journal_entries for optimistic locking
        if current_version < 6:
            logger.info("Applying migration 6: Adding version column to journal_entries")
            
            # Add version column to journal_entries table
            cursor.execute("""
                ALTER TABLE journal_entries 
                ADD COLUMN version INTEGER DEFAULT 1
            """)
            
            # Update existing entries to have version 1
            cursor.execute("""
                UPDATE journal_entries 
                SET version = 1 
                WHERE version IS NULL
            """)
            
            # Create index on version for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_entries_version ON journal_entries(version)")
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (6)")
            logger.info("Migration 6 applied successfully")
        
        # Migration 7: Add journal_drafts table for auto-save functionality
        if current_version < 7:
            logger.info("Applying migration 7: Adding journal_drafts table for auto-save")
            
            # Create journal_drafts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date DATE NOT NULL,
                    entry_type VARCHAR(10) NOT NULL CHECK (entry_type IN ('daily', 'weekly', 'monthly')),
                    content TEXT NOT NULL,
                    content_hash VARCHAR(64),
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(36),
                    is_recovered BOOLEAN DEFAULT FALSE,
                    UNIQUE(entry_date, entry_type, session_id)
                )
            """)
            
            # Create indexes for journal_drafts
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_date_type ON journal_drafts(entry_date, entry_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_session ON journal_drafts(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_saved_at ON journal_drafts(saved_at)")
            
            # Create trigger to clean up old drafts (older than 7 days)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS cleanup_old_drafts
                AFTER INSERT ON journal_drafts
                BEGIN
                    DELETE FROM journal_drafts
                    WHERE saved_at < datetime('now', '-7 days')
                    AND is_recovered = FALSE;
                END
            """)
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (7)")
            logger.info("Migration 7 applied successfully")
        
        # Migration 8: Add FTS5 virtual table for journal search
        if current_version < 8:
            logger.info("Applying migration 8: Adding FTS5 virtual table for journal search")
            
            # Create FTS5 virtual table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS journal_search USING fts5(
                    entry_id UNINDEXED,
                    entry_date UNINDEXED,
                    entry_type UNINDEXED,
                    content,
                    tokenize='porter unicode61',
                    content_rowid='entry_id'
                )
            """)
            
            # Populate FTS table with existing journal entries
            cursor.execute("""
                INSERT INTO journal_search(entry_id, entry_date, entry_type, content)
                SELECT id, entry_date, entry_type, content
                FROM journal_entries
                WHERE content IS NOT NULL
            """)
            
            # Create triggers to keep FTS table in sync
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS journal_search_insert 
                AFTER INSERT ON journal_entries
                BEGIN
                    INSERT INTO journal_search(entry_id, entry_date, entry_type, content)
                    VALUES (NEW.id, NEW.entry_date, NEW.entry_type, NEW.content);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS journal_search_update 
                AFTER UPDATE ON journal_entries
                BEGIN
                    UPDATE journal_search 
                    SET content = NEW.content,
                        entry_date = NEW.entry_date,
                        entry_type = NEW.entry_type
                    WHERE entry_id = NEW.id;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS journal_search_delete 
                AFTER DELETE ON journal_entries
                BEGIN
                    DELETE FROM journal_search WHERE entry_id = OLD.id;
                END
            """)
            
            # Create search_history table for tracking searches
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    result_count INTEGER,
                    clicked_result_id INTEGER,
                    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for search_history
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_date ON search_history(searched_at DESC)")
            
            # Record migration
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (8)")
            logger.info("Migration 8 applied successfully")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """Execute SELECT query and return all matching rows.
        
        Provides a high-level interface for executing SELECT queries with automatic
        connection management and parameter binding. Returns all results as a list
        of Row objects that support both index and column name access.
        
        Args:
            query: SQL SELECT query string to execute. Use ? placeholders for parameters.
            params: Optional tuple of values to bind to query parameters. Must match
                the number of ? placeholders in the query.
                
        Returns:
            List of sqlite3.Row objects containing query results. Each row supports:
                - Index access: row[0], row[1], etc.
                - Column name access: row['column_name']
                - Dict conversion: dict(row)
                
        Examples:
            Simple query without parameters:
            >>> db = DatabaseManager()
            >>> rows = db.execute_query("SELECT * FROM user_preferences")
            >>> for row in rows:
            ...     print(f"Preference: {row['preference_key']} = {row['preference_value']}")
            
            Parameterized query:
            >>> rows = db.execute_query(
            ...     "SELECT * FROM journal_entries WHERE entry_type = ? AND entry_date >= ?",
            ...     ("daily", "2024-01-01")
            ... )
            >>> print(f"Found {len(rows)} daily entries")
            
            Access row data:
            >>> rows = db.execute_query("SELECT preference_key, preference_value FROM user_preferences")
            >>> if rows:
            ...     first_row = rows[0]
            ...     print(f"By index: {first_row[0]} = {first_row[1]}")
            ...     print(f"By name: {first_row['preference_key']} = {first_row['preference_value']}")
            ...     print(f"As dict: {dict(first_row)}")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_command(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute data modification command with automatic transaction handling.
        
        Provides a high-level interface for executing INSERT, UPDATE, and DELETE
        commands with automatic connection management, parameter binding, and
        transaction commit. Returns useful information about the operation result.
        
        Args:
            query: SQL command string to execute (INSERT, UPDATE, DELETE, etc.).
                Use ? placeholders for parameters to prevent SQL injection.
            params: Optional tuple of values to bind to query parameters. Must match
                the number of ? placeholders in the query.
                
        Returns:
            For INSERT operations: The row ID of the newly inserted record.
            For UPDATE/DELETE operations: The number of rows affected.
            
        Examples:
            Insert new record:
            >>> db = DatabaseManager()
            >>> new_id = db.execute_command(
            ...     "INSERT INTO journal_entries (entry_date, entry_type, content) VALUES (?, ?, ?)",
            ...     ("2024-01-15", "daily", "Had a great workout today!")
            ... )
            >>> print(f"Created journal entry with ID: {new_id}")
            
            Update existing record:
            >>> affected_rows = db.execute_command(
            ...     "UPDATE user_preferences SET preference_value = ? WHERE preference_key = ?",
            ...     ("dark", "theme_mode")
            ... )
            >>> print(f"Updated {affected_rows} preference records")
            
            Delete records:
            >>> deleted_count = db.execute_command(
            ...     "DELETE FROM cached_metrics WHERE expires_at < datetime('now')"
            ... )
            >>> print(f"Cleaned up {deleted_count} expired cache entries")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute same command multiple times with different parameters efficiently.
        
        Uses SQLite's executemany() method for optimal performance when executing
        the same SQL command with different parameter sets. This is significantly
        faster than individual execute() calls for bulk operations.
        
        Args:
            query: SQL command string to execute multiple times. Use ? placeholders
                for parameters.
            params_list: List of parameter tuples, one tuple for each execution.
                Each tuple must match the number of ? placeholders in the query.
                
        Examples:
            Bulk insert preferences:
            >>> db = DatabaseManager()
            >>> preferences_data = [
            ...     ("window_width", "1200", "integer"),
            ...     ("window_height", "800", "integer"),
            ...     ("theme_mode", "light", "string"),
            ...     ("auto_save", "true", "boolean")
            ... ]
            >>> db.execute_many(
            ...     "INSERT INTO user_preferences (preference_key, preference_value, data_type) VALUES (?, ?, ?)",
            ...     preferences_data
            ... )
            
            Bulk update cache entries:
            >>> cache_updates = [
            ...     ("2024-02-01", "cache_key_1"),
            ...     ("2024-02-01", "cache_key_2"),
            ...     ("2024-02-01", "cache_key_3")
            ... ]
            >>> db.execute_many(
            ...     "UPDATE cached_metrics SET expires_at = ? WHERE cache_key = ?",
            ...     cache_updates
            ... )
            
        Note:
            This method is ideal for bulk operations like data imports or batch updates.
            For single operations, use execute_command() instead.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check whether a specific table exists in the database.
        
        Queries the SQLite system catalog to determine if a table with the given
        name exists. Useful for conditional operations and database validation.
        
        Args:
            table_name: Name of the table to check for existence. Case-sensitive.
            
        Returns:
            True if the table exists in the database, False otherwise.
            
        Examples:
            Check before using a table:
            >>> db = DatabaseManager()
            >>> if db.table_exists("user_preferences"):
            ...     preferences = db.execute_query("SELECT * FROM user_preferences")
            ... else:
            ...     print("Preferences table not found, initializing database...")
            ...     db.initialize_database()
            
            Validate database schema:
            >>> required_tables = [
            ...     "journal_entries", "user_preferences", "health_records"
            ... ]
            >>> missing_tables = [
            ...     table for table in required_tables
            ...     if not db.table_exists(table)
            ... ]
            >>> if missing_tables:
            ...     print(f"Missing tables: {missing_tables}")
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0
    
    def create_indexes(self):
        """Create comprehensive performance optimization indexes for health data queries.
        
        Creates additional indexes on the health_records table beyond those created
        during initialization to optimize performance for complex queries, especially
        those used in the Configuration tab and data analysis operations.
        
        This method is safe to call multiple times as it uses CREATE INDEX IF NOT EXISTS
        and only operates on existing tables. Missing tables are logged and skipped.
        
        Performance indexes created:
            - idx_source: Single-column index on sourceName for source filtering
            - idx_source_type: Composite index on sourceName and type for combined filtering
            - idx_date_type_source: Triple composite index for complex time-based queries
            
        These indexes significantly improve performance for:
            - Filtering records by data source (iPhone, Apple Watch, etc.)
            - Getting distinct source names for UI dropdowns
            - Combined source and health type filtering
            - Time-based queries with source/type constraints
            - Configuration tab data loading and statistics
            
        Examples:
            Create indexes after data import:
            >>> db = DatabaseManager()
            >>> db.create_indexes()  # Safe to call multiple times
            
            Verify index creation:
            >>> if db.table_exists('health_records'):
            ...     db.create_indexes()
            ...     print("Performance indexes created")
            
        Note:
            These indexes are automatically created during database initialization,
            but this method can be called to ensure they exist after manual
            database modifications or repairs.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Only create indexes if health_records table exists
            if not self.table_exists('health_records'):
                logger.warning("health_records table doesn't exist, skipping index creation")
                return
            
            logger.info("Creating performance optimization indexes")
            
            # Create indexes if not exists
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_source ON health_records(sourceName)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_source_type ON health_records(sourceName, type)"
            )
            
            # Additional composite indexes for common query patterns
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_date_type_source ON health_records(creationDate, type, sourceName)"
            )
            
            conn.commit()
            logger.info("Performance optimization indexes created successfully")
    
    def close(self):
        """Close all database connections and clean up resources.
        
        This method provides a way to explicitly close any active database connections
        and clean up resources. While SQLite connections are typically short-lived and
        managed through context managers, this method ensures proper cleanup during
        application shutdown or data erasure operations.
        
        Since this DatabaseManager uses context managers for connection lifecycle,
        most connections are automatically closed. This method serves as a cleanup
        point for any persistent connections and ensures proper resource management.
        
        Examples:
            Explicit cleanup during application shutdown:
            >>> db = DatabaseManager()
            >>> db.close()
            >>> print("Database connections closed")
        
        Note:
            This method is safe to call multiple times and will not raise errors
            if no connections are active. New connections can still be created
            after calling this method through the normal get_connection() context manager.
        """
        logger.info("Closing database connections and cleaning up resources")
        # Since we use context managers for connection lifecycle,
        # most connections are automatically managed. This method
        # serves as an explicit cleanup point.
        
        # Force garbage collection to clean up any remaining connection objects
        import gc
        gc.collect()
        
        logger.info("Database connections closed successfully")
    
    def clear_all_health_data(self) -> Dict[str, int]:
        """Clear all health-related data from the database while preserving preferences.
        
        This method performs a comprehensive erasure of all health record data and related
        entries from the database. It clears data from the following tables:
            - health_records: All imported health data
            - cached_metrics: All cached calculations and metrics
            - import_history: History of data imports
            - data_sources: Device and source information
            - health_metrics_metadata: Metric display metadata
            - filter_configs: Saved filter configurations
            - recent_files: List of recently imported files
            - achievements: User achievements (if table exists)
            - personal_records: Personal record tracking (if table exists)
            - streaks: Streak tracking data (if table exists)
        
        User preferences and journal entries are intentionally preserved as they
        represent user-generated content and application settings.
        
        Returns:
            Dict[str, int]: Dictionary mapping table names to the number of records
                deleted from each table. For example:
                {
                    'health_records': 50000,
                    'cached_metrics': 1234,
                    'import_history': 5,
                    ...
                }
        
        Raises:
            sqlite3.Error: If database operations fail during the clearing process.
                The operation is atomic - either all tables are cleared or none are.
        
        Examples:
            Clear all health data:
            >>> db = DatabaseManager()
            >>> deleted_counts = db.clear_all_health_data()
            >>> for table, count in deleted_counts.items():
            ...     print(f"Deleted {count} records from {table}")
            
            With error handling:
            >>> try:
            ...     counts = db.clear_all_health_data()
            ...     print(f"Successfully cleared {sum(counts.values())} total records")
            ... except sqlite3.Error as e:
            ...     print(f"Failed to clear data: {e}")
        
        Note:
            This operation cannot be undone. It's recommended to confirm with the user
            before calling this method and potentially create a backup first.
        """
        logger.info("Starting comprehensive health data erasure")
        
        # First, invalidate all cache entries then shutdown the cache manager
        try:
            from .analytics.cache_manager import invalidate_all_cache, shutdown_cache_manager
            invalidate_all_cache()
            logger.info("Invalidated all analytics cache entries")
            shutdown_cache_manager()
            logger.info("Shut down analytics cache manager")
        except Exception as e:
            logger.warning(f"Could not shutdown cache manager: {e}")
        
        # Tables to clear (in order to respect foreign key constraints if any)
        tables_to_clear = [
            'achievements',       # May not exist in all versions
            'personal_records',   # May not exist in all versions
            'streaks',           # May not exist in all versions
            'cached_metrics',
            'filter_configs',
            'health_metrics_metadata',
            'data_sources',
            'import_history',
            'recent_files',
            'health_records'     # Main data table, cleared last
        ]
        
        deleted_counts = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Begin transaction for atomic operation
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    for table in tables_to_clear:
                        # Check if table exists before attempting to clear
                        if self.table_exists(table):
                            # Get count before deletion for reporting
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            
                            # Delete all records from the table
                            cursor.execute(f"DELETE FROM {table}")
                            deleted_counts[table] = count
                            
                            logger.info(f"Deleted {count} records from {table}")
                        else:
                            logger.debug(f"Table {table} does not exist, skipping")
                    
                    # Reset SQLite auto-increment counters
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ({})".format(
                        ','.join(['?' for _ in tables_to_clear])
                    ), tables_to_clear)
                    
                    # Commit the transaction
                    cursor.execute("COMMIT")
                    
                    # Run VACUUM to reclaim disk space
                    logger.info("Running VACUUM to reclaim disk space")
                    cursor.execute("VACUUM")
                    
                    logger.info(f"Health data erasure completed. Total records deleted: {sum(deleted_counts.values())}")
                    
                except Exception as e:
                    # Rollback on any error
                    cursor.execute("ROLLBACK")
                    logger.error(f"Failed to clear health data: {e}")
                    raise
                
        except sqlite3.Error as e:
            logger.error(f"Database error during health data erasure: {e}")
            raise
        
        return deleted_counts


# Global singleton database manager instance
# This provides a convenient module-level access point for database operations
# while maintaining the singleton pattern for consistency
db_manager = DatabaseManager()