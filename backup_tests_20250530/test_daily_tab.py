#!/usr/bin/env python3
"""Test script to verify Daily tab data loading."""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    print("\n=== Test Instructions ===")
    print("1. Go to Configuration tab and import data")
    print("2. Click on the Daily tab")
    print("3. Check if data is displayed")
    print("4. Check the console for any error messages")
    print("\nWatch the console for logging messages...")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()