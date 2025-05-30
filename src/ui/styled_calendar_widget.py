"""Custom styled calendar widget with modern design and proper sizing.

This module provides a custom QCalendarWidget with modern styling that matches
the application's design system and fixes common display issues like cut-off
days and improper month boundaries.

Key features:
    - Proper sizing to show all 7 days and 6 week rows
    - Modern styling consistent with WSJ-inspired design
    - Hide days from adjacent months option
    - Enhanced visual feedback for data availability
    - Proper spacing and padding for readability

Example:
    >>> calendar = StyledCalendarWidget()
    >>> calendar.setHideDaysFromOtherMonths(True)
    >>> date_edit.setCalendarWidget(calendar)
"""

from PyQt6.QtWidgets import QCalendarWidget, QToolButton
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QTextCharFormat, QFont, QColor, QPalette

from .style_manager import StyleManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StyledCalendarWidget(QCalendarWidget):
    """Custom calendar widget with modern styling and proper sizing.
    
    This calendar widget provides a clean, modern appearance with proper sizing
    to ensure all days and weeks are visible. It integrates with the application's
    design system for consistent styling.
    
    Attributes:
        hide_other_months (bool): Whether to hide days from adjacent months
        style_manager (StyleManager): Application style manager instance
    """
    
    def __init__(self, parent=None):
        """Initialize the styled calendar widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.hide_other_months = True
        self.style_manager = StyleManager()
        
        self._setup_styling()
        self._configure_calendar()
        
    def _setup_styling(self):
        """Apply modern styling to the calendar widget."""
        # Base stylesheet for the calendar
        calendar_style = f"""
            /* Calendar widget container */
            QCalendarWidget {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                min-width: 300px;
                min-height: 320px;
                font-family: 'Inter', -apple-system, sans-serif;
            }}
            
            /* Navigation bar styling */
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                padding: 8px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            
            /* Month/Year display */
            QCalendarWidget QToolButton {{
                color: {self.style_manager.TEXT_INVERSE};
                font-size: 16px;
                font-weight: 600;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                margin: 0 4px;
            }}
            
            QCalendarWidget QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            QCalendarWidget QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            
            /* Navigation arrows */
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {{
                qproperty-icon: none;
                font-size: 20px;
                font-weight: bold;
                padding: 4px 8px;
            }}
            
            QCalendarWidget QToolButton#qt_calendar_prevmonth::after {{
                content: "←";
            }}
            
            QCalendarWidget QToolButton#qt_calendar_nextmonth::after {{
                content: "→";
            }}
            
            /* Menu button */
            QCalendarWidget QToolButton::menu-indicator {{
                image: none;
            }}
            
            /* Table view for calendar grid */
            QCalendarWidget QTableView {{
                background-color: {self.style_manager.PRIMARY_BG};
                selection-background-color: {self.style_manager.ACCENT_SECONDARY};
                selection-color: {self.style_manager.TEXT_INVERSE};
                border: none;
                outline: none;
                gridline-color: {self.style_manager.ACCENT_LIGHT};
                font-size: 14px;
                padding: 8px;
            }}
            
            /* Day headers (Mon, Tue, etc.) */
            QCalendarWidget QHeaderView::section {{
                background-color: {self.style_manager.SECONDARY_BG};
                color: {self.style_manager.TEXT_SECONDARY};
                padding: 8px 4px;
                border: none;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }}
            
            /* Individual day cells */
            QCalendarWidget QTableView QAbstractItemView::item {{
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
            }}
            
            /* Hover effect for days */
            QCalendarWidget QTableView QAbstractItemView::item:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
            }}
            
            /* Selected day */
            QCalendarWidget QTableView QAbstractItemView::item:selected {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                color: {self.style_manager.TEXT_INVERSE};
                font-weight: 600;
            }}
            
            /* Today's date */
            QCalendarWidget QTableView QAbstractItemView::item:focus {{
                border: 2px solid {self.style_manager.FOCUS_COLOR};
                background-color: rgba(0, 128, 199, 0.1);
            }}
            
            /* Disabled days from other months */
            QCalendarWidget QTableView QAbstractItemView::item:disabled {{
                color: {self.style_manager.TEXT_MUTED};
                background-color: transparent;
            }}
        """
        
        self.setStyleSheet(calendar_style)
        
    def _configure_calendar(self):
        """Configure calendar behavior and appearance."""
        # Set minimum size to ensure all content is visible
        self.setMinimumSize(QSize(320, 340))
        
        # Configure grid
        self.setGridVisible(True)
        
        # Set first day of week to Monday
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        
        # Hide week numbers
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        
        # Set horizontal header format to short day names
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        
        # Enable navigation bar
        self.setNavigationBarVisible(True)
        
        # Set selection mode
        self.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        
        # Apply custom day text formats to hide other month days if needed
        if self.hide_other_months:
            self._update_day_formats()
            
        # Connect to current page changed to update formats
        self.currentPageChanged.connect(self._update_day_formats)
        
    def _update_day_formats(self):
        """Update text formats for calendar days."""
        if not self.hide_other_months:
            return
            
        # Get current month and year
        current_month = self.monthShown()
        current_year = self.yearShown()
        
        # Clear all formats first
        self.setDateTextFormat(QDate(), QTextCharFormat())
        
        # Create format for days from other months
        other_month_format = QTextCharFormat()
        other_month_format.setForeground(QColor(0, 0, 0, 0))  # Fully transparent
        
        # Apply format to days before and after current month
        # Check days in first week
        first_day = QDate(current_year, current_month, 1)
        start_of_week = first_day.addDays(-(first_day.dayOfWeek() - 1))
        
        current_date = start_of_week
        while current_date < first_day:
            self.setDateTextFormat(current_date, other_month_format)
            current_date = current_date.addDays(1)
            
        # Check days in last week
        if current_month == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = current_month + 1
            next_year = current_year
            
        first_of_next = QDate(next_year, next_month, 1)
        last_of_current = first_of_next.addDays(-1)
        
        # Find end of last week
        end_of_week = last_of_current.addDays(7 - last_of_current.dayOfWeek())
        
        current_date = first_of_next
        while current_date <= end_of_week:
            self.setDateTextFormat(current_date, other_month_format)
            current_date = current_date.addDays(1)
            
    def setHideDaysFromOtherMonths(self, hide: bool):
        """Set whether to hide days from other months.
        
        Args:
            hide: True to hide days from adjacent months
        """
        self.hide_other_months = hide
        self._update_day_formats()
        
    def showEvent(self, event):
        """Handle show event to ensure proper sizing.
        
        Args:
            event: Show event
        """
        super().showEvent(event)
        # Ensure minimum size is respected
        self.updateGeometry()
        
    def paintCell(self, painter, rect, date):
        """Custom paint for calendar cells.
        
        This can be overridden by subclasses to provide custom cell rendering
        such as data availability indicators.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle
            date: QDate for the cell
        """
        # Check if this is a day from another month
        if self.hide_other_months:
            shown_month = self.monthShown()
            shown_year = self.yearShown()
            
            if date.month() != shown_month or date.year() != shown_year:
                # Don't paint days from other months
                return
                
        # Otherwise use default painting
        super().paintCell(painter, rect, date)


class DataAvailabilityCalendarWidget(StyledCalendarWidget):
    """Calendar widget with data availability visualization.
    
    Extends StyledCalendarWidget to show data availability using colors
    and visual indicators for each date.
    """
    
    def __init__(self, parent=None):
        """Initialize the data availability calendar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.available_dates = set()
        self.partial_dates = set()
        
    def set_availability_data(self, available_dates: set, partial_dates: set):
        """Set data availability information.
        
        Args:
            available_dates: Set of dates with available data
            partial_dates: Set of dates with partial data
        """
        self.available_dates = available_dates
        self.partial_dates = partial_dates
        self.updateCells()
        
    def paintCell(self, painter, rect, date):
        """Paint calendar cells with availability indicators.
        
        Args:
            painter: QPainter instance
            rect: Cell rectangle  
            date: QDate for the cell
        """
        # Check if this is a day from another month
        if self.hide_other_months:
            shown_month = self.monthShown()
            shown_year = self.yearShown()
            
            if date.month() != shown_month or date.year() != shown_year:
                # Don't paint days from other months
                return
                
        # Convert QDate to Python date for comparison
        py_date = date.toPython()
        
        # Draw background based on availability
        if py_date in self.available_dates:
            if py_date in self.partial_dates:
                # Partial data - yellow background
                painter.fillRect(rect, QColor(255, 193, 7, 30))
            else:
                # Full data - green background
                painter.fillRect(rect, QColor(40, 167, 69, 30))
        else:
            # No data - light red background
            painter.fillRect(rect, QColor(220, 53, 69, 15))
            
        # Call parent to draw the text
        super().paintCell(painter, rect, date)