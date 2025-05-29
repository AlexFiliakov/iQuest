"""WSJ-styled responsive dashboard layout for health metrics."""

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QSizePolicy, QFrame,
    QVBoxLayout, QHBoxLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor
from typing import List, Dict, Optional, Tuple
import logging

from .dashboard_models import (
    GridSpec, ChartConfig, DashboardTemplate,
    DashboardState, LayoutType
)
from ..charts.base_chart import BaseChart

logger = logging.getLogger(__name__)


class WSJDashboardLayout(QWidget):
    """WSJ-styled responsive dashboard layout for health data visualization."""
    
    # Signals
    layout_changed = pyqtSignal(str)  # layout_name
    chart_focused = pyqtSignal(str)  # chart_id
    chart_interaction = pyqtSignal(str, dict)  # chart_id, interaction_data
    time_range_changed = pyqtSignal(object, object)  # start, end
    
    # WSJ Grid System Constants
    GRID_COLUMNS = 12
    GUTTER_WIDTH = 16  # pixels
    MARGIN = 24  # pixels
    
    # Responsive breakpoints
    BREAKPOINTS = {
        'mobile': 768,
        'tablet': 1024,
        'desktop': 1440,
        'wide': 1920
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts: Dict[str, BaseChart] = {}
        self.chart_configs: Dict[str, ChartConfig] = {}
        self.current_layout = 'default'
        self.current_breakpoint = 'desktop'
        self._focused_chart: Optional[str] = None
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for dashboard
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(self.scroll_area)
        
        # Dashboard container
        self.dashboard_container = QWidget()
        self.scroll_area.setWidget(self.dashboard_container)
        
        # Grid layout for charts
        self.grid_layout = QGridLayout(self.dashboard_container)
        self._setup_wsj_styling()
        
        # Animation support
        self._animations: List[QPropertyAnimation] = []
        
    def _setup_wsj_styling(self):
        """Apply WSJ styling to dashboard."""
        # Background color matching WSJ aesthetic
        self.setStyleSheet(f"""
            WSJDashboardLayout {{
                background-color: #F5E6D3;
                border: 1px solid #D4B5A0;
            }}
            QScrollArea {{
                background-color: #F5E6D3;
                border: none;
            }}
            QScrollBar:vertical {{
                background: #F5E6D3;
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #D4B5A0;
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #C4A590;
            }}
        """)
        
        # Grid spacing matching WSJ
        self.grid_layout.setSpacing(self.GUTTER_WIDTH)
        self.grid_layout.setContentsMargins(self.MARGIN, self.MARGIN, 
                                           self.MARGIN, self.MARGIN)
        
    def add_chart(self, chart_id: str, chart: BaseChart, 
                  grid_spec: GridSpec, config: Optional[ChartConfig] = None) -> None:
        """Add chart to dashboard with grid specification."""
        if chart_id in self.charts:
            logger.warning(f"Replacing existing chart: {chart_id}")
            self.remove_chart(chart_id)
            
        self.charts[chart_id] = chart
        if config:
            self.chart_configs[chart_id] = config
        
        # Apply WSJ chart frame styling
        chart.setFrameStyle(QFrame.Shape.Box)
        chart.setStyleSheet("""
            BaseChart {
                background-color: white;
                border: 1px solid #E8D4BC;
                border-radius: 4px;
                padding: 8px;
            }
            BaseChart:hover {
                border: 2px solid #D4B5A0;
            }
        """)
        
        # Add to grid
        self.grid_layout.addWidget(
            chart,
            grid_spec.row,
            grid_spec.col,
            grid_spec.row_span,
            grid_spec.col_span
        )
        
        # Set size policy for responsive behavior
        chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Set minimum size if specified
        if config:
            chart.setMinimumSize(config.min_width, config.min_height)
        
        # Connect chart interactions
        self._connect_chart_signals(chart_id, chart)
        
    def remove_chart(self, chart_id: str) -> None:
        """Remove chart from dashboard."""
        if chart_id in self.charts:
            chart = self.charts[chart_id]
            self.grid_layout.removeWidget(chart)
            chart.deleteLater()
            del self.charts[chart_id]
            if chart_id in self.chart_configs:
                del self.chart_configs[chart_id]
            
    def _connect_chart_signals(self, chart_id: str, chart: BaseChart):
        """Connect chart interaction signals."""
        # Connect standard chart signals
        if hasattr(chart, 'clicked'):
            chart.clicked.connect(lambda: self._on_chart_clicked(chart_id))
        if hasattr(chart, 'time_range_selected'):
            chart.time_range_selected.connect(self._on_time_range_selected)
            
    def _on_chart_clicked(self, chart_id: str):
        """Handle chart click events."""
        self.set_focused_chart(chart_id)
        
    def _on_time_range_selected(self, start, end):
        """Handle time range selection from any chart."""
        # Broadcast to all charts for synchronization
        self.time_range_changed.emit(start, end)
        
    def set_focused_chart(self, chart_id: str):
        """Set the focused chart with visual feedback."""
        if self._focused_chart == chart_id:
            return
            
        # Remove focus from previous chart
        if self._focused_chart and self._focused_chart in self.charts:
            prev_chart = self.charts[self._focused_chart]
            prev_chart.setStyleSheet("""
                BaseChart {
                    background-color: white;
                    border: 1px solid #E8D4BC;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            
        # Set focus to new chart
        self._focused_chart = chart_id
        if chart_id in self.charts:
            chart = self.charts[chart_id]
            chart.setStyleSheet("""
                BaseChart {
                    background-color: white;
                    border: 2px solid #FF8C42;
                    border-radius: 4px;
                    padding: 8px;
                    box-shadow: 0 2px 8px rgba(255, 140, 66, 0.3);
                }
            """)
            self.chart_focused.emit(chart_id)
            
    def apply_layout_template(self, template: DashboardTemplate) -> None:
        """Apply predefined dashboard template."""
        # Clear existing layout
        self._clear_layout()
        
        # Apply new template
        for chart_config in template.chart_configs:
            # Create chart widget (this would be done by a factory in real implementation)
            chart = self._create_chart_for_config(chart_config)
            if chart:
                self.add_chart(
                    chart_config.chart_id,
                    chart,
                    chart_config.grid_spec,
                    chart_config
                )
            
        self.current_layout = template.name
        self.layout_changed.emit(template.name)
        
    def _create_chart_for_config(self, config: ChartConfig) -> Optional[BaseChart]:
        """Create appropriate chart widget for configuration."""
        # This would be handled by a chart factory in real implementation
        # For now, return None to indicate placeholder
        logger.info(f"Would create {config.chart_type} for {config.metric_type}")
        return None
        
    def _clear_layout(self):
        """Clear all charts from layout."""
        chart_ids = list(self.charts.keys())
        for chart_id in chart_ids:
            self.remove_chart(chart_id)
            
    def optimize_for_size(self, width: int, height: int) -> None:
        """Optimize layout for current window size."""
        old_breakpoint = self.current_breakpoint
        
        # Determine new breakpoint
        if width < self.BREAKPOINTS['mobile']:
            self.current_breakpoint = 'mobile'
        elif width < self.BREAKPOINTS['tablet']:
            self.current_breakpoint = 'tablet'
        elif width < self.BREAKPOINTS['desktop']:
            self.current_breakpoint = 'desktop'
        else:
            self.current_breakpoint = 'wide'
            
        # Only reorganize if breakpoint changed
        if old_breakpoint != self.current_breakpoint:
            self._reorganize_for_breakpoint()
            
    def _reorganize_for_breakpoint(self):
        """Reorganize charts based on current breakpoint."""
        if self.current_breakpoint == 'mobile':
            self._apply_mobile_layout()
        elif self.current_breakpoint == 'tablet':
            self._apply_tablet_layout()
        elif self.current_breakpoint == 'desktop':
            self._apply_desktop_layout()
        else:
            self._apply_wide_layout()
            
    def _apply_mobile_layout(self):
        """Stack all charts vertically for mobile."""
        row = 0
        for chart_id, chart in self.charts.items():
            self.grid_layout.removeWidget(chart)
            self.grid_layout.addWidget(chart, row, 0, 1, self.GRID_COLUMNS)
            row += 1
            
    def _apply_tablet_layout(self):
        """Apply 2-column layout for tablets."""
        row = 0
        col = 0
        half_grid = self.GRID_COLUMNS // 2
        
        for chart_id, chart in self.charts.items():
            self.grid_layout.removeWidget(chart)
            self.grid_layout.addWidget(chart, row, col * half_grid, 1, half_grid)
            col += 1
            if col >= 2:
                col = 0
                row += 1
                
    def _apply_desktop_layout(self):
        """Apply standard desktop grid layout."""
        # This would restore original grid specifications
        # For now, implement basic primary + sidebar layout
        charts_list = list(self.charts.items())
        if not charts_list:
            return
            
        # Primary chart takes 8 columns
        if len(charts_list) > 0:
            primary_id, primary_chart = charts_list[0]
            self.grid_layout.removeWidget(primary_chart)
            self.grid_layout.addWidget(primary_chart, 0, 0, 2, 8)
            
        # Secondary charts in 4-column sidebar
        row = 0
        for i in range(1, len(charts_list)):
            chart_id, chart = charts_list[i]
            self.grid_layout.removeWidget(chart)
            self.grid_layout.addWidget(chart, row, 8, 1, 4)
            row += 1
            
    def _apply_wide_layout(self):
        """Apply wide screen layout with more columns."""
        # Similar to desktop but can use more sophisticated grid
        self._apply_desktop_layout()  # For now
        
    def resizeEvent(self, event):
        """Handle resize events to adjust layout."""
        super().resizeEvent(event)
        self.optimize_for_size(event.size().width(), event.size().height())
        
    def get_dashboard_state(self) -> DashboardState:
        """Get current dashboard state for persistence."""
        chart_states = {}
        for chart_id, chart in self.charts.items():
            if hasattr(chart, 'get_state'):
                chart_states[chart_id] = chart.get_state()
                
        return DashboardState(
            layout_name=self.current_layout,
            chart_states=chart_states,
            focused_chart=self._focused_chart
        )
        
    def restore_dashboard_state(self, state: DashboardState):
        """Restore dashboard state from saved configuration."""
        # Restore chart states
        for chart_id, chart_state in state.chart_states.items():
            if chart_id in self.charts and hasattr(self.charts[chart_id], 'set_state'):
                self.charts[chart_id].set_state(chart_state)
                
        # Restore focus
        if state.focused_chart:
            self.set_focused_chart(state.focused_chart)