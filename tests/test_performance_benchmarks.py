"""
Performance benchmark tests for analytics components.
Tests processing speed, memory usage, and scalability.

This is the main performance test file that uses the performance testing
infrastructure in tests/performance/.
"""

import pytest
import pandas as pd
import numpy as np
import gc
import time
from typing import List, Dict, Any

# Import performance testing infrastructure
from tests.performance import PerformanceBenchmark, AdaptiveThresholds
from tests.generators.test_data_generator import HealthDataGenerator
from tests.mocks.data_sources import MockDataSource
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.statistics_calculator import StatisticsCalculator


@pytest.mark.performance
class TestPerformanceBenchmarks(PerformanceBenchmark):
    """Comprehensive performance tests for analytics system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.process = __import__('psutil').Process()
        self.baseline_memory = None
        self.results = {}
        self._start_metrics = {}
        self.thresholds = AdaptiveThresholds()
    
    def _convert_to_health_format(self, df):
        """Convert performance test data to health data format."""
        # Create empty result dataframe
        result_rows = []
        
        # Convert each metric to health data format
        for idx, row in df.iterrows():
            # Convert steps
            result_rows.append({
                'creationDate': row['date'],
                'type': 'HKQuantityTypeIdentifierStepCount',
                'value': float(row['steps']),
                'unit': 'count',
                'sourceName': 'TestData'
            })
            
            # Convert heart rate if present
            if 'heart_rate' in row:
                result_rows.append({
                    'creationDate': row['date'],
                    'type': 'HKQuantityTypeIdentifierHeartRate',
                    'value': float(row['heart_rate']),
                    'unit': 'count/min',
                    'sourceName': 'TestData'
                })
            
            # Convert distance if present
            if 'distance' in row:
                result_rows.append({
                    'creationDate': row['date'],
                    'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                    'value': float(row['distance']),
                    'unit': 'km',
                    'sourceName': 'TestData'
                })
            
            # Convert calories if present
            if 'calories' in row:
                result_rows.append({
                    'creationDate': row['date'],
                    'type': 'HKQuantityTypeIdentifierActiveEnergyBurned',
                    'value': float(row['calories']),
                    'unit': 'kcal',
                    'sourceName': 'TestData'
                })
        
        return pd.DataFrame(result_rows)
        
    @pytest.fixture
    def data_generator(self):
        """Create test data generator."""
        return HealthDataGenerator(seed=42)
    
    @pytest.fixture
    def small_dataset(self, data_generator):
        """Generate small dataset (1K records)."""
        return data_generator.generate_performance_data('small')
    
    @pytest.fixture
    def medium_dataset(self, data_generator):
        """Generate medium dataset (10K records)."""
        return data_generator.generate_performance_data('medium')
    
    @pytest.fixture
    def large_dataset(self, data_generator):
        """Generate large dataset (50K records)."""
        return data_generator.generate_performance_data('large')
    
    @pytest.fixture
    def xlarge_dataset(self, data_generator):
        """Generate extra large dataset (100K records)."""
        return data_generator.generate_performance_data('xlarge')

    # Daily Metrics Calculator Benchmarks
    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_small(self, benchmark, small_dataset):
        """Benchmark daily calculator with small dataset."""
        # Convert performance data to health data format
        health_data = self._convert_to_health_format(small_dataset)
        data_source = MockDataSource(health_data)
        calculator = DailyMetricsCalculator(data_source)
        
        # Test calculate_statistics for steps
        def calculate_metrics():
            return calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        result = benchmark.pedantic(
            calculate_metrics,
            rounds=5,
            warmup_rounds=2
        )
        
        # Check result structure
        assert result is not None
        assert result.mean is not None

    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_medium(self, benchmark, medium_dataset):
        """Benchmark daily calculator with medium dataset."""
        # Convert performance data to health data format
        health_data = self._convert_to_health_format(medium_dataset)
        data_source = MockDataSource(health_data)
        calculator = DailyMetricsCalculator(data_source)
        
        # Test calculate_statistics for steps
        def calculate_metrics():
            return calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        result = benchmark.pedantic(
            calculate_metrics,
            rounds=5,
            warmup_rounds=2
        )
        
        # Check result structure
        assert result is not None
        assert result.mean is not None

    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_large(self, benchmark, large_dataset):
        """Benchmark daily calculator with large dataset."""
        # Convert performance data to health data format
        health_data = self._convert_to_health_format(large_dataset)
        data_source = MockDataSource(health_data)
        calculator = DailyMetricsCalculator(data_source)
        
        # Test calculate_statistics for steps
        def calculate_metrics():
            return calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        result = benchmark(calculate_metrics)
        
        assert result is not None
        assert result.mean is not None
        assert benchmark.stats['mean'] < 1.0  # <1s

    # Note: Weekly and Monthly calculator performance tests are in tests/performance/test_calculator_benchmarks.py

    # Statistics Calculator Benchmarks
    @pytest.mark.benchmark(group="statistics")
    def test_statistics_calculation_performance(self, benchmark, large_dataset):
        """Benchmark statistics calculations."""
        calculator = StatisticsCalculator()
        
        result = benchmark(
            calculator.calculate_descriptive_stats,
            large_dataset['steps']
        )
        
        assert 'mean' in result
        assert 'std' in result
        assert benchmark.stats['mean'] < 0.1  # <100ms

    # Memory Usage Tests
    @pytest.mark.slow
    def test_memory_usage_daily_calculator(self, large_dataset):
        """Test memory usage of daily calculator."""
        # Convert performance data to health data format
        health_data = self._convert_to_health_format(large_dataset)
        data_source = MockDataSource(health_data)
        
        with self.measure_performance('daily_calculator_memory'):
            calculator = DailyMetricsCalculator(data_source)
            result = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        # Assert memory usage is within limits
        self.assert_performance(
            'daily_calculator_memory',
            max_memory_growth_mb=100  # <100MB for 100K records
        )

    @pytest.mark.slow
    def test_memory_leak_prevention(self, data_generator):
        """Test for memory leaks in repeated calculations."""
        import psutil
        process = psutil.Process()
        
        memory_samples = []
        
        # Perform multiple calculations
        for i in range(10):
            data = data_generator.generate_performance_data('medium')
            health_data = self._convert_to_health_format(data)
            data_source = MockDataSource(health_data)
            calculator = DailyMetricsCalculator(data_source)
            result = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
            
            # Force garbage collection
            del data
            del health_data
            del data_source
            del calculator
            del result
            gc.collect()
            
            # Record memory usage
            memory_samples.append(process.memory_info().rss)
        
        # Memory should not increase significantly over iterations
        memory_trend = np.polyfit(range(len(memory_samples)), memory_samples, 1)[0]
        assert memory_trend < 1024 * 1024  # <1MB increase per iteration

    # Scalability Tests
    @pytest.mark.parametrize("dataset_size", ['small', 'medium', 'large'])
    def test_scalability_analysis(self, data_generator, dataset_size):
        """Test how performance scales with data size."""
        data = data_generator.generate_performance_data(dataset_size)
        health_data = self._convert_to_health_format(data)
        data_source = MockDataSource(health_data)
        calculator = DailyMetricsCalculator(data_source)
        
        start_time = time.time()
        result = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        end_time = time.time()
        
        processing_time = end_time - start_time
        records_per_second = len(data) / processing_time
        
        # Should process at least 10K records per second
        assert records_per_second > 10000
        assert result is not None

    # Concurrent Processing Tests
    @pytest.mark.slow
    def test_concurrent_processing_performance(self, data_generator):
        """Test performance under concurrent load."""
        import threading
        import queue
        
        data = data_generator.generate_performance_data('medium')
        health_data = self._convert_to_health_format(data)
        
        results_queue = queue.Queue()
        start_time = time.time()
        
        def worker():
            data_source = MockDataSource(health_data.copy())
            calculator = DailyMetricsCalculator(data_source)
            result = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
            results_queue.put(result)
        
        # Launch concurrent workers
        threads = []
        num_workers = 4
        
        for _ in range(num_workers):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == num_workers
        assert total_time < 5.0  # Should complete within 5 seconds

    # Database Performance Tests
    @pytest.mark.skip(reason="Database methods need to be updated")
    @pytest.mark.benchmark(group="database")
    def test_database_insert_performance(self, benchmark, medium_dataset):
        """Benchmark database insert operations."""
        from src.database import DatabaseManager
        
        # Create in-memory database for testing
        db = DatabaseManager(':memory:')
        
        def insert_data():
            db.bulk_insert_health_data(medium_dataset)
            return db.get_record_count()
        
        result = benchmark(insert_data)
        
        assert result > 0
        assert benchmark.stats['mean'] < 2.0  # <2s for 10K records

    @pytest.mark.skip(reason="Database methods need to be updated")
    @pytest.mark.benchmark(group="database")
    def test_database_query_performance(self, benchmark, large_dataset):
        """Benchmark database query operations."""
        from src.database import DatabaseManager
        
        # Setup database with data
        db = DatabaseManager(':memory:')
        db.bulk_insert_health_data(large_dataset)
        
        def query_data():
            return db.get_data_range(
                start_date=large_dataset['date'].min(),
                end_date=large_dataset['date'].max(),
                metrics=['steps', 'heart_rate_avg']
            )
        
        result = benchmark(query_data)
        
        assert result is not None
        assert benchmark.stats['mean'] < 0.5  # <500ms

    # Chart Rendering Performance Tests
    @pytest.mark.skip(reason="Chart module methods need to be updated")
    @pytest.mark.benchmark(group="visualization")
    def test_chart_rendering_performance(self, benchmark, medium_dataset):
        """Benchmark chart rendering speed."""
        from src.ui.charts.line_chart import LineChart
        
        chart = LineChart()
        
        def render_chart():
            chart.set_data(medium_dataset)
            return chart.render_to_buffer()
        
        result = benchmark(render_chart)
        
        assert result is not None
        assert benchmark.stats['mean'] < 1.0  # <1s for chart rendering

    @pytest.mark.skip(reason="Chart module methods need to be updated")
    @pytest.mark.benchmark(group="visualization")
    @pytest.mark.parametrize("chart_type", ["line", "bar", "scatter"])
    def test_multiple_chart_rendering(self, benchmark, medium_dataset, chart_type):
        """Benchmark different chart types."""
        from src.ui.component_factory import ComponentFactory
        
        factory = ComponentFactory()
        
        def render_chart():
            chart = factory.create_chart(chart_type, medium_dataset)
            return chart.render()
        
        result = benchmark(render_chart)
        
        assert result is not None
        assert benchmark.stats['mean'] < 2.0  # <2s per chart

    # Analytics Pipeline Performance
    @pytest.mark.skip(reason="Weekly/Monthly calculators need API updates")
    @pytest.mark.benchmark(group="pipeline")
    @pytest.mark.slow
    def test_full_analytics_pipeline(self, benchmark, large_dataset):
        """Benchmark complete analytics pipeline."""
        # Convert data to health format
        health_data = self._convert_to_health_format(large_dataset)
        data_source = MockDataSource(health_data)
        
        daily_calc = DailyMetricsCalculator(data_source)
        weekly_calc = WeeklyMetricsCalculator(data_source)
        monthly_calc = MonthlyMetricsCalculator(data_source)
        
        def full_pipeline():
            # Calculate for different metrics
            step_stats = daily_calc.calculate_statistics('HKQuantityTypeIdentifierStepCount')
            heart_stats = daily_calc.calculate_statistics('HKQuantityTypeIdentifierHeartRate')
            
            # Simplified weekly/monthly metrics for performance testing
            weekly_data = len(data_source.get_data_for_period(
                start_date=pd.Timestamp.now() - pd.Timedelta(days=7),
                end_date=pd.Timestamp.now()
            ))
            monthly_data = len(data_source.get_data_for_period(
                start_date=pd.Timestamp.now() - pd.Timedelta(days=30), 
                end_date=pd.Timestamp.now()
            ))
            
            return {
                'daily': {'steps': step_stats, 'heart_rate': heart_stats},
                'weekly': weekly_data,
                'monthly': monthly_data
            }
        
        result = benchmark(full_pipeline)
        
        assert 'daily' in result
        assert 'weekly' in result
        assert 'monthly' in result
        assert benchmark.stats['mean'] < 5.0  # <5s for full pipeline

    # Regression Performance Tests
    def test_performance_regression_detection(self, large_dataset):
        """Test to detect performance regressions."""
        # Convert data to health format
        health_data = self._convert_to_health_format(large_dataset)
        data_source = MockDataSource(health_data)
        calculator = DailyMetricsCalculator(data_source)
        
        # Expected performance baselines (adjust based on hardware)
        performance_baselines = {
            'calculation_time': 1.0,  # Max 1 second
            'memory_usage': 50 * 1024 * 1024,  # Max 50MB
            'throughput': 50000  # Min 50K records/second
        }
        
        import psutil
        process = psutil.Process()
        
        # Measure performance
        gc.collect()
        memory_before = process.memory_info().rss
        start_time = time.time()
        
        result = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        end_time = time.time()
        memory_after = process.memory_info().rss
        
        calculation_time = end_time - start_time
        memory_used = memory_after - memory_before
        throughput = len(large_dataset) / calculation_time
        
        # Assert performance meets baselines
        assert calculation_time <= performance_baselines['calculation_time']
        assert memory_used <= performance_baselines['memory_usage']
        assert throughput >= performance_baselines['throughput']
        assert result is not None


# Performance test configuration
# pytest_plugins = ["pytest_benchmark"]  # Not needed - plugin auto-registers