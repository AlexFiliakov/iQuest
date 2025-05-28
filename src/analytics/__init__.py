"""Analytics module for Apple Health Monitor."""

from .data_source_protocol import DataSourceProtocol
from .dataframe_adapter import DataFrameAdapter
from .daily_metrics_calculator import DailyMetricsCalculator
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator
from .day_of_week_analyzer import DayOfWeekAnalyzer
from .week_over_week_trends import (
    WeekOverWeekTrends, TrendResult, StreakInfo, MomentumIndicator, 
    Prediction, WeekTrendData, MomentumType
)

# Caching system
from .cache_manager import AnalyticsCacheManager, get_cache_manager
from .cache_background_refresh import get_refresh_monitor, get_warmup_manager, analytics_cache
from .cached_calculators import (
    CachedDailyMetricsCalculator,
    CachedWeeklyMetricsCalculator, 
    CachedMonthlyMetricsCalculator,
    create_cached_daily_calculator,
    create_cached_weekly_calculator,
    create_cached_monthly_calculator,
    CacheInvalidationManager,
    create_invalidation_manager
)
from .cache_performance_test import run_cache_performance_tests

__all__ = [
    # Data source abstractions
    'DataSourceProtocol',
    'DataFrameAdapter',
    
    # Original calculators
    'DailyMetricsCalculator', 
    'WeeklyMetricsCalculator', 
    'MonthlyMetricsCalculator', 
    'DayOfWeekAnalyzer',
    
    # Week-over-week trends
    'WeekOverWeekTrends',
    'TrendResult',
    'StreakInfo', 
    'MomentumIndicator',
    'Prediction',
    'WeekTrendData',
    'MomentumType',
    
    # Cache system
    'AnalyticsCacheManager',
    'get_cache_manager',
    'get_refresh_monitor', 
    'get_warmup_manager',
    'analytics_cache',
    
    # Cached calculators
    'CachedDailyMetricsCalculator',
    'CachedWeeklyMetricsCalculator',
    'CachedMonthlyMetricsCalculator',
    'create_cached_daily_calculator',
    'create_cached_weekly_calculator', 
    'create_cached_monthly_calculator',
    'CacheInvalidationManager',
    'create_invalidation_manager',
    
    # Performance testing
    'run_cache_performance_tests'
]