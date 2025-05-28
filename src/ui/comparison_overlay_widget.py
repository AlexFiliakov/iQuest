"""
Comparison Overlay Widget for Daily Analytics

Provides interactive overlay visualization with ghost lines, confidence bands,
and interactive legends in the style of Wall Street Journal charts.
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QLabel, QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from ..analytics.comparison_overlay_calculator import OverlayData, ComparisonOverlayCalculator
import logging

logger = logging.getLogger(__name__)


class InteractiveLegend(QWidget):
    """Interactive legend widget for toggling overlays."""
    
    overlay_toggled = pyqtSignal(str, bool)  # overlay_type, visible
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay_items = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the legend UI."""
        self.setFixedWidth(250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Comparison Overlays")
        title.setFont(QFont("Poppins", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Scroll area for overlay items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F5F5F5;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #FF8C42;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(6)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.show_all_btn = QPushButton("Show All")
        self.hide_all_btn = QPushButton("Hide All")
        
        for btn in [self.show_all_btn, self.hide_all_btn]:
            btn.setFont(QFont("Inter", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background: #FF8C42;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #E07B3A;
                }
                QPushButton:pressed {
                    background: #CC6D32;
                }
            """)
            
        button_layout.addWidget(self.show_all_btn)
        button_layout.addWidget(self.hide_all_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.show_all_btn.clicked.connect(self.show_all_overlays)
        self.hide_all_btn.clicked.connect(self.hide_all_overlays)
        
    def add_overlay_item(self, overlay_type: str, overlay_data: OverlayData, color: str):
        """Add an overlay item to the legend."""
        if overlay_type in self.overlay_items:
            return
            
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #FF8C42;
                background: #FFF8F4;
            }
        """)
        
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(8, 8, 8, 8)
        item_layout.setSpacing(8)
        
        # Checkbox for toggle
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {color};
                border-radius: 3px;
                background: white;
            }}
            QCheckBox::indicator:checked {{
                background: {color};
            }}
            QCheckBox::indicator:checked:hover {{
                background: {color};
                border-color: {color};
            }}
        """)
        
        # Color indicator
        color_indicator = QLabel()
        color_indicator.setFixedSize(16, 3)
        color_indicator.setStyleSheet(f"background: {color}; border-radius: 1px;")
        
        # Label with overlay information
        label_text = self._format_overlay_label(overlay_type, overlay_data)
        label = QLabel(label_text)
        label.setFont(QFont("Inter", 10))
        label.setStyleSheet("color: #2C3E50;")
        label.setWordWrap(True)
        
        item_layout.addWidget(checkbox)
        item_layout.addWidget(color_indicator)
        item_layout.addWidget(label, 1)
        
        # Store reference
        self.overlay_items[overlay_type] = {
            'frame': item_frame,
            'checkbox': checkbox,
            'color': color,
            'data': overlay_data
        }
        
        # Connect checkbox signal
        checkbox.toggled.connect(lambda checked: self.overlay_toggled.emit(overlay_type, checked))
        
        self.content_layout.addWidget(item_frame)
        
    def remove_overlay_item(self, overlay_type: str):
        """Remove an overlay item from the legend."""
        if overlay_type in self.overlay_items:
            item = self.overlay_items[overlay_type]
            self.content_layout.removeWidget(item['frame'])
            item['frame'].deleteLater()
            del self.overlay_items[overlay_type]
            
    def show_all_overlays(self):
        """Show all overlay items."""
        for item in self.overlay_items.values():
            item['checkbox'].setChecked(True)
            
    def hide_all_overlays(self):
        """Hide all overlay items."""
        for item in self.overlay_items.values():
            item['checkbox'].setChecked(False)
            
    def _format_overlay_label(self, overlay_type: str, overlay_data: OverlayData) -> str:
        """Format the overlay label text."""
        metadata = overlay_data.metadata
        
        if overlay_type == "weekly_average":
            if 'mean' in metadata and metadata['mean'] is not None:
                return f"7-Day Average\n{metadata['mean']:.1f} avg"
            return "7-Day Average"
            
        elif overlay_type == "monthly_average":
            if 'mean' in metadata and metadata['mean'] is not None:
                return f"30-Day Average\n{metadata['mean']:.1f} avg"
            return "30-Day Average"
            
        elif overlay_type == "personal_best":
            if 'best_value' in metadata:
                days_since = metadata.get('days_since_best', 0)
                return f"Personal Best\n{metadata['best_value']:.1f} ({days_since}d ago)"
            return "Personal Best"
            
        elif overlay_type.startswith("historical_"):
            period = overlay_type.replace("historical_", "")
            if 'comparison_value' in metadata:
                return f"Last {period.title()}\n{metadata['comparison_value']:.1f}"
            return f"Last {period.title()}"
            
        return overlay_type.replace("_", " ").title()


class ComparisonOverlayWidget(QWidget):
    """Widget for managing and displaying comparison overlays on charts."""
    
    def __init__(self, chart_figure: Figure, chart_axes: Axes, parent=None):
        super().__init__(parent)
        self.figure = chart_figure
        self.axes = chart_axes
        self.overlays = {}
        self.overlay_lines = {}
        self.confidence_bands = {}
        self.calculator = ComparisonOverlayCalculator()
        
        # Color palette for overlays (WSJ-inspired)
        self.overlay_colors = {
            'weekly_average': '#4A90E2',      # Blue
            'monthly_average': '#7B68EE',     # Purple  
            'personal_best': '#FF6B6B',       # Red
            'historical_week': '#50C878',     # Green
            'historical_month': '#FF8C42',    # Orange
            'historical_year': '#9B59B6'      # Violet
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Interactive legend
        self.legend = InteractiveLegend()
        self.legend.overlay_toggled.connect(self.toggle_overlay)
        layout.addWidget(self.legend)
        
    def add_overlay(self, overlay_type: str, overlay_data: OverlayData):
        """Add a new overlay to the chart."""
        try:
            if overlay_data.values.empty or 'error' in overlay_data.metadata:
                logger.warning(f"Cannot add overlay {overlay_type}: {overlay_data.metadata.get('error', 'no data')}")
                return
                
            # Store overlay data
            self.overlays[overlay_type] = overlay_data
            
            # Get color for this overlay type
            color = self.overlay_colors.get(overlay_type, '#666666')
            
            # Add to legend
            self.legend.add_overlay_item(overlay_type, overlay_data, color)
            
            # Draw overlay on chart
            self._draw_overlay(overlay_type, overlay_data, color)
            
            # Refresh chart
            self.figure.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error adding overlay {overlay_type}: {e}")
            
    def remove_overlay(self, overlay_type: str):
        """Remove an overlay from the chart."""
        try:
            if overlay_type in self.overlays:
                # Remove from chart
                self._remove_overlay_from_chart(overlay_type)
                
                # Remove from data structures
                del self.overlays[overlay_type]
                
                # Remove from legend
                self.legend.remove_overlay_item(overlay_type)
                
                # Refresh chart
                self.figure.canvas.draw_idle()
                
        except Exception as e:
            logger.error(f"Error removing overlay {overlay_type}: {e}")
            
    def toggle_overlay(self, overlay_type: str, visible: bool):
        """Toggle overlay visibility."""
        try:
            if overlay_type in self.overlay_lines:
                line = self.overlay_lines[overlay_type]
                line.set_visible(visible)
                
            if overlay_type in self.confidence_bands:
                band = self.confidence_bands[overlay_type]
                band.set_visible(visible)
                
            # Refresh chart
            self.figure.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error toggling overlay {overlay_type}: {e}")
            
    def _draw_overlay(self, overlay_type: str, overlay_data: OverlayData, color: str):
        """Draw an overlay on the chart."""
        try:
            # Remove existing overlay if present
            self._remove_overlay_from_chart(overlay_type)
            
            values = overlay_data.values
            if len(values) == 0:
                return
                
            # Determine line style based on overlay type
            if overlay_type == "personal_best":
                linestyle = '-'
                alpha = 0.8
                linewidth = 2
            else:
                linestyle = '--'
                alpha = 0.6
                linewidth = 1.5
                
            # Draw main overlay line
            line = self.axes.plot(
                values.index, 
                values.values,
                color=color,
                linestyle=linestyle,
                alpha=alpha,
                linewidth=linewidth,
                label=overlay_type.replace('_', ' ').title(),
                zorder=5
            )[0]
            
            self.overlay_lines[overlay_type] = line
            
            # Draw confidence bands if available
            if overlay_data.confidence_upper is not None and overlay_data.confidence_lower is not None:
                self._draw_confidence_band(
                    overlay_type,
                    overlay_data.confidence_upper,
                    overlay_data.confidence_lower,
                    color
                )
                
        except Exception as e:
            logger.error(f"Error drawing overlay {overlay_type}: {e}")
            
    def _draw_confidence_band(self, overlay_type: str, upper: pd.Series, lower: pd.Series, color: str):
        """Draw confidence band for an overlay."""
        try:
            # Create filled area between upper and lower bounds
            band = self.axes.fill_between(
                upper.index,
                lower.values,
                upper.values,
                color=color,
                alpha=0.15,
                zorder=1,
                label=f"{overlay_type} confidence"
            )
            
            self.confidence_bands[overlay_type] = band
            
        except Exception as e:
            logger.error(f"Error drawing confidence band for {overlay_type}: {e}")
            
    def _remove_overlay_from_chart(self, overlay_type: str):
        """Remove overlay elements from the chart."""
        try:
            # Remove main line
            if overlay_type in self.overlay_lines:
                line = self.overlay_lines[overlay_type]
                if line in self.axes.lines:
                    line.remove()
                del self.overlay_lines[overlay_type]
                
            # Remove confidence band
            if overlay_type in self.confidence_bands:
                band = self.confidence_bands[overlay_type]
                if band in self.axes.collections:
                    band.remove()
                del self.confidence_bands[overlay_type]
                
        except Exception as e:
            logger.error(f"Error removing overlay {overlay_type} from chart: {e}")
            
    def clear_all_overlays(self):
        """Clear all overlays from the chart."""
        for overlay_type in list(self.overlays.keys()):
            self.remove_overlay(overlay_type)
            
    def add_weekly_average_overlay(self, data: pd.Series, current_date):
        """Add weekly average overlay."""
        overlay_data = self.calculator.calculate_weekly_average(data, current_date)
        self.add_overlay("weekly_average", overlay_data)
        
    def add_monthly_average_overlay(self, data: pd.Series, current_date):
        """Add monthly average overlay."""
        overlay_data = self.calculator.calculate_monthly_average(data, current_date)
        self.add_overlay("monthly_average", overlay_data)
        
    def add_personal_best_overlay(self, data: pd.Series, metric_type: str, higher_is_better: bool = True):
        """Add personal best overlay."""
        overlay_data = self.calculator.calculate_personal_best(data, metric_type, higher_is_better)
        self.add_overlay("personal_best", overlay_data)
        
    def add_historical_comparison_overlays(self, data: pd.Series, current_date, periods: List[str] = None):
        """Add historical comparison overlays."""
        comparisons = self.calculator.calculate_historical_comparison(data, current_date, periods)
        
        for period_key, overlay_data in comparisons.items():
            overlay_type = f"historical_{period_key.replace('last_', '')}"
            self.add_overlay(overlay_type, overlay_data)
            
    def generate_context_message(self, metric: str, current_value: float, data: pd.Series) -> str:
        """Generate contextual message based on current overlays."""
        try:
            comparisons = {}
            
            # Extract comparison values from active overlays
            for overlay_type, overlay_data in self.overlays.items():
                if overlay_type == "weekly_average" and not overlay_data.values.empty:
                    comparisons['weekly_avg'] = overlay_data.values.iloc[-1]
                elif overlay_type == "monthly_average" and not overlay_data.values.empty:
                    comparisons['monthly_avg'] = overlay_data.values.iloc[-1]
                elif overlay_type == "personal_best" and not overlay_data.values.empty:
                    comparisons['personal_best'] = overlay_data.values.iloc[-1]
                elif overlay_type.startswith("historical_"):
                    period = overlay_type.replace("historical_", "")
                    if not overlay_data.values.empty:
                        comparisons[f'last_{period}'] = overlay_data.values.iloc[-1]
                        
            return self.calculator.generate_context_message(metric, current_value, comparisons)
            
        except Exception as e:
            logger.error(f"Error generating context message: {e}")
            return f"Today's {metric}: {current_value:.1f}"
            
    def update_chart_style(self):
        """Update chart styling to match WSJ aesthetic."""
        try:
            # Set background colors
            self.figure.patch.set_facecolor('#FAFAFA')
            self.axes.set_facecolor('white')
            
            # Remove top and right spines
            self.axes.spines['top'].set_visible(False)
            self.axes.spines['right'].set_visible(False)
            self.axes.spines['left'].set_color('#DDDDDD')
            self.axes.spines['bottom'].set_color('#DDDDDD')
            
            # Style grid
            self.axes.grid(True, linestyle='-', alpha=0.3, color='#DDDDDD', zorder=0)
            
            # Style tick labels
            self.axes.tick_params(colors='#666666', which='both')
            for label in self.axes.get_xticklabels() + self.axes.get_yticklabels():
                label.set_fontsize(10)
                label.set_color('#666666')
                
        except Exception as e:
            logger.error(f"Error updating chart style: {e}")