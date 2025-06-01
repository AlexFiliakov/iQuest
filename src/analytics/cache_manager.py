"""
Multi-Tier Analytics Caching System for High-Performance Health Data Analysis.

This module implements a sophisticated three-tier caching architecture designed to
optimize performance for computationally expensive health analytics operations.
The system provides automatic cache management, performance monitoring, and
intelligent cache promotion strategies.

Cache Architecture:
- L1 Cache: In-memory LRU cache for immediate access to frequently used results
- L2 Cache: SQLite-based persistent cache for medium-term storage
- L3 Cache: Compressed disk-based cache for long-term storage

Key Features:
- Automatic tier promotion for cache hits
- TTL-based expiration with configurable timeouts
- Memory usage monitoring and automatic eviction
- Dependency-based cache invalidation
- Thread-safe operations with proper locking
- Comprehensive performance metrics and monitoring
- Compressed storage for efficient disk usage

Example:
    Basic caching usage:
    
    >>> cache = get_cache_manager()
    >>> 
    >>> # Cache expensive calculation
    >>> def expensive_calculation():
    ...     # Simulate complex health analytics
    ...     return calculate_monthly_trends()
    >>> 
    >>> # Get result with automatic caching
    >>> result = cache.get(
    ...     'monthly_trends_2024_01',
    ...     expensive_calculation,
    ...     cache_tiers=['l1', 'l2'],
    ...     ttl=3600  # 1 hour
    ... )
    
    Advanced usage with dependencies:
    
    >>> # Cache with dependency tracking
    >>> cache.set(
    ...     'user_123_daily_stats',
    ...     daily_statistics,
    ...     dependencies=['user_123_data'],
    ...     ttl=1800
    ... )
    >>> 
    >>> # Invalidate when source data changes
    >>> cache.invalidate_dependencies('user_123_data')
    
    Performance monitoring:
    
    >>> # Get cache performance metrics
    >>> metrics = cache.get_metrics()
    >>> print(f"L1 hit rate: {metrics.l1_hit_rate:.2%}")
    >>> print(f"Overall hit rate: {metrics.overall_hit_rate:.2%}")
    >>> print(f"Memory usage: {metrics.memory_usage_mb:.1f} MB")

Note:
    This module is optimized for health analytics workloads with patterns of
    repeated expensive calculations and moderate cache invalidation rates.
"""

import hashlib
import json
import pickle
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
import logging
from collections import OrderedDict
import tempfile
import gzip

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Container for cache performance metrics."""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    total_requests: int = 0
    cache_sets: int = 0
    invalidations: int = 0
    memory_usage_mb: float = 0.0
    
    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate."""
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total > 0 else 0.0
    
    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 cache hit rate."""
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total > 0 else 0.0
    
    @property
    def l3_hit_rate(self) -> float:
        """Calculate L3 cache hit rate."""
        total = self.l3_hits + self.l3_misses
        return self.l3_hits / total if total > 0 else 0.0
    
    @property
    def overall_hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        return total_hits / self.total_requests if self.total_requests > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    dependencies: List[str] = None
    ttl_seconds: Optional[int] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)
    
    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()


class LRUCache:
    """Thread-safe LRU cache with size and TTL limits."""
    
    def __init__(self, maxsize: int = 1000, max_memory_mb: float = 500.0, default_ttl: int = 900):
        self.maxsize = maxsize
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl  # 15 minutes
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._current_memory -= entry.size_bytes
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, dependencies: List[str] = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
                if size_bytes > 1024 * 1024:  # Skip objects > 1MB
                    logger.warning(f"Skipping cache entry {key}: too large ({size_bytes} bytes)")
                    return
            except Exception as e:
                logger.warning(f"Could not calculate size for cache entry {key}: {e}")
                return
            
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_memory -= old_entry.size_bytes
                del self._cache[key]
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=size_bytes,
                dependencies=dependencies or [],
                ttl_seconds=ttl or self.default_ttl
            )
            
            # Check memory limits
            while (self._current_memory + entry.size_bytes > self.max_memory_bytes and 
                   len(self._cache) > 0):
                self._evict_lru()
            
            # Check size limits
            while len(self._cache) >= self.maxsize:
                self._evict_lru()
            
            # Add new entry
            self._cache[key] = entry
            self._current_memory += entry.size_bytes
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Remove oldest (least recently used)
        key, entry = self._cache.popitem(last=False)
        self._current_memory -= entry.size_bytes
        logger.debug(f"Evicted LRU cache entry: {key}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern."""
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                entry = self._cache[key]
                self._current_memory -= entry.size_bytes
                del self._cache[key]
            return len(keys_to_remove)
    
    def invalidate_dependencies(self, dependency: str) -> int:
        """Invalidate entries with specific dependency."""
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if dependency in entry.dependencies:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self._cache[key]
                self._current_memory -= entry.size_bytes
                del self._cache[key]
            
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    @property
    def memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self._current_memory / (1024 * 1024)
    
    @property
    def size(self) -> int:
        """Get number of entries."""
        return len(self._cache)


