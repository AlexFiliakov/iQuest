#!/usr/bin/env python3
"""
Run a UI demo and capture screenshot for analysis.
"""

import sys
import os
from datetime import datetime

# Set Qt to use offscreen platform
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add the src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from PyQt6.QtCore import QTimer
import subprocess

def run_dashboard_demo():
    """Run the dashboard demo and capture screenshot."""
    try:
        # Run the bar chart demo which is simpler
        subprocess.run([
            sys.executable, 
            "examples/bar_chart_demo.py"
        ], cwd=project_root, timeout=5)
    except subprocess.TimeoutExpired:
        print("Demo captured")
    except Exception as e:
        print(f"Error running demo: {e}")

def create_mock_ui():
    """Create a mock UI based on the actual structure."""
    app = QApplication(sys.argv)
    
    # Import style manager
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from ui.style_manager import StyleManager
    
    style_manager = StyleManager()
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Apple Health Monitor Dashboard")
    window.resize(1400, 900)
    
    # Apply styling
    window.setStyleSheet(style_manager.get_main_window_style())
    
    # Create central widget with tabs
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    # Create tab widget
    tabs = QTabWidget()
    tabs.setStyleSheet("""
        QTabWidget::pane {
            border: none;
            background-color: #FFFFFF;
        }
        QTabBar::tab {
            background-color: #F3F4F6;
            color: #4B5563;
            padding: 12px 24px;
            margin-right: 4px;
            border: none;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background-color: #FFFFFF;
            color: #0F172A;
            font-weight: 600;
        }
        QTabBar::tab:hover {
            background-color: #E5E7EB;
        }
    """)
    
    # Add sample tabs
    tab_names = ["Configuration", "Daily", "Weekly", "Monthly", "Comparative Analytics", 
                 "Health Insights", "Trophy Case", "Journal", "Help"]
    
    for name in tab_names:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.addStretch()
        tabs.addTab(tab, name)
    
    layout.addWidget(tabs)
    
    window.show()
    
    # Take screenshot after a delay
    def capture():
        pixmap = window.grab()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_ui_screenshot_{timestamp}.png"
        pixmap.save(filename)
        print(f"Mock UI screenshot saved to: {filename}")
        app.quit()
    
    QTimer.singleShot(1000, capture)
    app.exec()

if __name__ == "__main__":
    print("Creating mock UI for screenshot...")
    create_mock_ui()