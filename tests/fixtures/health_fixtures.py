"""
Centralized fixture factory for health data tests.
"""

import pytest
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..generators.time_series import TimeSeriesGenerator


class HealthDataFixtures:
    """Factory for creating test data fixtures."""
    
    @staticmethod
    def create_user_profile(
        age: int = 35,
        gender: str = 'male',
        fitness_level: str = 'moderate',
        **kwargs
    ) -> Dict[str, Any]:
        """Create user profile for data generation."""
        return {
            'age': age,
            'gender': gender,
            'fitness_level': fitness_level,
            'activity_multiplier': {
                'sedentary': 0.7,
                'moderate': 1.0,
                'active': 1.3,
                'athlete': 1.6
            }.get(fitness_level, 1.0),
            **kwargs
        }
    
    @staticmethod
    def create_health_dataframe(
        days: int = 30,
        metrics: Optional[List[str]] = None,
        user_profile: Optional[Dict] = None,
        include_anomalies: bool = False
    ) -> pd.DataFrame:
        """Create health data DataFrame."""
        if metrics is None:
            metrics = ['steps', 'distance', 'calories', 'heart_rate']
        
        generator = TimeSeriesGenerator()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create correlation matrix for realistic data
        correlation = HealthDataFixtures._get_correlation_matrix(metrics)
        
        df = generator.generate_series(
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            correlation_matrix=correlation
        )
        
        if include_anomalies:
            df = HealthDataFixtures._add_anomalies(df)
        
        return df
    
    @staticmethod
    def _get_correlation_matrix(metrics: List[str]) -> np.ndarray:
        """Get realistic correlation matrix for metrics."""
        n = len(metrics)
        corr = np.eye(n)
        
        # Define known correlations
        correlations = {
            ('steps', 'distance'): 0.95,
            ('steps', 'calories'): 0.85,
            ('distance', 'calories'): 0.80,
            ('heart_rate', 'calories'): 0.60,
            ('exercise_minutes', 'calories'): 0.70,
            ('exercise_minutes', 'heart_rate'): 0.50
        }
        
        for i, metric1 in enumerate(metrics):
            for j, metric2 in enumerate(metrics):
                if i != j:
                    key = tuple(sorted([metric1, metric2]))
                    if key in correlations:
                        corr[i, j] = correlations[key]
                        corr[j, i] = correlations[key]
        
        return corr
    
    @staticmethod
    def _add_anomalies(df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic anomalies to data."""
        rng = np.random.default_rng()
        
        # Add different types of anomalies
        for col in df.columns:
            # Point anomalies (2% of data)
            anomaly_mask = rng.random(len(df)) < 0.02
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            # Generate anomaly values
            anomaly_values = mean_val + rng.choice([-1, 1], anomaly_mask.sum()) * rng.uniform(2, 4, anomaly_mask.sum()) * std_val
            anomaly_values = np.clip(anomaly_values, 0, mean_val * 5)
            
            df.loc[anomaly_mask, col] = anomaly_values
        
        return df
    
    @staticmethod
    def create_sample_datasets() -> Dict[str, pd.DataFrame]:
        """Create a collection of sample datasets for different test scenarios."""
        return {
            'small': HealthDataFixtures.create_health_dataframe(days=7),
            'medium': HealthDataFixtures.create_health_dataframe(days=30),
            'large': HealthDataFixtures.create_health_dataframe(days=365),
            'with_anomalies': HealthDataFixtures.create_health_dataframe(
                days=30, include_anomalies=True
            ),
            'athlete': HealthDataFixtures.create_health_dataframe(
                days=30,
                user_profile=HealthDataFixtures.create_user_profile(
                    age=25, fitness_level='athlete'
                )
            ),
            'sedentary': HealthDataFixtures.create_health_dataframe(
                days=30,
                user_profile=HealthDataFixtures.create_user_profile(
                    age=55, fitness_level='sedentary'
                )
            )
        }