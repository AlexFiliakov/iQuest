"""
Small multiples component for comparative visualization.

Provides a grid of small charts with consistent scales for easy comparison.
Perfect for showing multiple metrics or time periods side by side.
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QFrame, QScrollArea, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from ..style_manager import StyleManager


class SmallMultipleChart:
    """Individual chart within the small multiples grid."""
    
    def __init__(self, title: str, chart_type: str, x_data: List, y_data: List):
        self.title = title
        self.chart_type = chart_type  # 'line', 'bar', 'area'
        self.x_data = x_data
        self.y_data = y_data
        self.color = '#2E86AB'  # Default WSJ blue
        self.annotations = []


class SmallMultiplesWidget(QWidget):
    """
    Professional small multiples widget with WSJ-inspired styling.
    
    Features:
    - Grid layout with consistent scales
    - Multiple chart types (line, bar, area)
    - Synchronized interactions
    - Responsive sizing
    - Clean, minimalist design
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.style_manager = StyleManager()
        
        # Chart data
        self.charts_data: List[SmallMultipleChart] = []
        self.title = ""
        self.grid_cols = 3
        self.grid_rows = 2
        
        # Visual properties
        self.wsj_colors = [
            '#2E86AB',  # Professional blue
            '#A23B72',  # Deep magenta
            '#F18F01',  # Warm orange
            '#C73E1D',  # WSJ red
            '#50C878',  # Emerald green
            '#6A4C93',  # Purple
        ]
        
        self.background_color = '#FAFAFA'
        self.grid_color = '#E8E8E8'
        self.text_color = '#2C3E50'
        self.font_family = 'Arial, sans-serif'
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(self)
        title_font = QFont(self.font_family, 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {self.text_color}; margin-bottom: 10px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Grid size controls
        header_layout.addWidget(QLabel("Columns:"))
        self.cols_spinbox = QSpinBox(self)
        self.cols_spinbox.setRange(1, 6)
        self.cols_spinbox.setValue(3)
        self.cols_spinbox.valueChanged.connect(self._update_grid_layout)
        header_layout.addWidget(self.cols_spinbox)
        
        header_layout.addWidget(QLabel("Rows:"))
        self.rows_spinbox = QSpinBox(self)
        self.rows_spinbox.setRange(1, 4)
        self.rows_spinbox.setValue(2)
        self.rows_spinbox.valueChanged.connect(self._update_grid_layout)
        header_layout.addWidget(self.rows_spinbox)
        
        layout.addLayout(header_layout)
        
        # Scrollable chart area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Chart container
        self.chart_container = QWidget(self)
        scroll_area.setWidget(self.chart_container)
        layout.addWidget(scroll_area)
        
        # Initialize with matplotlib figure
        self._create_matplotlib_figure()
    
    def _create_matplotlib_figure(self):
        """Create the matplotlib figure for small multiples."""
        # Calculate figure size based on grid
        fig_width = max(12, self.grid_cols * 4)
        fig_height = max(8, self.grid_rows * 3)
        
        self.figure = Figure(figsize=(fig_width, fig_height), 
                           dpi=100, facecolor=self.background_color)
        
        # Create canvas
        if hasattr(self, 'canvas'):
            self.canvas.setParent(None)
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(self.canvas.sizePolicy().Expanding, 
                                self.canvas.sizePolicy().Expanding)
        
        # Add canvas to container
        container_layout = QVBoxLayout(self.chart_container)
        container_layout.addWidget(self.canvas)
        
        # Create subplot grid
        self.gs = gridspec.GridSpec(self.grid_rows, self.grid_cols, 
                                  figure=self.figure,
                                  hspace=0.4, wspace=0.3)
    
    def set_data(self, charts_data: List[SmallMultipleChart], title: str = ""):
        """Set chart data and refresh visualization."""
        self.charts_data = charts_data
        self.title = title
        self.title_label.setText(title)
        
        # Assign colors to charts
        for i, chart in enumerate(self.charts_data):
            chart.color = self.wsj_colors[i % len(self.wsj_colors)]
        
        self._render_charts()
    
    def _update_grid_layout(self):
        """Update grid layout based on spinbox values."""
        self.grid_cols = self.cols_spinbox.value()
        self.grid_rows = self.rows_spinbox.value()
        
        self._create_matplotlib_figure()
        if self.charts_data:
            self._render_charts()
    
    def _render_charts(self):
        """Render all charts in the grid."""
        if not self.charts_data:
            return
        
        self.figure.clear()
        
        # Recreate grid spec
        self.gs = gridspec.GridSpec(self.grid_rows, self.grid_cols, 
                                  figure=self.figure,
                                  hspace=0.4, wspace=0.3)
        
        # Calculate global y-axis limits for consistency
        all_y_values = []
        for chart in self.charts_data:
            if chart.y_data:
                all_y_values.extend(chart.y_data)
        
        if all_y_values:
            global_y_min = min(all_y_values) * 0.95
            global_y_max = max(all_y_values) * 1.05
        else:
            global_y_min, global_y_max = 0, 1
        
        # Render each chart
        for i, chart_data in enumerate(self.charts_data):
            if i >= self.grid_rows * self.grid_cols:
                break  # Skip if too many charts for grid
            
            row = i // self.grid_cols
            col = i % self.grid_cols
            
            ax = self.figure.add_subplot(self.gs[row, col])
            self._render_single_chart(ax, chart_data, global_y_min, global_y_max)
        
        # Set figure background
        self.figure.patch.set_facecolor(self.background_color)
        
        # Refresh canvas
        self.canvas.draw()
    
    def _render_single_chart(self, ax, chart_data: SmallMultipleChart, 
                           global_y_min: float, global_y_max: float):
        """Render a single chart in the grid."""
        if not chart_data.x_data or not chart_data.y_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12, color=self.text_color)
            return
        
        # Set style
        ax.set_facecolor(self.background_color)
        ax.grid(True, linestyle='-', alpha=0.3, color=self.grid_color)
        ax.set_axisbelow(True)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.grid_color)
        ax.spines['bottom'].set_color(self.grid_color)
        
        # Configure ticks
        ax.tick_params(colors=self.text_color, which='both', labelsize=8)
        
        # Render based on chart type
        if chart_data.chart_type == 'line':
            ax.plot(chart_data.x_data, chart_data.y_data, 
                   color=chart_data.color, linewidth=2, marker='o', 
                   markersize=3, alpha=0.8)
            
        elif chart_data.chart_type == 'bar':
            ax.bar(range(len(chart_data.y_data)), chart_data.y_data,
                  color=chart_data.color, alpha=0.7, 
                  edgecolor='white', linewidth=0.5)
            
            # Set x-tick labels
            if len(chart_data.x_data) == len(chart_data.y_data):
                ax.set_xticks(range(len(chart_data.x_data)))
                ax.set_xticklabels(chart_data.x_data, rotation=45, ha='right')
                
        elif chart_data.chart_type == 'area':
            ax.fill_between(range(len(chart_data.y_data)), chart_data.y_data,
                          color=chart_data.color, alpha=0.5)
            ax.plot(range(len(chart_data.y_data)), chart_data.y_data,
                   color=chart_data.color, linewidth=2)
            
            # Set x-tick labels
            if len(chart_data.x_data) == len(chart_data.y_data):
                ax.set_xticks(range(len(chart_data.x_data)))
                ax.set_xticklabels(chart_data.x_data, rotation=45, ha='right')
        
        # Set consistent y-axis limits
        ax.set_ylim(global_y_min, global_y_max)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))
        
        # Set title
        ax.set_title(chart_data.title, fontsize=10, fontweight='bold',
                    color=self.text_color, pad=10)
        
        # Add annotations if any
        for annotation in chart_data.annotations:
            ax.annotate(annotation['text'], 
                       xy=annotation['xy'],
                       xytext=annotation.get('xytext', (5, 5)),
                       textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='yellow', alpha=0.7),
                       fontsize=7)
    
    def add_trend_lines(self, enable_trends: bool = True):
        """Add trend lines to line charts."""
        if not enable_trends or not self.charts_data:
            return
        
        for i, chart_data in enumerate(self.charts_data):
            if chart_data.chart_type != 'line' or len(chart_data.y_data) < 3:
                continue
            
            if i >= self.grid_rows * self.grid_cols:
                break
            
            row = i // self.grid_cols
            col = i % self.grid_cols
            
            try:
                ax = self.figure.axes[i]
                
                # Calculate trend line
                x_vals = np.arange(len(chart_data.y_data))
                z = np.polyfit(x_vals, chart_data.y_data, 1)
                trend_line = np.poly1d(z)
                
                # Add trend line
                ax.plot(x_vals, trend_line(x_vals), 
                       color=chart_data.color, linestyle='--', 
                       alpha=0.6, linewidth=1)
                
            except (IndexError, np.RankWarning):
                continue
        
        self.canvas.draw()
    
    def highlight_extremes(self, highlight_max: bool = True, highlight_min: bool = True):
        """Highlight maximum and minimum values in each chart."""
        for i, chart_data in enumerate(self.charts_data):
            if not chart_data.y_data or i >= len(self.figure.axes):
                continue
            
            ax = self.figure.axes[i]
            
            if highlight_max:
                max_idx = np.argmax(chart_data.y_data)
                max_val = chart_data.y_data[max_idx]
                ax.scatter([max_idx], [max_val], color='red', s=50, 
                          marker='^', zorder=10, alpha=0.8)
                ax.annotate(f'Max: {max_val:.1f}', 
                           xy=(max_idx, max_val),
                           xytext=(5, 10), textcoords='offset points',
                           fontsize=7, color='red', weight='bold')
            
            if highlight_min:
                min_idx = np.argmin(chart_data.y_data)
                min_val = chart_data.y_data[min_idx]
                ax.scatter([min_idx], [min_val], color='blue', s=50, 
                          marker='v', zorder=10, alpha=0.8)
                ax.annotate(f'Min: {min_val:.1f}', 
                           xy=(min_idx, min_val),
                           xytext=(5, -15), textcoords='offset points',
                           fontsize=7, color='blue', weight='bold')
        
        self.canvas.draw()
    
    def export_chart(self, filepath: str, dpi: int = 300):
        """Export chart to file."""
        try:
            self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight',
                              facecolor=self.background_color)
            return True
        except Exception as e:
            print(f"Failed to export chart: {e}")
            return False
    
    def get_chart_data(self) -> Dict[str, Any]:
        """Get chart data for external use."""
        charts_dict = []
        for chart in self.charts_data:
            charts_dict.append({
                'title': chart.title,
                'type': chart.chart_type,
                'x_data': chart.x_data,
                'y_data': chart.y_data,
                'color': chart.color
            })
        
        return {
            'title': self.title,
            'grid_cols': self.grid_cols,
            'grid_rows': self.grid_rows,
            'charts': charts_dict
        }


