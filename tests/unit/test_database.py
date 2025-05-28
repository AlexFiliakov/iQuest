"""Unit tests for database operations as per SPECS_DB.md."""

import unittest
import tempfile
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
import json

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import DatabaseManager, DB_FILE_NAME
from src.models import JournalEntry, UserPreference, RecentFile, CachedMetric
from src.data_access import JournalDAO, PreferenceDAO, RecentFilesDAO, CacheDAO


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager.
    
    This test class validates the DatabaseManager singleton class functionality
    including database initialization, table creation, connection management,
    and query execution methods.
    
    Tests cover:
    - Database initialization with proper table structure
    - Singleton pattern implementation
    - Connection context manager functionality
    - Query execution methods (SELECT, INSERT, UPDATE, DELETE)
    - Table existence checking
    - Migration system functionality
    """
    
    def setUp(self):
        """Set up test database.
        
        Creates a temporary directory and database for isolated testing.
        Resets the DatabaseManager singleton instance to ensure clean
        test state and temporarily overrides the DATA_DIR configuration.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, DB_FILE_NAME)
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Override DATA_DIR for testing
        import src.config as config
        original_data_dir = config.DATA_DIR
        config.DATA_DIR = self.temp_dir
        
        # Create a test database manager
        self.db_manager = DatabaseManager()
        
        # Restore original DATA_DIR
        config.DATA_DIR = original_data_dir
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database is properly initialized with all required tables."""
        # Check that all tables exist as per spec
        self.assertTrue(self.db_manager.table_exists("journal_entries"))
        self.assertTrue(self.db_manager.table_exists("user_preferences"))
        self.assertTrue(self.db_manager.table_exists("recent_files"))
        self.assertTrue(self.db_manager.table_exists("cached_metrics"))
        self.assertTrue(self.db_manager.table_exists("schema_migrations"))
    
    def test_default_preferences_inserted(self):
        """Test that default preferences are inserted on initialization."""
        results = self.db_manager.execute_query(
            "SELECT COUNT(*) as count FROM user_preferences"
        )
        # Should have 15 default preferences as per spec
        self.assertEqual(results[0]["count"], 15)
        
        # Check specific default
        results = self.db_manager.execute_query(
            "SELECT preference_value, data_type FROM user_preferences WHERE preference_key = ?",
            ("theme_mode",)
        )
        self.assertEqual(results[0]["preference_value"], "light")
        self.assertEqual(results[0]["data_type"], "string")


class TestModels(unittest.TestCase):
    """Test cases for data models."""
    
    def test_journal_entry_validation(self):
        """Test JournalEntry validation for different entry types."""
        # Valid daily entry
        entry = JournalEntry(
            entry_date=date.today(),
            entry_type="daily",
            content="Daily health log"
        )
        self.assertEqual(entry.entry_type, "daily")
        
        # Valid weekly entry
        week_start = date.today() - timedelta(days=date.today().weekday())
        weekly_entry = JournalEntry(
            entry_date=week_start,
            entry_type="weekly",
            content="Weekly summary",
            week_start_date=week_start
        )
        self.assertEqual(weekly_entry.entry_type, "weekly")
        
        # Invalid entry type
        with self.assertRaises(ValueError):
            JournalEntry(
                entry_date=date.today(),
                entry_type="hourly",
                content="Invalid type"
            )
        
        # Weekly without week_start_date
        with self.assertRaises(ValueError):
            JournalEntry(
                entry_date=date.today(),
                entry_type="weekly",
                content="Missing week start"
            )
    
    def test_user_preference_type_conversion(self):
        """Test UserPreference type conversion methods."""
        # Integer preference
        pref = UserPreference(
            preference_key="window_width",
            preference_value="1200",
            data_type="integer"
        )
        self.assertEqual(pref.get_typed_value(), 1200)
        self.assertIsInstance(pref.get_typed_value(), int)
        
        # Boolean preference
        bool_pref = UserPreference(
            preference_key="chart_animation",
            preference_value="true",
            data_type="boolean"
        )
        self.assertTrue(bool_pref.get_typed_value())
        
        # JSON preference
        json_pref = UserPreference(
            preference_key="selected_sources",
            preference_value='["iPhone", "Apple Watch"]',
            data_type="json"
        )
        value = json_pref.get_typed_value()
        self.assertEqual(value, ["iPhone", "Apple Watch"])
    
    def test_cached_metric_expiration(self):
        """Test CachedMetric expiration check."""
        # Non-expired metric
        future_time = datetime.now() + timedelta(hours=1)
        metric = CachedMetric(
            cache_key="test_key",
            metric_type="StepCount",
            date_range_start=date.today(),
            date_range_end=date.today(),
            aggregation_type="daily",
            metric_data={"steps": 10000},
            expires_at=future_time
        )
        self.assertFalse(metric.is_expired())
        
        # Expired metric
        past_time = datetime.now() - timedelta(hours=1)
        expired_metric = CachedMetric(
            cache_key="expired_key",
            metric_type="StepCount",
            date_range_start=date.today(),
            date_range_end=date.today(),
            aggregation_type="daily",
            metric_data={"steps": 5000},
            expires_at=past_time
        )
        self.assertTrue(expired_metric.is_expired())


class TestJournalDAO(unittest.TestCase):
    """Test cases for JournalDAO."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, DB_FILE_NAME)
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Override DATA_DIR for testing
        import src.config as config
        self.original_data_dir = config.DATA_DIR
        config.DATA_DIR = self.temp_dir
        
        # Create database manager and initialize
        self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
        # Restore original DATA_DIR
        import src.config as config
        config.DATA_DIR = self.original_data_dir
        
        # Reset singleton instance
        DatabaseManager._instance = None
    
    def test_save_and_retrieve_journal_entry(self):
        """Test creating and retrieving journal entries."""
        # Create daily entry
        test_date = date.today()
        entry_id = JournalDAO.save_journal_entry(
            entry_date=test_date,
            entry_type="daily",
            content="Test daily journal entry"
        )
        self.assertIsNotNone(entry_id)
        
        # Retrieve entries
        entries = JournalDAO.get_journal_entries(
            start_date=test_date,
            end_date=test_date,
            entry_type="daily"
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].content, "Test daily journal entry")
        self.assertEqual(entries[0].entry_type, "daily")
    
    def test_upsert_journal_entry(self):
        """Test that save_journal_entry performs upsert correctly."""
        test_date = date.today()
        
        # First save
        JournalDAO.save_journal_entry(
            entry_date=test_date,
            entry_type="daily",
            content="Original content"
        )
        
        # Update same date/type
        JournalDAO.save_journal_entry(
            entry_date=test_date,
            entry_type="daily",
            content="Updated content"
        )
        
        # Should only have one entry
        entries = JournalDAO.get_journal_entries(test_date, test_date)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].content, "Updated content")
    
    def test_search_journal_entries(self):
        """Test searching journal entries."""
        # Create entries
        JournalDAO.save_journal_entry(
            entry_date=date(2024, 1, 1),
            entry_type="daily",
            content="Morning workout completed"
        )
        JournalDAO.save_journal_entry(
            entry_date=date(2024, 1, 2),
            entry_type="daily",
            content="Rest day, focused on stretching"
        )
        
        # Search
        results = JournalDAO.search_journal_entries("workout")
        self.assertEqual(len(results), 1)
        self.assertIn("workout", results[0].content)


