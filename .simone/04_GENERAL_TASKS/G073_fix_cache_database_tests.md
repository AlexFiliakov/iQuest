# G073: Fix Cache Manager and Database Test Issues

## Status: ACTIVE
Priority: HIGH
Type: BUG_FIX
Parallel: Yes (can work on database layer independently)

## Problem Summary
Cache and database tests failing:
- CacheManager tests (11 failures)
- SQLite cache tests (TTL expiration, cleanup, invalidation)
- Database corruption recovery tests
- Transaction rollback tests

## Root Cause Analysis
1. Test database not properly isolated
2. Cache TTL timing issues in tests
3. Missing database schema in test environment
4. Concurrent test execution conflicts

## Implementation Options Analysis

### Option A: In-Memory SQLite for All Tests
**Pros:**
- Fast test execution
- No disk I/O
- Automatic cleanup
- Perfect isolation

**Cons:**
- May not catch file-based issues
- Different behavior from production
- Memory constraints for large tests
- Some SQLite features unavailable

### Option B: Temporary File Databases
**Pros:**
- Closer to production behavior
- Supports all SQLite features
- Can test file permissions
- Better for integration tests

**Cons:**
- Slower than in-memory
- Requires cleanup
- Potential file system issues
- OS-specific behavior

### Option C: Hybrid Approach (Recommended)
**Pros:**
- Use in-memory for unit tests
- Use temp files for integration
- Best of both approaches
- Flexible per test needs

**Cons:**
- More complex setup
- Two patterns to maintain

## Detailed Implementation Plan

### Phase 1: Database Test Infrastructure
1. **Create database test factory**
   ```python
   # tests/fixtures/database.py
   import sqlite3
   import tempfile
   from contextlib import contextmanager
   from pathlib import Path
   import pytest
   
   class TestDatabaseFactory:
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
               CREATE TABLE IF NOT EXISTS cache (
                   key TEXT PRIMARY KEY,
                   value BLOB,
                   expires_at REAL,
                   created_at REAL DEFAULT (julianday('now'))
               );
               
               CREATE TABLE IF NOT EXISTS health_data (
                   id INTEGER PRIMARY KEY,
                   date TEXT NOT NULL,
                   metric TEXT NOT NULL,
                   value REAL NOT NULL,
                   UNIQUE(date, metric)
               );
               
               CREATE INDEX idx_cache_expires ON cache(expires_at);
               CREATE INDEX idx_health_date ON health_data(date);
           ''')
           conn.commit()
   ```

2. **Database isolation fixtures**
   ```python
   # tests/conftest.py additions
   @pytest.fixture
   def memory_db():
       """In-memory database for fast unit tests."""
       with TestDatabaseFactory.in_memory_db() as conn:
           yield conn
   
   @pytest.fixture
   def file_db():
       """File-based database for integration tests."""
       with TestDatabaseFactory.temp_file_db() as (conn, path):
           yield conn, path
   
   @pytest.fixture(autouse=True)
   def isolate_tests(monkeypatch):
       """Ensure each test gets fresh database."""
       # Prevent tests from using production database
       monkeypatch.setenv('HEALTH_DB_PATH', ':memory:')
   ```

### Phase 2: Fix Cache TTL Timing Issues
1. **Time mocking utilities**
   ```python
   # tests/helpers/time_helpers.py
   import time
   from unittest.mock import patch
   from contextlib import contextmanager
   
   class TimeMocker:
       def __init__(self):
           self.current_time = time.time()
           
       def advance(self, seconds):
           """Advance mocked time by seconds."""
           self.current_time += seconds
           
       def get_time(self):
           """Get current mocked time."""
           return self.current_time
   
   @contextmanager
   def mock_time():
       """Context manager for time mocking."""
       mocker = TimeMocker()
       with patch('time.time', mocker.get_time):
           yield mocker
   ```

2. **Fix cache TTL tests**
   ```python
   # Example fixed test
   def test_cache_ttl_expiration():
       with mock_time() as time_mocker:
           cache = CacheManager(ttl_seconds=60)
           
           # Add item to cache
           cache.set('key1', 'value1')
           
           # Verify item exists
           assert cache.get('key1') == 'value1'
           
           # Advance time past TTL
           time_mocker.advance(61)
           
           # Verify item expired
           assert cache.get('key1') is None
   ```

