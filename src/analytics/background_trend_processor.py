"""
Background Trend Processor for Apple Health Monitor.

Calculates and caches trend patterns in the background to improve performance.
Triggers automatically when new data is imported and periodically refreshes cached trends.
"""

import logging
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, Future
import json
import pickle
from pathlib import Path

from .advanced_trend_engine import AdvancedTrendAnalysisEngine
from .advanced_trend_models import TrendAnalysis as TrendResult
from .comparative_analytics import ComparativeAnalyticsEngine
from .cache_manager import AnalyticsCacheManager as CacheManager
# from ..models import Metric  # TODO: Define Metric enum

logger = logging.getLogger(__name__)

# Temporary metric list until proper enum is defined
VALID_METRICS = {
    'HKQuantityTypeIdentifierStepCount',
    'HKQuantityTypeIdentifierDistanceWalkingRunning', 
    'HKQuantityTypeIdentifierActiveEnergyBurned',
    'HKQuantityTypeIdentifierHeartRate',
    'HKCategoryTypeIdentifierSleepAnalysis',
    'HKQuantityTypeIdentifierBodyMass',
    'HKQuantityTypeIdentifierHeight'
}


class TrendProcessingTask:
    """Represents a trend processing task."""
    
    def __init__(self, metric: str, priority: int = 0, force_refresh: bool = False):
        self.metric = metric
        self.priority = priority
        self.force_refresh = force_refresh
        self.created_at = datetime.now()
        self.task_id = f"{metric}_{self.created_at.timestamp()}"
    
    def __lt__(self, other):
        """Higher priority tasks are processed first."""
        return self.priority > other.priority


