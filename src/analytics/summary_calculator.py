"""Centralized summary calculator for pre-computing metrics during import.

This module provides a unified interface for calculating all metric summaries
(daily, weekly, monthly) during the data import process. It consolidates logic
from existing calculator modules and optimizes for batch processing.

Example:
    >>> calculator = SummaryCalculator(data_access)
    >>> summaries = calculator.calculate_all_summaries(
    ...     progress_callback=lambda p, m: print(f"{p}%: {m}")
    ... )
    >>> print(f"Calculated {len(summaries['daily'])} daily summaries")
    Calculated 365 daily summaries
"""

from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime, date, timedelta
import logging
import json
from dataclasses import asdict

from src.analytics.daily_metrics_calculator import MetricStatistics
from src.data_access import DataAccess
from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class SummaryCalculator:
    """Centralized calculator for all metric summaries during import.
    
    This class consolidates the calculation logic from daily, weekly, and monthly
    metrics calculators into a single, optimized interface for use during the
    import process. It supports batch processing and progress reporting.
    
    Attributes:
        data_access: DataAccess instance for database operations
        db_path: Path to the SQLite database
        _total_metrics: Total number of metrics to process
        _processed_metrics: Number of metrics processed so far
    """
    
    def __init__(self, data_access: DataAccess):
        """Initialize the summary calculator.
        
        Args:
            data_access: DataAccess instance for database operations
        """
        self.data_access = data_access
        # Get db_manager directly from DatabaseManager singleton
        self.db_manager = DatabaseManager()
        self.db_path = self.db_manager.db_path
        self._total_metrics = 0
        self._processed_metrics = 0
        
    def calculate_all_summaries(self, 
                              progress_callback: Optional[Callable[[float, str], None]] = None,
                              months_back: int = 12) -> Dict[str, Any]:
        """Calculate daily, weekly, and monthly summaries for all metrics.
        
        This method discovers all available metrics in the database and calculates
        summaries for each time period. It's optimized for batch processing during
        import.
        
        Args:
            progress_callback: Optional callback for progress updates.
                               Called with (percentage, message).
            months_back: Number of months of historical data to process.
                        Defaults to 12 months.
        
        Returns:
            Dict containing summaries organized by time period:
            {
                'daily': {metric: {date: stats}},
                'weekly': {metric: {week: stats}},
                'monthly': {metric: {month: stats}},
                'metadata': {
                    'import_timestamp': str,
                    'metrics_processed': int,
                    'date_range': {'start': str, 'end': str}
                }
            }
        
        Raises:
            Exception: If database operations fail
        """
        start_time = datetime.now()
        summaries = {
            'daily': {},
            'weekly': {},
            'monthly': {},
            'metadata': {
                'import_timestamp': start_time.isoformat(),
                'metrics_processed': 0,
                'date_range': {}
            }
        }
        
        try:
            # Step 1: Discover all metrics
            self._report_progress(0, "Discovering available metrics...", progress_callback)
            metrics = self._discover_metrics(months_back)
            self._total_metrics = len(metrics)
            
            if not metrics:
                logger.warning("No metrics found in database")
                return summaries
                
            # Determine date range
            end_date = date.today()
            start_date = end_date - timedelta(days=months_back * 30)
            summaries['metadata']['date_range'] = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
            
            # Step 2: Calculate summaries for each metric
            for metric_type in metrics:
                metric_progress = (self._processed_metrics / self._total_metrics) * 100
                self._report_progress(
                    metric_progress, 
                    f"Processing {metric_type}...", 
                    progress_callback
                )
                
                # Calculate daily summaries
                daily_stats = self._calculate_daily_summaries(
                    metric_type, start_date, end_date
                )
                if daily_stats:
                    summaries['daily'][metric_type] = daily_stats
                
                # Calculate weekly summaries
                weekly_stats = self._calculate_weekly_summaries(
                    metric_type, start_date, end_date
                )
                if weekly_stats:
                    summaries['weekly'][metric_type] = weekly_stats
                
                # Calculate monthly summaries
                monthly_stats = self._calculate_monthly_summaries(
                    metric_type, start_date, end_date
                )
                if monthly_stats:
                    summaries['monthly'][metric_type] = monthly_stats
                
                self._processed_metrics += 1
                
            # Step 3: Finalize metadata
            summaries['metadata']['metrics_processed'] = self._processed_metrics
            summaries['metadata']['processing_time'] = (
                datetime.now() - start_time
            ).total_seconds()
            
            self._report_progress(100, "Summary calculation complete!", progress_callback)
            
            logger.info(
                f"Calculated summaries for {self._processed_metrics} metrics "
                f"in {summaries['metadata']['processing_time']:.2f} seconds"
            )
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error calculating summaries: {e}")
            raise
            
    def _discover_metrics(self, months_back: int) -> List[str]:
        """Discover all metric types with data in the specified time range.
        
        Args:
            months_back: Number of months to look back
            
        Returns:
            List of metric type names
        """
        query = """
        SELECT DISTINCT type
        FROM health_records
        WHERE DATE(startDate) >= DATE('now', '-' || ? || ' months')
          AND value IS NOT NULL
        ORDER BY type
        """
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, (months_back,))
            return [row[0] for row in cursor.fetchall()]
            
    def _calculate_daily_summaries(self, 
                                 metric_type: str, 
                                 start_date: date,
                                 end_date: date) -> Dict[str, Dict[str, Any]]:
        """Calculate daily summaries for a specific metric.
        
        Args:
            metric_type: The metric type to calculate
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict mapping date strings to statistics
        """
        query = """
        WITH source_aggregates AS (
            SELECT 
                DATE(startDate) as date,
                sourceName,
                SUM(CAST(value AS FLOAT)) as source_sum,
                COUNT(*) as source_count
            FROM health_records
            WHERE type = ?
              AND DATE(startDate) BETWEEN ? AND ?
              AND value IS NOT NULL
            GROUP BY DATE(startDate), sourceName
        )
        SELECT 
            date,
            SUM(source_sum) as total_sum,
            AVG(source_sum) as avg_value,
            MAX(source_sum) as max_value,
            MIN(source_sum) as min_value,
            SUM(source_count) as total_count,
            COUNT(DISTINCT sourceName) as source_count
        FROM source_aggregates
        GROUP BY date
        ORDER BY date
        """
        
        summaries = {}
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query, 
                (metric_type, start_date.isoformat(), end_date.isoformat())
            )
            
            for row in cursor.fetchall():
                date_str = row[0]
                summaries[date_str] = {
                    'sum': row[1],
                    'avg': row[2],
                    'max': row[3],
                    'min': row[4],
                    'count': row[5],
                    'sources': row[6]
                }
                
        return summaries
        
    def _calculate_weekly_summaries(self,
                                  metric_type: str,
                                  start_date: date,
                                  end_date: date) -> Dict[str, Dict[str, Any]]:
        """Calculate weekly summaries for a specific metric.
        
        Args:
            metric_type: The metric type to calculate
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict mapping ISO week strings to statistics
        """
        query = """
        WITH daily_totals AS (
            SELECT 
                DATE(startDate) as date,
                SUM(CAST(value AS FLOAT)) as daily_sum
            FROM health_records
            WHERE type = ?
              AND DATE(startDate) BETWEEN ? AND ?
              AND value IS NOT NULL
            GROUP BY DATE(startDate)
        )
        SELECT 
            strftime('%Y-W%W', date) as week,
            SUM(daily_sum) as week_sum,
            AVG(daily_sum) as daily_avg,
            MAX(daily_sum) as daily_max,
            MIN(daily_sum) as daily_min,
            COUNT(*) as days_with_data
        FROM daily_totals
        GROUP BY strftime('%Y-W%W', date)
        ORDER BY week
        """
        
        summaries = {}
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query,
                (metric_type, start_date.isoformat(), end_date.isoformat())
            )
            
            for row in cursor.fetchall():
                week_str = row[0]
                summaries[week_str] = {
                    'sum': row[1],
                    'daily_avg': row[2],
                    'daily_max': row[3],
                    'daily_min': row[4],
                    'days_with_data': row[5]
                }
                
        return summaries
        
    def _calculate_monthly_summaries(self,
                                   metric_type: str,
                                   start_date: date,
                                   end_date: date) -> Dict[str, Dict[str, Any]]:
        """Calculate monthly summaries for a specific metric.
        
        Args:
            metric_type: The metric type to calculate
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict mapping month strings to statistics
        """
        query = """
        WITH daily_aggregates AS (
            SELECT 
                DATE(startDate) as date,
                strftime('%Y-%m', startDate) as month,
                SUM(CAST(value AS FLOAT)) as daily_total
            FROM health_records
            WHERE type = ?
              AND DATE(startDate) BETWEEN ? AND ?
              AND value IS NOT NULL
            GROUP BY DATE(startDate)
        )
        SELECT 
            month,
            SUM(daily_total) as month_total,
            AVG(daily_total) as daily_average,
            MAX(daily_total) as max_daily,
            MIN(daily_total) as min_daily,
            COUNT(*) as days_with_data,
            -- For standard deviation calculation
            AVG(daily_total * daily_total) - AVG(daily_total) * AVG(daily_total) as variance
        FROM daily_aggregates
        GROUP BY month
        ORDER BY month
        """
        
        summaries = {}
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                query,
                (metric_type, start_date.isoformat(), end_date.isoformat())
            )
            
            for row in cursor.fetchall():
                month_str = row[0]
                variance = row[6] if row[6] and row[6] > 0 else 0
                
                summaries[month_str] = {
                    'sum': row[1],
                    'daily_avg': row[2],
                    'daily_max': row[3],
                    'daily_min': row[4],
                    'days_with_data': row[5],
                    'std_dev': variance ** 0.5 if variance > 0 else 0
                }
                
        return summaries
        
    def _report_progress(self, 
                        percentage: float, 
                        message: str,
                        callback: Optional[Callable[[float, str], None]] = None):
        """Report progress to the callback if provided.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Progress message
            callback: Optional callback function
        """
        if callback:
            callback(percentage, message)
        logger.debug(f"Summary calculation progress: {percentage:.1f}% - {message}")