"""
Tests for component factory.
Tests creation of UI components with consistent WSJ styling.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication

from src.ui.component_factory import ComponentFactory
from src.ui.summary_cards import SummaryCard
from src.ui.charts.enhanced_line_chart import EnhancedLineChart
from src.ui.charts.chart_config import ChartConfig
from src.ui.bar_chart_component import BarChart as BarChartComponent, BarChartConfig
from src.ui.table_components import MetricTable, TableConfig


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def factory():
    """Create ComponentFactory instance."""
    return ComponentFactory()


class TestComponentFactory:
    """Test ComponentFactory class."""
    
    def test_initialization(self, app, factory):
        """Test factory initialization."""
        assert hasattr(factory, 'style_manager')
        assert hasattr(factory, '_wsj_config')
        
        # Check WSJ config structure
        wsj_config = factory._wsj_config
        assert 'colors' in wsj_config
        assert 'typography' in wsj_config
        assert 'spacing' in wsj_config
        assert 'borders' in wsj_config
        
        # Check color configuration
        colors = wsj_config['colors']
        assert colors['primary'] == '#FF8C42'  # Warm orange
        assert colors['secondary'] == '#FFD166'  # Soft yellow
        assert colors['background'] == '#F5E6D3'  # Warm tan
        assert colors['text'] == '#5D4E37'  # Dark brown
    
    def test_create_metric_card(self, app, factory):
        """Test metric card creation."""
        card = factory.create_metric_card(
            title="Test Card",
            value="100",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        assert isinstance(card, SummaryCard)
        # SimpleMetricCard stores title in title_label widget
        if hasattr(card, 'title_label'):
            assert card.title_label.text() == "Test Card"
        if hasattr(card, 'value_label'):
            # Value might be formatted as float
            assert card.value_label.text() in ["100", "100.0"]
        assert card.card_type == "simple"
        assert card.size == "medium"
    
    def test_create_metric_card_no_wsj_style(self, app, factory):
        """Test metric card creation without WSJ styling."""
        card = factory.create_metric_card(
            title="Test Card",
            value="100",
            wsj_style=False
        )
        
        assert isinstance(card, SummaryCard)
        # Should still create card but without WSJ styling applied
    
    def test_create_line_chart(self, app, factory):
        """Test line chart creation."""
        chart = factory.create_line_chart(wsj_style=True)
        
        assert isinstance(chart, EnhancedLineChart)
        assert hasattr(chart, 'config')
    
    def test_create_line_chart_custom_config(self, app, factory):
        """Test line chart creation with custom config."""
        config = ChartConfig()
        config.title = "Custom Chart"
        
        chart = factory.create_line_chart(config=config, wsj_style=True)
        
        assert isinstance(chart, EnhancedLineChart)
        assert chart.config.title == "Custom Chart"
    
    def test_create_bar_chart(self, app, factory):
        """Test bar chart creation."""
        chart = factory.create_bar_chart(
            chart_type="grouped",
            wsj_style=True
        )
        
        assert isinstance(chart, BarChartComponent)
    
    def test_create_data_table(self, app, factory):
        """Test data table creation."""
        table = factory.create_data_table(wsj_style=True)
        
        assert isinstance(table, MetricTable)
        assert hasattr(table, 'config')
    
    def test_create_data_table_custom_config(self, app, factory):
        """Test data table creation with custom config."""
        config = TableConfig(
            page_size=10,
            show_pagination=False
        )
        
        table = factory.create_data_table(config=config, wsj_style=True)
        
        assert isinstance(table, MetricTable)
        assert table.config.page_size == 10
        assert not table.config.show_pagination
    
    def test_get_wsj_style_config(self, app, factory):
        """Test WSJ style configuration retrieval."""
        config = factory.get_wsj_style_config()
        
        assert 'chart_config' in config
        assert 'card_config' in config
        assert 'table_config' in config
        
        # Check chart config
        chart_config = config['chart_config']
        assert chart_config['background'] == 'white'
        assert chart_config['text_color'] == '#5D4E37'
        assert chart_config['font_family'] == 'Georgia, serif'
        
        # Check card config
        card_config = config['card_config']
        assert card_config['background'] == 'white'
        assert card_config['border_color'] == '#D4C4B7'
        
        # Check table config
        table_config = config['table_config']
        assert table_config['alternating_rows'] is True
        assert table_config['hover_highlight'] is True
        assert table_config['warm_accent'] is True


class TestWSJStyling:
    """Test WSJ styling application."""
    
    def test_wsj_color_consistency(self, factory):
        """Test that WSJ colors are consistent across components."""
        wsj_config = factory._wsj_config
        colors = wsj_config['colors']
        
        # Create different components and verify they use consistent colors
        style_config = factory.get_wsj_style_config()
        
        # All components should use the same text color
        assert style_config['chart_config']['text_color'] == colors['text']
        assert style_config['card_config']['text_color'] == colors['text']
        assert style_config['table_config']['font_family'] == wsj_config['typography']['font_family']
    
    def test_typography_consistency(self, factory):
        """Test that typography settings are consistent."""
        wsj_config = factory._wsj_config
        typography = wsj_config['typography']
        
        # All components should use the same font family
        style_config = factory.get_wsj_style_config()
        expected_font = typography['font_family']
        
        assert style_config['chart_config']['font_family'] == expected_font
        assert style_config['card_config']['font_family'] == expected_font
        assert style_config['table_config']['font_family'] == expected_font
    
    def test_border_consistency(self, factory):
        """Test that border settings are consistent."""
        wsj_config = factory._wsj_config
        border_color = wsj_config['colors']['border']
        
        style_config = factory.get_wsj_style_config()
        
        assert style_config['card_config']['border_color'] == border_color
        assert style_config['table_config']['border_color'] == border_color