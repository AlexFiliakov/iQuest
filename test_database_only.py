#!/usr/bin/env python3
"""Test database functionality without PyQt6 dependency."""

import sys
import os
from datetime import date, datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
try:
    from database import db_manager, DB_FILE_NAME
    from data_access import JournalDAO, PreferenceDAO, CacheDAO
    from models import JournalEntry, UserPreference, CachedMetric
    print("✓ All database imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test database initialization
try:
    print(f"\nInitializing database: {DB_FILE_NAME}")
    db_manager.initialize_database()
    print("✓ Database initialized successfully")
    
    # Check tables
    tables = ['journal_entries', 'user_preferences', 'recent_files', 'cached_metrics', 'schema_migrations']
    for table in tables:
        if db_manager.table_exists(table):
            print(f"  ✓ Table '{table}' exists")
        else:
            print(f"  ❌ Table '{table}' missing")
    
except Exception as e:
    print(f"❌ Database initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test journal entry
try:
    print("\n\nTesting Journal Entry:")
    entry_id = JournalDAO.save_journal_entry(
        entry_date=date.today(),
        entry_type='daily',
        content="Test journal entry from database test script"
    )
    print(f"✓ Created journal entry with ID: {entry_id}")
    
    entries = JournalDAO.get_journal_entries(date.today(), date.today())
    print(f"✓ Retrieved {len(entries)} journal entries")
    
except Exception as e:
    print(f"❌ Journal entry error: {e}")
    import traceback
    traceback.print_exc()

# Test preferences
try:
    print("\n\nTesting User Preferences:")
    
    # Get default preference
    theme = PreferenceDAO.get_preference('theme_mode')
    print(f"✓ Theme mode: {theme}")
    
    # Set preference
    PreferenceDAO.set_preference('window_width', 1600)
    width = PreferenceDAO.get_preference('window_width')
    print(f"✓ Window width set to: {width}")
    
except Exception as e:
    print(f"❌ Preference error: {e}")
    import traceback
    traceback.print_exc()

# Test cache
try:
    print("\n\nTesting Cache:")
    
    cache_key = CacheDAO.cache_metrics(
        metric_type="TestMetric",
        data={"value": 123},
        date_start=date.today(),
        date_end=date.today(),
        ttl_hours=1
    )
    print(f"✓ Cached data with key: {cache_key}")
    
    cached = CacheDAO.get_cached_metrics(
        metric_type="TestMetric",
        date_start=date.today(),
        date_end=date.today()
    )
    print(f"✓ Retrieved cached data: {cached}")
    
except Exception as e:
    print(f"❌ Cache error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Database testing complete!")
print(f"\nDatabase location: {os.path.join('data', DB_FILE_NAME)}")
print("\nTo run the full application, install dependencies with:")
print("  pip install -r requirements.txt")