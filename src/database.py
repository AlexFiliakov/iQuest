"""Database connection manager and initialization for Apple Health Monitor."""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
from datetime import datetime

import config

logger = logging.getLogger(__name__)

# Database filename as per specification
DB_FILE_NAME = "health_monitor.db"


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single database manager instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database manager."""
        if not hasattr(self, 'initialized'):
            self.db_path = Path(config.DATA_DIR) / DB_FILE_NAME
            self.initialized = True
            self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file and directory exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            logger.info(f"Creating new database at {self.db_path}")
            self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
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
        """Initialize database with required tables as per SPECS_DB.md."""
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
        """Apply database migrations."""
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
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_command(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE command."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute multiple commands efficiently."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0


# Global database manager instance
db_manager = DatabaseManager()