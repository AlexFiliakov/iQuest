"""Adaptive date edit widget with data availability integration."""

from datetime import date
from typing import Optional, Set

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCalendarWidget
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QPalette

from .enhanced_date_edit import EnhancedDateEdit
from .styled_calendar_widget import DataAvailabilityCalendarWidget
from ..data_availability_service import DataAvailabilityService, AvailabilityLevel
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AdaptiveDateEdit(EnhancedDateEdit):
    """Enhanced date edit with data availability feedback."""
    
    availabilityChanged = pyqtSignal()
    
    def __init__(self, parent=None, availability_service: Optional[DataAvailabilityService] = None):
        super().__init__(parent)
        
        self.availability_service = availability_service
        self.current_metric_type: Optional[str] = None
        self.available_dates: Set[date] = set()
        self.partial_dates: Set[date] = set()
        
        # Register for availability updates
        if self.availability_service:
            self.availability_service.register_callback(self._on_availability_updated)
            
        # Connect date changed signal to update availability
        self.dateChanged.connect(self._on_date_changed)
        
        # Customize calendar popup if available
        self.setCalendarPopup(True)
        
        # Replace default calendar with our styled version
        self._setup_styled_calendar()
        
        logger.debug("AdaptiveDateEdit initialized")
        
    def _setup_styled_calendar(self):
        """Setup the custom styled calendar widget."""
        # Create and set our custom calendar
        self.custom_calendar = DataAvailabilityCalendarWidget()
        self.custom_calendar.setHideDaysFromOtherMonths(True)
        self.setCalendarWidget(self.custom_calendar)
        
    def set_metric_type(self, metric_type: str):
        """Set the metric type for availability checking."""
        if self.current_metric_type != metric_type:
            self.current_metric_type = metric_type
            self._update_availability_data()
            
    def _update_availability_data(self):
        """Update availability data for the current metric type."""
        if not self.availability_service or not self.current_metric_type:
            self.available_dates.clear()
            self.partial_dates.clear()
            return
            
        try:
            # Get availability information
            data_range = self.availability_service.get_availability(self.current_metric_type)
            if not data_range or not data_range.start_date or not data_range.end_date:
                self.available_dates.clear()
                self.partial_dates.clear()
                self._update_calendar_highlighting()
                return
                
            # Get dates with data
            dates_with_data = self.availability_service.db.get_dates_with_data(
                self.current_metric_type, 
                data_range.start_date, 
                data_range.end_date
            )
            
            self.available_dates = set(dates_with_data)
            
            # Determine partial dates (gaps in otherwise available periods)
            self.partial_dates = set()
            for gap_start, gap_end in data_range.gaps:
                current = gap_start
                while current <= gap_end:
                    if current in self.available_dates:
                        self.partial_dates.add(current)
                    current = date(current.year, current.month, current.day)
                    
            self._update_calendar_highlighting()
            self._update_current_date_feedback()
            
        except Exception as e:
            logger.error(f"Error updating availability data: {e}")
            
    def _update_calendar_highlighting(self):
        """Update calendar highlighting to show data availability."""
        # Update our custom calendar with availability data
        if hasattr(self, 'custom_calendar'):
            self.custom_calendar.set_availability_data(
                self.available_dates,
                self.partial_dates
            )
                
    def _update_current_date_feedback(self):
        """Update tooltip and styling for current date availability."""
        current_py_date = self.date().toPython()
        
        if not self.current_metric_type:
            self.setToolTip("Select a metric type to see data availability")
            return
            
        if current_py_date in self.available_dates:
            if current_py_date in self.partial_dates:
                level = "partial"
                tooltip = f"Partial data available for {self.current_metric_type} on {current_py_date}"
                self.setStyleSheet("QDateEdit { border: 1px solid #FFC107; background-color: rgba(255, 193, 7, 0.08); }")
            else:
                level = "full" 
                tooltip = f"Full data available for {self.current_metric_type} on {current_py_date}"
                self.setStyleSheet("QDateEdit { border: 1px solid #28A745; background-color: rgba(40, 167, 69, 0.08); }")
        else:
            level = "none"
            tooltip = f"No data available for {self.current_metric_type} on {current_py_date}"
            self.setStyleSheet("QDateEdit { border: 1px solid #DC3545; background-color: rgba(220, 53, 69, 0.08); }")
            
        # Add keyboard navigation hints
        enhanced_tooltip = f"{tooltip}\n\nKeyboard Navigation:\n" \
                          "• Left/Right arrows: Previous/Next day\n" \
                          "• Up/Down arrows: Previous/Next week\n" \
                          "• Ctrl+Up/Down: Previous/Next month\n" \
                          "• Home/End: First/Last day of month\n" \
                          "• Page Up/Down: Previous/Next month"
        super().setToolTip(enhanced_tooltip)
        
    def _on_availability_updated(self):
        """Handle availability service updates."""
        self._update_availability_data()
        self.availabilityChanged.emit()
        
    def _on_date_changed(self, qdate: QDate):
        """Handle date changes to update feedback."""
        self._update_current_date_feedback()
        
    def suggest_available_date(self, prefer_recent: bool = True) -> Optional[date]:
        """Suggest an available date for the current metric."""
        if not self.available_dates:
            return None
            
        if prefer_recent:
            return max(self.available_dates)
        else:
            return min(self.available_dates)
            
    def has_data_for_current_date(self) -> bool:
        """Check if current date has data."""
        current_py_date = self.date().toPython()
        return current_py_date in self.available_dates
        
    def get_availability_level(self, target_date: Optional[date] = None) -> AvailabilityLevel:
        """Get availability level for a specific date (or current date)."""
        if target_date is None:
            target_date = self.date().toPython()
            
        if target_date in self.available_dates:
            if target_date in self.partial_dates:
                return AvailabilityLevel.PARTIAL
            else:
                return AvailabilityLevel.FULL
        else:
            return AvailabilityLevel.NONE
            
    def clear_highlighting(self):
        """Clear all availability highlighting."""
        self.available_dates.clear()
        self.partial_dates.clear()
        self.setStyleSheet("")
        if hasattr(self, 'custom_calendar'):
            self.custom_calendar.set_availability_data(set(), set())
            
    def cleanup(self):
        """Cleanup when widget is destroyed."""
        if self.availability_service:
            self.availability_service.unregister_callback(self._on_availability_updated)


