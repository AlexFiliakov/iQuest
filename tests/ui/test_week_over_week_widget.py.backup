"""
UI tests for week-over-week trends widget.
Tests widget functionality, data display, and user interactions.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from src.ui.week_over_week_widget import (
    WeekOverWeekWidget, MomentumIndicatorWidget, StreakTrackerWidget, 
    SlopeGraphWidget
)
from src.analytics.week_over_week_trends import (
    WeekOverWeekTrends, TrendResult, StreakInfo, MomentumIndicator, 
    WeekTrendData, MomentumType, Prediction
)


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_trends_calculator():
    """Create mock trends calculator."""
    return Mock(spec=WeekOverWeekTrends)


@pytest.fixture
def sample_trend_result():
    """Create sample trend result."""
    return TrendResult(
        percent_change=12.5,
        absolute_change=800,
        momentum=MomentumType.ACCELERATING,
        streak=3,
        confidence=0.9,
        current_week_avg=7200,
        previous_week_avg=6400,
        trend_direction='up'
    )


@pytest.fixture
def sample_streak_info():
    """Create sample streak info."""
    return StreakInfo(
        current_streak=3,
        best_streak=5,
        streak_direction='improving',
        streak_start_date=date.today() - timedelta(weeks=3),
        is_current_streak_best=False
    )


@pytest.fixture
def sample_momentum():
    """Create sample momentum indicator."""
    return MomentumIndicator(
        momentum_type=MomentumType.ACCELERATING,
        acceleration_rate=2.5,
        change_velocity=5.0,
        trend_strength=0.8,
        confidence_level=0.9
    )


@pytest.fixture
def sample_trend_series():
    """Create sample trend series data."""
    trend_data = []
    base_date = date.today() - timedelta(weeks=8)
    
    for i in range(8):
        week_start = base_date + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        value = 6000 + i * 200  # Increasing trend
        
        percent_change = None
        if i > 0:
            prev_value = 6000 + (i-1) * 200
            percent_change = ((value - prev_value) / prev_value) * 100
        
        trend_data.append(WeekTrendData(
            week_start=week_start,
            week_end=week_end,
            value=value,
            percent_change_from_previous=percent_change,
            trend_direction='up' if percent_change and percent_change > 2 else 'stable',
            momentum=MomentumType.STEADY,
            is_incomplete_week=(i == 7),  # Last week incomplete
            missing_days=2 if i == 7 else 0
        ))
    
    return trend_data


@pytest.fixture
def sample_prediction():
    """Create sample prediction."""
    return Prediction(
        predicted_value=7800.0,
        confidence_interval_lower=7500.0,
        confidence_interval_upper=8100.0,
        prediction_confidence=0.75,
        methodology="linear_regression",
        factors_considered=["historical_trend", "data_consistency"]
    )


class TestMomentumIndicatorWidget:
    """Test momentum indicator widget."""
    
    def test_initialization(self, qapp):
        """Test widget initialization."""
        widget = MomentumIndicatorWidget()
        
        assert widget.momentum == MomentumType.STEADY
        assert widget.acceleration_rate == 0.0
        assert widget.confidence == 0.0
        assert widget.size().width() == 60
        assert widget.size().height() == 40
    
    def test_set_momentum_accelerating(self, qapp):
        """Test setting accelerating momentum."""
        widget = MomentumIndicatorWidget()
        
        widget.set_momentum(MomentumType.ACCELERATING, 2.5, 0.9)
        
        assert widget.momentum == MomentumType.ACCELERATING
        assert widget.acceleration_rate == 2.5
        assert widget.confidence == 0.9
    
    def test_set_momentum_decelerating(self, qapp):
        """Test setting decelerating momentum."""
        widget = MomentumIndicatorWidget()
        
        widget.set_momentum(MomentumType.DECELERATING, -1.5, 0.7)
        
        assert widget.momentum == MomentumType.DECELERATING
        assert widget.acceleration_rate == -1.5
        assert widget.confidence == 0.7
    
    def test_paint_event_no_crash(self, qapp):
        """Test paint event doesn't crash."""
        widget = MomentumIndicatorWidget()
        widget.show()
        
        # Trigger paint event
        widget.update()
        QTest.qWait(100)  # Wait for paint


