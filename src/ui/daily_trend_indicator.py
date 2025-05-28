"""Daily trend indicator widget with animated arrows and sparklines."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolTip
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QFont, QFontMetrics, QPainterPath
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TrendData:
    """Container for trend indicator data."""
    current_value: float
    previous_value: Optional[float]
    change_absolute: Optional[float]
    change_percent: Optional[float]
    history: List[float]  # Last 7 days
    dates: List[datetime]
    unit: str
    metric_name: str


class ArrowIndicator(QWidget):
    """Animated arrow indicator for trend direction."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._rotation = 0
        self._color = QColor("#8B7355")  # Default neutral color
        self._pulse_opacity = 0.0
        
        # Animation for rotation
        self.rotation_anim = QPropertyAnimation(self, b"rotation")
        self.rotation_anim.setDuration(500)
        self.rotation_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Animation for pulse effect
        self.pulse_anim = QPropertyAnimation(self, b"pulseOpacity")
        self.pulse_anim.setDuration(1000)
        self.pulse_anim.setLoopCount(-1)  # Infinite loop
        
    @pyqtProperty(float)
    def rotation(self):
        return self._rotation
        
    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.update()
        
    @pyqtProperty(float)
    def pulseOpacity(self):
        return self._pulse_opacity
        
    @pulseOpacity.setter
    def pulseOpacity(self, value):
        self._pulse_opacity = value
        self.update()
        
    def set_trend(self, change_percent: Optional[float]):
        """Update arrow based on trend percentage."""
        if change_percent is None:
            # Neutral position
            target_rotation = 0
            self._color = QColor("#8B7355")
            self.pulse_anim.stop()
            self._pulse_opacity = 0.0
        else:
            # Calculate rotation: -90 for decrease, 90 for increase
            if abs(change_percent) < 0.1:  # Less than 0.1% is neutral
                target_rotation = 0
                self._color = QColor("#8B7355")
            elif change_percent > 0:
                # Positive change - arrow up
                target_rotation = 90
                if change_percent > 10:
                    self._color = QColor("#95C17B")  # Green for >10%
                else:
                    self._color = QColor("#FFD166")  # Yellow for <10%
            else:
                # Negative change - arrow down
                target_rotation = -90
                if abs(change_percent) > 10:
                    self._color = QColor("#E76F51")  # Red for >10% decrease
                else:
                    self._color = QColor("#F4A261")  # Amber for <10% decrease
                    
            # Start pulse animation for significant changes
            if abs(change_percent) > 20:
                self.pulse_anim.setStartValue(0.0)
                self.pulse_anim.setEndValue(0.5)
                self.pulse_anim.start()
            else:
                self.pulse_anim.stop()
                self._pulse_opacity = 0.0
                
        # Animate rotation
        self.rotation_anim.setStartValue(self._rotation)
        self.rotation_anim.setEndValue(target_rotation)
        self.rotation_anim.start()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw pulse effect if active
        if self._pulse_opacity > 0:
            pulse_color = QColor(self._color)
            pulse_color.setAlphaF(self._pulse_opacity)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pulse_color))
            painter.drawEllipse(self.rect())
        
        # Setup for arrow
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        
        # Draw arrow
        arrow_size = 15
        arrow = QPolygonF([
            QPointF(0, -arrow_size),  # Top point
            QPointF(-arrow_size * 0.5, arrow_size * 0.3),  # Left base
            QPointF(-arrow_size * 0.2, arrow_size * 0.3),  # Left indent
            QPointF(-arrow_size * 0.2, arrow_size),  # Left tail
            QPointF(arrow_size * 0.2, arrow_size),  # Right tail
            QPointF(arrow_size * 0.2, arrow_size * 0.3),  # Right indent
            QPointF(arrow_size * 0.5, arrow_size * 0.3),  # Right base
        ])
        
        painter.setPen(QPen(self._color.darker(120), 2))
        painter.setBrush(QBrush(self._color))
        painter.drawPolygon(arrow)


class SparklineWidget(FigureCanvas):
    """Mini chart showing 7-day trend."""
    
    def __init__(self, parent=None):
        # Create figure with minimal margins
        self.figure = Figure(figsize=(2, 0.8), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)
        self.setStyleSheet("background-color: transparent;")
        
    def update_data(self, values: List[float], highlight_last: bool = True):
        """Update sparkline with new data."""
        self.figure.clear()
        
        if not values or len(values) < 2:
            return
            
        # Create axis with no margins
        ax = self.figure.add_axes([0, 0.1, 1, 0.8])
        ax.set_xlim(-0.5, len(values) - 0.5)
        
        # Remove all decorations
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        # Plot line
        x = range(len(values))
        ax.plot(x, values, color='#FF8C42', linewidth=2)
        
        # Add shaded area
        ax.fill_between(x, values, alpha=0.1, color='#FF8C42')
        
        # Highlight last point
        if highlight_last:
            ax.scatter([len(values) - 1], [values[-1]], 
                      color='#FF8C42', s=30, zorder=5)
            
        self.draw()


