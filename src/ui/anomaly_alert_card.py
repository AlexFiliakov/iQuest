"""
Anomaly Alert Card for Activity Timeline.

This module provides a card widget that displays anomalies and unusual activities
in a user-friendly way, converting technical anomaly detection results into
understandable alerts and explanations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPalette
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class AnomalyAlertCard(QFrame):
    """
    Card widget that displays anomaly alerts in plain language.
    
    Transforms anomaly detection results into contextual alerts that
    help users understand unusual patterns in their activity data.
    """
    
    # Signals
    anomaly_clicked = pyqtSignal(str, dict)  # anomaly_id, details
    
    # Color palette
    COLORS = {
        'card_bg': '#FFFFFF',
        'header_bg': '#FFFFFF',      # White header (changed from cream)
        'text_primary': '#2C3E50',
        'text_secondary': '#5D6D7E',
        'alert_high': '#FF6B6B',
        'alert_medium': '#FFA726',
        'alert_low': '#66BB6A',
        'border': '#E0E0E0',
        'time_bg': '#F5F5F5',
        'dismiss_hover': '#E0E0E0'
    }
    
    # Severity icons
    SEVERITY_ICONS = {
        'high': '🚨',
        'medium': '⚠️',
        'low': 'ℹ️'
    }
    
    def __init__(self, parent=None):
        """Initialize the Anomaly Alert Card."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.anomalies = []
        self.dismissed_anomalies = set()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Card styling
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            AnomalyAlertCard {{
                background-color: {self.COLORS['card_bg']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                padding: 0px;
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['header_bg']};
                border: none;
                border-radius: 8px 8px 0 0;
                padding: 15px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🔍 Unusual Activity Detected")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_primary']};
                font-size: 16px;
                font-weight: 600;
                font-family: 'Poppins', 'Inter', sans-serif;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Alert count badge
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.COLORS['alert_medium']};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self.count_label.hide()  # Initially hidden
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        
        layout.addWidget(header_frame)
        
        # Content widget (no scroll)
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLORS['card_bg']};
            }}
        """)
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout.setSpacing(10)
        
        # Placeholder
        self.placeholder_label = QLabel("No unusual activity detected. Great job staying consistent!")
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 14px;
                padding: 20px;
            }}
        """)
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder_label)
        
        layout.addWidget(content_widget)
        
        # Set size constraints
        self.setMinimumHeight(200)
        # self.setMaximumHeight(400)
        
    def update_anomalies(self, anomalies: List[Dict[str, Any]]):
        """
        Update the card with new anomaly data.
        
        Args:
            anomalies: List of anomaly dictionaries containing:
                - time: DateTime of the anomaly
                - severity: 'high', 'medium', or 'low'
                - explanations: List of explanation strings
                - data: Raw data dictionary
        """
        self.anomalies = anomalies
        
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Filter out dismissed anomalies
        active_anomalies = [a for a in anomalies 
                           if self._get_anomaly_id(a) not in self.dismissed_anomalies]
        
        # Update count
        self.count_label.setText(str(len(active_anomalies)))
        if len(active_anomalies) == 0:
            self.count_label.hide()
        else:
            self.count_label.show()
            
        if not active_anomalies:
            self.placeholder_label = QLabel("No unusual activity detected. Great job staying consistent!")
            self.placeholder_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.COLORS['text_secondary']};
                    font-size: 14px;
                    padding: 20px;
                }}
            """)
            self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.placeholder_label)
            return
            
        # Add anomaly items
        for anomaly in active_anomalies[:5]:  # Show max 5 alerts
            alert_item = self.create_alert_item(anomaly)
            self.content_layout.addWidget(alert_item)
            
        # Add stretch to push items to top
        self.content_layout.addStretch()
        
    def show_loading(self):
        """Show a loading state in the card."""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add loading message
        loading_label = QLabel("Analyzing for unusual patterns...")
        loading_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 14px;
                font-style: italic;
                padding: 20px;
            }}
        """)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(loading_label)
        
        # Hide count
        self.count_label.hide()
        
    def show_error(self, error_message: str):
        """Show an error state in the card."""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add error message
        error_label = QLabel(f"Error analyzing patterns: {error_message}")
        error_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['alert_high']};
                font-size: 14px;
                padding: 20px;
            }}
        """)
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(error_label)
        
        # Hide count
        self.count_label.hide()
        
    def create_alert_item(self, anomaly: Dict[str, Any]) -> QFrame:
        """Create a widget for displaying a single anomaly alert."""
        alert_frame = QFrame()
        alert_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Get severity color
        severity_color = {
            'high': self.COLORS['alert_high'],
            'medium': self.COLORS['alert_medium'],
            'low': self.COLORS['alert_low']
        }.get(anomaly['severity'], self.COLORS['alert_low'])
        
        alert_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLORS['card_bg']};
                border: 2px solid {severity_color};
                border-radius: 6px;
                padding: 12px;
            }}
            QFrame:hover {{
                background-color: {self.COLORS['header_bg']};
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout(alert_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Header with icon, time, and dismiss button
        header_layout = QHBoxLayout()
        
        # Severity icon
        icon_label = QLabel(self.SEVERITY_ICONS[anomaly['severity']])
        icon_label.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(icon_label)
        
        # Time label
        time_str = self.format_time_relative(anomaly['time'])
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_primary']};
                font-size: 14px;
                font-weight: 600;
                background-color: {self.COLORS['time_bg']};
                padding: 2px 8px;
                border-radius: 4px;
            }}
        """)
        header_layout.addWidget(time_label)
        
        header_layout.addStretch()
        
        # # Dismiss button
        # dismiss_btn = QPushButton("✕")
        # dismiss_btn.setFixedSize(20, 20)
        # dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # dismiss_btn.setStyleSheet(f"""
        #     QPushButton {{
        #         background-color: transparent;
        #         border: none;
        #         color: {self.COLORS['text_secondary']};
        #         font-size: 14px;
        #         font-weight: bold;
        #         border-radius: 10px;
        #     }}
        #     QPushButton:hover {{
        #         background-color: {self.COLORS['dismiss_hover']};
        #         color: {self.COLORS['text_primary']};
        #     }}
        # """)
        # dismiss_btn.clicked.connect(lambda: self.dismiss_anomaly(anomaly))
        # header_layout.addWidget(dismiss_btn)
        
        main_layout.addLayout(header_layout)
        
        # Explanations
        for explanation in anomaly['explanations']:
            exp_label = QLabel(f"• {explanation}")
            exp_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.COLORS['text_primary']};
                    font-size: 13px;
                    padding-left: 5px;
                }}
            """)
            exp_label.setWordWrap(True)
            main_layout.addWidget(exp_label)
            
        # Add context suggestion
        context_label = QLabel(self.get_context_suggestion(anomaly))
        context_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 12px;
                font-style: italic;
                padding-top: 4px;
            }}
        """)
        context_label.setWordWrap(True)
        main_layout.addWidget(context_label)
        
        # Click handler
        alert_frame.mousePressEvent = lambda e: self.anomaly_clicked.emit(
            self._get_anomaly_id(anomaly), anomaly
        )
        
        return alert_frame
        
    def format_time_relative(self, time: datetime) -> str:
        """Format time as relative string (e.g., '2 hours ago', 'Yesterday')."""
        now = datetime.now()
        if hasattr(time, 'to_pydatetime'):
            time = time.to_pydatetime()
            
        diff = now - time
        
        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60} minutes ago"
            elif diff.seconds < 7200:
                return "1 hour ago"
            else:
                return f"{diff.seconds // 3600} hours ago"
        elif diff.days == 1:
            return f"Yesterday at {time.strftime('%I:%M %p').lstrip('0')}"
        elif diff.days < 7:
            return f"{time.strftime('%A')} at {time.strftime('%I:%M %p').lstrip('0')}"
        else:
            return time.strftime('%b %d at %I:%M %p').replace(' 0', ' ')
            
    def get_context_suggestion(self, anomaly: Dict[str, Any]) -> str:
        """Generate a contextual suggestion based on the anomaly type."""
        severity = anomaly['severity']
        time = anomaly['time']
        
        if hasattr(time, 'hour'):
            hour = time.hour
        else:
            hour = 12  # Default
            
        if severity == 'high':
            if hour < 6:
                return "💡 Late night activity can affect sleep quality. Consider earlier workouts."
            elif hour > 22:
                return "💡 Very late activity detected. Ensure you're getting adequate rest."
            else:
                return "💡 Significantly different from your usual pattern. Was this intentional?"
        elif severity == 'medium':
            return "💡 This differs from your typical routine. Track how you feel after this change."
        else:
            return "💡 Minor variation detected. This is normal and healthy!"
            
    def dismiss_anomaly(self, anomaly: Dict[str, Any]):
        """Dismiss an anomaly alert."""
        anomaly_id = self._get_anomaly_id(anomaly)
        self.dismissed_anomalies.add(anomaly_id)
        
        # Refresh display
        self.update_anomalies(self.anomalies)
        
        # Log dismissal for learning
        self.logger.info(f"User dismissed anomaly: {anomaly_id}")
        
    def _get_anomaly_id(self, anomaly: Dict[str, Any]) -> str:
        """Generate a unique ID for an anomaly."""
        time_str = anomaly['time'].isoformat() if hasattr(anomaly['time'], 'isoformat') else str(anomaly['time'])
        return f"{time_str}_{anomaly['severity']}"
        
    def paintEvent(self, event):
        """Custom paint event for drop shadow effect."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw subtle shadow
        shadow_color = QColor(0, 0, 0, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow_color)
        
        # Draw shadow with offset
        for i in range(3):
            offset = i + 1
            shadow_rect = self.rect().adjusted(offset, offset, -offset, -offset)
            painter.drawRoundedRect(shadow_rect, 8 - i, 8 - i)