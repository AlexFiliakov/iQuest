"""
Database test factory for creating isolated test databases.
Provides both in-memory and temporary file databases with proper schema initialization.
"""

import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
import pytest


class TestDatabaseFactory:
    """Factory for creating test databases with proper isolation."""
    
    @staticmethod
    @contextmanager
    def in_memory_db():
        """Create in-memory database for unit tests."""
        conn = sqlite3.connect(':memory:')
        try:
            TestDatabaseFactory._init_schema(conn)
            yield conn
        finally:
            conn.close()
    
    @staticmethod
    @contextmanager
    def temp_file_db():
        """Create temporary file database for integration tests."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = Path(tmp.name)
        
        try:
            conn = sqlite3.connect(str(db_path))
            TestDatabaseFactory._init_schema(conn)
            yield conn, db_path
        finally:
            conn.close()
            db_path.unlink(missing_ok=True)
    
    @staticmethod
    def _init_schema(conn):
        """Initialize database schema for tests."""
        conn.executescript('''
            -- Cache entries table for analytics cache manager
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                size_bytes INTEGER,
                dependencies TEXT,
                ttl_seconds INTEGER,
                expires_at TIMESTAMP
            );
            
            -- Health data table for general testing
            CREATE TABLE IF NOT EXISTS health_data (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                UNIQUE(date, metric)
            );
            
            -- Journal entries table
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date DATE NOT NULL,
                entry_type TEXT NOT NULL CHECK (entry_type IN ('daily', 'weekly')),
                content TEXT NOT NULL,
                week_start_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entry_date, entry_type)
            );
            
            -- User preferences table
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_key TEXT PRIMARY KEY,
                preference_value TEXT NOT NULL,
                data_type TEXT NOT NULL CHECK (data_type IN ('string', 'integer', 'boolean', 'json')),
                description TEXT,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Recent files table
            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size_bytes INTEGER,
                record_count INTEGER
            );
            
            -- Cached metrics table
            CREATE TABLE IF NOT EXISTS cached_metrics (
                cache_key TEXT PRIMARY KEY,
                metric_type TEXT NOT NULL,
                date_range_start DATE NOT NULL,
                date_range_end DATE NOT NULL,
                aggregation_type TEXT NOT NULL,
                source_name TEXT,
                metric_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Schema migrations table
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);
            CREATE INDEX IF NOT EXISTS idx_cache_created ON cache_entries(created_at);
            CREATE INDEX IF NOT EXISTS idx_health_date ON health_data(date);
            CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date);
            CREATE INDEX IF NOT EXISTS idx_journal_type ON journal_entries(entry_type);
            CREATE INDEX IF NOT EXISTS idx_recent_opened ON recent_files(last_opened);
            CREATE INDEX IF NOT EXISTS idx_cached_expires ON cached_metrics(expires_at);
            CREATE INDEX IF NOT EXISTS idx_cached_type_date ON cached_metrics(metric_type, date_range_start, date_range_end);
        ''')
        conn.commit()