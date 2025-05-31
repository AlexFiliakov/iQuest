"""
Cached wrapper classes for analytics calculators.
Provides seamless caching integration with existing calculator classes.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, date, timedelta
import pandas as pd
from functools import wraps
import logging

from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics
from .weekly_metrics_calculator import WeeklyMetricsCalculator, TrendInfo, WeekComparison
from .monthly_metrics_calculator import MonthlyMetricsCalculator, MonthlyMetrics, MonthlyComparison, GrowthRateInfo
from .cache_manager import get_cache_manager, cache_key
from .cache_background_refresh import cached_analytics_call, get_refresh_monitor

logger = logging.getLogger(__name__)


class CachedDailyMetricsCalculator:
    """Cached wrapper for DailyMetricsCalculator."""
    
    def __init__(self, calculator: DailyMetricsCalculator = None):
        if calculator is None:
            # Create empty DataFrame as fallback
            import pandas as pd
            empty_df = pd.DataFrame(columns=['creationDate', 'type', 'value'])
            calculator = DailyMetricsCalculator(empty_df)
        self.calculator = calculator
        self.cache_manager = get_cache_manager()
        
        # Cache TTL configurations (seconds)
        self.statistics_ttl = 3600  # 1 hour for statistics
        self.aggregates_ttl = 1800  # 30 minutes for aggregates
        self.outliers_ttl = 7200    # 2 hours for outlier detection
    
    def calculate_statistics(self, metric: str, start_date: date = None, 
                           end_date: date = None, interpolation: str = "none") -> MetricStatistics:
        """Calculate statistics with caching."""
        
        key = f"daily_stats|{cache_key(metric, start_date, end_date, interpolation)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_statistics(metric, start_date, end_date, interpolation)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],  # Fast stats go to L1 and L2
            ttl=self.statistics_ttl,
            dependencies=dependencies
        )
    
    def calculate_percentiles(self, metric: str, percentiles: List[int], 
                            start_date: date = None, end_date: date = None) -> Dict[int, float]:
        """Calculate percentiles with caching."""
        
        key = f"daily_percentiles|{cache_key(metric, percentiles, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_percentiles(metric, percentiles, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.statistics_ttl,
            dependencies=dependencies
        )
    
    def detect_outliers(self, metric: str, method: str = "iqr", 
                       start_date: date = None, end_date: date = None) -> pd.Series:
        """Detect outliers with caching."""
        
        key = f"daily_outliers|{cache_key(metric, method, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.detect_outliers(metric, method, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],  # Outlier detection is compute-intensive
            ttl=self.outliers_ttl,
            dependencies=dependencies
        )
    
    def calculate_daily_aggregates(self, metric: str, aggregation: str = "mean",
                                  start_date: date = None, end_date: date = None) -> pd.Series:
        """Calculate daily aggregates with caching."""
        
        key = f"daily_aggregates|{cache_key(metric, aggregation, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_daily_aggregates(metric, aggregation, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.aggregates_ttl,
            dependencies=dependencies
        )
    
    def get_metrics_summary(self, metrics: List[str], start_date: date = None, 
                           end_date: date = None) -> Dict[str, MetricStatistics]:
        """Get metrics summary with caching."""
        
        key = f"daily_summary|{cache_key(metrics, start_date, end_date)}"
        dependencies = [f"metric:{m}" for m in metrics] + [f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.get_metrics_summary(metrics, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.statistics_ttl,
            dependencies=dependencies
        )


class CachedWeeklyMetricsCalculator:
    """Cached wrapper for WeeklyMetricsCalculator."""
    
    def __init__(self, calculator: WeeklyMetricsCalculator = None):
        if calculator is None:
            # Create empty DataFrame as fallback
            import pandas as pd
            empty_df = pd.DataFrame(columns=['creationDate', 'type', 'value'])
            daily_calculator = DailyMetricsCalculator(empty_df)
            calculator = WeeklyMetricsCalculator(daily_calculator)
        self.calculator = calculator
        self.cache_manager = get_cache_manager()
        
        # Cache TTL configurations (seconds)
        self.rolling_stats_ttl = 1800   # 30 minutes for rolling stats
        self.trends_ttl = 3600          # 1 hour for trend analysis
        self.comparisons_ttl = 7200     # 2 hours for comparisons
        self.volatility_ttl = 3600      # 1 hour for volatility
    
    def calculate_rolling_stats(self, metric: str, window: int = 7, 
                               start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """Calculate rolling statistics with caching."""
        
        key = f"weekly_rolling|{cache_key(metric, window, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_rolling_stats(metric, window, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2', 'l3'],  # Rolling stats are expensive, use all tiers
            ttl=self.rolling_stats_ttl,
            dependencies=dependencies
        )
    
    def compare_week_to_date(self, metric: str, current_week: int, year: int) -> WeekComparison:
        """Compare week-to-date with caching."""
        
        key = f"weekly_comparison|{cache_key(metric, current_week, year)}"
        dependencies = [f"metric:{metric}", f"week:{year}:{current_week}"]
        
        def compute_fn():
            return self.calculator.compare_week_to_date(metric, current_week, year)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.comparisons_ttl,
            dependencies=dependencies
        )
    
    def calculate_moving_averages(self, metric: str, windows: List[int] = None,
                                 start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """Calculate moving averages with caching."""
        
        if windows is None:
            windows = [7, 14, 28]
        
        key = f"weekly_ma|{cache_key(metric, windows, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_moving_averages(metric, windows, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2', 'l3'],
            ttl=self.rolling_stats_ttl,
            dependencies=dependencies
        )
    
    def detect_trend(self, metric: str, window: int = 7, 
                    start_date: date = None, end_date: date = None) -> TrendInfo:
        """Detect trend with caching."""
        
        key = f"weekly_trend|{cache_key(metric, window, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.detect_trend(metric, window, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.trends_ttl,
            dependencies=dependencies
        )
    
    def calculate_volatility(self, metric: str, window: int = 7,
                           start_date: date = None, end_date: date = None) -> Dict[str, float]:
        """Calculate volatility with caching."""
        
        key = f"weekly_volatility|{cache_key(metric, window, start_date, end_date)}"
        dependencies = [f"metric:{metric}", f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_volatility(metric, window, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.volatility_ttl,
            dependencies=dependencies
        )
    
    def calculate_multiple_metrics_parallel(self, metrics: List[str], window: int = 7,
                                          start_date: date = None, end_date: date = None) -> Dict[str, pd.DataFrame]:
        """Calculate multiple metrics in parallel with caching."""
        
        key = f"weekly_multi|{cache_key(metrics, window, start_date, end_date)}"
        dependencies = [f"metric:{m}" for m in metrics] + [f"date_range:{start_date}:{end_date}"]
        
        def compute_fn():
            return self.calculator.calculate_multiple_metrics_parallel(metrics, window, start_date, end_date)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l2', 'l3'],  # Parallel processing results are large and expensive
            ttl=self.rolling_stats_ttl,
            dependencies=dependencies
        )


class CachedMonthlyMetricsCalculator:
    """Cached wrapper for MonthlyMetricsCalculator."""
    
    def __init__(self, calculator: MonthlyMetricsCalculator = None):
        if calculator is None:
            # Create empty DataFrame as fallback
            import pandas as pd
            empty_df = pd.DataFrame(columns=['creationDate', 'type', 'value'])
            daily_calculator = DailyMetricsCalculator(empty_df)
            calculator = MonthlyMetricsCalculator(daily_calculator)
        self.calculator = calculator
        self.cache_manager = get_cache_manager()
        
        # Cache TTL configurations (seconds)
        self.monthly_stats_ttl = 7200     # 2 hours for monthly stats
        self.comparisons_ttl = 14400      # 4 hours for YoY comparisons
        self.growth_rates_ttl = 21600     # 6 hours for growth rate analysis
        self.distributions_ttl = 7200     # 2 hours for distribution analysis
    
    def calculate_monthly_stats(self, metric: str, year: int, month: int) -> MonthlyMetrics:
        """Calculate monthly statistics with caching."""
        
        key = f"monthly_stats|{cache_key(metric, year, month)}"
        dependencies = [f"metric:{metric}", f"month:{year}:{month}"]
        
        def compute_fn():
            return self.calculator.calculate_monthly_stats(metric, year, month)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2', 'l3'],  # Monthly stats are expensive and stable
            ttl=self.monthly_stats_ttl,
            dependencies=dependencies
        )
    
    def compare_year_over_year(self, metric: str, month: int, target_year: int, 
                              years_back: int = 1) -> MonthlyComparison:
        """Compare year-over-year with caching."""
        
        key = f"monthly_yoy|{cache_key(metric, month, target_year, years_back)}"
        dependencies = [f"metric:{metric}", f"month:{target_year}:{month}"]
        
        def compute_fn():
            return self.calculator.compare_year_over_year(metric, month, target_year, years_back)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l2', 'l3'],  # YoY comparisons are stable and expensive
            ttl=self.comparisons_ttl,
            dependencies=dependencies
        )
    
    def calculate_growth_rate(self, metric: str, periods: int, 
                             end_year: int, end_month: int) -> GrowthRateInfo:
        """Calculate growth rate with caching."""
        
        key = f"monthly_growth|{cache_key(metric, periods, end_year, end_month)}"
        dependencies = [f"metric:{metric}", f"period_end:{end_year}:{end_month}"]
        
        def compute_fn():
            return self.calculator.calculate_growth_rate(metric, periods, end_year, end_month)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l2', 'l3'],  # Growth rates are computationally expensive
            ttl=self.growth_rates_ttl,
            dependencies=dependencies
        )
    
    def analyze_distribution(self, metric: str, year: int, month: int):
        """Analyze distribution with caching."""
        
        key = f"monthly_distribution|{cache_key(metric, year, month)}"
        dependencies = [f"metric:{metric}", f"month:{year}:{month}"]
        
        def compute_fn():
            return self.calculator.analyze_distribution(metric, year, month)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2'],
            ttl=self.distributions_ttl,
            dependencies=dependencies
        )
    
    def calculate_multiple_months_parallel(self, metrics: List[str], 
                                         year_month_pairs: List[Tuple[int, int]]) -> Dict[str, Dict[Tuple[int, int], MonthlyMetrics]]:
        """Calculate multiple months in parallel with caching."""
        
        key = f"monthly_multi|{cache_key(metrics, year_month_pairs)}"
        dependencies = ([f"metric:{m}" for m in metrics] + 
                       [f"month:{y}:{m}" for y, m in year_month_pairs])
        
        def compute_fn():
            return self.calculator.calculate_multiple_months_parallel(metrics, year_month_pairs)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l3'],  # Large parallel results go to disk cache
            ttl=self.monthly_stats_ttl,
            dependencies=dependencies
        )
    
    def get_monthly_summary(self, metrics: List[str], year: int, month: int) -> Dict[str, Dict[str, Union[float, bool]]]:
        """Get monthly summary with caching."""
        
        key = f"monthly_summary|{cache_key(metrics, year, month)}"
        dependencies = [f"metric:{m}" for m in metrics] + [f"month:{year}:{month}"]
        
        def compute_fn():
            return self.calculator.get_monthly_summary(metrics, year, month)
        
        return cached_analytics_call(
            key=key,
            compute_fn=compute_fn,
            cache_tiers=['l1', 'l2', 'l3'],
            ttl=self.monthly_stats_ttl,
            dependencies=dependencies
        )


class CacheInvalidationManager:
    """Manages cache invalidation based on data updates."""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
    
    def invalidate_metric_data(self, metric: str, start_date: date = None, end_date: date = None) -> Dict[str, int]:
        """Invalidate all cache entries for a specific metric and date range."""
        
        patterns = [f"metric:{metric}"]
        
        if start_date and end_date:
            patterns.append(f"date_range:{start_date}:{end_date}")
        elif start_date:
            patterns.append(f"date_range:{start_date}")
        elif end_date:
            patterns.append(f"date_range.*:{end_date}")
        
        results = {}
        for pattern in patterns:
            result = self.cache_manager.invalidate_pattern(pattern)
            for tier, count in result.items():
                results[f"{tier}_{pattern}"] = count
        
        logger.info(f"Invalidated cache for metric {metric}: {results}")
        return results
    
    def invalidate_date_range(self, start_date: date, end_date: date) -> Dict[str, int]:
        """Invalidate all cache entries for a date range."""
        
        pattern = f"date_range:{start_date}:{end_date}"
        results = self.cache_manager.invalidate_pattern(pattern)
        
        logger.info(f"Invalidated cache for date range {start_date} to {end_date}: {results}")
        return results
    
    def invalidate_all_calculations(self) -> Dict[str, int]:
        """Invalidate all analytics calculations."""
        
        patterns = ["daily_", "weekly_", "monthly_"]
        total_results = {'l1': 0, 'l2': 0, 'l3': 0}
        
        for pattern in patterns:
            results = self.cache_manager.invalidate_pattern(pattern)
            for tier, count in results.items():
                total_results[tier] += count
        
        logger.info(f"Invalidated all analytics calculations: {total_results}")
        return total_results


# Factory functions for cached calculators
def create_cached_daily_calculator() -> CachedDailyMetricsCalculator:
    """Create cached daily metrics calculator with proper data source."""
    try:
        # Try to use database connection
        from ..database import DatabaseManager
        import pandas as pd
        
        db = DatabaseManager()
        # Create a simple data source that loads from database
        with db.get_connection() as conn:
            df = pd.read_sql("SELECT creationDate, type, value FROM health_records", conn)
        
        if not df.empty:
            calculator = DailyMetricsCalculator(df)
            return CachedDailyMetricsCalculator(calculator)
    except Exception as e:
        logger.warning(f"Could not create calculator with database data: {e}")
    
    # Fallback to default initialization
    return CachedDailyMetricsCalculator()


def create_cached_weekly_calculator() -> CachedWeeklyMetricsCalculator:
    """Create cached weekly metrics calculator with proper data source."""
    try:
        # Create daily calculator first
        cached_daily = create_cached_daily_calculator()
        if cached_daily and cached_daily.calculator:
            calculator = WeeklyMetricsCalculator(cached_daily.calculator)
            return CachedWeeklyMetricsCalculator(calculator)
    except Exception as e:
        logger.warning(f"Could not create weekly calculator: {e}")
    
    # Fallback to default initialization
    return CachedWeeklyMetricsCalculator()


def create_cached_monthly_calculator() -> CachedMonthlyMetricsCalculator:
    """Create cached monthly metrics calculator with proper data source."""
    try:
        # Create daily calculator first
        cached_daily = create_cached_daily_calculator()
        if cached_daily and cached_daily.calculator:
            calculator = MonthlyMetricsCalculator(cached_daily.calculator)
            return CachedMonthlyMetricsCalculator(calculator)
    except Exception as e:
        logger.warning(f"Could not create monthly calculator: {e}")
    
    # Fallback to default initialization
    return CachedMonthlyMetricsCalculator()


def create_invalidation_manager() -> CacheInvalidationManager:
    """Create cache invalidation manager."""
    return CacheInvalidationManager()