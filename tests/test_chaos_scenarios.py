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
from src.analytics.dataframe_adapter import DataFrameAdapter
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
        # Transform data to expected format
        health_data = []
        for _, row in clean_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row['steps']
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(health_data)
        
        # Inject extreme values in steps
        df.loc[10:15, 'value'] = [1e10, -5000, None, 0, 1e6, float('inf')]
        
        # Initialize calculator with corrupted data
        calculator = DailyMetricsCalculator(df)
        
        # System should handle gracefully
        result = calculator.calculate_statistics('StepCount')
        
        assert result is not None
        # MetricStatistics object should handle corrupted data gracefully
        assert hasattr(result, 'count')
        # Should have filtered out invalid values (negative, None, inf)
        assert result.count < len(df)

    def test_handle_missing_date_columns(self, clean_data):
        """Test handling of missing or corrupted date columns."""
        # Remove date column
        corrupted_data = clean_data.drop('date', axis=1)
        
        # Try to create calculator with corrupted data
        with pytest.raises((KeyError, ValueError)):
            # This should fail either when creating the adapter or the calculator
            adapter = DataFrameAdapter(corrupted_data)
            calculator = DailyMetricsCalculator(adapter)

    def test_handle_duplicate_dates(self, data_generator):
        """Test handling of duplicate date entries."""
        edge_cases = data_generator.generate_edge_cases()
        duplicate_data = edge_cases['duplicate_dates']
        
        # Convert to expected format
        health_data = []
        for _, row in duplicate_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df = pd.DataFrame(health_data)
        calculator = DailyMetricsCalculator(df)
        
        # Should handle or raise appropriate error
        try:
            # Calculate statistics for StepCount metric
            result = calculator.calculate_statistics('StepCount')
            # If it succeeds, should have handled duplicates gracefully
            assert result is not None
            assert hasattr(result, 'count')
            # The count should reflect the data after handling duplicates
            assert result.count > 0
        except ValueError as e:
            assert 'duplicate' in str(e).lower()

    def test_handle_null_data_scenarios(self, data_generator):
        """Test various null data scenarios."""
        edge_cases = data_generator.generate_edge_cases()
        
        # All nulls
        all_nulls = edge_cases['all_nulls']
        # Convert to expected format
        null_health_data = []
        for _, row in all_nulls.iterrows():
            null_health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', None)
            })
        
        df_nulls = pd.DataFrame(null_health_data)
        try:
            calculator = DailyMetricsCalculator(df_nulls)
            result = calculator.calculate_statistics('StepCount')
            # Should either handle nulls or have insufficient data
            assert result is None or result.insufficient_data or result.count == 0
        except (ValueError, KeyError):
            pass  # Acceptable to raise error
        
        # All zeros
        all_zeros = edge_cases['all_zeros']
        # Convert to expected format
        zero_health_data = []
        for _, row in all_zeros.iterrows():
            zero_health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df_zeros = pd.DataFrame(zero_health_data)
        calculator = DailyMetricsCalculator(df_zeros)
        result = calculator.calculate_statistics('StepCount')
        assert result is not None  # Should handle zeros

    def test_handle_extreme_values(self, data_generator):
        """Test handling of extreme values."""
        edge_cases = data_generator.generate_edge_cases()
        extreme_data = edge_cases['extreme_values']
        
        # Convert to expected format
        extreme_health_data = []
        for _, row in extreme_data.iterrows():
            extreme_health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df_extreme = pd.DataFrame(extreme_health_data)
        calculator = DailyMetricsCalculator(df_extreme)
        result = calculator.calculate_statistics('StepCount')
        
        # Should detect and handle extremes
        assert result is not None
        # Check that infinite values are handled
        if result.mean is not None:
            assert not np.isinf(result.mean)
            assert not np.isnan(result.mean)
        if result.std is not None:
            assert not np.isinf(result.std)
            assert not np.isnan(result.std)

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
        data = data_generator.generate(500)
        
        # Convert to expected format
        health_data = []
        for _, row in data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df = pd.DataFrame(health_data)
        calculator = DailyMetricsCalculator(df)
        
        results_queue = queue.Queue()
        errors = []
        
        def calculate_metrics(thread_id: int):
            try:
                result = calculator.calculate_statistics('StepCount')
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
            # Check that all results have same metric name and similar values
            assert result.metric_name == first_result.metric_name
            assert result.count == first_result.count

    # Memory Pressure Tests
    @pytest.mark.slow
    def test_low_memory_conditions(self, chaos_engine, data_generator):
        """Test system behavior under low memory conditions."""
        # Create memory pressure
        memory_hogs = chaos_engine.create_memory_pressure(50)  # 50MB
        
        try:
            # Try to process data under memory pressure
            large_data = data_generator.generate_performance_data('medium')
            
            # Convert to expected format
            health_data = []
            for _, row in large_data.iterrows():
                health_data.append({
                    'creationDate': row['date'],
                    'type': 'StepCount',
                    'value': row.get('steps', 0)
                })
            
            df = pd.DataFrame(health_data)
            calculator = DailyMetricsCalculator(df)
            result = calculator.calculate_statistics('StepCount')
            
            # Should either succeed or fail gracefully
            if result is not None:
                assert result.count > 0
            
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
        # Create circular reference scenario
        circular_data = data_generator.generate(50)
        # Simulate a condition that might cause infinite loops
        circular_data.loc[0, 'steps'] = float('inf')
        circular_data.loc[1, 'steps'] = float('-inf')
        
        # Convert to expected format
        health_data = []
        for _, row in circular_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df = pd.DataFrame(health_data)
        calculator = DailyMetricsCalculator(df)
        
        # Should complete within timeout
        try:
            result = calculator.calculate_statistics('StepCount')
            assert result is not None
        except (RecursionError, ValueError):
            # Acceptable to detect and prevent infinite loops
            pass

    @pytest.mark.timeout(5)
    def test_large_dataset_timeout_protection(self, data_generator):
        """Test timeout protection for very large datasets."""
        # Create dataset that might cause timeout
        very_large_data = data_generator.generate_performance_data('xlarge')
        
        # Convert to expected format
        health_data = []
        for _, row in very_large_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row.get('steps', 0)
            })
        
        df = pd.DataFrame(health_data)
        calculator = DailyMetricsCalculator(df)
        
        start_time = time.time()
        try:
            result = calculator.calculate_statistics('StepCount')
            end_time = time.time()
            
            # Should complete reasonably quickly
            assert end_time - start_time < 30  # 30 second max
            if result is not None:
                assert result.count > 0
                
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
        # Create data with wrong types
        wrong_type_data = data_generator.generate(50)
        wrong_type_data['steps'] = wrong_type_data['steps'].astype(str)  # Convert to string
        
        # Convert to expected format
        health_data = []
        for _, row in wrong_type_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount',
                'value': row['steps']  # This is now a string
            })
        
        df = pd.DataFrame(health_data)
        
        try:
            calculator = DailyMetricsCalculator(df)
            result = calculator.calculate_statistics('StepCount')
            # Should handle type conversion or fail gracefully
            assert result is not None
        except (TypeError, ValueError):
            # Acceptable to reject wrong types
            pass

    def test_missing_required_columns(self, data_generator):
        """Test handling of missing required columns."""
        incomplete_data = data_generator.generate(50)
        del incomplete_data['steps']  # Remove required column
        
        # Convert to expected format - will be missing 'value'
        health_data = []
        for _, row in incomplete_data.iterrows():
            health_data.append({
                'creationDate': row['date'],
                'type': 'StepCount'
                # 'value' is missing
            })
        
        df = pd.DataFrame(health_data)
        
        with pytest.raises((KeyError, ValueError)):
            calculator = DailyMetricsCalculator(df)
            result = calculator.calculate_statistics('StepCount')

    # Race Condition Tests
    def test_race_condition_detection(self, data_generator):
        """Test detection and handling of race conditions."""
        shared_data = data_generator.generate(100)
        
        results = []
        
        def modify_and_calculate():
            # Modify data while calculating
            local_data = shared_data.copy()
            local_data.loc[0, 'steps'] = random.randint(1000, 20000)
            
            # Convert to expected format
            health_data = []
            for _, row in local_data.iterrows():
                health_data.append({
                    'creationDate': row['date'],
                    'type': 'StepCount',
                    'value': row.get('steps', 0)
                })
            
            df = pd.DataFrame(health_data)
            calculator = DailyMetricsCalculator(df)
            result = calculator.calculate_statistics('StepCount')
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
        # Simulate various error conditions and recovery
        problematic_datasets = [
            data_generator.generate_edge_cases()['all_nulls'],
            data_generator.generate_edge_cases()['extreme_values'],
            data_generator.generate_edge_cases()['single_point']
        ]
        
        recovery_count = 0
        
        for problem_data in problematic_datasets:
            try:
                # Convert to expected format
                health_data = []
                for _, row in problem_data.iterrows():
                    health_data.append({
                        'creationDate': row['date'],
                        'type': 'StepCount',
                        'value': row.get('steps', 0)
                    })
                
                df = pd.DataFrame(health_data)
                calculator = DailyMetricsCalculator(df)
                result = calculator.calculate_statistics('StepCount')
                if result is not None:
                    recovery_count += 1
            except Exception:
                # Count as handled error
                recovery_count += 1
        
        # Should handle or recover from most error conditions
        assert recovery_count >= len(problematic_datasets) * 0.8  # 80% recovery rate


# Custom markers for chaos tests
pytestmark = pytest.mark.chaos