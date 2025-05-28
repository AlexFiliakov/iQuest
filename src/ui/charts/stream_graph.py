"""
Stream graph component for composition visualization over time.

Shows stacked area charts with smooth curves and flowing aesthetics.
Perfect for showing how different components contribute to the whole.
"""

from typing import List, Dict, Optional, Any
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import PolyCollection
import matplotlib.patches as patches
from scipy.interpolate import make_interp_spline

from ..style_manager import StyleManager


class StreamGraphWidget(QWidget):
    """
    Professional stream graph widget with flowing aesthetics.
    
    Features:
    - Smooth interpolated curves
    - Interactive layer toggling
    - Baseline positioning options
    - WSJ-inspired color palette
    - Responsive design
    """
    
    layer_clicked = pyqtSignal(str)  # category_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.style_manager = StyleManager()
        
        # Chart data
        self.categories = []
        self.dates = []
        self.values = {}
        self.baseline = []
        self.title = ""
        self.visible_categories = set()
        
        # Visual properties
        self.wsj_colors = [
            '#2E86AB',  # Professional blue
            '#A23B72',  # Deep magenta
            '#F18F01',  # Warm orange
            '#C73E1D',  # WSJ red
            '#50C878',  # Emerald green
            '#6A4C93',  # Purple
            '#FF6B6B',  # Coral
            '#4ECDC4',  # Turquoise
            '#45B7D1',  # Sky blue
            '#96CEB4',  # Mint
            '#FFEAA7',  # Light yellow
            '#DDA0DD'   # Plum
        ]
        
        self.background_color = '#FAFAFA'
        self.grid_color = '#E8E8E8'
        self.text_color = '#2C3E50'
        self.font_family = 'Arial, sans-serif'
        
        self._setup_ui()
        self._setup_matplotlib_style()
    
    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(self.font_family, 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {self.text_color}; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # Controls panel
        controls_layout = QHBoxLayout()
        self.controls_frame = QFrame()
        self.controls_frame.setLayout(controls_layout)
        self.controls_frame.setStyleSheet("""
            QFrame { 
                background-color: #F8F9FA; 
                border: 1px solid #E9ECEF; 
                border-radius: 4px; 
                padding: 5px; 
                margin: 5px 0; 
            }
        """)
        layout.addWidget(self.controls_frame)
        
        # Chart canvas
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor=self.background_color)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(self.canvas.sizePolicy().Expanding, self.canvas.sizePolicy().Expanding)
        layout.addWidget(self.canvas)
        
        # Chart axis
        self.ax = self.figure.add_subplot(111)
    
    def _setup_matplotlib_style(self):
        """Configure matplotlib for WSJ-style charts."""
        plt.style.use('default')
        
        # Set figure background
        self.figure.patch.set_facecolor(self.background_color)
        
        # Configure axis
        self.ax.set_facecolor(self.background_color)
        self.ax.grid(True, linestyle='-', alpha=0.3, color=self.grid_color, axis='y')
        self.ax.set_axisbelow(True)
        
        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.grid_color)
        self.ax.spines['bottom'].set_color(self.grid_color)
        
        # Configure ticks
        self.ax.tick_params(colors=self.text_color, which='both')
    
    def set_data(self, 
                 categories: List[str],
                 dates: List[str],
                 values: Dict[str, List[float]],
                 baseline: List[float],
                 title: str = ""):
        """Set chart data and refresh visualization."""
        self.categories = categories
        self.dates = dates
        self.values = values
        self.baseline = baseline
        self.title = title
        self.visible_categories = set(categories)  # Show all by default
        
        self.title_label.setText(title)
        self._create_controls()
        self._render_chart()
    
    def _create_controls(self):
        """Create category toggle controls."""
        # Clear existing controls
        layout = self.controls_frame.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        
        # Add category checkboxes
        for i, category in enumerate(self.categories):
            checkbox = QCheckBox(category)
            checkbox.setChecked(True)
            color = self.wsj_colors[i % len(self.wsj_colors)]
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {color};
                    font-weight: bold;
                    margin: 2px 8px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {color};
                }}
            """)
            checkbox.toggled.connect(lambda checked, c=category: self._toggle_category(c, checked))
            layout.addWidget(checkbox)
        
        layout.addStretch()
    
    def _toggle_category(self, category: str, visible: bool):
        """Toggle category visibility."""
        if visible:
            self.visible_categories.add(category)
        else:
            self.visible_categories.discard(category)
        self._render_chart()
    
    def _render_chart(self):
        """Render the stream graph with smooth curves."""
        if not self.categories or not self.dates or not self.values:
            return
        
        self.ax.clear()
        self._setup_matplotlib_style()
        
        # Prepare data
        x_positions = np.arange(len(self.dates))
        
        # Filter visible categories
        visible_cats = [cat for cat in self.categories if cat in self.visible_categories]
        if not visible_cats:
            return
        
        # Prepare stacked data
        y_stack = np.zeros(len(self.dates))
        polygons = []
        colors = []
        labels = []
        
        for i, category in enumerate(visible_cats):
            if category not in self.values or not self.values[category]:
                continue
            
            y_values = np.array(self.values[category])
            
            # Create smooth curves using spline interpolation
            if len(x_positions) > 3:
                try:
                    # Smooth interpolation
                    x_smooth = np.linspace(x_positions.min(), x_positions.max(), len(x_positions) * 3)
                    
                    # Interpolate bottom curve
                    spl_bottom = make_interp_spline(x_positions, y_stack, k=min(3, len(x_positions)-1))
                    y_bottom_smooth = spl_bottom(x_smooth)
                    
                    # Interpolate top curve
                    y_top = y_stack + y_values
                    spl_top = make_interp_spline(x_positions, y_top, k=min(3, len(x_positions)-1))
                    y_top_smooth = spl_top(x_smooth)
                    
                    # Create polygon vertices
                    vertices = []
                    
                    # Bottom curve (left to right)
                    for x, y in zip(x_smooth, y_bottom_smooth):
                        vertices.append([x, y])
                    
                    # Top curve (right to left)
                    for x, y in zip(reversed(x_smooth), reversed(y_top_smooth)):
                        vertices.append([x, y])
                    
                    polygons.append(vertices)
                    
                except:
                    # Fallback to simple polygon
                    vertices = []
                    for x, y in zip(x_positions, y_stack):
                        vertices.append([x, y])
                    for x, y in zip(reversed(x_positions), reversed(y_stack + y_values)):
                        vertices.append([x, y])
                    polygons.append(vertices)
            else:
                # Simple polygon for small datasets
                vertices = []
                for x, y in zip(x_positions, y_stack):
                    vertices.append([x, y])
                for x, y in zip(reversed(x_positions), reversed(y_stack + y_values)):
                    vertices.append([x, y])
                polygons.append(vertices)
            
            # Color and label
            colors.append(self.wsj_colors[i % len(self.wsj_colors)])
            labels.append(category)
            
            # Update stack
            y_stack += y_values
        
        # Create polygon collection
        poly_collection = PolyCollection(polygons, 
                                       facecolors=colors, 
                                       alpha=0.7,
                                       edgecolors='white',
                                       linewidths=0.5)
        self.ax.add_collection(poly_collection)
        
        # Add center lines for each stream
        y_stack = np.zeros(len(self.dates))
        for i, category in enumerate(visible_cats):
            if category not in self.values:
                continue
            
            y_values = np.array(self.values[category])
            y_center = y_stack + y_values / 2
            
            color = self.wsj_colors[i % len(self.wsj_colors)]
            self.ax.plot(x_positions, y_center, color=color, linewidth=2, alpha=0.8)
            
            # Add category labels at the end
            if len(y_center) > 0:
                self.ax.text(x_positions[-1] + 0.1, y_center[-1], category,
                           ha='left', va='center', color=color, weight='bold',
                           fontsize=9, 
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
            
            y_stack += y_values
        
        # Customize chart
        self.ax.set_xticks(x_positions)
        self.ax.set_xticklabels(self.dates, rotation=45, ha='right', fontsize=9)
        self.ax.set_ylabel('Percentage', fontsize=11, color=self.text_color,
                          fontfamily=self.font_family)
        
        # Set limits
        self.ax.set_xlim(x_positions[0] - 0.5, x_positions[-1] + 0.5)
        if len(polygons) > 0:
            max_y = np.max([np.max([p[1] for p in poly]) for poly in polygons])
            self.ax.set_ylim(0, max_y * 1.05)
        
        # Format y-axis as percentage
        self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # Add subtle background shading
        for i in range(0, len(x_positions), 2):
            end_x = min(i + 1, len(x_positions) - 1)
            self.ax.axvspan(i - 0.5, end_x + 0.5, alpha=0.05, color='gray', zorder=0)
        
        # Tight layout
        self.figure.tight_layout(pad=2.0)
        
        # Refresh canvas
        self.canvas.draw()
    
    def add_annotations(self, annotations: Dict[str, Dict[str, str]]):
        """Add annotations for specific categories at specific dates."""
        if not hasattr(self, 'ax') or not self.dates:
            return
        
        for category, date_annotations in annotations.items():
            if category not in self.values:
                continue
                
            for date_str, text in date_annotations.items():
                if date_str in self.dates:
                    date_idx = self.dates.index(date_str)
                    
                    # Find y position for this category
                    y_stack = 0
                    for cat in self.categories:
                        if cat == category:
                            y_pos = y_stack + self.values[cat][date_idx] / 2
                            break
                        if cat in self.values:
                            y_stack += self.values[cat][date_idx]
                    else:
                        continue
                    
                    self.ax.annotate(text, xy=(date_idx, y_pos),
                                   xytext=(10, 10), textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.3',
                                           facecolor='#FFE066',
                                           alpha=0.8),
                                   arrowprops=dict(arrowstyle='->',
                                                 connectionstyle='arc3,rad=0.1'),
                                   fontsize=8, ha='left')
        
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
        return {
            'categories': self.categories,
            'dates': self.dates,
            'values': self.values,
            'baseline': self.baseline,
            'title': self.title,
            'visible_categories': list(self.visible_categories)
        }


class StreamGraphContainer(QFrame):
    """
    Complete stream graph container with controls and metadata.
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
        self.chart = StreamGraphWidget()
        layout.addWidget(self.chart)
        
        # Summary panel
        summary_layout = QHBoxLayout()
        
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        summary_layout.addWidget(self.summary_label)
        
        summary_layout.addStretch()
        
        layout.addLayout(summary_layout)
    
    def set_chart_data(self, categories, dates, values, baseline, title=""):
        """Set chart data and update summary."""
        self.chart.set_data(categories, dates, values, baseline, title)
        
        # Calculate summary statistics
        if values and dates:
            # Find dominant category
            category_totals = {}
            for category in categories:
                if category in values:
                    category_totals[category] = sum(values[category])
            
            if category_totals:
                dominant_category = max(category_totals.items(), key=lambda x: x[1])
                dominant_pct = (dominant_category[1] / sum(category_totals.values())) * 100
                
                summary_text = (f"Dominant category: {dominant_category[0]} "
                              f"({dominant_pct:.1f}% of total)")
            else:
                summary_text = "No data available for analysis"
        else:
            summary_text = "Insufficient data for composition analysis"
        
        self.summary_label.setText(summary_text)