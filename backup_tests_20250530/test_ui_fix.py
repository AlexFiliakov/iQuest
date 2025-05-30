#!/usr/bin/env python3
"""Test script to verify the UI loads without the setColor error."""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Test if the main window loads without errors."""
    app = QApplication(sys.argv)
    
    try:
        # Create main window
        logger.info("Creating main window...")
        window = MainWindow()
        logger.info("Main window created successfully!")
        
        # Show window
        window.show()
        logger.info("Main window displayed successfully!")
        
        # Don't run the app, just check if it loads
        logger.info("UI loaded without errors. Test passed!")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create main window: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())