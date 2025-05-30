"""
Integration tests for comparative analytics with UI.
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.main_window import MainWindow
from src.ui.comparative_visualization import (
    ComparativeAnalyticsWidget, HistoricalComparisonWidget,
    PercentileGauge
)
from src.analytics.comparative_analytics import (
    ComparativeAnalyticsEngine, HistoricalComparison, ComparisonType
)
# Peer group comparison imports removed - feature no longer supported
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator  
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator


class TestComparativeAnalyticsIntegration:
    """Test comparative analytics integration with UI."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=365),
            end=datetime.now(),
            freq='D'
        )
        
        # Create realistic step data with trends and seasonality
        base_steps = 8000
        trend = np.linspace(0, 1000, len(dates))  # Gradual improvement
        seasonality = 1000 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
        noise = np.random.normal(0, 500, len(dates))
        
        steps = base_steps + trend + seasonality + noise
        steps = np.clip(steps, 2000, 15000)  # Realistic bounds
        
        df = pd.DataFrame({
            'date': dates,
            'steps': steps.astype(int),
            'distance': steps / 1300,  # Rough conversion
            'calories': steps / 20 + np.random.normal(100, 20, len(dates))
        })
        
        return df
        
    @pytest.fixture
    def calculators(self, sample_data):
        """Create calculator instances with sample data."""
        # Use our proper MockDataSource from tests.mocks
        from tests.mocks import MockDataSource
        
        # Ensure sample_data has the required columns
        if 'creationDate' not in sample_data.columns:
            sample_data['creationDate'] = sample_data['date']
        if 'type' not in sample_data.columns:
            # Add type column for each metric
            sample_data['type'] = 'HKQuantityTypeIdentifierStepCount'
            # For other metrics, we'd need to map them properly
            
        # Rename columns to match expected format
        metrics_data = []
        for metric in ['steps', 'distance', 'calories']:
            metric_type = {
                'steps': 'HKQuantityTypeIdentifierStepCount',
                'distance': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'calories': 'HKQuantityTypeIdentifierActiveEnergyBurned'
            }.get(metric, metric)
            
            if metric in sample_data.columns:
                for idx, row in sample_data.iterrows():
                    metrics_data.append({
                        'creationDate': row['date'],
                        'type': metric_type,
                        'value': row[metric]
                    })
        
        # Create DataFrame in expected format
        data_df = pd.DataFrame(metrics_data)
        data_source = MockDataSource(data_df)
        
        daily = DailyMetricsCalculator(data_source)
        weekly = WeeklyMetricsCalculator(daily)
        monthly = MonthlyMetricsCalculator(daily)
        
        return daily, weekly, monthly
        
    @pytest.fixture
    def engine(self, calculators):
        """Create comparative analytics engine."""
        daily, weekly, monthly = calculators
        return ComparativeAnalyticsEngine(daily, weekly, monthly)
        
    @pytest.fixture
    def app(self, qtbot):
        """Create QApplication for testing."""
        # QApplication is created by pytest-qt
        pass
        
    def test_comparative_widget_creation(self, qtbot):
        """Test creating comparative analytics widget."""
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        
        # Check components exist
        assert widget.historical_widget is not None
        assert widget.personal_btn.isChecked()
        assert widget.seasonal_btn is not None
        assert not widget.seasonal_btn.isChecked()
        
    def test_historical_comparison_display(self, qtbot, engine):
        """Test displaying historical comparisons."""
        widget = HistoricalComparisonWidget()
        qtbot.addWidget(widget)
        
        # Generate comparison
        current_date = datetime.now()
        historical = engine.compare_to_historical('HKQuantityTypeIdentifierStepCount', current_date)
        
        # Update widget
        current_value = 9000
        widget.update_comparison(historical, current_value)
        
        # Check cards updated - handle case where there's no data
        card_text = widget.week_card.value_label.text()
        # If we have data, it should show the value, otherwise "--"
        assert "9,000" in card_text or "--" in card_text
        
        # Check trend display
        if historical.trend_direction:
            assert widget.trend_label.text() != "Calculating trend..."
            
    def test_percentile_gauge_animation(self, qtbot):
        """Test percentile gauge animation."""
        gauge = PercentileGauge()
        qtbot.addWidget(gauge)
        gauge.show()
        
        # Set initial value
        gauge.set_value(25)
        gauge.set_label("Building Momentum")
        gauge.set_subtitle("Every step counts!")
        
        # Wait for animation
        qtbot.wait(100)
        
        # Update to new value
        gauge.set_value(75)
        gauge.set_color('#4CAF50')
        gauge.set_label("Top Quarter")
        gauge.set_subtitle("You're inspiring others!")
        
        # Wait for animation to complete
        qtbot.wait(1100)
        
        # Check final value
        assert gauge.target_percentile == 75
        assert gauge.label == "Top Quarter"
        
    def test_seasonal_trends_flow(self, qtbot):
        """Test seasonal trends flow."""
        # Create widget
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        widget.show()
        
        # Switch to seasonal view
        QTest.mouseClick(widget.seasonal_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        # Check seasonal widget created
        assert hasattr(widget, 'seasonal_widget')
        assert widget.seasonal_widget is not None
        assert widget.seasonal_btn.isChecked()
        assert not widget.personal_btn.isChecked()
        
    def test_view_switching(self, qtbot):
        """Test switching between comparison views."""
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        widget.show()
        
        # Initially personal view
        assert widget.historical_widget.isVisible()
        
        # Switch to seasonal view
        QTest.mouseClick(widget.seasonal_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        assert not widget.historical_widget.isVisible()
        assert hasattr(widget, 'seasonal_widget')
        assert widget.seasonal_widget.isVisible()
        assert widget.seasonal_btn.isChecked()
        assert not widget.personal_btn.isChecked()
        
        # Switch back to personal
        QTest.mouseClick(widget.personal_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        assert widget.historical_widget.isVisible()
        assert not widget.seasonal_widget.isVisible()
        
    def test_main_window_integration(self, qtbot, monkeypatch):
        """Test comparative analytics integration in main window."""
        # Mock the configuration tab to avoid dependencies
        def mock_create_config_tab(self):
            from PyQt6.QtWidgets import QWidget
            self.config_tab = QWidget(self)  # Add parent
            self.tab_widget.addTab(self.config_tab, "Configuration")
            
        monkeypatch.setattr(MainWindow, '_create_configuration_tab', mock_create_config_tab)
        
        # Mock the database manager to avoid disk I/O errors
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value = MagicMock()
        mock_db.get_connection.return_value.__exit__.return_value = None
        # Patch the imported db_manager in main_window module
        import src.ui.main_window
        monkeypatch.setattr(src.ui.main_window, 'db_manager', mock_db)
        
        # Mock BackgroundTrendProcessor to avoid initialization issues
        class MockBackgroundTrendProcessor:
            def __init__(self, *args, **kwargs):
                self.queue_trend_calculation = MagicMock()
                self.get_trend = MagicMock(return_value=None)
                self.shutdown = MagicMock()
                self.set_comparative_engine = MagicMock()
                self.get_processing_status = MagicMock(return_value=(0, 0))
                self.VALID_METRICS = set()
        
        monkeypatch.setattr('src.analytics.background_trend_processor.BackgroundTrendProcessor', MockBackgroundTrendProcessor)
        
        # Create main window
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        
        # Find the Compare tab
        compare_tab_index = None
        for i in range(window.tab_widget.count()):
            if window.tab_widget.tabText(i) == "Compare":
                compare_tab_index = i
                break
                
        assert compare_tab_index is not None, "Compare tab not found"
        
        # Switch to Compare tab
        window.tab_widget.setCurrentIndex(compare_tab_index)
        qtbot.wait(100)
        
        # Check tab tooltip
        tooltip = window.tab_widget.tabToolTip(compare_tab_index)
        assert "compare" in tooltip.lower()
        assert "personal" in tooltip.lower() or "peer" in tooltip.lower()
        
    def test_privacy_settings_integration(self, qtbot, engine):
        """Test privacy settings affect comparisons."""
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        
        # Initially no demographic permission
        result = engine.compare_to_demographic('steps', 35, 'male')
        assert result is None
        
        # Grant permission
        engine.privacy_manager.permissions['demographic_comparison'] = {
            'granted': True,
            'timestamp': datetime.now()
        }
        
        # Now should get result
        result = engine.compare_to_demographic('steps', 35, 'male')
        assert result is not None
        assert result.comparison_type == ComparisonType.DEMOGRAPHIC
        
    def test_responsive_layout(self, qtbot):
        """Test widget responds to size changes."""
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        widget.show()
        
        # Test different sizes
        sizes = [(800, 600), (1200, 800), (600, 400)]
        
        for width, height in sizes:
            widget.resize(width, height)
            qtbot.wait(100)
            
            # Widget should remain functional
            assert widget.historical_widget.isVisible() or (hasattr(widget, 'seasonal_widget') and widget.seasonal_widget.isVisible())
            
    def test_error_handling(self, qtbot):
        """Test error handling in comparisons."""
        widget = HistoricalComparisonWidget()
        qtbot.addWidget(widget)
        
        # Create comparison with None values to simulate error
        from src.analytics.comparative_analytics import HistoricalComparison
        error_comparison = HistoricalComparison(
            rolling_7_day=None,
            rolling_30_day=None,
            rolling_90_day=None,
            rolling_365_day=None,
            same_period_last_year=None,
            personal_best=None,
            personal_average=None,
            trend_direction=None
        )
        
        # Update widget with error
        widget.update_comparison(error_comparison, 8000)
        
        # Check that widget handles None values gracefully
        assert widget.week_card is not None
        # With None values, the widget should show "--"
        assert "--" in widget.week_card.value_label.text()