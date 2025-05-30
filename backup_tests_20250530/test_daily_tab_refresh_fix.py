#!/usr/bin/env python3
"""Test script to verify Daily tab refresh fix."""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Run the test to verify Daily tab refresh."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Test instructions
    print("\n" + "="*50)
    print("Daily Tab Refresh Test")
    print("="*50)
    print("\nInstructions:")
    print("1. Switch between tabs (Config, Daily, Weekly, Monthly)")
    print("2. Check that the Daily tab refreshes properly")
    print("3. Verify that no visuals from other tabs persist")
    print("4. Confirm that Daily information is displayed correctly")
    print("\nExpected behavior:")
    print("- Daily tab should clear and redraw when switching to it")
    print("- No content from other tabs should remain visible")
    print("- Daily metrics and charts should display properly")
    print("="*50 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()