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

# Optimized analytics engine
from .optimized_analytics_engine import OptimizedAnalyticsEngine, AnalyticsRequest
from .streaming_data_loader import StreamingDataLoader, DataChunk
from .computation_queue import ComputationQueue, TaskPriority
from .progressive_loader import ProgressiveLoader, ProgressiveLoaderCallbacks, ProgressiveAnalyticsManager
from .connection_pool import ConnectionPool, create_optimized_pool
from .performance_monitor import PerformanceMonitor
from .optimized_calculator_integration import (
    OptimizedCalculatorFactory,
    OptimizedDailyCalculator,
    OptimizedWeeklyCalculator,
    OptimizedMonthlyCalculator,
    OptimizedStatisticsCalculator,
    OptimizedComparisonCalculator,
    migrate_to_optimized_calculators
)

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
    'run_cache_performance_tests',
    
    # Optimized analytics engine
    'OptimizedAnalyticsEngine',
    'AnalyticsRequest',
    'StreamingDataLoader',
    'DataChunk',
    'ComputationQueue',
    'TaskPriority',
    'ProgressiveLoader',
    'ProgressiveLoaderCallbacks',
    'ProgressiveAnalyticsManager',
    'ConnectionPool',
    'create_optimized_pool',
    'PerformanceMonitor',
    
    # Optimized calculator integration
    'OptimizedCalculatorFactory',
    'OptimizedDailyCalculator',
    'OptimizedWeeklyCalculator',
    'OptimizedMonthlyCalculator',
    'OptimizedStatisticsCalculator',
    'OptimizedComparisonCalculator',
    'migrate_to_optimized_calculators'
]