class SmallMultiplesContainer(QFrame):
    """
    Complete small multiples container with controls and metadata.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the container UI."""
        layout = QVBoxLayout(self)
        
        # Chart widget
        self.chart = SmallMultiplesWidget()
        layout.addWidget(self.chart)
        
        # Controls panel
        controls_layout = QHBoxLayout()
        
        # Trend lines toggle
        self.trends_checkbox = QCheckBox("Show Trend Lines")
        self.trends_checkbox.toggled.connect(self.chart.add_trend_lines)
        controls_layout.addWidget(self.trends_checkbox)
        
        # Extremes toggle
        self.extremes_checkbox = QCheckBox("Highlight Extremes")
        self.extremes_checkbox.toggled.connect(
            lambda checked: self.chart.highlight_extremes(checked, checked)
        )
        controls_layout.addWidget(self.extremes_checkbox)
        
        controls_layout.addStretch()
        
        # Summary label
        self.summary_label = QLabel(self)
        self.summary_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        controls_layout.addWidget(self.summary_label)
        
        layout.addLayout(controls_layout)
    
    def set_chart_data(self, charts_data: List[SmallMultipleChart], title=""):
        """Set chart data and update summary."""
        self.chart.set_data(charts_data, title)
        
        # Calculate summary
        total_charts = len(charts_data)
        chart_types = set(chart.chart_type for chart in charts_data)
        
        summary_text = f"{total_charts} charts • Types: {', '.join(chart_types)}"
        self.summary_label.setText(summary_text)