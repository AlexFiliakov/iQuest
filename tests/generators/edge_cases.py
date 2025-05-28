"""
Edge case data generator for testing boundary conditions.
"""

from typing import Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base import BaseDataGenerator
from ..fixtures.health_fixtures import HealthDataFixtures


class EdgeCaseGenerator(BaseDataGenerator):
    """Generate edge case data for testing."""
    
    def generate(self, **kwargs):
        """Generate edge case data based on parameters."""
        # Default implementation returns all edge case datasets
        return self.generate_edge_case_datasets()
    
    def generate_empty_periods(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add empty periods to data."""
        # Add week-long gaps
        gap_start = len(df) // 2
        gap_end = gap_start + 7
        df.iloc[gap_start:gap_end] = np.nan
        return df
    
    def generate_outliers(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Add statistical outliers."""
        mean = df[metric].mean()
        std = df[metric].std()
        
        # Add some extreme values
        outlier_indices = self.rng.choice(
            len(df), size=int(len(df) * 0.02), replace=False
        )
        for idx in outlier_indices:
            # Create outlier 3-5 std deviations away
            multiplier = self.rng.uniform(3, 5)
            if self.rng.random() > 0.5:
                df.loc[df.index[idx], metric] = mean + multiplier * std
            else:
                df.loc[df.index[idx], metric] = max(0, mean - multiplier * std)
        
        return df
    
    def generate_corrupted_data(self) -> pd.DataFrame:
        """Generate data with various corruption types."""
        df = HealthDataFixtures.create_health_dataframe()
        
        # Add different types of corruption
        # 1. Duplicate timestamps
        df = pd.concat([df, df.iloc[10:15]])
        
        # 2. Negative values
        df.iloc[20:25, 0] = -100
        
        # 3. Missing required columns
        if 'date' in df.columns:
            df = df.drop('date', axis=1)
        
        return df
    
    def generate_edge_case_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate comprehensive edge case datasets."""
        base_date = datetime(2024, 1, 1)
        
        return {
            'all_zeros': pd.DataFrame({
                'date': pd.date_range(base_date, periods=30),
                'steps': [0] * 30,
                'heart_rate': [0] * 30,
                'sleep_hours': [0] * 30,
                'calories': [0] * 30
            }),
            
            'all_nulls': pd.DataFrame({
                'date': pd.date_range(base_date, periods=30),
                'steps': [None] * 30,
                'heart_rate': [None] * 30,
                'sleep_hours': [None] * 30,
                'calories': [None] * 30
            }),
            
            'single_point': pd.DataFrame({
                'date': [base_date],
                'steps': [10000],
                'heart_rate': [72],
                'sleep_hours': [8.0],
                'calories': [2000]
            }),
            
            'extreme_values': pd.DataFrame({
                'date': pd.date_range(base_date, periods=10),
                'steps': [1e6, -1000, 0, 100000, 1, 999999, 50000, 0, 1e5, 75000],
                'heart_rate': [300, -50, 0, 250, 20, 400, 80, 60, 500, 70],
                'sleep_hours': [50, -10, 0, 25, 0.1, 48, 8, 7, 100, 6],
                'calories': [10000, -500, 0, 8000, 10, 15000, 2000, 1800, 20000, 2200]
            }),
            
            'missing_dates': pd.DataFrame({
                'date': [
                    base_date,
                    base_date + timedelta(days=4),  # Gap
                    base_date + timedelta(days=5),
                    base_date + timedelta(days=9)   # Gap
                ],
                'steps': [8000, 9000, 7500, 8500],
                'heart_rate': [70, 72, 68, 71],
                'sleep_hours': [7.5, 8.0, 7.0, 7.8],
                'calories': [2000, 2100, 1950, 2050]
            }),
            
            'duplicate_dates': pd.DataFrame({
                'date': [
                    base_date,
                    base_date,  # Duplicate
                    base_date + timedelta(days=1),
                    base_date + timedelta(days=1)  # Duplicate
                ],
                'steps': [8000, 9000, 7500, 8500],
                'heart_rate': [70, 72, 68, 71],
                'sleep_hours': [7.5, 8.0, 7.0, 7.8],
                'calories': [2000, 2100, 1950, 2050]
            }),
            
            'perfect_correlation': pd.DataFrame({
                'date': pd.date_range(base_date, periods=100),
                'steps': range(100),
                'heart_rate': range(100),  # Perfect correlation
                'sleep_hours': [x/10 for x in range(100)],
                'calories': [x*20 for x in range(100)]
            }),
            
            'no_correlation': pd.DataFrame({
                'date': pd.date_range(base_date, periods=100),
                'steps': self.rng.random(100) * 20000,
                'heart_rate': self.rng.random(100) * 100 + 50,
                'sleep_hours': self.rng.random(100) * 10 + 4,
                'calories': self.rng.random(100) * 3000 + 1000
            }),
            
            'monotonic_increase': pd.DataFrame({
                'date': pd.date_range(base_date, periods=30),
                'steps': [1000 + i * 100 for i in range(30)],
                'heart_rate': [60 + i for i in range(30)],
                'sleep_hours': [6.0 + i * 0.1 for i in range(30)],
                'calories': [1500 + i * 50 for i in range(30)]
            }),
            
            'cyclic_pattern': pd.DataFrame({
                'date': pd.date_range(base_date, periods=30),
                'steps': [8000 + 2000 * np.sin(2 * np.pi * i / 7) for i in range(30)],
                'heart_rate': [70 + 10 * np.sin(2 * np.pi * i / 7) for i in range(30)],
                'sleep_hours': [7.5 + 1.5 * np.sin(2 * np.pi * i / 7) for i in range(30)],
                'calories': [2000 + 500 * np.sin(2 * np.pi * i / 7) for i in range(30)]
            })
        }