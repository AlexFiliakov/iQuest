#!/usr/bin/env python3
"""Demo script to showcase UI improvements."""

import sys
import os
from datetime import datetime

# Set Qt to use offscreen platform for WSL
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap

def create_improved_ui():
    """Create the improved UI demo."""
    app = QApplication(sys.argv)
    
    # Import necessary modules
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from src.ui.style_manager import StyleManager
    from src.ui.configuration_tab_improved import ImprovedConfigurationTab
    
    # Initialize style manager
    style_manager = StyleManager()
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Apple Health Monitor Dashboard - UI Improvements Demo")
    window.resize(1400, 900)
    
    # Apply global styles
    style_manager.apply_global_style(app)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Create tab widget with improved styling
    tabs = QTabWidget()
    tabs.setStyleSheet(style_manager.get_main_window_style())
    
    # Add improved configuration tab
    config_tab = ImprovedConfigurationTab()
    tabs.addTab(config_tab, "Configuration")
    
    # Add placeholder tabs to show tab styling
    for name in ["Daily", "Weekly", "Monthly", "Compare", "Insights", "Records", "Journal", "Help"]:
        placeholder = QWidget()
        tabs.addTab(placeholder, name)
    
    layout.addWidget(tabs)
    
    # Show the window
    window.show()
    
    # Schedule screenshot capture
    def capture_screenshot():
        pixmap = window.grab()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"improved_ui_screenshot_{timestamp}.png"
        pixmap.save(filename)
        print(f"Screenshot saved to: {filename}")
        
        # Also save to ad hoc directory
        ad_hoc_path = os.path.join(project_root, "ad hoc", filename)
        os.makedirs(os.path.dirname(ad_hoc_path), exist_ok=True)
        pixmap.save(ad_hoc_path)
        print(f"Screenshot also saved to: {ad_hoc_path}")
        
        app.quit()
    
    QTimer.singleShot(2000, capture_screenshot)
    
    return app.exec()

if __name__ == "__main__":
    print("Creating improved UI demo...")
    create_improved_ui()