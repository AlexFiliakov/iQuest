"""
Waterfall chart component for month-over-month trend visualization.

Inspired by Wall Street Journal chart styling with clean, professional aesthetics.
Shows cumulative changes over time with clear visual indicators for positive/negative changes.
"""

from typing import List, Optional, Dict, Any
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QLinearGradient

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib import patheffects

from ..style_manager import StyleManager


class WaterfallChartWidget(QWidget):
    """
    Professional waterfall chart widget with WSJ-inspired styling.
    
    Features:
    - Clean, minimalist design
    - Animated transitions
    - Interactive hover details
    - Responsive layout
    - Customizable color schemes
    """
    
    data_point_clicked = pyqtSignal(str, float)  # category, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.style_manager = StyleManager()
        
        # Chart data
        self.categories = []
        self.values = []
        self.cumulative = []
        self.colors = []
        self.labels = []
        self.title = ""
        
        # Visual properties
        self.wsj_colors = {
            'positive': '#50C878',  # Emerald green
            'negative': '#E74C3C',  # WSJ red
            'neutral': '#3498DB',   # Professional blue
            'background': '#FAFAFA',
            'grid': '#E8E8E8',
            'text': '#2C3E50',
            'accent': '#F39C12'
        }
        
        self.font_family = 'Arial, sans-serif'
        self.animation_duration = 800
        
        self._setup_ui()
        self._setup_matplotlib_style()
    
    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel(self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(self.font_family, 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {self.wsj_colors['text']}; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # Chart canvas
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor=self.wsj_colors['background'])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(self.canvas.sizePolicy().Expanding, self.canvas.sizePolicy().Expanding)
        layout.addWidget(self.canvas)
        
        # Chart axis
        self.ax = self.figure.add_subplot(111)
    
    def _setup_matplotlib_style(self):
        """Configure matplotlib for WSJ-style charts."""
        plt.style.use('default')
        
        # Set figure background
        self.figure.patch.set_facecolor(self.wsj_colors['background'])
        
        # Configure axis
        self.ax.set_facecolor(self.wsj_colors['background'])
        self.ax.grid(True, linestyle='-', alpha=0.3, color=self.wsj_colors['grid'])
        self.ax.set_axisbelow(True)
        
        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.wsj_colors['grid'])
        self.ax.spines['bottom'].set_color(self.wsj_colors['grid'])
        
        # Configure ticks
        self.ax.tick_params(colors=self.wsj_colors['text'], which='both')
        self.ax.tick_params(axis='x', rotation=45)
    
    def set_data(self, 
                 categories: List[str],
                 values: List[float],
                 cumulative: List[float],
                 colors: List[str],
                 labels: List[str],
                 title: str = ""):
        """Set chart data and refresh visualization."""
        self.categories = categories
        self.values = values
        self.cumulative = cumulative
        self.colors = colors
        self.labels = labels
        self.title = title
        
        self.title_label.setText(title)
        self._render_chart()
    
    def _render_chart(self):
        """Render the waterfall chart with WSJ styling."""
        if not self.categories or not self.values:
            return
        
        self.ax.clear()
        self._setup_matplotlib_style()
        
        # Prepare data
        x_positions = np.arange(len(self.categories))
        bar_width = 0.6
        
        # Track cumulative position for waterfall effect
        running_total = 0
        bar_bottoms = []
        bar_heights = []
        bar_colors = []
        
        for i, (category, value, color) in enumerate(zip(self.categories, self.values, self.colors)):
            if i == 0 or 'Final' in category:
                # Starting or ending bars - start from zero
                bar_bottoms.append(0)
                bar_heights.append(value)
                running_total = value
            else:
                # Change bars - start from previous cumulative
                if value >= 0:
                    bar_bottoms.append(running_total)
                    bar_heights.append(value)
                else:
                    bar_bottoms.append(running_total + value)
                    bar_heights.append(abs(value))
                running_total += value
            
            # Map colors
            if color.startswith('#'):
                bar_colors.append(color)
            else:
                bar_colors.append(self.wsj_colors.get(color, self.wsj_colors['neutral']))
        
        # Create bars
        bars = self.ax.bar(x_positions, bar_heights, bar_width, 
                          bottom=bar_bottoms, color=bar_colors, 
                          alpha=0.8, edgecolor='white', linewidth=1)
        
        # Add connecting lines for waterfall effect
        for i in range(len(x_positions) - 1):
            if i > 0 and 'Final' not in self.categories[i+1]:  # Skip connection to final bar
                start_y = bar_bottoms[i] + bar_heights[i]
                end_y = bar_bottoms[i+1]
                
                self.ax.plot([x_positions[i] + bar_width/2, x_positions[i+1] - bar_width/2],
                           [start_y, end_y], 'k--', alpha=0.4, linewidth=1)
        
        # Add value labels on bars
        for i, (bar, label, height, bottom) in enumerate(zip(bars, self.labels, bar_heights, bar_bottoms)):
            label_y = bottom + height/2
            
            # Position label above or inside bar based on height
            if height > max(bar_heights) * 0.1:
                va = 'center'
                color = 'white'
                weight = 'bold'
            else:
                label_y = bottom + height + max(bar_heights) * 0.02
                va = 'bottom'
                color = self.wsj_colors['text']
                weight = 'normal'
            
            self.ax.text(x_positions[i], label_y, label, 
                        ha='center', va=va, color=color, weight=weight,
                        fontsize=9, fontfamily=self.font_family)
        
        # Customize chart
        self.ax.set_xticks(x_positions)
        self.ax.set_xticklabels(self.categories, rotation=45, ha='right', fontsize=9)
        self.ax.set_ylabel('Value', fontsize=11, color=self.wsj_colors['text'], 
                          fontfamily=self.font_family)
        
        # Set y-axis limits with padding
        y_min = min(0, min(bar_bottoms)) * 1.1
        y_max = max(self.cumulative) * 1.1
        self.ax.set_ylim(y_min, y_max)
        
        # Format y-axis labels
        self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        # Add subtle background gradient
        gradient = patches.Rectangle((x_positions[0] - 0.5, y_min), 
                                   len(x_positions), y_max - y_min,
                                   facecolor='none', edgecolor='none')
        self.ax.add_patch(gradient)
        
        # Tight layout
        self.figure.tight_layout(pad=2.0)
        
        # Refresh canvas
        self.canvas.draw()
    
    def add_annotations(self, annotations: Dict[str, str]):
        """Add text annotations to specific categories."""
        if not hasattr(self, 'ax') or not self.categories:
            return
        
        for category, text in annotations.items():
            if category in self.categories:
                idx = self.categories.index(category)
                x_pos = idx
                y_pos = max(self.cumulative) * 0.9
                
                self.ax.annotate(text, xy=(x_pos, y_pos), 
                               xytext=(10, 10), textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor=self.wsj_colors['accent'], 
                                       alpha=0.7),
                               arrowprops=dict(arrowstyle='->', 
                                             connectionstyle='arc3,rad=0'),
                               fontsize=8, color='white')
        
        self.canvas.draw()
    
    def export_chart(self, filepath: str, dpi: int = 300):
        """Export chart to file."""
        try:
            self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                              facecolor=self.wsj_colors['background'])
            return True
        except Exception as e:
            print(f"Failed to export chart: {e}")
            return False
    
    def get_chart_data(self) -> Dict[str, Any]:
        """Get chart data for external use."""
        return {
            'categories': self.categories,
            'values': self.values,
            'cumulative': self.cumulative,
            'colors': self.colors,
            'labels': self.labels,
            'title': self.title
        }


class WaterfallChartContainer(QFrame):
    """
    Complete waterfall chart container with controls and metadata.
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
        self.chart = WaterfallChartWidget()
        layout.addWidget(self.chart)
        
        # Metadata panel
        metadata_layout = QHBoxLayout()
        
        self.summary_label = QLabel(self)
        self.summary_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        metadata_layout.addWidget(self.summary_label)
        
        metadata_layout.addStretch()
        
        layout.addLayout(metadata_layout)
    
    def set_chart_data(self, categories, values, cumulative, colors, labels, title=""):
        """Set chart data and update summary."""
        self.chart.set_data(categories, values, cumulative, colors, labels, title)
        
        # Update summary
        total_change = cumulative[-1] - cumulative[0] if len(cumulative) >= 2 else 0
        change_pct = (total_change / cumulative[0] * 100) if cumulative and cumulative[0] != 0 else 0
        periods = len([v for v in values if v != 0]) - 2  # Exclude start and end
        
        summary_text = (f"Total Change: {total_change:+.1f} ({change_pct:+.1f}%) "
                       f"over {periods} periods")
        self.summary_label.setText(summary_text)