"""
Mock data source implementations for testing.
Implements DataSourceProtocol for type-safe testing.
"""

from typing import Optional, Tuple, List
from datetime import datetime
import pandas as pd
import numpy as np

from src.analytics.data_source_protocol import DataSourceProtocol


class MockDataSource:
    """Full mock implementation of DataSourceProtocol."""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize mock data source with a DataFrame.
        
        Args:
            data: DataFrame with columns 'creationDate', 'type', 'value'
                  Additional columns like 'date', 'sourceName', 'unit' are optional
        """
        self._data = data.copy()
        self._validate_data()
        self._prepare_data()
    
    def _validate_data(self):
        """Validate that data has required columns."""
        required_cols = {'creationDate', 'type', 'value'}
        if 'date' in self._data.columns:
            # Support both 'date' and 'creationDate' for flexibility
            if 'creationDate' not in self._data.columns:
                self._data['creationDate'] = pd.to_datetime(self._data['date'])
        
        missing = required_cols - set(self._data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    def _prepare_data(self):
        """Prepare data with proper types."""
        # Ensure creationDate is datetime
        if not pd.api.types.is_datetime64_any_dtype(self._data['creationDate']):
            self._data['creationDate'] = pd.to_datetime(self._data['creationDate'])
        
        # Ensure value is numeric
        if not pd.api.types.is_numeric_dtype(self._data['value']):
            self._data['value'] = pd.to_numeric(self._data['value'], errors='coerce')
        
        # Add date column if not present (for daily aggregation)
        if 'date' not in self._data.columns:
            self._data['date'] = self._data['creationDate'].dt.date
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return full dataset as DataFrame."""
        return self._data.copy()
    
    def get_data_for_period(self, metric: str, start_date: datetime, end_date: datetime) -> pd.Series:
        """
        Get specific metric data for date range.
        
        Args:
            metric: Metric type to filter for
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Series with date index and values
        """
        mask = (
            (self._data['creationDate'] >= start_date) & 
            (self._data['creationDate'] <= end_date) &
            (self._data['type'] == metric)
        )
        filtered = self._data.loc[mask, ['creationDate', 'value']].copy()
        
        if filtered.empty:
            return pd.Series(dtype=float)
        
        # Set date as index
        filtered.set_index('creationDate', inplace=True)
        return filtered['value']
    
    def get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Return the date range of available data."""
        if self._data.empty:
            return None
        
        valid_dates = self._data['creationDate'].dropna()
        if valid_dates.empty:
            return None
        
        return (valid_dates.min(), valid_dates.max())
    
    def get_available_metrics(self) -> List[str]:
        """List all available metric types."""
        if self._data.empty:
            return []
        
        return self._data['type'].dropna().unique().tolist()


class EmptyDataSource(MockDataSource):
    """Mock data source with no data for edge case testing."""
    
    def __init__(self):
        """Initialize empty data source."""
        empty_df = pd.DataFrame(columns=['creationDate', 'type', 'value'])
        super().__init__(empty_df)


class LargeDataSource(MockDataSource):
    """Mock data source with large dataset for performance testing."""
    
    def __init__(self, days: int = 365, metrics: Optional[List[str]] = None):
        """
        Initialize large data source.
        
        Args:
            days: Number of days of data to generate
            metrics: List of metric types (default: common health metrics)
        """
        if metrics is None:
            metrics = [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'HKQuantityTypeIdentifierActiveEnergyBurned',
                'HKQuantityTypeIdentifierHeartRate'
            ]
        
        # Generate large dataset
        data = []
        base_date = datetime.now()
        
        for day in range(days):
            current_date = base_date - pd.Timedelta(days=day)
            
            for metric in metrics:
                # Multiple readings per day for some metrics
                readings_per_day = 24 if metric == 'HKQuantityTypeIdentifierHeartRate' else 1
                
                for hour in range(readings_per_day):
                    timestamp = current_date.replace(hour=hour % 24)
                    value = self._generate_value(metric, day, hour)
                    
                    data.append({
                        'creationDate': timestamp,
                        'type': metric,
                        'value': value,
                        'sourceName': 'Mock Device',
                        'unit': self._get_unit(metric)
                    })
        
        df = pd.DataFrame(data)
        super().__init__(df)
    
    def _generate_value(self, metric: str, day: int, hour: int) -> float:
        """Generate realistic values for metrics."""
        np.random.seed(day * 24 + hour)  # Reproducible randomness
        
        base_values = {
            'HKQuantityTypeIdentifierStepCount': 8000,
            'HKQuantityTypeIdentifierDistanceWalkingRunning': 5.0,
            'HKQuantityTypeIdentifierActiveEnergyBurned': 500,
            'HKQuantityTypeIdentifierHeartRate': 70
        }
        
        base = base_values.get(metric, 100)
        
        # Add daily variation
        daily_factor = 1.0 + 0.2 * np.sin(2 * np.pi * day / 7)  # Weekly pattern
        
        # Add hourly variation for heart rate
        if metric == 'HKQuantityTypeIdentifierHeartRate':
            hourly_factor = 1.0 + 0.1 * np.sin(2 * np.pi * hour / 24)
        else:
            hourly_factor = 1.0
        
        # Add random noise
        noise = np.random.normal(1.0, 0.1)
        
        return max(0, base * daily_factor * hourly_factor * noise)
    
    def _get_unit(self, metric: str) -> str:
        """Get unit for metric type."""
        units = {
            'HKQuantityTypeIdentifierStepCount': 'count',
            'HKQuantityTypeIdentifierDistanceWalkingRunning': 'km',
            'HKQuantityTypeIdentifierActiveEnergyBurned': 'Cal',
            'HKQuantityTypeIdentifierHeartRate': 'count/min'
        }
        return units.get(metric, 'unknown')


class CorruptDataSource(MockDataSource):
    """Mock data source with corrupted data for error handling testing."""
    
    def __init__(self):
        """Initialize corrupt data source."""
        # Create data with various issues
        data = pd.DataFrame({
            'creationDate': [
                '2024-01-01',
                'invalid_date',
                '2024-01-03',
                None,
                '2024-01-05'
            ],
            'type': [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierStepCount',
                None,  # Missing type
                'HKQuantityTypeIdentifierHeartRate',
                'HKQuantityTypeIdentifierStepCount'
            ],
            'value': [
                1000,
                'not_a_number',  # Invalid value
                2000,
                -50,  # Negative heart rate
                None  # Missing value
            ]
        })
        
        # Initialize without validation to keep corrupt data
        self._data = data
        
        # Attempt to prepare data (will handle errors)
        try:
            self._prepare_data()
        except Exception:
            pass  # Allow corrupt data for testing
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return corrupt data as-is."""
        return self._data.copy()