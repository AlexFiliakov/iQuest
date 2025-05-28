"""
Synthetic data generator for analytics test suite.
Provides realistic fake health data for comprehensive testing.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random

# Import faker with fallback
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False


class HealthDataPatterns:
    """Generates realistic health data patterns."""
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        if FAKER_AVAILABLE:
            self.fake = Faker()
            if seed:
                Faker.seed(seed)
        else:
            self.fake = None

    def generate_steps_pattern(self, days: int, base_avg: int = 8000) -> np.ndarray:
        """Generate realistic step count patterns with weekly cycles."""
        dates = np.arange(days)
        
        # Base pattern with weekly cycle (lower on weekends)
        weekly_pattern = base_avg + 2000 * np.sin(dates * 2 * np.pi / 7)
        
        # Add daily variation
        daily_variation = np.random.normal(0, 1000, days)
        
        # Weekend pattern (higher weekend activity for some people)
        weekend_mask = np.array([i % 7 in [5, 6] for i in range(days)])
        weekend_boost = weekend_mask * np.random.normal(1500, 800, days)
        
        # Seasonal trend (slightly more active in summer)
        seasonal_trend = 500 * np.sin(dates * 2 * np.pi / 365.25 + np.pi/2)
        
        # Combine all patterns
        steps = weekly_pattern + daily_variation + weekend_boost + seasonal_trend
        
        # Add occasional "lazy days" and "very active days"
        outlier_mask = np.random.random(days) < 0.05
        outlier_mult = np.where(
            np.random.random(days) < 0.5, 
            np.random.uniform(0.2, 0.5, days),  # Lazy days
            np.random.uniform(1.8, 3.0, days)   # Very active days
        )
        steps = np.where(outlier_mask, steps * outlier_mult, steps)
        
        return np.clip(steps, 0, 50000).astype(int)

    def generate_heart_rate_pattern(self, days: int, resting_hr: int = 65) -> np.ndarray:
        """Generate realistic heart rate patterns."""
        # Resting heart rate with small daily variations
        base_hr = resting_hr + np.random.normal(0, 3, days)
        
        # Add stress/activity spikes (5-10% of days)
        spike_mask = np.random.random(days) < 0.07
        spikes = np.where(spike_mask, np.random.uniform(15, 40, days), 0)
        
        # Gradual fitness improvements over time
        fitness_trend = -0.01 * np.arange(days)  # Slight HR decrease over time
        
        heart_rate = base_hr + spikes + fitness_trend
        return np.clip(heart_rate, 40, 200).astype(int)

    def generate_sleep_pattern(self, days: int, avg_hours: float = 7.5) -> np.ndarray:
        """Generate realistic sleep duration patterns."""
        # Base sleep with weekend variation
        base_sleep = avg_hours + np.random.normal(0, 0.8, days)
        
        # Weekend pattern (slightly more sleep)
        weekend_mask = np.array([i % 7 in [5, 6] for i in range(days)])
        weekend_bonus = weekend_mask * np.random.normal(0.5, 0.3, days)
        
        # Occasional insomnia or oversleep
        extreme_mask = np.random.random(days) < 0.08
        extreme_sleep = np.where(
            np.random.random(days) < 0.3,
            np.random.uniform(3, 5, days),    # Insomnia
            np.random.uniform(9, 11, days)    # Oversleep
        )
        
        sleep = np.where(extreme_mask, extreme_sleep, base_sleep + weekend_bonus)
        return np.clip(sleep, 2, 12)

    def generate_exercise_pattern(self, days: int) -> np.ndarray:
        """Generate realistic exercise minutes per day."""
        # Most days have little to no exercise
        base_exercise = np.random.exponential(15, days)
        
        # 20% of days have intentional exercise
        exercise_days = np.random.random(days) < 0.2
        intentional_exercise = np.random.gamma(2, 20, days)  # 20-60 min typical
        
        exercise = np.where(exercise_days, intentional_exercise, base_exercise)
        return np.clip(exercise, 0, 180).astype(int)


class HealthDataGenerator:
    """Main test data generator for analytics test suite."""
    
    def __init__(self, seed: Optional[int] = None):
        self.patterns = HealthDataPatterns(seed)
        if FAKER_AVAILABLE:
            self.fake = Faker()
            if seed:
                Faker.seed(seed)
        else:
            self.fake = None

    def generate_synthetic_data(self, days: int = 365) -> pd.DataFrame:
        """Generate realistic synthetic health data."""
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days-1)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = {
            'date': dates,
            'steps': self.patterns.generate_steps_pattern(days),
            'heart_rate_avg': self.patterns.generate_heart_rate_pattern(days),
            'sleep_hours': self.patterns.generate_sleep_pattern(days),
            'exercise_minutes': self.patterns.generate_exercise_pattern(days)
        }
        
        # Add derived metrics
        df = pd.DataFrame(data)
        df['active_energy'] = (df['steps'] * 0.04 + df['exercise_minutes'] * 8).astype(int)
        df['day_of_week'] = df['date'].dt.dayofweek
        df['weekend'] = df['day_of_week'].isin([5, 6])
        df['month'] = df['date'].dt.month
        
        return df

    def generate_edge_cases(self) -> Dict[str, pd.DataFrame]:
        """Generate edge case datasets for chaos testing."""
        return {
            'all_zeros': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=30),
                'steps': [0] * 30,
                'heart_rate_avg': [0] * 30,
                'sleep_hours': [0] * 30
            }),
            
            'all_nulls': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=30),
                'steps': [None] * 30,
                'heart_rate_avg': [None] * 30,
                'sleep_hours': [None] * 30
            }),
            
            'single_point': pd.DataFrame({
                'date': [datetime(2024, 1, 1)],
                'steps': [10000],
                'heart_rate_avg': [72],
                'sleep_hours': [8.0]
            }),
            
            'extreme_values': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'steps': [1e6, -1000, 0, 100000, 1, 999999, 50000, 0, 1e5, 75000],
                'heart_rate_avg': [300, -50, 0, 250, 20, 400, 80, 60, 500, 70],
                'sleep_hours': [50, -10, 0, 25, 0.1, 48, 8, 7, 100, 6]
            }),
            
            'missing_dates': pd.DataFrame({
                'date': [
                    datetime(2024, 1, 1),
                    datetime(2024, 1, 5),  # Gap
                    datetime(2024, 1, 6),
                    datetime(2024, 1, 10)  # Gap
                ],
                'steps': [8000, 9000, 7500, 8500],
                'heart_rate_avg': [70, 72, 68, 71],
                'sleep_hours': [7.5, 8.0, 7.0, 7.8]
            }),
            
            'duplicate_dates': pd.DataFrame({
                'date': [
                    datetime(2024, 1, 1),
                    datetime(2024, 1, 1),  # Duplicate
                    datetime(2024, 1, 2),
                    datetime(2024, 1, 2)   # Duplicate
                ],
                'steps': [8000, 9000, 7500, 8500],
                'heart_rate_avg': [70, 72, 68, 71],
                'sleep_hours': [7.5, 8.0, 7.0, 7.8]
            }),
            
            'perfect_correlation': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=100),
                'steps': range(100),
                'heart_rate_avg': range(100),  # Perfect correlation
                'sleep_hours': [x/10 for x in range(100)]
            }),
            
            'no_correlation': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=100),
                'steps': np.random.random(100) * 20000,
                'heart_rate_avg': np.random.random(100) * 100 + 50,
                'sleep_hours': np.random.random(100) * 10 + 4
            })
        }

    def generate_performance_data(self, size: str = 'large') -> pd.DataFrame:
        """Generate large datasets for performance testing."""
        sizes = {
            'small': 1000,      # 1K records
            'medium': 10000,    # 10K records
            'large': 100000,    # 100K records
            'xlarge': 1000000   # 1M records
        }
        
        days = sizes.get(size, 100000)
        return self.generate(days)

    def generate_anonymized_sample(self, original_patterns: Dict) -> pd.DataFrame:
        """Generate anonymized data that preserves statistical patterns."""
        # This would use differential privacy techniques in production
        # For testing, we'll create realistic data with similar statistical properties
        
        if 'steps_mean' in original_patterns:
            steps_avg = int(original_patterns['steps_mean'])
        else:
            steps_avg = 8000
            
        days = original_patterns.get('days', 365)
        
        # Generate data with similar statistical properties
        data = self.generate(days)
        
        # Adjust to match original patterns
        if 'steps_mean' in original_patterns:
            current_mean = data['steps'].mean()
            adjustment = steps_avg - current_mean
            data['steps'] = (data['steps'] + adjustment).clip(0, 50000)
        
        return data

    def create_test_database_data(self) -> Dict[str, pd.DataFrame]:
        """Create comprehensive test data for database operations."""
        return {
            'normal_year': self.generate(365),
            'leap_year': self.generate(366),
            'partial_year': self.generate(90),
            'multi_year': self.generate(365 * 3),
            'stress_test': self.generate_performance_data('large')
        }