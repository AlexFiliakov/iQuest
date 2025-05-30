"""
Weekly metrics calculator for health data analysis.
Provides 7-day rolling statistics with configurable windows, trend detection,
and advanced analytics including week-to-date comparisons and volatility scores.
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from collections import deque
import logging
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics


logger = logging.getLogger(__name__)


class WeekStandard:
    """Week numbering standards."""
    ISO = "ISO"  # Monday as first day, week 1 contains first Thursday
    US = "US"    # Sunday as first day, week 1 contains January 1


@dataclass
class TrendInfo:
    """Container for trend analysis results."""
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    trend_direction: str  # 'up', 'down', or 'stable'
    confidence_level: float
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if trend is statistically significant."""
        return self.p_value < alpha


@dataclass
class WeekComparison:
    """Container for week-to-date comparison results."""
    current_week_avg: float
    previous_week_avg: float
    percent_change: float
    absolute_change: float
    current_week_days: int
    previous_week_days: int
    is_partial_week: bool


@dataclass
class WeeklyMetrics:
    """Container for weekly metrics matching API specification."""
    week_start: datetime
    daily_values: Dict[datetime, float]
    trend_direction: str  # 'up', 'down', 'stable'
    avg: float
    min: float
    max: float


class WeeklyMetricsCalculator:
    """
    Calculator for weekly health metrics with advanced analytics.
    
    Provides rolling statistics, trend detection, volatility analysis,
    and week-to-date comparisons with performance optimizations.
    """
    
    def __init__(self, daily_calculator: DailyMetricsCalculator, 
                 week_standard: WeekStandard = WeekStandard.ISO,
                 use_parallel: bool = True):
        """
        Initialize the weekly calculator.
        
        Args:
            daily_calculator: Instance of DailyMetricsCalculator for base calculations
            week_standard: Week numbering standard (ISO or US)
            use_parallel: Whether to use parallel processing for multiple metrics
        """
        self.daily_calculator = daily_calculator
        self.week_standard = week_standard
        self.use_parallel = use_parallel
        self.window_cache = {}
        self._max_workers = multiprocessing.cpu_count() - 1
        
    def calculate_rolling_stats(self, 
                              metric: str, 
                              window: int = 7,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Calculate rolling statistics with configurable window.
        
        Args:
            metric: The metric type to analyze
            window: Rolling window size in days (default: 7)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            DataFrame with rolling statistics (mean, std, min, max)
        """
        # Check cache first
        cache_key = f"{metric}_{window}_{start_date}_{end_date}"
        if cache_key in self.window_cache:
            return self.window_cache[cache_key]
        
        # Get daily aggregates from daily calculator
        daily_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', start_date, end_date
        )
        
        if daily_data.empty:
            return pd.DataFrame()
        
        # Create complete date range to handle missing days
        date_range = pd.date_range(
            start=daily_data.index.min(), 
            end=daily_data.index.max(), 
            freq='D'
        )
        
        # Reindex to include all dates
        complete_series = daily_data.reindex(date_range)
        
        # Calculate rolling statistics efficiently
        rolling = complete_series.rolling(window=window, min_periods=1)
        
        stats_df = pd.DataFrame({
            'date': complete_series.index,
            'value': complete_series.values,
            'rolling_mean': rolling.mean().values,
            'rolling_std': rolling.std().values,
            'rolling_min': rolling.min().values,
            'rolling_max': rolling.max().values,
            'rolling_median': rolling.median().values
        })
        
        # Add additional statistics
        stats_df['rolling_cv'] = stats_df['rolling_std'] / stats_df['rolling_mean']  # Coefficient of variation
        
        # Cache results for performance
        cache_key = f"{metric}_{window}_{start_date}_{end_date}"
        self.window_cache[cache_key] = stats_df
        
        return stats_df
    
    def compare_week_to_date(self, 
                           metric: str, 
                           current_week: int, 
                           year: int) -> WeekComparison:
        """
        Compare current week-to-date with previous week.
        
        Args:
            metric: The metric type to analyze
            current_week: Week number to compare (1-53)
            year: Year of the week
            
        Returns:
            WeekComparison object with comparison results
        """
        # Get week dates based on standard
        current_start, current_end = self._get_week_dates(year, current_week)
        
        # Get previous week dates
        if current_week == 1:
            # Handle year boundary
            prev_year = year - 1
            prev_week = self._get_weeks_in_year(prev_year)
        else:
            prev_year = year
            prev_week = current_week - 1
        
        prev_start, prev_end = self._get_week_dates(prev_year, prev_week)
        
        # Get today's date to determine if current week is partial
        today = date.today()
        is_partial = today < current_end
        
        if is_partial:
            # Adjust current week end to today
            current_end = today
            # Adjust previous week to same day count
            days_elapsed = (current_end - current_start).days + 1
            prev_end = prev_start + timedelta(days=days_elapsed - 1)
        
        # Get daily data for both weeks
        current_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', current_start, current_end
        )
        
        prev_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', prev_start, prev_end
        )
        
        # Calculate averages
        current_avg = current_data.mean() if not current_data.empty else 0
        prev_avg = prev_data.mean() if not prev_data.empty else 0
        
        # Calculate changes
        if prev_avg != 0:
            percent_change = ((current_avg - prev_avg) / prev_avg) * 100
        else:
            percent_change = 0 if current_avg == 0 else float('inf')
        
        absolute_change = current_avg - prev_avg
        
        return WeekComparison(
            current_week_avg=float(current_avg),
            previous_week_avg=float(prev_avg),
            percent_change=float(percent_change),
            absolute_change=float(absolute_change),
            current_week_days=len(current_data),
            previous_week_days=len(prev_data),
            is_partial_week=is_partial
        )
    
    def calculate_moving_averages(self,
                                metric: str,
                                windows: List[int] = [7, 14, 28],
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Calculate multiple moving averages for a metric.
        
        Args:
            metric: The metric type to analyze
            windows: List of window sizes (default: [7, 14, 28])
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            DataFrame with moving averages for each window
        """
        # Get daily data
        daily_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', start_date, end_date
        )
        
        if daily_data.empty:
            return pd.DataFrame()
        
        # Create complete date range
        date_range = pd.date_range(
            start=daily_data.index.min(), 
            end=daily_data.index.max(), 
            freq='D'
        )
        
        # Reindex to include all dates
        complete_series = daily_data.reindex(date_range)
        
        # Initialize result DataFrame
        result = pd.DataFrame({
            'date': complete_series.index,
            'value': complete_series.values
        })
        
        # Calculate moving averages for each window
        for window in windows:
            result[f'ma_{window}'] = complete_series.rolling(
                window=window, 
                min_periods=1
            ).mean()
        
        # Add exponential moving averages
        for window in windows:
            result[f'ema_{window}'] = complete_series.ewm(
                span=window, 
                adjust=False
            ).mean()
        
        return result
    
    def detect_trend(self, 
                    metric: str, 
                    window: int = 7,
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None) -> TrendInfo:
        """
        Detect trend using linear regression.
        
        Args:
            metric: The metric type to analyze
            window: Window size for trend analysis
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            TrendInfo object with trend analysis results
        """
        # Get rolling statistics
        rolling_stats = self.calculate_rolling_stats(metric, window, start_date, end_date)
        
        if rolling_stats.empty or len(rolling_stats) < window:
            raise ValueError(f"Insufficient data for trend analysis (need at least {window} days)")
        
        # Use rolling mean for trend detection
        y_values = rolling_stats['rolling_mean'].dropna().values
        x_values = np.arange(len(y_values))
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
        
        # Determine trend direction
        if p_value < 0.05:  # Statistically significant
            if slope > 0:
                trend_direction = "up"
            elif slope < 0:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"  # Not statistically significant
        
        # Calculate confidence level
        confidence_level = 1 - p_value
        
        return TrendInfo(
            slope=float(slope),
            intercept=float(intercept),
            r_squared=float(r_value ** 2),
            p_value=float(p_value),
            trend_direction=trend_direction,
            confidence_level=float(confidence_level)
        )
    
    def calculate_volatility(self, 
                           metric: str, 
                           window: int = 7,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> Dict[str, float]:
        """
        Calculate volatility/consistency scores.
        
        Args:
            metric: The metric type to analyze
            window: Window size for volatility calculation
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with volatility metrics
        """
        # Get rolling statistics
        rolling_stats = self.calculate_rolling_stats(metric, window, start_date, end_date)
        
        if rolling_stats.empty:
            return {
                'volatility_score': None,
                'consistency_score': None,
                'coefficient_of_variation': None,
                'range_ratio': None
            }
        
        # Calculate various volatility measures
        values = rolling_stats['value'].dropna()
        
        # Standard deviation as volatility
        volatility = values.std()
        
        # Coefficient of variation (normalized volatility)
        mean_value = values.mean()
        cv = volatility / mean_value if mean_value != 0 else float('inf')
        
        # Range ratio (max-min)/mean
        value_range = values.max() - values.min()
        range_ratio = value_range / mean_value if mean_value != 0 else float('inf')
        
        # Consistency score (inverse of CV, bounded 0-1)
        consistency = 1 / (1 + cv) if cv != float('inf') else 0
        
        # Calculate rolling volatility
        rolling_vol = rolling_stats['rolling_std'].mean()
        
        return {
            'volatility_score': float(volatility),
            'consistency_score': float(consistency),
            'coefficient_of_variation': float(cv),
            'range_ratio': float(range_ratio),
            'rolling_volatility': float(rolling_vol)
        }
    
    def calculate_multiple_metrics_parallel(self,
                                          metrics: List[str],
                                          window: int = 7,
                                          start_date: Optional[date] = None,
                                          end_date: Optional[date] = None) -> Dict[str, pd.DataFrame]:
        """
        Calculate rolling statistics for multiple metrics in parallel.
        
        Args:
            metrics: List of metric types to analyze
            window: Rolling window size
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary mapping metric names to DataFrames
        """
        if not self.use_parallel or len(metrics) < 3:
            # Use sequential processing for small number of metrics
            results = {}
            for metric in metrics:
                try:
                    results[metric] = self.calculate_rolling_stats(
                        metric, window, start_date, end_date
                    )
                except Exception as e:
                    logger.error(f"Error processing {metric}: {e}")
                    results[metric] = pd.DataFrame()
            return results
        
        # Use parallel processing
        results = {}
        with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit tasks
            future_to_metric = {
                executor.submit(
                    self.calculate_rolling_stats, 
                    metric, window, start_date, end_date
                ): metric 
                for metric in metrics
            }
            
            # Collect results
            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                try:
                    results[metric] = future.result()
                except Exception as e:
                    logger.error(f"Error processing {metric}: {e}")
                    results[metric] = pd.DataFrame()
        
        return results
    
    def _get_week_dates(self, year: int, week: int) -> Tuple[date, date]:
        """Get start and end dates for a specific week."""
        if self.week_standard == WeekStandard.ISO:
            # ISO week date
            jan4 = date(year, 1, 4)
            week1_start = jan4 - timedelta(days=jan4.weekday())  # Monday of week 1
            week_start = week1_start + timedelta(weeks=week - 1)
            week_end = week_start + timedelta(days=6)
        else:
            # US week (Sunday as first day)
            jan1 = date(year, 1, 1)
            # Calculate days back to previous Sunday
            days_to_sunday = jan1.weekday() + 1 if jan1.weekday() != 6 else 0
            week1_start = jan1 - timedelta(days=days_to_sunday)
            week_start = week1_start + timedelta(weeks=week - 1)
            week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    def _get_weeks_in_year(self, year: int) -> int:
        """Get number of weeks in a year (52 or 53)."""
        if self.week_standard == WeekStandard.ISO:
            # Check if year has 53 ISO weeks
            dec28 = date(year, 12, 28)
            return dec28.isocalendar()[1]
        else:
            # US standard - check if Dec 31 starts a new week
            dec31 = date(year, 12, 31)
            jan1 = date(year, 1, 1)
            
            # Count Sundays in the year
            sundays = 0
            current = jan1
            while current.year == year:
                if current.weekday() == 6:  # Sunday
                    sundays += 1
                current += timedelta(days=1)
            
            return sundays
    
    def get_weekly_summary(self,
                         metrics: List[str],
                         week: int,
                         year: int) -> Dict[str, Dict[str, float]]:
        """
        Get comprehensive weekly summary for multiple metrics.
        
        Args:
            metrics: List of metric types
            week: Week number
            year: Year
            
        Returns:
            Dictionary with summary statistics for each metric
        """
        week_start, week_end = self._get_week_dates(year, week)
        results = {}
        
        for metric in metrics:
            try:
                # Get basic statistics
                stats = self.daily_calculator.calculate_statistics(
                    metric, week_start, week_end
                )
                
                # Get volatility
                volatility = self.calculate_volatility(
                    metric, 7, week_start, week_end
                )
                
                # Combine results
                results[metric] = {
                    'mean': stats.mean,
                    'median': stats.median,
                    'std': stats.std,
                    'min': stats.min,
                    'max': stats.max,
                    'consistency_score': volatility['consistency_score'],
                    'coefficient_of_variation': volatility['coefficient_of_variation']
                }
            except Exception as e:
                logger.error(f"Error calculating weekly summary for {metric}: {e}")
                results[metric] = {}
        
        return results
    
    def calculate_weekly_metrics(self,
                               data: pd.DataFrame,
                               metric_type: str,
                               week_start: datetime) -> WeeklyMetrics:
        """
        Calculate metrics for a week matching API specification.
        
        Args:
            data: DataFrame with health data
            metric_type: Type of metric to calculate
            week_start: Start date of the week
            
        Returns:
            WeeklyMetrics: avg, min, max, daily_values, trend
        """
        # Calculate week end
        week_end = week_start + timedelta(days=6)
        
        # Filter data for the specific metric and week
        # Convert datetime objects to pandas datetime for proper comparison
        week_start_pd = pd.Timestamp(week_start)
        week_end_pd = pd.Timestamp(week_end)
        
        # Ensure creationDate is in datetime format
        if 'creationDate' in data.columns:
            data['creationDate'] = pd.to_datetime(data['creationDate'])
        
        mask = (data['type'] == metric_type) & \
               (data['creationDate'] >= week_start_pd) & \
               (data['creationDate'] <= week_end_pd)
        week_data = data[mask].copy()
        
        # Group by date and calculate daily values
        if not week_data.empty:
            week_data['date'] = pd.to_datetime(week_data['creationDate']).dt.date
            daily_aggs = week_data.groupby('date')['value'].mean()
            
            # Create complete date range for the week
            date_range = pd.date_range(start=week_start.date(), end=week_end.date(), freq='D')
            daily_values = {}
            
            for date in date_range:
                date_key = date.date()
                if date_key in daily_aggs.index:
                    daily_values[datetime.combine(date_key, datetime.min.time())] = float(daily_aggs[date_key])
                else:
                    daily_values[datetime.combine(date_key, datetime.min.time())] = 0.0
            
            # Calculate statistics
            values = list(daily_values.values())
            non_zero_values = [v for v in values if v > 0]
            
            if non_zero_values:
                avg = float(np.mean(non_zero_values))
                min_val = float(np.min(non_zero_values))
                max_val = float(np.max(non_zero_values))
                
                # Determine trend by comparing first half to second half
                mid_point = len(values) // 2
                first_half = np.mean(values[:mid_point]) if values[:mid_point] else 0
                second_half = np.mean(values[mid_point:]) if values[mid_point:] else 0
                
                if second_half > first_half * 1.05:
                    trend_direction = 'up'
                elif second_half < first_half * 0.95:
                    trend_direction = 'down'
                else:
                    trend_direction = 'stable'
            else:
                avg = min_val = max_val = 0.0
                trend_direction = 'stable'
        else:
            # No data for this week
            daily_values = {
                datetime.combine((week_start + timedelta(days=i)).date(), datetime.min.time()): 0.0
                for i in range(7)
            }
            avg = min_val = max_val = 0.0
            trend_direction = 'stable'
        
        return WeeklyMetrics(
            week_start=week_start,
            daily_values=daily_values,
            trend_direction=trend_direction,
            avg=avg,
            min=min_val,
            max=max_val
        )