#!/usr/bin/env python3
"""Test script to verify the streamlined import flow."""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Run a minimal test of the import flow."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    logger.info("Main window created. Test the import flow:")
    logger.info("1. Go to File > Import...")
    logger.info("2. Select a valid CSV or XML file")
    logger.info("3. Import should start automatically after file selection")
    logger.info("4. Progress dialog should close automatically after completion")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()