class TestStreakTrackerWidget:
    """Test streak tracker widget."""
    
    def test_initialization(self, qapp):
        """Test widget initialization."""
        widget = StreakTrackerWidget()
        
        assert widget.streak_info is None
        assert "No active streak" in widget.current_streak_label.text()
        assert not widget.streak_progress.isVisible()
    
    def test_update_streak_improving(self, qapp, sample_streak_info):
        """Test updating with improving streak."""
        widget = StreakTrackerWidget()
        
        widget.update_streak(sample_streak_info)
        
        assert "3 weeks improving" in widget.current_streak_label.text()
        assert widget.streak_progress.isVisible()
        assert widget.streak_progress.value() == 3
        assert widget.streak_progress.maximum() == 5  # Best streak
        assert "Best: 5 weeks" in widget.best_streak_label.text()
    
    def test_update_streak_declining(self, qapp):
        """Test updating with declining streak."""
        widget = StreakTrackerWidget()
        
        declining_streak = StreakInfo(
            current_streak=2,
            best_streak=5,
            streak_direction='declining',
            streak_start_date=date.today() - timedelta(weeks=2),
            is_current_streak_best=False
        )
        
        widget.update_streak(declining_streak)
        
        assert "2 weeks declining" in widget.current_streak_label.text()
        assert widget.streak_progress.isVisible()
    
    def test_update_streak_best_current(self, qapp):
        """Test updating when current streak is best."""
        widget = StreakTrackerWidget()
        
        best_streak = StreakInfo(
            current_streak=6,
            best_streak=6,
            streak_direction='improving',
            streak_start_date=date.today() - timedelta(weeks=6),
            is_current_streak_best=True
        )
        
        widget.update_streak(best_streak)
        
        assert "🏆" in widget.current_streak_label.text()
        assert "BEST!" in widget.current_streak_label.text()
    
    def test_update_streak_no_active(self, qapp):
        """Test updating with no active streak."""
        widget = StreakTrackerWidget()
        
        no_streak = StreakInfo(
            current_streak=0,
            best_streak=3,
            streak_direction='none',
            streak_start_date=None,
            is_current_streak_best=False
        )
        
        widget.update_streak(no_streak)
        
        assert "No active streak" in widget.current_streak_label.text()
        assert not widget.streak_progress.isVisible()




class TestSlopeGraphWidget:
    """Test slope graph widget."""
    
    def test_initialization(self, qapp):
        """Test widget initialization."""
        widget = SlopeGraphWidget()
        
        assert widget.trend_data == []
        assert hasattr(widget, 'chart')  # Now uses EnhancedLineChart
    
    def test_set_data(self, qapp, sample_trend_series):
        """Test setting data and updating graph."""
        widget = SlopeGraphWidget()
        
        # This should not crash
        widget.set_data(sample_trend_series, "Steps")
        
        assert widget.trend_data == sample_trend_series
        assert widget.metric_name == "Steps"
    
    def test_update_graph_no_crash(self, qapp, sample_trend_series):
        """Test updating graph doesn't crash."""
        widget = SlopeGraphWidget()
        widget.show()
        
        widget.set_data(sample_trend_series, "Steps")
        
        # This should create the graph without crashing
        QTest.qWait(200)  # Wait for chart rendering


