#!/usr/bin/env python3
"""Example usage of the general-purpose journaling system."""

import sys
import os
from datetime import date, datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import db_manager
from src.data_access import JournalDAO, PreferenceDAO, CacheDAO
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()

def demonstrate_journal_entries():
    """Demonstrate creating and retrieving journal entries."""
    print("\n=== Journal Entry Examples ===\n")
    
    # Daily journal entry
    today = date.today()
    JournalDAO.save_journal_entry(
        entry_date=today,
        entry_type='daily',
        content="Today was productive! Completed morning workout - 30 min cardio, 20 min weights. "
                "Energy levels good throughout the day. Had a healthy lunch and stayed hydrated."
    )
    print(f"✓ Created daily journal entry for {today}")
    
    # Weekly journal entry
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    JournalDAO.save_journal_entry(
        entry_date=week_start,
        entry_type='weekly',
        content="Great week overall! Hit all workout goals (5/5 days). "
                "Average sleep was 7.5 hours. Need to work on reducing screen time before bed.",
        week_start_date=week_start
    )
    print(f"✓ Created weekly journal entry for week starting {week_start}")
    
    # Monthly journal entry
    month_start = today.replace(day=1)
    month_year = today.strftime("%Y-%m")
    JournalDAO.save_journal_entry(
        entry_date=month_start,
        entry_type='monthly',
        content="January fitness goals: 80% achieved! Weight down by 2 lbs. "
                "Consistently hit 10k steps daily. February goal: Add yoga 2x per week.",
        month_year=month_year
    )
    print(f"✓ Created monthly journal entry for {month_year}")
    
    # Retrieve entries
    print("\n--- Retrieving Journal Entries ---")
    
    # Get all entries from last 30 days
    start_date = today - timedelta(days=30)
    entries = JournalDAO.get_journal_entries(start_date, today)
    print(f"\nFound {len(entries)} journal entries in the last 30 days:")
    
    for entry in entries:
        print(f"\n{entry.entry_type.upper()} - {entry.entry_date}")
        print(f"Content: {entry.content[:100]}...")
    
    # Search entries
    search_results = JournalDAO.search_journal_entries("workout")
    print(f"\n\nSearch for 'workout' found {len(search_results)} entries")


def demonstrate_preferences():
    """Demonstrate user preferences system."""
    print("\n\n=== User Preferences Examples ===\n")
    
    # Set preferences
    PreferenceDAO.set_preference('last_csv_path', '/Users/demo/health_export.csv')
    PreferenceDAO.set_preference('selected_sources', ['iPhone', 'Apple Watch'])
    PreferenceDAO.set_preference('chart_animation', True)
    PreferenceDAO.set_preference('window_width', 1440)
    
    print("✓ Updated user preferences")
    
    # Get individual preferences
    csv_path = PreferenceDAO.get_preference('last_csv_path', default='No file selected')
    print(f"\nLast CSV Path: {csv_path}")
    
    sources = PreferenceDAO.get_preference('selected_sources', default=[])
    print(f"Selected Sources: {sources}")
    
    # Get all preferences
    all_prefs = PreferenceDAO.get_all_preferences()
    print("\nAll Preferences:")
    for key, value in all_prefs.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")


def demonstrate_health_metrics_cache():
    """Demonstrate caching of health metrics."""
    print("\n\n=== Health Metrics Cache Examples ===\n")
    
    # Example health metrics data
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Cache daily step count data
    daily_steps = {
        "average": 8542,
        "total": 59794,
        "days": 7,
        "max": 12340,
        "min": 5021,
        "data_points": [
            {"date": "2024-01-20", "value": 8234},
            {"date": "2024-01-21", "value": 12340},
            {"date": "2024-01-22", "value": 5021},
            # ... more data
        ]
    }
    
    cache_key = CacheDAO.cache_metrics(
        metric_type="StepCount",
        data=daily_steps,
        date_start=today - timedelta(days=7),
        date_end=today,
        aggregation_type="daily",
        source_name="iPhone",
        health_type="HKQuantityTypeIdentifierStepCount",
        ttl_hours=24
    )
    print(f"✓ Cached step count data with key: {cache_key}")
    
    # Cache heart rate data
    heart_rate_data = {
        "average_resting": 62,
        "average_active": 85,
        "max": 145,
        "min": 48,
        "measurements": 1250
    }
    
    CacheDAO.cache_metrics(
        metric_type="HeartRate",
        data=heart_rate_data,
        date_start=yesterday,
        date_end=yesterday,
        aggregation_type="daily",
        source_name="Apple Watch",
        health_type="HKQuantityTypeIdentifierHeartRate"
    )
    print("✓ Cached heart rate data")
    
    # Retrieve cached data
    print("\n--- Retrieving Cached Data ---")
    
    cached_steps = CacheDAO.get_cached_metrics(
        metric_type="StepCount",
        date_start=today - timedelta(days=7),
        date_end=today,
        aggregation_type="daily",
        source_name="iPhone",
        health_type="HKQuantityTypeIdentifierStepCount"
    )
    
    if cached_steps:
        print(f"\nCached Step Data:")
        print(f"  Average: {cached_steps['average']} steps/day")
        print(f"  Total: {cached_steps['total']} steps")
        print(f"  Max: {cached_steps['max']} steps")
    
    # Clean expired cache
    deleted = CacheDAO.clean_expired_cache()
    print(f"\n✓ Cleaned {deleted} expired cache entries")


def main():
    """Run all examples."""
    print("Apple Health Monitor - General Purpose Database Examples")
    print("=" * 55)
    
    # Initialize database
    db_manager.initialize_database()
    
    # Run demonstrations
    demonstrate_journal_entries()
    demonstrate_preferences()
    demonstrate_health_metrics_cache()
    
    print("\n\n✅ All examples completed successfully!")


if __name__ == "__main__":
    main()