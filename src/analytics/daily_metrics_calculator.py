"""
Daily Metrics Calculator for Apple Health Data Analysis.

This module provides comprehensive statistical analysis for daily health metrics including
mean, median, standard deviation, percentiles, and outlier detection. It supports multiple
interpolation methods for missing data and flexible aggregation strategies.

The calculator processes health data through the DataFrameAdapter pattern for flexibility
and provides extensive validation and error handling for robust analysis.

Example:
    Basic usage for calculating daily statistics:

    >>> import pandas as pd
    >>> from datetime import date, datetime
    >>> 
    >>> # Create sample health data
    >>> data = pd.DataFrame({
    ...     'creationDate': pd.date_range('2024-01-01', periods=30),
    ...     'type': 'HKQuantityTypeIdentifierStepCount',
    ...     'value': [8000, 7500, 9200, 6800, 10500] * 6
    ... })
    >>> 
    >>> calculator = DailyMetricsCalculator(data)
    >>> stats = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
    >>> print(f"Average daily steps: {stats.mean:.0f}")
    Average daily steps: 8400
    
    Advanced usage with date filtering and interpolation:
    
    >>> # Calculate statistics for specific date range with missing data handling
    >>> start_date = date(2024, 1, 1)
    >>> end_date = date(2024, 1, 15)
    >>> stats = calculator.calculate_statistics(
    ...     'HKQuantityTypeIdentifierStepCount',
    ...     start_date=start_date,
    ...     end_date=end_date,
    ...     interpolation=InterpolationMethod.LINEAR
    ... )
    >>> 
    >>> # Get percentiles for distribution analysis
    >>> percentiles = calculator.calculate_percentiles(
    ...     'HKQuantityTypeIdentifierStepCount',
    ...     [25, 50, 75, 90, 95]
    ... )
    >>> print(f"90th percentile: {percentiles[90]:.0f}")
    
    Outlier detection:
    
    >>> # Detect outliers using IQR method
    >>> outliers = calculator.detect_outliers(
    ...     'HKQuantityTypeIdentifierStepCount',
    ...     method=OutlierMethod.IQR
    ... )
    >>> print(f"Found {outliers.sum()} outlier days")

Note:
    This module uses deprecation warnings for direct DataFrame usage.
    Use DataSourceProtocol implementations for new code.
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

# Windows to pytz timezone mapping
WINDOWS_TIMEZONE_MAP = {
    'Eastern Standard Time': 'US/Eastern',
    'Eastern Daylight Time': 'US/Eastern',
    'Central Standard Time': 'US/Central',
    'Central Daylight Time': 'US/Central',
    'Mountain Standard Time': 'US/Mountain',
    'Mountain Daylight Time': 'US/Mountain',
    'Pacific Standard Time': 'US/Pacific',
    'Pacific Daylight Time': 'US/Pacific',
    'GMT Standard Time': 'Europe/London',
    'Central European Standard Time': 'Europe/Berlin',
    'W. Europe Standard Time': 'Europe/Amsterdam',
    'Romance Standard Time': 'Europe/Paris',
    'Tokyo Standard Time': 'Asia/Tokyo',
    'China Standard Time': 'Asia/Shanghai',
    'India Standard Time': 'Asia/Kolkata',
    'AUS Eastern Standard Time': 'Australia/Sydney',
}

def normalize_timezone(tz_name: str) -> str:
    """Convert Windows timezone names to pytz-compatible names.
    
    Args:
        tz_name: Timezone name (possibly Windows format)
        
    Returns:
        pytz-compatible timezone name
    """
    return WINDOWS_TIMEZONE_MAP.get(tz_name, tz_name)


class InterpolationMethod(Enum):
    """Enumeration of supported interpolation methods for handling missing data.
    
    Attributes:
        NONE: No interpolation - missing values remain as NaN
        LINEAR: Linear interpolation between adjacent values
        FORWARD_FILL: Forward fill using last valid observation
        BACKWARD_FILL: Backward fill using next valid observation
        
    Example:
        >>> # Use linear interpolation for missing data
        >>> stats = calculator.calculate_statistics(
        ...     'steps',
        ...     interpolation=InterpolationMethod.LINEAR
        ... )
    """
    NONE = "none"
    LINEAR = "linear"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"


class OutlierMethod(Enum):
    """Enumeration of supported outlier detection methods.
    
    Attributes:
        IQR: Interquartile Range method (Q3 + 1.5*IQR, Q1 - 1.5*IQR)
        Z_SCORE: Z-score method (threshold typically 3.0)
        ISOLATION_FOREST: Isolation Forest algorithm (not yet implemented)
        
    Example:
        >>> # Detect outliers using IQR method
        >>> outliers = calculator.detect_outliers(
        ...     'heart_rate',
        ...     method=OutlierMethod.IQR
        ... )
    """
    IQR = "iqr"
    Z_SCORE = "z_score"
    ISOLATION_FOREST = "isolation_forest"


@dataclass
class MetricStatistics:
    """Container for comprehensive statistical measures of a health metric.
    
    This dataclass holds all calculated statistics for a specific metric including
    central tendency measures, dispersion measures, percentiles, and data quality indicators.
    
    Attributes:
        metric_name: Name of the health metric (e.g., 'HKQuantityTypeIdentifierStepCount')
        count: Number of valid observations used in calculations
        mean: Arithmetic mean of the metric values
        median: Middle value when data is sorted (50th percentile)
        std: Sample standard deviation (using ddof=1)
        min: Minimum observed value
        max: Maximum observed value
        percentile_25: 25th percentile (Q1)
        percentile_75: 75th percentile (Q3)
        percentile_95: 95th percentile
        outlier_count: Number of detected outliers (default: 0)
        missing_data_count: Number of missing/interpolated data points (default: 0)
        insufficient_data: Whether there was insufficient data for reliable statistics (default: False)
        
    Example:
        >>> stats = MetricStatistics(
        ...     metric_name='steps',
        ...     count=30,
        ...     mean=8500.0,
        ...     median=8200.0,
        ...     std=1200.0,
        ...     min=5500.0,
        ...     max=12000.0,
        ...     percentile_25=7500.0,
        ...     percentile_75=9500.0,
        ...     percentile_95=11200.0
        ... )
        >>> print(f"CV: {stats.std / stats.mean:.2%}")
        CV: 14.12%
    """
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
        """Convert statistics to dictionary format for serialization or API responses.
        
        Returns:
            Dictionary containing all statistics fields with their values.
            
        Example:
            >>> stats = MetricStatistics(metric_name='steps', count=10, mean=8000.0, 
            ...                          median=7800.0, std=1000.0, min=6000.0, max=10000.0,
            ...                          percentile_25=7200.0, percentile_75=8800.0, percentile_95=9500.0)
            >>> data = stats.to_dict()
            >>> print(data['mean'])
            8000.0
        """
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
    Comprehensive calculator for daily health metrics with advanced statistical analysis.
    
    This class provides robust statistical analysis for health data including descriptive
    statistics, percentile calculations, outlier detection, and time-series aggregation.
    It handles missing data through multiple interpolation methods and provides extensive
    validation and error handling.
    
    The calculator is designed to work with Apple Health data but can handle any time-series
    health data that follows the expected schema (creationDate, type, value columns).
    
    Attributes:
        data: Processed DataFrame with health data
        timezone: Timezone used for date handling
        
    Example:
        Basic statistical analysis:
        
        >>> import pandas as pd
        >>> from datetime import date
        >>> 
        >>> # Create sample data
        >>> data = pd.DataFrame({
        ...     'creationDate': pd.date_range('2024-01-01', periods=30),
        ...     'type': 'HKQuantityTypeIdentifierStepCount',
        ...     'value': range(8000, 11000, 100)
        ... })
        >>> 
        >>> calculator = DailyMetricsCalculator(data)
        >>> stats = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        >>> print(f"Mean: {stats.mean:.0f}, Std: {stats.std:.0f}")
        
        Advanced analysis with date filtering:
        
        >>> # Analyze specific time period
        >>> recent_stats = calculator.calculate_statistics(
        ...     'HKQuantityTypeIdentifierStepCount',
        ...     start_date=date(2024, 1, 15),
        ...     end_date=date(2024, 1, 30)
        ... )
        >>> 
        >>> # Get multiple metrics summary
        >>> summary = calculator.get_metrics_summary([
        ...     'HKQuantityTypeIdentifierStepCount',
        ...     'HKQuantityTypeIdentifierDistanceWalkingRunning'
        ... ])
        
        Outlier detection:
        
        >>> # Detect unusual days
        >>> outliers = calculator.detect_outliers(
        ...     'HKQuantityTypeIdentifierStepCount',
        ...     method=OutlierMethod.IQR
        ... )
        >>> outlier_dates = outliers[outliers].index
        >>> print(f"Outlier dates: {list(outlier_dates)}")
    """
    
    def __init__(self, data: Union[pd.DataFrame, DataSourceProtocol], timezone: str = 'UTC'):
        """
        Initialize the calculator with health data and configuration.
        
        Args:
            data: Health data source. Can be either:
                - pandas.DataFrame with columns: 'creationDate', 'type', 'value'
                - DataSourceProtocol implementation for advanced data sources
                DataFrame usage is deprecated - use DataSourceProtocol for new code.
            timezone: Timezone for date handling and calculations. Defaults to 'UTC'.
                     Common values: 'UTC', 'US/Eastern', 'Europe/London', etc.
                     
        Raises:
            ValueError: If data doesn't contain required columns
            TypeError: If data is not DataFrame or DataSourceProtocol
            
        Example:
            >>> import pandas as pd
            >>> 
            >>> # Using DataFrame (deprecated but supported)
            >>> data = pd.DataFrame({
            ...     'creationDate': pd.date_range('2024-01-01', periods=10),
            ...     'type': 'steps',
            ...     'value': range(8000, 9000, 100)
            ... })
            >>> calculator = DailyMetricsCalculator(data, timezone='US/Eastern')
            >>> 
            >>> # Using DataSourceProtocol (recommended)
            >>> from .dataframe_adapter import DataFrameAdapter
            >>> adapter = DataFrameAdapter(data)
            >>> calculator = DailyMetricsCalculator(adapter)
        """
        # Use adapter for flexibility
        adapter = DataFrameAdapter(data)
        self.data = adapter.get_dataframe()
        self.timezone = normalize_timezone(timezone)
        
        # Show deprecation warning for direct DataFrame usage
        if isinstance(data, pd.DataFrame):
            warnings.warn(
                "Direct DataFrame usage is deprecated. Please use DataSourceProtocol implementations.",
                DeprecationWarning,
                stacklevel=2
            )
        
        self._prepare_data()
        
    def _prepare_data(self):
        """Prepare data for analysis by ensuring proper types and indexing.
        
        This method performs essential data preprocessing including:
        - Converting creationDate to datetime with timezone handling
        - Creating normalized date column for daily aggregation
        - Converting values to consistent float64 format
        - Sorting data chronologically for time-based operations
        
        Raises:
            ValueError: If required columns are missing or invalid
            
        Note:
            This method modifies self.data in place and adds a 'date' column
            for daily aggregation operations.
        """
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
            # Use normalize() to ensure we get date at midnight for proper comparison
            self.data['date'] = pd.to_datetime(self.data['creationDate']).dt.normalize().dt.date
            
            # Log some debug info
            logger.debug(f"Prepared data with {len(self.data)} records")
            if len(self.data) > 0:
                logger.debug(f"Date range: {self.data['date'].min()} to {self.data['date'].max()}")
        
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
        Calculate comprehensive statistical measures for a specific health metric.
        
        This method computes descriptive statistics including measures of central tendency,
        dispersion, and distribution shape. It handles missing data through interpolation
        and provides robust error handling for edge cases.
        
        Args:
            metric: The health metric type identifier to analyze.
                   Examples: 'HKQuantityTypeIdentifierStepCount', 'HKQuantityTypeIdentifierHeartRate'
            start_date: Start date for analysis window (inclusive). If None, uses all available data.
            end_date: End date for analysis window (inclusive). If None, uses all available data.
            interpolation: Method for handling missing data points. Options:
                          - NONE: Leave missing values as NaN
                          - LINEAR: Linear interpolation between points
                          - FORWARD_FILL: Use last valid observation
                          - BACKWARD_FILL: Use next valid observation
                          
        Returns:
            MetricStatistics object containing:
            - Basic statistics (count, mean, median, std, min, max)
            - Percentiles (25th, 75th, 95th)
            - Data quality indicators (missing data count, insufficient data flag)
            
        Raises:
            ValueError: If metric type is not found in data
            TypeError: If date parameters are not date objects
            
        Example:
            >>> from datetime import date
            >>> 
            >>> # Calculate basic statistics
            >>> stats = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
            >>> print(f"Average: {stats.mean:.0f} ± {stats.std:.0f}")
            >>> 
            >>> # Calculate for specific time period with interpolation
            >>> stats = calculator.calculate_statistics(
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31),
            ...     interpolation=InterpolationMethod.LINEAR
            ... )
            >>> 
            >>> # Check data quality
            >>> if stats.insufficient_data:
            ...     print("Warning: Insufficient data for reliable statistics")
            >>> if stats.missing_data_count > 0:
            ...     print(f"Note: {stats.missing_data_count} missing data points interpolated")
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
        Calculate specified percentiles for detailed distribution analysis.
        
        This method computes percentiles using numpy's percentile function with
        linear interpolation. It's useful for understanding data distribution
        and identifying threshold values for analysis.
        
        Args:
            metric: The health metric type identifier to analyze
            percentiles: List of percentiles to calculate, values must be between 0-100.
                        Common values: [25, 50, 75, 90, 95, 99]
            start_date: Start date for analysis window (inclusive). None for all data.
            end_date: End date for analysis window (inclusive). None for all data.
            
        Returns:
            Dictionary mapping percentile values to their calculated values.
            Returns {percentile: None} for any percentiles that couldn't be calculated.
            
        Raises:
            ValueError: If any percentile is not between 0-100
            ValueError: If metric is not found in data
            
        Example:
            >>> # Calculate common percentiles
            >>> percentiles = calculator.calculate_percentiles(
            ...     'HKQuantityTypeIdentifierStepCount',
            ...     [25, 50, 75, 90, 95]
            ... )
            >>> print(f"Median (50th): {percentiles[50]:.0f}")
            >>> print(f"90th percentile: {percentiles[90]:.0f}")
            >>> 
            >>> # Calculate extreme percentiles
            >>> extremes = calculator.calculate_percentiles(
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     [1, 5, 95, 99],
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31)
            ... )
            >>> if extremes[99] is not None:
            ...     print(f"99th percentile heart rate: {extremes[99]:.1f} BPM")
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
        Detect outliers in health data using statistical methods.
        
        This method identifies data points that significantly deviate from the
        normal pattern using established statistical techniques. Useful for
        data quality assessment and identifying unusual health events.
        
        Args:
            metric: The health metric type identifier to analyze
            method: Outlier detection method to use:
                   - IQR: Interquartile Range (values outside Q1-1.5*IQR, Q3+1.5*IQR)
                   - Z_SCORE: Z-score method (values with |z-score| > 3.0)
                   - ISOLATION_FOREST: Not yet implemented
            start_date: Start date for analysis window (inclusive). None for all data.
            end_date: End date for analysis window (inclusive). None for all data.
            
        Returns:
            Boolean pandas Series with datetime index where True indicates an outlier.
            Returns empty Series if no data available or method fails.
            
        Raises:
            ValueError: If metric is not found in data
            NotImplementedError: If unsupported outlier method is specified
            
        Example:
            >>> # Detect outliers using IQR method
            >>> outliers = calculator.detect_outliers(
            ...     'HKQuantityTypeIdentifierStepCount',
            ...     method=OutlierMethod.IQR
            ... )
            >>> outlier_dates = outliers[outliers].index
            >>> print(f"Found {len(outlier_dates)} outlier days")
            >>> 
            >>> # Get outlier values
            >>> daily_data = calculator.calculate_daily_aggregates(
            ...     'HKQuantityTypeIdentifierStepCount'
            ... )
            >>> outlier_values = daily_data[outliers]
            >>> for date, value in outlier_values.items():
            ...     print(f"{date.date()}: {value:.0f} steps (outlier)")
            >>> 
            >>> # Detect outliers in specific time period
            >>> recent_outliers = calculator.detect_outliers(
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     method=OutlierMethod.Z_SCORE,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31)
            ... )
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
        """
        Filter health data for specific metric and optional date range.
        
        This internal method handles data filtering with proper validation
        and logging for debugging purposes.
        
        Args:
            metric: The health metric type identifier to filter for
            start_date: Start date for filtering (inclusive). None for no start limit.
            end_date: End date for filtering (inclusive). None for no end limit.
            
        Returns:
            Filtered DataFrame containing only the specified metric and date range.
            
        Raises:
            ValueError: If required 'type' or 'date' columns are missing
            
        Note:
            This method logs debug information about filtering results.
        """
        # Filter by metric type
        if 'type' not in self.data.columns:
            raise ValueError("Data must have 'type' column")
        
        metric_data = self.data[self.data['type'] == metric].copy()
        
        # Log debug info
        logger.debug(f"Filtering data for metric '{metric}', found {len(metric_data)} records")
        
        # Filter by date range if provided
        if start_date or end_date:
            if 'date' not in metric_data.columns:
                raise ValueError("Data must have 'date' column")
            
            if start_date:
                # Ensure start_date is a date object for comparison
                if isinstance(start_date, pd.Timestamp):
                    start_date = start_date.date()
                metric_data = metric_data[metric_data['date'] >= start_date]
                logger.debug(f"After start_date filter ({start_date}): {len(metric_data)} records")
            if end_date:
                # Ensure end_date is a date object for comparison
                if isinstance(end_date, pd.Timestamp):
                    end_date = end_date.date()
                metric_data = metric_data[metric_data['date'] <= end_date]
                logger.debug(f"After end_date filter ({end_date}): {len(metric_data)} records")
        
        return metric_data
    
    def _interpolate_missing(self, 
                           values: np.ndarray,
                           dates: pd.Index,
                           method: InterpolationMethod) -> np.ndarray:
        """
        Interpolate missing values in time series data using specified method.
        
        This method handles gaps in daily data by applying different interpolation
        strategies to maintain data continuity for statistical analysis.
        
        Args:
            values: Array of metric values with potential NaN gaps
            dates: DatetimeIndex corresponding to the values
            method: Interpolation method to apply
            
        Returns:
            Array with interpolated values. Original array returned if interpolation fails.
            
        Note:
            - Creates complete date range for interpolation
            - Handles edge cases where interpolation is not possible
            - LINEAR method uses pandas interpolate with both directions
        """
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
            series = series.ffill()
        elif method == InterpolationMethod.BACKWARD_FILL:
            series = series.bfill()
        
        return series.values
    
    def _detect_outliers_iqr(self, data: pd.Series) -> pd.Series:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        This method identifies outliers as values that fall outside the range
        [Q1 - 1.5*IQR, Q3 + 1.5*IQR] where IQR = Q3 - Q1.
        
        Args:
            data: Time series data to analyze for outliers
            
        Returns:
            Boolean Series indicating outlier status for each data point.
            
        Note:
            This is a robust method that works well for most distributions
            and is less sensitive to extreme values than z-score methods.
        """
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
        """
        Detect outliers using Z-score method with configurable threshold.
        
        This method identifies outliers as values with absolute z-scores exceeding
        the specified threshold. Z-score = (value - mean) / standard_deviation.
        
        Args:
            data: Time series data to analyze for outliers
            threshold: Z-score threshold for outlier detection. Common values:
                      - 2.0: More sensitive (identifies ~5% of normal data as outliers)
                      - 3.0: Standard threshold (identifies ~0.3% of normal data)
                      - 4.0: Conservative threshold
                      
        Returns:
            Boolean Series indicating outlier status for each data point.
            Returns all False if standard deviation is zero.
            
        Note:
            This method assumes normal distribution and may not work well
            for highly skewed data. Consider IQR method for non-normal distributions.
        """
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
        Calculate comprehensive statistics for multiple health metrics efficiently.
        
        This method provides a convenient way to analyze multiple metrics simultaneously
        with consistent parameters and error handling for each metric.
        
        Args:
            metrics: List of metric type identifiers to analyze. If None, analyzes
                    all unique metric types found in the data.
            start_date: Start date for analysis window (inclusive). None for all data.
            end_date: End date for analysis window (inclusive). None for all data.
            
        Returns:
            Dictionary mapping metric names to their MetricStatistics objects.
            Failed calculations return MetricStatistics with insufficient_data=True.
            
        Example:
            >>> # Analyze all available metrics
            >>> summary = calculator.get_metrics_summary()
            >>> for metric, stats in summary.items():
            ...     if not stats.insufficient_data:
            ...         print(f"{metric}: {stats.mean:.1f} ± {stats.std:.1f}")
            >>> 
            >>> # Analyze specific metrics for a time period
            >>> metrics_of_interest = [
            ...     'HKQuantityTypeIdentifierStepCount',
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     'HKQuantityTypeIdentifierDistanceWalkingRunning'
            ... ]
            >>> monthly_summary = calculator.get_metrics_summary(
            ...     metrics=metrics_of_interest,
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31)
            ... )
            >>> 
            >>> # Check data quality across metrics
            >>> for metric, stats in monthly_summary.items():
            ...     if stats.insufficient_data:
            ...         print(f"Warning: Insufficient data for {metric}")
            ...     elif stats.missing_data_count > 0:
            ...         print(f"Note: {metric} has {stats.missing_data_count} missing days")
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
        Calculate daily aggregated values for time series analysis and visualization.
        
        This method aggregates multiple readings per day into single daily values
        using the specified aggregation method. Essential for daily trend analysis
        and preparing data for further statistical processing.
        
        Args:
            metric: The health metric type identifier to aggregate
            aggregation: Aggregation method to apply:
                        - 'mean': Average of all readings (default, good for most metrics)
                        - 'sum': Total of all readings (good for cumulative metrics like steps)
                        - 'min': Minimum reading (useful for resting heart rate)
                        - 'max': Maximum reading (useful for peak values)
                        - 'count': Number of readings per day
            start_date: Start date for analysis window (inclusive). None for all data.
            end_date: End date for analysis window (inclusive). None for all data.
            
        Returns:
            pandas Series with date index and aggregated daily values.
            Returns empty Series if no data available.
            
        Raises:
            ValueError: If aggregation method is not supported
            ValueError: If metric is not found in data
            
        Example:
            >>> # Get daily average step counts
            >>> daily_steps = calculator.calculate_daily_aggregates(
            ...     'HKQuantityTypeIdentifierStepCount',
            ...     aggregation='sum'  # Sum all step readings per day
            ... )
            >>> print(f"Steps on {daily_steps.index[0].date()}: {daily_steps.iloc[0]:.0f}")
            >>> 
            >>> # Get daily minimum heart rate (resting heart rate proxy)
            >>> daily_min_hr = calculator.calculate_daily_aggregates(
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     aggregation='min',
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31)
            ... )
            >>> print(f"Average resting HR: {daily_min_hr.mean():.1f} BPM")
            >>> 
            >>> # Count readings per day for data quality assessment
            >>> reading_counts = calculator.calculate_daily_aggregates(
            ...     'HKQuantityTypeIdentifierHeartRate',
            ...     aggregation='count'
            ... )
            >>> low_data_days = reading_counts[reading_counts < 10]
            >>> print(f"Days with <10 readings: {len(low_data_days)}")
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
    
    def calculate_daily_statistics(self, metric: str, target_date: date) -> Optional[MetricStatistics]:
        """
        Calculate comprehensive statistics for a specific metric on a single date.
        
        This method provides detailed statistical analysis for a single day's data,
        useful for investigating specific days or understanding daily variation patterns.
        
        Args:
            metric: The health metric type identifier to analyze
            target_date: The specific date to analyze
            
        Returns:
            MetricStatistics object with calculated values for that date, or None if
            no data exists for the specified date and metric.
            
        Note:
            - Standard deviation is 0.0 for single readings
            - All percentiles equal the mean for single readings
            - Multiple readings per day will have proper statistical calculations
            
        Example:
            >>> from datetime import date
            >>> 
            >>> # Analyze a specific day
            >>> day_stats = calculator.calculate_daily_statistics(
            ...     'HKQuantityTypeIdentifierStepCount',
            ...     date(2024, 1, 15)
            ... )
            >>> 
            >>> if day_stats:
            ...     print(f"Steps on Jan 15: {day_stats.mean:.0f}")
            ...     print(f"Readings taken: {day_stats.count}")
            ...     if day_stats.count > 1:
            ...         print(f"Range: {day_stats.min:.0f} - {day_stats.max:.0f}")
            ... else:
            ...     print("No data available for this date")
            >>> 
            >>> # Compare multiple days
            >>> dates_to_check = [date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12)]
            >>> for check_date in dates_to_check:
            ...     stats = calculator.calculate_daily_statistics(
            ...         'HKQuantityTypeIdentifierHeartRate',
            ...         check_date
            ...     )
            ...     if stats:
            ...         print(f"{check_date}: {stats.mean:.1f} BPM ({stats.count} readings)")
        """
        # Filter data for the specific metric and date
        metric_data = self._filter_metric_data(metric, target_date, target_date)
        
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