class TestWeekOverWeekWidget:
    """Test main week-over-week widget."""
    
    def test_initialization(self, qapp):
        """Test widget initialization."""
        widget = WeekOverWeekWidget()
        
        assert widget.trends_calculator is None
        assert hasattr(widget, 'current_week_card')
        assert hasattr(widget, 'change_card')
        assert hasattr(widget, 'momentum_indicator')
        assert hasattr(widget, 'streak_tracker')
        assert hasattr(widget, 'slope_graph')
        assert hasattr(widget, 'narrative_label')
        assert hasattr(widget, 'prediction_label')
    
    def test_set_trends_calculator(self, qapp, mock_trends_calculator):
        """Test setting trends calculator."""
        widget = WeekOverWeekWidget()
        
        widget.set_trends_calculator(mock_trends_calculator)
        
        assert widget.trends_calculator == mock_trends_calculator
    
    def test_create_summary_card(self, qapp):
        """Test creating summary card."""
        widget = WeekOverWeekWidget()
        
        card = widget.create_summary_card("Test Title", "123.4", "test subtitle")
        
        assert card.title() == "Test Title"
        assert hasattr(card, 'value_label')
        assert hasattr(card, 'subtitle_label')
        assert hasattr(card, 'mini_chart')
        assert card.value_label.text() == "123.4"
        assert card.subtitle_label.text() == "test subtitle"
    
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_summary_cards')
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_momentum_display')
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_streak_display')
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_slope_graph')
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_narrative')
    @patch('src.ui.week_over_week_widget.WeekOverWeekWidget.update_prediction')
    def test_update_analysis_success(self, mock_pred, mock_narr, mock_slope, 
                                   mock_streak, mock_momentum, mock_summary, 
                                   qapp, mock_trends_calculator, sample_trend_result,
                                   sample_momentum, sample_streak_info, 
                                   sample_trend_series, sample_prediction):
        """Test successful analysis update."""
        widget = WeekOverWeekWidget()
        widget.set_trends_calculator(mock_trends_calculator)
        
        # Setup mock returns
        mock_trends_calculator.calculate_week_change.return_value = sample_trend_result
        mock_trends_calculator.detect_momentum.return_value = sample_momentum
        mock_trends_calculator.get_current_streak.return_value = sample_streak_info
        mock_trends_calculator.get_trend_series.return_value = sample_trend_series
        mock_trends_calculator.predict_next_week.return_value = sample_prediction
        
        widget.update_analysis("steps", 15, 2024)
        
        # Verify all update methods were called
        mock_summary.assert_called_once()
        mock_momentum.assert_called_once()
        mock_streak.assert_called_once()
        mock_slope.assert_called_once()
        mock_narr.assert_called_once()
        mock_pred.assert_called_once()
    
    def test_update_analysis_no_calculator(self, qapp):
        """Test analysis update with no calculator."""
        widget = WeekOverWeekWidget()
        
        # Should not crash
        widget.update_analysis("steps", 15, 2024)
    
    def test_update_summary_cards(self, qapp, sample_trend_result, sample_trend_series):
        """Test updating summary cards."""
        widget = WeekOverWeekWidget()
        
        widget.update_summary_cards(sample_trend_result, sample_trend_series)
        
        assert "7200.0" in widget.current_week_card.value_label.text()
        assert "+12.5%" in widget.change_card.value_label.text()
    
    def test_update_momentum_display(self, qapp, sample_momentum):
        """Test updating momentum display."""
        widget = WeekOverWeekWidget()
        
        widget.update_momentum_display(sample_momentum)
        
        assert "Accelerating" in widget.momentum_label.text()
        assert "High confidence" in widget.momentum_label.text()
    
    def test_update_momentum_display_low_confidence(self, qapp):
        """Test updating momentum display with low confidence."""
        widget = WeekOverWeekWidget()
        
        low_confidence_momentum = MomentumIndicator(
            momentum_type=MomentumType.STEADY,
            acceleration_rate=0.1,
            change_velocity=0.5,
            trend_strength=0.3,
            confidence_level=0.2  # Low confidence
        )
        
        widget.update_momentum_display(low_confidence_momentum)
        
        assert "Steady" in widget.momentum_label.text()
        assert "Low confidence" in widget.momentum_label.text()
    
    def test_update_streak_display(self, qapp, sample_streak_info):
        """Test updating streak display."""
        widget = WeekOverWeekWidget()
        
        widget.update_streak_display(sample_streak_info)
        
        # This should update the streak tracker widget
        assert widget.streak_tracker.streak_info == sample_streak_info
    
    def test_update_slope_graph(self, qapp, sample_trend_series):
        """Test updating slope graph."""
        widget = WeekOverWeekWidget()
        
        widget.update_slope_graph(sample_trend_series, "Steps")
        
        assert widget.slope_graph.trend_data == sample_trend_series
        assert widget.slope_graph.metric_name == "Steps"
    
    def test_update_narrative(self, qapp, mock_trends_calculator, sample_trend_result,
                            sample_streak_info, sample_momentum):
        """Test updating narrative."""
        widget = WeekOverWeekWidget()
        widget.set_trends_calculator(mock_trends_calculator)
        
        mock_trends_calculator.generate_trend_narrative.return_value = "Test narrative text."
        
        widget.update_narrative("steps", sample_trend_result, sample_streak_info, sample_momentum)
        
        assert widget.narrative_label.text() == "Test narrative text."
        mock_trends_calculator.generate_trend_narrative.assert_called_once()
    
    def test_update_prediction_high_confidence(self, qapp, sample_prediction):
        """Test updating prediction with high confidence."""
        widget = WeekOverWeekWidget()
        
        widget.update_prediction(sample_prediction)
        
        prediction_text = widget.prediction_label.text()
        assert "7800.0" in prediction_text
        assert "7500.0 - 8100.0" in prediction_text
        assert "75%" in prediction_text
    
    def test_update_prediction_low_confidence(self, qapp):
        """Test updating prediction with low confidence."""
        widget = WeekOverWeekWidget()
        
        low_confidence_prediction = Prediction(
            predicted_value=7800.0,
            confidence_interval_lower=7500.0,
            confidence_interval_upper=8100.0,
            prediction_confidence=0.1,  # Low confidence
            methodology="linear_regression",
            factors_considered=["historical_trend"]
        )
        
        widget.update_prediction(low_confidence_prediction)
        
        assert "Insufficient data for reliable prediction" in widget.prediction_label.text()
    
    def test_show_error_state(self, qapp):
        """Test showing error state."""
        widget = WeekOverWeekWidget()
        
        widget.show_error_state()
        
        assert "Unable to analyze trends" in widget.narrative_label.text()
        assert "No forecast available" in widget.prediction_label.text()
    
    def test_widget_visibility(self, qapp):
        """Test widget visibility and layout."""
        widget = WeekOverWeekWidget()
        widget.show()
        
        # Basic visibility test
        assert widget.isVisible()
        
        # Check that major components are present
        assert widget.current_week_card.isVisible()
        assert widget.change_card.isVisible()
        assert widget.momentum_indicator.isVisible()
        assert widget.streak_tracker.isVisible()
        assert widget.slope_graph.isVisible()
        assert widget.narrative_label.isVisible()
        assert widget.prediction_label.isVisible()


