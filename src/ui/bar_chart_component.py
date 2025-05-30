"""
Reusable Bar Chart Component for Apple Health Dashboard

This module provides a flexible bar chart component inspired by Wall Street Journal
style charts with warm color theming and interactive features.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle
from matplotlib.container import BarContainer
from matplotlib.axes import Axes
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates

from .style_manager import StyleManager


@dataclass
class BarChartConfig:
    """Configuration class for bar chart styling and behavior."""
    
    # Colors from StyleManager
    color_palette: List[str] = field(default_factory=lambda: StyleManager.CHART_COLORS)
    
    # Bar styling
    bar_width: float = 0.8
    bar_alpha: float = 0.8
    edge_color: str = 'none'
    
    # Labels
    show_value_labels: bool = True
    label_font_size: int = 10
    label_color: str = StyleManager.TEXT_PRIMARY
    label_offset: float = 0.02  # Percentage of y-range
    
    # Legend
    show_legend: bool = True
    legend_location: str = 'upper right'
    
    # Grid
    show_grid: bool = True
    grid_alpha: float = 0.3
    grid_color: str = StyleManager.TEXT_MUTED
    
    # Animation
    animate: bool = True
    animation_duration: int = 800
    
    # Interactivity
    enable_hover: bool = True
    enable_selection: bool = True
    tooltip_bg: str = StyleManager.SECONDARY_BG
    
    # WSJ-style formatting
    wsj_style: bool = True
    clean_spines: bool = True
    minimal_ticks: bool = True
    
    def get_color_sequence(self, n_colors: int) -> List[str]:
        """Get a sequence of colors for the chart."""
        if n_colors <= len(self.color_palette):
            return self.color_palette[:n_colors]
        else:
            # Cycle through palette if more colors needed
            return [self.color_palette[i % len(self.color_palette)] for i in range(n_colors)]


class ValueLabelManager:
    """Manages value labels positioning and formatting for bar charts."""
    
    def __init__(self, ax: Axes, config: BarChartConfig):
        self.ax = ax
        self.config = config
        
    def add_labels(self, bars: BarContainer, format_str: str = '{:.0f}', series_name: str = ''):
        """Add value labels to bars with smart positioning."""
        if not self.config.show_value_labels:
            return
            
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only label positive values
                label = format_str.format(height)
                
                # Smart positioning based on bar height and chart limits
                y_pos = height + self.config.label_offset * (self.ax.get_ylim()[1] - self.ax.get_ylim()[0])
                
                # If label would be too close to top, place inside bar
                if y_pos > self.ax.get_ylim()[1] * 0.95:
                    y_pos = height - self.config.label_offset * (self.ax.get_ylim()[1] - self.ax.get_ylim()[0])
                    color = StyleManager.TEXT_INVERSE
                    va = 'top'
                else:
                    color = self.config.label_color
                    va = 'bottom'
                    
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    y_pos,
                    label,
                    ha='center',
                    va=va,
                    fontsize=self.config.label_font_size,
                    color=color,
                    fontweight='500'
                )


class BarChart(QWidget):
    """
    Base bar chart component supporting simple, grouped, and stacked bar charts
    with WSJ-inspired styling and interactive features.
    """
    
    # Signals
    bar_clicked = pyqtSignal(str, float)  # category, value
    bar_hovered = pyqtSignal(str, float)  # category, value
    
    def __init__(self, config: Optional[BarChartConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or BarChartConfig()
        self.style_manager = StyleManager()
        
        # Chart components
        self.figure = Figure(figsize=(10, 6), facecolor=StyleManager.SECONDARY_BG)
        self.canvas = FigureCanvas(self.figure)
        self.ax = None
        
        # Data tracking
        self.bar_containers = []
        self.data = None
        self.chart_type = 'simple'
        
        # Interactive elements
        self.hover_annotation = None
        self.selected_bars = []
        
        # Animation
        self.animation = None
        
        self.setup_ui()
        self.setup_canvas_style()
        
    def setup_ui(self):
        """Initialize the widget layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
    def setup_canvas_style(self):
        """Configure canvas styling for WSJ-inspired look."""
        # Set figure style
        self.figure.patch.set_facecolor(StyleManager.SECONDARY_BG)
        self.figure.patch.set_alpha(1.0)
        
        # Tight layout for clean appearance
        self.figure.tight_layout(pad=2.0)
        
    def apply_wsj_style(self):
        """Apply Wall Street Journal-inspired styling to the chart."""
        if not self.config.wsj_style or not self.ax:
            return
            
        # Clean spines - only show left and bottom
        if self.config.clean_spines:
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(StyleManager.TEXT_MUTED)
            self.ax.spines['bottom'].set_color(StyleManager.TEXT_MUTED)
            self.ax.spines['left'].set_linewidth(0.8)
            self.ax.spines['bottom'].set_linewidth(0.8)
        
        # Minimal ticks
        if self.config.minimal_ticks:
            self.ax.tick_params(
                axis='both',
                which='major',
                labelsize=10,
                color=StyleManager.TEXT_MUTED,
                labelcolor=StyleManager.TEXT_SECONDARY,
                length=4,
                width=0.8
            )
            
        # Grid styling
        if self.config.show_grid:
            self.ax.grid(
                True,
                alpha=self.config.grid_alpha,
                color=self.config.grid_color,
                linewidth=0.5,
                linestyle='-',
                axis='y'
            )
            self.ax.set_axisbelow(True)
            
        # Font styling
        for label in self.ax.get_xticklabels():
            label.set_fontweight('400')
            label.set_fontsize(10)
        for label in self.ax.get_yticklabels():
            label.set_fontweight('400')
            label.set_fontsize(10)
            
    def plot(self, data: pd.DataFrame, chart_type: str = 'simple', **kwargs):
        """
        Plot bar chart with specified type.
        
        Args:
            data: DataFrame with categories as index and values as columns
            chart_type: 'simple', 'grouped', or 'stacked'
            **kwargs: Additional plotting parameters
        """
        self.data = data.copy()
        self.chart_type = chart_type
        
        # Clear previous plot
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.bar_containers = []
        
        # Apply base styling
        self.apply_wsj_style()
        
        # Plot based on type
        if chart_type == 'simple':
            self._plot_simple_bars(data, **kwargs)
        elif chart_type == 'grouped':
            self._plot_grouped_bars(data, **kwargs)
        elif chart_type == 'stacked':
            self._plot_stacked_bars(data, **kwargs)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
            
        # Add labels and configure legend
        self._add_value_labels()
        self._configure_legend()
        
        # Setup interactions
        if self.config.enable_hover or self.config.enable_selection:
            self.setup_interactions()
            
        # Refresh canvas
        self.canvas.draw()
        
        # Animate if enabled
        if self.config.animate:
            self.animate_bars()
            
    def _plot_simple_bars(self, data: pd.DataFrame, **kwargs):
        """Plot simple bar chart with single data series."""
        # Handle empty data
        if data.empty or data.shape[0] == 0 or data.shape[1] == 0:
            return
            
        if data.shape[1] != 1:
            # Use first column if multiple columns provided
            series = data.iloc[:, 0]
        else:
            series = data.iloc[:, 0]
            
        colors = self.config.get_color_sequence(len(series))
        
        bars = self.ax.bar(
            range(len(series)),
            series.values,
            width=self.config.bar_width,
            alpha=self.config.bar_alpha,
            color=colors,
            edgecolor=self.config.edge_color,
            **kwargs
        )
        
        self.bar_containers.append(bars)
        
        # Set labels
        self.ax.set_xticks(range(len(series)))
        self.ax.set_xticklabels(series.index, rotation=0)
        
        # Set title if provided
        if hasattr(series, 'name') and series.name:
            self.ax.set_ylabel(series.name, fontweight='500', fontsize=12)
            
    def _plot_grouped_bars(self, data: pd.DataFrame, **kwargs):
        """Plot grouped bar chart with multiple data series."""
        # Handle empty data
        if data.empty or data.shape[0] == 0 or data.shape[1] == 0:
            return
        n_groups = len(data.index)
        n_bars = len(data.columns)
        width = self.config.bar_width / n_bars
        
        colors = self.config.get_color_sequence(n_bars)
        
        for i, column in enumerate(data.columns):
            positions = np.arange(n_groups) + i * width - (n_bars - 1) * width / 2
            bars = self.ax.bar(
                positions,
                data[column],
                width,
                label=column,
                color=colors[i],
                alpha=self.config.bar_alpha,
                edgecolor=self.config.edge_color,
                **kwargs
            )
            self.bar_containers.append(bars)
            
        # Center x-tick labels
        self.ax.set_xticks(np.arange(n_groups))
        self.ax.set_xticklabels(data.index, rotation=0)
        
    def _plot_stacked_bars(self, data: pd.DataFrame, **kwargs):
        """Plot stacked bar chart with multiple data series."""
        # Handle empty data
        if data.empty or data.shape[0] == 0 or data.shape[1] == 0:
            return
        colors = self.config.get_color_sequence(len(data.columns))
        
        bottom = np.zeros(len(data.index))
        
        for i, column in enumerate(data.columns):
            bars = self.ax.bar(
                range(len(data.index)),
                data[column],
                width=self.config.bar_width,
                bottom=bottom,
                label=column,
                color=colors[i],
                alpha=self.config.bar_alpha,
                edgecolor=self.config.edge_color,
                **kwargs
            )
            self.bar_containers.append(bars)
            bottom += data[column]
            
        # Set labels
        self.ax.set_xticks(range(len(data.index)))
        self.ax.set_xticklabels(data.index, rotation=0)
        
    def _add_value_labels(self):
        """Add value labels to all bar containers."""
        label_manager = ValueLabelManager(self.ax, self.config)
        
        for i, container in enumerate(self.bar_containers):
            if self.chart_type == 'grouped' and len(self.data.columns) > 1:
                series_name = self.data.columns[i]
                format_str = '{:.0f}'
            else:
                series_name = ''
                format_str = '{:.0f}'
                
            label_manager.add_labels(container, format_str, series_name)
            
    def _configure_legend(self):
        """Configure legend if needed."""
        if self.config.show_legend and len(self.bar_containers) > 1:
            legend = self.ax.legend(
                loc=self.config.legend_location,
                frameon=True,
                fancybox=True,
                shadow=False,
                framealpha=0.9,
                edgecolor='none'
            )
            legend.get_frame().set_facecolor(StyleManager.SECONDARY_BG)
            for text in legend.get_texts():
                text.set_color(StyleManager.TEXT_PRIMARY)
                text.set_fontsize(10)
                text.set_fontweight('400')
                
    def setup_interactions(self):
        """Setup hover and click interactions."""
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
    def on_hover(self, event):
        """Handle hover events for interactive tooltips."""
        if not self.config.enable_hover or event.inaxes != self.ax:
            self.clear_hover()
            return
            
        # Find bar under cursor
        for container in self.bar_containers:
            for bar in container:
                if bar.contains(event)[0]:
                    self.show_hover_info(bar, event)
                    return
                    
        self.clear_hover()
        
    def on_click(self, event):
        """Handle click events for bar selection."""
        if not self.config.enable_selection or event.inaxes != self.ax:
            return
            
        # Find clicked bar
        for container in self.bar_containers:
            for bar in container:
                if bar.contains(event)[0]:
                    self.handle_bar_selection(bar)
                    return
                    
    def show_hover_info(self, bar: Rectangle, event):
        """Show detailed information on hover."""
        if self.hover_annotation:
            self.hover_annotation.remove()
            
        # Get bar data
        x_val = bar.get_x() + bar.get_width() / 2
        y_val = bar.get_height()
        
        # Create annotation text
        text = f"Value: {y_val:.1f}"
        if hasattr(bar, 'get_label') and bar.get_label():
            text += f"\nSeries: {bar.get_label()}"
            
        self.hover_annotation = self.ax.annotate(
            text,
            xy=(x_val, y_val),
            xytext=(20, 20),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.5',
                fc=self.config.tooltip_bg,
                edgecolor=StyleManager.TEXT_MUTED,
                alpha=0.9
            ),
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color=StyleManager.TEXT_MUTED
            ),
            fontsize=9,
            color=StyleManager.TEXT_PRIMARY
        )
        
        self.canvas.draw_idle()
        
        # Emit hover signal
        self.bar_hovered.emit(str(x_val), y_val)
        
    def clear_hover(self):
        """Clear hover annotation."""
        if self.hover_annotation:
            self.hover_annotation.remove()
            self.hover_annotation = None
            self.canvas.draw_idle()
            
    def handle_bar_selection(self, bar: Rectangle):
        """Handle bar selection/deselection."""
        x_val = bar.get_x() + bar.get_width() / 2
        y_val = bar.get_height()
        
        # Toggle selection state
        if bar in self.selected_bars:
            self.selected_bars.remove(bar)
            bar.set_alpha(self.config.bar_alpha)
        else:
            self.selected_bars.append(bar)
            bar.set_alpha(1.0)
            
        self.canvas.draw_idle()
        
        # Emit click signal
        self.bar_clicked.emit(str(x_val), y_val)
        
    def animate_bars(self, duration: Optional[int] = None):
        """Animate bars growing from zero with smooth easing."""
        if not self.config.animate:
            return
            
        duration = duration or self.config.animation_duration
        
        # Store final heights for all bars
        final_data = []
        for container in self.bar_containers:
            heights = [bar.get_height() for bar in container]
            final_data.append(heights)
            # Set all bars to zero height initially
            for bar in container:
                bar.set_height(0)
                
        # Animation function
        def animate_frame(frame):
            progress = frame / (duration / 16.67)  # Assuming ~60fps
            progress = min(1.0, progress)
            
            # Ease-out cubic function for smooth animation
            eased_progress = 1 - (1 - progress) ** 3
            
            for i, container in enumerate(self.bar_containers):
                for j, bar in enumerate(container):
                    if j < len(final_data[i]):
                        target_height = final_data[i][j]
                        current_height = target_height * eased_progress
                        bar.set_height(current_height)
                        
            # Update y-axis limits during animation
            if self.ax:
                max_height = max([max(heights) if heights else 0 for heights in final_data])
                if max_height > 0:
                    self.ax.set_ylim(0, max_height * 1.1)
                    
            return [bar for container in self.bar_containers for bar in container]
            
        # Create and start animation
        frames = int(duration / 16.67)  # Convert ms to frames
        self.animation = FuncAnimation(
            self.figure,
            animate_frame,
            frames=frames,
            interval=16.67,  # ~60fps
            blit=False,
            repeat=False
        )
        
    def export_chart(self, filename: str, dpi: int = 300, format: str = 'png'):
        """Export chart to file with high quality."""
        self.figure.savefig(
            filename,
            dpi=dpi,
            format=format,
            bbox_inches='tight',
            facecolor=StyleManager.SECONDARY_BG,
            edgecolor='none',
            transparent=False
        )
        
    def update_config(self, new_config: BarChartConfig):
        """Update chart configuration and refresh."""
        self.config = new_config
        if self.data is not None:
            self.plot(self.data, self.chart_type)


class InteractiveBarChart(BarChart):
    """Enhanced bar chart with advanced interactive features."""
    
    def __init__(self, config: Optional[BarChartConfig] = None, parent=None):
        super().__init__(config, parent)
        
        # Additional interactive elements
        self.control_panel = self.create_control_panel()
        
    def create_control_panel(self):
        """Create control panel for chart interactions."""
        panel = QWidget(self)
        layout = QHBoxLayout()
        
        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.setStyleSheet(self.style_manager.get_button_style("secondary"))
        export_btn.clicked.connect(self.show_export_dialog)
        
        # Animation toggle
        animate_btn = QPushButton("Toggle Animation")
        animate_btn.setStyleSheet(self.style_manager.get_button_style("secondary"))
        animate_btn.clicked.connect(self.toggle_animation)
        
        layout.addWidget(export_btn)
        layout.addWidget(animate_btn)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
        
    def show_export_dialog(self):
        """Show export dialog (placeholder for now)."""
        # TODO: Implement export dialog
        self.export_chart("chart_export.png")
        
    def toggle_animation(self):
        """Toggle animation on/off."""
        self.config.animate = not self.config.animate
        if self.data is not None:
            self.plot(self.data, self.chart_type)