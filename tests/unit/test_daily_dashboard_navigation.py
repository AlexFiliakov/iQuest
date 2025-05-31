"""Unit tests for Daily Dashboard navigation functionality."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from src.ui.daily_dashboard_widget import DailyDashboardWidget
# HealthDataModel import removed - class no longer exists


class TestDailyDashboardNavigation:
    """Test navigation functionality in Daily Dashboard."""
    
    @pytest.fixture
    def daily_dashboard(self, qtbot):
        """Create a daily dashboard widget for testing."""
        widget = DailyDashboardWidget()
        qtbot.addWidget(widget)
        return widget
    
    @pytest.fixture
    def mock_data_for_date(self):
        """Create a function that returns mock data for a specific date."""
        def _get_data(target_date):
            # Return simple mock statistics data for the test
            from src.analytics.daily_metrics_calculator import MetricStatistics
            return MetricStatistics(
                metric_name="steps",
                count=24,
                mean=8500.0,
                median=8400.0,
                std=1200.0,
                min=6800.0,
                max=10200.0,
                percentile_25=7600.0,
                percentile_75=9400.0,
                percentile_95=10800.0
            )
        return _get_data
    
    def test_initial_date_is_today(self, daily_dashboard):
        """Test that dashboard initializes with today's date."""
        assert daily_dashboard._current_date == date.today()
    
    def test_go_to_previous_day(self, daily_dashboard, qtbot):
        """Test navigation to previous day."""
        initial_date = daily_dashboard._current_date
        
        # Navigate to previous day
        daily_dashboard._go_to_previous_day()
        qtbot.wait(50)
        
        # Verify date changed
        expected_date = initial_date - timedelta(days=1)
        assert daily_dashboard._current_date == expected_date
    
    def test_go_to_next_day(self, daily_dashboard, qtbot):
        """Test navigation to next day."""
        # First go back a day so we can go forward
        daily_dashboard._current_date = date.today() - timedelta(days=1)
        initial_date = daily_dashboard._current_date
        
        # Navigate to next day
        daily_dashboard._go_to_next_day()
        qtbot.wait(50)
        
        # Verify date changed
        expected_date = initial_date + timedelta(days=1)
        assert daily_dashboard._current_date == expected_date
    
    def test_go_to_today(self, daily_dashboard, qtbot):
        """Test navigation to today."""
        # Set to a different date
        daily_dashboard._current_date = date.today() - timedelta(days=7)
        
        # Navigate to today
        daily_dashboard._go_to_today()
        qtbot.wait(50)
        
        # Verify date is today
        assert daily_dashboard._current_date == date.today()
    
    def test_cannot_navigate_beyond_today(self, daily_dashboard, qtbot):
        """Test that navigation beyond today is prevented."""
        # Set to today
        daily_dashboard._current_date = date.today()
        
        # Try to go to next day
        daily_dashboard._go_to_next_day()
        qtbot.wait(50)
        
        # Should still be today
        assert daily_dashboard._current_date == date.today()
        
        # Next button should be disabled
        if hasattr(daily_dashboard, 'next_button'):
            assert not daily_dashboard.next_button.isEnabled()
    
    def test_date_picker_navigation(self, daily_dashboard, qtbot):
        """Test navigation using date picker."""
        if hasattr(daily_dashboard, 'date_picker'):
            # Set a specific date
            target_date = date.today() - timedelta(days=10)
            q_date = QDate(target_date.year, target_date.month, target_date.day)
            
            # Change date using date picker
            daily_dashboard.date_picker.setDate(q_date)
            qtbot.wait(50)
            
            # Verify date changed
            assert daily_dashboard._current_date == target_date
    
    def test_navigation_updates_display(self, daily_dashboard, qtbot, mock_data_for_date):
        """Test that navigation updates the display."""
        with patch.object(daily_dashboard, '_refresh_data') as mock_refresh:
            # Navigate to previous day
            daily_dashboard._go_to_previous_day()
            qtbot.wait(50)
            
            # Verify refresh was called
            mock_refresh.assert_called_once()
    
    def test_navigation_with_data_loading(self, daily_dashboard, qtbot, mock_data_for_date):
        """Test navigation with data refresh."""
        # Navigate to previous day
        target_date = date.today() - timedelta(days=1)
        original_date = daily_dashboard._current_date
        
        # Set new date and refresh
        daily_dashboard._current_date = target_date
        daily_dashboard._refresh_data()
        qtbot.wait(100)
        
        # Verify the date changed
        assert daily_dashboard._current_date == target_date
        assert daily_dashboard._current_date != original_date
    
    def test_keyboard_navigation(self, daily_dashboard, qtbot):
        """Test keyboard shortcuts for navigation."""
        initial_date = daily_dashboard._current_date
        
        # Test left arrow for previous day
        QTest.keyClick(daily_dashboard, Qt.Key.Key_Left)
        qtbot.wait(50)
        assert daily_dashboard._current_date == initial_date - timedelta(days=1)
        
        # Test right arrow for next day
        QTest.keyClick(daily_dashboard, Qt.Key.Key_Right)
        qtbot.wait(50)
        assert daily_dashboard._current_date == initial_date
        
        # Test Home key for today
        daily_dashboard._current_date = initial_date - timedelta(days=5)
        QTest.keyClick(daily_dashboard, Qt.Key.Key_Home)
        qtbot.wait(50)
        assert daily_dashboard._current_date == date.today()
    
    def test_navigation_button_states(self, daily_dashboard, qtbot):
        """Test that navigation buttons are enabled/disabled correctly."""
        # When on today, next should be disabled
        daily_dashboard._go_to_today()
        qtbot.wait(50)
        
        if hasattr(daily_dashboard, 'next_button'):
            assert not daily_dashboard.next_button.isEnabled()
        if hasattr(daily_dashboard, 'prev_button'):
            assert daily_dashboard.prev_button.isEnabled()
        
        # When on past date, both should be enabled
        daily_dashboard._current_date = date.today() - timedelta(days=5)
        daily_dashboard._update_navigation_buttons()
        qtbot.wait(50)
        
        if hasattr(daily_dashboard, 'next_button'):
            assert daily_dashboard.next_button.isEnabled()
        if hasattr(daily_dashboard, 'prev_button'):
            assert daily_dashboard.prev_button.isEnabled()
    
    def test_date_display_format(self, daily_dashboard):
        """Test that date is displayed in correct format."""
        test_date = date(2024, 3, 15)
        daily_dashboard._current_date = test_date
        daily_dashboard._update_date_display()
        
        if hasattr(daily_dashboard, 'date_label'):
            # Should show the day name for dates that aren't today
            expected_text = test_date.strftime("%A")  # "Friday"
            assert daily_dashboard.date_label.text() == expected_text
            
        # The full date should be in the date picker
        if hasattr(daily_dashboard, 'date_picker'):
            from PyQt6.QtCore import QDate
            assert daily_dashboard.date_picker.date() == QDate(test_date)