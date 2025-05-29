"""
Keyboard navigation support for health visualizations.

Provides comprehensive keyboard controls for all chart interactions.
"""

from typing import Dict, Callable, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QEvent
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QKeyEvent

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class KeyboardNavigationManager(QObject):
    """Manages keyboard navigation for visualizations."""
    
    # Signals
    navigation_event = pyqtSignal(str, dict)  # action, context
    shortcut_activated = pyqtSignal(str)  # shortcut_name
    
    # Default keyboard shortcuts
    DEFAULT_SHORTCUTS = {
        # Navigation
        Qt.Key.Key_Tab: 'next_element',
        Qt.Key.Key_Backtab: 'previous_element',  # Shift+Tab
        Qt.Key.Key_Left: 'navigate_left',
        Qt.Key.Key_Right: 'navigate_right',
        Qt.Key.Key_Up: 'navigate_up',
        Qt.Key.Key_Down: 'navigate_down',
        Qt.Key.Key_Home: 'go_to_start',
        Qt.Key.Key_End: 'go_to_end',
        Qt.Key.Key_PageUp: 'previous_period',
        Qt.Key.Key_PageDown: 'next_period',
        
        # Activation
        Qt.Key.Key_Return: 'activate',
        Qt.Key.Key_Enter: 'activate',
        Qt.Key.Key_Space: 'toggle_selection',
        
        # Accessibility features
        Qt.Key.Key_A: 'announce_current',
        Qt.Key.Key_S: 'toggle_sonification',
        Qt.Key.Key_T: 'show_data_table',
        Qt.Key.Key_H: 'show_help',
        
        # Exit
        Qt.Key.Key_Escape: 'exit_focus'
    }
    
    def __init__(self):
        super().__init__()
        self.handlers = {}
        self.current_focus_widget = None
        self.navigation_mode = 'browse'
        
        logger.info("Initialized KeyboardNavigationManager")
    
    def get_default_shortcuts(self) -> Dict[str, str]:
        """Get human-readable default shortcuts."""
        readable = {}
        key_names = {
            Qt.Key.Key_Tab: 'Tab',
            Qt.Key.Key_Backtab: 'Shift+Tab',
            Qt.Key.Key_Left: 'Left Arrow',
            Qt.Key.Key_Right: 'Right Arrow',
            Qt.Key.Key_Up: 'Up Arrow',
            Qt.Key.Key_Down: 'Down Arrow',
            Qt.Key.Key_Home: 'Home',
            Qt.Key.Key_End: 'End',
            Qt.Key.Key_PageUp: 'Page Up',
            Qt.Key.Key_PageDown: 'Page Down',
            Qt.Key.Key_Return: 'Enter',
            Qt.Key.Key_Space: 'Space',
            Qt.Key.Key_Escape: 'Escape',
            Qt.Key.Key_A: 'A',
            Qt.Key.Key_S: 'S',
            Qt.Key.Key_T: 'T',
            Qt.Key.Key_H: 'H'
        }
        
        for key, action in self.DEFAULT_SHORTCUTS.items():
            if key in key_names:
                readable[key_names[key]] = action.replace('_', ' ').title()
        
        return readable
    
    def install_handler(self, widget: QWidget, 
                       shortcuts: Optional[Dict[str, str]] = None) -> None:
        """Install keyboard handler on widget."""
        try:
            # Use default shortcuts if none provided
            if shortcuts is None:
                shortcuts = self.get_default_shortcuts()
            
            # Store handler reference
            widget_id = id(widget)
            self.handlers[widget_id] = {
                'widget': widget,
                'shortcuts': shortcuts,
                'original_event_filter': widget.eventFilter
            }
            
            # Install event filter
            widget.installEventFilter(self)
            
            # Make widget focusable
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            logger.debug(f"Installed keyboard handler on widget: {widget}")
            
        except Exception as e:
            logger.error(f"Error installing keyboard handler: {e}")
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter keyboard events for navigation."""
        if event.type() == QEvent.Type.KeyPress:
            return self._handle_key_press(obj, event)
        elif event.type() == QEvent.Type.FocusIn:
            self._handle_focus_in(obj)
        elif event.type() == QEvent.Type.FocusOut:
            self._handle_focus_out(obj)
        
        return False
    
    def _handle_key_press(self, widget: QWidget, event: QKeyEvent) -> bool:
        """Handle key press events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle Shift+Tab specially
        if key == Qt.Key.Key_Tab and modifiers & Qt.KeyboardModifier.ShiftModifier:
            key = Qt.Key.Key_Backtab
        
        # Check if we have a handler for this key
        if key in self.DEFAULT_SHORTCUTS:
            action = self.DEFAULT_SHORTCUTS[key]
            
            # Emit signal
            self.shortcut_activated.emit(action)
            
            # Handle the action
            handled = self._execute_action(widget, action, event)
            
            if handled:
                event.accept()
                return True
        
        return False
    
    def _execute_action(self, widget: QWidget, action: str, 
                       event: QKeyEvent) -> bool:
        """Execute keyboard action."""
        try:
            context = {
                'widget': widget,
                'key': event.key(),
                'modifiers': event.modifiers()
            }
            
            # Emit navigation event
            self.navigation_event.emit(action, context)
            
            # Handle common actions
            if action == 'announce_current':
                return self._announce_current_element(widget)
            elif action == 'show_help':
                return self._show_keyboard_help(widget)
            elif action == 'toggle_high_contrast':
                return self._toggle_high_contrast(widget)
            elif action == 'show_data_table':
                return self._show_data_table(widget)
            
            # Delegate to widget-specific handlers
            if hasattr(widget, f'handle_{action}'):
                handler = getattr(widget, f'handle_{action}')
                return handler()
            
            # Default navigation handling
            if action in ['navigate_left', 'navigate_right', 'navigate_up', 'navigate_down']:
                return self._handle_navigation(widget, action)
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing keyboard action '{action}': {e}")
            return False
    
    def _handle_navigation(self, widget: QWidget, direction: str) -> bool:
        """Handle directional navigation."""
        if hasattr(widget, 'navigate'):
            direction_map = {
                'navigate_left': 'left',
                'navigate_right': 'right',
                'navigate_up': 'up',
                'navigate_down': 'down'
            }
            return widget.navigate(direction_map.get(direction, 'right'))
        
        return False
    
    def _announce_current_element(self, widget: QWidget) -> bool:
        """Announce current element to screen reader."""
        if hasattr(widget, 'get_current_description'):
            description = widget.get_current_description()
            # This would integrate with screen reader
            logger.info(f"Announcing: {description}")
            return True
        
        return False
    
    def _show_keyboard_help(self, widget: QWidget) -> bool:
        """Show keyboard shortcuts help."""
        # This would show a help dialog
        logger.info("Showing keyboard help")
        return True
    
    def _toggle_high_contrast(self, widget: QWidget) -> bool:
        """Toggle high contrast mode."""
        if hasattr(widget, 'toggle_high_contrast'):
            widget.toggle_high_contrast()
            return True
        
        return False
    
    def _show_data_table(self, widget: QWidget) -> bool:
        """Show data table view."""
        if hasattr(widget, 'show_data_table'):
            widget.show_data_table()
            return True
        
        return False
    
    def _handle_focus_in(self, widget: QWidget) -> None:
        """Handle focus in event."""
        self.current_focus_widget = widget
        logger.debug(f"Focus entered widget: {widget}")
        
        # Announce widget context
        if hasattr(widget, 'announce_focus'):
            widget.announce_focus()
    
    def _handle_focus_out(self, widget: QWidget) -> None:
        """Handle focus out event."""
        if self.current_focus_widget == widget:
            self.current_focus_widget = None
        
        logger.debug(f"Focus left widget: {widget}")
    
    def set_navigation_mode(self, mode: str) -> None:
        """Set navigation mode (browse, focus, form)."""
        self.navigation_mode = mode
        logger.info(f"Navigation mode set to: {mode}")
    
    def get_shortcut_description(self, action: str) -> str:
        """Get human-readable description of shortcut."""
        descriptions = {
            'next_element': 'Move to next element',
            'previous_element': 'Move to previous element',
            'navigate_left': 'Navigate left / Previous data point',
            'navigate_right': 'Navigate right / Next data point',
            'navigate_up': 'Navigate up / Increase value',
            'navigate_down': 'Navigate down / Decrease value',
            'go_to_start': 'Go to first data point',
            'go_to_end': 'Go to last data point',
            'previous_period': 'Previous time period',
            'next_period': 'Next time period',
            'activate': 'Activate / Select',
            'toggle_selection': 'Toggle selection',
            'announce_current': 'Announce current value',
            'toggle_sonification': 'Toggle audio representation',
            'show_data_table': 'Show data as table',
            'show_help': 'Show keyboard shortcuts',
            'toggle_high_contrast': 'Toggle high contrast mode',
            'zoom_in': 'Zoom in',
            'zoom_out': 'Zoom out',
            'reset_zoom': 'Reset zoom',
            'export_data': 'Export data',
            'exit_focus': 'Exit chart focus'
        }
        
        return descriptions.get(action, action.replace('_', ' ').title())