"""
Transaction and concurrency testing helpers.
Provides utilities for testing database transactions, rollbacks, and concurrent operations.
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Callable, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


@contextmanager
def transaction_rollback_test(conn):
    """Test transaction rollback behavior."""
    savepoint = f"test_savepoint_{int(time.time() * 1000000)}"
    try:
        conn.execute(f'SAVEPOINT {savepoint}')
        yield conn
        # Force rollback by raising exception
        raise Exception("Test rollback")
    except Exception:
        conn.execute(f'ROLLBACK TO {savepoint}')
        conn.execute(f'RELEASE {savepoint}')
    finally:
        # Verify rollback worked by checking state
        pass


@contextmanager
def isolated_transaction(conn):
    """Create isolated transaction for testing."""
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


class ConcurrentTestHelper:
    """Helper for running concurrent database operations in tests."""
    
    def __init__(self, db_factory=None):
        self.db_factory = db_factory
        self.results: List[Any] = []
        self.errors: List[Exception] = []
        self._lock = threading.Lock()
        
    def run_concurrent(self, func: Callable, num_threads: int = 10, *args, **kwargs) -> List[Any]:
        """Run function in multiple threads and collect results."""
        self.results.clear()
        self.errors.clear()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                future = executor.submit(self._run_with_error_capture, func, i, *args, **kwargs)
                futures.append(future)
            
            # Wait for all threads to complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        with self._lock:
                            self.results.append(result)
                except Exception as e:
                    with self._lock:
                        self.errors.append(e)
        
        if self.errors:
            error_msg = f"Concurrent errors ({len(self.errors)}): {[str(e) for e in self.errors[:3]]}"
            raise Exception(error_msg)
        
        return self.results
    
    def _run_with_error_capture(self, func: Callable, thread_id: int, *args, **kwargs):
        """Run function with error capture."""
        try:
            return func(thread_id, *args, **kwargs)
        except Exception as e:
            with self._lock:
                self.errors.append(e)
            raise


class DatabaseCorruptionTester:
    """Helper for testing database corruption recovery."""
    
    @staticmethod
    def corrupt_database(db_path, corruption_type='random'):
        """Corrupt database file for testing recovery."""
        import os
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        file_size = os.path.getsize(db_path)
        
        if corruption_type == 'random':
            # Corrupt random bytes in the middle
            with open(db_path, 'r+b') as f:
                f.seek(file_size // 2)
                f.write(b'CORRUPTED_DATA_123456789')
        elif corruption_type == 'header':
            # Corrupt database header
            with open(db_path, 'r+b') as f:
                f.seek(0)
                f.write(b'NOT_SQLITE_HEADER!!')
        elif corruption_type == 'truncate':
            # Truncate file
            with open(db_path, 'r+b') as f:
                f.truncate(file_size // 2)
    
    @staticmethod
    def is_database_corrupted(db_path) -> bool:
        """Check if database is corrupted."""
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute('PRAGMA integrity_check').fetchone()
                return False
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            return True
    
    @staticmethod
    def attempt_recovery(db_path, backup_path=None):
        """Attempt to recover corrupted database."""
        if backup_path and os.path.exists(backup_path):
            # Restore from backup
            import shutil
            shutil.copy2(backup_path, db_path)
            return True
        else:
            # Create new empty database
            os.remove(db_path)
            with sqlite3.connect(db_path) as conn:
                # Initialize with basic schema
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                ''')
            return True


class ConcurrentCacheTestHelper:
    """Specialized helper for testing concurrent cache operations."""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.operation_results = []
        self._lock = threading.Lock()
    
    def run_concurrent_operations(self, operations: List[dict], num_threads: int = 5):
        """Run multiple cache operations concurrently."""
        self.operation_results.clear()
        
        def worker(thread_id):
            results = []
            for op in operations:
                try:
                    if op['type'] == 'set':
                        self.cache_manager.set(op['key'], op['value'])
                        results.append(('set', op['key'], True))
                    elif op['type'] == 'get':
                        value = self.cache_manager.get(op['key'])
                        results.append(('get', op['key'], value))
                    elif op['type'] == 'invalidate':
                        count = self.cache_manager.invalidate_pattern(op['pattern'])
                        results.append(('invalidate', op['pattern'], count))
                except Exception as e:
                    results.append(('error', op.get('key', op.get('pattern')), str(e)))
            return results
        
        # Run operations in multiple threads
        helper = ConcurrentTestHelper()
        all_results = helper.run_concurrent(worker, num_threads)
        
        # Flatten results
        for thread_results in all_results:
            with self._lock:
                self.operation_results.extend(thread_results)
        
        return self.operation_results
    
    def verify_consistency(self, expected_state: dict):
        """Verify cache state is consistent after concurrent operations."""
        for key, expected_value in expected_state.items():
            actual_value = self.cache_manager.get(key)
            if actual_value != expected_value:
                raise AssertionError(f"Inconsistent state for {key}: expected {expected_value}, got {actual_value}")


# Utility functions for test isolation
def ensure_test_isolation():
    """Ensure tests don't interfere with each other."""
    import os
    
    # Clean up any leftover test databases
    test_patterns = ['test_*.db', 'temp_*.db', '*_test.db']
    for pattern in test_patterns:
        import glob
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except (OSError, FileNotFoundError):
                pass


@contextmanager
def temporary_environment_override(**env_vars):
    """Temporarily override environment variables."""
    import os
    
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = str(value)
    
    try:
        yield
    finally:
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value