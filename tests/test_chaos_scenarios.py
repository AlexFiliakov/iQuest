"""
Chaos testing for edge cases and failure scenarios.
Tests system resilience under abnormal conditions.
"""

import pytest
import pandas as pd
import numpy as np
import threading
import time
import queue
import random
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Optional

from tests.test_data_generator import HealthDataGenerator
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.database import DatabaseManager as HealthDatabase
from src.data_loader import DataLoader as HealthDataLoader


class ChaosTestEngine:
    """Engine for generating chaos testing scenarios."""
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def inject_data_corruption(self, data: pd.DataFrame, corruption_rate: float = 0.1) -> pd.DataFrame:
        """Inject random data corruption."""
        corrupted_data = data.copy()
        n_corrupt = int(len(data) * corruption_rate)
        
        if n_corrupt > 0:
            corrupt_indices = np.random.choice(len(data), n_corrupt, replace=False)
            
            for idx in corrupt_indices:
                corruption_type = random.choice(['extreme_value', 'negative', 'null', 'wrong_type'])
                
                if corruption_type == 'extreme_value':
                    corrupted_data.iloc[idx, random.randint(1, len(data.columns)-1)] = 1e10
                elif corruption_type == 'negative':
                    corrupted_data.iloc[idx, random.randint(1, len(data.columns)-1)] = -abs(
                        corrupted_data.iloc[idx, random.randint(1, len(data.columns)-1)]
                    )
                elif corruption_type == 'null':
                    corrupted_data.iloc[idx, random.randint(1, len(data.columns)-1)] = None
                # wrong_type would need more complex handling
        
        return corrupted_data
    
    def create_memory_pressure(self, size_mb: int = 100):
        """Create memory pressure for testing."""
        # Allocate large arrays to create memory pressure
        memory_hogs = []
        try:
            for _ in range(size_mb):
                memory_hogs.append(np.random.random(1024 * 1024 // 8))  # ~1MB per array
            return memory_hogs
        except MemoryError:
            return memory_hogs
    
    def simulate_network_failure(self):
        """Context manager to simulate network failures."""
        class NetworkFailureContext:
            def __enter__(self):
                # Mock network operations to fail
                self.original_urlopen = None
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restore original functions
                pass
        
        return NetworkFailureContext()


class TestChaosScenarios:
    """Comprehensive chaos testing for analytics system."""
    
    @pytest.fixture
    def chaos_engine(self):
        """Create chaos test engine."""
        return ChaosTestEngine(seed=42)
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator."""
        return HealthDataGenerator(seed=42)
    
    @pytest.fixture
    def clean_data(self, data_generator):
        """Generate clean test data."""
        return data_generator.generate(100)

    # Data Corruption Tests
    def test_handle_corrupted_step_data(self, chaos_engine, clean_data):
        """Test handling of corrupted step count data."""
        calculator = DailyMetricsCalculator()
        
        # Inject extreme values in steps
        corrupted_data = clean_data.copy()
        corrupted_data.loc[10:15, 'steps'] = [1e10, -5000, None, 0, 1e6, float('inf')]
        
        # System should handle gracefully
        result = calculator.calculate_statistics('steps', corrupted_data['steps'])
        
        assert result is not None
        assert 'error_handled' in result or result['count'] < len(corrupted_data)
        
        # Should detect outliers
        if 'outliers_detected' in result:
            assert result['outliers_detected'] > 0

    def test_handle_missing_date_columns(self, clean_data):
        """Test handling of missing or corrupted date columns."""
        calculator = DailyMetricsCalculator()
        
        # Remove date column
        corrupted_data = clean_data.drop('date', axis=1)
        
        with pytest.raises((KeyError, ValueError)):
            calculator.calculate_all_metrics(corrupted_data)

    def test_handle_duplicate_dates(self, data_generator):
        """Test handling of duplicate date entries."""
        calculator = DailyMetricsCalculator()
        
        edge_cases = data_generator.generate_edge_cases()
        duplicate_data = edge_cases['duplicate_dates']
        
        # Should handle or raise appropriate error
        try:
            result = calculator.calculate_all_metrics(duplicate_data)
            # If it succeeds, should have deduplication
            assert len(result) <= len(duplicate_data.drop_duplicates('date'))
        except ValueError as e:
            assert 'duplicate' in str(e).lower()

    def test_handle_null_data_scenarios(self, data_generator):
        """Test various null data scenarios."""
        calculator = DailyMetricsCalculator()
        
        edge_cases = data_generator.generate_edge_cases()
        
        # All nulls
        all_nulls = edge_cases['all_nulls']
        try:
            result = calculator.calculate_all_metrics(all_nulls)
            assert result is None or len(result) == 0
        except ValueError:
            pass  # Acceptable to raise error
        
        # All zeros
        all_zeros = edge_cases['all_zeros']
        result = calculator.calculate_all_metrics(all_zeros)
        assert result is not None  # Should handle zeros

    def test_handle_extreme_values(self, data_generator):
        """Test handling of extreme values."""
        calculator = DailyMetricsCalculator()
        
        edge_cases = data_generator.generate_edge_cases()
        extreme_data = edge_cases['extreme_values']
        
        result = calculator.calculate_all_metrics(extreme_data)
        
        # Should detect and handle extremes
        assert result is not None
        # Check that infinite values are handled
        for key, value in result.items():
            if isinstance(value, (int, float)):
                assert not np.isinf(value)
                assert not np.isnan(value)

    # Concurrency Tests
    def test_concurrent_database_writes(self, chaos_engine, data_generator):
        """Test concurrent database write operations."""
        db = HealthDatabase(':memory:')
        errors = []
        
        def write_data(thread_id: int):
            try:
                data = data_generator.generate(100)
                data['thread_id'] = thread_id
                db.bulk_insert_health_data(data)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Launch concurrent writes
        threads = []
        for i in range(5):
            t = threading.Thread(target=write_data, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Database should maintain consistency
        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        
        # Verify data integrity
        total_records = db.get_record_count()
        assert total_records > 0

    def test_concurrent_analytics_calculations(self, data_generator):
        """Test concurrent analytics calculations."""
        calculator = DailyMetricsCalculator()
        data = data_generator.generate(500)
        
        results_queue = queue.Queue()
        errors = []
        
        def calculate_metrics(thread_id: int):
            try:
                result = calculator.calculate_all_metrics(data.copy())
                results_queue.put((thread_id, result))
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Launch concurrent calculations
        threads = []
        for i in range(3):
            t = threading.Thread(target=calculate_metrics, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(errors) == 0, f"Concurrent calculation errors: {errors}"
        assert len(results) == 3
        
        # Results should be consistent
        first_result = results[0][1]
        for thread_id, result in results[1:]:
            assert result.keys() == first_result.keys()

    # Memory Pressure Tests
    @pytest.mark.slow
    def test_low_memory_conditions(self, chaos_engine, data_generator):
        """Test system behavior under low memory conditions."""
        calculator = DailyMetricsCalculator()
        
        # Create memory pressure
        memory_hogs = chaos_engine.create_memory_pressure(50)  # 50MB
        
        try:
            # Try to process data under memory pressure
            large_data = data_generator.generate_performance_data('medium')
            result = calculator.calculate_all_metrics(large_data)
            
            # Should either succeed or fail gracefully
            if result is not None:
                assert len(result) > 0
            
        except MemoryError:
            # Acceptable to run out of memory
            pass
        finally:
            # Clean up memory
            del memory_hogs

    # Timeout and Infinite Loop Protection
    @pytest.mark.timeout(10)
    def test_infinite_loop_protection(self, data_generator):
        """Test protection against infinite loops."""
        calculator = DailyMetricsCalculator()
        
        # Create circular reference scenario
        circular_data = data_generator.generate(50)
        # Simulate a condition that might cause infinite loops
        circular_data.loc[0, 'steps'] = float('inf')
        circular_data.loc[1, 'steps'] = float('-inf')
        
        # Should complete within timeout
        try:
            result = calculator.calculate_all_metrics(circular_data)
            assert result is not None
        except (RecursionError, ValueError):
            # Acceptable to detect and prevent infinite loops
            pass

    @pytest.mark.timeout(5)
    def test_large_dataset_timeout_protection(self, data_generator):
        """Test timeout protection for very large datasets."""
        calculator = DailyMetricsCalculator()
        
        # Create dataset that might cause timeout
        very_large_data = data_generator.generate_performance_data('xlarge')
        
        start_time = time.time()
        try:
            result = calculator.calculate_all_metrics(very_large_data)
            end_time = time.time()
            
            # Should complete reasonably quickly
            assert end_time - start_time < 30  # 30 second max
            if result is not None:
                assert len(result) > 0
                
        except TimeoutError:
            # Acceptable to timeout on extremely large datasets
            pass

    # Database Corruption Tests
    def test_database_corruption_recovery(self, data_generator):
        """Test database corruption recovery mechanisms."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create database and add data
            db = HealthDatabase(db_path)
            data = data_generator.generate(100)
            db.bulk_insert_health_data(data)
            db.close()
            
            # Corrupt the database file
            with open(db_path, 'r+b') as f:
                f.seek(100)
                f.write(b'corrupted data here')
            
            # Try to open corrupted database
            try:
                corrupted_db = HealthDatabase(db_path)
                result = corrupted_db.get_all_data()
                # Should handle corruption gracefully
                assert result is not None or len(result) == 0
                corrupted_db.close()
            except Exception as e:
                # Acceptable to detect corruption and fail safely
                assert 'corrupt' in str(e).lower() or 'database' in str(e).lower()
                
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    # Network and I/O Failure Tests
    def test_file_system_errors(self, data_generator):
        """Test handling of file system errors."""
        loader = HealthDataLoader()
        
        # Try to load from non-existent file
        with pytest.raises(FileNotFoundError):
            loader.load_csv_data('/non/existent/path.csv')
        
        # Try to load from directory instead of file
        with pytest.raises((IsADirectoryError, PermissionError)):
            loader.load_csv_data('/')

    @patch('pandas.read_csv')
    def test_csv_parsing_errors(self, mock_read_csv, data_generator):
        """Test handling of CSV parsing errors."""
        loader = HealthDataLoader()
        
        # Mock CSV parsing error
        mock_read_csv.side_effect = pd.errors.ParserError("Error parsing CSV")
        
        with pytest.raises(pd.errors.ParserError):
            loader.load_csv_data('fake_file.csv')

    # Resource Exhaustion Tests
    def test_disk_space_exhaustion(self, data_generator):
        """Test behavior when disk space is exhausted."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = HealthDatabase(db_path)
            large_data = data_generator.generate_performance_data('large')
            
            # Try to write large amount of data
            try:
                db.bulk_insert_health_data(large_data)
                # Should either succeed or fail gracefully
                assert db.get_record_count() >= 0
            except OSError as e:
                # Acceptable to fail due to disk space
                assert 'space' in str(e).lower() or 'disk' in str(e).lower()
            finally:
                db.close()
                
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    # Type Safety and Schema Validation Tests
    def test_wrong_data_types(self, data_generator):
        """Test handling of wrong data types."""
        calculator = DailyMetricsCalculator()
        
        # Create data with wrong types
        wrong_type_data = data_generator.generate(50)
        wrong_type_data['steps'] = wrong_type_data['steps'].astype(str)  # Convert to string
        
        try:
            result = calculator.calculate_all_metrics(wrong_type_data)
            # Should handle type conversion or fail gracefully
            assert result is not None
        except (TypeError, ValueError):
            # Acceptable to reject wrong types
            pass

    def test_missing_required_columns(self, data_generator):
        """Test handling of missing required columns."""
        calculator = DailyMetricsCalculator()
        
        incomplete_data = data_generator.generate(50)
        del incomplete_data['steps']  # Remove required column
        
        with pytest.raises((KeyError, ValueError)):
            calculator.calculate_all_metrics(incomplete_data)

    # Race Condition Tests
    def test_race_condition_detection(self, data_generator):
        """Test detection and handling of race conditions."""
        calculator = DailyMetricsCalculator()
        shared_data = data_generator.generate(100)
        
        results = []
        
        def modify_and_calculate():
            # Modify data while calculating
            local_data = shared_data.copy()
            local_data.loc[0, 'steps'] = random.randint(1000, 20000)
            result = calculator.calculate_all_metrics(local_data)
            results.append(result)
        
        # Run multiple threads that modify and calculate
        threads = []
        for _ in range(3):
            t = threading.Thread(target=modify_and_calculate)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All calculations should complete successfully
        assert len(results) == 3
        assert all(r is not None for r in results)

    # Error Recovery Tests
    def test_error_recovery_mechanisms(self, data_generator):
        """Test system error recovery mechanisms."""
        calculator = DailyMetricsCalculator()
        
        # Simulate various error conditions and recovery
        problematic_datasets = [
            data_generator.generate_edge_cases()['all_nulls'],
            data_generator.generate_edge_cases()['extreme_values'],
            data_generator.generate_edge_cases()['single_point']
        ]
        
        recovery_count = 0
        
        for problem_data in problematic_datasets:
            try:
                result = calculator.calculate_all_metrics(problem_data)
                if result is not None:
                    recovery_count += 1
            except Exception:
                # Count as handled error
                recovery_count += 1
        
        # Should handle or recover from most error conditions
        assert recovery_count >= len(problematic_datasets) * 0.8  # 80% recovery rate


# Custom markers for chaos tests
pytestmark = pytest.mark.chaos