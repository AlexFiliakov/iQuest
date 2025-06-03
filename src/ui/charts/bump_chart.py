"""
Bump chart component for ranking changes over time.

Shows smooth line transitions for metric rankings with Wall Street Journal styling.
Perfect for visualizing performance relative to other metrics or benchmarks.
"""

from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.collections import LineCollection

from ..style_manager import StyleManager


class BumpChartWidget(QWidget):
    """
    Professional bump chart widget with WSJ-inspired styling.
    
    Features:
    - Smooth line transitions
    - Interactive metric toggling
    - Ranking highlights
    - Position change indicators
    - Clean, minimalist design
    """
    
    metric_clicked = pyqtSignal(str)  # metric_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.style_manager = StyleManager()
        
        # Chart data
        self.metrics = []
        self.dates = []
        self.rankings = {}
        self.values = {}
        self.title = ""
        self.visible_metrics = set()
        
        # Visual properties
        self.wsj_colors = {
            'primary': '#2E86AB',    # Professional blue
            'secondary': '#A23B72',  # Deep magenta
            'tertiary': '#F18F01',   # Warm orange
            'quaternary': '#C73E1D', # WSJ red
            'background': '#FAFAFA',
            'grid': '#E8E8E8',
            'text': '#2C3E50',
            'highlight': '#FFE066'
        }
        
        self.color_palette = [
            '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', 
            '#50C878', '#6A4C93', '#FF6B6B', '#4ECDC4',
            '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'
        ]
        
        self.font_family = 'Arial, sans-serif'
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
        
        # Controls panel
        controls_layout = QHBoxLayout()
        self.controls_frame = QFrame(self)
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
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor=self.wsj_colors['background'])
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
        self.ax.grid(True, linestyle='-', alpha=0.3, color=self.wsj_colors['grid'], axis='y')
        self.ax.set_axisbelow(True)
        
        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.wsj_colors['grid'])
        self.ax.spines['bottom'].set_color(self.wsj_colors['grid'])
        
        # Configure ticks
        self.ax.tick_params(colors=self.wsj_colors['text'], which='both')
    
    def set_data(self, 
                 metrics: List[str],
                 dates: List[str],
                 rankings: Dict[str, List[int]],
                 values: Dict[str, List[float]],
                 title: str = ""):
        """Set chart data and refresh visualization."""
        self.metrics = metrics
        self.dates = dates
        self.rankings = rankings
        self.values = values
        self.title = title
        self.visible_metrics = set(metrics)  # Show all by default
        
        self.title_label.setText(title)
        self._create_controls()
        self._render_chart()
    
    def _create_controls(self):
        """Create metric toggle controls."""
        # Clear existing controls
        layout = self.controls_frame.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        
        # Add metric checkboxes
        for i, metric in enumerate(self.metrics):
            checkbox = QCheckBox(metric)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {self.color_palette[i % len(self.color_palette)]};
                    font-weight: bold;
                    margin: 2px 8px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {self.color_palette[i % len(self.color_palette)]};
                }}
            """)
            checkbox.toggled.connect(lambda checked, m=metric: self._toggle_metric(m, checked))
            layout.addWidget(checkbox)
        
        layout.addStretch()
    
    def _toggle_metric(self, metric: str, visible: bool):
        """Toggle metric visibility."""
        if visible:
            self.visible_metrics.add(metric)
        else:
            self.visible_metrics.discard(metric)
        self._render_chart()
    
    def _render_chart(self):
        """Render the bump chart with WSJ styling."""
        if not self.metrics or not self.dates or not self.rankings:
            return
        
        self.ax.clear()
        self._setup_matplotlib_style()
        
        # Prepare data
        x_positions = np.arange(len(self.dates))
        max_rank = max(max(ranks) for ranks in self.rankings.values() if ranks)
        
        # Plot lines for each visible metric
        for i, metric in enumerate(self.metrics):
            if metric not in self.visible_metrics or metric not in self.rankings:
                continue
            
            ranks = self.rankings[metric]
            if not ranks:
                continue
            
            color = self.color_palette[i % len(self.color_palette)]
            
            # Main line
            line = self.ax.plot(x_positions, ranks, 
                              color=color, linewidth=3, alpha=0.8,
                              marker='o', markersize=6, markerfacecolor=color,
                              markeredgecolor='white', markeredgewidth=2,
                              label=metric, zorder=10-i)
            
            # Add position change indicators
            for j in range(1, len(ranks)):
                prev_rank = ranks[j-1]
                curr_rank = ranks[j]
                
                if curr_rank < prev_rank:  # Improvement (lower rank number)
                    # Add up arrow
                    self.ax.annotate('▲', xy=(x_positions[j], curr_rank),
                                   xytext=(0, -10), textcoords='offset points',
                                   ha='center', va='top', color=color,
                                   fontsize=12, alpha=0.7)
                elif curr_rank > prev_rank:  # Decline (higher rank number)
                    # Add down arrow
                    self.ax.annotate('▼', xy=(x_positions[j], curr_rank),
                                   xytext=(0, 10), textcoords='offset points',
                                   ha='center', va='bottom', color=color,
                                   fontsize=12, alpha=0.7)
            
            # Add rank labels at start and end
            if len(ranks) > 0:
                start_rank = ranks[0]
                end_rank = ranks[-1]
                
                # Start label
                self.ax.text(x_positions[0] - 0.1, start_rank, f'{start_rank}',
                           ha='right', va='center', color=color, weight='bold',
                           fontsize=10, bbox=dict(boxstyle='round,pad=0.2',
                                                 facecolor='white', alpha=0.8))
                
                # End label
                self.ax.text(x_positions[-1] + 0.1, end_rank, f'{end_rank}',
                           ha='left', va='center', color=color, weight='bold',
                           fontsize=10, bbox=dict(boxstyle='round,pad=0.2',
                                                 facecolor='white', alpha=0.8))
        
        # Customize chart
        self.ax.set_xticks(x_positions)
        self.ax.set_xticklabels(self.dates, rotation=45, ha='right', fontsize=9)
        self.ax.set_ylabel('Rank Position', fontsize=11, color=self.wsj_colors['text'],
                          fontfamily=self.font_family)
        
        # Invert y-axis (rank 1 at top)
        self.ax.invert_yaxis()
        
        # Set y-axis limits
        self.ax.set_ylim(max_rank + 0.5, 0.5)
        
        # Set y-axis ticks to integers
        y_ticks = range(1, max_rank + 1)
        self.ax.set_yticks(y_ticks)
        
        # Add legend
        if len(self.visible_metrics) > 1:
            legend = self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5),
                                  frameon=True, fancybox=True, shadow=False,
                                  fontsize=9)
            legend.get_frame().set_facecolor('#FFFFFF')
            legend.get_frame().set_alpha(0.9)
        
        # Add rank zone backgrounds
        for rank in range(1, max_rank + 1):
            alpha = 0.1 if rank % 2 == 0 else 0.05
            color = '#4CAF50' if rank <= 3 else '#FFC107' if rank <= max_rank//2 else '#FF5722'
            self.ax.axhspan(rank - 0.5, rank + 0.5, alpha=alpha, color=color, zorder=0)
        
        # Tight layout
        self.figure.tight_layout(pad=2.0)
        
        # Refresh canvas
        self.canvas.draw()
    
    def add_annotations(self, annotations: Dict[str, Dict[str, str]]):
        """Add annotations for specific metrics at specific dates."""
        if not hasattr(self, 'ax') or not self.dates:
            return
        
        for metric, date_annotations in annotations.items():
            if metric not in self.rankings:
                continue
                
            for date_str, text in date_annotations.items():
                if date_str in self.dates:
                    date_idx = self.dates.index(date_str)
                    rank = self.rankings[metric][date_idx]
                    
                    self.ax.annotate(text, xy=(date_idx, rank),
                                   xytext=(10, -10), textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.3',
                                           facecolor=self.wsj_colors['highlight'],
                                           alpha=0.8),
                                   arrowprops=dict(arrowstyle='->',
                                                 connectionstyle='arc3,rad=0.1'),
                                   fontsize=8, ha='left')
        
        self.canvas.draw()
    
    def highlight_periods(self, periods: List[Tuple[str, str, str]]):
        """Highlight specific time periods with background colors."""
        for start_date, end_date, color in periods:
            try:
                start_idx = self.dates.index(start_date)
                end_idx = self.dates.index(end_date)
                
                self.ax.axvspan(start_idx, end_idx, alpha=0.2, color=color, zorder=0)
            except ValueError:
                continue  # Skip if dates not found
        
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
            'metrics': self.metrics,
            'dates': self.dates,
            'rankings': self.rankings,
            'values': self.values,
            'title': self.title,
            'visible_metrics': list(self.visible_metrics)
        }


class BumpChartContainer(QFrame):
    """
    Complete bump chart container with controls and metadata.
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
        self.chart = BumpChartWidget()
        layout.addWidget(self.chart)
        
        # Summary panel
        summary_layout = QHBoxLayout()
        
        self.summary_label = QLabel(self)
        self.summary_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        summary_layout.addWidget(self.summary_label)
        
        summary_layout.addStretch()
        
        layout.addLayout(summary_layout)
    
    def set_chart_data(self, metrics, dates, rankings, values, title=""):
        """Set chart data and update summary."""
        self.chart.set_data(metrics, dates, rankings, values, title)
        
        # Calculate summary statistics
        position_changes = {}
        for metric in metrics:
            if metric in rankings and len(rankings[metric]) >= 2:
                start_rank = rankings[metric][0]
                end_rank = rankings[metric][-1]
                position_changes[metric] = end_rank - start_rank
        
        # Find biggest mover
        if position_changes:
            biggest_improvement = min(position_changes.items(), key=lambda x: x[1])
            biggest_decline = max(position_changes.items(), key=lambda x: x[1])
            
            summary_parts = []
            if biggest_improvement[1] < 0:
                summary_parts.append(f"Biggest improvement: {biggest_improvement[0]} ({biggest_improvement[1]:+d} positions)")
            if biggest_decline[1] > 0:
                summary_parts.append(f"Biggest decline: {biggest_decline[0]} ({biggest_decline[1]:+d} positions)")
            
            summary_text = " | ".join(summary_parts) if summary_parts else "No significant position changes"
        else:
            summary_text = "Insufficient data for position analysis"
        
        self.summary_label.setText(summary_text)