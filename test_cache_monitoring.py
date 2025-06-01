#!/usr/bin/env python3
"""
Simple test of cache monitoring functionality without complex imports.
"""

import sqlite3
from pathlib import Path

def test_cache_monitoring():
    """Test basic cache monitoring."""
    print("=== Cache Monitoring Test ===\n")
    
    # Check if analytics cache exists
    cache_path = Path("analytics_cache.db")
    if cache_path.exists():
        print(f"✓ Analytics cache found: {cache_path}")
        
        # Get cache entry count
        try:
            with sqlite3.connect(cache_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                count = cursor.fetchone()[0]
                print(f"📊 Cache entries: {count}")
                
                # Get sample cache keys
                cursor = conn.execute("SELECT key FROM cache_entries LIMIT 5")
                keys = [row[0] for row in cursor.fetchall()]
                print("🔑 Sample cache keys:")
                for key in keys:
                    print(f"  - {key}")
                    
        except Exception as e:
            print(f"❌ Error reading cache: {e}")
    else:
        print("❌ Analytics cache not found")
    
    # Check if main database exists
    main_db_path = Path("health_monitor.db") 
    if main_db_path.exists():
        print(f"\n✓ Main database found: {main_db_path}")
        
        try:
            with sqlite3.connect(main_db_path) as conn:
                # Check cached_metrics table
                cursor = conn.execute("SELECT COUNT(*) FROM cached_metrics")
                count = cursor.fetchone()[0]
                print(f"📊 Cached metrics entries: {count}")
                
        except Exception as e:
            print(f"❌ Error reading main database: {e}")
    else:
        print("❌ Main database not found")
    
    print("\n✅ Cache monitoring test complete!")

if __name__ == "__main__":
    test_cache_monitoring()