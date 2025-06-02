"""
Activity Heatmap Widget for Activity Timeline.

This module provides a heatmap visualization that shows activity intensity
across hours of the day and days of the week, making it easy to spot
patterns at a glance.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QToolTip, QVBoxLayout, QWidget


class ActivityHeatmapWidget(QFrame):
    """
    Widget that displays activity data as a heatmap grid.
    
    Shows a 24x7 grid (hours x days) with color intensity representing
    activity levels, making patterns easily visible.
    """
    
    # Signals
    time_clicked = pyqtSignal(str, dict)  # time_key, details
    
    # Color palette
    COLORS = {
        'card_bg': '#FFFFFF',
        'header_bg': '#FFFFFF',      # White header (changed from cream)
        'text_primary': '#2C3E50',
        'text_secondary': '#5D6D7E',
        'grid_lines': '#E0E0E0',
        'cell_empty': '#F5F5F5',
        'heat_gradient': [
            '#E8F5E9',  # Very light green
            '#A5D6A7',  # Light green
            '#66BB6A',  # Medium green
            '#43A047',  # Green
            '#2E7D32'   # Dark green
        ],
        'border': '#E0E0E0',
        'hover_border': '#FF8C42'
    }
    
    def __init__(self, parent=None):
        """Initialize the Activity Heatmap Widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.data = {}  # (day, hour) -> intensity
        self.max_intensity = 0
        self.hovered_cell = None
        self.setup_ui()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def setup_ui(self):
        """Set up the user interface."""
        # Card styling
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            ActivityHeatmapWidget {{
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
        title_label = QLabel("📅 Activity Heatmap")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_primary']};
                font-size: 16px;
                font-weight: 600;
                font-family: 'Poppins', 'Inter', sans-serif;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Your activity patterns by hour and day")
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 13px;
                margin-left: 10px;
            }}
        """)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
        
        # Heatmap content
        content_frame = QFrame()
        content_frame.setStyleSheet("border: none; padding: 15px;")
        self.content_layout = QVBoxLayout(content_frame)
        self.content_layout.setSpacing(10)
        
        # Create heatmap grid
        self.create_heatmap_grid()
        
        layout.addWidget(content_frame)
        
        # Calculate and set minimum size dynamically
        self.calculate_minimum_size()
        
    def create_heatmap_grid(self):
        """Create the heatmap grid structure."""
        # Grid container
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(40, 20, 20, 20)  # Space for labels
        
        # Days of week labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {self.COLORS['text_secondary']};
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(label, 0, i + 1)
            
        # Hour labels (show every 3 hours)
        for hour in range(24):
            if hour % 3 == 0:
                label = QLabel(f"{hour:02d}")
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.COLORS['text_secondary']};
                        font-size: 11px;
                    }}
                """)
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                grid_layout.addWidget(label, hour + 1, 0)
                
        # Create grid cells
        self.grid_widget = HeatmapGrid(self)
        self.grid_widget.cell_clicked.connect(self.on_cell_clicked)
        grid_layout.addWidget(self.grid_widget, 1, 1, 24, 7)
        
        self.content_layout.addWidget(grid_container)
        
        # Legend
        self.create_legend()
        
    def create_legend(self):
        """Create a color legend for the heatmap."""
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(15)
        
        # Legend label
        legend_label = QLabel("Activity Level:")
        legend_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 12px;
            }}
        """)
        legend_layout.addWidget(legend_label)
        
        # Color gradient boxes
        gradient_layout = QHBoxLayout()
        gradient_layout.setSpacing(2)
        
        # Low label
        low_label = QLabel("Low")
        low_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 11px;
            }}
        """)
        gradient_layout.addWidget(low_label)
        
        # Color boxes
        for color in self.COLORS['heat_gradient']:
            color_box = QFrame()
            color_box.setFixedSize(20, 12)
            color_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: 1px solid {self.COLORS['grid_lines']};
                    border-radius: 2px;
                }}
            """)
            gradient_layout.addWidget(color_box)
            
        # High label
        high_label = QLabel("High")
        high_label.setStyleSheet(f"""
            QLabel {{
                color: {self.COLORS['text_secondary']};
                font-size: 11px;
            }}
        """)
        gradient_layout.addWidget(high_label)
        
        legend_layout.addLayout(gradient_layout)
        legend_layout.addStretch()
        
        # Add to content
        legend_widget = QWidget()
        legend_widget.setLayout(legend_layout)
        self.content_layout.addWidget(legend_widget)
        
    def calculate_minimum_size(self):
        """Calculate and set the minimum size based on content."""
        # Base measurements
        grid_height = 24 * 10 + 23 * 2  # 24 cells * 10px + 23 gaps * 2px = 286px
        header_height = 70  # Header with title and subtitle
        grid_margins = 40  # Top margin for grid container
        legend_height = 50  # Legend section
        content_padding = 30  # Content frame padding
        card_padding = 20  # Overall card padding
        
        # Calculate total minimum height
        min_height = (
            header_height + 
            grid_margins + 
            grid_height + 
            legend_height + 
            content_padding + 
            card_padding
        )
        
        # Set minimum height to prevent scrolling
        self.setMinimumHeight(min_height)
        
    def update_data(self, data: Dict[Tuple[str, int], float]):
        """
        Update the heatmap with new data.
        
        Args:
            data: Dictionary mapping (day_name, hour) to intensity value
        """
        self.data = data
        self.max_intensity = max(data.values()) if data else 0
        
        # Update grid widget
        if hasattr(self, 'grid_widget'):
            self.grid_widget.set_data(data, self.max_intensity)
            self.grid_widget.update()
            
    def on_cell_clicked(self, day: str, hour: int):
        """Handle cell click events."""
        key = (day, hour)
        intensity = self.data.get(key, 0)
        
        details = {
            'day': day,
            'hour': hour,
            'time_str': f"{day} {hour:02d}:00",
            'intensity': intensity,
            'relative_intensity': intensity / self.max_intensity if self.max_intensity > 0 else 0
        }
        
        self.time_clicked.emit(f"{day}_{hour:02d}", details)
        

class HeatmapGrid(QWidget):
    """Custom widget for drawing the heatmap grid."""
    
    # Signals
    cell_clicked = pyqtSignal(str, int)  # day, hour
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.data = {}
        self.max_intensity = 0
        self.hovered_cell = None
        self.setMouseTracking(True)
        
        # Grid dimensions
        self.cell_width = 30
        self.cell_height = 10
        self.days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Set fixed size
        self.setFixedSize(
            len(self.days) * self.cell_width + (len(self.days) - 1) * 2,
            24 * self.cell_height + 23 * 2
        )
        
    def set_data(self, data: Dict[Tuple[str, int], float], max_intensity: float):
        """Set the data for the heatmap."""
        self.data = data
        self.max_intensity = max_intensity
        
    def paintEvent(self, event):
        """Custom paint event to draw the heatmap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw cells
        for day_idx, day in enumerate(self.days):
            for hour in range(24):
                x = day_idx * (self.cell_width + 2)
                y = hour * (self.cell_height + 2)
                
                # Get intensity for this cell
                key = (day, hour)
                intensity = self.data.get(key, 0)
                
                # Determine color based on intensity
                if intensity == 0:
                    color = QColor(self.parent_widget.COLORS['cell_empty'])
                else:
                    # Map intensity to color gradient
                    if self.max_intensity > 0:
                        ratio = intensity / self.max_intensity
                        gradient_idx = int(ratio * (len(self.parent_widget.COLORS['heat_gradient']) - 1))
                        gradient_idx = min(gradient_idx, len(self.parent_widget.COLORS['heat_gradient']) - 1)
                        color = QColor(self.parent_widget.COLORS['heat_gradient'][gradient_idx])
                    else:
                        color = QColor(self.parent_widget.COLORS['cell_empty'])
                        
                # Draw cell
                painter.fillRect(x, y, self.cell_width, self.cell_height, color)
                
                # Draw hover border if this is the hovered cell
                if self.hovered_cell == key:
                    painter.setPen(QColor(self.parent_widget.COLORS['hover_border']))
                    painter.drawRect(x, y, self.cell_width - 1, self.cell_height - 1)
                    
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover effects."""
        # Calculate which cell is hovered
        x = event.position().x()
        y = event.position().y()
        
        day_idx = int(x / (self.cell_width + 2))
        hour = int(y / (self.cell_height + 2))
        
        if 0 <= day_idx < len(self.days) and 0 <= hour < 24:
            new_hovered = (self.days[day_idx], hour)
            if new_hovered != self.hovered_cell:
                self.hovered_cell = new_hovered
                self.update()
                
                # Show tooltip
                intensity = self.data.get(new_hovered, 0)
                tooltip = f"{new_hovered[0]} {hour:02d}:00 - Activity: {intensity:.0f}"
                QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
        else:
            if self.hovered_cell is not None:
                self.hovered_cell = None
                self.update()
                
    def leaveEvent(self, event):
        """Handle mouse leave."""
        if self.hovered_cell is not None:
            self.hovered_cell = None
            self.update()
            
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            y = event.position().y()
            
            day_idx = int(x / (self.cell_width + 2))
            hour = int(y / (self.cell_height + 2))
            
            if 0 <= day_idx < len(self.days) and 0 <= hour < 24:
                self.cell_clicked.emit(self.days[day_idx], hour)