"""
Time series data generator with realistic patterns.
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from .base import BaseDataGenerator
from .health_data import HealthMetricGenerator


class TimeSeriesGenerator(BaseDataGenerator):
    """Generate time series data with realistic patterns."""
    
    def generate(self, **kwargs):
        """Generate data based on parameters."""
        # Default implementation delegates to generate_series
        return self.generate_series(**kwargs)
    
    def generate_series(
        self,
        start_date: datetime,
        end_date: datetime,
        metrics: List[str],
        frequency: str = 'D',
        include_gaps: bool = False,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """Generate correlated time series data."""
        
        dates = pd.date_range(start_date, end_date, freq=frequency)
        n_points = len(dates)
        n_metrics = len(metrics)
        
        # Generate base data
        if correlation_matrix is not None:
            # Generate correlated data
            mean = np.zeros(n_metrics)
            data = self.rng.multivariate_normal(
                mean, correlation_matrix, n_points
            )
        else:
            # Independent data
            data = self.rng.standard_normal((n_points, n_metrics))
        
        # Apply metric-specific transformations
        df_data = {}
        for i, metric in enumerate(metrics):
            generator = HealthMetricGenerator(seed=self.rng.integers(1000))
            values = []
            for j, date in enumerate(dates):
                base_value = generator.generate(metric, date)
                # Scale by generated data
                scaled_value = base_value * (1 + 0.1 * data[j, i])
                values.append(scaled_value)
            df_data[metric] = values
        
        df = pd.DataFrame(df_data, index=dates)
        
        # Add gaps if requested
        if include_gaps:
            df = self._add_realistic_gaps(df)
        
        return df
    
    def _add_realistic_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic data gaps (device not worn, etc)."""
        gap_probability = 0.05
        for col in df.columns:
            mask = self.rng.random(len(df)) < gap_probability
            df.loc[mask, col] = np.nan
        return df
    
    def generate_with_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        metric: str,
        trend_type: str = 'linear',
        trend_strength: float = 0.1
    ) -> pd.Series:
        """Generate time series with specific trend patterns."""
        dates = pd.date_range(start_date, end_date, freq='D')
        n_points = len(dates)
        
        # Generate base data
        generator = HealthMetricGenerator(seed=self.rng.integers(1000))
        base_values = [generator.generate(metric, date) for date in dates]
        
        # Apply trend
        if trend_type == 'linear':
            trend = np.linspace(0, trend_strength, n_points)
        elif trend_type == 'exponential':
            trend = np.exp(np.linspace(0, trend_strength, n_points)) - 1
        elif trend_type == 'seasonal':
            # Annual seasonal pattern
            trend = trend_strength * np.sin(2 * np.pi * np.arange(n_points) / 365.25)
        elif trend_type == 'cyclic':
            # Monthly cycle
            trend = trend_strength * np.sin(2 * np.pi * np.arange(n_points) / 30)
        else:
            trend = np.zeros(n_points)
        
        # Apply trend to base values
        values = base_values * (1 + trend)
        
        return pd.Series(values, index=dates, name=metric)
    
    def generate_anomalous_series(
        self,
        start_date: datetime,
        end_date: datetime,
        metric: str,
        anomaly_rate: float = 0.02,
        anomaly_severity: float = 3.0
    ) -> pd.Series:
        """Generate time series with anomalies."""
        # Get base series
        series = self.generate_with_trends(start_date, end_date, metric)
        
        # Add anomalies
        n_points = len(series)
        anomaly_mask = self.rng.random(n_points) < anomaly_rate
        n_anomalies = anomaly_mask.sum()
        
        if n_anomalies > 0:
            # Generate anomaly magnitudes
            anomaly_signs = self.rng.choice([-1, 1], size=n_anomalies)
            anomaly_magnitudes = self.rng.exponential(anomaly_severity, size=n_anomalies)
            
            # Apply anomalies
            mean_val = series.mean()
            std_val = series.std()
            anomaly_values = mean_val + anomaly_signs * anomaly_magnitudes * std_val
            
            # Ensure reasonable bounds
            anomaly_values = np.clip(anomaly_values, 0, mean_val * 5)
            series[anomaly_mask] = anomaly_values
        
        return series