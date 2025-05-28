"""
Unit tests for analytics cache manager.
Tests multi-tier caching functionality, invalidation, and performance.
"""

import pytest
import tempfile
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.analytics.cache_manager import (
    AnalyticsCacheManager, LRUCache, SQLiteCache, DiskCache,
    CacheEntry, CacheMetrics, cache_key
)


class TestCacheEntry:
    """Test CacheEntry functionality."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and properties."""
        entry = CacheEntry(
            key="test_key",
            value="test_value", 
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=3600
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert not entry.is_expired
        assert entry.age_seconds >= 0
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Non-expiring entry
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=None
        )
        assert not entry.is_expired
        
        # Expired entry
        old_time = datetime.now() - timedelta(seconds=3600)
        entry = CacheEntry(
            key="test",
            value="value", 
            created_at=old_time,
            last_accessed=old_time,
            ttl_seconds=1800  # 30 minutes
        )
        assert entry.is_expired


class TestLRUCache:
    """Test LRU cache functionality."""
    
    def test_lru_cache_basic_operations(self):
        """Test basic get/set operations."""
        cache = LRUCache(maxsize=3, max_memory_mb=1.0)
        
        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Missing key
        assert cache.get("missing") is None
        
        # Size tracking
        assert cache.size == 1
    
    def test_lru_cache_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache(maxsize=2, max_memory_mb=1.0)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size == 2
    
    def test_lru_cache_access_order(self):
        """Test LRU access order updating."""
        cache = LRUCache(maxsize=2, max_memory_mb=1.0)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to make it most recent
        cache.get("key1")
        
        # Add key3, should evict key2 (least recent)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_lru_cache_ttl_expiration(self):
        """Test TTL expiration."""
        cache = LRUCache(maxsize=10, max_memory_mb=1.0, default_ttl=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_lru_cache_pattern_invalidation(self):
        """Test pattern-based invalidation."""
        cache = LRUCache(maxsize=10, max_memory_mb=1.0)
        
        cache.set("user:123:profile", "profile_data")
        cache.set("user:123:settings", "settings_data")
        cache.set("user:456:profile", "other_profile")
        
        # Invalidate all user:123 entries
        invalidated = cache.invalidate_pattern("user:123")
        assert invalidated == 2
        
        assert cache.get("user:123:profile") is None
        assert cache.get("user:123:settings") is None
        assert cache.get("user:456:profile") == "other_profile"
    
    def test_lru_cache_dependency_invalidation(self):
        """Test dependency-based invalidation."""
        cache = LRUCache(maxsize=10, max_memory_mb=1.0)
        
        cache.set("key1", "value1", dependencies=["dep1", "dep2"])
        cache.set("key2", "value2", dependencies=["dep2", "dep3"])
        cache.set("key3", "value3", dependencies=["dep3"])
        
        # Invalidate by dependency
        invalidated = cache.invalidate_dependencies("dep2")
        assert invalidated == 2
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_lru_cache_thread_safety(self):
        """Test thread safety of LRU cache."""
        cache = LRUCache(maxsize=100, max_memory_mb=1.0)
        results = []
        
        def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.set(key, value)
                retrieved = cache.get(key)
                results.append(retrieved == value)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)


