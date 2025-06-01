"""
Pattern Recognition Card for Activity Timeline.

This module provides a card widget that displays activity patterns in a
user-friendly way, converting technical cluster data into understandable
insights about user behavior patterns.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient
from typing import List, Dict, Any
import logging


class PatternRecognitionCard(QFrame):
    """
    Card widget that displays recognized activity patterns.
    
    Transforms cluster analysis results into human-readable insights
    about when and how users are typically active.
    """
    
    # Signals
    pattern_clicked = pyqtSignal(str, dict)  # pattern_name, details
    
    # Color palette
    COLORS = {
        'card_bg': '#FFFFFF',
        'header_bg': '#FFFFFF',      # White header (changed from cream)
        'text_primary': '#2C3E50',
        'text_secondary': '#5D6D7E', 
        'accent_orange': '#FF8C42',
        'accent_yellow': '#FFD166',
        'accent_green': '#95C17B',
        'border': '#E0E0E0',
        'progress_bg': '#F0F0F0',
        'shadow': 'rgba(0, 0, 0, 0.08)'
    }
    
    def __init__(self, parent=None):
        """Initialize the Pattern Recognition Card."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.patterns = []
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Card styling
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            PatternRecognitionCard {{
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
        
        # Title with icon
        title_label = QLabel("📊 Your Activity Patterns")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_primary']};
                font-size: 16px;
                font-weight: 600;
                font-family: 'Poppins', 'Inter', sans-serif;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
        
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                border: none;
                padding: 15px;
            }
        """)
        self.content_layout = QVBoxLayout(content_frame)
        self.content_layout.setSpacing(12)
        
        # Placeholder text
        self.placeholder_label = QLabel("Analyzing your activity patterns...")
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 14px;
                padding: 20px;
            }}
        """)
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder_label)
        
        layout.addWidget(content_frame)
        
        # Set minimum height
        self.setMinimumHeight(200)
        
    def update_patterns(self, patterns: List[Dict[str, Any]]):
        """
        Update the card with new pattern data.
        
        Args:
            patterns: List of pattern dictionaries containing:
                - name: Pattern name
                - detail: Detailed description
                - icon: Emoji icon
                - frequency: Percentage frequency
                - intensity: Average intensity
        """
        self.patterns = patterns
        
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not patterns:
            self.placeholder_label = QLabel("No patterns detected yet. Keep tracking!")
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
            
        # Add pattern items
        for i, pattern in enumerate(patterns[:3]):  # Show top 3 patterns
            pattern_item = self.create_pattern_item(pattern, i == 0)
            self.content_layout.addWidget(pattern_item)
            
    def create_pattern_item(self, pattern: Dict[str, Any], is_primary: bool = False) -> QFrame:
        """Create a widget for displaying a single pattern."""
        item_frame = QFrame()
        item_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style based on whether it's the primary pattern
        bg_color = self.COLORS['accent_yellow'] if is_primary else '#F8F9FA'
        text_color = self.COLORS['text_primary'] if is_primary else self.COLORS['text_secondary']
        
        item_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {self.COLORS['border']};
                border-radius: 6px;
                padding: 12px;
            }}
            QFrame:hover {{
                background-color: {self.COLORS['header_bg']};
                border-color: {self.COLORS['accent_orange']};
            }}
        """)
        
        # Layout
        layout = QVBoxLayout(item_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header row with icon and name
        header_layout = QHBoxLayout()
        
        # Icon and name
        icon_label = QLabel(pattern['icon'])
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        name_label = QLabel(pattern['name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 15px;
                font-weight: 600;
            }}
        """)
        header_layout.addWidget(name_label)
        
        # Frequency badge
        freq_label = QLabel(f"{pattern['frequency']:.0f}%")
        freq_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.COLORS['accent_orange']};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        header_layout.addStretch()
        header_layout.addWidget(freq_label)
        
        layout.addLayout(header_layout)
        
        # Detail text
        detail_label = QLabel(pattern['detail'])
        detail_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 13px;
            }}
        """)
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)
        
        # Progress bar showing relative frequency
        if pattern['frequency'] > 0:
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(100)
            progress.setValue(int(pattern['frequency']))
            progress.setTextVisible(False)
            progress.setFixedHeight(4)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {self.COLORS['progress_bg']};
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.COLORS['accent_green']};
                    border-radius: 2px;
                }}
            """)
            layout.addWidget(progress)
            
        # Click handler
        item_frame.mousePressEvent = lambda e: self.pattern_clicked.emit(
            pattern['name'], pattern
        )
        
        return item_frame
        
    def paintEvent(self, event):
        """Custom paint event for drop shadow effect."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw subtle shadow
        shadow_color = QColor(0, 0, 0, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow_color)
        
        # Draw shadow rectangles with offset
        for i in range(3):
            offset = i + 1
            shadow_rect = QRect(
                offset, offset,
                self.width() - offset * 2,
                self.height() - offset * 2
            )
            painter.drawRoundedRect(shadow_rect, 8 - i, 8 - i)