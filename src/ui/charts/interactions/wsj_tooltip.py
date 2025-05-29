"""
WSJ-styled tooltip for health data visualization.

Provides elegant, informative tooltips with health context and trend information.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont
from typing import Dict, Any, Optional
from datetime import datetime


class WSJTooltip(QWidget):
    """WSJ-styled tooltip for health data"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # WSJ color scheme
        self.background_color = QColor('#F5E6D3')  # Warm tan
        self.text_color = QColor('#6B4226')  # Dark brown
        self.border_color = QColor('#D4B5A0')  # Light brown
        self.accent_color = QColor('#FF8C42')  # Orange
        
        # Trend colors
        self.positive_color = QColor('#7CB342')  # Green
        self.negative_color = QColor('#F4511E')  # Red
        self.neutral_color = self.text_color
        
        # Setup UI
        self.setup_ui()
        self.setup_animations()
        
        # Add shadow effect
        self.setup_shadow()
        
        # Initially hidden
        self.hide()
        
    def setup_ui(self):
        """Setup tooltip UI with WSJ styling"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        
        # Title row (metric name and date)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        self.metric_label = QLabel()
        self.metric_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 11px;
                font-weight: 600;
                font-family: Arial, sans-serif;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }}
        """)
        
        self.date_label = QLabel()
        self.date_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 11px;
                font-family: Arial, sans-serif;
                opacity: 0.7;
            }}
        """)
        
        title_layout.addWidget(self.metric_label)
        title_layout.addStretch()
        title_layout.addWidget(self.date_label)
        
        # Primary value
        self.value_label = QLabel()
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 24px;
                font-weight: bold;
                font-family: Georgia, serif;
            }}
        """)
        
        # Secondary info row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)
        
        # Trend indicator
        self.trend_label = QLabel()
        self.trend_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-family: Arial, sans-serif;
                font-weight: 500;
            }}
        """)
        
        # Context information
        self.context_label = QLabel()
        self.context_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 12px;
                font-family: Arial, sans-serif;
                opacity: 0.8;
            }}
        """)
        
        info_layout.addWidget(self.trend_label)
        info_layout.addWidget(self.context_label)
        info_layout.addStretch()
        
        # Additional metrics (if applicable)
        self.additional_layout = QVBoxLayout()
        self.additional_layout.setSpacing(4)
        
        # Assemble layout
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.value_label)
        main_layout.addLayout(info_layout)
        main_layout.addLayout(self.additional_layout)
        
        self.setLayout(main_layout)
        
        # Set minimum size
        self.setMinimumWidth(240)
        
    def setup_shadow(self):
        """Add subtle drop shadow"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        
    def setup_animations(self):
        """Setup fade animations"""
        self._opacity = 0.0
        
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.fade_out)
        self.hide_timer.setSingleShot(True)
        
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
        
    def paintEvent(self, event):
        """Custom paint for WSJ-style background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, 6, 6)
        
        # Fill background
        painter.fillPath(path, self.background_color)
        
        # Draw border
        pen = QPen(self.border_color, 1)
        painter.setPen(pen)
        painter.drawPath(path)
        
    def show_health_data(self, data_point: Dict[str, Any]):
        """Display health data in tooltip"""
        # Clear additional metrics
        self._clear_additional_metrics()
        
        # Extract data
        metric_name = data_point.get('metric', 'Health Metric')
        value = data_point.get('value', 0)
        unit = data_point.get('unit', '')
        timestamp = data_point.get('timestamp', None)
        trend = data_point.get('trend', 0)
        average = data_point.get('average', None)
        goal = data_point.get('goal', None)
        percentile = data_point.get('percentile', None)
        
        # Set metric name
        self.metric_label.setText(metric_name.upper())
        
        # Format date
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime('%b %d, %Y')
                except:
                    date_str = timestamp
            else:
                date_str = timestamp.strftime('%b %d, %Y')
            self.date_label.setText(date_str)
        else:
            self.date_label.setText('')
            
        # Format primary value
        if isinstance(value, (int, float)):
            if value >= 10000:
                formatted_value = f"{value:,.0f}"
            elif value >= 100:
                formatted_value = f"{value:.0f}"
            else:
                formatted_value = f"{value:.1f}"
        else:
            formatted_value = str(value)
            
        if unit:
            self.value_label.setText(f"{formatted_value} {unit}")
        else:
            self.value_label.setText(formatted_value)
            
        # Format trend
        if trend != 0:
            trend_text = f"{abs(trend):.1%}"
            if trend > 0:
                self.trend_label.setText(f"↑ {trend_text}")
                self.trend_label.setStyleSheet(f"color: {self.positive_color.name()}; font-size: 12px; font-weight: 500;")
            else:
                self.trend_label.setText(f"↓ {trend_text}")
                self.trend_label.setStyleSheet(f"color: {self.negative_color.name()}; font-size: 12px; font-weight: 500;")
        else:
            self.trend_label.setText("—")
            self.trend_label.setStyleSheet(f"color: {self.neutral_color.name()}; font-size: 12px; font-weight: 500;")
            
        # Format context
        context_parts = []
        if average is not None:
            context_parts.append(f"Avg: {average:.0f}")
        if goal is not None:
            progress = (value / goal * 100) if goal > 0 else 0
            context_parts.append(f"Goal: {progress:.0f}%")
        if percentile is not None:
            context_parts.append(f"{percentile}th percentile")
            
        if context_parts:
            self.context_label.setText(" • ".join(context_parts))
        else:
            self.context_label.setText("")
            
        # Add additional metrics if provided
        additional_metrics = data_point.get('additional_metrics', {})
        for metric, value in additional_metrics.items():
            self._add_additional_metric(metric, value)
            
        # Show with animation
        self.fade_in()
        
    def _add_additional_metric(self, name: str, value: Any):
        """Add an additional metric row"""
        metric_label = QLabel(f"{name}: {value}")
        metric_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 11px;
                font-family: Arial, sans-serif;
                padding-top: 2px;
            }}
        """)
        self.additional_layout.addWidget(metric_label)
        
    def _clear_additional_metrics(self):
        """Clear all additional metric labels"""
        while self.additional_layout.count():
            item = self.additional_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def fade_in(self):
        """Fade in the tooltip"""
        self.show()
        self.raise_()
        
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.opacity)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Reset auto-hide timer
        self.hide_timer.stop()
        self.hide_timer.start(5000)  # Hide after 5 seconds
        
    def fade_out(self):
        """Fade out the tooltip"""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.opacity)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
        
    def enterEvent(self, event):
        """Stop auto-hide when mouse enters"""
        self.hide_timer.stop()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Restart auto-hide when mouse leaves"""
        self.hide_timer.start(2000)  # Hide after 2 seconds
        super().leaveEvent(event)