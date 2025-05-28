"""
Memory usage benchmarks.

Tests for memory efficiency and leak detection.
"""

import pytest
import pandas as pd
import numpy as np
import gc
import tracemalloc
from memory_profiler import profile
import psutil
from pathlib import Path
from tests.performance.benchmark_base import PerformanceBenchmark
from tests.generators.health_data import HealthDataGenerator
from src.xml_streaming_processor import XMLStreamingProcessor
from src.data_loader import DataLoader
from src.analytics.cache_manager import CacheManager


@pytest.mark.performance
class TestMemoryUsage(PerformanceBenchmark):
    """Memory usage and efficiency tests."""
    
    def setup_method(self):
        """Set up test environment."""
        super().__init__()
        self.process = psutil.Process()
        self.generator = HealthDataGenerator(seed=42)
        
    def get_memory_usage_mb(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
        
    def test_streaming_processor_memory(self, tmp_path):
        """Test that streaming processor maintains constant memory usage."""
        # Create a large test XML file
        xml_file = tmp_path / "large_export.xml"
        self._create_large_xml(xml_file, records=100000)
        
        # Start memory tracking
        tracemalloc.start()
        initial_memory = self.get_memory_usage_mb()
        
        # Process the file
        processor = XMLStreamingProcessor()
        records_processed = 0
        peak_memory = initial_memory
        
        for batch in processor.process_file(str(xml_file), batch_size=1000):
            records_processed += len(batch)
            current_memory = self.get_memory_usage_mb()
            peak_memory = max(peak_memory, current_memory)
            
            # Memory should not grow significantly during processing
            memory_growth = current_memory - initial_memory
            assert memory_growth < 100, f"Memory grew by {memory_growth:.1f}MB"
        
        current, peak_trace = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Verify memory efficiency
        peak_mb = peak_trace / 1024 / 1024
        assert peak_mb < 100, f"Peak memory usage: {peak_mb:.1f}MB"
        assert records_processed == 100000
        
    def test_data_loader_memory_efficiency(self):
        """Test DataLoader memory usage with large datasets."""
        # Generate large dataset
        large_data = self.generator.generate_dataframe(
            days=1825,  # 5 years
            records_per_day=200
        )
        
        with self.measure_performance('data_loader_memory'):
            loader = DataLoader()
            
            # Test chunked processing
            total_processed = 0
            for chunk in loader.process_in_chunks(large_data, chunk_size=10000):
                total_processed += len(chunk)
                # Process chunk (simulate work)
                _ = chunk.groupby('date')['value'].mean()
        
        # Check memory efficiency
        self.assert_performance(
            'data_loader_memory',
            max_memory_growth_mb=50  # Should use minimal additional memory
        )
        
    def test_cache_manager_memory_limits(self):
        """Test that cache manager respects memory limits."""
        # Create cache with 50MB limit
        cache = CacheManager(max_memory_mb=50)
        
        initial_memory = self.get_memory_usage_mb()
        
        # Add data until we exceed the limit
        for i in range(100):
            # Create ~1MB of data
            data = pd.DataFrame({
                'values': np.random.random(125000)  # ~1MB in memory
            })
            cache.put(f'key_{i}', data)
        
        # Check that memory usage is controlled
        final_memory = self.get_memory_usage_mb()
        memory_growth = final_memory - initial_memory
        
        # Should not exceed limit by more than 20MB (overhead)
        assert memory_growth < 70, f"Cache memory grew by {memory_growth:.1f}MB"
        
        # Verify cache is evicting old entries
        assert len(cache) < 100  # Some entries should be evicted
        
    @profile
    def test_calculator_memory_profile(self):
        """Profile memory usage of calculator operations."""
        # This decorator will output line-by-line memory usage
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        
        # Generate test data
        data = self.generator.generate_dataframe(days=365, records_per_day=100)
        
        # Create calculator
        calculator = DailyMetricsCalculator(data)
        
        # Perform calculations
        results = calculator.calculate_all_metrics()
        
        # Clean up
        del calculator
        del results
        gc.collect()
        
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        initial_memory = self.get_memory_usage_mb()
        memory_readings = []
        
        # Perform repeated operations
        for i in range(10):
            # Generate data
            data = self.generator.generate_dataframe(days=30)
            
            # Create and use calculator
            from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
            calc = WeeklyMetricsCalculator(data)
            results = calc.calculate_weekly_summary()
            
            # Explicit cleanup
            del calc
            del results
            del data
            gc.collect()
            
            # Record memory
            current_memory = self.get_memory_usage_mb()
            memory_readings.append(current_memory)
        
        # Check for memory leak
        # Memory should stabilize, not continuously grow
        first_half_avg = np.mean(memory_readings[:5])
        second_half_avg = np.mean(memory_readings[5:])
        
        # Second half should not be significantly higher
        memory_increase = second_half_avg - first_half_avg
        assert memory_increase < 10, f"Potential memory leak: {memory_increase:.1f}MB increase"
        
    def test_dataframe_memory_optimization(self):
        """Test memory optimization techniques for DataFrames."""
        # Create large DataFrame with different data types
        n_rows = 1000000
        
        # Original DataFrame (inefficient)
        df_original = pd.DataFrame({
            'id': range(n_rows),
            'category': np.random.choice(['A', 'B', 'C', 'D'], n_rows),
            'value': np.random.random(n_rows) * 1000,
            'flag': np.random.choice([True, False], n_rows)
        })
        
        original_memory = df_original.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Optimized DataFrame
        df_optimized = pd.DataFrame({
            'id': pd.array(range(n_rows), dtype='uint32'),
            'category': pd.Categorical(np.random.choice(['A', 'B', 'C', 'D'], n_rows)),
            'value': pd.array(np.random.random(n_rows) * 1000, dtype='float32'),
            'flag': pd.array(np.random.choice([True, False], n_rows), dtype='bool')
        })
        
        optimized_memory = df_optimized.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Optimized should use significantly less memory
        memory_reduction = (original_memory - optimized_memory) / original_memory
        assert memory_reduction > 0.4, f"Only {memory_reduction:.1%} memory reduction"
        
        print(f"Memory optimization: {original_memory:.1f}MB -> {optimized_memory:.1f}MB "
              f"({memory_reduction:.1%} reduction)")
        
    def test_concurrent_memory_usage(self):
        """Test memory usage under concurrent load."""
        import concurrent.futures
        import threading
        
        memory_readings = []
        lock = threading.Lock()
        
        def worker(worker_id):
            """Worker function that uses memory."""
            # Generate data
            data = self.generator.generate_dataframe(days=90)
            
            # Perform calculations
            from src.statistics_calculator import StatisticsCalculator
            calc = StatisticsCalculator()
            results = calc.calculate_comprehensive_stats(data['value'].values)
            
            # Record memory usage
            with lock:
                memory_readings.append(self.get_memory_usage_mb())
            
            return len(results)
        
        initial_memory = self.get_memory_usage_mb()
        
        # Run concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Check peak memory usage
        peak_memory = max(memory_readings) if memory_readings else initial_memory
        memory_per_worker = (peak_memory - initial_memory) / 5  # Max 5 concurrent
        
        # Each worker should use reasonable memory
        assert memory_per_worker < 50, f"Each worker used {memory_per_worker:.1f}MB"
        
    def _create_large_xml(self, filepath: Path, records: int):
        """Create a large XML file for testing."""
        with open(filepath, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<HealthData>\n')
            
            for i in range(records):
                f.write(f'  <Record type="HKQuantityTypeIdentifierStepCount" '
                       f'value="{np.random.randint(0, 20000)}" '
                       f'startDate="2023-01-01 {i%24:02d}:00:00" '
                       f'endDate="2023-01-01 {i%24:02d}:00:00"/>\n')
                
            f.write('</HealthData>\n')