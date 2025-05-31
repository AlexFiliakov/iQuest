"""
Component factory for creating standardized UI components.
Provides a centralized way to create reusable components with consistent styling.
"""

from typing import Optional, Dict, Any
from .summary_cards import SummaryCard
from .charts.enhanced_line_chart import EnhancedLineChart
from .charts.chart_config import ChartConfig, LineChartConfig
from .charts.adaptive_chart_renderer import AdaptiveChartRenderer
from .charts.optimized_line_chart import OptimizedLineChart
from .charts.chart_performance_optimizer import ChartPerformanceOptimizer
from .bar_chart_component import BarChart as BarChartComponent, BarChartConfig
from .table_components import MetricTable, TableConfig
from .style_manager import StyleManager
from .dashboards import (
    WSJDashboardLayout, 
    HealthDashboardTemplates
)


class ComponentFactory:
    """Factory for creating standardized UI components with WSJ-style consistency."""
    
    def __init__(self):
        self.style_manager = StyleManager()
        self._wsj_config = self._initialize_wsj_config()
        self.adaptive_renderer = AdaptiveChartRenderer()
        self.performance_optimizer = ChartPerformanceOptimizer()
        self.use_optimized_charts = True  # Enable by default
    
    def _initialize_wsj_config(self) -> Dict[str, Any]:
        """Initialize WSJ-style configuration for all components."""
        return {
            'colors': {
                'primary': '#FF8C42',      # Warm orange
                'secondary': '#FFD166',    # Soft yellow  
                'accent': '#95C17B',       # Soft green
                'background': '#F5E6D3',   # Warm tan
                'text': '#5D4E37',         # Dark brown
                'grid': '#E5D5C8',         # Light brown grid
                'border': '#D4C4B7'        # Border color
            },
            'typography': {
                'font_family': 'Roboto, sans-serif',  # Use Roboto for body text
                'heading_font_family': 'Roboto Condensed, sans-serif',  # Use Roboto Condensed for headings
                'title_size': 16,
                'subtitle_size': 12,
                'body_size': 11,
                'caption_size': 9
            },
            'spacing': {
                'tight': 4,
                'normal': 8,
                'loose': 16,
                'section': 24
            },
            'borders': {
                'thin': 1,
                'medium': 2,
                'thick': 3,
                'radius': 4  # WSJ uses subtle rounded corners
            }
        }
    
    def create_metric_card(
        self,
        title: str,
        value: str = "-",
        card_type: str = "simple", 
        size: str = "medium",
        subtitle: str = None,
        trend: str = None,
        wsj_style: bool = True
    ) -> SummaryCard:
        """Create a metric card with WSJ styling."""
        # Create the appropriate card type
        if card_type == "simple":
            from src.ui.summary_cards import SimpleMetricCard
            card = SimpleMetricCard(size=size, card_id=title)
        elif card_type == "comparison":
            from src.ui.summary_cards import ComparisonCard
            card = ComparisonCard(size=size, card_id=title)
        elif card_type == "goal":
            from src.ui.summary_cards import GoalProgressCard
            card = GoalProgressCard(size=size, card_id=title)
        else:
            # Default to base class
            card = SummaryCard(card_type=card_type, size=size, card_id=title)
        
        # Update content using the update_content method
        content = {'title': title, 'value': value}
        if subtitle:
            content['subtitle'] = subtitle
        if trend:
            # Parse trend for current/previous values if needed
            content['trend'] = trend
            
        card.update_content(content, animate=False)
        
        if wsj_style:
            self._apply_wsj_card_styling(card)
        
        return card
    
    def create_line_chart(self, config: Optional[ChartConfig] = None, wsj_style: bool = True, 
                         data_size: Optional[int] = None) -> EnhancedLineChart:
        """Create a line chart with WSJ styling and optional performance optimization.
        
        Args:
            config: Chart configuration
            wsj_style: Whether to apply WSJ styling
            data_size: Expected data size (enables optimization for large datasets)
        
        Returns:
            Either OptimizedLineChart or EnhancedLineChart based on data size
        """
        if config is None:
            config = LineChartConfig.get_wsj_style() if wsj_style else LineChartConfig()
        elif wsj_style:
            self._apply_wsj_chart_config(config)
        
        # Use optimized chart for large datasets
        if self.use_optimized_charts and data_size and data_size > 10000:
            return OptimizedLineChart(config)
        else:
            return EnhancedLineChart(config)
    
    def create_bar_chart(
        self, 
        chart_type: str = "simple", 
        config: Optional[BarChartConfig] = None,
        wsj_style: bool = True
    ) -> BarChartComponent:
        """Create a bar chart with WSJ styling."""
        if config is None:
            config = BarChartConfig.get_default()
            config.chart_type = chart_type
        
        if wsj_style:
            self._apply_wsj_bar_chart_config(config)
            
        return BarChartComponent(config)
    
    def create_data_table(
        self, 
        config: Optional[TableConfig] = None,
        wsj_style: bool = True
    ) -> MetricTable:
        """Create a data table with WSJ styling."""
        if config is None:
            config = TableConfig(
                page_size=25
            )
        
        if wsj_style:
            self._apply_wsj_table_config(config)
            
        return MetricTable(config)
    
    def _apply_wsj_card_styling(self, card: SummaryCard):
        """Apply WSJ-style styling to a summary card."""
        wsj_colors = self._wsj_config['colors']
        
        # Apply WSJ-style colors and typography
        card.setStyleSheet(f"""
            SummaryCard {{
                background-color: white;
                border: {self._wsj_config['borders']['thin']}px solid {wsj_colors['border']};
                border-radius: {self._wsj_config['borders']['radius']}px;
                font-family: {self._wsj_config['typography']['font_family']};
                color: {wsj_colors['text']};
            }}
            .title {{
                font-size: {self._wsj_config['typography']['title_size']}px;
                font-weight: bold;
                color: {wsj_colors['text']};
            }}
            .value {{
                font-size: {self._wsj_config['typography']['title_size'] + 4}px;
                font-weight: bold;
                color: {wsj_colors['primary']};
            }}
        """)
        
    def _apply_wsj_chart_config(self, config: ChartConfig):
        """Apply WSJ-style configuration to charts."""
        wsj_colors = self._wsj_config['colors']
        
        config.background_color = 'white'
        config.grid_color = wsj_colors['grid']
        config.text_color = wsj_colors['text']
        config.font_family = self._wsj_config['typography']['font_family']
        config.border_color = wsj_colors['border']
        config.show_grid = True
        config.grid_alpha = 0.3
        
    def _apply_wsj_bar_chart_config(self, config: BarChartConfig):
        """Apply WSJ-style configuration to bar charts."""
        wsj_colors = self._wsj_config['colors']
        
        config.primary_color = wsj_colors['primary']
        config.secondary_color = wsj_colors['secondary'] 
        config.accent_color = wsj_colors['accent']
        config.background_color = 'white'
        config.grid_color = wsj_colors['grid']
        config.text_color = wsj_colors['text']
        config.show_grid = True
        config.warm_theme = True
        
    def _apply_wsj_table_config(self, config: TableConfig):
        """Apply WSJ-style configuration to tables."""
        wsj_colors = self._wsj_config['colors']
        
        config.header_background = wsj_colors['background']
        config.alternating_row_color = '#FAFAF8'  # Very light warm background
        config.border_color = wsj_colors['border']
        config.text_color = wsj_colors['text']
        config.font_family = self._wsj_config['typography']['font_family']
        config.hover_color = wsj_colors['secondary']
        config.font_size = self._wsj_config['typography']['body_size']
    
    def apply_warm_theme(self):
        """Apply warm color theme to all component types."""
        # Apply the WSJ warm theme globally
        pass
    
    def create_dashboard(
        self,
        template_name: Optional[str] = 'daily_overview',
        wsj_style: bool = True
    ) -> WSJDashboardLayout:
        """Create a multi-metric dashboard with WSJ styling."""
        dashboard = WSJDashboardLayout()
        
        if template_name:
            # Load predefined template
            template = HealthDashboardTemplates.get_template_by_name(template_name)
            dashboard.apply_layout_template(template)
        
        return dashboard
    
    # def create_dashboard_persistence(self) -> DashboardPersistence:
    #     """Create dashboard persistence manager."""
    #     return DashboardPersistence()
    
    def create_adaptive_chart(self, data, chart_type: str = 'line', 
                            container=None, **kwargs):
        """Create a chart using the adaptive renderer that selects optimal backend.
        
        Args:
            data: Chart data (DataFrame)
            chart_type: Type of chart to create
            container: Widget container for the chart
            **kwargs: Additional chart options
            
        Returns:
            Rendered chart object
        """
        return self.adaptive_renderer.render(data, chart_type, container, **kwargs)
    
    def optimize_chart_data(self, data, target_points: Optional[int] = None,
                          algorithm: str = 'auto'):
        """Optimize chart data for better performance.
        
        Args:
            data: Input DataFrame
            target_points: Target number of points after optimization
            algorithm: Optimization algorithm ('lttb', 'decimation', 'aggregation', 'auto')
            
        Returns:
            Optimized DataFrame
        """
        return self.performance_optimizer.optimize_data(data, target_points, algorithm)
    
    def set_optimization_enabled(self, enabled: bool):
        """Enable or disable automatic chart optimization."""
        self.use_optimized_charts = enabled
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from the adaptive renderer."""
        return self.adaptive_renderer.get_performance_stats()
    
    def get_dashboard_templates(self) -> Dict[str, Any]:
        """Get all available dashboard templates."""
        return HealthDashboardTemplates.get_all_templates()
    
    def get_wsj_style_config(self) -> Dict[str, Any]:
        """Get complete WSJ-inspired styling configuration."""
        return {
            'chart_config': {
                'background': 'white',
                'grid_color': self._wsj_config['colors']['grid'],
                'text_color': self._wsj_config['colors']['text'],
                'font_family': self._wsj_config['typography']['font_family']
            },
            'card_config': {
                'background': 'white',
                'border_color': self._wsj_config['colors']['border'],
                'text_color': self._wsj_config['colors']['text'],
                'font_family': self._wsj_config['typography']['font_family']
            },
            'table_config': {
                'alternating_rows': True,
                'hover_highlight': True,
                'warm_accent': True,
                'border_color': self._wsj_config['colors']['border'],
                'font_family': self._wsj_config['typography']['font_family']
            },
            'dashboard_config': {
                'grid_system': '12-column',
                'gutter_width': 16,
                'margin': 24,
                'responsive_breakpoints': {
                    'mobile': 768,
                    'tablet': 1024,
                    'desktop': 1440,
                    'wide': 1920
                }
            }
        }