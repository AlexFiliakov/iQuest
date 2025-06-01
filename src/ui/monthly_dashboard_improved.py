"""
Improved monthly dashboard widget with better layout and spacing.

This module provides an enhanced version of the monthly dashboard with:
- Better visual hierarchy and spacing
- Responsive layout that adapts to content
- Modern empty states
- Improved alignment and proportions
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..utils.logging_config import get_logger
from .charts.calendar_heatmap import CalendarHeatmapComponent
from .empty_state_widget import EmptyStateWidget
from .style_manager import StyleManager

logger = get_logger(__name__)


class ImprovedMonthlyDashboard(QWidget):
    """
    Enhanced monthly dashboard with improved layout and UX.
    """
    
    month_changed = pyqtSignal(int, int)
    metric_changed = pyqtSignal(str)
    
    def __init__(self, monthly_calculator=None, parent=None):
        """Initialize the improved monthly dashboard."""
        super().__init__(parent)
        
        self.monthly_calculator = monthly_calculator
        self.style_manager = StyleManager()
        
        # Current date
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        
        # Data
        self._available_metrics = []
        self._current_metric = ("StepCount", None)
        self._metric_data = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the improved UI layout."""
        # Main layout with proper margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Header with navigation
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Main content area with responsive layout
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Calendar section with adaptive sizing
        self.calendar_container = self._create_calendar_section()
        content_layout.addWidget(self.calendar_container)
        
        # Summary cards in a grid layout
        self.summary_container = self._create_summary_section()
        content_layout.addWidget(self.summary_container)
        
        # Add stretch to push content up
        content_layout.addStretch()
        
        main_layout.addWidget(content_widget, 1)
        
    def _create_header(self) -> QWidget:
        """Create improved header with better alignment."""
        header = QFrame()
        # header.setMaximumHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(16)
        
        # Month navigation - left aligned
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation buttons with consistent sizing
        self.prev_btn = self._create_nav_button("←", "Previous month")
        self.month_label = QLabel()
        self.month_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                padding: 0 16px;
                min-width: 180px;
                text-align: center;
            }}
        """)
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = self._create_nav_button("→", "Next month")
        self.today_btn = self._create_nav_button("Today", "Go to current month", width=60)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.month_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addSpacing(8)
        nav_layout.addWidget(self.today_btn)
        
        layout.addWidget(nav_widget)
        layout.addStretch()
        
        # Metric selector - right aligned
        metric_widget = QWidget()
        metric_layout = QHBoxLayout(metric_widget)
        metric_layout.setSpacing(8)
        metric_layout.setContentsMargins(0, 0, 0, 0)
        
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 500;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        self.metric_combo = QComboBox()
        self.metric_combo.setMinimumWidth(200)
        self.metric_combo.setStyleSheet(self.style_manager.get_combo_style())
        
        metric_layout.addWidget(metric_label)
        metric_layout.addWidget(self.metric_combo)
        
        layout.addWidget(metric_widget)
        
        # Update month label
        self._update_month_label()
        
        return header
        
    def _create_nav_button(self, text: str, tooltip: str, width: int = 36) -> QPushButton:
        """Create a navigation button with consistent styling."""
        btn = QPushButton(text)
        btn.setFixedSize(width, 36)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.ACCENT_LIGHT};
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.SECONDARY_BG};
            }}
        """)
        return btn
        
    def _create_calendar_section(self) -> QWidget:
        """Create calendar section with adaptive sizing."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        
        # Create calendar or empty state
        if self._metric_data:
            self.calendar_heatmap = CalendarHeatmapComponent()
            self.calendar_heatmap.setMinimumHeight(300)
            # self.calendar_heatmap.setMaximumHeight(400)
            layout.addWidget(self.calendar_heatmap)
        else:
            # Show empty state instead of calendar when no data
            self.empty_state = EmptyStateWidget(
                title="No Health Data Available",
                message="Import your Apple Health data to see monthly insights and trends",
                action_text="Go to Configuration",
                parent=self
            )
            self.empty_state.setMinimumHeight(300)
            layout.addWidget(self.empty_state)
            
        return container
        
    def _create_summary_section(self) -> QWidget:
        """Create summary section with grid layout."""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
            }}
        """)
        
        # Grid layout for summary cards
        grid = QGridLayout(container)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # Create summary cards
        cards = [
            ("Average", "0", "Daily average for the month"),
            ("Total", "0", "Total for the month"),
            ("Best Day", "0", "Highest single day value"),
            ("Trend", "—", "Month over month trend")
        ]
        
        for i, (title, value, tooltip) in enumerate(cards):
            card = self._create_summary_card(title, value, tooltip)
            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)
            
        # Ensure equal column stretch
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        return container
        
    def _create_summary_card(self, title: str, value: str, tooltip: str) -> QFrame:
        """Create a summary statistics card."""
        card = QFrame()
        card.setToolTip(tooltip)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 16px;
                min-height: 80px;
            }}
            QFrame:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        
        return card
        
    def _update_month_label(self):
        """Update the month/year label."""
        if hasattr(self, 'month_label'):
            month_name = datetime(self._current_year, self._current_month, 1).strftime("%B %Y")
            self.month_label.setText(month_name)