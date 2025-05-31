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
from tests.test_data_generator import HealthDataGenerator
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
        """Generate large dataset (100K records)."""
        return data_generator.generate_performance_data('large')
    
    @pytest.fixture
    def xlarge_dataset(self, data_generator):
        """Generate extra large dataset (1M records)."""
        return data_generator.generate_performance_data('xlarge')

    # Daily Metrics Calculator Benchmarks
    def _transform_to_health_records(self, df):
        """Transform performance test data to health records format."""
        records = []
        for _, row in df.iterrows():
            # Add steps record
            records.append({
                'creationDate': row['date'],
                'type': 'HKQuantityTypeIdentifierStepCount',
                'value': row['steps']
            })
            # Add heart rate record
            records.append({
                'creationDate': row['date'],
                'type': 'HKQuantityTypeIdentifierHeartRate',
                'value': row['heart_rate']
            })
            # Add distance record
            records.append({
                'creationDate': row['date'],
                'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'value': row['distance']
            })
        return pd.DataFrame(records)

    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_small(self, benchmark, small_dataset):
        """Benchmark daily calculator with small dataset."""
        health_records = self._transform_to_health_records(small_dataset)
        data_source = MockDataSource(health_records)
        calculator = DailyMetricsCalculator(data_source)
        
        result = benchmark.pedantic(
            calculator.calculate_statistics,
            args=('HKQuantityTypeIdentifierStepCount',),  # Test with steps metric
            rounds=5,
            warmup_rounds=2
        )
        
        # Use adaptive threshold
        threshold = self.thresholds.get_threshold(
            'daily_calculator_small',
            'duration',
            margin=1.2
        )
        
        # The benchmark returns the calculated stats, but we need to check benchmark timing
        assert benchmark.stats['mean'] < threshold

    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_medium(self, benchmark, medium_dataset):
        """Benchmark daily calculator with medium dataset."""
        health_records = self._transform_to_health_records(medium_dataset)
        data_source = MockDataSource(health_records)
        calculator = DailyMetricsCalculator(data_source)
        
        result = benchmark.pedantic(
            calculator.calculate_statistics,
            args=('HKQuantityTypeIdentifierStepCount',),
            rounds=5,
            warmup_rounds=2
        )
        
        # Use adaptive threshold
        threshold = self.thresholds.get_threshold(
            'daily_calculator_medium',
            'duration',
            margin=1.3
        )
        
        # Check benchmark timing
        assert benchmark.stats['mean'] < threshold

    @pytest.mark.benchmark(group="daily_calculator")
    def test_daily_calculator_large(self, benchmark, large_dataset):
        """Benchmark daily calculator with large dataset."""
        health_records = self._transform_to_health_records(large_dataset)
        data_source = MockDataSource(health_records)
        calculator = DailyMetricsCalculator(data_source)
        
        result = benchmark(
            calculator.calculate_statistics,
            'HKQuantityTypeIdentifierStepCount'  # Use full Apple Health metric name
        )
        
        # Verify the calculation completed successfully and returned valid stats
        assert result is not None
        assert result.count > 0  # Should have processed some data
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
        with self.measure_performance('daily_calculator_memory'):
            calculator = DailyMetricsCalculator(large_dataset)
            result = calculator.calculate_all_metrics()
        
        # Assert memory usage is within limits
        self.assert_performance(
            'daily_calculator_memory',
            max_memory_growth_mb=100  # <100MB for 100K records
        )

    @pytest.mark.slow
    def test_memory_leak_prevention(self, data_generator):
        """Test for memory leaks in repeated calculations."""
        calculator = DailyMetricsCalculator()
        
        import psutil
        process = psutil.Process()
        
        memory_samples = []
        
        # Perform multiple calculations
        for i in range(10):
            data = data_generator.generate_performance_data('medium')
            result = calculator.calculate_all_metrics(data)
            
            # Force garbage collection
            del data
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
        calculator = DailyMetricsCalculator()
        data = data_generator.generate_performance_data(dataset_size)
        
        start_time = time.time()
        result = calculator.calculate_all_metrics(data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        records_per_second = len(data) / processing_time
        
        # Should process at least 10K records per second
        assert records_per_second > 10000
        assert len(result) > 0

    # Concurrent Processing Tests
    @pytest.mark.slow
    def test_concurrent_processing_performance(self, data_generator):
        """Test performance under concurrent load."""
        import threading
        import queue
        
        calculator = DailyMetricsCalculator()
        data = data_generator.generate_performance_data('medium')
        
        results_queue = queue.Queue()
        start_time = time.time()
        
        def worker():
            result = calculator.calculate_all_metrics(data.copy())
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
    @pytest.mark.benchmark(group="database")
    def test_database_insert_performance(self, benchmark, medium_dataset):
        """Benchmark database insert operations."""
        from src.database import DatabaseManager
        from src.data_loader import convert_xml_to_sqlite
        import tempfile
        
        # Create temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as db_file:
            db_path = db_file.name
            db = DatabaseManager()
            
            def insert_data():
                # Convert dataframe to health records and insert
                conn = db.get_connection()
                try:
                    medium_dataset.to_sql('health_records', conn, if_exists='append', index=False)
                    conn.commit()
                    # Get count to verify
                    cursor = conn.execute("SELECT COUNT(*) FROM health_records")
                    return cursor.fetchone()[0]
                finally:
                    conn.close()
            
            result = benchmark(insert_data)
            
            assert result > 0
            assert benchmark.stats['mean'] < 2.0  # <2s for 10K records

    @pytest.mark.benchmark(group="database")
    def test_database_query_performance(self, benchmark, large_dataset):
        """Benchmark database query operations."""
        from src.database import DatabaseManager
        import tempfile
        
        # Setup database with data
        with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as db_file:
            db_path = db_file.name
            db = DatabaseManager()
            
            # Insert test data
            conn = db.get_connection()
            try:
                # Ensure the table exists with proper schema
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_records (
                        type TEXT,
                        sourceName TEXT,
                        sourceVersion TEXT,
                        device TEXT,
                        unit TEXT,
                        creationDate TEXT,
                        startDate TEXT,
                        endDate TEXT,
                        value REAL
                    )
                """)
                large_dataset.to_sql('health_records', conn, if_exists='append', index=False)
                conn.commit()
            finally:
                conn.close()
            
            def query_data():
                return db.execute_query(
                    "SELECT * FROM health_records WHERE date >= ? AND date <= ?",
                    (large_dataset['date'].min(), large_dataset['date'].max())
                )
            
            result = benchmark(query_data)
            
            assert len(result) > 0
            assert benchmark.stats['mean'] < 0.5  # <500ms

    # Chart Rendering Performance Tests
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
    @pytest.mark.benchmark(group="pipeline")
    @pytest.mark.slow
    def test_full_analytics_pipeline(self, benchmark, large_dataset):
        """Benchmark complete analytics pipeline."""
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
        from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
        
        daily_calc = DailyMetricsCalculator()
        weekly_calc = WeeklyMetricsCalculator()
        monthly_calc = MonthlyMetricsCalculator()
        
        def full_pipeline():
            daily_metrics = daily_calc.calculate_all_metrics(large_dataset)
            weekly_metrics = weekly_calc.calculate_weekly_trends(large_dataset)
            monthly_metrics = monthly_calc.calculate_monthly_summary(large_dataset)
            
            return {
                'daily': daily_metrics,
                'weekly': weekly_metrics,
                'monthly': monthly_metrics
            }
        
        result = benchmark(full_pipeline)
        
        assert 'daily' in result
        assert 'weekly' in result
        assert 'monthly' in result
        assert benchmark.stats['mean'] < 5.0  # <5s for full pipeline

    # Regression Performance Tests
    def test_performance_regression_detection(self, large_dataset):
        """Test to detect performance regressions."""
        calculator = DailyMetricsCalculator(large_dataset)
        
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
        
        result = calculator.calculate_all_metrics(large_dataset)
        
        end_time = time.time()
        memory_after = process.memory_info().rss
        
        calculation_time = end_time - start_time
        memory_used = memory_after - memory_before
        throughput = len(large_dataset) / calculation_time
        
        # Assert performance meets baselines
        assert calculation_time <= performance_baselines['calculation_time']
        assert memory_used <= performance_baselines['memory_usage']
        assert throughput >= performance_baselines['throughput']
        assert len(result) > 0


# Performance test configuration
# pytest_plugins = ["pytest_benchmark"]  # Not needed - plugin auto-registers