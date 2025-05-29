"""Integration module to connect optimized analytics engine with existing calculators."""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import logging
import pandas as pd

from .optimized_analytics_engine import OptimizedAnalyticsEngine, AnalyticsRequest, TaskPriority
from .daily_metrics_calculator import DailyMetricsCalculator
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator
from ..statistics_calculator import StatisticsCalculator
from .comparison_overlay_calculator import ComparisonOverlayCalculator
from .cached_calculators import CachedDailyMetricsCalculator, CachedWeeklyMetricsCalculator, CachedMonthlyMetricsCalculator
from .cache_manager import AnalyticsCacheManager as CacheManager
from .streaming_data_loader import StreamingDataLoader
from .progressive_loader import ProgressiveLoaderCallbacks

logger = logging.getLogger(__name__)


class OptimizedCalculatorFactory:
    """Factory for creating optimized calculator instances."""
    
    def __init__(self, database_path: str, cache_manager: Optional[CacheManager] = None):
        """
        Initialize factory with optimized analytics engine.
        
        Args:
            database_path: Path to SQLite database
            cache_manager: Optional cache manager instance
        """
        self.engine = OptimizedAnalyticsEngine(
            database_path=database_path,
            cache_manager=cache_manager,
            enable_monitoring=True
        )
        
        # Store original calculator instances for compatibility
        self._calculators = {}
        
    def get_daily_calculator(self) -> 'OptimizedDailyCalculator':
        """Get optimized daily metrics calculator."""
        if 'daily' not in self._calculators:
            self._calculators['daily'] = OptimizedDailyCalculator(self.engine)
        return self._calculators['daily']
    
    def get_weekly_calculator(self) -> 'OptimizedWeeklyCalculator':
        """Get optimized weekly metrics calculator."""
        if 'weekly' not in self._calculators:
            self._calculators['weekly'] = OptimizedWeeklyCalculator(self.engine)
        return self._calculators['weekly']
    
    def get_monthly_calculator(self) -> 'OptimizedMonthlyCalculator':
        """Get optimized monthly metrics calculator."""
        if 'monthly' not in self._calculators:
            self._calculators['monthly'] = OptimizedMonthlyCalculator(self.engine)
        return self._calculators['monthly']
    
    def get_statistics_calculator(self) -> 'OptimizedStatisticsCalculator':
        """Get optimized statistics calculator."""
        if 'statistics' not in self._calculators:
            self._calculators['statistics'] = OptimizedStatisticsCalculator(self.engine)
        return self._calculators['statistics']
    
    def get_comparison_calculator(self) -> 'OptimizedComparisonCalculator':
        """Get optimized comparison overlay calculator."""
        if 'comparison' not in self._calculators:
            self._calculators['comparison'] = OptimizedComparisonCalculator(self.engine)
        return self._calculators['comparison']
    
    def shutdown(self):
        """Shutdown the analytics engine."""
        self.engine.shutdown()


class OptimizedCalculatorBase:
    """Base class for optimized calculator wrappers."""
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with optimized engine."""
        self.engine = engine
        self._callbacks = ProgressiveLoaderCallbacks()
        
    def set_progress_callbacks(self, callbacks: ProgressiveLoaderCallbacks):
        """Set callbacks for progressive loading."""
        self._callbacks = callbacks
    
    def _create_request(self, start_date: datetime, end_date: datetime,
                       metrics: Optional[List[str]] = None,
                       priority: TaskPriority = TaskPriority.NORMAL,
                       **kwargs) -> AnalyticsRequest:
        """Create analytics request."""
        return AnalyticsRequest(
            metric_type=self.metric_type,
            start_date=start_date,
            end_date=end_date,
            aggregation_level=self.aggregation_level,
            metrics=metrics,
            options=kwargs,
            priority=priority
        )


class OptimizedDailyCalculator(OptimizedCalculatorBase):
    """Optimized daily metrics calculator."""
    
    metric_type = 'daily'
    aggregation_level = 'daily'
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with engine and base calculator."""
        super().__init__(engine)
        # Keep reference to original calculator for method compatibility
        self._base_calculator = DailyMetricsCalculator()
        
    def calculate_daily_metrics(self, df: pd.DataFrame, start_date: datetime, 
                              end_date: datetime, source_info: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate daily metrics using optimized engine.
        
        This method maintains API compatibility with the original calculator.
        """
        # If DataFrame is provided directly, use original calculator
        if df is not None and not df.empty:
            return self._base_calculator.calculate_daily_metrics(df, start_date, end_date, source_info)
        
        # Otherwise use optimized engine
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            source_info=source_info
        )
        
        return self.engine.calculate_metrics(request)
    
    def calculate_progressive(self, start_date: datetime, end_date: datetime,
                            metrics: Optional[List[str]] = None) -> str:
        """Calculate with progressive loading."""
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            priority=TaskPriority.CRITICAL
        )
        
        return self.engine.calculate_progressive(request)
    
    # Delegate other methods to base calculator for compatibility
    def __getattr__(self, name):
        """Delegate unknown attributes to base calculator."""
        return getattr(self._base_calculator, name)


class OptimizedWeeklyCalculator(OptimizedCalculatorBase):
    """Optimized weekly metrics calculator."""
    
    metric_type = 'weekly'
    aggregation_level = 'weekly'
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with engine and base calculator."""
        super().__init__(engine)
        self._base_calculator = WeeklyMetricsCalculator()
        
    def calculate_weekly_metrics(self, df: pd.DataFrame, start_date: datetime,
                               end_date: datetime, include_current: bool = True) -> Dict[str, Any]:
        """Calculate weekly metrics using optimized engine."""
        # If DataFrame is provided directly, use original calculator
        if df is not None and not df.empty:
            return self._base_calculator.calculate_weekly_metrics(df, start_date, end_date, include_current)
        
        # Otherwise use optimized engine
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            include_current=include_current
        )
        
        return self.engine.calculate_metrics(request)
    
    def calculate_progressive(self, start_date: datetime, end_date: datetime,
                            metrics: Optional[List[str]] = None) -> str:
        """Calculate with progressive loading."""
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            priority=TaskPriority.CRITICAL
        )
        
        return self.engine.calculate_progressive(request)
    
    def __getattr__(self, name):
        """Delegate unknown attributes to base calculator."""
        return getattr(self._base_calculator, name)


