"""Analytics module for Apple Health Monitor.

This module provides comprehensive analytics capabilities for health data processing,
including calculators for daily/weekly/monthly metrics, caching systems, trend analysis,
and optimized engines for high-performance data processing.

The module is organized into several key components:

- **Basic Calculators**: Core metric calculation classes for different time periods
- **Caching System**: High-performance caching with background refresh and invalidation
- **Trend Analysis**: Week-over-week trends, momentum indicators, and predictions  
- **Optimized Engine**: Streaming data processing with connection pooling and queues
- **Data Adapters**: Protocol definitions and DataFrame adapters for data sources

Example:
    Basic usage with cached calculators:
    
    >>> from analytics import create_cached_daily_calculator
    >>> calculator = create_cached_daily_calculator(database)
    >>> metrics = calculator.calculate_metrics('HKQuantityTypeIdentifierStepCount', 
    ...                                        start_date, end_date)
    
    Advanced usage with optimized engine:
    
    >>> from analytics import OptimizedAnalyticsEngine, AnalyticsRequest
    >>> engine = OptimizedAnalyticsEngine(database)
    >>> request = AnalyticsRequest(metric_type='HKQuantityTypeIdentifierStepCount',
    ...                           calculation_type='daily_metrics')
    >>> results = await engine.process_request(request)
"""

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