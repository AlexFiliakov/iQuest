"""Cache-only data access layer for dashboard tabs.

This module provides a data access interface that reads exclusively from
pre-computed summaries cached during import. It implements the same interface
as DataAccess but returns data from cache instead of querying the database.

This approach eliminates post-import database queries and provides instant
data access for all dashboard tabs.

Example:
    >>> cached_access = CachedDataAccess()
    >>> stats = cached_access.get_daily_summary('StepCount', date(2024, 1, 15))
    >>> print(f"Steps: {stats['sum']}")
    Steps: 8542
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime

from src.analytics.cache_manager import get_cache_manager, cache_key
from src.models import MetricStatistics

logger = logging.getLogger(__name__)


class CachedDataAccess:
    """Data access layer that reads exclusively from cached summaries.
    
    This class provides the same interface as DataAccess but retrieves data
    from pre-computed summaries stored in the cache during import. It's designed
    for use by dashboard tabs to eliminate database queries.
    
    Attributes:
        cache_manager: The global cache manager instance
        _cache_misses: Counter for tracking cache misses (should be 0 normally)
    """
    
    def __init__(self):
        """Initialize the cached data access layer."""
        self.cache_manager = get_cache_manager()
        self._cache_misses = 0
        
    def get_daily_summary(self, metric: str, target_date: date) -> Optional[Dict[str, Any]]:
        """Get daily summary statistics from cache.
        
        Args:
            metric: The metric type (e.g., 'StepCount')
            target_date: The date to get statistics for
            
        Returns:
            Dict with summary statistics or None if not cached
        """
        key = cache_key('daily_summary', metric, target_date.isoformat())
        
        # Get from L2 cache (SQLite) directly since import stores there
        result = self.cache_manager.l2_cache.get(key)
        
        if result is None:
            self._cache_misses += 1
            logger.warning(
                f"Cache miss for daily summary: {metric} on {target_date}. "
                f"Total misses: {self._cache_misses}"
            )
            return None
            
        # Parse JSON result from cache
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cached daily summary: {e}")
            return None
            
    def get_weekly_summary(self, metric: str, week: str) -> Optional[Dict[str, Any]]:
        """Get weekly summary statistics from cache.
        
        Args:
            metric: The metric type (e.g., 'StepCount')
            week: ISO week string (e.g., '2024-W03')
            
        Returns:
            Dict with summary statistics or None if not cached
        """
        key = cache_key('weekly_summary', metric, week)
        
        result = self.cache_manager.l2_cache.get(key)
        
        if result is None:
            self._cache_misses += 1
            logger.warning(
                f"Cache miss for weekly summary: {metric} for {week}. "
                f"Total misses: {self._cache_misses}"
            )
            return None
            
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cached weekly summary: {e}")
            return None
            
    def get_monthly_summary(self, metric: str, month: str) -> Optional[Dict[str, Any]]:
        """Get monthly summary statistics from cache.
        
        Args:
            metric: The metric type (e.g., 'StepCount') 
            month: Month string (e.g., '2024-01')
            
        Returns:
            Dict with summary statistics or None if not cached
        """
        key = cache_key('monthly_summary', metric, month)
        
        result = self.cache_manager.l2_cache.get(key)
        
        if result is None:
            self._cache_misses += 1
            logger.warning(
                f"Cache miss for monthly summary: {metric} for {month}. "
                f"Total misses: {self._cache_misses}"
            )
            return None
            
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cached monthly summary: {e}")
            return None
            
    def get_available_metrics(self) -> List[str]:
        """Get list of available metrics from import metadata.
        
        Returns:
            List of metric type names available in cache
        """
        # Try to get from the most recent import metadata
        try:
            # Search for import metadata entries
            import sqlite3
            with sqlite3.connect(self.cache_manager.l2_cache.db_path) as conn:
                cursor = conn.execute("""
                    SELECT value FROM cache_entries 
                    WHERE key LIKE 'import_metadata|%'
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    metadata = json.loads(row[0])
                    # Extract metrics from the summaries
                    metrics = set()
                    
                    for period in ['daily', 'weekly', 'monthly']:
                        if period in metadata:
                            metrics.update(metadata[period].keys())
                            
                    return sorted(list(metrics))
                    
        except Exception as e:
            logger.error(f"Error getting available metrics from cache: {e}")
            
        # Fallback: scan cache entries for metric types
        try:
            metrics = set()
            import sqlite3
            with sqlite3.connect(self.cache_manager.l2_cache.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT 
                        SUBSTR(key, INSTR(key, '|') + 1, 
                               INSTR(SUBSTR(key, INSTR(key, '|') + 1), '|') - 1) as metric
                    FROM cache_entries
                    WHERE key LIKE '%_summary|%'
                """)
                
                for row in cursor:
                    if row[0]:
                        metrics.add(row[0])
                        
            return sorted(list(metrics))
            
        except Exception as e:
            logger.error(f"Error scanning cache for metrics: {e}")
            return []
            
    def get_date_range_for_metric(self, metric: str) -> Optional[Dict[str, date]]:
        """Get the date range available for a specific metric.
        
        Args:
            metric: The metric type to check
            
        Returns:
            Dict with 'start' and 'end' dates, or None if no data
        """
        try:
            # Query daily summaries to find date range
            import sqlite3
            with sqlite3.connect(self.cache_manager.l2_cache.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        MIN(SUBSTR(key, -10)) as start_date,
                        MAX(SUBSTR(key, -10)) as end_date
                    FROM cache_entries
                    WHERE key LIKE 'daily_summary|' || ? || '|%'
                """, (metric,))
                
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    return {
                        'start': date.fromisoformat(row[0]),
                        'end': date.fromisoformat(row[1])
                    }
                    
        except Exception as e:
            logger.error(f"Error getting date range for {metric}: {e}")
            
        return None
        
    def has_data_for_date(self, metric: str, target_date: date) -> bool:
        """Check if cached data exists for a specific metric and date.
        
        Args:
            metric: The metric type
            target_date: The date to check
            
        Returns:
            True if cached data exists
        """
        key = cache_key('daily_summary', metric, target_date.isoformat())
        return self.cache_manager.l2_cache.get(key) is not None
        
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get statistics about cache usage and performance.
        
        Returns:
            Dict with cache statistics including miss count
        """
        return {
            'cache_misses': self._cache_misses,
            'metrics': self.cache_manager.get_metrics().asdict()
        }
        
    def convert_to_metric_statistics(self, summary: Dict[str, Any]) -> Optional[MetricStatistics]:
        """Convert cached summary to MetricStatistics object.
        
        Args:
            summary: Cached summary dict
            
        Returns:
            MetricStatistics object or None
        """
        if not summary:
            return None
            
        try:
            return MetricStatistics(
                mean=summary.get('avg', summary.get('daily_avg', 0)),
                median=summary.get('median', summary.get('avg', 0)),  # Fallback to avg
                std_dev=summary.get('std_dev', 0),
                min_value=summary.get('min', summary.get('daily_min', 0)),
                max_value=summary.get('max', summary.get('daily_max', 0)),
                sum_value=summary.get('sum', 0),
                count=summary.get('count', summary.get('days_with_data', 0))
            )
        except Exception as e:
            logger.error(f"Error converting summary to MetricStatistics: {e}")
            return None