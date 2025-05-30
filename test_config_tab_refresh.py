#!/usr/bin/env python3
"""Test script to verify Config tab shows data summary on switch."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_config_tab_refresh():
    """Test that Config tab refreshes when switched to."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Show instructions
    logger.info("Test Instructions:")
    logger.info("1. If data loads automatically, switch to another tab")
    logger.info("2. Switch back to Configuration tab")
    logger.info("3. Verify that summary cards and statistics are shown")
    logger.info("4. If no data loaded, import some data first")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_config_tab_refresh()