class TestSQLiteCache:
    """Test SQLite cache functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    def test_sqlite_cache_basic_operations(self, temp_db):
        """Test basic SQLite cache operations."""
        cache = SQLiteCache(db_path=temp_db)
        
        # Set and get
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        assert result == {"data": "value1"}
        
        # Missing key
        assert cache.get("missing") is None
    
    def test_sqlite_cache_ttl_expiration(self, temp_db):
        """Test TTL expiration in SQLite cache."""
        cache = SQLiteCache(db_path=temp_db)
        
        # Set with short TTL
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_sqlite_cache_cleanup_expired(self, temp_db):
        """Test cleanup of expired entries."""
        cache = SQLiteCache(db_path=temp_db)
        
        # Set entries with different TTLs
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=10)
        
        # Wait for first to expire
        time.sleep(1.1)
        
        # Cleanup should remove expired entry
        cleaned = cache.cleanup_expired()
        assert cleaned >= 1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_sqlite_cache_pattern_invalidation(self, temp_db):
        """Test pattern invalidation in SQLite cache."""
        cache = SQLiteCache(db_path=temp_db)
        
        cache.set("user:123:profile", "profile_data")
        cache.set("user:123:settings", "settings_data")
        cache.set("user:456:profile", "other_profile")
        
        # Invalidate pattern
        invalidated = cache.invalidate_pattern("user:123")
        assert invalidated == 2
        
        assert cache.get("user:123:profile") is None
        assert cache.get("user:123:settings") is None
        assert cache.get("user:456:profile") == "other_profile"


class TestDiskCache:
    """Test disk cache functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_disk_cache_basic_operations(self, temp_dir):
        """Test basic disk cache operations."""
        cache = DiskCache(cache_dir=temp_dir)
        
        # Set and get
        test_data = {"large_dataset": list(range(1000))}
        cache.set("dataset_key", test_data)
        result = cache.get("dataset_key")
        assert result == test_data
        
        # Missing key
        assert cache.get("missing") is None
    
    def test_disk_cache_compression(self, temp_dir):
        """Test disk cache compression."""
        cache = DiskCache(cache_dir=temp_dir)
        
        # Large data should be compressed
        large_data = {"data": "x" * 10000}
        cache.set("large_key", large_data)
        
        # Check file exists and is compressed
        files = list(Path(temp_dir).glob("*.cache.gz"))
        assert len(files) == 1
        
        # Verify data integrity
        result = cache.get("large_key")
        assert result == large_data
    
    def test_disk_cache_metadata(self, temp_dir):
        """Test disk cache metadata handling."""
        cache = DiskCache(cache_dir=temp_dir)
        
        cache.set("key1", "value1", dependencies=["dep1"])
        
        # Check metadata file exists
        metadata_file = Path(temp_dir) / "metadata.json"
        assert metadata_file.exists()
        
        # Verify metadata content
        assert "key1" in cache._metadata
        metadata = cache._metadata["key1"]
        assert metadata["dependencies"] == ["dep1"]
        assert "created_at" in metadata
        assert "size_bytes" in metadata


