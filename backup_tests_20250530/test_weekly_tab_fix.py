#!/usr/bin/env python3
"""
Test script to verify weekly tab fixes.
"""

import sys
import os
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt, QTimer

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.ui.main_window import MainWindow
from src.utils.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

def test_weekly_tab():
    """Test the weekly tab functionality."""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    # Create a timer to navigate to weekly tab after window is shown
    def navigate_to_weekly():
        logger.info("Navigating to weekly tab...")
        
        # Find the weekly tab index
        tab_widget = main_window.tab_widget
        weekly_index = -1
        
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i).lower() == "weekly":
                weekly_index = i
                break
        
        if weekly_index >= 0:
            logger.info(f"Found weekly tab at index {weekly_index}")
            tab_widget.setCurrentIndex(weekly_index)
            
            # Check if weekly dashboard exists
            if hasattr(main_window, 'weekly_dashboard'):
                logger.info("Weekly dashboard widget exists")
                
                # Try to trigger a refresh
                if hasattr(main_window, '_refresh_weekly_data'):
                    logger.info("Calling _refresh_weekly_data...")
                    main_window._refresh_weekly_data()
                else:
                    logger.warning("_refresh_weekly_data method not found")
            else:
                logger.error("Weekly dashboard widget not found")
        else:
            logger.error("Weekly tab not found")
    
    # Set timer to navigate after 1 second
    QTimer.singleShot(1000, navigate_to_weekly)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_weekly_tab()