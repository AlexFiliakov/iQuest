"""
Daily metrics calculator for health data analysis.
Provides statistical calculations for daily health metrics.
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
import logging
from enum import Enum
import warnings

from .dataframe_adapter import DataFrameAdapter
from .data_source_protocol import DataSourceProtocol


logger = logging.getLogger(__name__)


class InterpolationMethod(Enum):
    """Supported interpolation methods for missing data."""
    NONE = "none"
    LINEAR = "linear"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"


class OutlierMethod(Enum):
    """Supported outlier detection methods."""
    IQR = "iqr"
    Z_SCORE = "z_score"
    ISOLATION_FOREST = "isolation_forest"


@dataclass
class MetricStatistics:
    """Container for calculated statistics of a metric."""
    metric_name: str
    count: int
    mean: Optional[float]
    median: Optional[float]
    std: Optional[float]
    min: Optional[float]
    max: Optional[float]
    percentile_25: Optional[float]
    percentile_75: Optional[float]
    percentile_95: Optional[float]
    outlier_count: int = 0
    missing_data_count: int = 0
    insufficient_data: bool = False
    
    def to_dict(self) -> Dict[str, Union[str, int, float, bool, None]]:
        """Convert statistics to dictionary."""
        return {
            'metric_name': self.metric_name,
            'count': self.count,
            'mean': self.mean,
            'median': self.median,
            'std': self.std,
            'min': self.min,
            'max': self.max,
            'percentile_25': self.percentile_25,
            'percentile_75': self.percentile_75,
            'percentile_95': self.percentile_95,
            'outlier_count': self.outlier_count,
            'missing_data_count': self.missing_data_count,
            'insufficient_data': self.insufficient_data
        }


class DailyMetricsCalculator:
    """
    Calculator for daily health metrics statistics.
    
    Provides statistical analysis including mean, median, standard deviation,
    percentiles, and outlier detection for health data metrics.
    """
    
    def __init__(self, data: Union[pd.DataFrame, DataSourceProtocol], timezone: str = 'UTC'):
        """
        Initialize the calculator with health data.
        
        Args:
            data: Either a DataFrame or DataSourceProtocol implementation
                  Must have columns: 'creationDate', 'type', 'value'
            timezone: Timezone for date handling (default: 'UTC')
        """
        # Use adapter for flexibility
        adapter = DataFrameAdapter(data)
        self.data = adapter.get_dataframe()
        self.timezone = timezone
        
        # Show deprecation warning for direct DataFrame usage
        if isinstance(data, pd.DataFrame):
            warnings.warn(
                "Direct DataFrame usage is deprecated. Please use DataSourceProtocol implementations.",
                DeprecationWarning,
                stacklevel=2
            )
        
        self._prepare_data()
        
    def _prepare_data(self):
        """Prepare data for analysis by ensuring proper types and indexing."""
        # Ensure creationDate is datetime
        if 'creationDate' in self.data.columns:
            self.data['creationDate'] = pd.to_datetime(
                self.data['creationDate'], 
                errors='coerce',
                utc=True
            )
            # Convert to specified timezone
            if self.timezone != 'UTC':
                self.data['creationDate'] = self.data['creationDate'].dt.tz_convert(self.timezone)
            
            # Add date column for daily aggregation
            self.data['date'] = self.data['creationDate'].dt.date
        
        # Ensure value is numeric and convert to float64 for consistency
        if 'value' in self.data.columns:
            self.data['value'] = pd.to_numeric(self.data['value'], errors='coerce').astype('float64')
        
        # Sort by date for time-based operations
        if 'creationDate' in self.data.columns:
            self.data = self.data.sort_values('creationDate')
    
    def calculate_statistics(self, 
                           metric: str,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None,
                           interpolation: InterpolationMethod = InterpolationMethod.NONE) -> MetricStatistics:
        """
        Calculate all statistical measures for a metric.
        
        Args:
            metric: The metric type to analyze
            start_date: Start date for analysis (inclusive)
            end_date: End date for analysis (inclusive)
            interpolation: Method for handling missing data
            
        Returns:
            MetricStatistics object with calculated values
        """
        # Filter data for the specific metric
        metric_data = self._filter_metric_data(metric, start_date, end_date)
        
        if metric_data.empty:
            return MetricStatistics(
                metric_name=metric,
                count=0,
                mean=None,
                median=None,
                std=None,
                min=None,
                max=None,
                percentile_25=None,
                percentile_75=None,
                percentile_95=None,
                insufficient_data=True
            )
        
        # Check if all values are null/NaN
        if metric_data['value'].isna().all():
            return MetricStatistics(
                metric_name=metric,
                count=0,
                mean=None,
                median=None,
                std=None,
                min=None,
                max=None,
                percentile_25=None,
                percentile_75=None,
                percentile_95=None,
                missing_data_count=len(metric_data),
                insufficient_data=True
            )
        
        # Group by date and aggregate (handle multiple readings per day)
        # Use skipna=False to preserve NaN values when all values in a group are NaN
        daily_data = metric_data.groupby('date')['value'].agg(['mean', 'count'])
        values = daily_data['mean'].values
        
        # Handle missing data if needed
        if interpolation != InterpolationMethod.NONE:
            values = self._interpolate_missing(values, daily_data.index, interpolation)
            missing_count = np.isnan(values).sum()
        else:
            missing_count = 0
        
        # Remove NaN values for calculation
        valid_values = values[~np.isnan(values)]
        
        # Check for insufficient data
        if len(valid_values) < 2:
            return MetricStatistics(
                metric_name=metric,
                count=len(valid_values),
                mean=valid_values[0] if len(valid_values) == 1 else None,
                median=valid_values[0] if len(valid_values) == 1 else None,
                std=None,
                min=valid_values[0] if len(valid_values) == 1 else None,
                max=valid_values[0] if len(valid_values) == 1 else None,
                percentile_25=None,
                percentile_75=None,
                percentile_95=None,
                missing_data_count=missing_count,
                insufficient_data=True
            )
        
        # Calculate statistics using numpy for performance
        # Round to avoid floating point precision issues
        mean_val = float(np.mean(valid_values))
        median_val = float(np.median(valid_values))
        std_val = float(np.std(valid_values, ddof=1))  # Sample standard deviation
        min_val = float(np.min(valid_values))
        max_val = float(np.max(valid_values))
        
        # Handle floating point precision issues
        # If all values are very close (within machine epsilon), treat them as equal
        if np.allclose(valid_values, mean_val, rtol=1e-15, atol=1e-15):
            min_val = mean_val
            max_val = mean_val
            median_val = mean_val
        
        stats = MetricStatistics(
            metric_name=metric,
            count=len(valid_values),
            mean=mean_val,
            median=median_val,
            std=std_val,
            min=min_val,
            max=max_val,
            percentile_25=float(np.percentile(valid_values, 25)),
            percentile_75=float(np.percentile(valid_values, 75)),
            percentile_95=float(np.percentile(valid_values, 95)),
            missing_data_count=missing_count,
            insufficient_data=False
        )
        
        return stats
    
    def calculate_percentiles(self, 
                            metric: str, 
                            percentiles: List[int],
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> Dict[int, float]:
        """
        Calculate specified percentiles for a metric.
        
        Args:
            metric: The metric type to analyze
            percentiles: List of percentiles to calculate (0-100)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary mapping percentile to value
        """
        # Validate percentiles
        for p in percentiles:
            if not 0 <= p <= 100:
                raise ValueError(f"Percentile {p} must be between 0 and 100")
        
        # Filter data
        metric_data = self._filter_metric_data(metric, start_date, end_date)
        
        if metric_data.empty:
            return {p: None for p in percentiles}
        
        # Group by date and get daily averages
        daily_data = metric_data.groupby('date')['value'].mean()
        values = daily_data.values
        
        # Remove NaN values
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            return {p: None for p in percentiles}
        
        # Calculate percentiles using numpy
        results = {}
        for p in percentiles:
            results[p] = float(np.percentile(valid_values, p))
        
        return results
    
    def detect_outliers(self, 
                       metric: str,
                       method: OutlierMethod = OutlierMethod.IQR,
                       start_date: Optional[date] = None,
                       end_date: Optional[date] = None) -> pd.Series:
        """
        Detect outliers using specified method.
        
        Args:
            metric: The metric type to analyze
            method: Outlier detection method
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Boolean Series indicating outliers (True = outlier)
        """
        # Filter data
        metric_data = self._filter_metric_data(metric, start_date, end_date)
        
        if metric_data.empty:
            return pd.Series(dtype=bool)
        
        # Group by date for daily values
        daily_data = metric_data.groupby('date')['value'].mean()
        
        if method == OutlierMethod.IQR:
            return self._detect_outliers_iqr(daily_data)
        elif method == OutlierMethod.Z_SCORE:
            return self._detect_outliers_zscore(daily_data)
        else:
            raise NotImplementedError(f"Outlier method {method} not implemented")
    
    def _filter_metric_data(self, 
                           metric: str,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> pd.DataFrame:
        """Filter data for specific metric and date range."""
        # Filter by metric type
        if 'type' not in self.data.columns:
            raise ValueError("Data must have 'type' column")
        
        metric_data = self.data[self.data['type'] == metric].copy()
        
        # Filter by date range if provided
        if start_date or end_date:
            if 'date' not in metric_data.columns:
                raise ValueError("Data must have 'date' column")
            
            if start_date:
                metric_data = metric_data[metric_data['date'] >= start_date]
            if end_date:
                metric_data = metric_data[metric_data['date'] <= end_date]
        
        return metric_data
    
    def _interpolate_missing(self, 
                           values: np.ndarray,
                           dates: pd.Index,
                           method: InterpolationMethod) -> np.ndarray:
        """Interpolate missing values in time series data."""
        # Create a complete date range
        if len(dates) < 2:
            return values
        
        date_range = pd.date_range(start=dates.min(), end=dates.max(), freq='D')
        
        # Create series with complete date range
        series = pd.Series(index=date_range, dtype=float)
        series.loc[dates] = values
        
        # Apply interpolation
        if method == InterpolationMethod.LINEAR:
            series = series.interpolate(method='linear', limit_direction='both')
        elif method == InterpolationMethod.FORWARD_FILL:
            series = series.fillna(method='ffill')
        elif method == InterpolationMethod.BACKWARD_FILL:
            series = series.fillna(method='bfill')
        
        return series.values
    
    def _detect_outliers_iqr(self, data: pd.Series) -> pd.Series:
        """Detect outliers using Interquartile Range (IQR) method."""
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        
        # Calculate bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Identify outliers
        outliers = (data < lower_bound) | (data > upper_bound)
        
        return outliers
    
    def _detect_outliers_zscore(self, data: pd.Series, threshold: float = 3.0) -> pd.Series:
        """Detect outliers using Z-score method."""
        # Calculate z-scores
        mean = data.mean()
        std = data.std()
        
        if std == 0:
            return pd.Series([False] * len(data), index=data.index)
        
        z_scores = np.abs((data - mean) / std)
        outliers = z_scores > threshold
        
        return outliers
    
    def get_metrics_summary(self, 
                          metrics: Optional[List[str]] = None,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> Dict[str, MetricStatistics]:
        """
        Calculate statistics for multiple metrics.
        
        Args:
            metrics: List of metric types (None = all metrics)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary mapping metric name to statistics
        """
        if metrics is None:
            metrics = self.data['type'].unique().tolist()
        
        results = {}
        for metric in metrics:
            try:
                stats = self.calculate_statistics(metric, start_date, end_date)
                results[metric] = stats
            except Exception as e:
                logger.error(f"Error calculating statistics for {metric}: {e}")
                results[metric] = MetricStatistics(
                    metric_name=metric,
                    count=0,
                    mean=None,
                    median=None,
                    std=None,
                    min=None,
                    max=None,
                    percentile_25=None,
                    percentile_75=None,
                    percentile_95=None,
                    insufficient_data=True
                )
        
        return results
    
    def calculate_daily_aggregates(self,
                                 metric: str,
                                 aggregation: str = 'mean',
                                 start_date: Optional[date] = None,
                                 end_date: Optional[date] = None) -> pd.Series:
        """
        Calculate daily aggregates for a metric.
        
        Args:
            metric: The metric type to analyze
            aggregation: Aggregation method ('mean', 'sum', 'min', 'max', 'count')
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Series with daily aggregated values
        """
        # Filter data
        metric_data = self._filter_metric_data(metric, start_date, end_date)
        
        if metric_data.empty:
            return pd.Series(dtype=float)
        
        # Group by date and aggregate
        if aggregation not in ['mean', 'sum', 'min', 'max', 'count']:
            raise ValueError(f"Invalid aggregation method: {aggregation}")
        
        daily_data = metric_data.groupby('date')['value'].agg(aggregation)
        
        return daily_data
    
    def calculate_daily_statistics(self, metric: str, date: date) -> Optional[MetricStatistics]:
        """Calculate statistics for a specific metric on a specific date.
        
        Args:
            metric: The metric type to analyze
            date: The specific date to analyze
            
        Returns:
            MetricStatistics object with calculated values for that date
        """
        # Filter data for the specific metric and date
        metric_data = self._filter_metric_data(metric, date, date)
        
        if metric_data.empty:
            return None
        
        # Calculate statistics for this single day
        values = metric_data['value'].values
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            return None
        
        # For a single day, some statistics don't make sense (like std)
        # But we'll calculate what we can
        return MetricStatistics(
            metric_name=metric,
            count=len(valid_values),
            mean=float(np.mean(valid_values)),
            median=float(np.median(valid_values)),
            std=float(np.std(valid_values)) if len(valid_values) > 1 else 0.0,
            min=float(np.min(valid_values)),
            max=float(np.max(valid_values)),
            percentile_25=float(np.percentile(valid_values, 25)),
            percentile_75=float(np.percentile(valid_values, 75)),
            percentile_95=float(np.percentile(valid_values, 95)),
            insufficient_data=False
        )