class BackgroundTrendProcessor:
    """
    Processes trend calculations in the background with intelligent caching.
    
    Features:
    - Asynchronous trend calculation
    - Priority-based task queue
    - Intelligent cache management
    - Automatic refresh on data changes
    - Minimal resource usage
    """
    
    CACHE_EXPIRY_HOURS = 24  # Default cache expiry
    MAX_WORKERS = 2  # Limit concurrent processing
    BATCH_SIZE = 5  # Process trends in batches
    
    def __init__(self, database, cache_manager: Optional[CacheManager] = None):
        """Initialize the background trend processor."""
        self.database = database
        self.cache_manager = cache_manager or CacheManager()
        
        # Initialize processing components
        self.task_queue = queue.PriorityQueue()
        self.processing_threads = []
        self.executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        self._shutdown = False
        
        # Track processing state
        self.processing_metrics: Set[str] = set()
        self.last_processed: Dict[str, datetime] = {}
        self.processing_futures: Dict[str, Future] = {}
        
        # Initialize analytics engines
        self.trend_engine = AdvancedTrendAnalysisEngine()
        self.comparative_engine = ComparativeAnalyticsEngine(database)
        
        # Cache configuration
        self.cache_dir = Path.home() / ".apple_health_monitor" / "trend_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Start background processor
        self._start_processor()
    
    def _start_processor(self):
        """Start the background processing thread."""
        processor_thread = threading.Thread(
            target=self._process_tasks,
            daemon=True,
            name="TrendProcessor"
        )
        processor_thread.start()
        self.processing_threads.append(processor_thread)
        logger.info("Background trend processor started")
    
    def _process_tasks(self):
        """Main processing loop."""
        while not self._shutdown:
            try:
                # Get next task with timeout
                task = self.task_queue.get(timeout=1.0)
                
                if task.metric not in self.processing_metrics:
                    # Submit for processing
                    self.processing_metrics.add(task.metric)
                    future = self.executor.submit(
                        self._calculate_trend,
                        task.metric,
                        task.force_refresh
                    )
                    self.processing_futures[task.metric] = future
                    
                    # Handle completion
                    future.add_done_callback(
                        lambda f, m=task.metric: self._on_trend_complete(m, f)
                    )
                
            except queue.Empty:
                # No tasks, check for stale cache entries
                self._check_stale_cache()
            except Exception as e:
                logger.error(f"Error in trend processor: {e}")
    
    def _calculate_trend(self, metric: str, force_refresh: bool = False) -> Optional[TrendResult]:
        """Calculate trend for a specific metric."""
        try:
            # Check cache first
            if not force_refresh:
                cached_result = self._get_cached_trend(metric)
                if cached_result:
                    logger.debug(f"Using cached trend for {metric}")
                    return cached_result
            
            logger.info(f"Calculating trend for {metric}")
            
            # Get data from database
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Analyze last year
            
            data = self.database.get_metric_data(
                metric=metric,
                start_date=start_date,
                end_date=end_date
            )
            
            if not data or len(data) < 7:
                logger.warning(f"Insufficient data for trend analysis: {metric}")
                return None
            
            # Perform trend analysis
            trend_result = self.trend_engine.analyze_trend(
                data,
                metric_name=metric,
                forecast_days=30
            )
            
            # Calculate comparative analytics
            historical_comparison = self.comparative_engine.get_historical_comparison(
                metric=metric,
                current_date=end_date
            )
            
            # Enhance trend result with comparative data
            if trend_result and historical_comparison:
                trend_result.comparative_data = {
                    'rolling_7_day': historical_comparison.rolling_7_day,
                    'rolling_30_day': historical_comparison.rolling_30_day,
                    'rolling_90_day': historical_comparison.rolling_90_day,
                    'trend_direction': historical_comparison.trend_direction,
                    'personal_best': historical_comparison.personal_best,
                    'personal_average': historical_comparison.personal_average
                }
            
            # Cache the result
            if trend_result:
                self._cache_trend(metric, trend_result)
                self.last_processed[metric] = datetime.now()
            
            return trend_result
            
        except Exception as e:
            logger.error(f"Error calculating trend for {metric}: {e}")
            return None
    
    def _on_trend_complete(self, metric: str, future: Future):
        """Handle trend calculation completion."""
        try:
            result = future.result()
            if result:
                logger.info(f"Trend calculation complete for {metric}")
                # Notify any listeners (could emit signal here)
        except Exception as e:
            logger.error(f"Trend calculation failed for {metric}: {e}")
        finally:
            self.processing_metrics.discard(metric)
            self.processing_futures.pop(metric, None)
    
    def _get_cached_trend(self, metric: str) -> Optional[TrendResult]:
        """Retrieve cached trend result."""
        cache_key = f"trend_{metric}"
        
        # Check in-memory cache first
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                # Check if cache is still valid
                file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_age < timedelta(hours=self.CACHE_EXPIRY_HOURS):
                    with open(cache_file, 'rb') as f:
                        trend_result = pickle.load(f)
                    
                    # Store in memory cache
                    self.cache_manager.set(cache_key, trend_result, ttl=3600)
                    return trend_result
            except Exception as e:
                logger.error(f"Error loading cached trend: {e}")
        
        return None
    
    def _cache_trend(self, metric: str, trend_result: TrendResult):
        """Cache trend result to memory and disk."""
        cache_key = f"trend_{metric}"
        
        # Store in memory cache
        self.cache_manager.set(cache_key, trend_result, ttl=3600)
        
        # Store on disk for persistence
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(trend_result, f)
        except Exception as e:
            logger.error(f"Error caching trend to disk: {e}")
    
    def _check_stale_cache(self):
        """Check for and refresh stale cache entries."""
        current_time = datetime.now()
        
        for metric, last_time in self.last_processed.items():
            if current_time - last_time > timedelta(hours=self.CACHE_EXPIRY_HOURS):
                # Queue for refresh with low priority
                self.queue_trend_calculation(metric, priority=-1)
    
    def queue_trend_calculation(self, metric: str, priority: int = 0, force_refresh: bool = False):
        """Queue a metric for trend calculation."""
        if metric not in VALID_METRICS:
            logger.warning(f"Invalid metric: {metric}")
            return
        
        task = TrendProcessingTask(metric, priority, force_refresh)
        self.task_queue.put(task)
        logger.debug(f"Queued trend calculation for {metric} with priority {priority}")
    
    def queue_all_metrics(self, priority: int = 0):
        """Queue all available metrics for trend calculation."""
        for metric in VALID_METRICS:
            self.queue_trend_calculation(metric, priority)
    
    def get_trend(self, metric: str, wait: bool = False) -> Optional[TrendResult]:
        """
        Get trend for a metric, optionally waiting for calculation.
        
        Args:
            metric: The metric to get trend for
            wait: Whether to wait for calculation if not cached
            
        Returns:
            TrendResult if available, None otherwise
        """
        # Check cache first
        cached_result = self._get_cached_trend(metric)
        if cached_result:
            return cached_result
        
        # Queue for calculation if not being processed
        if metric not in self.processing_metrics:
            self.queue_trend_calculation(metric, priority=10)  # High priority
        
        if wait and metric in self.processing_futures:
            # Wait for completion
            future = self.processing_futures[metric]
            try:
                return future.result(timeout=30)  # 30 second timeout
            except Exception as e:
                logger.error(f"Error waiting for trend calculation: {e}")
        
        return None
    
    def on_data_import_complete(self, metrics_affected: List[str]):
        """
        Handle data import completion by queueing affected metrics.
        
        Args:
            metrics_affected: List of metrics that were updated
        """
        logger.info(f"Data import complete, refreshing trends for: {metrics_affected}")
        
        for metric in metrics_affected:
            # Force refresh with high priority
            self.queue_trend_calculation(metric, priority=5, force_refresh=True)
    
    def clear_cache(self, metric: Optional[str] = None):
        """Clear cached trends."""
        if metric:
            # Clear specific metric
            cache_key = f"trend_{metric}"
            self.cache_manager.delete(cache_key)
            
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cached trends
            self.cache_manager.clear()
            for cache_file in self.cache_dir.glob("trend_*.pkl"):
                cache_file.unlink()
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status."""
        return {
            'queue_size': self.task_queue.qsize(),
            'processing': list(self.processing_metrics),
            'cached_metrics': list(self.last_processed.keys()),
            'cache_age': {
                metric: (datetime.now() - last_time).total_seconds() / 3600
                for metric, last_time in self.last_processed.items()
            }
        }
    
    def shutdown(self):
        """Shutdown the background processor."""
        logger.info("Shutting down background trend processor")
        self._shutdown = True
        
        # Wait for threads to complete
        for thread in self.processing_threads:
            thread.join(timeout=5)
        
        # Shutdown executor
        self.executor.shutdown(wait=True, cancel_futures=True)
        
        logger.info("Background trend processor shutdown complete")