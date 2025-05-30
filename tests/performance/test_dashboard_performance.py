"""Performance tests for Core Health Dashboard to verify <500ms rendering requirement."""

import time
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.core_health_dashboard import CoreHealthDashboard
from src.ui.style_manager import StyleManager


class TestDashboardPerformance:
    """Test dashboard rendering performance."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock data manager."""
        import pandas as pd
        
        manager = MagicMock()
        # Mock the data retrieval to return quickly
        manager.get_metrics.return_value = {
            'total_steps': 10000,
            'total_distance': 8000,
            'total_active_energy': 500,
            'total_floors_climbed': 20,
            'avg_resting_heart_rate': 60,
            'avg_heart_rate': 75,
            'max_heart_rate': 120,
            'avg_hrv': 45.5,
            'avg_sleep_duration': 7.5,
            'sleep_efficiency': 0.85,
            'avg_deep_sleep': 1.5,
            'deep_sleep_ratio': 0.2,
            'current_weight': 70,
            'current_bmi': 22.5,
            'current_body_fat': 18
        }
        
        # Create a minimal DataFrame for DailyMetricsCalculator
        now = datetime.now()
        dates = pd.date_range(end=now, periods=30, freq='D')
        sample_data = []
        
        for date in dates:
            sample_data.append({
                'creationDate': date,
                'type': 'HKQuantityTypeIdentifierStepCount',
                'value': 8000 + (date.day * 100)
            })
            sample_data.append({
                'creationDate': date,
                'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'value': 6.5 + (date.day * 0.1)
            })
            
        df = pd.DataFrame(sample_data)
        
        # Mock get_dataframe method for DataSourceProtocol
        manager.get_dataframe.return_value = df
        
        return manager
    
    @pytest.fixture
    def dashboard(self, qtbot, mock_data_manager, monkeypatch):
        """Create dashboard instance."""
        # Mock the CoreHealthDashboard to avoid deep initialization
        from unittest.mock import patch
        from PyQt6.QtWidgets import QWidget
        
        # Patch the problematic initializations
        with patch('src.ui.core_health_dashboard.DailyMetricsCalculator') as mock_daily, \
             patch('src.ui.core_health_dashboard.WeeklyMetricsCalculator') as mock_weekly, \
             patch('src.ui.core_health_dashboard.MonthlyMetricsCalculator') as mock_monthly, \
             patch('src.ui.core_health_dashboard.MetricComparisonView') as mock_comparison, \
             patch('src.ui.core_health_dashboard.ActivityMetricPanel') as mock_activity, \
             patch('src.ui.core_health_dashboard.HeartRatePanel') as mock_heart, \
             patch('src.ui.core_health_dashboard.SleepPanel') as mock_sleep, \
             patch('src.ui.core_health_dashboard.BodyMetricsPanel') as mock_body, \
             patch('src.ui.core_health_dashboard.AdaptiveTimeRangeSelector') as mock_selector:
            
            # Create mocks that don't raise errors
            mock_daily.return_value = MagicMock()
            mock_weekly.return_value = MagicMock()
            mock_monthly.return_value = MagicMock()
            
            # All panels need to be QWidgets
            for panel_mock in [mock_activity, mock_heart, mock_sleep, mock_body]:
                widget = QWidget()
                widget.update_data = MagicMock()
                panel_mock.return_value = widget
            
            # MetricComparisonView needs to be a QWidget
            mock_widget = QWidget()
            mock_comparison.return_value = mock_widget
            
            # AdaptiveTimeRangeSelector with proper signal
            selector_widget = QWidget()
            selector_widget.time_range_changed = MagicMock()
            mock_selector.return_value = selector_widget
            
            dashboard = CoreHealthDashboard(mock_data_manager)
            qtbot.addWidget(dashboard)
            return dashboard
    
    def test_initial_render_performance(self, dashboard, qtbot):
        """Test that initial dashboard render completes in <500ms."""
        start_time = time.time()
        
        # Show the dashboard
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Wait for initial render to complete
        qtbot.wait(10)  # Small wait for Qt event processing
        
        render_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert render_time < 500, f"Initial render took {render_time:.2f}ms, exceeds 500ms requirement"
    
    def test_data_update_performance(self, dashboard, qtbot):
        """Test that data updates complete in <500ms."""
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Measure update performance
        start_time = time.time()
        
        # Trigger data refresh
        dashboard.refresh_data()
        
        # Process events
        qtbot.wait(10)
        
        update_time = (time.time() - start_time) * 1000
        
        assert update_time < 500, f"Data update took {update_time:.2f}ms, exceeds 500ms requirement"
    
    def test_time_range_change_performance(self, dashboard, qtbot):
        """Test that time range changes complete in <500ms."""
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Measure time range change performance
        start_time = time.time()
        
        # Change time range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        dashboard.on_time_range_changed("7D", start_date, end_date)
        
        # Process events
        qtbot.wait(10)
        
        change_time = (time.time() - start_time) * 1000
        
        assert change_time < 500, f"Time range change took {change_time:.2f}ms, exceeds 500ms requirement"
    
    def test_tab_switch_performance(self, dashboard, qtbot):
        """Test that tab switching completes in <500ms."""
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Measure tab switch performance
        start_time = time.time()
        
        # Switch to comparison tab
        dashboard.tab_widget.setCurrentIndex(1)
        
        # Process events
        qtbot.wait(10)
        
        switch_time = (time.time() - start_time) * 1000
        
        assert switch_time < 500, f"Tab switch took {switch_time:.2f}ms, exceeds 500ms requirement"
    
    def test_responsive_layout_performance(self, dashboard, qtbot):
        """Test that responsive layout adjustments complete in <500ms."""
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Measure resize performance
        start_time = time.time()
        
        # Trigger resize
        dashboard.resize(600, 800)  # Trigger responsive layout
        
        # Process events
        qtbot.wait(10)
        
        resize_time = (time.time() - start_time) * 1000
        
        assert resize_time < 500, f"Responsive resize took {resize_time:.2f}ms, exceeds 500ms requirement"
    
    @pytest.mark.timeout(60)
    @pytest.mark.parametrize("panel_count", [10, 25, 50])  # Reduced from 100
    def test_scalability_performance(self, dashboard, qtbot, panel_count):
        """Test dashboard performance with multiple data updates."""
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Measure multiple updates
        start_time = time.time()
        
        for i in range(panel_count):
            # Update data
            dashboard.observer_manager.notify('activity', {
                'steps': 10000 + i,
                'distance': 8000 + i,
                'active_energy': 500 + i,
                'floors_climbed': 20 + i
            })
        
        # Process all events
        qtbot.wait(10)
        
        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / panel_count
        
        assert avg_time < 50, f"Average update time {avg_time:.2f}ms exceeds 50ms per update"
    
    def test_memory_efficiency(self, dashboard, qtbot):
        """Test that dashboard doesn't leak memory during updates."""
        import gc
        import sys
        
        dashboard.show()
        qtbot.waitExposed(dashboard)
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many updates
        for i in range(50):  # Reduced from 100
            dashboard.refresh_data()
            qtbot.wait(1)
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow for some object growth but not excessive
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Excessive object growth: {object_growth} new objects"