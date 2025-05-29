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
    PeerGroupComparisonWidget, PercentileGauge
)
from src.analytics.comparative_analytics import (
    ComparativeAnalyticsEngine, HistoricalComparison, ComparisonType
)
from src.analytics.peer_group_comparison import (
    PeerGroupManager, GroupPrivacyLevel
)
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
        assert widget.group_widget is not None
        assert widget.personal_btn.isChecked()
        assert not widget.group_btn.isChecked()
        
    def test_historical_comparison_display(self, qtbot, engine):
        """Test displaying historical comparisons."""
        widget = HistoricalComparisonWidget()
        qtbot.addWidget(widget)
        
        # Generate comparison
        current_date = datetime.now()
        historical = engine.compare_to_historical('steps', current_date)
        
        # Update widget
        current_value = 9000
        widget.update_comparison(historical, current_value)
        
        # Check cards updated
        assert "9,000" in widget.week_card.value_label.text()
        
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
        
    def test_peer_group_comparison_flow(self, qtbot):
        """Test peer group comparison flow."""
        # Create managers
        group_manager = PeerGroupManager()
        
        # Create widget
        widget = PeerGroupComparisonWidget()
        qtbot.addWidget(widget)
        
        # Create a group
        group = group_manager.create_group(
            "Test Fitness Group",
            "Integration test group",
            "test_user",
            GroupPrivacyLevel.PUBLIC
        )
        
        # Add members to make it valid
        for i in range(5):
            group_manager.join_group(group.group_id, f"member_{i}")
            
        # Create comparison
        comparison = group_manager.compare_to_group(
            group.group_id,
            "test_user",
            "steps",
            8500
        )
        
        # Update widget
        widget.update_comparison(comparison, group.name)
        
        # Check display
        assert "Test Fitness Group" in widget.group_name_label.text()
        assert "Members: 6" in widget.members_label.text()
        assert widget.gauge.gauge_color.name() in ['#4caf50', '#2196f3', '#ff9800', '#9c27b0']
        
    def test_view_switching(self, qtbot):
        """Test switching between comparison views."""
        widget = ComparativeAnalyticsWidget()
        qtbot.addWidget(widget)
        widget.show()
        
        # Initially personal view
        assert widget.historical_widget.isVisible()
        assert not widget.group_widget.isVisible()
        
        # Switch to group view
        QTest.mouseClick(widget.group_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        assert not widget.historical_widget.isVisible()
        assert widget.group_widget.isVisible()
        assert widget.group_btn.isChecked()
        assert not widget.personal_btn.isChecked()
        
        # Switch back to personal
        QTest.mouseClick(widget.personal_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)
        
        assert widget.historical_widget.isVisible()
        assert not widget.group_widget.isVisible()
        
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
            assert widget.historical_widget.isVisible() or widget.group_widget.isVisible()
            
    def test_error_handling(self, qtbot):
        """Test error handling in comparisons."""
        widget = PeerGroupComparisonWidget()
        qtbot.addWidget(widget)
        
        # Create comparison with error
        from src.analytics.peer_group_comparison import GroupComparison
        error_comparison = GroupComparison(
            group_id="test",
            metric="steps",
            comparison_date=datetime.now(),
            user_value=8000,
            group_stats={},
            anonymous_ranking="",
            error="Group too small for comparison"
        )
        
        # Update widget with error
        widget.update_comparison(error_comparison, "Small Group")
        
        # Check error displayed
        assert widget.gauge.label == "No Data"
        assert "too small" in widget.gauge.subtitle.lower()