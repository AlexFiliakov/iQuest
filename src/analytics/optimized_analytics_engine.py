"""Optimized analytics engine integrating all performance improvements.

This module provides a high-performance analytics engine that combines streaming
data loading, progressive UI updates, multi-level caching, connection pooling,
and priority-based task scheduling for optimal health data processing.

The engine is designed to handle large datasets efficiently while providing
responsive user experiences through progressive loading and real-time updates.

Classes:
    AnalyticsRequest: Data class for analytics computation requests.
    OptimizedAnalyticsEngine: Main engine class integrating all optimizations.

Example:
    >>> engine = OptimizedAnalyticsEngine(database_path="health.db")
    >>> request = AnalyticsRequest(
    ...     metric_type='HKQuantityTypeIdentifierStepCount',
    ...     start_date=datetime(2023, 1, 1),
    ...     end_date=datetime(2023, 12, 31),
    ...     aggregation_level='daily'
    ... )
    >>> results = await engine.process_request(request)
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime, date
import logging
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..health_database import HealthDatabase
from .streaming_data_loader import StreamingDataLoader, DataChunk
from .computation_queue import ComputationQueue, TaskPriority
from .progressive_loader import ProgressiveAnalyticsManager
from .connection_pool import ConnectionPool, PooledDataAccess
from .performance_monitor import PerformanceMonitor
from .cache_manager import AnalyticsCacheManager as CacheManager

logger = logging.getLogger(__name__)


# Aliases for backward compatibility
Priority = TaskPriority


class CalculationType(Enum):
    """Types of calculations available."""
    DAILY_METRICS = "daily_metrics"
    WEEKLY_METRICS = "weekly_metrics"
    MONTHLY_METRICS = "monthly_metrics"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION = "correlation"
    STREAMING = "streaming"
    PROGRESSIVE = "progressive"
    CUSTOM = "custom"


class CacheStrategy(Enum):
    """Cache strategy options."""
    NONE = "none"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


@dataclass
class AnalyticsRequest:
    """Request for analytics computation.
    
    Encapsulates all parameters needed for an analytics computation,
    including the metric type, date range, aggregation level, and
    processing options.
    
    Attributes:
        metric_type (str): The health metric type to analyze.
        start_date (Union[datetime, date]): Start date for the analysis.
        end_date (Union[datetime, date]): End date for the analysis.
        calculation_type (Optional[CalculationType]): Type of calculation to perform.
        aggregation_level (str): Time grouping level ('daily', 'weekly', 'monthly').
        metrics (Optional[List[str]]): Specific metrics to calculate.
        options (Optional[Dict[str, Any]]): Additional processing options.
        priority (Priority): Task priority for queue scheduling.
        cache_strategy (Optional[CacheStrategy]): Cache strategy to use.
        optimize (bool): Whether to use optimized calculations.
        memory_limit_mb (Optional[int]): Memory limit for processing.
    """
    metric_type: str
    start_date: Union[datetime, date] = None
    end_date: Union[datetime, date] = None
    calculation_type: Optional[CalculationType] = None
    aggregation_level: str = 'daily'  # daily, weekly, monthly
    metrics: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None
    priority: Priority = TaskPriority.NORMAL
    cache_strategy: Optional[CacheStrategy] = None
    optimize: bool = False
    memory_limit_mb: Optional[int] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.options is None:
            self.options = {}
        if self.start_date is None:
            self.start_date = datetime.now().date()
        if self.end_date is None:
            self.end_date = datetime.now().date()
    
    def cache_key(self) -> str:
        """Generate cache key for this request.
        
        Creates a unique string identifier for caching purposes based on
        all relevant request parameters.
        
        Returns:
            str: Unique cache key string.
        """
        metrics_str = ','.join(sorted(self.metrics)) if self.metrics else 'all'
        start = self.start_date if isinstance(self.start_date, date) else self.start_date.date()
        end = self.end_date if isinstance(self.end_date, date) else self.end_date.date()
        calc_type = self.calculation_type.value if self.calculation_type else 'default'
        return f"{self.metric_type}_{calc_type}_{self.aggregation_level}_{start}_{end}_{metrics_str}"
    
    def __hash__(self):
        """Make request hashable for caching."""
        return hash(self.cache_key())


@dataclass
class AnalyticsResult:
    """Result of analytics computation.
    
    Contains the computed results along with metadata about the computation
    including success status, any errors, and the original request.
    
    Attributes:
        request (AnalyticsRequest): The original request that generated this result.
        data (Dict[str, Any]): The computed results data.
        success (bool): Whether the computation was successful.
        error (Optional[str]): Error message if computation failed.
        metadata (Optional[Dict[str, Any]]): Additional metadata about the computation.
    """
    request: AnalyticsRequest
    data: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OptimizedAnalyticsEngine:
    """High-performance analytics engine with all optimizations integrated.
    
    This engine combines multiple performance optimization techniques to provide
    fast, memory-efficient health data analytics with real-time UI updates.
    
    Features:
        - Streaming data loading for large datasets
        - Progressive UI updates during computation
        - Multi-level caching with intelligent invalidation
        - Connection pooling for database efficiency
        - Priority-based task scheduling
        - Performance monitoring and metrics
        - Memory-efficient chunked processing
        - Asynchronous computation with callbacks
    
    The engine is designed to handle datasets of any size while maintaining
    responsive user interfaces through progressive loading and incremental
    result delivery.
    
    Attributes:
        connection_pool (ConnectionPool): Database connection pool.
        data_access (PooledDataAccess): Pooled database access layer.
        data_loader (StreamingDataLoader): Streaming data loading system.
        computation_queue (ComputationQueue): Task scheduling and execution.
        progressive_manager (ProgressiveAnalyticsManager): Progressive loading coordination.
        cache_manager (CacheManager): Multi-level caching system.
        performance_monitor (PerformanceMonitor): Performance tracking.
    """
    
    def __init__(self,
                 database_path: str,
                 cache_manager: Optional[CacheManager] = None,
                 enable_monitoring: bool = True):
        """Initialize optimized analytics engine.
        
        Sets up all components including connection pooling, streaming data loading,
        computation queues, progressive loading, caching, and performance monitoring.
        
        Args:
            database_path (str): Path to SQLite database file.
            cache_manager (Optional[CacheManager]): Optional cache manager instance.
                                                   Creates new one if not provided.
            enable_monitoring (bool): Whether to enable performance monitoring.
                                     Defaults to True.
        """
        # Connection pooling
        self.connection_pool = ConnectionPool(
            database_path=database_path,
            min_connections=3,
            max_connections=10,
            enable_wal=True,
            enable_query_cache=True
        )
        
        # Data access with pooling
        self.data_access = PooledDataAccess(self.connection_pool)
        
        # Streaming data loader
        self.data_loader = StreamingDataLoader(
            data_access=self.data_access,
            chunk_days=30,
            max_memory_mb=100,
            prefetch_chunks=2
        )
        
        # Computation queue
        self.computation_queue = ComputationQueue(
            max_io_workers=4,
            max_cpu_workers=4,
            enable_monitoring=enable_monitoring
        )
        
        # Progressive loading
        self.progressive_manager = ProgressiveAnalyticsManager(
            data_loader=self.data_loader,
            computation_queue=self.computation_queue
        )
        
        # Caching
        self.cache_manager = cache_manager or CacheManager()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(
            enable_memory_profiling=enable_monitoring
        ) if enable_monitoring else None
        
        # Calculators cache
        self._calculators = {}
        
    def calculate_metrics(self, request: AnalyticsRequest) -> Any:
        """
        Calculate metrics with full optimization stack.
        
        Args:
            request: Analytics request
            
        Returns:
            Calculation results
        """
        # Check cache first
        cache_key = request.cache_key()
        cached_result = self.cache_manager.get(cache_key)
        
        if cached_result is not None:
            logger.debug(f"Cache hit for {cache_key}")
            if self.performance_monitor:
                self.performance_monitor.record_metric("cache_hit", 1, "count")
            return cached_result
        
        # Profile the operation
        with self._profile_context(f"calculate_{request.metric_type}") as profile:
            # Submit to computation queue
            task_id = self.computation_queue.submit(
                self._perform_calculation,
                request,
                priority=request.priority,
                cpu_bound=True
            )
            
            # Get result
            result = self.computation_queue.get_result(task_id)
            
            # Cache result
            self.cache_manager.set(cache_key, result, ttl=3600)
            
            return result
    
    def calculate_progressive(self, request: AnalyticsRequest) -> str:
        """
        Calculate metrics with progressive loading.
        
        Args:
            request: Analytics request
            
        Returns:
            Session ID for tracking progress
        """
        # Create computation function
        def compute_chunk(data: pd.DataFrame) -> Any:
            calculator = self._get_calculator(request.metric_type)
            return calculator.calculate_chunk(data, request)
        
        # Start progressive loading
        session_id = self.progressive_manager.loader.load_progressive(
            computation_func=compute_chunk,
            start_date=request.start_date,
            end_date=request.end_date,
            metrics=request.metrics,
            skeleton_config={
                'metric_type': request.metric_type,
                'aggregation': request.aggregation_level
            }
        )
        
        return session_id
    
    def _perform_calculation(self, request: AnalyticsRequest) -> Any:
        """Perform the actual calculation."""
        with self._profile_context(f"calculation_{request.metric_type}"):
            # Get calculator
            calculator = self._get_calculator(request.metric_type)
            
            # Determine optimal loading strategy
            date_range_days = (request.end_date - request.start_date).days + 1
            
            if date_range_days <= 365:
                # Small dataset - load all at once
                return self._calculate_direct(calculator, request)
            else:
                # Large dataset - use streaming
                return self._calculate_streaming(calculator, request)
    
    def _calculate_direct(self, calculator: Any, request: AnalyticsRequest) -> Any:
        """Calculate using direct data loading."""
        with self._profile_context("direct_loading"):
            # Load optimized data
            data = self.data_loader.load_optimized(
                start_date=request.start_date,
                end_date=request.end_date,
                metrics=request.metrics,
                aggregation=request.aggregation_level
            )
            
            # Calculate
            with self._profile_context("computation"):
                result = calculator.calculate(data, request)
            
            return result
    
    def _calculate_streaming(self, calculator: Any, request: AnalyticsRequest) -> Any:
        """Calculate using streaming data loading."""
        results = []
        
        # Stream data in chunks
        for chunk in self.data_loader.stream_data(
            start_date=request.start_date,
            end_date=request.end_date,
            metrics=request.metrics
        ):
            with self._profile_context(f"chunk_{chunk.chunk_index}"):
                # Process chunk
                chunk_result = calculator.calculate_chunk(chunk.data, request)
                results.append(chunk_result)
            
            # Free memory if needed
            if chunk.size_mb > 50:
                self._optimize_memory()
        
        # Combine results
        with self._profile_context("combine_results"):
            final_result = calculator.combine_results(results, request)
        
        return final_result
    
    def _get_calculator(self, metric_type: str) -> Any:
        """Get or create calculator instance."""
        if metric_type not in self._calculators:
            # Import and create calculator
            if metric_type == 'daily':
                from .daily_metrics_calculator import DailyMetricsCalculator
                calculator = OptimizedDailyMetricsCalculator()
            elif metric_type == 'weekly':
                from .weekly_metrics_calculator import WeeklyMetricsCalculator
                calculator = OptimizedWeeklyMetricsCalculator()
            elif metric_type == 'monthly':
                from .monthly_metrics_calculator import MonthlyMetricsCalculator
                calculator = OptimizedMonthlyMetricsCalculator()
            else:
                raise ValueError(f"Unknown metric type: {metric_type}")
            
            self._calculators[metric_type] = calculator
        
        return self._calculators[metric_type]
    
    def _profile_context(self, operation_name: str):
        """Get profiling context if monitoring is enabled."""
        if self.performance_monitor:
            return self.performance_monitor.profile_operation(operation_name)
        else:
            # Null context manager
            from contextlib import nullcontext
            return nullcontext()
    
    def _optimize_memory(self):
        """Optimize memory usage."""
        import gc
        gc.collect()
        
        if self.performance_monitor:
            self.performance_monitor.record_metric(
                "memory_optimization",
                1,
                "count"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            'connection_pool': self.connection_pool.get_stats(),
            'computation_queue': self.computation_queue.get_queue_stats(),
            'cache': self.cache_manager.get_stats() if hasattr(self.cache_manager, 'get_stats') else {}
        }
        
        if self.performance_monitor:
            stats['performance'] = self.performance_monitor.get_performance_summary()
        
        return stats
    
    def shutdown(self):
        """Shutdown the analytics engine."""
        logger.info("Shutting down analytics engine")
        
        # Shutdown components
        self.computation_queue.shutdown()
        self.connection_pool.close()
        
        if self.performance_monitor:
            self.performance_monitor.shutdown()


class OptimizedCalculatorBase:
    """Base class for optimized calculators."""
    
    def calculate(self, data: pd.DataFrame, request: AnalyticsRequest) -> Any:
        """Calculate metrics for full dataset."""
        raise NotImplementedError
    
    def calculate_chunk(self, data: pd.DataFrame, request: AnalyticsRequest) -> Any:
        """Calculate metrics for a data chunk."""
        # Default implementation - can be overridden
        return self.calculate(data, request)
    
    def combine_results(self, results: List[Any], request: AnalyticsRequest) -> Any:
        """Combine chunk results into final result."""
        raise NotImplementedError
    
    def _optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        # Handle empty DataFrame
        if df is None or df.empty:
            return df
            
        try:
            # Convert object columns to category if appropriate
            for col in df.select_dtypes(['object']).columns:
                num_unique = df[col].nunique()
                num_total = len(df[col])
                if num_total > 0 and num_unique / num_total < 0.5:
                    df[col] = df[col].astype('category')
            
            # Downcast numeric types
            for col in df.select_dtypes(['float']).columns:
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            for col in df.select_dtypes(['int']).columns:
                df[col] = pd.to_numeric(df[col], downcast='integer')
            
            return df
            
        except Exception as e:
            logger.warning(f"Error optimizing DataFrame: {e}")
            return df


class OptimizedDailyMetricsCalculator(OptimizedCalculatorBase):
    """Optimized daily metrics calculator."""
    
    def calculate(self, data: pd.DataFrame, request: AnalyticsRequest) -> Dict[str, Any]:
        """Calculate daily metrics."""
        # Optimize DataFrame
        data = self._optimize_dataframe(data)
        
        # Group by date efficiently
        daily_groups = data.groupby(pd.Grouper(key='date', freq='D'))
        
        # Calculate metrics using numpy where possible
        results = {}
        
        for date, group in daily_groups:
            if not group.empty:
                values = group['value'].values  # numpy array
                
                results[date] = {
                    'count': len(values),
                    'sum': np.sum(values),
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'percentiles': {
                        '25': np.percentile(values, 25),
                        '75': np.percentile(values, 75),
                        '90': np.percentile(values, 90)
                    }
                }
        
        return results
    
    def combine_results(self, results: List[Dict[str, Any]], request: AnalyticsRequest) -> Dict[str, Any]:
        """Combine daily results from chunks."""
        combined = {}
        
        for chunk_result in results:
            combined.update(chunk_result)
        
        return combined


class OptimizedWeeklyMetricsCalculator(OptimizedCalculatorBase):
    """Optimized weekly metrics calculator."""
    
    def calculate(self, data: pd.DataFrame, request: AnalyticsRequest) -> Dict[str, Any]:
        """Calculate weekly metrics."""
        # Optimize DataFrame
        data = self._optimize_dataframe(data)
        
        # Add week column
        data['week'] = pd.to_datetime(data['date']).dt.to_period('W-MON')
        
        # Group by week
        weekly_groups = data.groupby('week')
        
        results = {}
        for week, group in weekly_groups:
            values = group['value'].values
            
            results[str(week)] = {
                'count': len(values),
                'sum': np.sum(values),
                'mean': np.mean(values),
                'daily_averages': self._calculate_daily_pattern(group)
            }
        
        return results
    
    def _calculate_daily_pattern(self, week_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate average by day of week."""
        week_data['day_of_week'] = pd.to_datetime(week_data['date']).dt.day_name()
        return week_data.groupby('day_of_week')['value'].mean().to_dict()


class OptimizedMonthlyMetricsCalculator(OptimizedCalculatorBase):
    """Optimized monthly metrics calculator."""
    
    def calculate(self, data: pd.DataFrame, request: AnalyticsRequest) -> Dict[str, Any]:
        """Calculate monthly metrics."""
        # Optimize DataFrame
        data = self._optimize_dataframe(data)
        
        # Add month column
        data['month'] = pd.to_datetime(data['date']).dt.to_period('M')
        
        # Group by month
        monthly_groups = data.groupby('month')
        
        results = {}
        for month, group in monthly_groups:
            values = group['value'].values
            
            results[str(month)] = {
                'count': len(values),
                'sum': np.sum(values),
                'mean': np.mean(values),
                'trend': self._calculate_trend(group)
            }
        
        return results
    
    def _calculate_trend(self, month_data: pd.DataFrame) -> str:
        """Calculate month trend."""
        # Simple linear regression on day number vs value
        days = np.arange(len(month_data))
        values = month_data['value'].values
        
        if len(values) < 2:
            return 'insufficient_data'
        
        # Calculate slope
        slope = np.polyfit(days, values, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'