class TestWidgetIntegration:
    """Test widget integration and interactions."""
    
    def test_full_widget_update_cycle(self, qapp, mock_trends_calculator,
                                    sample_trend_result, sample_momentum,
                                    sample_streak_info, sample_trend_series,
                                    sample_prediction):
        """Test full widget update cycle."""
        widget = WeekOverWeekWidget()
        widget.set_trends_calculator(mock_trends_calculator)
        widget.show()
        
        # Setup all mock returns
        mock_trends_calculator.calculate_week_change.return_value = sample_trend_result
        mock_trends_calculator.detect_momentum.return_value = sample_momentum
        mock_trends_calculator.get_current_streak.return_value = sample_streak_info
        mock_trends_calculator.get_trend_series.return_value = sample_trend_series
        mock_trends_calculator.predict_next_week.return_value = sample_prediction
        mock_trends_calculator.generate_trend_narrative.return_value = "Your steps improved by 12.5% this week and the improvement is accelerating. You're on a 3-week improvement streak!"
        
        # Perform update
        widget.update_analysis("steps", 15, 2024)
        
        # Wait for UI updates
        QTest.qWait(300)
        
        # Verify UI state
        assert "7200.0" in widget.current_week_card.value_label.text()
        assert "+12.5%" in widget.change_card.value_label.text()
        assert "improved by 12.5%" in widget.narrative_label.text()
        assert widget.streak_tracker.streak_info == sample_streak_info
    
    def test_widget_resize_handling(self, qapp):
        """Test widget handles resizing properly."""
        widget = WeekOverWeekWidget()
        widget.show()
        
        # Resize widget
        widget.resize(800, 600)
        QTest.qWait(100)
        
        # Should not crash and should be properly sized
        assert widget.size().width() == 800
        assert widget.size().height() == 600