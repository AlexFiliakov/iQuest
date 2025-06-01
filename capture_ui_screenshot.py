#!/usr/bin/env python3
"""
Capture UI screenshot using offscreen rendering for UI analysis.
"""

import sys
import os
from datetime import datetime

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Set Qt to use offscreen platform
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer

def capture_main_window():
    """Capture screenshot of main window."""
    app = QApplication(sys.argv)
    
    try:
        # Import after QApplication is created
        from ui.main_window import MainWindow
        from database import DatabaseManager
        
        # Create a mock database manager that doesn't connect
        class MockDatabaseManager:
            def __init__(self):
                pass
            def get_connection(self):
                return None
            def execute_query(self, *args, **kwargs):
                return []
            def insert_data(self, *args, **kwargs):
                pass
            def update_data(self, *args, **kwargs):
                pass
            def table_exists(self, *args):
                return False
        
        # Create main window with mock database
        window = MainWindow()
        window.show()
        
        # Ensure window is properly sized
        window.resize(1400, 900)
        
        # Schedule screenshot capture
        def take_screenshot():
            # Grab the window
            pixmap = window.grab()
            
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ui_screenshot_{timestamp}.png"
            pixmap.save(filename)
            print(f"Screenshot saved to: {filename}")
            
            # Close application
            app.quit()
        
        # Take screenshot after a short delay to ensure rendering
        QTimer.singleShot(1000, take_screenshot)
        
        app.exec()
        
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        # Try a simpler approach with just the configuration tab
        try:
            from ui.configuration_tab import ConfigurationTab
            tab = ConfigurationTab()
            tab.resize(1200, 800)
            tab.show()
            
            def take_tab_screenshot():
                pixmap = tab.grab()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"configuration_tab_screenshot_{timestamp}.png"
                pixmap.save(filename)
                print(f"Configuration tab screenshot saved to: {filename}")
                app.quit()
            
            QTimer.singleShot(1000, take_tab_screenshot)
            app.exec()
            
        except Exception as e2:
            print(f"Error capturing configuration tab: {e2}")

if __name__ == "__main__":
    capture_main_window()