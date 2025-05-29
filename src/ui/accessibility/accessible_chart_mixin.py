"""
Mixin class to add accessibility features to chart components.

This provides an easy way to make existing charts accessible.
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QKeyEvent

from .accessibility_manager import VisualizationAccessibilityManager
from .keyboard_navigation import KeyboardNavigationManager
from ..charts.wsj_style_manager import WSJStyleManager
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class AccessibleChartMixin:
    """
    Mixin to add accessibility features to chart widgets.
    
    Usage:
        class MyChart(BaseChart, AccessibleChartMixin):
            def __init__(self):
                BaseChart.__init__(self)
                AccessibleChartMixin.__init__(self)
    """
    
    # Accessibility-specific signals
    accessibility_announcement = pyqtSignal(str)
    focus_changed = pyqtSignal(str)  # element description
    
    def __init__(self):
        """Initialize accessibility features."""
        # Flag to track if accessibility is enabled
        self._accessibility_enabled = False
        self._high_contrast_mode = False
        self._current_focus_index = 0
        self._focusable_elements = []
        
        # Accessibility manager (lazy loaded)
        self._accessibility_manager = None
        
        # Set up basic accessibility
        self._setup_basic_accessibility()
        
        logger.debug("AccessibleChartMixin initialized")
    
    def _setup_basic_accessibility(self):
        """Set up basic accessibility features."""
        # Make widget focusable
        if hasattr(self, 'setFocusPolicy'):
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set basic accessible properties
        if hasattr(self, 'setAccessibleName'):
            self.setAccessibleName(self.get_accessible_name())
        
        if hasattr(self, 'setAccessibleDescription'):
            self.setAccessibleDescription(self.get_accessible_description())
    
    def enable_accessibility(self, full_features: bool = True):
        """Enable accessibility features."""
        if self._accessibility_enabled:
            return
        
        try:
            if full_features:
                # Initialize full accessibility manager
                theme_manager = WSJStyleManager()
                self._accessibility_manager = VisualizationAccessibilityManager(theme_manager)
                
                # Make chart accessible
                chart_config = {
                    'type': self.get_chart_type(),
                    'title': self.get_accessible_name()
                }
                
                self._accessibility_manager.make_chart_accessible(self, chart_config)
            
            self._accessibility_enabled = True
            logger.info("Accessibility enabled for chart")
            
        except Exception as e:
            logger.error(f"Error enabling accessibility: {e}")
    
    def get_accessible_name(self) -> str:
        """Get accessible name for the chart."""
        if hasattr(self, '_title') and self._title:
            return self._title
        return "Health Data Chart"
    
    def get_accessible_description(self) -> str:
        """Get accessible description."""
        parts = []
        
        if hasattr(self, '_subtitle') and self._subtitle:
            parts.append(self._subtitle)
        
        if hasattr(self, '_data') and self._data:
            parts.append(f"Displaying {len(self._data)} data points")
        
        return ". ".join(parts) if parts else "Chart visualization"
    
    def get_chart_type(self) -> str:
        """Get chart type for accessibility."""
        return self.__class__.__name__.replace('Chart', '').lower()
    
    def get_data_summary(self) -> str:
        """Get summary of chart data for screen readers."""
        if not hasattr(self, '_data') or not self._data:
            return "No data available"
        
        # This should be overridden by specific chart types
        return f"Chart contains {len(self._data)} data points"
    
    def get_key_insights(self) -> List[str]:
        """Get key insights from the chart."""
        # This should be overridden by specific chart types
        return []
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events for accessibility."""
        if not self._accessibility_enabled:
            # Call parent implementation if exists
            if hasattr(super(), 'keyPressEvent'):
                super().keyPressEvent(event)
            return
        
        key = event.key()
        handled = False
        
        # Navigation keys
        if key == Qt.Key.Key_Left:
            handled = self.navigate_previous()
        elif key == Qt.Key.Key_Right:
            handled = self.navigate_next()
        elif key == Qt.Key.Key_Home:
            handled = self.navigate_first()
        elif key == Qt.Key.Key_End:
            handled = self.navigate_last()
        elif key == Qt.Key.Key_A:
            handled = self.announce_current()
        elif key == Qt.Key.Key_S:
            handled = self.toggle_sonification()
        elif key == Qt.Key.Key_T:
            handled = self.show_data_table()
        
        if handled:
            event.accept()
        else:
            # Call parent implementation if exists
            if hasattr(super(), 'keyPressEvent'):
                super().keyPressEvent(event)
    
    def navigate_previous(self) -> bool:
        """Navigate to previous data point."""
        if self._current_focus_index > 0:
            self._current_focus_index -= 1
            self._update_focus()
            return True
        return False
    
    def navigate_next(self) -> bool:
        """Navigate to next data point."""
        if hasattr(self, '_data') and self._current_focus_index < len(self._data) - 1:
            self._current_focus_index += 1
            self._update_focus()
            return True
        return False
    
    def navigate_first(self) -> bool:
        """Navigate to first data point."""
        self._current_focus_index = 0
        self._update_focus()
        return True
    
    def navigate_last(self) -> bool:
        """Navigate to last data point."""
        if hasattr(self, '_data'):
            self._current_focus_index = len(self._data) - 1
            self._update_focus()
            return True
        return False
    
    def announce_current(self) -> bool:
        """Announce current focused element."""
        if hasattr(self, '_data') and self._current_focus_index < len(self._data):
            announcement = self._create_element_announcement(self._current_focus_index)
            self.accessibility_announcement.emit(announcement)
            logger.debug(f"Announced: {announcement}")
            return True
        return False
    
    def toggle_high_contrast(self) -> bool:
        """Toggle high contrast mode."""
        self._high_contrast_mode = not self._high_contrast_mode
        
        if hasattr(self, 'update'):
            self.update()
        
        announcement = f"High contrast mode {'enabled' if self._high_contrast_mode else 'disabled'}"
        self.accessibility_announcement.emit(announcement)
        
        return True
    
    def toggle_sonification(self) -> bool:
        """Toggle sonification (audio representation) of data."""
        if hasattr(self, '_sonification_enabled'):
            self._sonification_enabled = not self._sonification_enabled
        else:
            self._sonification_enabled = True
        
        if self._sonification_enabled and self._accessibility_manager:
            # Trigger sonification through accessibility manager
            logger.info("Sonification enabled - audio representation will play")
            announcement = "Sonification enabled. Press S again to disable."
        else:
            logger.info("Sonification disabled")
            announcement = "Sonification disabled"
        
        self.accessibility_announcement.emit(announcement)
        return True
    
    def show_data_table(self) -> bool:
        """Show data table representation."""
        if self._accessibility_manager:
            # This would show the data table
            logger.info("Showing data table view")
            return True
        return False
    
    def get_high_contrast_colors(self) -> Dict[str, str]:
        """Get high contrast color scheme."""
        return {
            'background': '#FFFFFF',
            'foreground': '#000000',
            'primary': '#0066CC',
            'secondary': '#FF6600',
            'positive': '#008800',
            'negative': '#CC0000',
            'grid': '#666666'
        }
    
    def supports_high_contrast(self) -> bool:
        """Check if chart supports high contrast mode."""
        return True
    
    def has_pattern_coding(self) -> bool:
        """Check if chart has pattern coding as alternative to color."""
        # Can be overridden by specific charts
        return False
    
    def shows_units(self) -> bool:
        """Check if chart shows measurement units."""
        # Should be overridden by specific charts
        return True
    
    def shows_normal_ranges(self) -> bool:
        """Check if chart shows normal ranges for health metrics."""
        # Should be overridden by specific charts
        return False
    
    def has_focus_indicators(self) -> bool:
        """Check if chart has visible focus indicators."""
        return True
    
    def _update_focus(self):
        """Update focus to current element."""
        announcement = self._create_element_announcement(self._current_focus_index)
        self.focus_changed.emit(announcement)
        
        # Trigger visual update
        if hasattr(self, 'update'):
            self.update()
    
    def _create_element_announcement(self, index: int) -> str:
        """Create announcement for element at index."""
        if not hasattr(self, '_data') or index >= len(self._data):
            return "No data"
        
        # This should be overridden by specific chart types
        data_point = self._data[index]
        return f"Data point {index + 1} of {len(self._data)}"
    
    def get_current_description(self) -> str:
        """Get description of currently focused element."""
        return self._create_element_announcement(self._current_focus_index)