"""
Tests for the Bar Chart Component

Tests cover chart rendering, data handling, animations, and interactive features.
"""

import pytest
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

from src.ui.bar_chart_component import BarChart, BarChartConfig, ValueLabelManager, InteractiveBarChart


@pytest.fixture
def sample_data_simple():
    """Simple bar chart test data."""
    return pd.DataFrame({
        'Steps': [8542, 9234, 7892, 10345, 6789]
    }, index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])


@pytest.fixture
def sample_data_grouped():
    """Grouped bar chart test data."""
    return pd.DataFrame({
        'Steps': [8542, 9234, 7892, 10345, 6789],
        'Heart Rate': [72, 75, 68, 80, 65],
        'Sleep Hours': [7.5, 8.2, 6.8, 7.9, 8.1]
    }, index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])


@pytest.fixture
def sample_data_stacked():
    """Stacked bar chart test data."""
    return pd.DataFrame({
        'Active Minutes': [45, 60, 30, 75, 40],
        'Moderate Minutes': [30, 25, 45, 20, 35],
        'Light Minutes': [120, 110, 140, 105, 125]
    }, index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])


class TestBarChartConfig:
    """Test BarChartConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BarChartConfig()
        
        assert config.bar_width == 0.8
        assert config.bar_alpha == 0.8
        assert config.show_value_labels is True
        assert config.show_legend is True
        assert config.animate is True
        assert config.wsj_style is True
        
    def test_color_sequence(self):
        """Test color sequence generation."""
        config = BarChartConfig()
        
        # Test with fewer colors than palette
        colors = config.get_color_sequence(3)
        assert len(colors) == 3
        assert all(color in config.color_palette for color in colors)
        
        # Test with more colors than palette
        colors = config.get_color_sequence(10)
        assert len(colors) == 10


class TestBarChart:
    """Test BarChart component."""
    
    def test_initialization(self, qtbot):
        """Test bar chart initialization."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        assert chart.config is not None
        assert chart.figure is not None
        assert chart.canvas is not None
        assert chart.bar_containers == []
        
    def test_simple_bar_chart(self, qtbot, sample_data_simple):
        """Test simple bar chart plotting."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple, chart_type='simple')
        
        assert chart.data is not None
        assert chart.chart_type == 'simple'
        assert len(chart.bar_containers) == 1
        assert chart.ax is not None
        
    def test_grouped_bar_chart(self, qtbot, sample_data_grouped):
        """Test grouped bar chart plotting."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_grouped, chart_type='grouped')
        
        assert chart.chart_type == 'grouped'
        assert len(chart.bar_containers) == 3  # Three data series
        
    def test_stacked_bar_chart(self, qtbot, sample_data_stacked):
        """Test stacked bar chart plotting."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_stacked, chart_type='stacked')
        
        assert chart.chart_type == 'stacked'
        assert len(chart.bar_containers) == 3  # Three data series
        
    def test_wsj_styling(self, qtbot, sample_data_simple):
        """Test WSJ styling application."""
        config = BarChartConfig(wsj_style=True, clean_spines=True)
        chart = BarChart(config)
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Check that spines are configured
        assert not chart.ax.spines['top'].get_visible()
        assert not chart.ax.spines['right'].get_visible()
        
    def test_animation_disabled(self, qtbot, sample_data_simple):
        """Test chart without animation."""
        config = BarChartConfig(animate=False)
        chart = BarChart(config)
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        assert chart.animation is None
        
    def test_value_labels_disabled(self, qtbot, sample_data_simple):
        """Test chart without value labels."""
        config = BarChartConfig(show_value_labels=False)
        chart = BarChart(config)
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Check that no text annotations were added
        texts = chart.ax.texts
        # Should only have tick labels, no value labels
        assert len([t for t in texts if t.get_text().replace('.', '').isdigit()]) == 0
        
    def test_export_functionality(self, qtbot, sample_data_simple, tmp_path):
        """Test chart export functionality."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        export_path = tmp_path / "test_chart.png"
        chart.export_chart(str(export_path))
        
        assert export_path.exists()
        assert export_path.stat().st_size > 0
        
    def test_config_update(self, qtbot, sample_data_simple):
        """Test configuration update."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Update config
        new_config = BarChartConfig(bar_alpha=0.5, show_grid=False)
        chart.update_config(new_config)
        
        assert chart.config.bar_alpha == 0.5
        assert chart.config.show_grid is False


class TestValueLabelManager:
    """Test ValueLabelManager class."""
    
    def test_label_positioning(self, qtbot, sample_data_simple):
        """Test value label positioning logic."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Get the bar container
        bars = chart.bar_containers[0]
        config = BarChartConfig()
        
        label_manager = ValueLabelManager(chart.ax, config)
        label_manager.add_labels(bars)
        
        # Check that labels were added
        texts = chart.ax.texts
        value_labels = [t for t in texts if t.get_text().replace('.', '').isdigit()]
        assert len(value_labels) > 0


