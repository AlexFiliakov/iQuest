"""
Statistics display widget for health data.
Shows record counts, date ranges, and breakdowns by type and source.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
from ..statistics_calculator import BasicStatistics


class StatisticsWidget(QWidget):
    """Widget for displaying basic health data statistics."""
    
    # Signal emitted when user clicks on a type or source
    filter_requested = pyqtSignal(str, str)  # (filter_type, filter_value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._statistics = None
    
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Data Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Summary section
        self.summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout()
        
        self.total_records_label = QLabel("Total Records: -")
        self.date_range_label = QLabel("Date Range: -")
        
        summary_layout.addWidget(self.total_records_label)
        summary_layout.addWidget(self.date_range_label)
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # Create scrollable area for types and sources
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Types section
        self.types_group = QGroupBox("Record Types")
        self.types_layout = QVBoxLayout()
        self.types_group.setLayout(self.types_layout)
        scroll_layout.addWidget(self.types_group)
        
        # Sources section
        self.sources_group = QGroupBox("Data Sources")
        self.sources_layout = QVBoxLayout()
        self.sources_group.setLayout(self.sources_layout)
        scroll_layout.addWidget(self.sources_group)
        
        # Add stretch to push content to top
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def update_statistics(self, stats: Optional[BasicStatistics]):
        """
        Update the display with new statistics.
        
        Args:
            stats: BasicStatistics object or None to clear
        """
        self._statistics = stats
        
        if not stats or stats.total_records == 0:
            self.clear_display()
            return
        
        # Update summary
        self.total_records_label.setText(f"Total Records: {stats.total_records:,}")
        
        if stats.date_range[0] and stats.date_range[1]:
            date_str = (f"Date Range: {stats.date_range[0].strftime('%Y-%m-%d')} "
                       f"to {stats.date_range[1].strftime('%Y-%m-%d')}")
            self.date_range_label.setText(date_str)
        else:
            self.date_range_label.setText("Date Range: -")
        
        # Clear existing items
        self._clear_layout(self.types_layout)
        self._clear_layout(self.sources_layout)
        
        # Add types (sorted by count)
        sorted_types = sorted(stats.records_by_type.items(), 
                            key=lambda x: x[1], reverse=True)
        
        for type_name, count in sorted_types[:10]:  # Show top 10
            type_label = ClickableLabel(f"{type_name}: {count:,}")
            type_label.clicked.connect(
                lambda checked, t=type_name: self.filter_requested.emit("type", t)
            )
            self.types_layout.addWidget(type_label)
        
        if len(sorted_types) > 10:
            more_label = QLabel(f"... and {len(sorted_types) - 10} more types")
            more_label.setStyleSheet("color: #666;")
            self.types_layout.addWidget(more_label)
        
        # Add sources (sorted by count)
        sorted_sources = sorted(stats.records_by_source.items(), 
                              key=lambda x: x[1], reverse=True)
        
        for source_name, count in sorted_sources:
            source_label = ClickableLabel(f"{source_name}: {count:,}")
            source_label.clicked.connect(
                lambda checked, s=source_name: self.filter_requested.emit("source", s)
            )
            self.sources_layout.addWidget(source_label)
    
    def clear_display(self):
        """Clear all statistics from the display."""
        self.total_records_label.setText("Total Records: -")
        self.date_range_label.setText("Date Range: -")
        self._clear_layout(self.types_layout)
        self._clear_layout(self.sources_layout)
        
        # Add "No data" labels
        no_data_types = QLabel("No data available")
        no_data_types.setStyleSheet("color: #999;")
        self.types_layout.addWidget(no_data_types)
        
        no_data_sources = QLabel("No data available")
        no_data_sources.setStyleSheet("color: #999;")
        self.sources_layout.addWidget(no_data_sources)
    
    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def get_statistics(self) -> Optional[BasicStatistics]:
        """Get the current statistics object."""
        return self._statistics


class ClickableLabel(QLabel):
    """Label that can be clicked like a link."""
    
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: #0066CC;
                padding: 2px;
            }
            QLabel:hover {
                color: #0052A3;
                text-decoration: underline;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)