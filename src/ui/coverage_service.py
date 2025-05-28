"""
Service for calculating data coverage metrics from health data sources.
Provides analysis of data availability, gaps, and quality scores.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
from collections import defaultdict

from .data_availability_indicator import CoverageData, DateGap
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CoverageService:
    """Service for analyzing data coverage from health datasets."""
    
    def __init__(self):
        """Initialize the coverage service."""
        self.logger = logger
    
    def analyze_dataframe_coverage(self, 
                                 df: pd.DataFrame, 
                                 date_column: str = 'Date',
                                 value_columns: Optional[List[str]] = None,
                                 start_date: Optional[date] = None,
                                 end_date: Optional[date] = None) -> CoverageData:
        """
        Analyze coverage for a pandas DataFrame.
        
        Args:
            df: DataFrame containing health data
            date_column: Name of the date column
            value_columns: List of columns to analyze (if None, uses all numeric columns)
            start_date: Start of analysis period (if None, uses min date in data)
            end_date: End of analysis period (if None, uses max date in data)
        
        Returns:
            CoverageData object with coverage analysis
        """
        if df.empty:
            return self._create_empty_coverage_data()
        
        try:
            # Ensure date column is datetime
            df[date_column] = pd.to_datetime(df[date_column]).dt.date
            
            # Determine analysis period
            if start_date is None:
                start_date = df[date_column].min()
            if end_date is None:
                end_date = df[date_column].max()
            
            # Determine value columns
            if value_columns is None:
                value_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            # Create date range for analysis
            date_range = pd.date_range(start_date, end_date, freq='D').date
            total_days = len(date_range)
            
            # Group data by date and calculate quality scores
            daily_data = df.groupby(date_column)[value_columns].agg(['count', 'mean']).fillna(0)
            
            # Calculate quality scores and coverage metrics
            quality_scores = {}
            days_with_data = 0
            partial_days = 0
            
            for analysis_date in date_range:
                if analysis_date in daily_data.index:
                    # Calculate quality score based on data completeness
                    counts = daily_data.loc[analysis_date, (slice(None), 'count')]
                    total_possible = len(value_columns)
                    data_points = counts.sum()
                    
                    # Quality score: ratio of actual data points to expected
                    quality_score = min(1.0, data_points / (total_possible * 24))  # Assuming hourly data
                    quality_scores[datetime.combine(analysis_date, datetime.min.time())] = quality_score
                    
                    days_with_data += 1
                    
                    # Count partial days (< 90% data)
                    if quality_score < 0.9:
                        partial_days += 1
                else:
                    quality_scores[datetime.combine(analysis_date, datetime.min.time())] = 0.0
            
            # Calculate coverage percentage
            coverage_percentage = (days_with_data / total_days * 100) if total_days > 0 else 0.0
            
            # Find gaps in data
            gaps = self._find_gaps(date_range, set(daily_data.index))
            
            return CoverageData(
                percentage=coverage_percentage,
                total_days=total_days,
                days_with_data=days_with_data,
                partial_days=partial_days,
                quality_scores=quality_scores,
                gaps=gaps,
                date_range=(datetime.combine(start_date, datetime.min.time()),
                           datetime.combine(end_date, datetime.min.time()))
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing DataFrame coverage: {e}")
            return self._create_empty_coverage_data()
    
    def analyze_metric_coverage(self, 
                              metric_data: Dict[date, float],
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> CoverageData:
        """
        Analyze coverage for a simple metric dictionary.
        
        Args:
            metric_data: Dictionary mapping dates to metric values
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            CoverageData object with coverage analysis
        """
        if not metric_data:
            return self._create_empty_coverage_data()
        
        try:
            # Determine analysis period
            dates = list(metric_data.keys())
            if start_date is None:
                start_date = min(dates)
            if end_date is None:
                end_date = max(dates)
            
            # Create complete date range
            current_date = start_date
            total_days = 0
            days_with_data = 0
            partial_days = 0
            quality_scores = {}
            
            while current_date <= end_date:
                total_days += 1
                
                if current_date in metric_data:
                    value = metric_data[current_date]
                    
                    # Quality score based on data availability and completeness
                    if value is not None and not pd.isna(value):
                        quality_scores[datetime.combine(current_date, datetime.min.time())] = 1.0
                        days_with_data += 1
                    else:
                        quality_scores[datetime.combine(current_date, datetime.min.time())] = 0.0
                else:
                    quality_scores[datetime.combine(current_date, datetime.min.time())] = 0.0
                
                current_date += timedelta(days=1)
            
            # Calculate coverage percentage
            coverage_percentage = (days_with_data / total_days * 100) if total_days > 0 else 0.0
            
            # Find gaps
            data_dates = {d for d in metric_data.keys() if metric_data[d] is not None and not pd.isna(metric_data[d])}
            all_dates = {start_date + timedelta(days=i) for i in range(total_days)}
            gaps = self._find_gaps(all_dates, data_dates)
            
            return CoverageData(
                percentage=coverage_percentage,
                total_days=total_days,
                days_with_data=days_with_data,
                partial_days=partial_days,
                quality_scores=quality_scores,
                gaps=gaps,
                date_range=(datetime.combine(start_date, datetime.min.time()),
                           datetime.combine(end_date, datetime.min.time()))
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing metric coverage: {e}")
            return self._create_empty_coverage_data()
    
    def analyze_multi_metric_coverage(self, 
                                    metrics: Dict[str, Dict[date, float]],
                                    weights: Optional[Dict[str, float]] = None,
                                    start_date: Optional[date] = None,
                                    end_date: Optional[date] = None) -> CoverageData:
        """
        Analyze coverage across multiple metrics with optional weighting.
        
        Args:
            metrics: Dictionary of metric name to date->value mappings
            weights: Optional weights for each metric (default: equal weight)
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            CoverageData object with weighted coverage analysis
        """
        if not metrics:
            return self._create_empty_coverage_data()
        
        try:
            # Set equal weights if not provided
            if weights is None:
                weights = {metric: 1.0 for metric in metrics.keys()}
            
            # Normalize weights
            total_weight = sum(weights.values())
            weights = {k: v / total_weight for k, v in weights.items()}
            
            # Determine analysis period
            all_dates = set()
            for metric_data in metrics.values():
                all_dates.update(metric_data.keys())
            
            if start_date is None:
                start_date = min(all_dates) if all_dates else date.today()
            if end_date is None:
                end_date = max(all_dates) if all_dates else date.today()
            
            # Analyze each day
            current_date = start_date
            total_days = 0
            days_with_data = 0
            partial_days = 0
            quality_scores = {}
            
            while current_date <= end_date:
                total_days += 1
                
                # Calculate weighted quality score for this day
                daily_quality = 0.0
                has_any_data = False
                
                for metric_name, metric_data in metrics.items():
                    weight = weights.get(metric_name, 0.0)
                    
                    if current_date in metric_data:
                        value = metric_data[current_date]
                        if value is not None and not pd.isna(value):
                            daily_quality += weight * 1.0
                            has_any_data = True
                        # else: contributes 0 to quality score
                    # else: missing data contributes 0 to quality score
                
                quality_scores[datetime.combine(current_date, datetime.min.time())] = daily_quality
                
                if has_any_data:
                    days_with_data += 1
                    
                    # Consider it partial if quality score < 0.9
                    if daily_quality < 0.9:
                        partial_days += 1
                
                current_date += timedelta(days=1)
            
            # Calculate overall coverage
            coverage_percentage = (days_with_data / total_days * 100) if total_days > 0 else 0.0
            
            # Find gaps (days with no data from any metric)
            all_metric_dates = set()
            for metric_data in metrics.values():
                all_metric_dates.update(d for d, v in metric_data.items() 
                                      if v is not None and not pd.isna(v))
            
            all_analysis_dates = {start_date + timedelta(days=i) for i in range(total_days)}
            gaps = self._find_gaps(all_analysis_dates, all_metric_dates)
            
            return CoverageData(
                percentage=coverage_percentage,
                total_days=total_days,
                days_with_data=days_with_data,
                partial_days=partial_days,
                quality_scores=quality_scores,
                gaps=gaps,
                date_range=(datetime.combine(start_date, datetime.min.time()),
                           datetime.combine(end_date, datetime.min.time()))
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing multi-metric coverage: {e}")
            return self._create_empty_coverage_data()
    
    def _find_gaps(self, all_dates: set, data_dates: set) -> List[DateGap]:
        """Find continuous gaps in data coverage."""
        missing_dates = sorted(all_dates - data_dates)
        
        if not missing_dates:
            return []
        
        gaps = []
        gap_start = missing_dates[0]
        gap_end = missing_dates[0]
        
        for current_date in missing_dates[1:]:
            if isinstance(current_date, date):
                prev_date = gap_end
                gap_delta = current_date - prev_date
            else:
                # Handle datetime objects
                prev_date = gap_end.date() if hasattr(gap_end, 'date') else gap_end
                current_date_only = current_date.date() if hasattr(current_date, 'date') else current_date
                gap_delta = current_date_only - prev_date
            
            if gap_delta.days == 1:
                # Consecutive missing day, extend current gap
                gap_end = current_date
            else:
                # Non-consecutive, close current gap and start new one
                gaps.append(DateGap(
                    start=datetime.combine(gap_start if isinstance(gap_start, date) else gap_start.date(), datetime.min.time()),
                    end=datetime.combine(gap_end if isinstance(gap_end, date) else gap_end.date(), datetime.min.time())
                ))
                gap_start = current_date
                gap_end = current_date
        
        # Add the final gap
        gaps.append(DateGap(
            start=datetime.combine(gap_start if isinstance(gap_start, date) else gap_start.date(), datetime.min.time()),
            end=datetime.combine(gap_end if isinstance(gap_end, date) else gap_end.date(), datetime.min.time())
        ))
        
        return gaps
    
    def _create_empty_coverage_data(self) -> CoverageData:
        """Create empty coverage data for error cases."""
        today = date.today()
        return CoverageData(
            percentage=0.0,
            total_days=0,
            days_with_data=0,
            partial_days=0,
            quality_scores={},
            gaps=[],
            date_range=(datetime.combine(today, datetime.min.time()),
                       datetime.combine(today, datetime.min.time()))
        )


# Utility functions for common use cases
def create_sample_coverage_data(days: int = 30, coverage_rate: float = 0.8) -> CoverageData:
    """Create sample coverage data for testing and demos."""
    start_date = date.today() - timedelta(days=days-1)
    end_date = date.today()
    
    # Generate sample data with specified coverage rate
    import random
    quality_scores = {}
    days_with_data = 0
    partial_days = 0
    
    current_date = start_date
    while current_date <= end_date:
        if random.random() < coverage_rate:
            # Has data - random quality between 0.5 and 1.0
            quality = 0.5 + random.random() * 0.5
            quality_scores[datetime.combine(current_date, datetime.min.time())] = quality
            days_with_data += 1
            
            if quality < 0.9:
                partial_days += 1
        else:
            # No data
            quality_scores[datetime.combine(current_date, datetime.min.time())] = 0.0
        
        current_date += timedelta(days=1)
    
    # Find gaps
    service = CoverageService()
    all_dates = {start_date + timedelta(days=i) for i in range(days)}
    data_dates = {d.date() for d, q in quality_scores.items() if q > 0}
    gaps = service._find_gaps(all_dates, data_dates)
    
    coverage_percentage = (days_with_data / days * 100) if days > 0 else 0.0
    
    return CoverageData(
        percentage=coverage_percentage,
        total_days=days,
        days_with_data=days_with_data,
        partial_days=partial_days,
        quality_scores=quality_scores,
        gaps=gaps,
        date_range=(datetime.combine(start_date, datetime.min.time()),
                   datetime.combine(end_date, datetime.min.time()))
    )