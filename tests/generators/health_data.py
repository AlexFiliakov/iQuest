"""
Health-specific data generators for Apple Health Monitor tests.
"""

from typing import Dict, Optional
from datetime import datetime
from .base import BaseDataGenerator


class HealthMetricGenerator(BaseDataGenerator):
    """Generate realistic health metric data."""
    
    METRIC_CONFIGS = {
        'steps': {
            'base': 8000,
            'variance': 3000,
            'weekly_pattern': True,
            'seasonal_pattern': True
        },
        'heart_rate': {
            'base': 70,
            'variance': 15,
            'activity_based': True
        },
        'distance': {
            'base': 5.0,  # km
            'variance': 2.0,
            'correlates_with': 'steps'
        },
        'calories': {
            'base': 2000,
            'variance': 500,
            'correlates_with': ['steps', 'distance']
        },
        'sleep_hours': {
            'base': 7.5,
            'variance': 1.0,
            'weekly_pattern': True
        },
        'exercise_minutes': {
            'base': 30,
            'variance': 20,
            'weekly_pattern': True
        }
    }
    
    def generate(
        self, 
        metric: str,
        date: datetime,
        user_profile: Optional[Dict] = None
    ) -> float:
        """Generate single health metric value."""
        config = self.METRIC_CONFIGS.get(metric, {})
        base = config.get('base', 100)
        variance = config.get('variance', 10)
        
        # Apply patterns
        value = base
        if config.get('weekly_pattern'):
            value *= self._weekly_factor(date)
        if config.get('seasonal_pattern'):
            value *= self._seasonal_factor(date)
        
        # Add noise
        value += self.rng.normal(0, variance * 0.1)
        
        # Apply user profile adjustments
        if user_profile:
            value *= self._user_factor(user_profile, metric)
        
        return max(0, value)  # Ensure non-negative
    
    def _weekly_factor(self, date: datetime) -> float:
        """Weekly activity pattern (lower on weekends)."""
        day_of_week = date.weekday()
        if day_of_week in [5, 6]:  # Weekend
            return 0.8 + self.rng.random() * 0.2
        return 0.9 + self.rng.random() * 0.2
    
    def _seasonal_factor(self, date: datetime) -> float:
        """Seasonal activity pattern (higher in summer)."""
        month = date.month
        # Peak in June (month 6), lowest in December (month 12)
        seasonal_multiplier = 1.0 + 0.2 * abs(6 - month) / 6
        return seasonal_multiplier
    
    def _user_factor(self, user_profile: Dict, metric: str) -> float:
        """Apply user profile adjustments."""
        activity_multiplier = user_profile.get('activity_multiplier', 1.0)
        
        # Apply different multipliers based on metric
        if metric in ['steps', 'distance', 'calories', 'exercise_minutes']:
            return activity_multiplier
        elif metric == 'heart_rate':
            # Active people typically have lower resting heart rate
            return 2.0 - activity_multiplier
        else:
            return 1.0