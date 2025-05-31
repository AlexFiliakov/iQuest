"""
Background cache refresh mechanism for proactive cache warming.
Monitors popular queries and refreshes them before expiration.
"""

import threading
import time
import heapq
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .cache_manager import get_cache_manager, CacheEntry

logger = logging.getLogger(__name__)


@dataclass
class RefreshTask:
    """Background refresh task."""
    key: str
    compute_fn: Callable[[], Any]
    priority: float
    scheduled_time: datetime
    cache_tiers: List[str]
    ttl: Optional[int]
    dependencies: List[str]
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """For heap ordering."""
        return self.scheduled_time < other.scheduled_time


class CacheRefreshMonitor:
    """Monitors cache access patterns and schedules background refreshes."""
    
    def __init__(self, max_workers: int = 2):
        self.access_counts: Counter = Counter()
        self.compute_functions: Dict[str, Callable] = {}
        self.refresh_configs: Dict[str, Dict] = {}
        self.refresh_queue: List[RefreshTask] = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="cache-refresh")
        self.running = False
        self.refresh_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Configuration
        self.min_access_count = 3  # Minimum accesses to qualify for refresh
        self.refresh_threshold = 0.75  # Refresh when 75% of TTL elapsed
        self.check_interval = 30  # Check every 30 seconds
        self.max_concurrent_refreshes = 2
        
    def record_access(self, key: str, compute_fn: Callable, cache_tiers: List[str] = None,
                     ttl: Optional[int] = None, dependencies: List[str] = None) -> None:
        """Record cache access for potential refresh scheduling."""
        with self._lock:
            self.access_counts[key] += 1
            self.compute_functions[key] = compute_fn
            self.refresh_configs[key] = {
                'cache_tiers': cache_tiers or ['l1', 'l2', 'l3'],
                'ttl': ttl,
                'dependencies': dependencies or []
            }
            
            # Schedule refresh if popular enough
            if self.access_counts[key] >= self.min_access_count:
                self._schedule_refresh(key)
    
    def _schedule_refresh(self, key: str) -> None:
        """Schedule background refresh for a key."""
        cache_manager = get_cache_manager()
        
        # Check if already scheduled
        if any(task.key == key for task in self.refresh_queue):
            return
        
        # Determine refresh time based on cache tier and TTL
        refresh_time = self._calculate_refresh_time(key)
        if refresh_time is None:
            return
        
        config = self.refresh_configs[key]
        task = RefreshTask(
            key=key,
            compute_fn=self.compute_functions[key],
            priority=self.access_counts[key],  # Higher access count = higher priority
            scheduled_time=refresh_time,
            cache_tiers=config['cache_tiers'],
            ttl=config['ttl'],
            dependencies=config['dependencies']
        )
        
        heapq.heappush(self.refresh_queue, task)
        logger.debug(f"Scheduled refresh for {key} at {refresh_time}")
    
    def _calculate_refresh_time(self, key: str) -> Optional[datetime]:
        """Calculate when to refresh based on cache TTL."""
        cache_manager = get_cache_manager()
        
        # Check L1 cache first
        if key in cache_manager.l1_cache._cache:
            entry = cache_manager.l1_cache._cache[key]
            if entry.ttl_seconds:
                elapsed_ratio = entry.age_seconds / entry.ttl_seconds
                if elapsed_ratio < self.refresh_threshold:
                    # Schedule refresh at threshold
                    remaining_time = entry.ttl_seconds - entry.age_seconds
                    refresh_delay = remaining_time * (1 - self.refresh_threshold)
                    return datetime.now() + timedelta(seconds=refresh_delay)
        
        # Default refresh time (refresh frequently accessed items more often)
        access_count = self.access_counts[key]
        base_refresh_minutes = max(5, 30 - (access_count * 2))  # More popular = more frequent
        return datetime.now() + timedelta(minutes=base_refresh_minutes)
    
    def start(self) -> None:
        """Start background refresh monitoring."""
        if self.running:
            return
        
        self.running = True
        self.refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.refresh_thread.start()
        logger.info("Started cache refresh monitor")
    
    def stop(self) -> None:
        """Stop background refresh monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        logger.info("Stopped cache refresh monitor")
    
    def _refresh_loop(self) -> None:
        """Main refresh monitoring loop."""
        active_refreshes = 0
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Process due refresh tasks
                while (self.refresh_queue and 
                       self.refresh_queue[0].scheduled_time <= current_time and
                       active_refreshes < self.max_concurrent_refreshes):
                    
                    task = heapq.heappop(self.refresh_queue)
                    
                    # Submit refresh task
                    future = self.executor.submit(self._execute_refresh, task)
                    active_refreshes += 1
                    
                    # Decrement counter when done
                    def on_complete(fut):
                        nonlocal active_refreshes
                        active_refreshes -= 1
                        try:
                            fut.result()  # Re-raise any exceptions
                        except Exception as e:
                            logger.error(f"Background refresh failed: {e}")
                    
                    future.add_done_callback(on_complete)
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
                time.sleep(self.check_interval)
    
    def _execute_refresh(self, task: RefreshTask) -> None:
        """Execute background refresh task."""
        try:
            logger.debug(f"Executing background refresh for {task.key}")
            
            # Compute new value
            start_time = time.time()
            result = task.compute_fn()
            compute_time = time.time() - start_time
            
            # Update cache
            cache_manager = get_cache_manager()
            cache_manager.set(
                key=task.key,
                value=result,
                cache_tiers=task.cache_tiers,
                ttl=task.ttl,
                dependencies=task.dependencies
            )
            
            logger.debug(f"Background refresh completed for {task.key} in {compute_time:.2f}s")
            
        except Exception as e:
            logger.warning(f"Background refresh failed for {task.key}: {e}")
            
            # Retry if under limit
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.scheduled_time = datetime.now() + timedelta(minutes=5)  # Retry in 5 minutes
                heapq.heappush(self.refresh_queue, task)
                logger.debug(f"Scheduled retry {task.retry_count}/{task.max_retries} for {task.key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get refresh monitor statistics."""
        with self._lock:
            return {
                'total_keys_monitored': len(self.access_counts),
                'access_counts': dict(self.access_counts.most_common(10)),
                'pending_refreshes': len(self.refresh_queue),
                'next_refresh': self.refresh_queue[0].scheduled_time.isoformat() if self.refresh_queue else None,
                'running': self.running
            }


