"""
Qt configuration for consistent visual testing.
Ensures reproducible rendering across different platforms and environments.
"""

import os
import sys
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QGuiApplication, QFontDatabase
from PyQt6.QtWidgets import QApplication


class VisualTestConfig:
    """Configure Qt for consistent visual testing."""
    
    @staticmethod
    def setup_qt_for_testing():
        """Configure Qt for reproducible rendering."""
        # Force software rendering for consistency
        os.environ['QT_QUICK_BACKEND'] = 'software'
        os.environ['QSG_RHI_BACKEND'] = 'software'
        
        # Disable animations and scaling
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
        
        # Set consistent DPI
        os.environ['QT_FONT_DPI'] = '96'
        
        # Disable high DPI scaling
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
        
        # Create application if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Configure application for consistent rendering
        app.setStyle('Fusion')  # Consistent cross-platform style
        app.setApplicationName('HealthMonitorVisualTest')
        
        # Load consistent fonts
        VisualTestConfig._load_test_fonts()
        
        return app
    
    @staticmethod
    def _load_test_fonts():
        """Load consistent fonts for testing."""
        # Try to load system fonts consistently
        # This helps ensure text rendering is similar across platforms
        font_db = QFontDatabase()
        
        # Add system fonts that are commonly available
        font_families = [
            'Arial', 'Helvetica', 'Sans Serif', 'DejaVu Sans'
        ]
        
        for family in font_families:
            if font_db.hasFamily(family):
                break
        
        # Set default font properties for consistency
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setFamily('Arial')  # Fall back to Arial
            font.setPointSize(10)
            app.setFont(font)