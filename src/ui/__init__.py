"""UI package for Apple Health Monitor Dashboard.

This module provides comprehensive user interface components for the health monitoring
application, including the main window, visualization widgets, charts, and comprehensive
accessibility features for WCAG 2.1 AA compliance.

The UI package is organized into several key areas:

- **Main Interface**: Primary application window and navigation
- **Visualization Components**: Health data charts and interactive displays  
- **Configuration**: Settings, preferences, and adaptive controls
- **Data Display**: Tables, statistics, and summary widgets
- **Accessibility**: Screen reader support, keyboard navigation, high contrast themes

Example:
    Basic application startup:
    
    >>> from ui import MainWindow
    >>> app = QApplication(sys.argv)
    >>> window = MainWindow()
    >>> window.show()
    >>> sys.exit(app.exec_())

The package follows Material Design principles and provides both light and dark
themes with extensive customization options for users with different accessibility needs.
"""

from .main_window import MainWindow

# Import accessibility module
from . import accessibility

__all__ = ['MainWindow', 'accessibility']