class DailyTrendIndicator(QWidget):
    """Complete daily trend indicator with arrow, value, and sparkline."""
    
    # Signal emitted when hovering for tooltip
    hover_details = pyqtSignal(str)
    
    def __init__(self, metric_name: str, parent=None):
        super().__init__(parent)
        self.metric_name = metric_name
        self.trend_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Left section: Metric name and value
        left_layout = QVBoxLayout()
        
        # Metric name
        self.name_label = QLabel(self.metric_name)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #5D4E37;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        left_layout.addWidget(self.name_label)
        
        # Current value
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            QLabel {
                color: #5D4E37;
                font-size: 22px;
                font-weight: 600;
            }
        """)
        left_layout.addWidget(self.value_label)
        
        # Change label
        self.change_label = QLabel("")
        self.change_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
            }
        """)
        left_layout.addWidget(self.change_label)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Middle section: Arrow indicator
        self.arrow_indicator = ArrowIndicator()
        layout.addWidget(self.arrow_indicator)
        
        # Right section: Sparkline
        self.sparkline = SparklineWidget()
        self.sparkline.setFixedSize(120, 60)
        layout.addWidget(self.sparkline)
        
        # Set widget styling
        self.setStyleSheet("""
            DailyTrendIndicator {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E8DED3;
            }
            DailyTrendIndicator:hover {
                border: 1px solid #FF8C42;
            }
        """)
        
        # Enable mouse tracking for tooltips
        self.setMouseTracking(True)
        
    def update_trend(self, trend_data: TrendData):
        """Update the indicator with new trend data."""
        self.trend_data = trend_data
        
        # Update value label
        self.value_label.setText(f"{trend_data.current_value:.1f} {trend_data.unit}")
        
        # Update change label
        if trend_data.change_percent is not None:
            # Handle zero previous value case
            if trend_data.previous_value == 0:
                change_text = f"{trend_data.change_absolute:+.1f} {trend_data.unit}"
                color = "#95C17B" if trend_data.change_absolute > 0 else "#E76F51" if trend_data.change_absolute < 0 else "#8B7355"
            else:
                change_text = f"{trend_data.change_absolute:+.1f} ({trend_data.change_percent:+.1f}%)"
                if trend_data.change_percent > 0:
                    color = "#95C17B" if trend_data.change_percent > 10 else "#FFD166"
                elif trend_data.change_percent < 0:
                    color = "#E76F51" if abs(trend_data.change_percent) > 10 else "#F4A261"
                else:
                    color = "#8B7355"
            self.change_label.setText(change_text)
            self.change_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        else:
            self.change_label.setText("Setting baseline")
            self.change_label.setStyleSheet("color: #8B7355; font-size: 12px; font-style: italic;")
            
        # Update arrow
        self.arrow_indicator.set_trend(trend_data.change_percent)
        
        # Update sparkline
        if len(trend_data.history) > 1:
            self.sparkline.update_data(trend_data.history)
            
    def enterEvent(self, event):
        """Show detailed tooltip on hover."""
        if self.trend_data:
            self.show_detailed_tooltip()
            
    def show_detailed_tooltip(self):
        """Display detailed change information."""
        if not self.trend_data:
            return
            
        tooltip_parts = [f"<b>{self.metric_name}</b><br>"]
        
        # Current value
        tooltip_parts.append(f"Current: {self.trend_data.current_value:.1f} {self.trend_data.unit}<br>")
        
        # Previous value and change
        if self.trend_data.previous_value is not None:
            tooltip_parts.append(f"Previous: {self.trend_data.previous_value:.1f} {self.trend_data.unit}<br>")
            tooltip_parts.append(f"Change: {self.trend_data.change_absolute:+.1f} ({self.trend_data.change_percent:+.1f}%)<br>")
        else:
            tooltip_parts.append("No previous data available<br>")
            
        # 7-day summary
        if len(self.trend_data.history) > 1:
            avg_7day = np.mean(self.trend_data.history)
            min_7day = np.min(self.trend_data.history)
            max_7day = np.max(self.trend_data.history)
            tooltip_parts.append(f"<br><b>7-Day Summary:</b><br>")
            tooltip_parts.append(f"Average: {avg_7day:.1f}<br>")
            tooltip_parts.append(f"Range: {min_7day:.1f} - {max_7day:.1f}")
            
        QToolTip.showText(self.mapToGlobal(self.rect().center()), "".join(tooltip_parts))