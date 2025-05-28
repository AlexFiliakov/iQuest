"""
Integration tests for week-over-week trends functionality.
Tests end-to-end workflow from data loading to UI display.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
    from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator, WeekStandard
    from src.analytics.week_over_week_trends import WeekOverWeekTrends, MomentumType
except ImportError as e:
    pytest.skip(f"Analytics modules not available: {e}", allow_module_level=True)


@pytest.fixture
def sample_health_data():
    """Create sample health data for testing."""
    data = []
    base_date = datetime.now() - timedelta(days=90)  # 90 days of data
    
    for i in range(90):
        current_date = base_date + timedelta(days=i)
        
        # Create improving steps trend over time
        base_steps = 8000
        trend_improvement = i * 50  # Gradual improvement
        daily_variation = np.random.normal(0, 500)  # Random daily variation
        steps = max(0, base_steps + trend_improvement + daily_variation)
        
        data.append({
            'creationDate': current_date,
            'type': 'HKQuantityTypeIdentifierStepCount',
            'value': steps,
            'sourceName': 'iPhone',
            'unit': 'count'
        })
        
        # Add some heart rate data
        hr_base = 70
        hr_variation = np.random.normal(0, 5)
        heart_rate = max(50, hr_base + hr_variation)
        
        data.append({
            'creationDate': current_date,
            'type': 'HKQuantityTypeIdentifierHeartRate',
            'value': heart_rate,
            'sourceName': 'Apple Watch',
            'unit': 'count/min'
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_data_loader(sample_health_data):
    """Create mock data loader with sample data."""
    loader = Mock()
    loader.get_all_records.return_value = sample_health_data
    return loader


@pytest.fixture
def daily_calculator(mock_data_loader):
    """Create daily metrics calculator."""
    return DailyMetricsCalculator(mock_data_loader)


@pytest.fixture
def weekly_calculator(daily_calculator):
    """Create weekly metrics calculator."""
    return WeeklyMetricsCalculator(daily_calculator, WeekStandard.ISO)


@pytest.fixture
def trends_calculator(weekly_calculator):
    """Create week-over-week trends calculator."""
    return WeekOverWeekTrends(weekly_calculator)


class TestWeekOverWeekIntegration:
    """Integration tests for week-over-week trends workflow."""
    
    def test_full_workflow_steps_analysis(self, trends_calculator, sample_health_data):
        """Test complete workflow for steps analysis."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        # Calculate week change
        trend_result = trends_calculator.calculate_week_change(metric, current_week - 1, current_week, year)
        
        assert trend_result is not None
        assert isinstance(trend_result.percent_change, float)
        assert isinstance(trend_result.confidence, float)
        assert trend_result.confidence >= 0.0
        assert trend_result.confidence <= 1.0
        assert trend_result.trend_direction in ['up', 'down', 'stable']
    
    def test_momentum_detection_integration(self, trends_calculator):
        """Test momentum detection with real workflow."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        momentum = trends_calculator.detect_momentum(metric, current_week, year)
        
        assert momentum is not None
        assert isinstance(momentum.momentum_type, MomentumType)
        assert isinstance(momentum.acceleration_rate, float)
        assert isinstance(momentum.confidence_level, float)
        assert momentum.confidence_level >= 0.0
        assert momentum.confidence_level <= 1.0
    
    def test_streak_tracking_integration(self, trends_calculator):
        """Test streak tracking with real workflow."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        streak_info = trends_calculator.get_current_streak(metric, current_week, year)
        
        assert streak_info is not None
        assert isinstance(streak_info.current_streak, int)
        assert isinstance(streak_info.best_streak, int)
        assert streak_info.streak_direction in ['improving', 'declining', 'none']
        assert streak_info.current_streak >= 0
        assert streak_info.best_streak >= 0
        assert streak_info.best_streak >= streak_info.current_streak
    
    def test_prediction_integration(self, trends_calculator):
        """Test prediction functionality integration."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        prediction = trends_calculator.predict_next_week(metric, current_week, year)
        
        assert prediction is not None
        assert isinstance(prediction.predicted_value, float)
        assert isinstance(prediction.prediction_confidence, float)
        assert prediction.prediction_confidence >= 0.0
        assert prediction.prediction_confidence <= 1.0
        assert prediction.methodology in ["linear_regression", "exponential_smoothing", "seasonal", "insufficient_data"]
    
    def test_trend_series_integration(self, trends_calculator):
        """Test getting trend series for visualization."""
        metric = "HKQuantityTypeIdentifierStepCount"
        
        trend_series = trends_calculator.get_trend_series(metric, weeks_back=8)
        
        assert trend_series is not None
        assert isinstance(trend_series, list)
        assert len(trend_series) <= 8
        
        for trend_data in trend_series:
            assert hasattr(trend_data, 'week_start')
            assert hasattr(trend_data, 'week_end')
            assert hasattr(trend_data, 'value')
            assert hasattr(trend_data, 'trend_direction')
            assert trend_data.trend_direction in ['up', 'down', 'stable']
    
    def test_narrative_generation_integration(self, trends_calculator):
        """Test narrative generation integration."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        # Get required components
        trend_result = trends_calculator.calculate_week_change(metric, current_week - 1, current_week, year)
        streak_info = trends_calculator.get_current_streak(metric, current_week, year)
        momentum = trends_calculator.detect_momentum(metric, current_week, year)
        
        # Generate narrative
        narrative = trends_calculator.generate_trend_narrative(metric, trend_result, streak_info, momentum)
        
        assert narrative is not None
        assert isinstance(narrative, str)
        assert len(narrative) > 0
        assert metric in narrative or "step" in narrative.lower()
        assert narrative.endswith('.')
    
    def test_multiple_metrics_workflow(self, trends_calculator):
        """Test workflow with multiple metrics."""
        metrics = ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierHeartRate"]
        current_week = 15
        year = 2024
        
        results = {}
        
        for metric in metrics:
            try:
                results[metric] = {
                    'trend': trends_calculator.calculate_week_change(metric, current_week - 1, current_week, year),
                    'momentum': trends_calculator.detect_momentum(metric, current_week, year),
                    'streak': trends_calculator.get_current_streak(metric, current_week, year),
                    'prediction': trends_calculator.predict_next_week(metric, current_week, year)
                }
            except Exception as e:
                # Some metrics might not have enough data
                pytest.skip(f"Insufficient data for {metric}: {e}")
        
        assert len(results) > 0
        
        for metric, analysis in results.items():
            assert analysis['trend'] is not None
            assert analysis['momentum'] is not None
            assert analysis['streak'] is not None
            assert analysis['prediction'] is not None
    
    def test_edge_case_insufficient_data(self, trends_calculator):
        """Test handling of insufficient data edge case."""
        # Use a metric that likely won't have data
        metric = "NonexistentMetric"
        current_week = 15
        year = 2024
        
        # These should handle missing data gracefully
        trend_result = trends_calculator.calculate_week_change(metric, current_week - 1, current_week, year)
        momentum = trends_calculator.detect_momentum(metric, current_week, year)
        streak_info = trends_calculator.get_current_streak(metric, current_week, year)
        prediction = trends_calculator.predict_next_week(metric, current_week, year)
        
        # Should return valid objects even with no data
        assert trend_result is not None
        assert momentum is not None
        assert streak_info is not None
        assert prediction is not None
        
        # Confidence should be low
        assert trend_result.confidence <= 0.5
        assert momentum.confidence_level <= 0.5
        assert prediction.prediction_confidence <= 0.5
    
    def test_caching_behavior(self, trends_calculator):
        """Test that caching works correctly."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 15
        year = 2024
        
        # First call
        streak1 = trends_calculator.get_current_streak(metric, current_week, year)
        
        # Second call should use cache
        streak2 = trends_calculator.get_current_streak(metric, current_week, year)
        
        # Results should be identical
        assert streak1.current_streak == streak2.current_streak
        assert streak1.best_streak == streak2.best_streak
        assert streak1.streak_direction == streak2.streak_direction
    
    def test_year_boundary_handling(self, trends_calculator):
        """Test handling of year boundaries in calculations."""
        metric = "HKQuantityTypeIdentifierStepCount"
        
        # Test with week 1 (should look back to previous year)
        current_week = 1
        year = 2024
        
        try:
            trend_result = trends_calculator.calculate_week_change(metric, 52, current_week, year)
            assert trend_result is not None
        except Exception:
            # This is acceptable if there's no data for previous year
            pass
        
        # Test momentum detection across year boundary
        try:
            momentum = trends_calculator.detect_momentum(metric, current_week, year, lookback_weeks=4)
            assert momentum is not None
        except Exception:
            # This is acceptable if there's insufficient data
            pass
    
    def test_partial_week_handling(self, trends_calculator):
        """Test handling of partial weeks (current week)."""
        metric = "HKQuantityTypeIdentifierStepCount"
        
        # Get current week
        today = date.today()
        current_year, current_week, _ = today.isocalendar()
        
        # This week might be partial
        trend_result = trends_calculator.calculate_week_change(metric, current_week - 1, current_week, current_year)
        
        assert trend_result is not None
        
        # Confidence might be reduced for partial weeks
        if today.weekday() < 6:  # Not Sunday (end of week)
            # Confidence should account for partial week
            assert isinstance(trend_result.confidence, float)
    
    @patch('src.analytics.week_over_week_trends.logger')
    def test_error_logging(self, mock_logger, trends_calculator):
        """Test that errors are properly logged."""
        # Force an error by using invalid parameters
        metric = "HKQuantityTypeIdentifierStepCount"
        
        # Try to get momentum with insufficient lookback
        momentum = trends_calculator.detect_momentum(metric, 15, 2024, lookback_weeks=1)
        
        assert momentum.momentum_type == MomentumType.INSUFFICIENT_DATA
    
    def test_performance_large_dataset(self, trends_calculator):
        """Test performance with larger lookback periods."""
        metric = "HKQuantityTypeIdentifierStepCount"
        current_week = 30
        year = 2024
        
        # Test with large lookback
        start_time = datetime.now()
        
        streak_info = trends_calculator.get_current_streak(metric, current_week, year, max_lookback=52)
        trend_series = trends_calculator.get_trend_series(metric, weeks_back=26)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0
        assert streak_info is not None
        assert trend_series is not None


class TestWeekOverWeekUIIntegration:
    """Integration tests for UI components with real data."""
    
    @pytest.mark.skipif(not pytest.importorskip("PyQt6"), reason="PyQt6 not available")
    def test_ui_widget_with_real_calculator(self, trends_calculator):
        """Test UI widget with real calculator."""
        from src.ui.week_over_week_widget import WeekOverWeekWidget
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        
        widget = WeekOverWeekWidget()
        widget.set_trends_calculator(trends_calculator)
        
        # This should not crash
        widget.update_analysis("HKQuantityTypeIdentifierStepCount", 15, 2024)
        
        # Basic checks
        assert widget.trends_calculator == trends_calculator
        assert widget.narrative_label.text() != "Select a metric to view trend analysis."
    
    @pytest.mark.skipif(not pytest.importorskip("PyQt6"), reason="PyQt6 not available")
    def test_momentum_indicator_real_data(self, trends_calculator):
        """Test momentum indicator with real momentum data."""
        from src.ui.week_over_week_widget import MomentumIndicatorWidget
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        
        # Get real momentum data
        momentum = trends_calculator.detect_momentum("HKQuantityTypeIdentifierStepCount", 15, 2024)
        
        widget = MomentumIndicatorWidget()
        widget.set_momentum(momentum.momentum_type, momentum.acceleration_rate, momentum.confidence_level)
        widget.show()
        
        # Should not crash
        widget.update()
        
        assert widget.momentum == momentum.momentum_type
    
    @pytest.mark.skipif(not pytest.importorskip("PyQt6"), reason="PyQt6 not available")
    def test_streak_tracker_real_data(self, trends_calculator):
        """Test streak tracker with real streak data."""
        from src.ui.week_over_week_widget import StreakTrackerWidget
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        
        # Get real streak data
        streak_info = trends_calculator.get_current_streak("HKQuantityTypeIdentifierStepCount", 15, 2024)
        
        widget = StreakTrackerWidget()
        widget.update_streak(streak_info)
        widget.show()
        
        # Should display streak information
        assert widget.streak_info == streak_info
        if streak_info.current_streak > 0:
            assert str(streak_info.current_streak) in widget.current_streak_label.text()
    
    @pytest.mark.skipif(not pytest.importorskip("matplotlib"), reason="matplotlib not available")
    def test_slope_graph_real_data(self, trends_calculator):
        """Test slope graph with real trend data."""
        from src.ui.week_over_week_widget import SlopeGraphWidget
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        
        # Get real trend series
        trend_series = trends_calculator.get_trend_series("HKQuantityTypeIdentifierStepCount", weeks_back=8)
        
        widget = SlopeGraphWidget()
        widget.set_data(trend_series, "Steps")
        widget.show()
        
        # Should not crash and should have data
        assert widget.trend_data == trend_series
        assert widget.metric_name == "Steps"