class TestAnalyticsCacheManager:
    """Test analytics cache manager functionality."""
    
    @pytest.fixture
    def temp_cache_manager(self):
        """Create cache manager with temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            cache_dir = Path(temp_dir) / "cache"
            
            manager = AnalyticsCacheManager(
                l1_maxsize=10,
                l1_memory_mb=1.0,
                l2_db_path=str(db_path),
                l3_cache_dir=str(cache_dir)
            )
            yield manager
    
    def test_cache_manager_tier_fallback(self, temp_cache_manager):
        """Test cache tier fallback logic."""
        manager = temp_cache_manager
        
        # Mock compute function
        compute_fn = MagicMock(return_value="computed_value")
        
        # First call should compute and cache
        result = manager.get("test_key", compute_fn)
        assert result == "computed_value"
        assert compute_fn.call_count == 1
        
        # Second call should hit L1 cache
        result = manager.get("test_key", compute_fn)
        assert result == "computed_value"
        assert compute_fn.call_count == 1  # Should not compute again
    
    def test_cache_manager_tier_promotion(self, temp_cache_manager):
        """Test cache tier promotion."""
        manager = temp_cache_manager
        
        # Set in L3 only
        manager.set("test_key", "test_value", cache_tiers=['l3'])
        
        # Get should promote to L2 and L1
        compute_fn = MagicMock(return_value="computed_value")
        result = manager.get("test_key", compute_fn)
        
        assert result == "test_value"
        assert compute_fn.call_count == 0  # Should not compute
        
        # Should now be in L1
        l1_result = manager.l1_cache.get("test_key")
        assert l1_result == "test_value"
    
    def test_cache_manager_metrics(self, temp_cache_manager):
        """Test cache metrics tracking."""
        manager = temp_cache_manager
        
        compute_fn = MagicMock(return_value="value")
        
        # Generate some cache activity
        manager.get("key1", compute_fn)  # Miss, then cache
        manager.get("key1", compute_fn)  # L1 hit
        manager.get("key2", compute_fn)  # Miss, then cache
        
        metrics = manager.get_metrics()
        assert metrics.total_requests == 3
        assert metrics.l1_hits == 1
        assert metrics.l1_misses >= 1
    
    def test_cache_manager_invalidation(self, temp_cache_manager):
        """Test cache invalidation across tiers."""
        manager = temp_cache_manager
        
        # Populate all tiers
        manager.set("user:123:profile", "profile_data")
        manager.set("user:123:settings", "settings_data")
        manager.set("user:456:profile", "other_data")
        
        # Invalidate pattern
        results = manager.invalidate_pattern("user:123")
        
        # Should invalidate across all tiers
        assert results['l1'] >= 0
        assert results['l2'] >= 0
        assert results['l3'] >= 0
        
        # Verify invalidation
        compute_fn = MagicMock(return_value="new_value")
        result = manager.get("user:123:profile", compute_fn)
        assert result == "new_value"  # Should compute, not cache hit


class TestCacheKey:
    """Test cache key generation."""
    
    def test_cache_key_basic(self):
        """Test basic cache key generation."""
        key = cache_key("func", "arg1", "arg2")
        assert isinstance(key, str)
        assert "func" in key
        assert "arg1" in key
        assert "arg2" in key
    
    def test_cache_key_kwargs(self):
        """Test cache key with keyword arguments."""
        key = cache_key("func", param1="value1", param2="value2")
        assert "param1=value1" in key
        assert "param2=value2" in key
    
    def test_cache_key_datetime(self):
        """Test cache key with datetime objects."""
        dt = datetime(2025, 1, 1, 12, 0, 0)
        key = cache_key("func", dt)
        assert "2025-01-01T12:00:00" in key
    
    def test_cache_key_consistency(self):
        """Test cache key consistency."""
        # Same inputs should generate same key
        key1 = cache_key("func", "arg1", param="value")
        key2 = cache_key("func", "arg1", param="value")
        assert key1 == key2
        
        # Different inputs should generate different keys
        key3 = cache_key("func", "arg2", param="value")
        assert key1 != key3


class TestCacheIntegration:
    """Integration tests for cache system."""
    
    def test_cache_with_real_data(self):
        """Test cache with realistic data structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AnalyticsCacheManager(
                l1_maxsize=5,
                l1_memory_mb=1.0,
                l2_db_path=str(Path(temp_dir) / "test.db"),
                l3_cache_dir=str(Path(temp_dir) / "cache")
            )
            
            # Simulate analytics data
            analytics_data = {
                "metric": "steps",
                "statistics": {
                    "mean": 8500.5,
                    "median": 8200,
                    "std": 1200.3,
                    "min": 5000,
                    "max": 15000
                },
                "trend": "increasing",
                "confidence": 0.95
            }
            
            def compute_analytics():
                return analytics_data
            
            # Test caching
            result1 = manager.get("analytics:steps:2025-01", compute_analytics)
            result2 = manager.get("analytics:steps:2025-01", compute_analytics)
            
            assert result1 == analytics_data
            assert result2 == analytics_data
            
            # Should have cache hit
            metrics = manager.get_metrics()
            assert metrics.l1_hits > 0 or metrics.l2_hits > 0 or metrics.l3_hits > 0
    
    def test_cache_memory_limits(self):
        """Test cache memory limit enforcement."""
        # Very small memory limit
        manager = AnalyticsCacheManager(l1_memory_mb=0.001)  # 1KB limit
        
        # Try to cache large objects
        large_data = {"data": "x" * 10000}  # ~10KB
        
        def compute_large():
            return large_data
        
        # Should not cache due to size limit
        result = manager.get("large_key", compute_large)
        assert result == large_data
        
        # L1 cache should be empty or very small
        assert manager.l1_cache.size <= 1
    
    def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        manager = AnalyticsCacheManager(l1_maxsize=100)
        results = []
        
        def worker(worker_id):
            def compute_fn():
                return f"result_{worker_id}"
            
            # Each worker accesses different keys
            for i in range(5):
                key = f"worker_{worker_id}_key_{i}"
                result = manager.get(key, compute_fn)
                results.append(result.startswith(f"result_{worker_id}"))
        
        # Run concurrent workers
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(results) == 15  # 3 workers * 5 operations each