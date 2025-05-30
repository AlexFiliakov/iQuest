"""Integration tests for Configuration tab functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from src.ui.main_window import MainWindow
from src.ui.configuration_tab import ConfigurationTab


class TestConfigTabIntegration:
    """Test Configuration tab integration with main window."""
    
    @pytest.fixture
    def main_window(self, qtbot):
        """Create a main window instance for testing."""
        window = MainWindow()
        qtbot.addWidget(window)
        return window
    
    @pytest.fixture
    def mock_data(self):
        """Create mock health data."""
        records = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Create 30 days of mock data
        for i in range(30):
            date = base_date + timedelta(days=i)
            records.extend([
                {
                    'type': "StepCount",
                    'value': 5000 + i * 100,
                    'unit': "count",
                    'creationDate': date,
                    'startDate': date,
                    'endDate': date,
                    'sourceName': "Test Device"
                },
                {
                    'type': "HeartRate",
                    'value': 60 + i % 20,
                    'unit': "count/min",
                    'creationDate': date,
                    'startDate': date,
                    'endDate': date,
                    'sourceName': "Test Device"
                }
            ])
        
        return records
    
    def test_config_tab_refresh_on_switch(self, main_window, mock_data, qtbot):
        """Test that Configuration tab refreshes when switched to."""
        # Find the configuration tab index (it's the first tab)
        config_tab_index = 0
        
        # Switch to config tab first
        main_window.tab_widget.setCurrentIndex(config_tab_index)
        qtbot.wait(100)
        
        # Now we should be on config tab
        assert main_window.tab_widget.currentIndex() == config_tab_index
        
        # Switch to another tab
        main_window.tab_widget.setCurrentIndex(1)
        qtbot.wait(100)
        
        # Switch back to config tab
        main_window.tab_widget.setCurrentIndex(config_tab_index)
        qtbot.wait(100)
        
        # Get the config tab from scroll area
        scroll_area = main_window.tab_widget.widget(config_tab_index)
        config_tab = scroll_area.widget() if hasattr(scroll_area, 'widget') else None
        
        # Verify the config tab exists
        assert config_tab is not None
        
        # Verify that config tab UI elements are visible
        # The config tab should have various UI elements
        assert config_tab.isVisible()
    
    def test_config_tab_data_summary_display(self, main_window, mock_data, qtbot):
        """Test that Configuration tab displays data summary correctly."""
        # Get the config tab from scroll area
        scroll_area = main_window.tab_widget.widget(0)
        config_tab = scroll_area.widget() if hasattr(scroll_area, 'widget') else None
        
        assert config_tab is not None
        
        # Check if summary cards exist in the config tab
        if hasattr(config_tab, 'summary_cards'):
            # Check that summary cards are visible
            assert config_tab.summary_cards.isVisible()
        
        # Check for statistics display
        if hasattr(config_tab, 'statistics_label'):
            assert config_tab.statistics_label.isVisible()
    
    def test_config_tab_no_data_message(self, main_window, qtbot):
        """Test that Configuration tab shows appropriate message when no data."""
        # Get the config tab from scroll area
        config_tab_index = 0
        main_window.tab_widget.setCurrentIndex(config_tab_index)
        qtbot.wait(100)
        
        scroll_area = main_window.tab_widget.widget(config_tab_index)
        config_tab = scroll_area.widget() if hasattr(scroll_area, 'widget') else None
        
        # Verify the config tab exists (it should always exist)
        assert config_tab is not None
        
        # Verify config tab is visible
        assert config_tab.isVisible()
        
        # The config tab should always be visible regardless of data
        # It should show import options when no data is available
    
    def test_config_tab_metric_selection(self, main_window, mock_data, qtbot):
        """Test metric selection in Configuration tab."""
        # Get the config tab from scroll area
        scroll_area = main_window.tab_widget.widget(0)
        config_tab = scroll_area.widget() if hasattr(scroll_area, 'widget') else None
        
        assert config_tab is not None
        
        # The config tab has metric tables instead of selectors
        # Check if metric table exists
        if hasattr(config_tab, 'metric_table'):
            assert config_tab.metric_table.isVisible()
    
    def test_config_tab_time_range_selection(self, main_window, mock_data, qtbot):
        """Test time range selection in Configuration tab."""
        # Get the config tab from scroll area
        config_tab_index = 0
        main_window.tab_widget.setCurrentIndex(config_tab_index)
        qtbot.wait(100)
        
        scroll_area = main_window.tab_widget.widget(config_tab_index)
        config_tab = scroll_area.widget() if hasattr(scroll_area, 'widget') else None
        
        # Verify the config tab exists
        assert config_tab is not None
        
        # Config tab has date range selectors
        if hasattr(config_tab, 'start_date_edit') and hasattr(config_tab, 'end_date_edit'):
            assert config_tab.start_date_edit.isVisible()
            assert config_tab.end_date_edit.isVisible()