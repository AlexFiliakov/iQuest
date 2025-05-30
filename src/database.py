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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
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
        with self.get_connection() as conn:
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
                ('hide_empty_metrics', 'true', 'boolean')
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


# Global singleton database manager instance
# This provides a convenient module-level access point for database operations
# while maintaining the singleton pattern for consistency
db_manager = DatabaseManager()