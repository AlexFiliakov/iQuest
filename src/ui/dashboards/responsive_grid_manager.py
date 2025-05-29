"""Responsive grid management for dashboard layouts."""

from PyQt6.QtCore import QSize, QRect, QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
from typing import List, Dict, Tuple, Optional
import math

from .dashboard_models import GridConfiguration, GridSpec, ChartConfig


class ResponsiveGridManager(QObject):
    """Manages responsive grid behavior for dashboards."""
    
    # Signals
    layout_recalculated = pyqtSignal()
    
    # Golden ratio for aesthetic proportions
    GOLDEN_RATIO = 1.618
    
    # Minimum chart dimensions
    MIN_CHART_WIDTH = 250
    MIN_CHART_HEIGHT = 200
    
    # Aspect ratio ranges for different chart types
    ASPECT_RATIOS = {
        'time_series': (2.0, 3.0),      # Wide
        'bar_chart': (1.2, 2.0),         # Moderate
        'pie_chart': (1.0, 1.2),         # Square-ish
        'heatmap': (1.5, 2.5),           # Wide
        'gauge': (1.0, 1.0),             # Square
        'progress_ring': (1.0, 1.0),     # Square
        'timeline': (3.0, 4.0),          # Very wide
        'default': (1.2, 2.0)            # Default range
    }
    
    def __init__(self, dashboard_widget: QWidget = None):
        super().__init__()
        self.dashboard = dashboard_widget
        self.current_breakpoint = 'desktop'
        self.grid_columns = 12
        self.gutter = 16
        self.margin = 24
        
    def calculate_optimal_layout(self, container_size: QSize, 
                               chart_configs: List[ChartConfig]) -> GridConfiguration:
        """Calculate optimal grid configuration for given size and charts."""
        width = container_size.width()
        height = container_size.height()
        
        # Determine breakpoint
        breakpoint = self._get_breakpoint(width)
        
        # Calculate usable space
        usable_width = width - (2 * self.margin)
        usable_height = height - (2 * self.margin)
        
        # Calculate grid dimensions based on breakpoint
        if breakpoint == 'mobile':
            return self._mobile_grid(chart_configs, usable_width, usable_height)
        elif breakpoint == 'tablet':
            return self._tablet_grid(chart_configs, usable_width, usable_height)
        elif breakpoint == 'desktop':
            return self._desktop_grid(chart_configs, usable_width, usable_height)
        else:
            return self._wide_grid(chart_configs, usable_width, usable_height)
    
    def _get_breakpoint(self, width: int) -> str:
        """Determine current responsive breakpoint."""
        if width < 768:
            return 'mobile'
        elif width < 1024:
            return 'tablet'
        elif width < 1440:
            return 'desktop'
        else:
            return 'wide'
    
    def _mobile_grid(self, charts: List[ChartConfig], 
                    width: int, height: int) -> GridConfiguration:
        """Calculate mobile grid configuration (single column)."""
        # All charts stack vertically
        chart_height = min(height // len(charts), 400)  # Cap height
        chart_width = width
        
        return GridConfiguration(
            primary_size=(chart_width, chart_height),
            secondary_size=(chart_width, chart_height),
            layout='stacked',
            columns=1,
            gutter=self.gutter,
            margin=self.margin
        )
    
    def _tablet_grid(self, charts: List[ChartConfig], 
                    width: int, height: int) -> GridConfiguration:
        """Calculate tablet grid configuration (2 columns)."""
        # 2-column layout
        column_width = (width - self.gutter) // 2
        
        # Determine primary chart size (if any)
        primary_charts = [c for c in charts if c.grid_spec.col_span > 6]
        if primary_charts:
            # Primary takes full width
            primary_width = width
            primary_height = int(primary_width / self.GOLDEN_RATIO)
            
            # Secondary charts in 2 columns
            secondary_width = column_width
            secondary_height = int(secondary_width / 1.5)
        else:
            # All charts equal in 2-column grid
            primary_width = secondary_width = column_width
            primary_height = secondary_height = int(column_width / 1.5)
        
        return GridConfiguration(
            primary_size=(primary_width, primary_height),
            secondary_size=(secondary_width, secondary_height),
            layout='grid',
            columns=2,
            gutter=self.gutter,
            margin=self.margin
        )
    
    def _desktop_grid(self, charts: List[ChartConfig], 
                     width: int, height: int) -> GridConfiguration:
        """Calculate desktop grid configuration."""
        # Use golden ratio for primary chart
        primary_width = int(width * 0.618)
        primary_height = int(primary_width / self.GOLDEN_RATIO)
        
        # Calculate secondary chart dimensions
        secondary_width = width - primary_width - self.gutter
        secondary_count = max(1, len(charts) - 1)
        secondary_height = min(
            (height - (secondary_count - 1) * self.gutter) // secondary_count,
            int(secondary_width / 1.5)
        )
        
        return GridConfiguration(
            primary_size=(primary_width, primary_height),
            secondary_size=(secondary_width, secondary_height),
            layout='sidebar',
            columns=12,
            gutter=self.gutter,
            margin=self.margin
        )
    
    def _wide_grid(self, charts: List[ChartConfig], 
                  width: int, height: int) -> GridConfiguration:
        """Calculate wide screen grid configuration."""
        # Can accommodate more complex layouts
        # Calculate optimal column width
        column_width = (width - (self.grid_columns - 1) * self.gutter) // self.grid_columns
        
        # Primary charts can be wider
        primary_cols = 8
        primary_width = (column_width * primary_cols) + (self.gutter * (primary_cols - 1))
        primary_height = int(primary_width / self.GOLDEN_RATIO)
        
        # Secondary charts in remaining space
        secondary_cols = 4
        secondary_width = (column_width * secondary_cols) + (self.gutter * (secondary_cols - 1))
        secondary_height = int(secondary_width / 1.5)
        
        return GridConfiguration(
            primary_size=(primary_width, primary_height),
            secondary_size=(secondary_width, secondary_height),
            layout='grid',
            columns=12,
            gutter=self.gutter,
            margin=self.margin
        )
    
    def calculate_chart_size(self, grid_spec: GridSpec, 
                           grid_config: GridConfiguration,
                           chart_type: str = 'default') -> Tuple[int, int]:
        """Calculate actual size for a chart based on grid specification."""
        # Get column width
        total_width = grid_config.primary_size[0] + grid_config.secondary_size[0] + self.gutter
        column_width = (total_width - (grid_config.columns - 1) * self.gutter) // grid_config.columns
        
        # Calculate chart width
        chart_width = (column_width * grid_spec.col_span) + \
                     (self.gutter * (grid_spec.col_span - 1))
        
        # Get aspect ratio range for chart type
        min_ratio, max_ratio = self.ASPECT_RATIOS.get(chart_type, self.ASPECT_RATIOS['default'])
        
        # Calculate height based on aspect ratio
        ideal_height = int(chart_width / ((min_ratio + max_ratio) / 2))
        
        # Apply minimum constraints
        chart_width = max(chart_width, self.MIN_CHART_WIDTH)
        chart_height = max(ideal_height, self.MIN_CHART_HEIGHT)
        
        return (chart_width, chart_height)
    
    def get_chart_position(self, grid_spec: GridSpec,
                          grid_config: GridConfiguration) -> QRect:
        """Calculate position rectangle for a chart in the grid."""
        # Calculate column width
        total_width = grid_config.primary_size[0] + grid_config.secondary_size[0] + self.gutter
        column_width = (total_width - (grid_config.columns - 1) * self.gutter) // grid_config.columns
        
        # Calculate position
        x = grid_config.margin + (grid_spec.col * (column_width + self.gutter))
        y = grid_config.margin + (grid_spec.row * (self.MIN_CHART_HEIGHT + self.gutter))
        
        # Calculate size
        width, height = self.calculate_chart_size(grid_spec, grid_config)
        
        return QRect(x, y, width, height)
    
    def validate_grid_spec(self, grid_spec: GridSpec, 
                          container_size: QSize) -> Tuple[bool, Optional[str]]:
        """Validate if a grid specification fits in the container."""
        breakpoint = self._get_breakpoint(container_size.width())
        
        # Check column bounds
        if breakpoint == 'mobile' and grid_spec.col > 0:
            return False, "Mobile layout only supports single column"
        elif breakpoint == 'tablet' and grid_spec.col + grid_spec.col_span > 2:
            return False, "Tablet layout only supports 2 columns"
        elif grid_spec.col + grid_spec.col_span > self.grid_columns:
            return False, f"Grid specification exceeds {self.grid_columns} columns"
        
        # Check if chart would be too small
        dummy_config = GridConfiguration(
            primary_size=(container_size.width(), container_size.height()),
            secondary_size=(300, 200),
            layout='grid'
        )
        width, height = self.calculate_chart_size(grid_spec, dummy_config)
        
        if width < self.MIN_CHART_WIDTH or height < self.MIN_CHART_HEIGHT:
            return False, "Chart would be too small with current specification"
        
        return True, None
    
    def suggest_layout(self, chart_count: int, 
                      container_size: QSize) -> List[GridSpec]:
        """Suggest optimal grid layout for given number of charts."""
        breakpoint = self._get_breakpoint(container_size.width())
        suggestions = []
        
        if breakpoint == 'mobile':
            # Stack all vertically
            for i in range(chart_count):
                suggestions.append(GridSpec(row=i, col=0, row_span=1, col_span=1))
                
        elif breakpoint == 'tablet':
            # 2-column layout
            row = 0
            col = 0
            for i in range(chart_count):
                suggestions.append(GridSpec(row=row, col=col, row_span=1, col_span=1))
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
                    
        else:  # desktop or wide
            # Intelligent layout based on chart count
            if chart_count == 1:
                # Single large chart
                suggestions.append(GridSpec(row=0, col=0, row_span=2, col_span=12))
            elif chart_count == 2:
                # Side by side
                suggestions.append(GridSpec(row=0, col=0, row_span=2, col_span=6))
                suggestions.append(GridSpec(row=0, col=6, row_span=2, col_span=6))
            elif chart_count == 3:
                # One large, two small
                suggestions.append(GridSpec(row=0, col=0, row_span=2, col_span=8))
                suggestions.append(GridSpec(row=0, col=8, row_span=1, col_span=4))
                suggestions.append(GridSpec(row=1, col=8, row_span=1, col_span=4))
            elif chart_count == 4:
                # 2x2 grid
                suggestions.append(GridSpec(row=0, col=0, row_span=1, col_span=6))
                suggestions.append(GridSpec(row=0, col=6, row_span=1, col_span=6))
                suggestions.append(GridSpec(row=1, col=0, row_span=1, col_span=6))
                suggestions.append(GridSpec(row=1, col=6, row_span=1, col_span=6))
            else:
                # Complex layout with primary chart
                suggestions.append(GridSpec(row=0, col=0, row_span=2, col_span=8))
                
                # Fill sidebar
                row = 0
                for i in range(1, min(chart_count, 4)):
                    suggestions.append(GridSpec(row=row, col=8, row_span=1, col_span=4))
                    row += 1
                
                # Additional charts below if needed
                if chart_count > 4:
                    row = 2
                    col = 0
                    for i in range(4, chart_count):
                        suggestions.append(GridSpec(row=row, col=col, row_span=1, col_span=4))
                        col += 4
                        if col >= 12:
                            col = 0
                            row += 1
        
        return suggestions