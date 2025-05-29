"""
Keyboard navigation handler for accessible chart interactions.

Provides comprehensive keyboard shortcuts for all chart operations.
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent, QKeySequence
from typing import Dict, Any, Optional, Callable


class KeyboardNavigationHandler(QObject):
    """Handle keyboard navigation for charts"""
    
    # Signals
    action_triggered = pyqtSignal(str, object)  # action_name, data
    help_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Define keyboard shortcuts
        self.shortcuts = {
            # Zoom controls
            Qt.Key.Key_Plus: ('zoom_in', 'Zoom in'),
            Qt.Key.Key_Minus: ('zoom_out', 'Zoom out'),
            Qt.Key.Key_Equal: ('zoom_in', 'Zoom in'),  # For keyboards without numpad
            Qt.Key.Key_0: ('reset_zoom', 'Reset zoom to 100%'),
            
            # Pan controls
            Qt.Key.Key_Left: ('pan_left', 'Pan left'),
            Qt.Key.Key_Right: ('pan_right', 'Pan right'),
            Qt.Key.Key_Up: ('pan_up', 'Pan up'),
            Qt.Key.Key_Down: ('pan_down', 'Pan down'),
            
            # Navigation
            Qt.Key.Key_Home: ('go_to_start', 'Go to start of data'),
            Qt.Key.Key_End: ('go_to_end', 'Go to end of data'),
            Qt.Key.Key_PageUp: ('page_left', 'Page left'),
            Qt.Key.Key_PageDown: ('page_right', 'Page right'),
            
            # Selection
            Qt.Key.Key_A: ('select_all', 'Select all data', Qt.KeyboardModifier.ControlModifier),
            Qt.Key.Key_Escape: ('clear_selection', 'Clear selection'),
            
            # Data points
            Qt.Key.Key_Tab: ('next_point', 'Navigate to next data point'),
            Qt.Key.Key_Backtab: ('previous_point', 'Navigate to previous data point'),
            Qt.Key.Key_Return: ('select_point', 'Select current data point'),
            Qt.Key.Key_Enter: ('select_point', 'Select current data point'),
            
            # View controls
            Qt.Key.Key_F: ('fit_to_data', 'Fit view to data'),
            Qt.Key.Key_G: ('toggle_grid', 'Toggle grid'),
            Qt.Key.Key_L: ('toggle_legend', 'Toggle legend'),
            Qt.Key.Key_T: ('toggle_tooltips', 'Toggle tooltips'),
            
            # Export
            Qt.Key.Key_S: ('save_chart', 'Save chart', Qt.KeyboardModifier.ControlModifier),
            Qt.Key.Key_C: ('copy_chart', 'Copy chart to clipboard', Qt.KeyboardModifier.ControlModifier),
            
            # Help
            Qt.Key.Key_Question: ('show_help', 'Show keyboard shortcuts'),
            Qt.Key.Key_F1: ('show_help', 'Show help'),
        }
        
        # Current focus state
        self.focused_point_index = -1
        self.total_points = 0
        
        # Custom action handlers
        self.custom_handlers: Dict[str, Callable] = {}
        
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """
        Handle keyboard event and return True if handled.
        """
        key = event.key()
        modifiers = event.modifiers()
        
        # Check for shortcut match
        for shortcut_key, shortcut_info in self.shortcuts.items():
            if key == shortcut_key:
                if len(shortcut_info) == 3:
                    # Shortcut requires modifier
                    action, description, required_modifier = shortcut_info
                    if modifiers & required_modifier:
                        self._trigger_action(action, event)
                        return True
                else:
                    # No modifier required
                    action, description = shortcut_info
                    if modifiers == Qt.KeyboardModifier.NoModifier or action in ['zoom_in', 'zoom_out']:
                        self._trigger_action(action, event)
                        return True
                        
        # Handle numeric keys for quick zoom levels
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                zoom_level = key - Qt.Key.Key_0  # 1-9
                self._trigger_action('zoom_to_level', zoom_level)
                return True
                
        return False
        
    def _trigger_action(self, action: str, data: Any = None):
        """Trigger an action"""
        # Check for custom handler
        if action in self.custom_handlers:
            self.custom_handlers[action](data)
        else:
            # Emit signal for standard actions
            self.action_triggered.emit(action, data)
            
        # Special handling for help
        if action == 'show_help':
            self.help_requested.emit()
            
    def register_custom_handler(self, action: str, handler: Callable):
        """Register a custom handler for an action"""
        self.custom_handlers[action] = handler
        
    def set_data_points_count(self, count: int):
        """Set total number of data points for navigation"""
        self.total_points = count
        if self.focused_point_index >= count:
            self.focused_point_index = count - 1
            
    def navigate_to_point(self, index: int):
        """Navigate focus to a specific data point"""
        if 0 <= index < self.total_points:
            self.focused_point_index = index
            self._trigger_action('focus_point', index)
            
    def navigate_next_point(self):
        """Navigate to next data point"""
        if self.focused_point_index < self.total_points - 1:
            self.navigate_to_point(self.focused_point_index + 1)
            
    def navigate_previous_point(self):
        """Navigate to previous data point"""
        if self.focused_point_index > 0:
            self.navigate_to_point(self.focused_point_index - 1)
            
    def get_shortcuts_help(self) -> str:
        """Get formatted help text for keyboard shortcuts"""
        help_text = "Keyboard Shortcuts:\n\n"
        
        categories = {
            'Navigation': ['pan_left', 'pan_right', 'pan_up', 'pan_down', 
                          'go_to_start', 'go_to_end', 'page_left', 'page_right'],
            'Zoom': ['zoom_in', 'zoom_out', 'reset_zoom', 'fit_to_data'],
            'Selection': ['select_all', 'clear_selection', 'next_point', 
                         'previous_point', 'select_point'],
            'View': ['toggle_grid', 'toggle_legend', 'toggle_tooltips'],
            'Export': ['save_chart', 'copy_chart'],
            'Help': ['show_help']
        }
        
        for category, actions in categories.items():
            help_text += f"{category}:\n"
            
            for key, shortcut_info in self.shortcuts.items():
                action = shortcut_info[0]
                if action in actions:
                    key_name = QKeySequence(key).toString()
                    
                    if len(shortcut_info) == 3:
                        # Has modifier
                        modifier = shortcut_info[2]
                        if modifier == Qt.KeyboardModifier.ControlModifier:
                            key_name = f"Ctrl+{key_name}"
                        elif modifier == Qt.KeyboardModifier.ShiftModifier:
                            key_name = f"Shift+{key_name}"
                            
                    description = shortcut_info[1]
                    help_text += f"  {key_name:<20} {description}\n"
                    
            help_text += "\n"
            
        return help_text
        
    def is_navigation_key(self, key: int) -> bool:
        """Check if key is used for navigation"""
        navigation_keys = [
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
            Qt.Key.Key_Tab, Qt.Key.Key_Backtab
        ]
        return key in navigation_keys