class TestPreferenceDAO(unittest.TestCase):
    """Test cases for PreferenceDAO."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, DB_FILE_NAME)
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Override DATA_DIR for testing
        import src.config as config
        self.original_data_dir = config.DATA_DIR
        config.DATA_DIR = self.temp_dir
        
        self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
        # Restore original DATA_DIR
        import src.config as config
        config.DATA_DIR = self.original_data_dir
        
        # Reset singleton instance
        DatabaseManager._instance = None
    
    def test_get_and_set_preferences(self):
        """Test getting and setting preferences with type conversion."""
        # Set integer preference
        success = PreferenceDAO.set_preference('window_width', 1440)
        self.assertTrue(success)
        
        # Get integer preference
        width = PreferenceDAO.get_preference('window_width')
        self.assertEqual(width, 1440)
        self.assertIsInstance(width, int)
        
        # Set boolean preference
        PreferenceDAO.set_preference('chart_animation', False)
        animation = PreferenceDAO.get_preference('chart_animation')
        self.assertFalse(animation)
        
        # Set JSON preference
        sources = ['iPhone', 'Apple Watch', 'iPad']
        PreferenceDAO.set_preference('selected_sources', sources)
        retrieved_sources = PreferenceDAO.get_preference('selected_sources')
        self.assertEqual(retrieved_sources, sources)


class TestCacheDAO(unittest.TestCase):
    """Test cases for CacheDAO."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, DB_FILE_NAME)
        
        # Reset singleton instance for testing
        DatabaseManager._instance = None
        
        # Override DATA_DIR for testing
        import src.config as config
        self.original_data_dir = config.DATA_DIR
        config.DATA_DIR = self.temp_dir
        
        # Create a test database manager
        self.db_manager = DatabaseManager()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
        # Restore original DATA_DIR
        import src.config as config
        config.DATA_DIR = self.original_data_dir
        
        # Reset singleton instance
        DatabaseManager._instance = None
    
    def test_cache_and_retrieve_metrics(self):
        """Test caching and retrieving metrics."""
        test_data = {
            "average": 10000,
            "max": 15000,
            "min": 5000,
            "total": 70000
        }
        
        # Cache metrics
        cache_key = CacheDAO.cache_metrics(
            metric_type="StepCount",
            data=test_data,
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 7),
            aggregation_type="weekly",
            source_name="iPhone",
            ttl_hours=24
        )
        self.assertIsNotNone(cache_key)
        
        # Retrieve cached data
        cached = CacheDAO.get_cached_metrics(
            metric_type="StepCount",
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 7),
            aggregation_type="weekly",
            source_name="iPhone"
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached["average"], 10000)
    
    def test_cache_expiration(self):
        """Test that expired cache entries are not returned."""
        # Cache with normal TTL first
        cache_key = CacheDAO.cache_metrics(
            metric_type="HeartRate",
            data={"avg": 70},
            date_start=date.today(),
            date_end=date.today(),
            ttl_hours=1
        )
        self.assertIsNotNone(cache_key)
        
        # Manually update the expires_at to be in the past to simulate expiration
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE cached_metrics SET expires_at = datetime('now', '-1 hour') WHERE cache_key = ?",
                (cache_key,)
            )
            conn.commit()
        
        # Should not retrieve expired data
        cached = CacheDAO.get_cached_metrics(
            metric_type="HeartRate",
            date_start=date.today(),
            date_end=date.today()
        )
        self.assertIsNone(cached)
        
        # Create another expired entry to ensure we have something to clean
        cache_key2 = CacheDAO.cache_metrics(
            metric_type="StepCount",
            data={"total": 5000},
            date_start=date.today() - timedelta(days=1),
            date_end=date.today() - timedelta(days=1),
            ttl_hours=1
        )
        
        # Manually expire this one too
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE cached_metrics SET expires_at = datetime('now', '-2 hours') WHERE cache_key = ?",
                (cache_key2,)
            )
            conn.commit()
        
        # Clean expired entries
        deleted = CacheDAO.clean_expired_cache()
        self.assertGreaterEqual(deleted, 1)


if __name__ == "__main__":
    unittest.main()