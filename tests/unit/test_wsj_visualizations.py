"""Tests for WSJ-inspired health visualization components."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.charts.wsj_style_manager import WSJStyleManager
from src.ui.charts.pyqtgraph_chart_factory import PyQtGraphChartFactory
from src.ui.charts.matplotlib_chart_factory import MatplotlibChartFactory
from src.ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite, PerformanceManager


class TestWSJStyleManager:
    """Test WSJ style manager functionality."""
    
    def test_init(self):
        """Test style manager initialization."""
        manager = WSJStyleManager()
        
        # Check color palette
        assert manager.WARM_PALETTE['primary'] == '#FF8C42'
        assert manager.WARM_PALETTE['secondary'] == '#FFD166'
        assert manager.WARM_PALETTE['background'] == '#F5E6D3'
        
        # Check typography
        assert manager.TYPOGRAPHY['title']['size'] == 18
        assert manager.TYPOGRAPHY['title']['weight'] == 600
        
        # Check colormaps created
        assert hasattr(manager, 'cmap_warm')
        assert hasattr(manager, 'cmap_diverging')
        assert hasattr(manager, 'cmap_sequential')
    
    def test_get_warm_palette(self):
        """Test warm palette retrieval."""
        manager = WSJStyleManager()
        palette = manager.get_warm_palette()
        
        assert isinstance(palette, list)
        assert len(palette) >= 5
        assert palette[0] == '#FF8C42'  # Primary color
    
    def test_format_number(self):
        """Test number formatting."""
        manager = WSJStyleManager()
        
        assert manager.format_number(1500) == '1.5K'
        assert manager.format_number(2300000) == '2.3M'
        assert manager.format_number(999) == '999.0'
        assert manager.format_number(1500, precision=2) == '1.50K'
    
    def test_get_metric_color(self):
        """Test metric-specific color assignment."""
        manager = WSJStyleManager()
        
        assert manager.get_metric_color('steps') == '#FF8C42'
        assert manager.get_metric_color('heart_rate') == '#E76F51'
        assert manager.get_metric_color('unknown_metric', 0) == '#FF8C42'
    
    def test_apply_chart_style(self):
        """Test matplotlib chart styling."""
        manager = WSJStyleManager()
        fig, ax = plt.subplots()
        
        manager.apply_chart_style(
            ax,
            title="Test Chart",
            subtitle="Test Subtitle",
            x_label="X Axis",
            y_label="Y Axis"
        )
        
        # Check that styling was applied
        assert ax.get_facecolor() == manager.WARM_PALETTE['surface']
        assert ax.get_title() == "Test Chart"
        assert ax.get_xlabel() == "X Axis"
        assert ax.get_ylabel() == "Y Axis"
        
        plt.close(fig)
    
    def test_configure_independent_axes(self):
        """Test independent axes configuration."""
        manager = WSJStyleManager()
        metrics = ['steps', 'heart_rate', 'calories']
        
        config = manager.configure_independent_axes(metrics)
        
        assert len(config) == 3
        assert config['steps']['position'] == 'left'
        assert config['heart_rate']['position'] == 'right'
        assert config['calories']['position'] == 'right'
        assert config['calories']['offset'] == 60
    
    def test_create_accessibility_description(self):
        """Test accessibility description generation."""
        manager = WSJStyleManager()
        
        data_summary = {
            'metric': 'steps',
            'min': 1000,
            'max': 15000,
            'trend': 'increasing'
        }
        
        description = manager.create_accessibility_description('line', data_summary)
        assert 'Line chart showing steps' in description
        assert '1000 to 15000' in description
        assert 'increasing' in description


class TestPerformanceManager:
    """Test performance optimization functionality."""
    
    def test_optimize_data_for_display(self):
        """Test data optimization for large datasets."""
        manager = PerformanceManager()
        
        # Create large dataset
        dates = pd.date_range(start='2024-01-01', periods=50000, freq='5min')
        data = pd.DataFrame({'value': np.random.randn(50000)}, index=dates)
        
        # Optimize
        optimized = manager.optimize_data_for_display(data, max_points=1000)
        
        assert len(optimized) <= 1000
        assert optimized.index[0] == data.index[0]  # First point preserved
        assert optimized.index[-1] == data.index[-1]  # Last point preserved
    
    def test_should_use_cached(self):
        """Test cache validity checking."""
        manager = PerformanceManager()
        
        # No cache exists
        assert not manager.should_use_cached('test_key')
        
        # Add to cache
        manager.cache['test_key'] = {
            'timestamp': datetime.now(),
            'data': 'test_data'
        }
        
        # Should use cache (recent)
        assert manager.should_use_cached('test_key', ttl_seconds=300)
        
        # Simulate old cache
        manager.cache['test_key']['timestamp'] = datetime.now() - timedelta(minutes=10)
        assert not manager.should_use_cached('test_key', ttl_seconds=300)


@pytest.mark.skipif(not QApplication.instance(), reason="Requires Qt application")
class TestPyQtGraphChartFactory:
    """Test PyQtGraph chart factory."""
    
    def test_factory_init(self):
        """Test factory initialization."""
        style_manager = WSJStyleManager()
        factory = PyQtGraphChartFactory(style_manager)
        
        assert factory.style_manager == style_manager
    
    @patch('src.ui.charts.pyqtgraph_chart_factory.PYQTGRAPH_AVAILABLE', False)
    def test_fallback_widget(self):
        """Test fallback widget when PyQtGraph not available."""
        style_manager = WSJStyleManager()
        factory = PyQtGraphChartFactory(style_manager)
        
        widget = factory.create_chart('multi_metric_line', {}, {})
        
        assert widget is not None
        # Check it's a fallback widget
        assert widget.layout().count() > 0


class TestMatplotlibChartFactory:
    """Test Matplotlib chart factory."""
    
    def test_factory_init(self):
        """Test factory initialization."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        assert factory.style_manager == style_manager
    
    def test_create_multi_metric_line(self):
        """Test multi-metric line chart creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        data = {
            'steps': pd.DataFrame({'value': np.random.randint(5000, 15000, 30)}, index=dates),
            'heart_rate': pd.DataFrame({'value': np.random.randint(60, 100, 30)}, index=dates)
        }
        
        config = {
            'title': 'Test Multi-Metric',
            'subtitle': 'Test Subtitle',
            'y_axes': style_manager.configure_independent_axes(['steps', 'heart_rate'])
        }
        
        fig = factory.create_chart('multi_metric_line', data, config)
        
        assert fig is not None
        assert len(fig.axes) >= 2  # Multiple axes for multiple metrics
        
        plt.close(fig)
    
    def test_create_correlation_heatmap(self):
        """Test correlation heatmap creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        # Create correlation matrix
        corr_matrix = pd.DataFrame(
            np.random.rand(5, 5),
            columns=['A', 'B', 'C', 'D', 'E'],
            index=['A', 'B', 'C', 'D', 'E']
        )
        np.fill_diagonal(corr_matrix.values, 1.0)
        
        data = {'correlation': corr_matrix}
        config = {'title': 'Test Correlation'}
        
        fig = factory.create_chart('correlation_heatmap', data, config)
        
        assert fig is not None
        plt.close(fig)
    
    def test_create_sparkline(self):
        """Test sparkline creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        data = pd.Series(np.random.randn(20).cumsum())
        config = {'show_value': True, 'fill': True}
        
        fig = factory.create_chart('sparkline', data, config)
        
        assert fig is not None
        assert fig.get_figwidth() == 3  # Small figure
        
        plt.close(fig)
    
    def test_create_polar_chart(self):
        """Test polar chart creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        # Create hourly data
        data = pd.DataFrame({'value': np.random.rand(24) * 100})
        config = {'title': 'Daily Pattern', 'pattern_type': 'daily'}
        
        fig = factory.create_chart('polar', data, config)
        
        assert fig is not None
        assert len(fig.axes) == 1
        assert fig.axes[0].name == 'polar'
        
        plt.close(fig)
    
    def test_create_box_plot(self):
        """Test box plot creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        # Create distribution data
        data = pd.DataFrame({
            'Group1': np.random.normal(100, 15, 100),
            'Group2': np.random.normal(90, 20, 100),
            'Group3': np.random.normal(110, 10, 100)
        })
        
        config = {'title': 'Distribution Comparison', 'show_means': True}
        
        fig = factory.create_chart('box_plot', data, config)
        
        assert fig is not None
        plt.close(fig)
    
    def test_create_waterfall_chart(self):
        """Test waterfall chart creation."""
        style_manager = WSJStyleManager()
        factory = MatplotlibChartFactory(style_manager)
        
        data = pd.Series([100, -20, 30, -10, 50], 
                        index=['Start', 'Loss1', 'Gain1', 'Loss2', 'Gain2'])
        config = {'title': 'Waterfall Analysis'}
        
        fig = factory.create_chart('waterfall', data, config)
        
        assert fig is not None
        plt.close(fig)


@pytest.mark.skipif(not QApplication.instance(), reason="Requires Qt application")
class TestWSJHealthVisualizationSuite:
    """Test the main visualization suite."""
    
    @pytest.fixture
    def mock_data_source(self):
        """Create mock data source."""
        mock = Mock()
        mock.get_available_metrics.return_value = ['steps', 'heart_rate', 'calories', 'distance']
        
        # Mock metric data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        mock.get_metric_data.return_value = pd.DataFrame(
            {'value': np.random.randint(5000, 15000, 30)}, 
            index=dates
        )
        
        return mock
    
    def test_suite_init(self, mock_data_source):
        """Test suite initialization."""
        suite = WSJHealthVisualizationSuite(mock_data_source)
        
        assert suite.data_source == mock_data_source
        assert suite.style_manager is not None
        assert suite.performance_manager is not None
        assert suite.interactive_factory is not None
        assert suite.export_factory is not None
    
    def test_create_interactive_chart(self, mock_data_source):
        """Test interactive chart creation."""
        suite = WSJHealthVisualizationSuite(mock_data_source)
        
        data = pd.DataFrame({'value': np.random.randn(100)})
        config = {'title': 'Test Chart'}
        
        widget = suite.create_interactive_chart('sparkline', data, config)
        
        assert widget is not None
        assert suite.current_chart_type == 'sparkline'
        assert suite.current_data is not None
    
    def test_create_export_chart(self, mock_data_source):
        """Test export chart creation."""
        suite = WSJHealthVisualizationSuite(mock_data_source)
        
        data = pd.DataFrame({'value': np.random.randn(100)})
        config = {'title': 'Test Chart'}
        
        chart_bytes = suite.create_export_chart('sparkline', data, config, 'png')
        
        assert chart_bytes is not None
        assert len(chart_bytes) > 0
    
    def test_show_multi_metric(self, mock_data_source):
        """Test multi-metric visualization."""
        suite = WSJHealthVisualizationSuite(mock_data_source)
        
        # Trigger multi-metric view
        suite._show_multi_metric()
        
        # Check tabs were created
        assert suite.tab_widget.count() > 0
        
        # Verify data source was called
        mock_data_source.get_available_metrics.assert_called()
        mock_data_source.get_metric_data.assert_called()
    
    def test_performance_optimization(self, mock_data_source):
        """Test that large datasets are optimized."""
        suite = WSJHealthVisualizationSuite(mock_data_source)
        
        # Create large dataset
        large_data = pd.DataFrame({'value': np.random.randn(20000)})
        config = {}
        
        widget = suite.create_interactive_chart('sparkline', large_data, config)
        
        # Check that optimization was noted in config
        assert suite.current_config.get('data_optimized', False)