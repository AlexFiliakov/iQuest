"""
Improved configuration tab with better layout and modern design.

This module provides an enhanced configuration interface with:
- Better visual hierarchy and spacing
- Aligned date inputs in a horizontal layout
- Improved empty states and user guidance
- Modern card-based design
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDateEdit, QFrame, QScrollArea, QGridLayout,
    QGroupBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from .style_manager import StyleManager
from .empty_state_widget import EmptyStateWidget
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ImprovedConfigurationTab(QWidget):
    """
    Enhanced configuration tab with improved layout and UX.
    """
    
    data_loaded = pyqtSignal()
    filters_applied = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the improved configuration tab."""
        super().__init__(parent)
        
        self.style_manager = StyleManager()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the improved UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Scroll area for responsive layout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F8F9FA;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ADB5BD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6C757D;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Import section
        import_section = self._create_import_section()
        content_layout.addWidget(import_section)
        
        # Filter section
        filter_section = self._create_filter_section()
        content_layout.addWidget(filter_section)
        
        # Summary section
        summary_section = self._create_summary_section()
        content_layout.addWidget(summary_section)
        
        # Data preview section
        preview_section = self._create_preview_section()
        content_layout.addWidget(preview_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_section_card(self, title: str) -> QFrame:
        """Create a consistent section card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: {self.style_manager.RADIUS['lg']}px;
                padding: {self.style_manager.SPACING['lg']}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(self.style_manager.SPACING['md'])
        
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: {self.style_manager.SPACING['sm']}px;
            }}
        """)
        layout.addWidget(title_label)
        
        return card
        
    def _create_import_section(self) -> QWidget:
        """Create the import data section."""
        card = self._create_section_card("Import Data")
        layout = card.layout()
        
        # File selection row
        file_row = QHBoxLayout()
        file_row.setSpacing(self.style_manager.SPACING['sm'])
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select Apple Health export file...")
        self.file_input.setReadOnly(True)
        self.file_input.setStyleSheet(self.style_manager.get_input_style())
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        file_row.addWidget(self.file_input, 1)
        file_row.addWidget(browse_button)
        
        layout.addLayout(file_row)
        
        # Import actions row
        action_row = QHBoxLayout()
        action_row.setSpacing(self.style_manager.SPACING['sm'])
        
        import_button = QPushButton("Import Data")
        import_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        import_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        clear_button = QPushButton("Clear Data")
        clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_ERROR};
                color: white;
                border: none;
                border-radius: {self.style_manager.RADIUS['md']}px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
        """)
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        action_row.addWidget(import_button)
        action_row.addWidget(clear_button)
        action_row.addStretch()
        
        layout.addLayout(action_row)
        
        return card
        
    def _create_filter_section(self) -> QWidget:
        """Create the filter data section with improved layout."""
        card = self._create_section_card("Filter Data")
        layout = card.layout()
        
        # Date range row - HORIZONTAL LAYOUT
        date_row = QHBoxLayout()
        date_row.setSpacing(self.style_manager.SPACING['md'])
        
        # Start date group
        start_group = QWidget()
        start_layout = QVBoxLayout(start_group)
        start_layout.setSpacing(self.style_manager.SPACING['xs'])
        start_layout.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("Start Date")
        start_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setStyleSheet(self._get_date_edit_style())
        
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_date)
        
        # End date group
        end_group = QWidget()
        end_layout = QVBoxLayout(end_group)
        end_layout.setSpacing(self.style_manager.SPACING['xs'])
        end_layout.setContentsMargins(0, 0, 0, 0)
        
        end_label = QLabel("End Date")
        end_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet(self._get_date_edit_style())
        
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_date)
        
        # Apply button
        apply_button = QPushButton("Apply Filters")
        apply_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button.setFixedHeight(self.start_date.height())
        
        date_row.addWidget(start_group)
        date_row.addWidget(end_group)
        date_row.addWidget(apply_button)
        date_row.addStretch()
        
        layout.addLayout(date_row)
        
        # Additional filters placeholder
        filter_info = QLabel("Additional filters for metrics and sources will appear here after importing data")
        filter_info.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.style_manager.TEXT_MUTED};
                font-style: italic;
                padding: {self.style_manager.SPACING['md']}px 0;
            }}
        """)
        layout.addWidget(filter_info)
        
        return card
        
    def _create_summary_section(self) -> QWidget:
        """Create the summary cards section."""
        card = self._create_section_card("Summary")
        layout = card.layout()
        
        # Show empty state when no data
        empty_state = EmptyStateWidget(
            title="No Data Loaded",
            message="Import your Apple Health data to see summary statistics",
            action_text=None,  # No action button in summary
            parent=self
        )
        empty_state.setMinimumHeight(150)
        layout.addWidget(empty_state)
        
        return card
        
    def _create_preview_section(self) -> QWidget:
        """Create the data preview section."""
        card = self._create_section_card("Data Preview")
        layout = card.layout()
        
        # Preview controls
        controls_row = QHBoxLayout()
        controls_row.setSpacing(self.style_manager.SPACING['sm'])
        
        export_button = QPushButton("Export")
        export_button.setEnabled(False)
        export_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        
        filter_button = QPushButton("Filters")
        filter_button.setEnabled(False)
        filter_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        
        columns_button = QPushButton("Columns")
        columns_button.setEnabled(False)
        columns_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        
        controls_row.addWidget(export_button)
        controls_row.addWidget(filter_button)
        controls_row.addWidget(columns_button)
        controls_row.addStretch()
        
        layout.addLayout(controls_row)
        
        # Empty state for preview
        preview_empty = EmptyStateWidget(
            title="No Data to Preview",
            message="Data preview will appear here after importing",
            action_text=None,
            parent=self
        )
        preview_empty.setMinimumHeight(200)
        layout.addWidget(preview_empty)
        
        return card
        
    def _get_date_edit_style(self) -> str:
        """Get consistent date edit styling."""
        return f"""
            QDateEdit {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: {self.style_manager.RADIUS['md']}px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 140px;
            }}
            QDateEdit:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QDateEdit:focus {{
                border-color: {self.style_manager.FOCUS_COLOR};
                outline: none;
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.style_manager.TEXT_SECONDARY};
                width: 0;
                height: 0;
            }}
        """