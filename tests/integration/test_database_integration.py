"""Integration tests for database functionality."""

import pytest
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

# Import database modules
from database import DatabaseManager, DB_FILE_NAME
from data_access import JournalDAO, PreferenceDAO, CacheDAO, MetricsMetadataDAO
from models import JournalEntry, UserPreference, CachedMetric


class TestDatabaseIntegration:
    """Test database functionality without PyQt6 dependency."""
    
    @pytest.fixture
    def temp_db(self, monkeypatch):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset singleton
            DatabaseManager._instance = None
            
            # Override the data directory in config
            import config
            monkeypatch.setattr(config, 'DATA_DIR', temp_dir)
            
            # Create database manager (will use temp directory)
            db_manager = DatabaseManager()
            db_manager.initialize_database()
            
            yield db_manager
            
            # Cleanup
            DatabaseManager._instance = None
    
    def test_database_initialization(self, temp_db):
        """Test that database initializes with all required tables."""
        expected_tables = [
            'journal_entries', 
            'user_preferences', 
            'recent_files', 
            'cached_metrics', 
            'health_metrics_metadata',
            'data_sources',
            'import_history',
            'filter_configs',
            'schema_migrations'
        ]
        
        for table in expected_tables:
            assert temp_db.table_exists(table), f"Table '{table}' should exist"
    
    def test_journal_entry_crud(self, temp_db):
        """Test creating, reading, updating, and deleting journal entries."""
        # Create entry
        entry_date = date.today()
        entry_id = JournalDAO.save_journal_entry(
            entry_date=entry_date,
            entry_type='daily',
            content="Test journal entry from pytest"
        )
        assert entry_id is not None
        
        # Read entries
        entries = JournalDAO.get_journal_entries(entry_date, entry_date)
        assert len(entries) == 1
        assert entries[0].content == "Test journal entry from pytest"
        assert entries[0].entry_type == 'daily'
        
        # Update entry
        updated_id = JournalDAO.save_journal_entry(
            entry_date=entry_date,
            entry_type='daily',
            content="Updated content"
        )
        assert updated_id == entry_id  # Should update existing entry
        
        # Verify update
        entries = JournalDAO.get_journal_entries(entry_date, entry_date)
        assert len(entries) == 1
        assert entries[0].content == "Updated content"
    
    def test_preferences_operations(self, temp_db):
        """Test preference get/set operations."""
        # Get default preference
        theme = PreferenceDAO.get_preference('theme_mode')
        assert theme == 'warm'  # Default value
        
        # Set preference
        PreferenceDAO.set_preference('window_width', 1600)
        width = PreferenceDAO.get_preference('window_width')
        assert width == 1600
        
        # Test different data types
        PreferenceDAO.set_preference('show_tooltips', True)
        assert PreferenceDAO.get_preference('show_tooltips') is True
        
        PreferenceDAO.set_preference('last_import_date', date.today())
        last_date = PreferenceDAO.get_preference('last_import_date')
        assert isinstance(last_date, date)
        
        # Test JSON preference
        PreferenceDAO.set_preference('filter_config', {'types': ['HeartRate', 'Steps']})
        config = PreferenceDAO.get_preference('filter_config')
        assert isinstance(config, dict)
        assert 'HeartRate' in config['types']
    
    def test_cache_operations(self, temp_db):
        """Test cache storage and retrieval."""
        # Cache data
        test_data = {
            'avg': 75.5,
            'min': 60,
            'max': 90,
            'count': 100
        }
        
        cache_key = CacheDAO.cache_metrics(
            metric_type="HeartRate",
            data=test_data,
            date_start=date.today(),
            date_end=date.today(),
            ttl_hours=1
        )
        assert cache_key is not None
        
        # Retrieve cached data
        cached = CacheDAO.get_cached_metrics(
            metric_type="HeartRate",
            date_start=date.today(),
            date_end=date.today()
        )
        assert cached is not None
        assert cached['avg'] == 75.5
        assert cached['count'] == 100
        
        # Test cache expiration
        expired_key = CacheDAO.cache_metrics(
            metric_type="Steps",
            data={'count': 5000},
            date_start=date.today() - timedelta(days=1),
            date_end=date.today() - timedelta(days=1),
            ttl_hours=0  # Already expired
        )
        
        # Manually update the created_at to simulate expiration
        with temp_db.get_connection() as conn:
            conn.execute(
                "UPDATE cached_metrics SET created_at = datetime('now', '-2 hours') WHERE cache_key = ?",
                (expired_key,)
            )
            conn.commit()
        
        # Should return None for expired cache
        expired_cache = CacheDAO.get_cached_metrics(
            metric_type="Steps",
            date_start=date.today() - timedelta(days=1),
            date_end=date.today() - timedelta(days=1)
        )
        assert expired_cache is None
    
    def test_metrics_metadata(self, temp_db):
        """Test health metrics metadata operations."""
        # Get existing metadata
        metadata = MetricsMetadataDAO.get_all_metadata()
        assert len(metadata) > 0  # Should have default entries
        
        # Get specific metric
        heart_rate = MetricsMetadataDAO.get_metric_metadata('HeartRate')
        assert heart_rate is not None
        assert heart_rate.unit == 'bpm'
        assert heart_rate.category == 'vitals'
    
    def test_concurrent_access(self, temp_db):
        """Test that database handles concurrent access properly."""
        import threading
        
        results = []
        
        def write_preference(key, value):
            try:
                PreferenceDAO.set_preference(key, value)
                results.append(True)
            except Exception:
                results.append(False)
        
        # Create multiple threads writing different preferences
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_preference, args=(f'test_key_{i}', i))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All operations should succeed
        assert all(results)
        
        # Verify all values were written
        for i in range(10):
            value = PreferenceDAO.get_preference(f'test_key_{i}')
            assert value == i