"""Adaptive time range selector with data availability integration."""

from datetime import date, timedelta, datetime
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QButtonGroup, QFrame)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from ..data_availability_service import (DataAvailabilityService, TimeRange, 
                                        RangeAvailability, AvailabilityLevel)
from .smart_default_selector import SmartDefaultSelector, SelectionContext
from .preference_tracker import PreferenceTracker
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AdaptiveTimeRangeSelector(QWidget):
    """Time range selector that adapts based on data availability."""
    
    rangeSelected = pyqtSignal(str)  # Emits range type as string
    availabilityChanged = pyqtSignal()
    
    def __init__(self, parent=None, availability_service: Optional[DataAvailabilityService] = None,
                 smart_selector: Optional[SmartDefaultSelector] = None):
        super().__init__(parent)
        
        self.availability_service = availability_service
        self.current_metric_type: Optional[str] = None
        self.range_availabilities: Dict[TimeRange, RangeAvailability] = {}
        
        # Smart selection system
        if smart_selector:
            self.smart_selector = smart_selector
        elif availability_service:
            # Create smart selector with availability service
            self.smart_selector = SmartDefaultSelector(availability_service)
        else:
            self.smart_selector = None
            
        # Interaction tracking for learning
        self.selection_start_time: Optional[datetime] = None
        self.interaction_actions = 0
        self.last_selected_range: Optional[TimeRange] = None
        
        # Timer for tracking view duration
        self.interaction_timer = QTimer()
        self.interaction_timer.timeout.connect(self._on_interaction_timeout)
        
        self._setup_ui()
        self._setup_styles()
        
        # Register for availability updates
        if self.availability_service:
            self.availability_service.register_callback(self._on_availability_updated)
            
        logger.debug("AdaptiveTimeRangeSelector initialized with smart selection")
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel("Time Range")
        title_font = QFont()
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setPointSize(10)
        self.title_label.setFont(title_font)
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        
        # Range buttons
        self.range_buttons: Dict[TimeRange, QPushButton] = {}
        
        # Today button
        self.today_button = QPushButton("Today")
        self.today_button.setCheckable(True)
        self.today_button.setProperty('range_type', TimeRange.TODAY)
        self.button_group.addButton(self.today_button)
        self.range_buttons[TimeRange.TODAY] = self.today_button
        
        # Week button  
        self.week_button = QPushButton("Week")
        self.week_button.setCheckable(True)
        self.week_button.setProperty('range_type', TimeRange.WEEK)
        self.button_group.addButton(self.week_button)
        self.range_buttons[TimeRange.WEEK] = self.week_button
        
        # Month button
        self.month_button = QPushButton("Month")
        self.month_button.setCheckable(True)
        self.month_button.setProperty('range_type', TimeRange.MONTH)
        self.button_group.addButton(self.month_button)
        self.range_buttons[TimeRange.MONTH] = self.month_button
        
        # Year button
        self.year_button = QPushButton("Year")
        self.year_button.setCheckable(True)
        self.year_button.setProperty('range_type', TimeRange.YEAR)
        self.button_group.addButton(self.year_button)
        self.range_buttons[TimeRange.YEAR] = self.year_button
        
        # Connect button signals
        for button in self.range_buttons.values():
            button.clicked.connect(self._on_range_button_clicked)
            
        # Layout buttons in a grid
        button_layout = QVBoxLayout()
        
        # First row: Today, Week
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.today_button)
        row1_layout.addWidget(self.week_button)
        
        # Second row: Month, Year
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(self.month_button)
        row2_layout.addWidget(self.year_button)
        
        button_layout.addLayout(row1_layout)
        button_layout.addLayout(row2_layout)
        
        # Status label for feedback
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumHeight(60)
        status_font = QFont()
        status_font.setPointSize(8)
        self.status_label.setFont(status_font)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        
        # Add to main layout
        layout.addWidget(self.title_label)
        layout.addWidget(separator)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def _setup_styles(self):
        """Setup widget styles."""
        # Set fixed width for consistent layout
        self.setFixedWidth(200)
        
        # Button styles will be set dynamically based on availability
        for button in self.range_buttons.values():
            button.setMinimumHeight(35)
            
    def set_metric_type(self, metric_type: str):
        """Set the metric type for availability checking."""
        if self.current_metric_type != metric_type:
            # End any current interaction tracking
            self._end_interaction_tracking()
            
            self.current_metric_type = metric_type
            self._update_availability()
            
            # Auto-select best range for new metric
            if metric_type:
                self.auto_select_best_range(SelectionContext.METRIC_CHANGE)
            
    def _update_availability(self):
        """Update availability for all time ranges."""
        if not self.availability_service or not self.current_metric_type:
            self._clear_availability()
            return
            
        try:
            # Get availability for all ranges
            available_ranges = self.availability_service.get_available_ranges(self.current_metric_type)
            
            # Store availability info
            self.range_availabilities.clear()
            for range_availability in available_ranges:
                self.range_availabilities[range_availability.range_type] = range_availability
                
            self._update_button_states()
            self._update_status_message()
            
        except Exception as e:
            logger.error(f"Error updating availability: {e}")
            self._clear_availability()
            
    def _clear_availability(self):
        """Clear availability information."""
        self.range_availabilities.clear()
        for button in self.range_buttons.values():
            button.setEnabled(False)
            button.setStyleSheet("")
            button.setToolTip("No metric selected")
        self.status_label.setText("Select a metric to see available time ranges")
        
    def _update_button_states(self):
        """Update button states based on availability."""
        for range_type, button in self.range_buttons.items():
            availability = self.range_availabilities.get(range_type)
            
            if availability and availability.available:
                # Enable button
                button.setEnabled(True)
                
                # Set style based on availability level
                if availability.level == AvailabilityLevel.FULL:
                    button.setStyleSheet("""
                        QPushButton { 
                            background-color: #90EE90; 
                            border: 2px solid #32CD32;
                            color: #006400;
                        }
                        QPushButton:hover { 
                            background-color: #98FB98; 
                        }
                        QPushButton:checked { 
                            background-color: #32CD32;
                            color: white;
                            font-weight: bold;
                        }
                    """)
                elif availability.level == AvailabilityLevel.PARTIAL:
                    button.setStyleSheet("""
                        QPushButton { 
                            background-color: #FFFF99; 
                            border: 2px solid #FFD700;
                            color: #B8860B;
                        }
                        QPushButton:hover { 
                            background-color: #FFFFE0; 
                        }
                        QPushButton:checked { 
                            background-color: #FFD700;
                            color: #8B4513;
                            font-weight: bold;
                        }
                    """)
                else:  # SPARSE
                    button.setStyleSheet("""
                        QPushButton { 
                            background-color: #FFE4B5; 
                            border: 2px solid #DEB887;
                            color: #8B4513;
                        }
                        QPushButton:hover { 
                            background-color: #FFF8DC; 
                        }
                        QPushButton:checked { 
                            background-color: #DEB887;
                            color: #654321;
                            font-weight: bold;
                        }
                    """)
                    
                # Set detailed tooltip
                tooltip = self._create_availability_tooltip(availability)
                button.setToolTip(tooltip)
                
            else:
                # Disable button
                button.setEnabled(False)
                button.setStyleSheet("""
                    QPushButton { 
                        background-color: #FFB6C1; 
                        border: 2px solid #CD5C5C;
                        color: #8B0000;
                    }
                """)
                
                # Set reason in tooltip
                reason = availability.reason if availability else "Insufficient data"
                button.setToolTip(f"Unavailable: {reason}")
                
    def _create_availability_tooltip(self, availability: RangeAvailability) -> str:
        """Create detailed tooltip for availability information."""
        range_name = availability.range_type.value.title()
        level_name = availability.level.value.title()
        
        tooltip = f"{range_name} View - {level_name} Data Available\n\n"
        tooltip += f"Data Points: {availability.data_points}\n"
        tooltip += f"Coverage: {availability.coverage_percent:.1f}%\n"
        
        if availability.level == AvailabilityLevel.FULL:
            tooltip += "\n✓ Complete data available"
        elif availability.level == AvailabilityLevel.PARTIAL:
            tooltip += "\n⚠ Some data gaps, but usable"
        else:  # SPARSE
            tooltip += "\n⚠ Limited data available"
            
        return tooltip
        
    def _update_status_message(self):
        """Update status message based on current availability."""
        if not self.current_metric_type:
            self.status_label.setText("Select a metric to see available time ranges")
            return
            
        available_count = sum(1 for avail in self.range_availabilities.values() if avail.available)
        total_count = len(TimeRange) - 1  # Exclude CUSTOM
        
        if available_count == 0:
            self.status_label.setText(f"No time ranges available for {self.current_metric_type}")
            self.status_label.setStyleSheet("color: #8B0000;")
        elif available_count == total_count:
            self.status_label.setText(f"All time ranges available for {self.current_metric_type}")
            self.status_label.setStyleSheet("color: #006400;")
        else:
            self.status_label.setText(f"{available_count}/{total_count} time ranges available for {self.current_metric_type}")
            self.status_label.setStyleSheet("color: #B8860B;")
            
    def _on_range_button_clicked(self):
        """Handle range button clicks."""
        button = self.sender()
        if button and button.isChecked():
            range_type = button.property('range_type')
            logger.info(f"Time range selected: {range_type.value}")
            
            # Track user interaction for learning
            self._track_range_selection(range_type, explicit=True)
            
            self.rangeSelected.emit(range_type.value)
            
    def _on_availability_updated(self):
        """Handle availability service updates."""
        self._update_availability()
        self.availabilityChanged.emit()
        
    def get_selected_range(self) -> Optional[TimeRange]:
        """Get the currently selected time range."""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            return checked_button.property('range_type')
        return None
        
    def select_range(self, range_type: TimeRange):
        """Programmatically select a time range."""
        button = self.range_buttons.get(range_type)
        if button and button.isEnabled():
            button.setChecked(True)
            
    def suggest_default_range(self, context: SelectionContext = SelectionContext.STARTUP) -> Optional[TimeRange]:
        """Suggest the best available time range using smart selection.
        
        Args:
            context: Context for the selection (startup, metric change, etc.)
            
        Returns:
            Best time range or None if no data available
        """
        if not self.current_metric_type:
            return None
            
        # Use smart selector if available, otherwise fallback to basic logic
        if self.smart_selector:
            return self.smart_selector.select_default_range(self.current_metric_type, context)
        elif self.availability_service:
            return self.availability_service.suggest_default_range(self.current_metric_type)
        else:
            return None
        
    def auto_select_best_range(self, context: SelectionContext = SelectionContext.STARTUP):
        """Automatically select the best available time range using smart selection.
        
        Args:
            context: Context for the selection
        """
        suggested_range = self.suggest_default_range(context)
        if suggested_range:
            self.select_range(suggested_range)
            self._track_range_selection(suggested_range, explicit=False, context=context)
            logger.info(f"Auto-selected range: {suggested_range.value} (context: {context.value})")
        else:
            # Clear selection if no good options
            checked_button = self.button_group.checkedButton()
            if checked_button:
                checked_button.setChecked(False)
                
    def _track_range_selection(self, range_type: TimeRange, explicit: bool = False, 
                              context: SelectionContext = SelectionContext.USER_INITIATED):
        """Track range selection for learning purposes.
        
        Args:
            range_type: The selected time range
            explicit: Whether user explicitly selected this range
            context: Context of the selection
        """
        try:
            if not self.smart_selector or not self.current_metric_type:
                return
                
            # End previous interaction tracking if any
            self._end_interaction_tracking()
            
            # Start new interaction tracking
            self.selection_start_time = datetime.now()
            self.interaction_actions = 0
            self.last_selected_range = range_type
            
            # Record the selection
            self.smart_selector.preference_tracker.record_selection(
                self.current_metric_type, range_type, 
                'manual' if explicit else 'auto',
                context.value
            )
            
            # Start interaction timer (tracks for 5 minutes max)
            self.interaction_timer.start(5 * 60 * 1000)
            
            logger.debug(f"Started tracking interaction for {range_type.value}")
            
        except Exception as e:
            logger.error(f"Error tracking range selection: {e}")
            
    def _end_interaction_tracking(self):
        """End current interaction tracking and record behavior."""
        try:
            if (self.smart_selector and self.current_metric_type and 
                self.last_selected_range and self.selection_start_time):
                
                # Calculate interaction duration
                duration = (datetime.now() - self.selection_start_time).total_seconds()
                
                # Record the interaction for learning
                interaction_data = {
                    'view_duration': duration,
                    'actions_taken': self.interaction_actions,
                    'manually_selected': True,  # We'll assume explicit for now
                    'context': 'view_session'
                }
                
                self.smart_selector.learn_from_behavior(
                    self.current_metric_type, self.last_selected_range, interaction_data
                )
                
                logger.debug(f"Recorded interaction: {duration:.1f}s, {self.interaction_actions} actions")
                
            # Reset tracking state
            self.selection_start_time = None
            self.interaction_actions = 0
            self.last_selected_range = None
            self.interaction_timer.stop()
            
        except Exception as e:
            logger.error(f"Error ending interaction tracking: {e}")
            
    def _on_interaction_timeout(self):
        """Handle interaction timer timeout."""
        logger.debug("Interaction timer timeout - ending tracking")
        self._end_interaction_tracking()
        
    def record_user_action(self):
        """Record a user action (scroll, click, export, etc.) for interaction tracking."""
        if self.selection_start_time:
            self.interaction_actions += 1
                
    def get_availability_summary(self) -> Dict[str, any]:
        """Get summary of current availability status."""
        return {
            'metric_type': self.current_metric_type,
            'available_ranges': [avail.range_type.value for avail in self.range_availabilities.values() if avail.available],
            'selected_range': self.get_selected_range().value if self.get_selected_range() else None,
            'total_available': len([avail for avail in self.range_availabilities.values() if avail.available])
        }
        
    def get_smart_selection_info(self) -> Dict[str, any]:
        """Get information about smart selection system."""
        if not self.smart_selector:
            return {"smart_selection_enabled": False}
            
        info = {"smart_selection_enabled": True}
        
        try:
            if self.current_metric_type:
                info.update({
                    "current_metric": self.current_metric_type,
                    "selection_weights": self.smart_selector.get_selection_weights(),
                    "statistics": self.smart_selector.get_selection_statistics(),
                    "top_preferences": self.smart_selector.preference_tracker.get_top_preferences(
                        self.current_metric_type, 3
                    )
                })
        except Exception as e:
            logger.error(f"Error getting smart selection info: {e}")
            info["error"] = str(e)
            
        return info
        
    def export_preferences(self) -> Dict[str, any]:
        """Export user preferences for backup."""
        if self.smart_selector:
            return self.smart_selector.export_preferences()
        return {}
        
    def import_preferences(self, preferences: Dict[str, any]):
        """Import user preferences from backup."""
        if self.smart_selector:
            self.smart_selector.import_preferences(preferences)
            
    def reset_preferences(self):
        """Reset all learned preferences."""
        if self.smart_selector:
            self.smart_selector.preference_tracker.reset_preferences()
            logger.info("Time range preferences reset")
            
    def cleanup(self):
        """Cleanup when widget is destroyed."""
        # End any active interaction tracking
        self._end_interaction_tracking()
        
        # Cleanup timers
        if hasattr(self, 'interaction_timer'):
            self.interaction_timer.stop()
            
        # Unregister callbacks
        if self.availability_service:
            self.availability_service.unregister_callback(self._on_availability_updated)