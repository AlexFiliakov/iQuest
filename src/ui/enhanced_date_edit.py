"""Enhanced QDateEdit with explicit arrow key navigation support."""

from PyQt6.QtWidgets import QDateEdit
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QKeyEvent

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedDateEdit(QDateEdit):
    """QDateEdit with enhanced keyboard navigation using arrow keys."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Enable keyboard tracking and calendar popup
        self.setKeyboardTracking(True)
        self.setCalendarPopup(True)
        
        logger.debug("EnhancedDateEdit initialized with arrow key navigation")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events with enhanced arrow key navigation."""
        key = event.key()
        modifiers = event.modifiers()
        current_date = self.date()
        
        # Handle arrow key navigation for day/week/month changes
        if key == Qt.Key.Key_Left:
            # Left arrow: Previous day
            new_date = current_date.addDays(-1)
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to previous day ({new_date.toString('yyyy-MM-dd')})")
            return
            
        elif key == Qt.Key.Key_Right:
            # Right arrow: Next day
            new_date = current_date.addDays(1)
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to next day ({new_date.toString('yyyy-MM-dd')})")
            return
            
        elif key == Qt.Key.Key_Up:
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Up: Previous month
                new_date = current_date.addMonths(-1)
                self.setDate(new_date)
                logger.debug(f"Arrow key navigation: moved to previous month ({new_date.toString('yyyy-MM-dd')})")
                return
            else:
                # Up arrow: Previous week
                new_date = current_date.addDays(-7)
                self.setDate(new_date)
                logger.debug(f"Arrow key navigation: moved to previous week ({new_date.toString('yyyy-MM-dd')})")
                return
                
        elif key == Qt.Key.Key_Down:
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+Down: Next month
                new_date = current_date.addMonths(1)
                self.setDate(new_date)
                logger.debug(f"Arrow key navigation: moved to next month ({new_date.toString('yyyy-MM-dd')})")
                return
            else:
                # Down arrow: Next week
                new_date = current_date.addDays(7)
                self.setDate(new_date)
                logger.debug(f"Arrow key navigation: moved to next week ({new_date.toString('yyyy-MM-dd')})")
                return
        
        # Handle other special keys
        elif key == Qt.Key.Key_Home:
            # Home: First day of current month
            new_date = QDate(current_date.year(), current_date.month(), 1)
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to first day of month ({new_date.toString('yyyy-MM-dd')})")
            return
            
        elif key == Qt.Key.Key_End:
            # End: Last day of current month
            new_date = QDate(current_date.year(), current_date.month(), current_date.daysInMonth())
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to last day of month ({new_date.toString('yyyy-MM-dd')})")
            return
            
        elif key == Qt.Key.Key_PageUp:
            # Page Up: Previous month
            new_date = current_date.addMonths(-1)
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to previous month ({new_date.toString('yyyy-MM-dd')})")
            return
            
        elif key == Qt.Key.Key_PageDown:
            # Page Down: Next month
            new_date = current_date.addMonths(1)
            self.setDate(new_date)
            logger.debug(f"Arrow key navigation: moved to next month ({new_date.toString('yyyy-MM-dd')})")
            return
        
        # Fall back to default behavior for other keys
        super().keyPressEvent(event)
    
    def setAccessibleName(self, name: str):
        """Set accessible name for screen readers."""
        super().setAccessibleName(name)
        
    def setAccessibleDescription(self, description: str):
        """Set accessible description for screen readers."""
        super().setAccessibleDescription(description)
        
    def setToolTip(self, tooltip: str):
        """Set enhanced tooltip with keyboard navigation hints."""
        enhanced_tooltip = f"{tooltip}\n\nKeyboard Navigation:\n" \
                          "• Left/Right arrows: Previous/Next day\n" \
                          "• Up/Down arrows: Previous/Next week\n" \
                          "• Ctrl+Up/Down: Previous/Next month\n" \
                          "• Home/End: First/Last day of month\n" \
                          "• Page Up/Down: Previous/Next month"
        super().setToolTip(enhanced_tooltip)