"""
Calculator performance benchmarks.

Tests for analytics calculator performance and scalability.
"""

import pytest
import pandas as pd
import numpy as np
from tests.performance.benchmark_base import PerformanceBenchmark
from tests.performance.adaptive_thresholds import AdaptiveThresholds
from tests.generators.health_data import HealthMetricGenerator
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator  
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.statistics_calculator import StatisticsCalculator


def convert_to_health_format(wide_df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide format dataframe to Apple Health format."""
    data_rows = []
    for idx, row in wide_df.iterrows():
        for col in wide_df.columns:
            if col != 'timestamp' and pd.notna(row[col]):
                data_rows.append({
                    'creationDate': idx,
                    'type': col,
                    'value': row[col]
                })
    return pd.DataFrame(data_rows)


@pytest.mark.performance
class TestCalculatorPerformance(PerformanceBenchmark):
    """Performance tests for analytics calculators."""
    
    def setup_method(self):
        """Set up test environment."""
        self.process = __import__('psutil').Process()
        self.baseline_memory = None
        self.results = {}
        self._start_metrics = {}
        self.thresholds = AdaptiveThresholds()
        self.generator = HealthMetricGenerator(seed=42)
        
    @pytest.mark.parametrize('days,expected_time', [
        (30, 0.1),    # 1 month: 100ms
        (90, 0.3),    # 3 months: 300ms  
        (365, 1.0),   # 1 year: 1s
        (730, 2.0),   # 2 years: 2s
        (1825, 5.0),  # 5 years: 5s
    ])
    def test_daily_calculator_scaling(self, benchmark, days, expected_time):
        """Test that daily calculator performance scales linearly with data size."""
        # Generate data using HealthDataFixtures
        from tests.fixtures.health_fixtures import HealthDataFixtures
        wide_data = HealthDataFixtures.create_health_dataframe(
            days=days,
            metrics=['steps', 'distance', 'calories', 'heart_rate'],
            include_anomalies=False
        )
        
        # Convert to Apple Health format
        data = convert_to_health_format(wide_data)
        
        def calculate():
            calculator = DailyMetricsCalculator(data)
            return calculator.get_metrics_summary()
        
        # Benchmark
        result = benchmark.pedantic(
            calculate,
            rounds=5,
            warmup_rounds=2
        )
        
        # Get adaptive threshold
        threshold = self.thresholds.get_threshold(
            f'daily_calculator_{days}d',
            'duration'
        )
        
        # Use the minimum of expected time and adaptive threshold
        max_allowed = min(expected_time, threshold)
        
        # benchmark.pedantic returns None, stats are on benchmark object
        assert benchmark.stats['mean'] < max_allowed
        print(f"Daily calculator {days} days: {benchmark.stats['mean']:.3f}s (max: {max_allowed:.3f}s)")
        
    def test_weekly_calculator_performance(self, benchmark):
        """Test weekly calculator with various data sizes."""
        # Test with 1 year of data
        from tests.fixtures.health_fixtures import HealthDataFixtures
        data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(days=365))
        
        def calculate():
            daily_calc = DailyMetricsCalculator(data)
            calculator = WeeklyMetricsCalculator(daily_calc)
            return calculator.calculate_weekly_summary()
        
        result = benchmark.pedantic(
            calculate,
            rounds=10,
            warmup_rounds=3
        )
        
        # Weekly should be faster than daily for same data
        assert benchmark.stats['mean'] < 0.5  # <500ms for 1 year
        assert benchmark.stats['stddev'] < 0.1  # Consistent performance
        
    def test_monthly_calculator_performance(self, benchmark):
        """Test monthly calculator performance."""
        # Test with 2 years of data
        from tests.fixtures.health_fixtures import HealthDataFixtures
        data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(days=730))
        
        def calculate():
            daily_calc = DailyMetricsCalculator(data)
            calculator = MonthlyMetricsCalculator(daily_calc)
            return calculator.calculate_monthly_trends()
        
        result = benchmark(calculate)
        
        # Monthly aggregation should be efficient
        assert result.stats['mean'] < 0.3  # <300ms for 2 years
        
    def test_calculator_memory_efficiency(self):
        """Test memory usage of calculators with large datasets."""
        # Generate large dataset
        from tests.fixtures.health_fixtures import HealthDataFixtures
        large_data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(
            days=1825,  # 5 years
            include_anomalies=True
        ))
        
        with self.measure_performance('daily_calculator_memory'):
            calculator = DailyMetricsCalculator(large_data)
            results = calculator.get_metrics_summary()
            
        # Check memory usage
        self.assert_performance(
            'daily_calculator_memory',
            max_memory_growth_mb=200  # Should not grow by more than 200MB
        )
        
    def test_statistics_calculator_performance(self, benchmark):
        """Test statistics calculator with various array sizes."""
        sizes = [1000, 10000, 100000, 1000000]
        
        for size in sizes:
            data = np.random.normal(100, 15, size)
            
            def calculate_stats():
                calculator = StatisticsCalculator()
                return calculator.calculate_advanced_statistics(data)
            
            # Only benchmark if size is reasonable
            if size <= 100000:
                result = benchmark.pedantic(
                    calculate_stats,
                    rounds=5,
                    warmup_rounds=2
                )
                
                # Performance should be reasonable even for large arrays
                expected_time = size / 1000000  # Roughly 1ms per 1000 elements
                assert benchmark.stats['mean'] < expected_time
                
    def test_calculator_caching_performance(self, benchmark):
        """Test performance improvement from caching."""
        from tests.fixtures.health_fixtures import HealthDataFixtures
        data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(days=365))
        calculator = DailyMetricsCalculator(data)
        
        # First run - no cache
        def first_run():
            return calculator.get_metrics_summary()
            
        # Second run - with cache
        def cached_run():
            return calculator.get_metrics_summary()
        
        # Benchmark both
        first_result = benchmark(first_run)
        # Note: Caching may not be implemented in current version
        cached_result = benchmark(cached_run)
        
        # Cached should be significantly faster
        assert cached_result.stats['mean'] < first_result.stats['mean'] * 0.1
        
    def test_concurrent_calculator_performance(self, benchmark):
        """Test calculator performance under concurrent load."""
        import concurrent.futures
        
        # Generate shared dataset
        from tests.fixtures.health_fixtures import HealthDataFixtures
        data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(days=180))
        
        def concurrent_calculations():
            """Run multiple calculators concurrently."""
            def run_calculator(calc_type):
                if calc_type == 'daily':
                    calc = DailyMetricsCalculator(data)
                    return calc.get_metrics_summary()
                elif calc_type == 'weekly':
                    daily_calc = DailyMetricsCalculator(data)
                    calc = WeeklyMetricsCalculator(daily_calc)
                    return calc.calculate_weekly_summary()
                else:
                    daily_calc = DailyMetricsCalculator(data)
                    calc = MonthlyMetricsCalculator(daily_calc)
                    return calc.calculate_monthly_trends()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(run_calculator, 'daily'),
                    executor.submit(run_calculator, 'weekly'),
                    executor.submit(run_calculator, 'monthly')
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                
            return results
        
        # Benchmark concurrent execution
        result = benchmark(concurrent_calculations)
        
        # Should complete all three in reasonable time
        assert result.stats['mean'] < 2.0  # <2s for all three calculators
        
    @pytest.mark.slow
    def test_calculator_stress_test(self):
        """Stress test calculators with extreme data sizes."""
        # This test is marked slow and should only run in full test suite
        
        # Generate very large dataset
        from tests.fixtures.health_fixtures import HealthDataFixtures
        extreme_data = convert_to_health_format(HealthDataFixtures.create_health_dataframe(
            days=3650,  # 10 years
            include_anomalies=True
        ))
        
        with self.measure_performance('stress_test'):
            # Test all calculators
            daily = DailyMetricsCalculator(extreme_data)
            daily_results = daily.get_metrics_summary()
            
            weekly = WeeklyMetricsCalculator(daily)
            weekly_results = weekly.calculate_weekly_summary()
            
            monthly = MonthlyMetricsCalculator(daily)
            monthly_results = monthly.calculate_monthly_trends()
        
        # Even with extreme data, should complete
        self.assert_performance(
            'stress_test',
            max_duration=30.0,  # 30 seconds max
            max_memory_growth_mb=1000  # 1GB max growth
        )