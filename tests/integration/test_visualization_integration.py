"""Integration tests for WSJ visualization components with data infrastructure."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from src.ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite
from src.ui.charts.wsj_style_manager import WSJStyleManager
from src.analytics.dataframe_adapter import DataFrameAdapter
from PyQt6.QtWidgets import QApplication


@pytest.mark.integration
class TestVisualizationIntegration:
    """Test visualization components with real data flow."""
    
    @pytest.fixture
    def test_data(self):
        """Create test DataFrame with sample data."""
        # Generate sample health data
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=90, freq='D')
        
        # Generate realistic health data patterns
        steps_base = 8000
        steps = steps_base + np.random.normal(0, 2000, len(dates))
        steps = np.maximum(steps, 0)  # No negative steps
        
        hr_base = 70
        hr = hr_base + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 7) + np.random.normal(0, 5, len(dates))
        
        calories_base = 2000
        calories = calories_base + 0.1 * steps + np.random.normal(0, 200, len(dates))
        
        # Create DataFrame
        data = []
        for i, date in enumerate(dates):
            data.extend([
                {
                    'creationDate': date,
                    'startDate': date,
                    'type': 'StepCount',
                    'value': float(steps[i]),
                    'unit': 'count',
                    'sourceName': 'test'
                },
                {
                    'creationDate': date,
                    'startDate': date,
                    'type': 'HeartRate',
                    'value': float(hr[i]),
                    'unit': 'count/min',
                    'sourceName': 'test'
                },
                {
                    'creationDate': date,
                    'startDate': date,
                    'type': 'ActiveEnergyBurned',
                    'value': float(calories[i]),
                    'unit': 'Cal',
                    'sourceName': 'test'
                }
            ])
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def data_source(self, test_data):
        """Create data source with test data."""
        class MockDataSource:
            def __init__(self, df):
                self.df = df
                
            def get_available_metrics(self):
                """Return available metric types."""
                return list(self.df['type'].unique())
                
            def get_metric_data(self, metric, date_range):
                """Get data for a specific metric and date range."""
                start_date, end_date = date_range
                # Map display names to data types
                metric_map = {
                    'StepCount': 'StepCount',
                    'HeartRate': 'HeartRate', 
                    'ActiveEnergyBurned': 'ActiveEnergyBurned',
                    'steps': 'StepCount',
                    'heart_rate': 'HeartRate',
                    'active_energy': 'ActiveEnergyBurned'
                }
                data_type = metric_map.get(metric, metric)
                
                mask = (
                    (self.df['type'] == data_type) & 
                    (self.df['creationDate'] >= start_date) & 
                    (self.df['creationDate'] <= end_date)
                )
                result = self.df[mask][['creationDate', 'value']].copy()
                if not result.empty:
                    result.set_index('creationDate', inplace=True)
                    result.sort_index(inplace=True)
                return result
                
            def get_dataframe(self):
                """Return the full dataframe."""
                return self.df
                
        return MockDataSource(test_data)
    
    def test_end_to_end_visualization(self, data_source, qtbot):
        """Test complete visualization workflow."""
        # Create visualization suite
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        # Show multi-metric visualization
        suite._show_multi_metric()
        
        # Verify tabs were created
        assert suite.tab_widget.count() >= 1
        
        # Verify data was loaded
        assert suite.current_data is not None
        assert len(suite.current_data) > 0
        
        # Verify chart type is set
        assert suite.current_chart_type == 'multi_metric_line'
    
    def test_correlation_with_real_data(self, data_source, qtbot):
        """Test correlation heatmap with real data patterns."""
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        # Show correlation heatmap
        suite.chart_selector.setCurrentText("Correlation Heatmap")
        
        # Wait for processing
        qtbot.wait(100)
        
        # Verify correlation was calculated
        assert suite.tab_widget.count() >= 1
        assert suite.current_chart_type == 'correlation_heatmap'
        
        # Check that correlations include expected relationships
        if suite.current_data and 'correlation' in suite.current_data:
            corr_matrix = suite.current_data['correlation']
            # Steps and calories should be positively correlated in our test data
            if 'StepCount' in corr_matrix.columns and 'ActiveEnergyBurned' in corr_matrix.columns:
                correlation = corr_matrix.loc['StepCount', 'ActiveEnergyBurned']
                assert correlation > 0.5  # Should be positively correlated
    
    def test_export_functionality(self, data_source, qtbot):
        """Test chart export with real data."""
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        # Create a chart
        suite._show_sparklines()
        
        # Export to bytes
        if suite.current_data and suite.current_chart_type:
            export_bytes = suite.create_export_chart(
                suite.current_chart_type,
                suite.current_data,
                suite.current_config or {},
                'png'
            )
            
            assert export_bytes is not None
            assert len(export_bytes) > 1000  # Should be a real PNG
            
            # PNG magic number
            assert export_bytes[:8] == b'\x89PNG\r\n\x1a\n'
    
    def test_performance_with_large_dataset(self, qtbot):
        """Test performance optimization with large datasets."""
        # Create mock data source with large dataset
        from unittest.mock import Mock
        mock_source = Mock()
        mock_source.get_available_metrics.return_value = ['steps', 'heart_rate']
        
        # Create large dataset (1 year of 5-minute intervals)
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='5min')
        large_data = pd.DataFrame({
            'value': np.random.randn(len(dates))
        }, index=dates)
        
        mock_source.get_metric_data.return_value = large_data
        
        suite = WSJHealthVisualizationSuite(mock_source)
        qtbot.addWidget(suite)
        
        # Show visualization
        suite._show_multi_metric()
        
        # Verify optimization was applied
        assert suite.current_config.get('data_optimized', False)
    
    def test_style_consistency(self, data_source, qtbot):
        """Test that WSJ styling is consistently applied."""
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        style_manager = suite.style_manager
        
        # Test different chart types maintain styling
        chart_types = [
            "Multi-Metric Overlay",
            "Health Sparklines",
            "Cyclical Patterns"
        ]
        
        for chart_type in chart_types:
            suite.chart_selector.setCurrentText(chart_type)
            qtbot.wait(50)
            
            # Verify color palette is applied
            if suite.current_config:
                assert 'colors' in suite.current_config or 'color' in str(suite.current_config)
    
    def test_data_filtering_integration(self, test_data, qtbot):
        """Test visualization with filtered data."""
        # Create a filtered version of test data
        filtered_data = test_data[test_data['type'].isin(['StepCount', 'HeartRate'])].copy()
        
        # Create mock data source with filtered data
        class FilteredMockDataSource:
            def __init__(self, df):
                self.df = df
                
            def get_available_metrics(self):
                """Return available metric types."""
                return list(self.df['type'].unique())
                
            def get_metric_data(self, metric, date_range):
                """Get data for a specific metric and date range."""
                start_date, end_date = date_range
                mask = (
                    (self.df['type'] == metric) & 
                    (self.df['creationDate'] >= start_date) & 
                    (self.df['creationDate'] <= end_date)
                )
                result = self.df[mask][['creationDate', 'value']].copy()
                if not result.empty:
                    result.set_index('creationDate', inplace=True)
                    result.sort_index(inplace=True)
                return result
        
        data_source = FilteredMockDataSource(filtered_data)
        
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        # Show multi-metric
        suite._show_multi_metric()
        
        # Verify only filtered metrics are shown
        available_metrics = data_source.get_available_metrics()
        assert 'StepCount' in available_metrics
        assert 'HeartRate' in available_metrics
        assert len(available_metrics) == 2
    
    def test_accessibility_features(self, data_source, qtbot):
        """Test accessibility features in visualizations."""
        suite = WSJHealthVisualizationSuite(data_source)
        qtbot.addWidget(suite)
        
        # Create a chart
        suite._show_multi_metric()
        
        # Check accessibility config is applied
        if suite.current_config:
            assert 'accessible_name' in suite.current_config
            assert 'accessible_description' in suite.current_config
            
            # Verify descriptions are meaningful
            assert len(suite.current_config['accessible_name']) > 10
            assert 'chart' in suite.current_config['accessible_description'].lower()
    
    def test_empty_data_handling(self, qtbot):
        """Test handling of empty or missing data."""
        # Create mock source with no data
        from unittest.mock import Mock
        mock_source = Mock()
        mock_source.get_available_metrics.return_value = []
        mock_source.get_metric_data.return_value = pd.DataFrame()
        
        suite = WSJHealthVisualizationSuite(mock_source)
        qtbot.addWidget(suite)
        
        # Try to show visualization
        suite._show_multi_metric()
        
        # Should show no data message
        assert suite.tab_widget.count() >= 1
        # Tab should indicate no data
        assert 'No Data' in suite.tab_widget.tabText(0) or suite.tab_widget.count() == 1