# Global refresh monitor instance
_refresh_monitor: Optional[CacheRefreshMonitor] = None


def get_refresh_monitor() -> CacheRefreshMonitor:
    """Get global refresh monitor instance."""
    global _refresh_monitor
    if _refresh_monitor is None:
        _refresh_monitor = CacheRefreshMonitor()
    return _refresh_monitor


def cached_analytics_call(key: str, compute_fn: Callable[[], Any], 
                         cache_tiers: List[str] = None,
                         ttl: Optional[int] = None,
                         dependencies: List[str] = None,
                         enable_refresh: bool = True) -> Any:
    """Enhanced cache call with background refresh monitoring."""
    
    cache_manager = get_cache_manager()
    
    # Record access for refresh monitoring
    if enable_refresh:
        refresh_monitor = get_refresh_monitor()
        refresh_monitor.record_access(key, compute_fn, cache_tiers, ttl, dependencies)
    
    # Get from cache or compute
    return cache_manager.get(
        key=key,
        compute_fn=compute_fn,
        cache_tiers=cache_tiers,
        ttl=ttl,
        dependencies=dependencies
    )


class CacheWarmupManager:
    """Manages cache warming on application startup."""
    
    def __init__(self):
        self.warmup_tasks: List[Tuple[str, Callable, Dict]] = []
    
    def register_warmup_task(self, key: str, compute_fn: Callable, 
                           cache_config: Dict = None) -> None:
        """Register a task for cache warming."""
        config = cache_config or {}
        self.warmup_tasks.append((key, compute_fn, config))
    
    def warmup_cache(self, max_workers: int = 4, timeout: int = 30) -> Dict[str, bool]:
        """Warm up cache with registered tasks."""
        results = {}
        
        if not self.warmup_tasks:
            logger.info("No cache warmup tasks registered")
            return results
        
        logger.info(f"Starting cache warmup with {len(self.warmup_tasks)} tasks")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {}
            for key, compute_fn, config in self.warmup_tasks:
                future = executor.submit(self._warmup_task, key, compute_fn, config)
                future_to_key[future] = key
            
            # Wait for completion
            for future in as_completed(future_to_key, timeout=timeout):
                key = future_to_key[future]
                try:
                    future.result()
                    results[key] = True
                    logger.debug(f"Cache warmup completed for {key}")
                except Exception as e:
                    results[key] = False
                    logger.warning(f"Cache warmup failed for {key}: {e}")
        
        success_count = sum(results.values())
        logger.info(f"Cache warmup completed: {success_count}/{len(results)} successful")
        
        return results
    
    def _warmup_task(self, key: str, compute_fn: Callable, config: Dict) -> None:
        """Execute single cache warmup task."""
        try:
            result = compute_fn()
            
            cache_manager = get_cache_manager()
            cache_manager.set(
                key=key,
                value=result,
                cache_tiers=config.get('cache_tiers', ['l1', 'l2', 'l3']),
                ttl=config.get('ttl'),
                dependencies=config.get('dependencies', [])
            )
            
        except Exception as e:
            logger.error(f"Warmup task failed for {key}: {e}")
            raise


# Global warmup manager instance
_warmup_manager: Optional[CacheWarmupManager] = None


def get_warmup_manager() -> CacheWarmupManager:
    """Get global warmup manager instance."""
    global _warmup_manager
    if _warmup_manager is None:
        _warmup_manager = CacheWarmupManager()
    return _warmup_manager


