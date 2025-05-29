#!/usr/bin/env python3
"""Test script for the updated Daily dashboard tab."""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Switch to Daily tab
    window.tab_widget.setCurrentIndex(1)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()