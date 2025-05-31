"""
Chart configuration classes for customizing chart appearance and behavior.

This module provides configuration objects for charts following the 
Apple Health Monitor design system and Wall Street Journal style.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from PyQt6.QtGui import QColor


@dataclass
class ChartConfig:
    """
    Configuration class for chart styling and behavior.
    
    Follows the Apple Health Monitor warm color theme and 
    Wall Street Journal-inspired minimalist design.
    """
    
    # Colors - WSJ-inspired professional palette
    primary_color: str = '#5B6770'      # Sophisticated slate for primary data
    secondary_color: str = '#ADB5BD'    # Medium gray for secondary data
    tertiary_color: str = '#495057'     # Dark gray for tertiary data
    background_color: str = '#FFFFFF'   # White background
    plot_background: str = '#F8F9FA'    # Light gray like WSJ
    grid_color: str = '#E9ECEF'         # Light gray grid
    axis_color: str = '#6C757D'         # Medium gray for axes
    text_color: str = '#212529'         # Near-black for text
    text_muted: str = '#6C757D'         # Medium gray for labels
    
    # Typography - Clean, professional fonts
    title_font_size: int = 18
    subtitle_font_size: int = 14
    label_font_size: int = 11
    tick_font_size: int = 10
    font_family: str = 'Inter'          # Primary font
    title_font_family: str = 'Poppins'  # Display font for titles
    
    # Layout
    margins: Dict[str, float] = field(default_factory=lambda: {
        'left': 80, 'right': 40, 'top': 60, 'bottom': 60
    })
    
    # Grid and axes
    show_grid: bool = True
    grid_style: Literal['solid', 'dashed', 'dotted'] = 'dotted'
    grid_alpha: float = 0.3
    show_x_axis: bool = True
    show_y_axis: bool = True
    axis_width: int = 1
    
    # Data display
    line_width: float = 2.5
    show_data_points: bool = True
    point_size: float = 4.0
    hover_point_size: float = 6.0
    
    # Interactivity
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_tooltips: bool = True
    enable_crosshair: bool = False
    enable_selection: bool = True
    
    # Animation
    animate: bool = True
    animation_duration: int = 500  # milliseconds
    animation_easing: str = 'OutCubic'
    
    # Export settings
    export_dpi: int = 300
    export_transparent: bool = False
    
    # Legend
    show_legend: bool = True
    legend_position: Literal['top', 'right', 'bottom', 'left'] = 'top'
    legend_columns: int = 1
    
    # WSJ-specific styling
    wsj_mode: bool = True  # Enable WSJ-inspired styling
    subtle_colors: bool = True  # Use more muted color palette
    minimalist: bool = True  # Remove unnecessary visual elements


@dataclass 
class LineChartConfig(ChartConfig):
    """Extended configuration specific to line charts."""
    
    # Line styles
    line_style: Literal['solid', 'dashed', 'dotted'] = 'solid'
    smooth_lines: bool = True  # Spline interpolation
    area_fill: bool = False  # Fill area under line
    area_opacity: float = 0.1
    
    # Multiple series
    series_colors: List[str] = field(default_factory=lambda: [
        '#5B6770',  # Slate
        '#6C757D',  # Dark gray
        '#ADB5BD',  # Medium gray
        '#FF6B6B',  # Red
        '#95E1D3',  # Mint
        '#AA96DA',  # Purple
    ])
    
    # Data point styles
    marker_style: Literal['circle', 'square', 'diamond', 'none'] = 'circle'
    
    # Trend line
    show_trend_line: bool = False
    trend_line_color: str = '#999999'
    trend_line_style: str = 'dashed'
    
    @classmethod
    def get_wsj_style(cls) -> 'ChartConfig':
        """Get Wall Street Journal inspired chart configuration."""
        return cls(
            # WSJ uses very muted colors
            primary_color='#0066CC',      # Blue
            secondary_color='#666666',    # Gray
            tertiary_color='#CC0000',     # Red
            background_color='#FFFFFF',
            plot_background='#FAF8F5',
            grid_color='#E8DCC8',
            axis_color='#333333',
            text_color='#000000',
            text_muted='#666666',
            
            # Clean typography
            title_font_size=16,
            subtitle_font_size=12,
            label_font_size=10,
            tick_font_size=9,
            font_family='Helvetica',
            title_font_family='Helvetica',
            
            # Minimal grid
            show_grid=True,
            grid_style='dotted',
            grid_alpha=0.2,
            
            # Other styles
            line_width=1.5,
            point_size=4,
            animate=False
        )


class LineChartBuilder:
    """
    Fluent interface for building line charts with custom configuration.
    
    Example:
        chart = (LineChartBuilder()
            .with_title("Daily Heart Rate")
            .with_wsj_style()
            .with_animation(duration=300)
            .with_size(800, 400)
            .build())
    """
    
    def __init__(self):
        """Initialize builder with default config."""
        self.config = LineChartConfig()
        self._size = (800, 400)
        self._title = ""
        self._subtitle = ""
        self._x_label = ""
        self._y_label = ""
        
    def with_title(self, title: str, subtitle: Optional[str] = None) -> 'LineChartBuilder':
        """Set chart title and optional subtitle."""
        self._title = title
        if subtitle:
            self._subtitle = subtitle
        return self
        
    def with_labels(self, x_label: str, y_label: str) -> 'LineChartBuilder':
        """Set axis labels."""
        self._x_label = x_label
        self._y_label = y_label
        return self
        
    def with_colors(self, primary: str, secondary: Optional[str] = None) -> 'LineChartBuilder':
        """Set primary and secondary colors."""
        self.config.primary_color = primary
        if secondary:
            self.config.secondary_color = secondary
        return self
        
    def with_series_colors(self, colors: List[str]) -> 'LineChartBuilder':
        """Set colors for multiple data series."""
        self.config.series_colors = colors
        return self
        
    def with_animation(self, enabled: bool = True, duration: int = 500) -> 'LineChartBuilder':
        """Configure animation settings."""
        self.config.animate = enabled
        self.config.animation_duration = duration
        return self
        
    def with_interactivity(self, zoom: bool = True, pan: bool = True, 
                          tooltips: bool = True) -> 'LineChartBuilder':
        """Configure interactive features."""
        self.config.enable_zoom = zoom
        self.config.enable_pan = pan
        self.config.enable_tooltips = tooltips
        return self
        
    def with_wsj_style(self) -> 'LineChartBuilder':
        """Apply Wall Street Journal-inspired styling."""
        self.config.wsj_mode = True
        self.config.minimalist = True
        self.config.subtle_colors = True
        
        # WSJ color palette - professional grays
        self.config.background_color = '#FFFFFF'
        self.config.plot_background = '#F8F9FA'  # Light gray
        self.config.grid_color = '#E9ECEF'       # Light gray
        self.config.axis_color = '#6C757D'       # Medium gray
        self.config.text_color = '#212529'       # Near black
        self.config.text_muted = '#6C757D'       # Medium gray
        
        # Clean typography
        self.config.font_family = 'Arial'
        self.config.title_font_family = 'Georgia'  # Serif for titles
        
        # Minimalist grid
        self.config.grid_style = 'dotted'
        self.config.grid_alpha = 0.5
        self.config.axis_width = 1
        
        # Subtle data display
        self.config.line_width = 2.0
        self.config.show_data_points = False  # WSJ often omits points
        
        return self
        
    def with_warm_theme(self) -> 'LineChartBuilder':
        """Apply the warm color theme from the design system."""
        self.config.wsj_mode = False
        
        # Professional colors
        self.config.primary_color = '#5B6770'
        self.config.secondary_color = '#ADB5BD' 
        self.config.background_color = '#FFFFFF'
        self.config.plot_background = '#F8F9FA'
        self.config.grid_color = '#E9ECEF'
        
        return self
        
    def with_size(self, width: int, height: int) -> 'LineChartBuilder':
        """Set chart size."""
        self._size = (width, height)
        return self
        
    def with_legend(self, show: bool = True, 
                   position: Literal['top', 'right', 'bottom', 'left'] = 'top') -> 'LineChartBuilder':
        """Configure legend display."""
        self.config.show_legend = show
        self.config.legend_position = position
        return self
        
    def with_grid(self, show: bool = True, style: str = 'dotted') -> 'LineChartBuilder':
        """Configure grid display."""
        self.config.show_grid = show
        self.config.grid_style = style
        return self
        
    def build(self):
        """Build and return the configured line chart."""
        from .enhanced_line_chart import EnhancedLineChart
        
        chart = EnhancedLineChart(config=self.config)
        chart.set_labels(self._title, self._subtitle, self._x_label, self._y_label)
        chart.resize(*self._size)
        
        return chart