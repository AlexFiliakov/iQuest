"""
Week-over-week trends calculator for health data analysis.
Provides percentage changes, momentum indicators, streak tracking, and predictive analysis.
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
import logging
from enum import Enum
from scipy import stats
import json

from .weekly_metrics_calculator import WeeklyMetricsCalculator, WeekComparison, TrendInfo


logger = logging.getLogger(__name__)


class MomentumType(Enum):
    """Types of momentum indicators."""
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    STEADY = "steady"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TrendResult:
    """Container for trend analysis results."""
    percent_change: float
    absolute_change: float
    momentum: MomentumType
    streak: int
    confidence: float
    current_week_avg: float
    previous_week_avg: float
    trend_direction: str  # 'up', 'down', 'stable'


@dataclass
class StreakInfo:
    """Container for streak tracking information."""
    current_streak: int
    best_streak: int
    streak_direction: str  # 'improving', 'declining', 'none'
    streak_start_date: Optional[date]
    is_current_streak_best: bool


@dataclass
class MomentumIndicator:
    """Container for momentum analysis."""
    momentum_type: MomentumType
    acceleration_rate: float
    change_velocity: float
    trend_strength: float
    confidence_level: float


@dataclass
class Prediction:
    """Container for predictive analysis results."""
    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    prediction_confidence: float
    methodology: str
    factors_considered: List[str]


@dataclass
class WeekTrendData:
    """Container for week trend visualization data."""
    week_start: date
    week_end: date
    value: float
    percent_change_from_previous: Optional[float]
    trend_direction: str
    momentum: MomentumType
    is_incomplete_week: bool
    missing_days: int


class WeekOverWeekTrends:
    """
    Calculator for week-over-week trend analysis with momentum indicators,
    streak tracking, and predictive analytics.
    """
    
    def __init__(self, weekly_calculator: WeeklyMetricsCalculator):
        """
        Initialize the trends calculator.
        
        Args:
            weekly_calculator: Instance of WeeklyMetricsCalculator
        """
        self.weekly_calculator = weekly_calculator
        self.streak_cache = {}
        self.trend_cache = {}
        
    def calculate_week_change(self, 
                            metric: str, 
                            week1: int, 
                            week2: int, 
                            year: int) -> TrendResult:
        """
        Calculate change between two weeks.
        
        Args:
            metric: The metric type to analyze
            week1: First week number (usually previous week)
            week2: Second week number (usually current week)
            year: Year for the weeks
            
        Returns:
            TrendResult object with analysis results
        """
        # Get week comparisons
        comparison = self.weekly_calculator.compare_week_to_date(metric, week2, year)
        
        # Calculate momentum
        momentum = self.detect_momentum(metric, week2, year)
        
        # Get current streak
        streak = self.get_current_streak(metric, week2, year)
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(comparison)
        
        return TrendResult(
            percent_change=comparison.percent_change,
            absolute_change=comparison.absolute_change,
            momentum=momentum.momentum_type,
            streak=streak.current_streak,
            confidence=confidence,
            current_week_avg=comparison.current_week_avg,
            previous_week_avg=comparison.previous_week_avg,
            trend_direction=self._determine_trend_direction(comparison.percent_change)
        )
    
    def detect_momentum(self, 
                       metric: str, 
                       current_week: int, 
                       year: int,
                       lookback_weeks: int = 4) -> MomentumIndicator:
        """
        Detect if trend is accelerating, decelerating, or steady.
        
        Args:
            metric: The metric type to analyze
            current_week: Current week number
            year: Year
            lookback_weeks: Number of weeks to look back for momentum analysis
            
        Returns:
            MomentumIndicator object with momentum analysis
        """
        if lookback_weeks < 3:
            return MomentumIndicator(
                momentum_type=MomentumType.INSUFFICIENT_DATA,
                acceleration_rate=0.0,
                change_velocity=0.0,
                trend_strength=0.0,
                confidence_level=0.0
            )
        
        # Get percent changes for the last few weeks
        changes = []
        for i in range(lookback_weeks):
            week_num = current_week - i
            if week_num < 1:
                # Handle year boundary
                week_num = 52 + week_num  # Approximate
                calc_year = year - 1
            else:
                calc_year = year
            
            try:
                comparison = self.weekly_calculator.compare_week_to_date(metric, week_num, calc_year)
                changes.append(comparison.percent_change)
            except Exception as e:
                logger.warning(f"Could not get data for week {week_num} year {calc_year}: {e}")
                continue
        
        if len(changes) < 3:
            return MomentumIndicator(
                momentum_type=MomentumType.INSUFFICIENT_DATA,
                acceleration_rate=0.0,
                change_velocity=0.0,
                trend_strength=0.0,
                confidence_level=0.0
            )
        
        # Reverse to get chronological order
        changes.reverse()
        
        # Calculate acceleration (second derivative)
        velocities = np.diff(changes)
        acceleration = np.mean(np.diff(velocities)) if len(velocities) > 1 else 0
        
        # Calculate average velocity (first derivative)
        avg_velocity = np.mean(velocities)
        
        # Calculate trend strength using linear regression
        x = np.arange(len(changes))
        slope, _, r_value, p_value, _ = stats.linregress(x, changes)
        trend_strength = abs(r_value) if p_value < 0.05 else 0
        
        # Determine momentum type
        if abs(acceleration) < 0.5:  # Threshold for steady
            momentum_type = MomentumType.STEADY
        elif acceleration > 0.5:
            momentum_type = MomentumType.ACCELERATING
        else:
            momentum_type = MomentumType.DECELERATING
        
        # Calculate confidence based on data quality and consistency
        confidence = min(1.0, (len(changes) / lookback_weeks) * (1 - p_value))
        
        return MomentumIndicator(
            momentum_type=momentum_type,
            acceleration_rate=float(acceleration),
            change_velocity=float(avg_velocity),
            trend_strength=float(trend_strength),
            confidence_level=float(confidence)
        )
    
    def get_current_streak(self, 
                          metric: str, 
                          current_week: int, 
                          year: int,
                          max_lookback: int = 52) -> StreakInfo:
        """
        Calculate improvement/decline streaks.
        
        Args:
            metric: The metric type to analyze
            current_week: Current week number
            year: Year
            max_lookback: Maximum weeks to look back
            
        Returns:
            StreakInfo object with streak analysis
        """
        cache_key = f"{metric}_{current_week}_{year}"
        if cache_key in self.streak_cache:
            return self.streak_cache[cache_key]
        
        # Get week-over-week changes
        changes = []
        week_dates = []
        
        for i in range(max_lookback):
            week_num = current_week - i
            calc_year = year
            
            if week_num < 1:
                # Handle year boundary
                calc_year = year - 1
                week_num = 52 + week_num
            
            try:
                comparison = self.weekly_calculator.compare_week_to_date(metric, week_num, calc_year)
                changes.append(comparison.percent_change)
                
                # Get week start date for tracking
                week_start, _ = self.weekly_calculator._get_week_dates(calc_year, week_num)
                week_dates.append(week_start)
                
            except Exception as e:
                logger.warning(f"Could not get data for week {week_num} year {calc_year}: {e}")
                break
        
        if len(changes) < 2:
            result = StreakInfo(
                current_streak=0,
                best_streak=0,
                streak_direction='none',
                streak_start_date=None,
                is_current_streak_best=False
            )
            self.streak_cache[cache_key] = result
            return result
        
        # Reverse to get chronological order
        changes.reverse()
        week_dates.reverse()
        
        # Find current streak
        current_streak = 0
        streak_direction = 'none'
        streak_start_date = None
        
        # Start from most recent week
        if changes[-1] > 2:  # Improvement threshold (2% improvement)
            streak_direction = 'improving'
            current_streak = 1
            streak_start_date = week_dates[-1]
            
            # Count backwards
            for i in range(len(changes) - 2, -1, -1):
                if changes[i] > 2:
                    current_streak += 1
                    streak_start_date = week_dates[i]
                else:
                    break
                    
        elif changes[-1] < -2:  # Decline threshold (-2% decline)
            streak_direction = 'declining'
            current_streak = 1
            streak_start_date = week_dates[-1]
            
            # Count backwards
            for i in range(len(changes) - 2, -1, -1):
                if changes[i] < -2:
                    current_streak += 1
                    streak_start_date = week_dates[i]
                else:
                    break
        
        # Find best streak in the data
        best_improving_streak = 0
        best_declining_streak = 0
        temp_improving = 0
        temp_declining = 0
        
        for change in changes:
            if change > 2:
                temp_improving += 1
                temp_declining = 0
                best_improving_streak = max(best_improving_streak, temp_improving)
            elif change < -2:
                temp_declining += 1
                temp_improving = 0
                best_declining_streak = max(best_declining_streak, temp_declining)
            else:
                temp_improving = 0
                temp_declining = 0
        
        # Best streak is the longer of improvement or decline streaks
        best_streak = max(best_improving_streak, best_declining_streak)
        is_current_best = (current_streak == best_streak and current_streak > 0)
        
        result = StreakInfo(
            current_streak=current_streak,
            best_streak=best_streak,
            streak_direction=streak_direction,
            streak_start_date=streak_start_date,
            is_current_streak_best=is_current_best
        )
        
        self.streak_cache[cache_key] = result
        return result
    
    def predict_next_week(self, 
                         metric: str, 
                         current_week: int, 
                         year: int,
                         method: str = "linear") -> Prediction:
        """
        Forecast next week's value with confidence interval.
        
        Args:
            metric: The metric type to analyze
            current_week: Current week number
            year: Year
            method: Prediction method ('linear', 'exponential', 'seasonal')
            
        Returns:
            Prediction object with forecast results
        """
        # Get historical data for prediction
        lookback_weeks = 12  # Use last 3 months
        historical_values = []
        
        for i in range(lookback_weeks):
            week_num = current_week - i
            calc_year = year
            
            if week_num < 1:
                calc_year = year - 1
                week_num = 52 + week_num
            
            try:
                week_start, week_end = self.weekly_calculator._get_week_dates(calc_year, week_num)
                weekly_summary = self.weekly_calculator.get_weekly_summary([metric], week_num, calc_year)
                
                if metric in weekly_summary and 'mean' in weekly_summary[metric]:
                    historical_values.append(weekly_summary[metric]['mean'])
                
            except Exception as e:
                logger.warning(f"Could not get data for prediction for week {week_num}: {e}")
                continue
        
        if len(historical_values) < 4:
            return Prediction(
                predicted_value=0.0,
                confidence_interval_lower=0.0,
                confidence_interval_upper=0.0,
                prediction_confidence=0.0,
                methodology="insufficient_data",
                factors_considered=[]
            )
        
        # Reverse to get chronological order
        historical_values.reverse()
        
        if method == "linear":
            return self._linear_prediction(historical_values)
        elif method == "exponential":
            return self._exponential_prediction(historical_values)
        elif method == "seasonal":
            return self._seasonal_prediction(historical_values, metric, current_week, year)
        else:
            return self._linear_prediction(historical_values)
    
    def generate_trend_narrative(self, 
                               metric: str, 
                               trend_result: TrendResult,
                               streak_info: StreakInfo,
                               momentum: MomentumIndicator) -> str:
        """
        Generate automatic trend narrative.
        
        Args:
            metric: The metric type
            trend_result: Trend analysis results
            streak_info: Streak information
            momentum: Momentum analysis
            
        Returns:
            Generated narrative string
        """
        narrative_parts = []
        
        # Start with change description
        if abs(trend_result.percent_change) < 2:
            narrative_parts.append(f"Your {metric} remained relatively stable this week")
        elif trend_result.percent_change > 0:
            narrative_parts.append(f"Your {metric} improved by {trend_result.percent_change:.1f}% this week")
        else:
            narrative_parts.append(f"Your {metric} decreased by {abs(trend_result.percent_change):.1f}% this week")
        
        # Add momentum context
        if momentum.momentum_type == MomentumType.ACCELERATING:
            narrative_parts.append("and the improvement is accelerating")
        elif momentum.momentum_type == MomentumType.DECELERATING:
            narrative_parts.append("though the rate of change is slowing")
        elif momentum.momentum_type == MomentumType.STEADY:
            narrative_parts.append("with consistent progress")
        
        # Add streak information
        if streak_info.current_streak > 1:
            if streak_info.streak_direction == 'improving':
                narrative_parts.append(f"You're on a {streak_info.current_streak}-week improvement streak!")
                if streak_info.is_current_streak_best:
                    narrative_parts.append("This is your best streak yet.")
            elif streak_info.streak_direction == 'declining':
                narrative_parts.append(f"This marks {streak_info.current_streak} consecutive weeks of decline.")
        
        # Add confidence qualifier
        if trend_result.confidence < 0.5:
            narrative_parts.append("(Note: Limited data available for this analysis)")
        
        return " ".join(narrative_parts) + "."
    
    def get_trend_series(self, 
                        metric: str, 
                        weeks_back: int = 12,
                        end_week: Optional[int] = None,
                        end_year: Optional[int] = None) -> List[WeekTrendData]:
        """
        Get trend data series for visualization.
        
        Args:
            metric: The metric type
            weeks_back: Number of weeks to include
            end_week: End week (default: current week)
            end_year: End year (default: current year)
            
        Returns:
            List of WeekTrendData objects for visualization
        """
        if end_week is None or end_year is None:
            today = date.today()
            end_year, end_week, _ = today.isocalendar()
        
        trend_data = []
        previous_value = None
        
        for i in range(weeks_back):
            week_num = end_week - i
            calc_year = end_year
            
            if week_num < 1:
                calc_year = end_year - 1
                week_num = 52 + week_num
            
            try:
                # Get week dates
                week_start, week_end = self.weekly_calculator._get_week_dates(calc_year, week_num)
                
                # Get weekly summary
                weekly_summary = self.weekly_calculator.get_weekly_summary([metric], week_num, calc_year)
                
                if metric in weekly_summary and 'mean' in weekly_summary[metric]:
                    current_value = weekly_summary[metric]['mean']
                    
                    # Calculate percent change from previous week
                    percent_change = None
                    if previous_value is not None and previous_value != 0:
                        percent_change = ((current_value - previous_value) / previous_value) * 100
                    
                    # Get momentum
                    momentum = self.detect_momentum(metric, week_num, calc_year)
                    
                    # Check if week is incomplete
                    today = date.today()
                    is_incomplete = week_end > today
                    missing_days = (week_end - today).days if is_incomplete else 0
                    
                    trend_data.append(WeekTrendData(
                        week_start=week_start,
                        week_end=week_end,
                        value=current_value,
                        percent_change_from_previous=percent_change,
                        trend_direction=self._determine_trend_direction(percent_change) if percent_change else 'stable',
                        momentum=momentum.momentum_type,
                        is_incomplete_week=is_incomplete,
                        missing_days=missing_days
                    ))
                    
                    previous_value = current_value
                
            except Exception as e:
                logger.warning(f"Could not get trend data for week {week_num} year {calc_year}: {e}")
                continue
        
        # Reverse to get chronological order
        trend_data.reverse()
        return trend_data
    
    def _calculate_confidence(self, comparison: WeekComparison) -> float:
        """Calculate confidence score based on data completeness."""
        base_confidence = 1.0
        
        # Reduce confidence for partial weeks
        if comparison.is_partial_week:
            completeness = comparison.current_week_days / 7
            base_confidence *= completeness
        
        # Reduce confidence if previous week had missing data
        if comparison.previous_week_days < 7:
            prev_completeness = comparison.previous_week_days / 7
            base_confidence *= prev_completeness
        
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_trend_direction(self, percent_change: Optional[float]) -> str:
        """Determine trend direction from percent change."""
        if percent_change is None:
            return 'stable'
        elif percent_change > 2:
            return 'up'
        elif percent_change < -2:
            return 'down'
        else:
            return 'stable'
    
    def _linear_prediction(self, values: List[float]) -> Prediction:
        """Perform linear regression prediction."""
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Predict next value
        next_x = len(values)
        predicted_value = slope * next_x + intercept
        
        # Calculate confidence interval
        mse = np.mean((np.array(values) - (slope * x + intercept)) ** 2)
        margin = 1.96 * np.sqrt(mse)  # 95% confidence interval
        
        confidence = max(0.0, min(1.0, abs(r_value))) if p_value < 0.05 else 0.0
        
        return Prediction(
            predicted_value=float(predicted_value),
            confidence_interval_lower=float(predicted_value - margin),
            confidence_interval_upper=float(predicted_value + margin),
            prediction_confidence=float(confidence),
            methodology="linear_regression",
            factors_considered=["historical_trend", "data_consistency"]
        )
    
    def _exponential_prediction(self, values: List[float]) -> Prediction:
        """Perform exponential smoothing prediction."""
        alpha = 0.3  # Smoothing parameter
        
        # Simple exponential smoothing
        if len(values) < 2:
            return Prediction(
                predicted_value=values[0] if values else 0.0,
                confidence_interval_lower=0.0,
                confidence_interval_upper=0.0,
                prediction_confidence=0.0,
                methodology="insufficient_data",
                factors_considered=[]
            )
        
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[i-1])
        
        # Predict next value
        predicted_value = alpha * values[-1] + (1 - alpha) * smoothed[-1]
        
        # Calculate prediction interval based on recent variance
        recent_errors = [abs(values[i] - smoothed[i]) for i in range(len(values))]
        margin = 1.96 * np.std(recent_errors) if len(recent_errors) > 1 else 0
        
        return Prediction(
            predicted_value=float(predicted_value),
            confidence_interval_lower=float(predicted_value - margin),
            confidence_interval_upper=float(predicted_value + margin),
            prediction_confidence=0.7,  # Moderate confidence for exponential smoothing
            methodology="exponential_smoothing",
            factors_considered=["recent_values", "smoothing_trend"]
        )
    
    def _seasonal_prediction(self, values: List[float], metric: str, week: int, year: int) -> Prediction:
        """Perform seasonal prediction (placeholder for future enhancement)."""
        # For now, fall back to linear prediction
        # Future enhancement: incorporate day-of-week patterns, seasonal trends
        return self._linear_prediction(values)