### Phase 3: Transaction and Concurrency Testing
1. **Transaction test helpers**
   ```python
   # tests/helpers/transaction_helpers.py
   import sqlite3
   import threading
   from contextlib import contextmanager
   
   @contextmanager
   def transaction_rollback_test(conn):
       """Test transaction rollback behavior."""
       try:
           conn.execute('BEGIN')
           yield conn
           # Force rollback
           raise Exception("Test rollback")
       except:
           conn.rollback()
       finally:
           # Verify rollback worked
           pass
   
   class ConcurrentTestHelper:
       def __init__(self, db_factory):
           self.db_factory = db_factory
           self.results = []
           self.errors = []
           
       def run_concurrent(self, func, num_threads=10):
           """Run function in multiple threads."""
           threads = []
           for i in range(num_threads):
               t = threading.Thread(
                   target=self._run_with_error_capture,
                   args=(func, i)
               )
               threads.append(t)
               t.start()
           
           for t in threads:
               t.join()
               
           if self.errors:
               raise Exception(f"Concurrent errors: {self.errors}")
   ```

2. **Database corruption recovery tests**
   ```python
   # tests/test_database_recovery.py
   def test_corruption_recovery(file_db):
       conn, db_path = file_db
       
       # Corrupt the database file
       conn.close()
       with open(db_path, 'r+b') as f:
           f.seek(100)
           f.write(b'CORRUPT')
       
       # Test recovery mechanism
       recovery = DatabaseRecovery(db_path)
       assert recovery.is_corrupted()
       
       recovery.attempt_recovery()
       assert recovery.is_healthy()
   ```

### Phase 4: Cache Manager Specific Fixes
1. **Fix tier promotion/fallback tests**
   ```python
   # tests/test_cache_manager.py
   class TestCacheManager:
       def test_tier_promotion(self, memory_db):
           cache = CacheManager(
               memory_size=100,
               disk_db=memory_db
           )
           
           # Fill memory tier
           for i in range(150):
               cache.set(f'key{i}', f'value{i}')
           
           # Verify promotion to disk
           stats = cache.get_stats()
           assert stats['memory_items'] <= 100
           assert stats['disk_items'] >= 50
       
       def test_cache_invalidation(self):
           cache = CacheManager()
           
           # Add items with pattern
           cache.set('user:1:profile', 'data1')
           cache.set('user:1:settings', 'data2')
           cache.set('user:2:profile', 'data3')
           
           # Invalidate by pattern
           cache.invalidate_pattern('user:1:*')
           
           assert cache.get('user:1:profile') is None
           assert cache.get('user:1:settings') is None
           assert cache.get('user:2:profile') == 'data3'
   ```

### Phase 5: Performance and Stress Testing
1. **Cache performance benchmarks**
   ```python
   # tests/performance/test_cache_performance.py
   import pytest
   import time
   
   @pytest.mark.performance
   class TestCachePerformance:
       def test_cache_throughput(self, benchmark):
           cache = CacheManager()
           
           def cache_operations():
               for i in range(1000):
                   cache.set(f'key{i}', f'value{i}')
                   cache.get(f'key{i % 1000}')
           
           result = benchmark(cache_operations)
           assert result.stats['mean'] < 0.1  # 100ms
       
       def test_concurrent_cache_access(self):
           cache = CacheManager()
           helper = ConcurrentTestHelper()
           
           def concurrent_ops(thread_id):
               for i in range(100):
                   key = f'thread{thread_id}:key{i}'
                   cache.set(key, f'value{i}')
                   assert cache.get(key) == f'value{i}'
           
           helper.run_concurrent(concurrent_ops, num_threads=20)
   ```

### Phase 6: Test Documentation and Patterns
1. **Create cache testing guide**
   ```markdown
   # Cache Testing Guide
   
   ## Test Categories
   1. Unit tests - Use in-memory DB
   2. Integration tests - Use file DB
   3. Performance tests - Use production-like config
   
   ## Common Patterns
   - Always use fixtures for database setup
   - Mock time for TTL tests
   - Use transactions for isolation
   - Clean up resources in finally blocks
   ```

## Affected Files (Detailed)
- **Test files to fix:**
  - `tests/test_cache_manager.py`
  - `tests/test_sqlite_cache.py`
  - `tests/test_database_recovery.py`
  - `tests/performance/test_cache_performance.py`

- **New files to create:**
  - `tests/fixtures/database.py`
  - `tests/helpers/time_helpers.py`
  - `tests/helpers/transaction_helpers.py`
  - `docs/cache_testing_guide.md`

## Risk Mitigation
1. **Isolation verification**
   - Run tests in random order
   - Verify no shared state
   - Check for file cleanup

2. **Platform compatibility**
   - Test on Windows/Linux/Mac
   - Handle path differences
   - Check file permissions

## Success Criteria
- [ ] All 11 CacheManager tests passing
- [ ] SQLite TTL tests reliable (no flakes)
- [ ] Transaction tests properly isolated
- [ ] Concurrent tests pass consistently
- [ ] Performance benchmarks established
- [ ] Zero test database files left after runs
- [ ] Testing guide reviewed and approved