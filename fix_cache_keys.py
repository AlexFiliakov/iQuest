#!/usr/bin/env python3
"""
Temporary script to fix cache key formats and clear incompatible entries.
This script migrates from the old cache key format to the new standardized format.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_cache_keys():
    """Clear old cache entries with incompatible key formats."""
    
    analytics_cache_path = Path("analytics_cache.db")
    
    if not analytics_cache_path.exists():
        logger.info("Analytics cache database does not exist, nothing to fix")
        return
    
    try:
        with sqlite3.connect(analytics_cache_path) as conn:
            # Get current count
            cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
            old_count = cursor.fetchone()[0]
            logger.info(f"Found {old_count} existing cache entries")
            
            # Delete entries with old key formats that won't match new format
            old_patterns = [
                "monthly_stats|%",
                "weekly_stats|%", 
                "daily_stats|%",
                "weekly_rolling|%",
                "weekly_comparison|%",
                "weekly_ma|%",
                "daily_percentiles|%",
                "daily_outliers|%",
                "daily_aggregates|%",
                "daily_summary|%",
                "monthly_yoy|%",
                "monthly_growth|%",
                "monthly_distribution|%",
                "monthly_multi|%",
                "monthly_summary|%"
            ]
            
            for pattern in old_patterns:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key LIKE ?", (pattern,))
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"Deleted {deleted} entries with pattern: {pattern}")
            
            conn.commit()
            
            # Get new count
            cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
            new_count = cursor.fetchone()[0]
            logger.info(f"Cache cleanup complete. Entries: {old_count} -> {new_count}")
            
    except Exception as e:
        logger.error(f"Error fixing cache keys: {e}")
        raise

if __name__ == "__main__":
    fix_cache_keys()