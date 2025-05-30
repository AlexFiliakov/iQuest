# Erase All Data Bug Fix

## Issue
The "Erase All Data" feature was failing with an import error:
```
cannot import name 'CacheManager' from 'src.analytics.cache_manager'
```

## Root Cause
The cache_manager.py module exports `AnalyticsCacheManager`, not `CacheManager`. Additionally, the `clear_all()` method only clears the L1 (memory) cache, not the persistent L2 (SQLite) and L3 (disk) caches.

## Solution
Instead of trying to use the cache manager's methods, the fix directly deletes the cache files:

1. **Removed the problematic import** of CacheManager
2. **Direct file deletion approach**:
   - Delete the analytics cache database file (`analytics_cache.db`)
   - Delete the cache directory and all its contents
   - Check both the DATA_DIR and current directory locations

## Changes Made
- Removed: `from ..analytics.cache_manager import CacheManager`
- Removed: Cache manager instantiation and method calls
- Added: Direct deletion of `analytics_cache.db` in both DATA_DIR and current directory
- Added: Direct deletion of `cache` directory in both locations

## Result
The erase all data feature now works correctly by:
- Closing database connections
- Deleting the main health data database
- Deleting the analytics cache database
- Removing all cache directories
- Clearing filter configurations
- Resetting the UI state

This approach is more reliable as it doesn't depend on the internal implementation of the cache manager and ensures complete removal of all cached data.