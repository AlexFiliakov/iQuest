"""
Unit tests for MonthlyContextProvider.
Tests percentile calculations, goal progress tracking, seasonal adjustments,
and WSJ-style analytics features.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import numpy as np

from src.analytics.monthly_context_provider import (
    MonthlyContextProvider, WeekContext, GoalProgress, SeasonalAdjustment
)
from src.analytics.cache_manager import AnalyticsCacheManager as CacheManager


class TestWeekContext:
    """Test WeekContext dataclass functionality."""
    
    def test_percentile_category_exceptional(self):
        """Test percentile categorization for exceptional performance."""
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=95.0, is_best_week=True, is_worst_week=False,
            goal_progress=80.0, seasonal_factor=1.0, monthly_average=50000,
            current_week_value=60000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.9
        )
        
        assert context.percentile_category == "exceptional"
        
    def test_percentile_category_average(self):
        """Test percentile categorization for average performance."""
        context = WeekContext(
            week_number=2, month=1, year=2025, metric_name="steps",
            percentile_rank=45.0, is_best_week=False, is_worst_week=False,
            goal_progress=60.0, seasonal_factor=1.0, monthly_average=50000,
            current_week_value=48000, rank_within_month=2, total_weeks_in_month=4,
            confidence_level=0.7
        )
        
        assert context.percentile_category == "average"
        
    def test_vs_monthly_average_percent(self):
        """Test percentage calculation vs monthly average."""
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=75.0, is_best_week=False, is_worst_week=False,
            goal_progress=70.0, seasonal_factor=1.0, monthly_average=50000,
            current_week_value=55000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.8
        )
        
        expected_percent = ((55000 - 50000) / 50000) * 100
        assert abs(context.vs_monthly_average_percent - expected_percent) < 0.1
        
    def test_vs_monthly_average_zero_division(self):
        """Test handling of zero monthly average."""
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=50.0, is_best_week=False, is_worst_week=False,
            goal_progress=0.0, seasonal_factor=1.0, monthly_average=0.0,
            current_week_value=1000, rank_within_month=1, total_weeks_in_month=1,
            confidence_level=0.0
        )
        
        assert context.vs_monthly_average_percent == 0.0


class TestGoalProgress:
    """Test GoalProgress dataclass functionality."""
    
    def test_pace_vs_target_completed(self):
        """Test completed goal detection."""
        progress = GoalProgress(
            target_value=100000, current_progress=105000, projected_month_end=105000,
            days_elapsed=30, days_remaining=0, daily_required_average=0,
            on_track=True, progress_percentage=105.0
        )
        
        assert progress.pace_vs_target == "completed"
        
    def test_pace_vs_target_ahead(self):
        """Test ahead-of-pace detection."""
        progress = GoalProgress(
            target_value=100000, current_progress=60000, projected_month_end=120000,
            days_elapsed=15, days_remaining=15, daily_required_average=2000,
            on_track=True, progress_percentage=60.0
        )
        
        assert progress.pace_vs_target == "ahead"
        
    def test_pace_vs_target_behind(self):
        """Test behind-pace detection."""
        progress = GoalProgress(
            target_value=100000, current_progress=30000, projected_month_end=75000,
            days_elapsed=20, days_remaining=10, daily_required_average=7000,
            on_track=False, progress_percentage=30.0
        )
        
        assert progress.pace_vs_target == "behind"


class TestMonthlyContextProvider:
    """Test MonthlyContextProvider functionality."""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        cache_manager = Mock(spec=CacheManager)
        cache_manager.get.return_value = None  # Cache miss by default
        cache_manager.set.return_value = None
        return cache_manager
        
    @pytest.fixture
    def context_provider(self, mock_cache_manager):
        """Create context provider with mock cache."""
        return MonthlyContextProvider(mock_cache_manager)
        
    def test_set_monthly_goal(self, context_provider):
        """Test setting monthly goals."""
        context_provider.set_monthly_goal("steps", 2025, 1, 500000)
        
        goal_key = "steps_2025_1"
        assert context_provider._goal_targets[goal_key] == 500000
        
    def test_get_week_context_cache_hit(self, context_provider, mock_cache_manager):
        """Test cache hit scenario."""
        cached_context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=80.0, is_best_week=False, is_worst_week=False,
            goal_progress=70.0, seasonal_factor=1.1, monthly_average=50000,
            current_week_value=52000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.8
        )
        mock_cache_manager.get.return_value = cached_context
        
        result = context_provider.get_week_context(1, 2025, "steps")
        
        assert result == cached_context
        mock_cache_manager.get.assert_called_once()
        
    def test_get_week_context_cache_miss(self, context_provider, mock_cache_manager):
        """Test cache miss scenario with calculation."""
        mock_cache_manager.get.return_value = None
        
        with patch.object(context_provider, '_get_monthly_weekly_data') as mock_data:
            mock_data.return_value = {1: 50000, 2: 52000, 3: 48000, 4: 55000}
            
            result = context_provider.get_week_context(1, 2025, "steps")
            
            assert isinstance(result, WeekContext)
            assert result.week_number == 1
            assert result.year == 2025
            assert result.metric_name == "steps"
            mock_cache_manager.set.assert_called_once()
            
    def test_calculate_percentile_rank(self, context_provider):
        """Test percentile rank calculation."""
        values = [40000, 50000, 52000, 60000, 65000]
        
        # Test value in middle
        percentile = context_provider._calculate_percentile_rank(52000, values)
        assert 50 <= percentile <= 70  # Should be around 60th percentile
        
        # Test highest value
        percentile = context_provider._calculate_percentile_rank(65000, values)
        assert percentile >= 90
        
        # Test lowest value
        percentile = context_provider._calculate_percentile_rank(40000, values)
        assert percentile <= 20
        
    def test_calculate_percentile_rank_edge_cases(self, context_provider):
        """Test percentile calculation edge cases."""
        # Single value
        percentile = context_provider._calculate_percentile_rank(100, [100])
        assert percentile == 50.0
        
        # Empty list
        percentile = context_provider._calculate_percentile_rank(100, [])
        assert percentile == 50.0
        
    def test_calculate_goal_progress_no_goal(self, context_provider):
        """Test goal progress when no goal is set."""
        progress = context_provider._calculate_goal_progress(1, 2025, "steps", 1)
        assert progress == 0.0
        
    def test_calculate_goal_progress_with_goal(self, context_provider):
        """Test goal progress calculation with set goal."""
        context_provider.set_monthly_goal("steps", 2025, 1, 500000)
        
        progress = context_provider._calculate_goal_progress(1, 2025, "steps", 1)
        assert 0 <= progress <= 100
        
    def test_get_seasonal_adjustment(self, context_provider):
        """Test seasonal adjustment factors."""
        # Test winter month (should be lower for steps)
        adjustment = context_provider._get_seasonal_adjustment(1, "steps")
        assert isinstance(adjustment, SeasonalAdjustment)
        assert adjustment.base_factor < 1.0  # Winter should be lower
        
        # Test summer month (should be higher for steps)
        adjustment = context_provider._get_seasonal_adjustment(7, "steps")
        assert adjustment.base_factor > 1.0  # Summer should be higher
        
        # Test heart rate (should be stable year-round)
        adjustment = context_provider._get_seasonal_adjustment(7, "heart_rate")
        assert adjustment.base_factor == 1.0
        
    def test_calculate_confidence_level(self, context_provider):
        """Test confidence level calculation."""
        # High consistency (low CV) = high confidence
        consistent_values = [100, 101, 99, 100, 102]
        confidence = context_provider._calculate_confidence_level(consistent_values)
        assert confidence > 0.8
        
        # High variability (high CV) = low confidence
        variable_values = [50, 100, 150, 25, 200]
        confidence = context_provider._calculate_confidence_level(variable_values)
        assert confidence < 0.5
        
        # Edge cases
        assert context_provider._calculate_confidence_level([]) == 0.5
        assert context_provider._calculate_confidence_level([100]) == 0.5
        assert context_provider._calculate_confidence_level([0, 0, 0]) == 0.5
        
    def test_determine_exceptional_reason(self, context_provider):
        """Test exceptional reason determination."""
        values = [50, 52, 48, 51, 49]
        
        # Top percentile
        reason = context_provider._determine_exceptional_reason(100, values, 95, "steps")
        assert "Top 5%" in reason
        
        # Bottom percentile
        reason = context_provider._determine_exceptional_reason(10, values, 5, "steps")
        assert "Bottom 5%" in reason
        
        # Statistical outlier
        reason = context_provider._determine_exceptional_reason(150, values, 80, "steps")
        assert "statistically unusual" in reason.lower()
        
        # Normal performance
        reason = context_provider._determine_exceptional_reason(50, values, 50, "steps")
        assert reason is None
        
    def test_get_month_for_week(self, context_provider):
        """Test month calculation for week numbers."""
        # Week 1 should be in January
        month = context_provider._get_month_for_week(1, 2025)
        assert month == 1
        
        # Week 27 should be around June/July
        month = context_provider._get_month_for_week(27, 2025)
        assert 6 <= month <= 7
        
        # Week 52 should be in December
        month = context_provider._get_month_for_week(52, 2025)
        assert month == 12
        
    def test_create_empty_context(self, context_provider):
        """Test empty context creation."""
        context = context_provider._create_empty_context(1, 1, 2025, "steps")
        
        assert isinstance(context, WeekContext)
        assert context.week_number == 1
        assert context.month == 1
        assert context.year == 2025
        assert context.metric_name == "steps"
        assert context.percentile_rank == 50.0
        assert context.exceptional_reason == "No data available"
        
    def test_get_monthly_insights(self, context_provider):
        """Test monthly insights generation."""
        with patch.object(context_provider, '_get_monthly_weekly_data') as mock_data:
            mock_data.return_value = {1: 50000, 2: 52000, 3: 48000, 4: 55000}
            
            insights = context_provider.get_monthly_insights(1, 2025, "steps")
            
            assert "best_week" in insights
            assert "worst_week" in insights
            assert "monthly_trend" in insights
            assert "volatility_score" in insights
            assert insights["best_week"] == 4  # Highest value
            assert insights["worst_week"] == 3  # Lowest value
            
    def test_get_monthly_insights_no_data(self, context_provider):
        """Test monthly insights with no data."""
        with patch.object(context_provider, '_get_monthly_weekly_data') as mock_data:
            mock_data.return_value = {}
            
            insights = context_provider.get_monthly_insights(1, 2025, "steps")
            assert "error" in insights
            
    def test_find_most_consistent_period(self, context_provider):
        """Test finding most consistent consecutive weeks."""
        # Test data with a consistent period in the middle
        weekly_data = {1: 100, 2: 50, 3: 52, 4: 51, 5: 80}
        
        start_week, end_week = context_provider._find_most_consistent_period(weekly_data)
        
        # Weeks 2-4 should be most consistent (50, 52, 51)
        assert 2 <= start_week <= 3
        assert 3 <= end_week <= 4
        
    def test_find_most_consistent_period_edge_cases(self, context_provider):
        """Test consistency calculation edge cases."""
        # Single week
        result = context_provider._find_most_consistent_period({1: 100})
        assert result == (1, 1)
        
        # No data
        result = context_provider._find_most_consistent_period({})
        assert result == (1, 1)  # Should handle gracefully


class TestIntegration:
    """Integration tests for monthly context functionality."""
    
    @pytest.fixture
    def real_cache_manager(self):
        """Create real cache manager for integration testing."""
        return CacheManager(l2_db_path=":memory:")  # In-memory SQLite for testing
        
    def test_full_context_calculation_flow(self, real_cache_manager):
        """Test complete context calculation flow."""
        provider = MonthlyContextProvider(real_cache_manager)
        provider.set_monthly_goal("steps", 2025, 1, 500000)
        
        # First call should calculate and cache
        context1 = provider.get_week_context(1, 2025, "steps")
        assert isinstance(context1, WeekContext)
        
        # Second call should use cache
        context2 = provider.get_week_context(1, 2025, "steps")
        assert context1.week_number == context2.week_number
        assert context1.percentile_rank == context2.percentile_rank
        
    def test_multiple_metrics_context(self, real_cache_manager):
        """Test context calculation for multiple metrics."""
        provider = MonthlyContextProvider(real_cache_manager)
        
        metrics = ["steps", "heart_rate", "sleep_hours"]
        contexts = {}
        
        for metric in metrics:
            contexts[metric] = provider.get_week_context(1, 2025, metric)
            assert isinstance(contexts[metric], WeekContext)
            assert contexts[metric].metric_name == metric
            
        # Each metric should have different values
        percentiles = [ctx.percentile_rank for ctx in contexts.values()]
        assert len(set(percentiles)) > 1  # Should have some variation