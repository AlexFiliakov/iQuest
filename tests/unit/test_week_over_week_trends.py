"""
Unit tests for week-over-week trends calculator.
Tests trend calculation, momentum detection, streak tracking, and predictions.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from src.analytics.week_over_week_trends import (
    WeekOverWeekTrends, TrendResult, StreakInfo, MomentumIndicator, 
    Prediction, WeekTrendData, MomentumType
)
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator, WeekComparison


@pytest.fixture
def mock_weekly_calculator():
    """Create a mock weekly calculator."""
    calculator = Mock(spec=WeeklyMetricsCalculator)
    return calculator


@pytest.fixture
def trends_calculator(mock_weekly_calculator):
    """Create trends calculator with mock weekly calculator."""
    return WeekOverWeekTrends(mock_weekly_calculator)


class TestWeekOverWeekTrends:
    """Test suite for WeekOverWeekTrends calculator."""
    
    def test_initialization(self, mock_weekly_calculator):
        """Test proper initialization."""
        calculator = WeekOverWeekTrends(mock_weekly_calculator)
        assert calculator.weekly_calculator == mock_weekly_calculator
        assert calculator.streak_cache == {}
        assert calculator.trend_cache == {}
    
    def test_calculate_week_change_improvement(self, trends_calculator, mock_weekly_calculator):
        """Test calculating week change for improvement."""
        # Setup mock data for improvement
        mock_comparison = WeekComparison(
            current_week_avg=100.0,
            previous_week_avg=90.0,
            percent_change=11.11,
            absolute_change=10.0,
            current_week_days=7,
            previous_week_days=7,
            is_partial_week=False
        )
        mock_weekly_calculator.compare_week_to_date.return_value = mock_comparison
        
        # Mock momentum detection
        with patch.object(trends_calculator, 'detect_momentum') as mock_momentum:
            mock_momentum.return_value = MomentumIndicator(
                momentum_type=MomentumType.ACCELERATING,
                acceleration_rate=2.5,
                change_velocity=5.0,
                trend_strength=0.8,
                confidence_level=0.9
            )
            
            # Mock streak tracking
            with patch.object(trends_calculator, 'get_current_streak') as mock_streak:
                mock_streak.return_value = StreakInfo(
                    current_streak=3,
                    best_streak=5,
                    streak_direction='improving',
                    streak_start_date=date.today() - timedelta(weeks=3),
                    is_current_streak_best=False
                )
                
                result = trends_calculator.calculate_week_change("steps", 10, 11, 2024)
                
                assert isinstance(result, TrendResult)
                assert result.percent_change == 11.11
                assert result.absolute_change == 10.0
                assert result.momentum == MomentumType.ACCELERATING
                assert result.streak == 3
                assert result.confidence == 1.0  # Full confidence for complete weeks
                assert result.trend_direction == 'up'
    
    def test_calculate_week_change_decline(self, trends_calculator, mock_weekly_calculator):
        """Test calculating week change for decline."""
        mock_comparison = WeekComparison(
            current_week_avg=80.0,
            previous_week_avg=90.0,
            percent_change=-11.11,
            absolute_change=-10.0,
            current_week_days=7,
            previous_week_days=7,
            is_partial_week=False
        )
        mock_weekly_calculator.compare_week_to_date.return_value = mock_comparison
        
        with patch.object(trends_calculator, 'detect_momentum') as mock_momentum:
            mock_momentum.return_value = MomentumIndicator(
                momentum_type=MomentumType.DECELERATING,
                acceleration_rate=-1.5,
                change_velocity=-3.0,
                trend_strength=0.6,
                confidence_level=0.7
            )
            
            with patch.object(trends_calculator, 'get_current_streak') as mock_streak:
                mock_streak.return_value = StreakInfo(
                    current_streak=2,
                    best_streak=5,
                    streak_direction='declining',
                    streak_start_date=date.today() - timedelta(weeks=2),
                    is_current_streak_best=False
                )
                
                result = trends_calculator.calculate_week_change("steps", 10, 11, 2024)
                
                assert result.percent_change == -11.11
                assert result.trend_direction == 'down'
                assert result.momentum == MomentumType.DECELERATING
    
    def test_calculate_confidence_partial_week(self, trends_calculator):
        """Test confidence calculation for partial weeks."""
        # Partial current week
        comparison = WeekComparison(
            current_week_avg=100.0,
            previous_week_avg=90.0,
            percent_change=11.11,
            absolute_change=10.0,
            current_week_days=5,  # Partial week
            previous_week_days=7,
            is_partial_week=True
        )
        
        confidence = trends_calculator._calculate_confidence(comparison)
        expected = (5/7) * 1.0  # Reduced by current week completeness
        assert abs(confidence - expected) < 0.01
    
    def test_detect_momentum_accelerating(self, trends_calculator, mock_weekly_calculator):
        """Test momentum detection for accelerating trend."""
        # Setup mock comparisons showing accelerating improvements
        comparisons = [
            WeekComparison(current_week_avg=85, previous_week_avg=80, percent_change=6.25, 
                         absolute_change=5, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=90, previous_week_avg=85, percent_change=5.88,
                         absolute_change=5, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=96, previous_week_avg=90, percent_change=6.67,
                         absolute_change=6, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=104, previous_week_avg=96, percent_change=8.33,
                         absolute_change=8, current_week_days=7, previous_week_days=7, is_partial_week=False),
        ]
        
        mock_weekly_calculator.compare_week_to_date.side_effect = comparisons
        
        momentum = trends_calculator.detect_momentum("steps", 15, 2024, 4)
        
        assert momentum.momentum_type == MomentumType.ACCELERATING
        assert momentum.acceleration_rate > 0
        assert momentum.confidence_level > 0
    
    def test_detect_momentum_insufficient_data(self, trends_calculator):
        """Test momentum detection with insufficient data."""
        momentum = trends_calculator.detect_momentum("steps", 15, 2024, 2)  # Too few weeks
        
        assert momentum.momentum_type == MomentumType.INSUFFICIENT_DATA
        assert momentum.acceleration_rate == 0.0
        assert momentum.confidence_level == 0.0
    
    def test_get_current_streak_improvement(self, trends_calculator, mock_weekly_calculator):
        """Test streak calculation for improvement streak."""
        # Setup mock comparisons showing improvement streak
        comparisons = [
            WeekComparison(current_week_avg=104, previous_week_avg=96, percent_change=8.33,
                         absolute_change=8, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=96, previous_week_avg=90, percent_change=6.67,
                         absolute_change=6, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=90, previous_week_avg=85, percent_change=5.88,
                         absolute_change=5, current_week_days=7, previous_week_days=7, is_partial_week=False),
            WeekComparison(current_week_avg=85, previous_week_avg=82, percent_change=3.66,
                         absolute_change=3, current_week_days=7, previous_week_days=7, is_partial_week=False),
        ]
        
        mock_weekly_calculator.compare_week_to_date.side_effect = comparisons
        
        # Mock week dates
        base_date = date.today()
        mock_weekly_calculator._get_week_dates.side_effect = [
            (base_date - timedelta(weeks=i), base_date - timedelta(weeks=i) + timedelta(days=6))
            for i in range(10)
        ]
        
        streak = trends_calculator.get_current_streak("steps", 15, 2024, 10)
        
        assert streak.current_streak == 4  # All weeks show improvement > 2%
        assert streak.streak_direction == 'improving'
        assert streak.best_streak >= 4
    
    def test_get_current_streak_no_streak(self, trends_calculator, mock_weekly_calculator):
        """Test streak calculation when no streak exists."""
        # Setup mock comparison showing stable trend
        comparison = WeekComparison(
            current_week_avg=100, previous_week_avg=99, percent_change=1.0,  # Below threshold
            absolute_change=1, current_week_days=7, previous_week_days=7, is_partial_week=False
        )
        
        mock_weekly_calculator.compare_week_to_date.return_value = comparison
        mock_weekly_calculator._get_week_dates.return_value = (date.today(), date.today() + timedelta(days=6))
        
        streak = trends_calculator.get_current_streak("steps", 15, 2024, 5)
        
        assert streak.current_streak == 0
        assert streak.streak_direction == 'none'
    
    def test_predict_next_week_linear(self, trends_calculator, mock_weekly_calculator):
        """Test linear prediction."""
        # Setup mock weekly summaries with trending data
        summaries = []
        for i in range(12):
            summaries.append({
                "steps": {"mean": 8000 + i * 200}  # Increasing trend
            })
        
        mock_weekly_calculator.get_weekly_summary.side_effect = summaries
        mock_weekly_calculator._get_week_dates.side_effect = [
            (date.today() - timedelta(weeks=i), date.today() - timedelta(weeks=i) + timedelta(days=6))
            for i in range(12)
        ]
        
        prediction = trends_calculator.predict_next_week("steps", 15, 2024, "linear")
        
        assert prediction.predicted_value > 0
        assert prediction.confidence_interval_lower < prediction.predicted_value
        assert prediction.confidence_interval_upper > prediction.predicted_value
        assert prediction.methodology == "linear_regression"
        assert prediction.prediction_confidence > 0
    
    def test_predict_next_week_insufficient_data(self, trends_calculator, mock_weekly_calculator):
        """Test prediction with insufficient data."""
        # Setup mock with only 2 data points
        summaries = [
            {"steps": {"mean": 8000}},
            {"steps": {"mean": 8200}}
        ]
        
        mock_weekly_calculator.get_weekly_summary.side_effect = summaries
        mock_weekly_calculator._get_week_dates.side_effect = [
            (date.today() - timedelta(weeks=i), date.today() - timedelta(weeks=i) + timedelta(days=6))
            for i in range(2)
        ]
        
        prediction = trends_calculator.predict_next_week("steps", 15, 2024)
        
        assert prediction.methodology == "insufficient_data"
        assert prediction.prediction_confidence == 0.0
    
    def test_generate_trend_narrative_improvement(self, trends_calculator):
        """Test narrative generation for improvement."""
        trend_result = TrendResult(
            percent_change=15.5,
            absolute_change=1000,
            momentum=MomentumType.ACCELERATING,
            streak=3,
            confidence=0.9,
            current_week_avg=7500,
            previous_week_avg=6500,
            trend_direction='up'
        )
        
        streak_info = StreakInfo(
            current_streak=3,
            best_streak=5,
            streak_direction='improving',
            streak_start_date=date.today() - timedelta(weeks=3),
            is_current_streak_best=False
        )
        
        momentum = MomentumIndicator(
            momentum_type=MomentumType.ACCELERATING,
            acceleration_rate=2.5,
            change_velocity=5.0,
            trend_strength=0.8,
            confidence_level=0.9
        )
        
        narrative = trends_calculator.generate_trend_narrative("steps", trend_result, streak_info, momentum)
        
        assert "improved by 15.5%" in narrative
        assert "accelerating" in narrative
        assert "3-week improvement streak" in narrative
        assert isinstance(narrative, str)
        assert len(narrative) > 0
    
    def test_generate_trend_narrative_stable(self, trends_calculator):
        """Test narrative generation for stable trend."""
        trend_result = TrendResult(
            percent_change=1.0,  # Stable
            absolute_change=50,
            momentum=MomentumType.STEADY,
            streak=0,
            confidence=0.8,
            current_week_avg=7500,
            previous_week_avg=7450,
            trend_direction='stable'
        )
        
        streak_info = StreakInfo(
            current_streak=0,
            best_streak=3,
            streak_direction='none',
            streak_start_date=None,
            is_current_streak_best=False
        )
        
        momentum = MomentumIndicator(
            momentum_type=MomentumType.STEADY,
            acceleration_rate=0.1,
            change_velocity=0.5,
            trend_strength=0.3,
            confidence_level=0.8
        )
        
        narrative = trends_calculator.generate_trend_narrative("steps", trend_result, streak_info, momentum)
        
        assert "remained relatively stable" in narrative
        assert "consistent progress" in narrative
    
    def test_get_trend_series(self, trends_calculator, mock_weekly_calculator):
        """Test getting trend series for visualization."""
        # Setup mock weekly summaries
        summaries = []
        for i in range(8):
            summaries.append({
                "steps": {"mean": 7000 + i * 100}
            })
        
        mock_weekly_calculator.get_weekly_summary.side_effect = summaries
        
        # Mock week dates
        base_date = date.today()
        mock_weekly_calculator._get_week_dates.side_effect = [
            (base_date - timedelta(weeks=i), base_date - timedelta(weeks=i) + timedelta(days=6))
            for i in range(8)
        ]
        
        # Mock momentum detection
        with patch.object(trends_calculator, 'detect_momentum') as mock_momentum:
            mock_momentum.return_value = MomentumIndicator(
                momentum_type=MomentumType.STEADY,
                acceleration_rate=0.0,
                change_velocity=1.0,
                trend_strength=0.5,
                confidence_level=0.7
            )
            
            trend_series = trends_calculator.get_trend_series("steps", 8)
            
            assert len(trend_series) == 8
            assert all(isinstance(data, WeekTrendData) for data in trend_series)
            
            # Check chronological order
            for i in range(1, len(trend_series)):
                assert trend_series[i].week_start >= trend_series[i-1].week_start
    
    def test_determine_trend_direction(self, trends_calculator):
        """Test trend direction determination."""
        assert trends_calculator._determine_trend_direction(5.0) == 'up'
        assert trends_calculator._determine_trend_direction(-5.0) == 'down'
        assert trends_calculator._determine_trend_direction(1.0) == 'stable'
        assert trends_calculator._determine_trend_direction(None) == 'stable'
    
    def test_linear_prediction_method(self, trends_calculator):
        """Test linear prediction method."""
        # Test with trending data
        values = [100, 105, 110, 115, 120, 125]  # Steady increase
        
        prediction = trends_calculator._linear_prediction(values)
        
        assert prediction.predicted_value > 125  # Should predict continuation of trend
        assert prediction.methodology == "linear_regression"
        assert prediction.prediction_confidence > 0
        assert len(prediction.factors_considered) > 0
    
    def test_exponential_prediction_method(self, trends_calculator):
        """Test exponential smoothing prediction method."""
        values = [100, 105, 110, 115, 120, 125]
        
        prediction = trends_calculator._exponential_prediction(values)
        
        assert prediction.predicted_value > 0
        assert prediction.methodology == "exponential_smoothing"
        assert prediction.prediction_confidence == 0.7
    
    def test_exponential_prediction_insufficient_data(self, trends_calculator):
        """Test exponential prediction with insufficient data."""
        values = [100]  # Only one value
        
        prediction = trends_calculator._exponential_prediction(values)
        
        assert prediction.predicted_value == 100
        assert prediction.methodology == "insufficient_data"
        assert prediction.prediction_confidence == 0.0


class TestMomentumType:
    """Test MomentumType enum."""
    
    def test_momentum_type_values(self):
        """Test momentum type enum values."""
        assert MomentumType.ACCELERATING.value == "accelerating"
        assert MomentumType.DECELERATING.value == "decelerating"
        assert MomentumType.STEADY.value == "steady"
        assert MomentumType.INSUFFICIENT_DATA.value == "insufficient_data"


class TestDataClasses:
    """Test data class functionality."""
    
    def test_trend_result(self):
        """Test TrendResult data class."""
        result = TrendResult(
            percent_change=10.5,
            absolute_change=500,
            momentum=MomentumType.ACCELERATING,
            streak=3,
            confidence=0.9,
            current_week_avg=5500,
            previous_week_avg=5000,
            trend_direction='up'
        )
        
        assert result.percent_change == 10.5
        assert result.momentum == MomentumType.ACCELERATING
        assert result.trend_direction == 'up'
    
    def test_streak_info(self):
        """Test StreakInfo data class."""
        streak_date = date.today() - timedelta(weeks=2)
        streak = StreakInfo(
            current_streak=2,
            best_streak=5,
            streak_direction='improving',
            streak_start_date=streak_date,
            is_current_streak_best=False
        )
        
        assert streak.current_streak == 2
        assert streak.streak_start_date == streak_date
        assert not streak.is_current_streak_best
    
    def test_momentum_indicator(self):
        """Test MomentumIndicator data class."""
        momentum = MomentumIndicator(
            momentum_type=MomentumType.ACCELERATING,
            acceleration_rate=2.5,
            change_velocity=5.0,
            trend_strength=0.8,
            confidence_level=0.9
        )
        
        assert momentum.momentum_type == MomentumType.ACCELERATING
        assert momentum.acceleration_rate == 2.5
        assert momentum.confidence_level == 0.9
    
    def test_prediction(self):
        """Test Prediction data class."""
        prediction = Prediction(
            predicted_value=120.0,
            confidence_interval_lower=115.0,
            confidence_interval_upper=125.0,
            prediction_confidence=0.8,
            methodology="linear_regression",
            factors_considered=["historical_trend", "data_consistency"]
        )
        
        assert prediction.predicted_value == 120.0
        assert prediction.methodology == "linear_regression"
        assert len(prediction.factors_considered) == 2
    
    def test_week_trend_data(self):
        """Test WeekTrendData data class."""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        trend_data = WeekTrendData(
            week_start=start_date,
            week_end=end_date,
            value=7500.0,
            percent_change_from_previous=5.2,
            trend_direction='up',
            momentum=MomentumType.ACCELERATING,
            is_incomplete_week=False,
            missing_days=0
        )
        
        assert trend_data.week_start == start_date
        assert trend_data.value == 7500.0
        assert trend_data.trend_direction == 'up'
        assert not trend_data.is_incomplete_week