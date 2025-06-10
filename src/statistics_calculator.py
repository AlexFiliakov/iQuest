"""Comprehensive statistics calculator for health data analysis.

This module provides statistical analysis capabilities for health data, including
basic descriptive statistics, distribution analysis, time series analysis, and
statistical testing. It supports both DataFrame-based and database-based calculations
with comprehensive error handling and statistical rigor.

The module includes:
    - Basic statistics computation (mean, median, std, etc.)
    - Health data aggregation by type and source
    - Date range analysis and temporal statistics
    - Distribution analysis and normality testing
    - Time series trend analysis
    - Statistical hypothesis testing
    - Confidence interval calculations
    - Bootstrap resampling methods
    - Correlation analysis

Key classes:
    BasicStatistics: Container for fundamental health data statistics
    StatisticsCalculator: Main calculator with comprehensive analysis methods

Examples:
    Basic usage with DataFrame:
        >>> calculator = StatisticsCalculator()
        >>> stats = calculator.calculate_from_dataframe(health_df)
        >>> print(f"Total records: {stats.total_records}")
        >>> print(f"Date range: {stats.date_range}")
        
    Advanced statistical analysis:
        >>> calculator = StatisticsCalculator(data_loader)
        >>> descriptive = calculator.calculate_descriptive_stats(health_df['value'])
        >>> distribution = calculator.analyze_distribution(health_df['value'])
        >>> correlation = calculator.calculate_correlation_matrix(health_df)
        
    Database-based statistics:
        >>> stats = calculator.calculate_from_database(
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31),
        ...     types=['StepCount', 'HeartRate']
        ... )

Attributes:
    BasicStatistics: Dataclass for organizing fundamental statistics.
    StatisticsCalculator: Primary class for statistical computations.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class BasicStatistics:
    """Container for fundamental health data statistics and metadata.
    
    Organizes essential statistical information about health data including
    record counts, temporal coverage, and data distribution by type and source.
    Provides serialization methods for storage and API responses.
    
    Attributes:
        total_records (int): Total number of health records in the dataset.
        date_range (Tuple[datetime, datetime]): Earliest and latest record dates.
        records_by_type (Dict[str, int]): Count of records for each health metric type.
        records_by_source (Dict[str, int]): Count of records for each data source.
        types_by_source (Dict[str, List[str]]): List of health types available from each source.
        
    Examples:
        Create statistics object:
        >>> stats = BasicStatistics(
        ...     total_records=10000,
        ...     date_range=(datetime(2024, 1, 1), datetime(2024, 12, 31)),
        ...     records_by_type={'StepCount': 5000, 'HeartRate': 3000},
        ...     records_by_source={'iPhone': 6000, 'Apple Watch': 4000},
        ...     types_by_source={'iPhone': ['StepCount'], 'Apple Watch': ['HeartRate']}
        ... )
        
        Serialize for storage:
        >>> stats_dict = stats.to_dict()
        >>> # Can be saved to JSON or database
    """
    total_records: int
    date_range: Tuple[datetime, datetime]  # (earliest, latest)
    records_by_type: Dict[str, int]
    records_by_source: Dict[str, int]
    types_by_source: Dict[str, List[str]]  # source -> list of types
    
    def to_dict(self) -> dict:
        """Convert statistics to dictionary format for serialization and storage.
        
        Transforms the statistics object into a JSON-serializable dictionary
        with proper date formatting. Useful for API responses, caching, and
        configuration storage.
        
        Returns:
            Dictionary containing all statistics with proper type conversion:
                - total_records: Integer count
                - date_range: Dict with 'start' and 'end' ISO-formatted dates or None
                - records_by_type: Dict mapping type names to counts
                - records_by_source: Dict mapping source names to counts
                - types_by_source: Dict mapping source names to type lists
                
        Examples:
            Convert for JSON serialization:
            >>> stats = BasicStatistics(...)
            >>> stats_dict = stats.to_dict()
            >>> import json
            >>> json_str = json.dumps(stats_dict)
            
            Access converted data:
            >>> stats_dict = stats.to_dict()
            >>> if stats_dict['date_range']['start']:
            ...     print(f"Data starts: {stats_dict['date_range']['start']}")
        """
        return {
            'total_records': self.total_records,
            'date_range': {
                'start': self.date_range[0].isoformat() if self.date_range[0] else None,
                'end': self.date_range[1].isoformat() if self.date_range[1] else None
            },
            'records_by_type': self.records_by_type,
            'records_by_source': self.records_by_source,
            'types_by_source': self.types_by_source
        }


class StatisticsCalculator:
    """Comprehensive statistical analysis engine for health data.
    
    Provides a wide range of statistical analysis capabilities for health data,
    from basic descriptive statistics to advanced statistical modeling. Supports
    both in-memory DataFrame analysis and database-driven computations.
    
    The calculator offers:
        - Descriptive statistics (mean, median, std, quartiles, etc.)
        - Distribution analysis and normality testing
        - Time series analysis and trend detection
        - Correlation analysis and statistical relationships
        - Hypothesis testing and confidence intervals
        - Bootstrap resampling methods
        - Health data aggregation and summarization
        
    Attributes:
        data_loader: Optional DataLoader instance for database operations.
        
    Examples:
        Initialize with data loader:
        >>> from src.data_loader import DataLoader
        >>> loader = DataLoader()
        >>> loader.db_path = "health.db"
        >>> calculator = StatisticsCalculator(loader)
        
        Basic DataFrame analysis:
        >>> calculator = StatisticsCalculator()
        >>> basic_stats = calculator.calculate_from_dataframe(df)
        >>> summary = calculator.get_quick_summary(basic_stats)
        >>> print(summary)
        
        Advanced statistical analysis:
        >>> descriptive = calculator.calculate_descriptive_stats(df['value'])
        >>> distribution = calculator.analyze_distribution(df['value'])
        >>> trend = calculator.analyze_time_series(df['date'], df['value'])
    """
    
    def __init__(self, data_loader=None):
        """Initialize the statistics calculator with optional data loader.
        
        Args:
            data_loader: Optional DataLoader instance for database-based
                statistics computation. If provided, enables database-driven
                analysis methods.
                
        Examples:
            Calculator without data loader (DataFrame-only):
            >>> calculator = StatisticsCalculator()
            
            Calculator with database access:
            >>> from src.data_loader import DataLoader
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> calculator = StatisticsCalculator(loader)
        """
        self.data_loader = data_loader
    
    def calculate_from_dataframe(self, df: pd.DataFrame) -> BasicStatistics:
        """Calculate comprehensive statistics from a pandas DataFrame.
        
        Analyzes health data stored in a DataFrame format to compute fundamental
        statistics including record counts, date ranges, and distribution by type
        and source. Handles missing data and date parsing errors gracefully.
        
        Args:
            df: DataFrame containing health data with expected columns:
                - startDate: Timestamp when record was created
                - type: Health metric type (e.g., 'StepCount', 'HeartRate')
                - sourceName: Source device or app name
                - value: Numeric measurement value (optional)
                
        Returns:
            BasicStatistics object containing:
                - total_records: Count of all records
                - date_range: Tuple of (earliest, latest) dates
                - records_by_type: Dict of type -> count
                - records_by_source: Dict of source -> count
                - types_by_source: Dict of source -> list of types
                
        Examples:
            Analyze complete dataset:
            >>> calculator = StatisticsCalculator()
            >>> stats = calculator.calculate_from_dataframe(health_df)
            >>> print(f"Analyzed {stats.total_records} records")
            >>> print(f"Date span: {stats.date_range[1] - stats.date_range[0]}")
            
            Handle empty DataFrame:
            >>> empty_stats = calculator.calculate_from_dataframe(pd.DataFrame())
            >>> print(f"Empty dataset: {empty_stats.total_records} records")
            
            Examine data distribution:
            >>> stats = calculator.calculate_from_dataframe(df)
            >>> top_type = max(stats.records_by_type, key=stats.records_by_type.get)
            >>> print(f"Most common type: {top_type} ({stats.records_by_type[top_type]} records)")
        """
        if df.empty:
            return BasicStatistics(
                total_records=0,
                date_range=(None, None),
                records_by_type={},
                records_by_source={},
                types_by_source={}
            )
        
        # Total records
        total_records = len(df)
        
        # Date range - handle mixed date formats and timezones
        try:
            df['startDate'] = pd.to_datetime(df['startDate'], format='mixed', utc=True)
            date_range = (df['startDate'].min(), df['startDate'].max())
        except Exception as e:
            # If date parsing fails, try without format specification
            try:
                df['startDate'] = pd.to_datetime(df['startDate'], utc=True)
                date_range = (df['startDate'].min(), df['startDate'].max())
            except Exception:
                # If all parsing fails, return None for date range
                date_range = (None, None)
        
        # Records by type
        records_by_type = df['type'].value_counts().to_dict()
        
        # Records by source
        records_by_source = df['sourceName'].value_counts().to_dict()
        
        # Types by source
        types_by_source = defaultdict(list)
        grouped = df.groupby(['sourceName', 'type']).size()
        for (source, type_name), _ in grouped.items():
            if type_name not in types_by_source[source]:
                types_by_source[source].append(type_name)
        
        # Sort types within each source
        for source in types_by_source:
            types_by_source[source].sort()
        
        return BasicStatistics(
            total_records=total_records,
            date_range=date_range,
            records_by_type=records_by_type,
            records_by_source=records_by_source,
            types_by_source=dict(types_by_source)
        )
    
    def calculate_from_database(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               types: Optional[List[str]] = None,
                               sources: Optional[List[str]] = None) -> BasicStatistics:
        """Calculate statistics from database with comprehensive filtering options.
        
        Computes statistics directly from the database with optional filtering
        by date range, health metric types, and data sources. Currently loads
        all records into memory for filtering - future versions may implement
        database-level filtering for improved performance.
        
        Args:
            start_date: Optional start date filter (inclusive). Only records
                created on or after this date will be included.
            end_date: Optional end date filter (inclusive). Only records
                created on or before this date will be included.
            types: Optional list of health metric types to include
                (e.g., ['StepCount', 'HeartRate']).
            sources: Optional list of source names to include
                (e.g., ['iPhone', 'Apple Watch']).
                
        Returns:
            BasicStatistics object with filtered data statistics.
            
        Raises:
            ValueError: If DataLoader not provided during initialization or
                if database query fails.
                
        Examples:
            Calculate stats for specific date range:
            >>> calculator = StatisticsCalculator(data_loader)
            >>> stats = calculator.calculate_from_database(
            ...     start_date=datetime(2024, 1, 1),
            ...     end_date=datetime(2024, 3, 31)
            ... )
            >>> print(f"Q1 2024: {stats.total_records} records")
            
            Filter by health metric types:
            >>> activity_stats = calculator.calculate_from_database(
            ...     types=['StepCount', 'DistanceWalkingRunning', 'FlightsClimbed']
            ... )
            
            Analyze specific device data:
            >>> watch_stats = calculator.calculate_from_database(
            ...     sources=['Apple Watch']
            ... )
        """
        if not self.data_loader:
            raise ValueError("DataLoader not provided")
        
        # Load all records and filter in memory
        # This is less efficient than database filtering but works with current DataLoader
        try:
            df = self.data_loader.get_all_records()
            
            # Apply filters if provided
            if start_date:
                df = df[df['startDate'] >= start_date]
            
            if end_date:
                df = df[df['startDate'] <= end_date]
            
            if types:
                df = df[df['type'].isin(types)]
            
            if sources:
                df = df[df['sourceName'].isin(sources)]
            
            return self.calculate_from_dataframe(df)
            
        except Exception as e:
            raise ValueError(f"Failed to calculate statistics from database: {e}")
    
    def get_quick_summary(self, stats: BasicStatistics) -> str:
        """Generate human-readable summary of health data statistics.
        
        Creates a formatted text summary of the key statistics including
        record counts, date range, top health metric types, and data sources.
        Ideal for displaying in user interfaces or generating reports.
        
        Args:
            stats: BasicStatistics object containing computed statistics.
            
        Returns:
            Multi-line formatted string with:
                - Total record count with thousand separators
                - Date range in YYYY-MM-DD format
                - Top 5 health metric types with counts
                - All data sources with record counts
                
        Examples:
            Display statistics summary:
            >>> stats = calculator.calculate_from_dataframe(df)
            >>> summary = calculator.get_quick_summary(stats)
            >>> print(summary)
            # Output:
            # Total Records: 25,430
            # Date Range: 2024-01-01 to 2024-12-31
            # 
            # Top 5 Record Types:
            #   - StepCount: 8,760
            #   - HeartRate: 12,456
            #   ...
            
            Handle empty dataset:
            >>> empty_stats = BasicStatistics(0, (None, None), {}, {}, {})
            >>> summary = calculator.get_quick_summary(empty_stats)
            >>> print(summary)  # "No health records found."
        """
        if stats.total_records == 0:
            return "No health records found."
        
        lines = [
            f"Total Records: {stats.total_records:,}",
            f"Date Range: {stats.date_range[0].strftime('%Y-%m-%d')} to {stats.date_range[1].strftime('%Y-%m-%d')}",
            f"",
            f"Top 5 Record Types:",
        ]
        
        # Top 5 types
        sorted_types = sorted(stats.records_by_type.items(), 
                            key=lambda x: x[1], reverse=True)[:5]
        for type_name, count in sorted_types:
            lines.append(f"  - {type_name}: {count:,}")
        
        lines.extend([
            f"",
            f"Data Sources ({len(stats.records_by_source)}):",
        ])
        
        # All sources
        sorted_sources = sorted(stats.records_by_source.items(), 
                              key=lambda x: x[1], reverse=True)
        for source_name, count in sorted_sources:
            lines.append(f"  - {source_name}: {count:,} records")
        
        return "\n".join(lines)
    
    def calculate_descriptive_stats(self, data: pd.Series) -> Dict:
        """Calculate comprehensive descriptive statistics for numeric health data.
        
        Computes a full suite of descriptive statistics including measures of
        central tendency, variability, and distribution shape. Handles missing
        values and edge cases gracefully.
        
        Args:
            data: Pandas Series containing numeric health measurements.
            
        Returns:
            Dictionary containing descriptive statistics:
                - 'mean': Arithmetic mean
                - 'median': Middle value (50th percentile)
                - 'std': Standard deviation
                - 'var': Variance
                - 'min': Minimum value
                - 'max': Maximum value
                - 'range': Difference between max and min
                - 'q1': First quartile (25th percentile)
                - 'q3': Third quartile (75th percentile)
                - 'iqr': Interquartile range (Q3 - Q1)
                - 'skewness': Measure of distribution asymmetry
                - 'kurtosis': Measure of distribution tail heaviness
                - 'mode': Most frequent value
                
        Examples:
            Analyze step count data:
            >>> step_data = health_df[health_df['type'] == 'StepCount']['value']
            >>> stats = calculator.calculate_descriptive_stats(step_data)
            >>> print(f"Average steps: {stats['mean']:.0f}")
            >>> print(f"Step range: {stats['min']:.0f} - {stats['max']:.0f}")
            
            Check data distribution:
            >>> heart_rate = health_df[health_df['type'] == 'HeartRate']['value']
            >>> stats = calculator.calculate_descriptive_stats(heart_rate)
            >>> if abs(stats['skewness']) < 0.5:
            ...     print("Heart rate distribution is approximately normal")
        """
        if data.empty or data.isna().all():
            return {}
            
        clean_data = data.dropna()
        if clean_data.empty:
            return {}
            
        stats = {
            'mean': float(clean_data.mean()),
            'median': float(clean_data.median()),
            'std': float(clean_data.std()),
            'var': float(clean_data.var()),
            'min': float(clean_data.min()),
            'max': float(clean_data.max()),
            'range': float(clean_data.max() - clean_data.min()),
            'q1': float(clean_data.quantile(0.25)),
            'q3': float(clean_data.quantile(0.75)),
            'iqr': float(clean_data.quantile(0.75) - clean_data.quantile(0.25)),
            'skewness': float(clean_data.skew()) if len(clean_data) > 1 else 0.0,
            'kurtosis': float(clean_data.kurtosis()) if len(clean_data) > 1 else 0.0,
        }
        
        # Add mode (most frequent value)
        mode_result = clean_data.mode()
        stats['mode'] = float(mode_result.iloc[0]) if not mode_result.empty else stats['mean']
        
        return stats
    
    def calculate_correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Pearson correlation matrix for numeric health data columns.
        
        Computes pairwise correlations between all numeric columns in the DataFrame,
        identifying relationships between different health metrics. Useful for
        understanding how health measurements relate to each other.
        
        Args:
            df: DataFrame containing health data with numeric columns.
            
        Returns:
            DataFrame containing correlation matrix with correlation coefficients
            ranging from -1 (perfect negative correlation) to 1 (perfect positive
            correlation). Returns empty DataFrame if fewer than 2 numeric columns.
            
        Examples:
            Analyze correlations between health metrics:
            >>> # Assume df has columns for steps, heart_rate, calories, etc.
            >>> corr_matrix = calculator.calculate_correlation_matrix(health_df)
            >>> print(corr_matrix)
            >>> 
            >>> # Find strongest correlations
            >>> high_corr = corr_matrix.abs() > 0.7
            >>> print("Strong correlations found:", high_corr.sum().sum())
            
            Check specific metric relationships:
            >>> if 'steps' in corr_matrix and 'calories' in corr_matrix:
            ...     steps_calories_corr = corr_matrix.loc['steps', 'calories']
            ...     print(f"Steps-Calories correlation: {steps_calories_corr:.3f}")
        """
        numeric_cols = df.select_dtypes(include=[float, int]).columns
        if len(numeric_cols) < 2:
            return pd.DataFrame()
        return df[numeric_cols].corr()
    
    def analyze_distribution(self, data: pd.Series) -> Dict:
        """Analyze statistical distribution characteristics of health data.
        
        Performs comprehensive distribution analysis including normality testing
        and distribution shape classification. Uses appropriate statistical tests
        based on sample size and provides fallback options when scipy is unavailable.
        
        Args:
            data: Pandas Series containing numeric health measurements.
            
        Returns:
            Dictionary containing distribution analysis:
                - 'distribution_type': Classification of distribution shape
                  ('approximately_normal', 'right_skewed', 'left_skewed', etc.)
                - 'normality_test': Results of statistical normality test
                  (Shapiro-Wilk for n≤5000, Anderson-Darling for larger samples)
                - 'skewness': Numerical measure of distribution asymmetry
                
        Examples:
            Analyze heart rate distribution:
            >>> hr_data = health_df[health_df['type'] == 'HeartRate']['value']
            >>> distribution = calculator.analyze_distribution(hr_data)
            >>> print(f"Distribution type: {distribution['distribution_type']}")
            >>> if distribution['normality_test']:
            ...     test_result = distribution['normality_test']
            ...     print(f"Normality test: {test_result['test']} p-value: {test_result.get('p_value', 'N/A')}")
            
            Check if data follows normal distribution:
            >>> dist_analysis = calculator.analyze_distribution(data)
            >>> is_normal = dist_analysis['distribution_type'] == 'approximately_normal'
            >>> if is_normal:
            ...     print("Data appears normally distributed - parametric tests appropriate")
            ... else:
            ...     print("Data is not normal - consider non-parametric tests")
        """
        clean_data = data.dropna()
        if len(clean_data) < 10:
            return {'distribution_type': 'insufficient_data', 'normality_test': None}
        
        try:
            from scipy import stats

            # Shapiro-Wilk test for normality (for small samples)
            if len(clean_data) <= 5000:
                stat, p_value = stats.shapiro(clean_data)
                normality_test = {'test': 'shapiro', 'statistic': stat, 'p_value': p_value}
            else:
                # Use Anderson-Darling for larger samples
                result = stats.anderson(clean_data)
                normality_test = {'test': 'anderson', 'statistic': result.statistic, 'critical_values': result.critical_values}
            
            # Simple distribution classification
            skewness = clean_data.skew()
            if abs(skewness) < 0.5:
                dist_type = 'approximately_normal'
            elif skewness > 0.5:
                dist_type = 'right_skewed'
            else:
                dist_type = 'left_skewed'
                
            return {
                'distribution_type': dist_type,
                'normality_test': normality_test,
                'skewness': skewness
            }
        except ImportError:
            # Fallback without scipy
            return {
                'distribution_type': 'unknown',
                'normality_test': None,
                'skewness': float(clean_data.skew()) if len(clean_data) > 1 else 0.0
            }
    
    def analyze_time_series(self, dates: pd.Series, values: pd.Series) -> Dict:
        """Perform basic time series analysis on health data.
        
        Analyzes temporal patterns in health data including trend detection
        using linear regression. Provides foundation for understanding how
        health metrics change over time.
        
        Args:
            dates: Pandas Series containing dates/timestamps for measurements.
            values: Pandas Series containing corresponding numeric values.
                Must be same length as dates.
                
        Returns:
            Dictionary containing time series analysis:
                - 'trend': Dict with trend information including:
                  - 'direction': 'increasing', 'decreasing', or 'stable'
                  - 'slope': Numerical slope value (units per day)
                - 'seasonality': Placeholder for future seasonal analysis
                
        Examples:
            Analyze weight trend over time:
            >>> weight_data = health_df[health_df['type'] == 'BodyMass']
            >>> trend_analysis = calculator.analyze_time_series(
            ...     weight_data['startDate'],
            ...     weight_data['value']
            ... )
            >>> trend = trend_analysis['trend']
            >>> if trend:
            ...     print(f"Weight trend: {trend['direction']}")
            ...     print(f"Rate of change: {trend['slope']:.3f} units/day")
            
            Monitor step count trends:
            >>> steps_data = health_df[health_df['type'] == 'StepCount']
            >>> trend = calculator.analyze_time_series(
            ...     steps_data['startDate'],
            ...     steps_data['value']
            ... )['trend']
            >>> if trend and trend['direction'] == 'increasing':
            ...     print("Step count is trending upward - good progress!")
        """
        if len(dates) != len(values) or len(dates) < 2:
            return {'trend': None, 'seasonality': None}
        
        try:
            # Simple trend analysis using linear regression
            df = pd.DataFrame({'date': pd.to_datetime(dates), 'value': values}).dropna()
            if len(df) < 2:
                return {'trend': None, 'seasonality': None}
            
            df = df.sort_values('date')
            x = (df['date'] - df['date'].iloc[0]).dt.days
            y = df['value']
            
            # Simple linear trend
            slope = ((x * y).mean() - x.mean() * y.mean()) / (x.var() if x.var() > 0 else 1)
            
            trend_direction = 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable'
            
            return {
                'trend': {'direction': trend_direction, 'slope': slope},
                'seasonality': 'not_analyzed'  # Placeholder
            }
        except Exception:
            return {'trend': None, 'seasonality': None}
    
    def perform_statistical_tests(self, group1: pd.Series, group2: pd.Series) -> Dict:
        """Perform statistical hypothesis tests between two groups of health data.
        
        Conducts both parametric (t-test) and non-parametric (Mann-Whitney U)
        statistical tests to compare two groups. Useful for comparing health
        metrics between different time periods, devices, or conditions.
        
        Args:
            group1: First group of numeric measurements for comparison.
            group2: Second group of numeric measurements for comparison.
            
        Returns:
            Dictionary containing test results:
                - 't_test': Independent t-test results with:
                  - 'statistic': T-statistic value
                  - 'p_value': Probability value for significance testing
                - 'mann_whitney': Mann-Whitney U test results with:
                  - 'statistic': U-statistic value
                  - 'p_value': Probability value for significance testing
                  
        Examples:
            Compare heart rate between devices:
            >>> iphone_hr = health_df[
            ...     (health_df['type'] == 'HeartRate') & 
            ...     (health_df['sourceName'] == 'iPhone')
            ... ]['value']
            >>> watch_hr = health_df[
            ...     (health_df['type'] == 'HeartRate') & 
            ...     (health_df['sourceName'] == 'Apple Watch')
            ... ]['value']
            >>> tests = calculator.perform_statistical_tests(iphone_hr, watch_hr)
            >>> t_test = tests['t_test']
            >>> if t_test and t_test['p_value'] < 0.05:
            ...     print("Significant difference between device measurements")
            
            Compare step counts between seasons:
            >>> winter_steps = winter_data['value']
            >>> summer_steps = summer_data['value']
            >>> test_results = calculator.perform_statistical_tests(winter_steps, summer_steps)
            >>> mw_test = test_results['mann_whitney']
            >>> print(f"Mann-Whitney p-value: {mw_test['p_value']:.4f}")
        """
        try:
            from scipy import stats
            
            clean_group1 = group1.dropna()
            clean_group2 = group2.dropna()
            
            if len(clean_group1) < 2 or len(clean_group2) < 2:
                return {'t_test': None, 'mann_whitney': None}
            
            # Independent t-test
            t_stat, t_p = stats.ttest_ind(clean_group1, clean_group2)
            
            # Mann-Whitney U test (non-parametric alternative)
            u_stat, u_p = stats.mannwhitneyu(clean_group1, clean_group2)
            
            return {
                't_test': {'statistic': t_stat, 'p_value': t_p},
                'mann_whitney': {'statistic': u_stat, 'p_value': u_p}
            }
        except ImportError:
            # Fallback without scipy
            return {'t_test': None, 'mann_whitney': None}
    
    def calculate_confidence_interval(self, data: pd.Series, confidence: float = 0.95) -> Dict:
        """Calculate confidence interval for the population mean.
        
        Computes confidence intervals using appropriate statistical methods
        based on sample size. Uses t-distribution for small samples and
        normal approximation for large samples, with fallback calculations
        when scipy is unavailable.
        
        Args:
            data: Pandas Series containing numeric measurements.
            confidence: Confidence level (0 < confidence < 1).
                Common values: 0.90, 0.95, 0.99. Defaults to 0.95.
                
        Returns:
            Dictionary containing confidence interval:
                - 'lower': Lower bound of the confidence interval
                - 'upper': Upper bound of the confidence interval
                Returns None values if insufficient data (n < 2).
                
        Examples:
            Calculate 95% confidence interval for average steps:
            >>> step_data = health_df[health_df['type'] == 'StepCount']['value']
            >>> ci = calculator.calculate_confidence_interval(step_data)
            >>> if ci['lower'] and ci['upper']:
            ...     print(f"95% CI for average steps: [{ci['lower']:.0f}, {ci['upper']:.0f}]")
            
            Different confidence levels:
            >>> # 99% confidence interval
            >>> ci_99 = calculator.calculate_confidence_interval(data, confidence=0.99)
            >>> # 90% confidence interval  
            >>> ci_90 = calculator.calculate_confidence_interval(data, confidence=0.90)
            >>> print(f"90% CI: [{ci_90['lower']:.2f}, {ci_90['upper']:.2f}]")
            >>> print(f"99% CI: [{ci_99['lower']:.2f}, {ci_99['upper']:.2f}]")
        """
        clean_data = data.dropna()
        if len(clean_data) < 2:
            return {'lower': None, 'upper': None}
        
        try:
            from scipy import stats
            mean = clean_data.mean()
            sem = stats.sem(clean_data)  # Standard error of the mean
            
            # Calculate confidence interval
            interval = stats.t.interval(confidence, len(clean_data)-1, loc=mean, scale=sem)
            
            return {'lower': interval[0], 'upper': interval[1]}
        except ImportError:
            # Fallback calculation without scipy
            import math
            mean = clean_data.mean()
            std = clean_data.std()
            n = len(clean_data)
            
            # Use normal approximation for large samples
            if n >= 30:
                z_score = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
                margin = z_score * (std / math.sqrt(n))
            else:
                # Rough t-distribution approximation
                t_score = 2.0 if confidence == 0.95 else 2.5 if confidence == 0.99 else 1.7
                margin = t_score * (std / math.sqrt(n))
            
            return {'lower': mean - margin, 'upper': mean + margin}
    
    def bootstrap_statistics(self, data: pd.Series, statistic=None, n_bootstrap: int = 1000) -> Dict:
        """Calculate bootstrap statistics for robust statistical inference.
        
        Performs bootstrap resampling to estimate the sampling distribution
        of a statistic without making distributional assumptions. Useful for
        calculating confidence intervals and standard errors when traditional
        methods may not be appropriate.
        
        Args:
            data: Pandas Series containing numeric measurements.
            statistic: Function to calculate on each bootstrap sample.
                Defaults to numpy.mean. Can be any function that accepts
                an array and returns a scalar.
            n_bootstrap: Number of bootstrap resamples to generate.
                Defaults to 1000. Higher values provide more precise estimates.
                
        Returns:
            Dictionary containing bootstrap results:
                - 'estimate': Value of statistic on original data
                - 'confidence_interval': Dict with 'lower' and 'upper' bounds
                  (2.5th and 97.5th percentiles of bootstrap distribution)
                - 'standard_error': Standard deviation of bootstrap distribution
                
        Examples:
            Bootstrap confidence interval for mean:
            >>> step_data = health_df[health_df['type'] == 'StepCount']['value']
            >>> bootstrap_result = calculator.bootstrap_statistics(step_data)
            >>> print(f"Bootstrap mean: {bootstrap_result['estimate']:.0f}")
            >>> ci = bootstrap_result['confidence_interval']
            >>> print(f"Bootstrap 95% CI: [{ci['lower']:.0f}, {ci['upper']:.0f}]")
            
            Bootstrap for different statistics:
            >>> import numpy as np
            >>> # Bootstrap median
            >>> median_bootstrap = calculator.bootstrap_statistics(data, np.median)
            >>> # Bootstrap standard deviation
            >>> std_bootstrap = calculator.bootstrap_statistics(data, np.std)
            >>> print(f"Median 95% CI: {median_bootstrap['confidence_interval']}")
        """
        import numpy as np
        
        clean_data = data.dropna()
        if len(clean_data) < 2:
            return {'estimate': None, 'confidence_interval': None, 'standard_error': None}
        
        if statistic is None:
            statistic = np.mean
        
        # Bootstrap resampling
        bootstrap_stats = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(clean_data.values, size=len(clean_data), replace=True)
            bootstrap_stats.append(statistic(sample))
        
        bootstrap_stats = np.array(bootstrap_stats)
        
        return {
            'estimate': float(statistic(clean_data.values)),
            'confidence_interval': {
                'lower': float(np.percentile(bootstrap_stats, 2.5)),
                'upper': float(np.percentile(bootstrap_stats, 97.5))
            },
            'standard_error': float(np.std(bootstrap_stats))
        }