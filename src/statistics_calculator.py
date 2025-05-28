"""
Basic statistics calculator for health data.
Provides record counts, date ranges, and aggregations by type and source.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict


@dataclass
class BasicStatistics:
    """Container for basic health data statistics."""
    total_records: int
    date_range: Tuple[datetime, datetime]  # (earliest, latest)
    records_by_type: Dict[str, int]
    records_by_source: Dict[str, int]
    types_by_source: Dict[str, List[str]]  # source -> list of types
    
    def to_dict(self) -> dict:
        """Convert statistics to dictionary for serialization."""
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
    """Calculates basic statistics on health data."""
    
    def __init__(self, data_loader=None):
        """
        Initialize the calculator.
        
        Args:
            data_loader: DataLoader instance for database queries
        """
        self.data_loader = data_loader
    
    def calculate_from_dataframe(self, df: pd.DataFrame) -> BasicStatistics:
        """
        Calculate statistics from a pandas DataFrame.
        
        Args:
            df: DataFrame with columns: creationDate, type, sourceName, value
            
        Returns:
            BasicStatistics object with calculated values
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
            df['creationDate'] = pd.to_datetime(df['creationDate'], format='mixed', utc=True)
            date_range = (df['creationDate'].min(), df['creationDate'].max())
        except Exception as e:
            # If date parsing fails, try without format specification
            try:
                df['creationDate'] = pd.to_datetime(df['creationDate'], utc=True)
                date_range = (df['creationDate'].min(), df['creationDate'].max())
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
        """
        Calculate statistics from database with optional filters.
        
        Note: This method requires a DataLoader with database query capabilities.
        Currently, the DataLoader loads all records and filtering is done in memory.
        
        Args:
            start_date: Filter records after this date
            end_date: Filter records before this date
            types: Filter to specific record types
            sources: Filter to specific sources
            
        Returns:
            BasicStatistics object with calculated values
        """
        if not self.data_loader:
            raise ValueError("DataLoader not provided")
        
        # Load all records and filter in memory
        # This is less efficient than database filtering but works with current DataLoader
        try:
            df = self.data_loader.get_all_records()
            
            # Apply filters if provided
            if start_date:
                df = df[df['creationDate'] >= start_date]
            
            if end_date:
                df = df[df['creationDate'] <= end_date]
            
            if types:
                df = df[df['type'].isin(types)]
            
            if sources:
                df = df[df['sourceName'].isin(sources)]
            
            return self.calculate_from_dataframe(df)
            
        except Exception as e:
            raise ValueError(f"Failed to calculate statistics from database: {e}")
    
    def get_quick_summary(self, stats: BasicStatistics) -> str:
        """
        Generate a human-readable summary of the statistics.
        
        Args:
            stats: BasicStatistics object
            
        Returns:
            Formatted string summary
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
        """Calculate comprehensive descriptive statistics."""
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
        """Calculate correlation matrix for numeric columns."""
        numeric_cols = df.select_dtypes(include=[float, int]).columns
        if len(numeric_cols) < 2:
            return pd.DataFrame()
        return df[numeric_cols].corr()
    
    def analyze_distribution(self, data: pd.Series) -> Dict:
        """Analyze data distribution characteristics."""
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
        """Basic time series analysis."""
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
        """Perform basic statistical tests between two groups."""
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
        """Calculate confidence interval for the mean."""
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
        """Calculate bootstrap statistics."""
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