class SQLiteCache:
    """SQLite-based cache for computed aggregates."""
    
    def __init__(self, db_path: str = "analytics_cache.db"):
        self.db_path = Path(db_path)
        self._connection = None
        self._corrupted = False
        self._init_db_with_recovery()
    
    def _check_database_integrity(self) -> bool:
        """Check if the SQLite database is corrupted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Run integrity check
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result and result[0] == "ok":
                    # Also try to query the table to ensure it exists and is readable
                    conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()
                    return True
                else:
                    logger.warning(f"Database integrity check failed: {result}")
                    return False
        except sqlite3.DatabaseError as e:
            logger.error(f"Database corruption detected: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return False
    
    def _recover_corrupted_database(self) -> None:
        """Recover from a corrupted database by recreating it."""
        logger.warning(f"Attempting to recover corrupted cache database: {self.db_path}")
        
        # Backup the corrupted file
        if self.db_path.exists():
            backup_path = self.db_path.with_suffix('.corrupted.bak')
            try:
                import shutil
                shutil.move(str(self.db_path), str(backup_path))
                logger.info(f"Moved corrupted database to: {backup_path}")
            except Exception as e:
                logger.error(f"Could not backup corrupted database: {e}")
                # Try to just delete it
                try:
                    self.db_path.unlink()
                    logger.info("Deleted corrupted database")
                except Exception as del_error:
                    logger.error(f"Could not delete corrupted database: {del_error}")
                    # As a last resort, use a different cache file
                    self.db_path = self.db_path.with_name("analytics_cache_new.db")
                    logger.warning(f"Using alternative cache database: {self.db_path}")
    
    def _init_db_with_recovery(self) -> None:
        """Initialize SQLite database with corruption recovery."""
        # First check if database exists and is healthy
        if self.db_path.exists():
            if not self._check_database_integrity():
                self._recover_corrupted_database()
                self._corrupted = True
        
        # Now initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at TIMESTAMP,
                        last_accessed TIMESTAMP,
                        access_count INTEGER DEFAULT 0,
                        size_bytes INTEGER,
                        dependencies TEXT,
                        ttl_seconds INTEGER,
                        expires_at TIMESTAMP,
                        import_id TEXT
                    )
                """)
                
                # Performance indexes
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
                """)
                
                # Enable WAL mode for better concurrent performance
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")  # 10MB cache
                
                # Add migration for existing databases
                cursor = conn.execute("PRAGMA table_info(cache_entries)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'import_id' not in columns:
                    conn.execute("ALTER TABLE cache_entries ADD COLUMN import_id TEXT")
                    logger.info("Added import_id column to cache_entries table")
                
                if self._corrupted:
                    logger.info("Successfully created new cache database after corruption recovery")
                    self._corrupted = False
                    
        except Exception as e:
            logger.error(f"Failed to initialize cache database: {e}")
            # Fall back to in-memory mode if we can't create a database
            logger.warning("Cache will operate in degraded mode without persistence")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT value, expires_at FROM cache_entries 
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                """, (key,))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                # Update access statistics
                conn.execute("""
                    UPDATE cache_entries 
                    SET last_accessed = datetime('now'), access_count = access_count + 1
                    WHERE key = ?
                """, (key,))
                
                # Deserialize value
                value = pickle.loads(row['value'])
                return value
                
        except sqlite3.DatabaseError as e:
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower():
                logger.error(f"Cache database corruption detected during get: {e}")
                # Try to recover
                self._recover_corrupted_database()
                self._init_db()
            else:
                logger.error(f"Database error getting from SQLite cache: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting from SQLite cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, dependencies: List[str] = None) -> None:
        """Set value in SQLite cache."""
        try:
            # Serialize value
            value_blob = pickle.dumps(value)
            size_bytes = len(value_blob)
            
            # Calculate expiration using SQLite datetime functions for consistency
            dependencies_json = json.dumps(dependencies or [])
            
            with sqlite3.connect(self.db_path) as conn:
                if ttl:
                    # Use SQLite datetime arithmetic for consistent timing
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, created_at, last_accessed, access_count, size_bytes, dependencies, ttl_seconds, expires_at, import_id)
                        VALUES (?, ?, datetime('now'), datetime('now'), 1, ?, ?, ?, datetime('now', '+' || ? || ' seconds'), NULL)
                    """, (key, value_blob, size_bytes, dependencies_json, ttl, ttl))
                else:
                    # No expiration
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, created_at, last_accessed, access_count, size_bytes, dependencies, ttl_seconds, expires_at, import_id)
                        VALUES (?, ?, datetime('now'), datetime('now'), 1, ?, ?, ?, NULL, NULL)
                    """, (key, value_blob, size_bytes, dependencies_json, ttl))
                
        except sqlite3.DatabaseError as e:
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower():
                logger.error(f"Cache database corruption detected during set: {e}")
                # Try to recover and retry once
                self._recover_corrupted_database()
                self._init_db()
                try:
                    # Retry the operation once after recovery
                    with sqlite3.connect(self.db_path) as conn:
                        if ttl:
                            conn.execute("""
                                INSERT OR REPLACE INTO cache_entries 
                                (key, value, created_at, last_accessed, access_count, size_bytes, dependencies, ttl_seconds, expires_at, import_id)
                                VALUES (?, ?, datetime('now'), datetime('now'), 1, ?, ?, ?, datetime('now', '+' || ? || ' seconds'), NULL)
                            """, (key, value_blob, size_bytes, dependencies_json, ttl, ttl))
                        else:
                            conn.execute("""
                                INSERT OR REPLACE INTO cache_entries 
                                (key, value, created_at, last_accessed, access_count, size_bytes, dependencies, ttl_seconds, expires_at, import_id)
                                VALUES (?, ?, datetime('now'), datetime('now'), 1, ?, ?, ?, NULL, NULL)
                            """, (key, value_blob, size_bytes, dependencies_json, ttl))
                    logger.info("Successfully wrote to cache after recovery")
                except Exception as retry_error:
                    logger.error(f"Failed to write to cache even after recovery: {retry_error}")
            else:
                logger.error(f"Database error setting SQLite cache: {e}")
        except Exception as e:
            logger.error(f"Error setting SQLite cache: {e}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key LIKE ?", (f"%{pattern}%",))
                return cursor.rowcount
        except sqlite3.DatabaseError as e:
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower():
                logger.error(f"Cache database corruption detected during invalidate: {e}")
                self._recover_corrupted_database()
                self._init_db()
            else:
                logger.error(f"Database error invalidating SQLite cache pattern: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error invalidating SQLite cache pattern: {e}")
            return 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE expires_at < datetime('now')")
                return cursor.rowcount
        except sqlite3.DatabaseError as e:
            if "malformed" in str(e).lower() or "corrupt" in str(e).lower():
                logger.error(f"Cache database corruption detected during cleanup: {e}")
                self._recover_corrupted_database()
                self._init_db()
            else:
                logger.error(f"Database error cleaning up expired entries: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    def close(self) -> None:
        """Close any open database connections and prepare for cleanup."""
        # Since we use context managers, connections are auto-closed
        # But we should ensure no active connections remain
        try:
            # Force close any lingering connections by clearing the connection pool
            import gc
            gc.collect()
            
            # Try to close the database file if it exists
            if self.db_path.exists():
                # Ensure WAL mode is disabled to prevent lingering connections
                try:
                    with sqlite3.connect(self.db_path, timeout=1.0) as conn:
                        # Disable WAL mode to ensure all data is written to main db file
                        conn.execute("PRAGMA journal_mode=DELETE")
                        # Force a checkpoint to write any pending changes
                        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                        # Close any open transactions
                        conn.commit()
                except Exception as e:
                    logger.debug(f"Could not change journal mode: {e}")
                
                # Additional cleanup - remove WAL and SHM files if they exist
                import time
                time.sleep(0.1)  # Small delay to ensure connection is fully closed
                
                wal_file = Path(str(self.db_path) + "-wal")
                shm_file = Path(str(self.db_path) + "-shm")
                
                for file_path in [wal_file, shm_file]:
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            logger.debug(f"Removed {file_path.name}")
                        except Exception as e:
                            logger.debug(f"Could not remove {file_path.name}: {e}")
            
            # Force another garbage collection
            gc.collect()
            time.sleep(0.1)  # Give OS time to release file handles
            
            logger.debug("SQLite cache prepared for cleanup")
        except Exception as e:
            logger.error(f"Error closing SQLite cache: {e}")
    
    def get_size(self) -> int:
        """Get the number of entries in the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting cache size: {e}")
            return 0
    
    def clear(self) -> None:
        """Clear all entries from the SQLite cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
                logger.info("Cleared all entries from SQLite cache")
        except Exception as e:
            logger.error(f"Error clearing SQLite cache: {e}")


class DiskCache:
    """Disk-based cache for expensive calculations."""
    
    def __init__(self, cache_dir: str = "./cache/"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self._metadata: Dict[str, Dict] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load cache metadata."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache metadata: {e}")
        return {}
    
    def _save_metadata(self) -> None:
        """Save cache metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, default=str)
        except Exception as e:
            logger.error(f"Could not save cache metadata: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache.gz"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
            
            # Check metadata
            if key in self._metadata:
                metadata = self._metadata[key]
                ttl = metadata.get('ttl_seconds')
                created_at = datetime.fromisoformat(metadata['created_at'])
                
                if ttl and (datetime.now() - created_at).total_seconds() > ttl:
                    # Expired
                    file_path.unlink(missing_ok=True)
                    del self._metadata[key]
                    self._save_metadata()
                    return None
            
            # Load compressed data
            with gzip.open(file_path, 'rb') as f:
                value = pickle.load(f)
            
            # Update access statistics
            if key in self._metadata:
                self._metadata[key]['last_accessed'] = datetime.now().isoformat()
                self._metadata[key]['access_count'] = self._metadata[key].get('access_count', 0) + 1
                self._save_metadata()
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting from disk cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, dependencies: List[str] = None) -> None:
        """Set value in disk cache."""
        try:
            file_path = self._get_file_path(key)
            
            # Save compressed data
            with gzip.open(file_path, 'wb') as f:
                pickle.dump(value, f)
            
            # Update metadata
            self._metadata[key] = {
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'access_count': 1,
                'size_bytes': file_path.stat().st_size,
                'dependencies': dependencies or [],
                'ttl_seconds': ttl
            }
            
            self._save_metadata()
            
        except Exception as e:
            logger.error(f"Error setting disk cache: {e}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching pattern."""
        count = 0
        keys_to_remove = []
        
        for key in self._metadata.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            file_path = self._get_file_path(key)
            file_path.unlink(missing_ok=True)
            del self._metadata[key]
            count += 1
        
        if count > 0:
            self._save_metadata()
        
        return count
    
    def get_size(self) -> int:
        """Get the number of entries in the cache."""
        try:
            return len(self._metadata)
        except Exception as e:
            logger.error(f"Error getting disk cache size: {e}")
            return 0
    
    def clear(self) -> None:
        """Clear all entries from the disk cache."""
        try:
            # Remove all cache files
            for key in list(self._metadata.keys()):
                cache_file = self.cache_dir / f"{key}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
            
            # Clear metadata
            self._metadata.clear()
            self._save_metadata()
            
            logger.info("Cleared all entries from disk cache")
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")


class AnalyticsCacheManager:
    """Multi-tier cache manager for analytics calculations."""
    
    def __init__(self, 
                 l1_maxsize: int = 1000,
                 l1_memory_mb: float = 500.0,
                 l2_db_path: str = "analytics_cache.db",  # Keep analytics cache for now 
                 l3_cache_dir: str = "./cache/"):
        
        self.l1_cache = LRUCache(maxsize=l1_maxsize, max_memory_mb=l1_memory_mb)
        self.l2_cache = SQLiteCache(db_path=l2_db_path)
        self.l3_cache = DiskCache(cache_dir=l3_cache_dir)
        self.metrics = CacheMetrics()
        self._lock = threading.RLock()
        
        # Default TTL by tier (seconds)
        self.l1_default_ttl = 900    # 15 minutes
        self.l2_default_ttl = 86400  # 24 hours  
        self.l3_default_ttl = 604800 # 1 week
    
    def get(self, key: str, compute_fn: Callable[[], Any], 
            cache_tiers: List[str] = None, 
            ttl: Optional[int] = None,
            dependencies: List[str] = None) -> Any:
        """Get from cache or compute with tier fallback."""
        
        if cache_tiers is None:
            cache_tiers = ['l1', 'l2', 'l3']
        
        with self._lock:
            self.metrics.total_requests += 1
            
            # Try L1 cache first
            if 'l1' in cache_tiers:
                result = self.l1_cache.get(key)
                if result is not None:
                    self.metrics.l1_hits += 1
                    logger.debug(f"L1 cache hit: {key}")
                    return result
                else:
                    self.metrics.l1_misses += 1
                    logger.debug(f"L1 cache miss: {key}")
            
            # Try L2 cache
            if 'l2' in cache_tiers:
                result = self.l2_cache.get(key)
                if result is not None:
                    self.metrics.l2_hits += 1
                    logger.debug(f"L2 cache hit: {key}")
                    
                    # Promote to L1
                    if 'l1' in cache_tiers:
                        self.l1_cache.set(key, result, ttl=self.l1_default_ttl, dependencies=dependencies)
                    
                    return result
                else:
                    self.metrics.l2_misses += 1
            
            # Try L3 cache
            if 'l3' in cache_tiers:
                result = self.l3_cache.get(key)
                if result is not None:
                    self.metrics.l3_hits += 1
                    logger.debug(f"L3 cache hit: {key}")
                    
                    # Promote to L2 and L1
                    if 'l2' in cache_tiers:
                        self.l2_cache.set(key, result, ttl=self.l2_default_ttl, dependencies=dependencies)
                    if 'l1' in cache_tiers:
                        self.l1_cache.set(key, result, ttl=self.l1_default_ttl, dependencies=dependencies)
                    
                    return result
                else:
                    self.metrics.l3_misses += 1
            
            # Cache miss - compute result
            logger.debug(f"Cache miss - computing: {key}")
            result = compute_fn()
            
            # Store in all requested tiers
            self.set(key, result, cache_tiers=cache_tiers, ttl=ttl, dependencies=dependencies)
            
            return result
    
    def set(self, key: str, value: Any, 
            cache_tiers: List[str] = None,
            ttl: Optional[int] = None,
            dependencies: List[str] = None) -> None:
        """Set value in specified cache tiers."""
        
        if cache_tiers is None:
            cache_tiers = ['l1', 'l2', 'l3']
        
        with self._lock:
            self.metrics.cache_sets += 1
            
            if 'l1' in cache_tiers:
                self.l1_cache.set(key, value, ttl=ttl or self.l1_default_ttl, dependencies=dependencies)
            
            if 'l2' in cache_tiers:
                self.l2_cache.set(key, value, ttl=ttl or self.l2_default_ttl, dependencies=dependencies)
            
            if 'l3' in cache_tiers:
                self.l3_cache.set(key, value, ttl=ttl or self.l3_default_ttl, dependencies=dependencies)
    
    def invalidate_pattern(self, pattern: str) -> Dict[str, int]:
        """Invalidate caches matching pattern across all tiers."""
        with self._lock:
            self.metrics.invalidations += 1
            
            results = {
                'l1': self.l1_cache.invalidate_pattern(pattern),
                'l2': self.l2_cache.invalidate_pattern(pattern), 
                'l3': self.l3_cache.invalidate_pattern(pattern)
            }
            
            logger.info(f"Invalidated pattern '{pattern}': {results}")
            return results
    
    def invalidate_dependencies(self, dependency: str) -> Dict[str, int]:
        """Invalidate caches with specific dependency."""
        with self._lock:
            self.metrics.invalidations += 1
            
            results = {
                'l1': self.l1_cache.invalidate_dependencies(dependency),
                'l2': 0,  # TODO: implement for L2/L3
                'l3': 0
            }
            
            logger.info(f"Invalidated dependency '{dependency}': {results}")
            return results
    
    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        with self._lock:
            # Update memory usage
            self.metrics.memory_usage_mb = self.l1_cache.memory_usage_mb
            return self.metrics
    
    def clear_all(self) -> None:
        """Clear all cache tiers."""
        with self._lock:
            self.l1_cache.clear()
            # Note: L2 and L3 don't have clear methods - would need to implement
            logger.info("Cleared L1 cache")
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired entries across tiers."""
        results = {
            'l1': 0,  # LRU cache handles this automatically
            'l2': self.l2_cache.cleanup_expired(),
            'l3': 0   # Disk cache handles this on access
        }
        
        logger.info(f"Cleaned up expired entries: {results}")
        return results
    
    def cache_import_summaries(self, summaries: Dict[str, Any], import_id: str) -> None:
        """Cache all summaries from import process using simplified SQLite-only storage.
        
        This method is optimized for bulk import of pre-computed summaries during
        the data import process. It bypasses the multi-tier cache and stores
        directly in SQLite for persistence and simplicity.
        
        Args:
            summaries: Dictionary containing summaries organized by time period:
                      {
                          'daily': {metric: {date: stats}},
                          'weekly': {metric: {week: stats}},
                          'monthly': {metric: {month: stats}},
                          'metadata': {...}
                      }
            import_id: Unique identifier for this import session
        
        Raises:
            sqlite3.Error: If database operations fail
        """
        logger.info(f"Caching import summaries for import_id: {import_id}")
        
        with self._lock:
            try:
                # Clear previous import's summaries
                self._clear_previous_import_summaries(import_id)
                
                # Prepare batch data for insertion
                batch_data = []
                
                # Process daily summaries
                for metric, daily_data in summaries.get('daily', {}).items():
                    for date_str, stats in daily_data.items():
                        key = cache_key('daily_summary', metric, date_str)
                        batch_data.append((
                            key,
                            json.dumps(stats),
                            None,  # No TTL for import summaries
                            json.dumps([]),  # No dependencies
                            import_id
                        ))
                
                # Process weekly summaries
                for metric, weekly_data in summaries.get('weekly', {}).items():
                    for week_str, stats in weekly_data.items():
                        key = cache_key('weekly_summary', metric, week_str)
                        batch_data.append((
                            key,
                            json.dumps(stats),
                            None,
                            json.dumps([]),
                            import_id
                        ))
                
                # Process monthly summaries
                for metric, monthly_data in summaries.get('monthly', {}).items():
                    for month_str, stats in monthly_data.items():
                        key = cache_key('monthly_summary', metric, month_str)
                        batch_data.append((
                            key,
                            json.dumps(stats),
                            None,
                            json.dumps([]),
                            import_id
                        ))
                
                # Store metadata
                metadata_key = cache_key('import_metadata', import_id)
                batch_data.append((
                    metadata_key,
                    json.dumps(summaries.get('metadata', {})),
                    None,
                    json.dumps([]),
                    import_id
                ))
                
                # Bulk insert into SQLite cache
                self._bulk_insert_summaries(batch_data)
                
                logger.info(f"Successfully cached {len(batch_data)} summary entries")
                
            except Exception as e:
                logger.error(f"Error caching import summaries: {e}")
                raise
    
    def _clear_previous_import_summaries(self, current_import_id: str) -> None:
        """Clear summaries from previous imports.
        
        Args:
            current_import_id: The current import ID to preserve
        """
        try:
            # Use a custom query to delete summary entries not from current import
            with sqlite3.connect(self.l2_cache.db_path) as conn:
                conn.execute("""
                    DELETE FROM cache_entries 
                    WHERE key LIKE '%_summary|%' 
                    AND key NOT LIKE '%' || ? || '%'
                """, (current_import_id,))
                conn.commit()
                
                deleted = conn.total_changes
                if deleted > 0:
                    logger.info(f"Cleared {deleted} summaries from previous imports")
                    
        except sqlite3.Error as e:
            logger.error(f"Error clearing previous import summaries: {e}")
    
    def _bulk_insert_summaries(self, batch_data: List[Tuple]) -> None:
        """Bulk insert summary data into SQLite cache.
        
        Args:
            batch_data: List of tuples (key, value, ttl, dependencies, import_id)
        """
        try:
            with sqlite3.connect(self.l2_cache.db_path) as conn:
                # Use executemany for efficient bulk insert
                # Note: We need to insert with all required columns
                import time
                current_time = time.time()
                
                # Transform batch_data to include all required columns
                full_batch_data = []
                for key, value, ttl_seconds, dependencies, import_id in batch_data:
                    created_at = current_time
                    last_accessed = current_time
                    access_count = 0
                    size_bytes = len(value) if isinstance(value, (str, bytes)) else 0
                    expires_at = current_time + ttl_seconds if ttl_seconds else None
                    
                    full_batch_data.append((
                        key, value, created_at, last_accessed, access_count,
                        size_bytes, dependencies, ttl_seconds, expires_at, import_id
                    ))
                
                conn.executemany("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, last_accessed, access_count,
                     size_bytes, dependencies, ttl_seconds, expires_at, import_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, full_batch_data)
                
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Error bulk inserting summaries: {e}")
            raise
    
    def get_cache_health_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive cache health and performance metrics.
        
        Returns:
            Dict containing cache health information including hit rates,
            memory usage, entry counts, and performance statistics.
        """
        with self._lock:
            # Get current cache sizes
            l1_size = len(self.l1_cache._cache)
            l1_memory_mb = self.l1_cache._current_memory / (1024 * 1024)
            
            l2_size = self.l2_cache.get_size()
            l3_size = self.l3_cache.get_size()
            
            return {
                'hit_rates': {
                    'l1': self.metrics.l1_hit_rate,
                    'l2': self.metrics.l2_hit_rate,
                    'l3': self.metrics.l3_hit_rate,
                    'overall': self.metrics.overall_hit_rate
                },
                'cache_sizes': {
                    'l1_entries': l1_size,
                    'l1_memory_mb': round(l1_memory_mb, 2),
                    'l1_max_memory_mb': self.l1_cache.max_memory_bytes / (1024 * 1024),
                    'l2_entries': l2_size,
                    'l3_entries': l3_size
                },
                'request_counts': {
                    'total_requests': self.metrics.total_requests,
                    'l1_hits': self.metrics.l1_hits,
                    'l1_misses': self.metrics.l1_misses,
                    'l2_hits': self.metrics.l2_hits,
                    'l2_misses': self.metrics.l2_misses,
                    'l3_hits': self.metrics.l3_hits,
                    'l3_misses': self.metrics.l3_misses
                },
                'health_status': self._get_cache_health_status()
            }
    
    def _get_cache_health_status(self) -> str:
        """Determine overall cache health status."""
        overall_hit_rate = self.metrics.overall_hit_rate
        
        if overall_hit_rate >= 0.9:
            return "excellent"
        elif overall_hit_rate >= 0.7:
            return "good"
        elif overall_hit_rate >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def invalidate_all_cache(self) -> None:
        """Clear all cache tiers completely."""
        with self._lock:
            logger.info("Invalidating all cache entries")
            
            # Clear L1 cache
            self.l1_cache.clear()
            
            # Clear L2 cache
            self.l2_cache.clear()
            
            # Clear L3 cache 
            self.l3_cache.clear()
            
            logger.info("All cache entries invalidated")
    
    def shutdown(self) -> None:
        """Shutdown the cache manager and close all connections."""
        with self._lock:
            logger.info("Shutting down cache manager")
            
            # Clear L1 cache
            self.l1_cache.clear()
            
            # Close L2 cache database connection
            self.l2_cache.close()
            
            # L3 cache doesn't need closing (file-based)
            
            logger.info("Cache manager shutdown complete")


# Global cache manager instance
_cache_manager: Optional[AnalyticsCacheManager] = None


def get_cache_manager() -> AnalyticsCacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = AnalyticsCacheManager()
    return _cache_manager


def get_cache_diagnostics() -> Dict[str, Any]:
    """Get cache health diagnostics from the global cache manager."""
    global _cache_manager
    if _cache_manager is not None:
        try:
            return _cache_manager.get_cache_health_diagnostics()
        except Exception as e:
            logger.error(f"Error getting cache diagnostics: {e}")
            return {}
    return {}

def invalidate_all_cache() -> None:
    """Invalidate all cache entries in the global cache manager."""
    global _cache_manager
    if _cache_manager is not None:
        try:
            _cache_manager.invalidate_all_cache()
            logger.info("Successfully cleared all cache entries")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

def clear_cache_manually() -> bool:
    """Manually clear all cache for user-initiated cache management.
    
    Returns:
        bool: True if cache was cleared successfully, False otherwise.
    """
    try:
        invalidate_all_cache()
        return True
    except Exception as e:
        logger.error(f"Error clearing cache manually: {e}")
        return False

def shutdown_cache_manager() -> None:
    """Shutdown the global cache manager."""
    global _cache_manager
    if _cache_manager is not None:
        try:
            _cache_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during cache manager shutdown: {e}")
        finally:
            _cache_manager = None
            # Force garbage collection to release any remaining references
            import gc
            gc.collect()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, '__name__'):  # Function
            key_parts.append(arg.__name__)
        elif isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif hasattr(arg, 'isoformat'):  # DateTime
            key_parts.append(arg.isoformat())
        else:
            key_parts.append(str(hash(str(arg))))
    
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'isoformat'):  # DateTime
            key_parts.append(f"{k}={v.isoformat()}")
        else:
            key_parts.append(f"{k}={v}")
    
    return "|".join(key_parts)