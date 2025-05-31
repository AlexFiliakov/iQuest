"""
Monthly context provider for weekly health data analysis.
Provides percentile ranking, best/worst week indicators, goal progress tracking,
and seasonal adjustments with Wall Street Journal-inspired analytics style.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
import logging
from functools import lru_cache
import calendar
from collections import defaultdict
from scipy import stats

from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator
from .cache_manager import AnalyticsCacheManager
from .daily_metrics_calculator import DailyMetricsCalculator


logger = logging.getLogger(__name__)


@dataclass
class WeekContext:
    """Container for weekly context within monthly analytics."""
    week_number: int
    month: int
    year: int
    metric_name: str
    percentile_rank: float
    is_best_week: bool
    is_worst_week: bool
    goal_progress: float
    seasonal_factor: float
    monthly_average: float
    current_week_value: float
    rank_within_month: int
    total_weeks_in_month: int
    confidence_level: float
    exceptional_reason: Optional[str] = None
    
    @property
    def percentile_category(self) -> str:
        """Categorize percentile rank for display."""
        if self.percentile_rank >= 90:
            return "exceptional"
        elif self.percentile_rank >= 75:
            return "above_average"
        elif self.percentile_rank >= 25:
            return "average"
        else:
            return "below_average"
    
    @property
    def vs_monthly_average_percent(self) -> float:
        """Calculate percentage difference from monthly average."""
        if self.monthly_average == 0:
            return 0.0
        return ((self.current_week_value - self.monthly_average) / self.monthly_average) * 100


@dataclass
class GoalProgress:
    """Container for monthly goal progress tracking."""
    target_value: float
    current_progress: float
    projected_month_end: float
    days_elapsed: int
    days_remaining: int
    daily_required_average: float
    on_track: bool
    progress_percentage: float
    
    @property
    def pace_vs_target(self) -> str:
        """Determine if pace is ahead, on track, or behind target."""
        if self.progress_percentage >= 100:
            return "completed"
        elif self.current_progress >= (self.target_value * (self.days_elapsed / (self.days_elapsed + self.days_remaining))):
            return "ahead"
        elif self.progress_percentage >= 80:
            return "on_track"
        else:
            return "behind"


@dataclass
class SeasonalAdjustment:
    """Container for seasonal adjustment factors."""
    base_factor: float
    weather_correlation: float
    historical_average: float
    year_over_year_change: float
    confidence_interval: Tuple[float, float]
    sample_size: int


class MonthlyContextProvider:
    """
    Provides monthly context for weekly health metrics.
    
    Features:
    - Percentile ranking within month
    - Best/worst week identification
    - Goal progress tracking
    - Seasonal adjustments
    - WSJ-style analytics insights
    """
    
    def __init__(self, cache_manager: AnalyticsCacheManager, 
                 daily_calculator: Optional[DailyMetricsCalculator] = None):
        """Initialize the monthly context provider.
        
        Args:
            cache_manager: Cache manager instance
            daily_calculator: Optional daily calculator instance
        """
        self.cache = cache_manager
        
        # Create a mock daily calculator if not provided (for testing)
        if daily_calculator is None:
            from unittest.mock import Mock
            daily_calculator = Mock(spec=DailyMetricsCalculator)
            
        self.weekly_calc = WeeklyMetricsCalculator(daily_calculator)
        self.monthly_calc = MonthlyMetricsCalculator(daily_calculator)
        self._goal_targets = {}  # Store monthly goals
        
    def set_monthly_goal(self, metric: str, year: int, month: int, target: float):
        """Set a monthly goal for a specific metric."""
        key = f"{metric}_{year}_{month}"
        self._goal_targets[key] = target
        
    def get_week_context(self, week_num: int, year: int, metric: str) -> WeekContext:
        """
        Get comprehensive monthly context for a specific week.
        
        Args:
            week_num: Week number (1-53)
            year: Year
            metric: Metric name (e.g., 'steps', 'heart_rate')
            
        Returns:
            WeekContext: Complete context information
        """
        month = self._get_month_for_week(week_num, year)
        
        # Try cache first
        cache_key = f"monthly_context_{year}_{month}_{metric}_{week_num}"
        
        def compute_context():
            return self._calculate_week_context(week_num, month, year, metric)
        
        # Use cache.get with compute function
        context = self.cache.get(cache_key, compute_context, ttl=3600)
        return context
        
    def _calculate_week_context(self, week_num: int, month: int, year: int, metric: str) -> WeekContext:
        """Calculate comprehensive weekly context."""
        try:
            # Get weekly data for the month
            weekly_data = self._get_monthly_weekly_data(month, year, metric)
            current_week_value = weekly_data.get(week_num, 0.0)
            
            if not weekly_data:
                logger.warning(f"No weekly data found for {month}/{year}")
                return self._create_empty_context(week_num, month, year, metric)
            
            # Calculate percentile rank
            values = list(weekly_data.values())
            percentile_rank = self._calculate_percentile_rank(current_week_value, values)
            
            # Identify best/worst weeks
            is_best_week = current_week_value == max(values) if values else False
            is_worst_week = current_week_value == min(values) if values else False
            
            # Calculate goal progress
            goal_progress = self._calculate_goal_progress(month, year, metric, week_num)
            
            # Apply seasonal adjustments
            seasonal_factor = self._get_seasonal_adjustment(month, metric).base_factor
            
            # Calculate monthly average
            monthly_average = np.mean(values) if values else 0.0
            
            # Determine rank within month
            sorted_values = sorted(values, reverse=True)
            rank_within_month = sorted_values.index(current_week_value) + 1 if current_week_value in sorted_values else len(sorted_values)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(values)
            
            # Determine exceptional reason
            exceptional_reason = self._determine_exceptional_reason(
                current_week_value, values, percentile_rank, metric
            )
            
            return WeekContext(
                week_number=week_num,
                month=month,
                year=year,
                metric_name=metric,
                percentile_rank=percentile_rank,
                is_best_week=is_best_week,
                is_worst_week=is_worst_week,
                goal_progress=goal_progress,
                seasonal_factor=seasonal_factor,
                monthly_average=monthly_average,
                current_week_value=current_week_value,
                rank_within_month=rank_within_month,
                total_weeks_in_month=len(values),
                confidence_level=confidence_level,
                exceptional_reason=exceptional_reason
            )
            
        except Exception as e:
            logger.error(f"Error calculating week context: {e}")
            return self._create_empty_context(week_num, month, year, metric)
    
    def _get_monthly_weekly_data(self, month: int, year: int, metric: str) -> Dict[int, float]:
        """Get weekly data for a specific month."""
        # This would integrate with the actual data source
        # For now, return mock data for demonstration
        weekly_data = {}
        
        # Calculate which weeks fall in this month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        current_date = first_day
        while current_date <= last_day:
            week_num = current_date.isocalendar()[1]
            if week_num not in weekly_data:
                # This would call the actual weekly calculator
                weekly_data[week_num] = self._mock_weekly_value(metric)
            current_date += timedelta(days=7)
            
        return weekly_data
    
    def _mock_weekly_value(self, metric: str) -> float:
        """Mock weekly value for demonstration (replace with actual data access)."""
        import random
        base_values = {
            'steps': 50000,
            'heart_rate': 75,
            'sleep_hours': 56,  # 8 hours * 7 days
            'distance': 25000  # meters
        }
        base = base_values.get(metric, 100)
        return base + random.randint(-int(base * 0.3), int(base * 0.3))
    
    def _calculate_percentile_rank(self, value: float, values: List[float]) -> float:
        """Calculate percentile rank of value within the list."""
        if not values or len(values) == 1:
            return 50.0
            
        return stats.percentileofscore(values, value, kind='rank')
    
    def _calculate_goal_progress(self, month: int, year: int, metric: str, week_num: int) -> float:
        """Calculate goal progress percentage."""
        goal_key = f"{metric}_{year}_{month}"
        target = self._goal_targets.get(goal_key, 0)
        
        if target == 0:
            return 0.0
            
        # Calculate current progress (mock implementation)
        current_date = date.today()
        if current_date.year == year and current_date.month == month:
            days_elapsed = current_date.day
        else:
            days_elapsed = calendar.monthrange(year, month)[1]
            
        # Mock current progress calculation
        estimated_progress = target * (days_elapsed / calendar.monthrange(year, month)[1])
        return min(100.0, (estimated_progress / target) * 100)
    
    def _get_seasonal_adjustment(self, month: int, metric: str) -> SeasonalAdjustment:
        """Get seasonal adjustment factors for the metric."""
        # Mock seasonal factors (replace with historical analysis)
        seasonal_factors = {
            'steps': {
                1: 0.85, 2: 0.90, 3: 0.95, 4: 1.05, 5: 1.10, 6: 1.15,
                7: 1.20, 8: 1.15, 9: 1.10, 10: 1.05, 11: 0.95, 12: 0.85
            },
            'heart_rate': {month: 1.0 for month in range(1, 13)},
            'sleep_hours': {
                1: 1.05, 2: 1.03, 3: 1.00, 4: 0.98, 5: 0.95, 6: 0.93,
                7: 0.90, 8: 0.93, 9: 0.95, 10: 0.98, 11: 1.00, 12: 1.03
            }
        }
        
        factor = seasonal_factors.get(metric, {}).get(month, 1.0)
        
        return SeasonalAdjustment(
            base_factor=factor,
            weather_correlation=0.0,  # Would be calculated from historical data
            historical_average=100.0,  # Mock value
            year_over_year_change=0.05,  # 5% growth
            confidence_interval=(factor * 0.95, factor * 1.05),
            sample_size=52  # Assume we have 1 year of data
        )
    
    def _calculate_confidence_level(self, values: List[float]) -> float:
        """Calculate statistical confidence level for the data."""
        if len(values) < 3:
            return 0.5
            
        # Calculate coefficient of variation as inverse confidence measure
        if np.mean(values) == 0:
            return 0.5
            
        cv = np.std(values) / np.mean(values)
        # Convert to confidence (lower variation = higher confidence)
        confidence = max(0.0, min(1.0, 1.0 - cv))
        return confidence
    
    def _determine_exceptional_reason(self, value: float, values: List[float], 
                                    percentile: float, metric: str) -> Optional[str]:
        """Determine reason for exceptional performance."""
        if percentile >= 95:
            return f"Top 5% performance for {metric}"
        elif percentile <= 5:
            return f"Bottom 5% performance for {metric}"
        elif len(values) > 1:
            std_dev = np.std(values)
            mean_val = np.mean(values)
            if abs(value - mean_val) > 2 * std_dev:
                direction = "above" if value > mean_val else "below"
                return f"Statistically unusual ({direction} 2 standard deviations)"
        return None
    
    def _get_month_for_week(self, week_num: int, year: int) -> int:
        """Get the month for a given week number."""
        # Use the Thursday of the week to determine the month
        jan_4 = date(year, 1, 4)
        week_start = jan_4 + timedelta(days=(week_num - 1) * 7 - jan_4.weekday())
        thursday = week_start + timedelta(days=3)
        return thursday.month
    
    def _create_empty_context(self, week_num: int, month: int, year: int, metric: str) -> WeekContext:
        """Create an empty context when no data is available."""
        return WeekContext(
            week_number=week_num,
            month=month,
            year=year,
            metric_name=metric,
            percentile_rank=50.0,
            is_best_week=False,
            is_worst_week=False,
            goal_progress=0.0,
            seasonal_factor=1.0,
            monthly_average=0.0,
            current_week_value=0.0,
            rank_within_month=1,
            total_weeks_in_month=1,
            confidence_level=0.0,
            exceptional_reason="No data available"
        )
    
    def get_monthly_insights(self, month: int, year: int, metric: str) -> Dict[str, Any]:
        """Get comprehensive monthly insights for reporting."""
        weekly_data = self._get_monthly_weekly_data(month, year, metric)
        
        if not weekly_data:
            return {"error": "No data available"}
        
        values = list(weekly_data.values())
        insights = {
            "best_week": max(weekly_data, key=weekly_data.get),
            "worst_week": min(weekly_data, key=weekly_data.get),
            "most_consistent_period": self._find_most_consistent_period(weekly_data),
            "monthly_trend": "improving" if values[-1] > values[0] else "declining",
            "volatility_score": np.std(values) / np.mean(values) if np.mean(values) > 0 else 0,
            "seasonal_adjustment": self._get_seasonal_adjustment(month, metric).base_factor
        }
        
        return insights
    
    def _find_most_consistent_period(self, weekly_data: Dict[int, float]) -> Tuple[int, int]:
        """Find the most consistent consecutive week period."""
        if len(weekly_data) < 2:
            return (list(weekly_data.keys())[0], list(weekly_data.keys())[0])
        
        weeks = sorted(weekly_data.keys())
        min_cv = float('inf')
        best_period = (weeks[0], weeks[0])
        
        for i in range(len(weeks) - 1):
            for j in range(i + 1, len(weeks)):
                period_values = [weekly_data[w] for w in weeks[i:j+1]]
                if len(period_values) >= 2:
                    cv = np.std(period_values) / np.mean(period_values) if np.mean(period_values) > 0 else float('inf')
                    if cv < min_cv:
                        min_cv = cv
                        best_period = (weeks[i], weeks[j])
        
        return best_period