class OptimizedMonthlyCalculator(OptimizedCalculatorBase):
    """Optimized monthly metrics calculator."""
    
    metric_type = 'monthly'
    aggregation_level = 'monthly'
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with engine and base calculator."""
        super().__init__(engine)
        self._base_calculator = MonthlyMetricsCalculator()
        
    def calculate_monthly_metrics(self, df: pd.DataFrame, start_date: datetime,
                                end_date: datetime, mode: str = 'calendar') -> Dict[str, Any]:
        """Calculate monthly metrics using optimized engine."""
        # If DataFrame is provided directly, use original calculator
        if df is not None and not df.empty:
            return self._base_calculator.calculate_monthly_metrics(df, start_date, end_date, mode)
        
        # Otherwise use optimized engine
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            mode=mode
        )
        
        return self.engine.calculate_metrics(request)
    
    def calculate_progressive(self, start_date: datetime, end_date: datetime,
                            metrics: Optional[List[str]] = None, mode: str = 'calendar') -> str:
        """Calculate with progressive loading."""
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            mode=mode,
            priority=TaskPriority.CRITICAL
        )
        
        return self.engine.calculate_progressive(request)
    
    def __getattr__(self, name):
        """Delegate unknown attributes to base calculator."""
        return getattr(self._base_calculator, name)


class OptimizedStatisticsCalculator(OptimizedCalculatorBase):
    """Optimized statistics calculator."""
    
    metric_type = 'statistics'
    aggregation_level = 'daily'
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with engine and base calculator."""
        super().__init__(engine)
        self._base_calculator = StatisticsCalculator()
        
    def calculate_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics using optimized engine."""
        # For basic statistics, delegate to original calculator
        # as it's already efficient for in-memory data
        return self._base_calculator.calculate_basic_statistics(df)
    
    def calculate_time_range_statistics(self, start_date: datetime, end_date: datetime,
                                      metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculate statistics for a time range using optimized engine."""
        request = self._create_request(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics
        )
        
        # Use custom metric type for statistics
        request.metric_type = 'statistics'
        
        return self.engine.calculate_metrics(request)
    
    def __getattr__(self, name):
        """Delegate unknown attributes to base calculator."""
        return getattr(self._base_calculator, name)


class OptimizedComparisonCalculator(OptimizedCalculatorBase):
    """Optimized comparison overlay calculator."""
    
    metric_type = 'comparison'
    aggregation_level = 'daily'
    
    def __init__(self, engine: OptimizedAnalyticsEngine):
        """Initialize with engine and base calculator."""
        super().__init__(engine)
        self._base_calculator = ComparisonOverlayCalculator()
        
    def calculate_period_comparison(self, current_data: pd.DataFrame, previous_data: pd.DataFrame,
                                  period_type: str = 'week') -> Dict[str, Any]:
        """Calculate period comparison."""
        # For direct DataFrame comparison, use original calculator
        return self._base_calculator.calculate_period_comparison(
            current_data, previous_data, period_type
        )
    
    def calculate_optimized_comparison(self, current_start: datetime, current_end: datetime,
                                     previous_start: datetime, previous_end: datetime,
                                     metrics: Optional[List[str]] = None,
                                     period_type: str = 'week') -> Dict[str, Any]:
        """Calculate comparison using optimized engine."""
        # Get current period data
        current_request = self._create_request(
            start_date=current_start,
            end_date=current_end,
            metrics=metrics
        )
        current_result = self.engine.calculate_metrics(current_request)
        
        # Get previous period data
        previous_request = self._create_request(
            start_date=previous_start,
            end_date=previous_end,
            metrics=metrics
        )
        previous_result = self.engine.calculate_metrics(previous_request)
        
        # Perform comparison
        return self._base_calculator.compare_results(
            current_result, previous_result, period_type
        )
    
    def __getattr__(self, name):
        """Delegate unknown attributes to base calculator."""
        return getattr(self._base_calculator, name)


def migrate_to_optimized_calculators(database_path: str, 
                                   cache_manager: Optional[CacheManager] = None) -> Dict[str, Any]:
    """
    Migrate existing calculator usage to optimized versions.
    
    Args:
        database_path: Path to SQLite database
        cache_manager: Optional cache manager
        
    Returns:
        Dictionary of optimized calculator instances
    """
    factory = OptimizedCalculatorFactory(database_path, cache_manager)
    
    return {
        'daily': factory.get_daily_calculator(),
        'weekly': factory.get_weekly_calculator(),
        'monthly': factory.get_monthly_calculator(),
        'statistics': factory.get_statistics_calculator(),
        'comparison': factory.get_comparison_calculator(),
        'factory': factory
    }