class AdaptiveDateRangeWidget(QWidget):
    """Widget with two adaptive date edits for date range selection."""
    
    rangeChanged = pyqtSignal(QDate, QDate)
    availabilityChanged = pyqtSignal()
    
    def __init__(self, parent=None, availability_service: Optional[DataAvailabilityService] = None):
        super().__init__(parent)
        
        self.availability_service = availability_service
        self.current_metric_type: Optional[str] = None
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Start date
        self.start_label = QLabel("Start Date:")
        self.start_date_edit = AdaptiveDateEdit(self, self.availability_service)
        self.start_date_edit.setAccessibleName("Start Date")
        
        # End date  
        self.end_label = QLabel("End Date:")
        self.end_date_edit = AdaptiveDateEdit(self, self.availability_service)
        self.end_date_edit.setAccessibleName("End Date")
        
        # Add to layout
        layout.addWidget(self.start_label)
        layout.addWidget(self.start_date_edit)
        layout.addWidget(self.end_label)
        layout.addWidget(self.end_date_edit)
        
        self.setLayout(layout)
        
    def _connect_signals(self):
        """Connect widget signals."""
        self.start_date_edit.dateChanged.connect(self._on_range_changed)
        self.end_date_edit.dateChanged.connect(self._on_range_changed)
        
        self.start_date_edit.availabilityChanged.connect(self.availabilityChanged)
        self.end_date_edit.availabilityChanged.connect(self.availabilityChanged)
        
    def _on_range_changed(self):
        """Handle date range changes."""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        # Ensure start <= end
        if start_date > end_date:
            if self.sender() == self.start_date_edit:
                self.end_date_edit.setDate(start_date)
            else:
                self.start_date_edit.setDate(end_date)
                
        self.rangeChanged.emit(self.start_date_edit.date(), self.end_date_edit.date())
        
    def set_metric_type(self, metric_type: str):
        """Set metric type for both date edits."""
        self.current_metric_type = metric_type
        self.start_date_edit.set_metric_type(metric_type)
        self.end_date_edit.set_metric_type(metric_type)
        
    def get_date_range(self) -> tuple[QDate, QDate]:
        """Get the current date range."""
        return (self.start_date_edit.date(), self.end_date_edit.date())
        
    def set_date_range(self, start_date: QDate, end_date: QDate):
        """Set the date range."""
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        
    def suggest_optimal_range(self) -> Optional[tuple[date, date]]:
        """Suggest optimal date range based on data availability."""
        start_suggestion = self.start_date_edit.suggest_available_date(prefer_recent=False)
        end_suggestion = self.end_date_edit.suggest_available_date(prefer_recent=True)
        
        if start_suggestion and end_suggestion:
            return (start_suggestion, end_suggestion)
        return None
        
    def has_data_for_range(self) -> bool:
        """Check if both start and end dates have data."""
        return (self.start_date_edit.has_data_for_current_date() and 
                self.end_date_edit.has_data_for_current_date())
                
    def cleanup(self):
        """Cleanup when widget is destroyed."""
        self.start_date_edit.cleanup()
        self.end_date_edit.cleanup()