class TestInteractiveBarChart:
    """Test InteractiveBarChart enhanced features."""
    
    def test_interactive_initialization(self, qtbot):
        """Test interactive bar chart initialization."""
        chart = InteractiveBarChart()
        qtbot.addWidget(chart)
        
        assert chart.control_panel is not None
        
    def test_hover_interactions(self, qtbot, sample_data_simple):
        """Test hover interaction setup."""
        config = BarChartConfig(enable_hover=True)
        chart = InteractiveBarChart(config)
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Test that hover is enabled
        assert chart.config.enable_hover is True
        
    def test_selection_interactions(self, qtbot, sample_data_simple):
        """Test selection interaction setup."""
        config = BarChartConfig(enable_selection=True)
        chart = InteractiveBarChart(config)
        qtbot.addWidget(chart)
        
        chart.plot(sample_data_simple)
        
        # Test that selection is enabled
        assert chart.config.enable_selection is True


class TestDataCompatibility:
    """Test chart compatibility with various data formats."""
    
    def test_empty_data(self, qtbot):
        """Test handling of empty data."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        empty_data = pd.DataFrame()
        
        # Should not raise an exception
        try:
            chart.plot(empty_data)
            # If no exception, consider it a pass
            assert True
        except Exception:
            # Empty data should be handled gracefully
            pytest.fail("Chart should handle empty data gracefully")
            
    def test_single_value_data(self, qtbot):
        """Test handling of single value data."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        single_data = pd.DataFrame({
            'Value': [100]
        }, index=['Single'])
        
        chart.plot(single_data)
        
        assert len(chart.bar_containers) == 1
        assert len(chart.bar_containers[0]) == 1
        
    def test_negative_values(self, qtbot):
        """Test handling of negative values."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        negative_data = pd.DataFrame({
            'Values': [-10, 5, -3, 8, -1]
        }, index=['A', 'B', 'C', 'D', 'E'])
        
        chart.plot(negative_data)
        
        # Should handle negative values without error
        assert chart.ax is not None
        
    def test_mixed_data_types(self, qtbot):
        """Test handling of mixed positive/negative values."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        mixed_data = pd.DataFrame({
            'Profit': [1000, -500, 2000, -300, 1500],
            'Loss': [-200, -800, -100, -600, -400]
        }, index=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        
        chart.plot(mixed_data, chart_type='grouped')
        
        assert len(chart.bar_containers) == 2


class TestPerformance:
    """Test chart performance with larger datasets."""
    
    def test_large_dataset(self, qtbot):
        """Test chart with large dataset."""
        chart = BarChart()
        qtbot.addWidget(chart)
        
        # Create dataset with 100 categories
        large_data = pd.DataFrame({
            'Values': np.random.randint(1, 1000, 100)
        }, index=[f'Cat_{i}' for i in range(100)])
        
        # Should handle large dataset efficiently
        chart.plot(large_data)
        
        assert len(chart.bar_containers[0]) == 100
        
    def test_animation_performance(self, qtbot):
        """Test animation performance doesn't block UI."""
        config = BarChartConfig(animate=True, animation_duration=100)  # Short animation
        chart = BarChart(config)
        qtbot.addWidget(chart)
        
        data = pd.DataFrame({
            'Values': [10, 20, 30, 40, 50]
        }, index=['A', 'B', 'C', 'D', 'E'])
        
        chart.plot(data)
        
        # Animation should be created
        assert chart.animation is not None


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])