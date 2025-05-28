"""
Centralized fixture factory for creating test data.
Provides consistent, realistic health data for testing.
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np

from tests.mocks.data_sources import MockDataSource, EmptyDataSource, LargeDataSource


class FixtureFactory:
    """Factory for creating standardized test fixtures."""
    
    @staticmethod
    def create_health_data(
        days: int = 365,
        metrics: Optional[List[str]] = None,
        start_date: Optional[Union[datetime, date]] = None,
        include_gaps: bool = False,
        include_anomalies: bool = False
    ) -> pd.DataFrame:
        """
        Generate realistic health data.
        
        Args:
            days: Number of days of data to generate
            metrics: List of metric types (default: common metrics)
            start_date: Starting date for data (default: days ago from now)
            include_gaps: Whether to include missing data gaps
            include_anomalies: Whether to include anomalous values
            
        Returns:
            DataFrame with health data
        """
        if metrics is None:
            metrics = [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'HKQuantityTypeIdentifierActiveEnergyBurned'
            ]
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        elif isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        
        data = []
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Skip some days if gaps requested
            if include_gaps and np.random.random() < 0.05:
                continue
            
            for metric in metrics:
                value = FixtureFactory._generate_value(metric, day)
                
                # Add anomalies if requested
                if include_anomalies and np.random.random() < 0.02:
                    value = value * np.random.uniform(0.1, 3.0)
                
                data.append({
                    'creationDate': current_date,
                    'type': metric,
                    'value': value,
                    'sourceName': 'iPhone',
                    'unit': FixtureFactory._get_unit(metric),
                    'date': current_date.date()  # Include date column
                })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def _generate_value(metric: str, day: int) -> float:
        """Generate realistic values with patterns."""
        base_values = {
            'HKQuantityTypeIdentifierStepCount': 8000,
            'HKQuantityTypeIdentifierDistanceWalkingRunning': 5.0,
            'HKQuantityTypeIdentifierActiveEnergyBurned': 500,
            'HKQuantityTypeIdentifierHeartRate': 70,
            'HKQuantityTypeIdentifierFlightsClimbed': 10,
            'HKQuantityTypeIdentifierAppleExerciseTime': 30
        }
        
        base = base_values.get(metric, 100)
        
        # Add weekly pattern (higher on weekdays)
        day_of_week = day % 7
        if day_of_week < 5:  # Weekday
            weekly_factor = 1.1
        else:  # Weekend
            weekly_factor = 0.9
        
        # Add seasonal pattern
        seasonal_factor = 1.0 + 0.2 * np.sin(2 * np.pi * day / 365)
        
        # Add random variation
        random_factor = np.random.normal(1.0, 0.15)
        
        # Ensure non-negative
        value = base * weekly_factor * seasonal_factor * random_factor
        return max(0, value)
    
    @staticmethod
    def _get_unit(metric: str) -> str:
        """Get appropriate unit for metric."""
        units = {
            'HKQuantityTypeIdentifierStepCount': 'count',
            'HKQuantityTypeIdentifierDistanceWalkingRunning': 'km',
            'HKQuantityTypeIdentifierActiveEnergyBurned': 'Cal',
            'HKQuantityTypeIdentifierHeartRate': 'count/min',
            'HKQuantityTypeIdentifierFlightsClimbed': 'count',
            'HKQuantityTypeIdentifierAppleExerciseTime': 'min'
        }
        return units.get(metric, 'unknown')
    
    @staticmethod
    def create_data_source(
        days: int = 30,
        metrics: Optional[List[str]] = None,
        **kwargs
    ) -> MockDataSource:
        """
        Create a MockDataSource with health data.
        
        Args:
            days: Number of days of data
            metrics: List of metrics to include
            **kwargs: Additional arguments for create_health_data
            
        Returns:
            MockDataSource instance
        """
        data = FixtureFactory.create_health_data(days, metrics, **kwargs)
        return MockDataSource(data)
    
    @staticmethod
    def create_weekly_data() -> pd.DataFrame:
        """Create exactly one week of health data for weekly calculations."""
        start_date = datetime.now() - timedelta(days=7)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        data = []
        metrics = ['HKQuantityTypeIdentifierStepCount', 'HKQuantityTypeIdentifierActiveEnergyBurned']
        
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            
            for metric in metrics:
                base_value = 8000 if metric == 'HKQuantityTypeIdentifierStepCount' else 500
                # Add some variation
                value = base_value * (1 + np.random.uniform(-0.2, 0.2))
                
                data.append({
                    'creationDate': current_date,
                    'type': metric,
                    'value': value,
                    'sourceName': 'iPhone',
                    'unit': FixtureFactory._get_unit(metric),
                    'date': current_date.date()
                })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def create_monthly_data() -> pd.DataFrame:
        """Create exactly one month of health data for monthly calculations."""
        start_date = datetime.now().replace(day=1) - timedelta(days=30)
        
        return FixtureFactory.create_health_data(
            days=30,
            start_date=start_date,
            metrics=['HKQuantityTypeIdentifierStepCount', 'HKQuantityTypeIdentifierActiveEnergyBurned']
        )
    
    @staticmethod
    def create_year_data() -> pd.DataFrame:
        """Create one year of health data for long-term analysis."""
        return FixtureFactory.create_health_data(
            days=365,
            metrics=[
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'HKQuantityTypeIdentifierActiveEnergyBurned',
                'HKQuantityTypeIdentifierHeartRate'
            ]
        )


# Pytest fixtures using the factory
@pytest.fixture
def health_data():
    """Standard health data for testing (30 days)."""
    return FixtureFactory.create_health_data(days=30)


@pytest.fixture
def mock_data_source(health_data):
    """Mock data source with health data."""
    return MockDataSource(health_data)


@pytest.fixture
def daily_calculator(mock_data_source):
    """Daily metrics calculator with mock data."""
    from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
    # DailyMetricsCalculator accepts DataSourceProtocol implementations
    return DailyMetricsCalculator(mock_data_source)


@pytest.fixture
def weekly_calculator(daily_calculator):
    """Weekly metrics calculator with daily calculator."""
    from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
    return WeeklyMetricsCalculator(daily_calculator)


@pytest.fixture
def monthly_calculator(daily_calculator):
    """Monthly metrics calculator with daily calculator."""
    from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
    return MonthlyMetricsCalculator(daily_calculator)


@pytest.fixture
def empty_data_source():
    """Empty data source for edge case testing."""
    return EmptyDataSource()


@pytest.fixture
def large_data_source():
    """Large data source for performance testing."""
    return LargeDataSource(days=365)


@pytest.fixture
def weekly_health_data():
    """One week of health data."""
    return FixtureFactory.create_weekly_data()


@pytest.fixture
def monthly_health_data():
    """One month of health data."""
    return FixtureFactory.create_monthly_data()


@pytest.fixture
def yearly_health_data():
    """One year of health data."""
    return FixtureFactory.create_year_data()