# Convenience decorator for caching analytics functions
def analytics_cache(cache_tiers: List[str] = None, 
                   ttl: Optional[int] = None,
                   dependencies: List[str] = None,
                   enable_refresh: bool = True):
    """Decorator for caching analytics functions."""
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            from .cache_manager import cache_key
            key = f"{func.__name__}|{cache_key(*args, **kwargs)}"
            
            # Create compute function
            def compute_fn():
                return func(*args, **kwargs)
            
            return cached_analytics_call(
                key=key,
                compute_fn=compute_fn,
                cache_tiers=cache_tiers,
                ttl=ttl,
                dependencies=dependencies,
                enable_refresh=enable_refresh
            )
        
        return wrapper
    return decorator


def identify_months_for_cache_population(db_manager, months_back: int = 12) -> List[Dict[str, Any]]:
    """Identify months that need cache population based on available health records.
    
    This function queries the health_records table to find all unique type and month
    combinations that have data within the specified time period. It returns results
    sorted by year descending, month descending, and type alphabetically.
    
    Args:
        db_manager: Database manager instance for executing queries.
        months_back: Number of months to look back from current date. Defaults to 12.
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing:
            - type: Health metric type (e.g., "StepCount", "HeartRate")
            - year: Year as string (e.g., "2024")
            - month: Month as string (e.g., "01", "12")
            - record_count: Number of records for this type/month combination
            
    Example:
        >>> months = identify_months_for_cache_population(db_manager)
        >>> for month_data in months:
        ...     print(f"{month_data['type']} - {month_data['year']}/{month_data['month']}: "
        ...           f"{month_data['record_count']} records")
    """
    query = """
    -- Identify months that need cache population
    SELECT DISTINCT 
        type,
        strftime('%Y', startDate) as year,
        strftime('%m', startDate) as month,
        COUNT(*) as record_count
    FROM health_records 
    WHERE DATE(startDate) >= DATE('now', '-' || ? || ' months')
    GROUP BY type, strftime('%Y', startDate), strftime('%m', startDate)
    HAVING record_count > 0
    ORDER BY year DESC, month DESC, type;
    """
    
    try:
        results = db_manager.execute_query(query, (months_back,))
        
        # Convert to list of dictionaries for easier processing
        months_data = []
        for row in results:
            months_data.append({
                'type': row[0],
                'year': row[1],
                'month': row[2],
                'record_count': row[3]
            })
        
        logger.info(f"Identified {len(months_data)} type/month combinations for cache population")
        return months_data
        
    except Exception as e:
        logger.error(f"Error identifying months for cache population: {e}")
        return []


def warm_monthly_metrics_cache(cached_monthly_calculator, db_manager, months_back: int = 12) -> Dict[str, bool]:
    """Warm the cache for monthly metrics based on available data.
    
    This function identifies all months with data in the specified time period and
    pre-populates the cache with monthly statistics for each metric type.
    
    Args:
        cached_monthly_calculator: Instance of CachedMonthlyMetricsCalculator.
        db_manager: Database manager instance for querying available data.
        months_back: Number of months to look back from current date. Defaults to 12.
        
    Returns:
        Dict[str, bool]: Dictionary mapping cache keys to success status.
        
    Example:
        >>> from .cached_calculators import create_cached_monthly_calculator
        >>> calculator = create_cached_monthly_calculator()
        >>> results = warm_monthly_metrics_cache(calculator, db_manager)
        >>> success_count = sum(results.values())
        >>> print(f"Successfully cached {success_count}/{len(results)} monthly metrics")
    """
    months_to_cache = identify_months_for_cache_population(db_manager, months_back)
    results = {}
    
    if not months_to_cache:
        logger.warning("No months identified for cache population")
        return results
    
    logger.info(f"Starting monthly metrics cache warmup for {len(months_to_cache)} type/month combinations")
    
    # Group by month for efficient batch processing
    months_by_period = defaultdict(list)
    for month_data in months_to_cache:
        key = (int(month_data['year']), int(month_data['month']))
        months_by_period[key].append(month_data['type'])
    
    # Process each month
    for (year, month), metrics in months_by_period.items():
        for metric in metrics:
            cache_key = f"monthly_stats|{metric}|{year}|{month}"
            try:
                # Calculate and cache the monthly statistics
                _ = cached_monthly_calculator.calculate_monthly_stats(metric, year, month)
                results[cache_key] = True
                logger.debug(f"Successfully cached monthly stats for {metric} {year}/{month:02d}")
            except Exception as e:
                results[cache_key] = False
                logger.warning(f"Failed to cache monthly stats for {metric} {year}/{month:02d}: {e}")
    
    success_count = sum(results.values())
    logger.info(f"Monthly cache warmup completed: {success_count}/{len(results)} successful")
    
    return results