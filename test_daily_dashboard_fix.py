"""Test script to debug daily dashboard initialization."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import setup_logging

def test_daily_dashboard():
    """Test daily dashboard initialization."""
    setup_logging()
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    
    # Check if daily dashboard was created
    if hasattr(window, 'daily_dashboard'):
        print("✓ Daily dashboard created successfully")
        
        # Check critical attributes
        dd = window.daily_dashboard
        print(f"  - daily_calculator: {dd.daily_calculator}")
        print(f"  - data_access: {dd.data_access if hasattr(dd, 'data_access') else 'Not set'}")
        print(f"  - health_db: {dd.health_db if hasattr(dd, 'health_db') else 'Not set'}")
        print(f"  - cached_data_access: {dd.cached_data_access if hasattr(dd, 'cached_data_access') else 'Not set'}")
        
        # Check if it's the actual widget or placeholder
        if hasattr(dd, '_load_daily_data'):
            print("✓ This is the actual DailyDashboardWidget")
        else:
            print("✗ This is a placeholder widget")
    else:
        print("✗ Daily dashboard not created")
    
    # Check tab count
    print(f"\nTotal tabs: {window.tab_widget.count()}")
    for i in range(window.tab_widget.count()):
        print(f"  Tab {i}: {window.tab_widget.tabText(i)}")
    
    window.close()
    
if __name__ == "__main__":
    test_daily_dashboard()