"""
Tests for summary card components.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from src.ui.summary_cards import (
    SummaryCard, SimpleMetricCard, ComparisonCard, 
    GoalProgressCard, MiniChartCard, TrendIndicatorWidget, 
    ChangeIndicatorWidget
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


class TestSummaryCard:
    """Test base SummaryCard class."""
    
    @pytest.mark.parametrize("card_class,expected_type,required_attrs", [
        (SummaryCard, 'simple', []),
        (SimpleMetricCard, 'simple', ['title_label', 'value_label', 'trend_widget', 'subtitle_label']),
        (ComparisonCard, 'comparison', ['title_label', 'current_label', 'current_value', 'previous_label', 'previous_value', 'change_widget']),
        (GoalProgressCard, 'goal', ['title_label', 'progress_bar', 'progress_label', 'goal_label']),
        (MiniChartCard, 'chart', ['title_label', 'chart_widget', 'stats_widget']),
    ])
    def test_card_initialization(self, app, card_class, expected_type, required_attrs):
        """Test card initialization for all card types."""
        card = card_class(size='large', card_id='test_card')
        assert card.card_type == expected_type
        assert card.size == 'large'
        assert card.card_id == 'test_card'
        
        # Check required UI elements exist
        for attr in required_attrs:
            assert hasattr(card, attr), f"{card_class.__name__} missing required attribute: {attr}"
    
    def test_default_initialization(self, app):
        """Test default initialization values."""
        card = SummaryCard()
        assert card.card_type == 'simple'
        assert card.size == 'medium'
        assert card.card_id == ""
    
    def test_size_configurations(self, app):
        """Test size configuration application."""
        sizes = ['small', 'medium', 'large']
        
        for size in sizes:
            card = SummaryCard(size=size)
            config = card.SIZE_CONFIGS[size]
            
            assert card.minimumWidth() == config['min_width']
            assert card.minimumHeight() == config['min_height']
    
    def test_animated_value_property(self, app):
        """Test animated value property."""
        card = SummaryCard()
        
        # Test setter/getter
        card.animated_value = 42.5
        assert card.animated_value == 42.5
    
    def test_click_signal(self, app):
        """Test card click signal emission."""
        card = SummaryCard(card_id='test_card')
        signal_received = []
        
        def slot(card_id):
            signal_received.append(card_id)
        
        card.clicked.connect(slot)
        
        # Simulate mouse click
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        
        assert len(signal_received) == 1
        assert signal_received[0] == 'test_card'


class TestSimpleMetricCard:
    """Test SimpleMetricCard implementation."""
    
    def test_content_update_without_animation(self, app):
        """Test content update without animation."""
        card = SimpleMetricCard()
        
        data = {
            'title': 'Steps Today',
            'value': 12345.0,
            'subtitle': 'Daily Goal: 10,000',
            'current_value': 12345.0,
            'previous_value': 10000.0
        }
        
        card.update_content(data, animate=False)
        
        assert card.title_label.text() == 'Steps Today'
        assert card.subtitle_label.text() == 'Daily Goal: 10,000'
        assert '12345' in card.value_label.text()
    
    def test_content_update_with_animation(self, app):
        """Test content update with animation."""
        card = SimpleMetricCard()
        
        # Set initial value
        card.value_label.setText('1000.0')
        
        data = {
            'title': 'Steps Today',
            'value': 5000.0,
            'current_value': 5000.0,
            'previous_value': 4000.0
        }
        
        card.update_content(data, animate=True)
        
        # Check animation was started
        assert card.value_animator.state() == card.value_animator.State.Running
        
        # Check title updated immediately
        assert card.title_label.text() == 'Steps Today'
    
    def test_value_display_update(self, app):
        """Test value display update during animation."""
        card = SimpleMetricCard()
        
        card.update_value_display(1234.5)
        assert '1234.5' in card.value_label.text()


class TestComparisonCard:
    """Test ComparisonCard implementation."""
    
    def test_content_update(self, app):
        """Test comparison card content update."""
        card = ComparisonCard()
        
        data = {
            'title': 'Weekly Comparison',
            'current_value': 75000.0,
            'previous_value': 65000.0
        }
        
        card.update_content(data)
        
        assert card.title_label.text() == 'Weekly Comparison'
        assert '75000' in card.current_value.text()
        assert '65000' in card.previous_value.text()


class TestGoalProgressCard:
    """Test GoalProgressCard implementation."""
    
    def test_content_update_without_animation(self, app):
        """Test progress card content update without animation."""
        card = GoalProgressCard()
        
        data = {
            'title': 'Weekly Steps Goal',
            'current_value': 35000.0,
            'target_value': 50000.0
        }
        
        card.update_content(data, animate=False)
        
        assert card.title_label.text() == 'Weekly Steps Goal'
        assert '35000' in card.progress_label.text()
        assert '50000' in card.progress_label.text()
        assert card.progress_bar.value() == 70  # 35000/50000 * 100
        assert '70.0%' in card.percentage_label.text()
    
    def test_content_update_with_animation(self, app):
        """Test progress card content update with animation."""
        card = GoalProgressCard()
        
        data = {
            'current_value': 30000.0,
            'target_value': 40000.0
        }
        
        card.update_content(data, animate=True)
        
        # Check animation was started
        assert card.value_animator.state() == card.value_animator.State.Running
    
    def test_progress_calculation_edge_cases(self, app):
        """Test progress calculation with edge cases."""
        card = GoalProgressCard()
        
        # Test division by zero
        data = {
            'current_value': 100.0,
            'target_value': 0.0
        }
        card.update_content(data, animate=False)
        assert card.progress_bar.value() == 0
        
        # Test exceeding goal
        data = {
            'current_value': 150.0,
            'target_value': 100.0
        }
        card.update_content(data, animate=False)
        assert card.progress_bar.value() == 100  # Capped at 100%


class TestMiniChartCard:
    """Test MiniChartCard implementation."""
    
    def test_content_update(self, app):
        """Test mini chart card content update."""
        card = MiniChartCard()
        
        data = {
            'title': 'Heart Rate Trend',
            'value': 72.5,
            'min_value': 60.0,
            'max_value': 85.0
        }
        
        card.update_content(data)
        
        assert card.title_label.text() == 'Heart Rate Trend'
        assert '72.5' in card.value_label.text()
        assert 'Min: 60.0' in card.min_label.text()
        assert 'Max: 85.0' in card.max_label.text()


class TestTrendIndicatorWidget:
    """Test TrendIndicatorWidget implementation."""
    
    def test_trend_calculation_positive(self, app):
        """Test positive trend calculation."""
        widget = TrendIndicatorWidget()
        
        widget.set_trend(120.0, 100.0)  # 20% increase
        
        assert widget.trend_value == 20.0
        assert '↑' in widget.label.text() or '↗' in widget.label.text()
        assert '20.0%' in widget.label.text()
    
    def test_trend_calculation_negative(self, app):
        """Test negative trend calculation."""
        widget = TrendIndicatorWidget()
        
        widget.set_trend(80.0, 100.0)  # 20% decrease
        
        assert widget.trend_value == -20.0
        assert '↓' in widget.label.text() or '↘' in widget.label.text()
        assert '20.0%' in widget.label.text()
    
    def test_trend_calculation_no_change(self, app):
        """Test no change trend calculation."""
        widget = TrendIndicatorWidget()
        
        widget.set_trend(100.0, 100.0)  # No change
        
        assert widget.trend_value == 0.0
        assert '→' in widget.label.text()
        assert '0.0%' in widget.label.text()
    
    def test_trend_calculation_zero_previous(self, app):
        """Test trend calculation with zero previous value."""
        widget = TrendIndicatorWidget()
        
        widget.set_trend(50.0, 0.0)  # Previous is zero
        
        assert widget.trend_value == 0.0
        assert '→' in widget.label.text()
    
    def test_trend_display_thresholds(self, app):
        """Test trend display for different thresholds."""
        widget = TrendIndicatorWidget()
        
        # Test significant increase (>5%)
        widget.set_trend(110.0, 100.0)
        assert '↗' in widget.label.text()
        
        # Test small increase (0-5%)
        widget.set_trend(102.0, 100.0)
        assert '↑' in widget.label.text()
        
        # Test significant decrease (<-5%)
        widget.set_trend(90.0, 100.0)
        assert '↘' in widget.label.text()
        
        # Test small decrease (-5% to 0%)
        widget.set_trend(98.0, 100.0)
        assert '↓' in widget.label.text()


class TestChangeIndicatorWidget:
    """Test ChangeIndicatorWidget implementation."""
    
    def test_positive_change(self, app):
        """Test positive change display."""
        widget = ChangeIndicatorWidget()
        
        widget.set_change(120.0, 100.0)
        
        assert '+20.0' in widget.change_label.text()
        assert '(+20.0%)' in widget.percentage_label.text()
    
    def test_negative_change(self, app):
        """Test negative change display."""
        widget = ChangeIndicatorWidget()
        
        widget.set_change(80.0, 100.0)
        
        assert '-20.0' in widget.change_label.text()
        assert '(-20.0%)' in widget.percentage_label.text()
    
    def test_no_change(self, app):
        """Test no change display."""
        widget = ChangeIndicatorWidget()
        
        widget.set_change(100.0, 100.0)
        
        assert 'No change' in widget.change_label.text()
        assert '(+0.0%)' in widget.percentage_label.text()
    
    def test_zero_previous_value(self, app):
        """Test change calculation with zero previous value."""
        widget = ChangeIndicatorWidget()
        
        widget.set_change(50.0, 0.0)
        
        assert '+50.0' in widget.change_label.text()
        assert '(+0.0%)' in widget.percentage_label.text()


class TestCardIntegration:
    """Test integration scenarios between different card types."""
    
    def test_multiple_cards_sizing(self, app):
        """Test multiple cards with different sizes."""
        cards = [
            SimpleMetricCard(size='small'),
            ComparisonCard(size='medium'),
            GoalProgressCard(size='large'),
            MiniChartCard(size='medium')
        ]
        
        # Verify sizes are applied correctly
        assert cards[0].minimumWidth() == 150  # small
        assert cards[1].minimumWidth() == 200  # medium
        assert cards[2].minimumWidth() == 300  # large
        assert cards[3].minimumWidth() == 200  # medium
    
    def test_card_animation_coordination(self, app):
        """Test that multiple card animations can run simultaneously."""
        cards = [
            SimpleMetricCard(),
            GoalProgressCard()
        ]
        
        # Start animations on both cards
        cards[0].update_content({'value': 100.0}, animate=True)
        cards[1].update_content({'current_value': 50.0, 'target_value': 100.0}, animate=True)
        
        # Both animations should be running
        assert cards[0].value_animator.state() == cards[0].value_animator.State.Running
        assert cards[1].value_animator.state() == cards[1].value_animator.State.Running
    
    def test_consistent_styling_across_cards(self, app):
        """Test that all card types use consistent styling."""
        cards = [
            SimpleMetricCard(),
            ComparisonCard(),
            GoalProgressCard(),
            MiniChartCard()
        ]
        
        # All cards should have the same object name for styling
        for card in cards:
            assert card.card_frame.objectName() == "summaryCard"
    
    @pytest.mark.parametrize("card_class", [
        SimpleMetricCard, ComparisonCard, GoalProgressCard, MiniChartCard
    ])
    def test_card_click_signals(self, app, card_class):
        """Test that all card types emit click signals."""
        card = card_class(card_id='test_card')
        signal_received = []
        
        def slot(card_id):
            signal_received.append(card_id)
        
        card.clicked.connect(slot)
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        
        assert len(signal_received) == 1
        assert signal_received[0] == 'test_card'


class TestCardAccessibility:
    """Test accessibility features of summary cards."""
    
    def test_keyboard_focus(self, app):
        """Test that cards can receive keyboard focus."""
        card = SimpleMetricCard()
        
        # Cards should be focusable for accessibility
        assert card.focusPolicy() != Qt.FocusPolicy.NoFocus
    
    def test_tooltip_support(self, app):
        """Test that cards support tooltips."""
        card = SimpleMetricCard()
        
        # Set tooltip
        card.setToolTip("Steps taken today")
        assert card.toolTip() == "Steps taken today"
    
    def test_screen_reader_support(self, app):
        """Test that cards provide accessible names."""
        card = SimpleMetricCard()
        card.update_content({
            'title': 'Daily Steps',
            'value': 8500.0,
            'subtitle': 'Goal: 10,000'
        })
        
        # Accessible name should include key information
        card.setAccessibleName(f"{card.title_label.text()}: {card.value_label.text()}")
        assert 'Daily Steps' in card.accessibleName()
        assert '8500' in card.accessibleName()


class TestPerformance:
    """Test performance characteristics of summary cards."""
    
    def test_many_cards_creation(self, app):
        """Test creating many cards doesn't cause performance issues."""
        cards = []
        
        # Create 50 cards of different types
        for i in range(50):
            card_type = [SimpleMetricCard, ComparisonCard, GoalProgressCard, MiniChartCard][i % 4]
            cards.append(card_type(card_id=f'card_{i}'))
        
        assert len(cards) == 50
        
        # All cards should be properly initialized
        for card in cards:
            assert card.card_frame is not None
            assert card.style_manager is not None
    
    def test_rapid_content_updates(self, app):
        """Test rapid content updates don't cause issues."""
        card = SimpleMetricCard()
        
        # Perform many rapid updates
        for i in range(20):
            card.update_content({
                'title': f'Test {i}',
                'value': float(i * 100),
                'current_value': float(i * 100),
                'previous_value': float((i-1) * 100) if i > 0 else 0.0
            }, animate=False)
        
        # Card should still be functional
        assert 'Test 19' in card.title_label.text()
        assert '1900' in card.value_label.text()


if __name__ == "__main__":
    pytest.main([__file__])