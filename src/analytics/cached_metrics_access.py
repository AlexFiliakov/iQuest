"""Access layer for cached metrics from the main database.

This module provides fast access to pre-computed metric summaries stored in the
cached_metrics table, eliminating the need for expensive recalculations during
dashboard rendering.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
from dataclasses import dataclass

from ..data_access import CacheDAO
from ..database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class MetricStatistics:
    """Simple statistics container for compatibility."""
    metric_name: str
    count: int
    mean: float
    median: float = None
    std: float = None
    min: float = None
    max: float = None
    percentile_25: float = None
    percentile_75: float = None
    percentile_95: float = None


class CachedMetricsAccess:
    """Fast access to cached metric summaries from the main database.
    
    This class provides methods to retrieve pre-computed summaries that were
    cached during the import process, enabling instant dashboard loading.
    """
    
    def __init__(self):
        """Initialize the cached metrics access layer."""
        self.db = DatabaseManager()
    
    def convert_to_metric_statistics(self, summary: Dict[str, Any]) -> Optional[MetricStatistics]:
        """Convert a cached summary to MetricStatistics format.
        
        Args:
            summary: Dictionary containing summary statistics
            
        Returns:
            MetricStatistics object or None if conversion fails
        """
        if not summary:
            return None
            
        try:
            return MetricStatistics(
                metric_name=summary.get('metric', ''),
                count=summary.get('count', 0),
                mean=summary.get('mean', summary.get('avg', 0)),
                median=summary.get('median'),
                std=summary.get('std'),
                min=summary.get('min'),
                max=summary.get('max'),
                percentile_25=summary.get('percentile_25'),
                percentile_75=summary.get('percentile_75'),
                percentile_95=summary.get('percentile_95')
            )
        except Exception as e:
            logger.error(f"Error converting summary to MetricStatistics: {e}")
            return None
    
    def get_available_metrics(self) -> List[str]:
        """Get list of all available metrics in the cache.
        
        Returns:
            List of metric names
        """
        return self.get_all_cached_metrics()
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources from cached metrics.
        
        Returns:
            List of source names (e.g., ['iPhone', 'Apple Watch'])
        """
        try:
            query = """
                SELECT DISTINCT source_name 
                FROM cached_metrics 
                WHERE source_name IS NOT NULL
                ORDER BY source_name
            """
            
            with self.db.get_connection() as conn:
                cursor = conn.execute(query)
                sources = [row[0] for row in cursor.fetchall()]
                
            logger.info(f"Found {len(sources)} sources in cached metrics")
            return sources
            
        except Exception as e:
            logger.error(f"Error getting available sources: {e}")
            return []
        
    def get_daily_summary(self, metric: str, target_date: date, source_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached daily summary for a metric.
        
        Args:
            metric: The metric name (e.g., 'HKQuantityTypeIdentifierStepCount')
            target_date: The date to get summary for
            source_name: Optional source name to filter by (e.g., 'iPhone', 'Apple Watch')
            
        Returns:
            Dictionary containing the summary statistics or None if not cached
        """
        try:
            # For source-specific queries, use the metric type directly
            # For aggregated queries, use 'daily_summary' for backward compatibility
            metric_type = metric if source_name else 'daily_summary'
            
            cached_data = CacheDAO.get_cached_metrics(
                metric_type=metric_type,
                date_start=target_date,
                date_end=target_date,
                aggregation_type='daily',
                source_name=source_name,
                health_type=metric
            )
            
            if cached_data and isinstance(cached_data, dict):
                # Extract the stats from the cached data
                stats = cached_data.get('stats', {})
                return stats
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving daily summary for {metric} on {target_date}: {e}")
            return None
    
    def get_weekly_summary(self, metric: str, week_str: str) -> Optional[Dict[str, Any]]:
        """Get cached weekly summary for a metric.
        
        Args:
            metric: The metric name
            week_str: Week identifier in format "2024-W01"
            
        Returns:
            Dictionary containing the summary statistics or None if not cached
        """
        try:
            # Parse week to get date range
            year, week = week_str.split('-W')
            year = int(year)
            week = int(week)
            
            # Calculate week start and end dates
            jan1 = datetime(year, 1, 1).date()
            week_start = jan1 + timedelta(days=(week - 1) * 7 - jan1.weekday())
            week_end = week_start + timedelta(days=6)
            
            cached_data = CacheDAO.get_cached_metrics(
                metric_type='weekly_summary',
                date_start=week_start,
                date_end=week_end,
                aggregation_type='weekly',
                health_type=metric
            )
            
            if cached_data and isinstance(cached_data, dict):
                stats = cached_data.get('stats', {})
                return stats
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving weekly summary for {metric} on {week_str}: {e}")
            return None
    
    def get_monthly_summary(self, metric: str, month_str: str) -> Optional[Dict[str, Any]]:
        """Get cached monthly summary for a metric.
        
        Args:
            metric: The metric name
            month_str: Month identifier in format "2024-01"
            
        Returns:
            Dictionary containing the summary statistics or None if not cached
        """
        try:
            # Parse month to get date range
            year, month = map(int, month_str.split('-'))
            
            # Calculate month start and end dates
            month_start = datetime(year, month, 1).date()
            if month == 12:
                month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            cached_data = CacheDAO.get_cached_metrics(
                metric_type='monthly_summary',
                date_start=month_start,
                date_end=month_end,
                aggregation_type='monthly',
                health_type=metric
            )
            
            if cached_data and isinstance(cached_data, dict):
                stats = cached_data.get('stats', {})
                return stats
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving monthly summary for {metric} on {month_str}: {e}")
            return None
    
    def get_date_range_summaries(self, metric: str, start_date: date, end_date: date, 
                                aggregation: str = 'daily') -> Dict[str, Dict[str, Any]]:
        """Get all cached summaries for a date range.
        
        Args:
            metric: The metric name
            start_date: Start of date range
            end_date: End of date range
            aggregation: Type of aggregation ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary mapping date/week/month strings to summary statistics
        """
        results = {}
        
        try:
            if aggregation == 'daily':
                current_date = start_date
                while current_date <= end_date:
                    summary = self.get_daily_summary(metric, current_date)
                    if summary:
                        results[current_date.isoformat()] = summary
                    current_date += timedelta(days=1)
                    
            elif aggregation == 'weekly':
                # Get all weeks in range
                current_date = start_date
                while current_date <= end_date:
                    week_str = current_date.strftime('%Y-W%U')
                    if week_str not in results:
                        summary = self.get_weekly_summary(metric, week_str)
                        if summary:
                            results[week_str] = summary
                    current_date += timedelta(days=7)
                    
            elif aggregation == 'monthly':
                # Get all months in range
                current_month = start_date.replace(day=1)
                end_month = end_date.replace(day=1)
                
                while current_month <= end_month:
                    month_str = current_month.strftime('%Y-%m')
                    summary = self.get_monthly_summary(metric, month_str)
                    if summary:
                        results[month_str] = summary
                    
                    # Move to next month
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
            
        except Exception as e:
            logger.error(f"Error retrieving {aggregation} summaries for {metric}: {e}")
        
        return results
    
    def get_all_cached_metrics(self) -> List[str]:
        """Get list of all metrics that have cached data.
        
        Returns:
            List of metric names with cached data
        """
        try:
            query = """
                SELECT DISTINCT health_type 
                FROM cached_metrics 
                WHERE health_type IS NOT NULL
                AND expires_at > datetime('now')
                ORDER BY health_type
            """
            
            results = self.db.execute_query(query)
            return [row['health_type'] for row in results]
            
        except Exception as e:
            logger.error(f"Error retrieving cached metric list: {e}")
            return []
    
    def clear_expired_cache(self) -> int:
        """Clear expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        return CacheDAO.clean_expired_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats_query = """
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT health_type) as unique_metrics,
                    COUNT(DISTINCT aggregation_type) as aggregation_types,
                    MIN(date_range_start) as earliest_date,
                    MAX(date_range_end) as latest_date,
                    SUM(CASE WHEN expires_at <= datetime('now') THEN 1 ELSE 0 END) as expired_entries
                FROM cached_metrics
            """
            
            results = self.db.execute_query(stats_query)
            if results:
                return dict(results[0])
            
            return {
                'total_entries': 0,
                'unique_metrics': 0,
                'aggregation_types': 0,
                'earliest_date': None,
                'latest_date': None,
                'expired_entries': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# Singleton instance
_cached_metrics_access = None


def get_cached_metrics_access() -> CachedMetricsAccess:
    """Get singleton instance of CachedMetricsAccess.
    
    Returns:
        CachedMetricsAccess instance
    """
    global _cached_metrics_access
    if _cached_metrics_access is None:
        _cached_metrics_access = CachedMetricsAccess()
    return _cached_metrics_access