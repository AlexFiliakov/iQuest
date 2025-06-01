"""
Empty state widget with helpful guidance for users.

This module provides a modern empty state component that guides users
when no data is available, following best UX practices.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

class EmptyStateWidget(QWidget):
    """
    A modern empty state widget with illustration and call-to-action.
    
    Features:
    - Customizable illustration/icon
    - Primary and secondary messages
    - Action button with signal
    - Clean, modern design
    """
    
    action_clicked = pyqtSignal()
    
    def __init__(self, 
                 title="No Data Available",
                 message="Get started by importing your Apple Health data",
                 action_text="Import Data",
                 icon_name=None,
                 parent=None):
        """Initialize the empty state widget."""
        super().__init__(parent)
        
        self.title = title
        self.message = message
        self.action_text = action_text
        self.icon_name = icon_name
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        
        # Add stretch at top
        layout.addStretch(1)
        
        # Icon/Illustration placeholder
        if self.icon_name:
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # For now, create a simple colored circle as placeholder
            pixmap = self._create_placeholder_icon(80, 80)
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #1F2937;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(400)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #6B7280;
                line-height: 1.5;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        layout.addWidget(message_label)
        
        # Action button
        if self.action_text:
            button_container = QHBoxLayout()
            button_container.addStretch()
            
            action_button = QPushButton(self.action_text)
            action_button.setCursor(Qt.CursorShape.PointingHandCursor)
            action_button.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #1D4ED8;
                }
                QPushButton:pressed {
                    background-color: #1E40AF;
                }
            """)
            action_button.clicked.connect(self.action_clicked.emit)
            button_container.addWidget(action_button)
            
            button_container.addStretch()
            layout.addLayout(button_container)
        
        # Add stretch at bottom
        layout.addStretch(1)
        
        # Set background
        self.setStyleSheet("""
            EmptyStateWidget {
                background-color: #FAFBFC;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        
    def _create_placeholder_icon(self, width, height):
        """Create a simple placeholder icon."""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a simple circle with gradient
        gradient_color = QColor("#E0E7FF")
        painter.setBrush(gradient_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, width, height)
        
        # Draw an icon in the center (simple chart icon)
        painter.setPen(QColor("#4F46E5"))
        painter.setPen(QPainter.Antialiasing)
        
        # Simple bar chart icon
        bar_width = 8
        bar_spacing = 4
        start_x = width // 2 - (3 * bar_width + 2 * bar_spacing) // 2
        
        heights = [height * 0.3, height * 0.5, height * 0.4]
        for i, h in enumerate(heights):
            x = start_x + i * (bar_width + bar_spacing)
            y = height // 2 + 10 - h // 2
            painter.fillRect(int(x), int(y), bar_width, int(h), QColor("#4F46E5"))
        
        painter.end()
        return pixmap
        
    def set_content(self, title=None, message=None, action_text=None):
        """Update the empty state content dynamically."""
        if title:
            self.title = title
        if message:
            self.message = message
        if action_text:
            self.action_text = action_text
            
        # Recreate UI with new content
        # Clear existing layout
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        self._setup_ui()