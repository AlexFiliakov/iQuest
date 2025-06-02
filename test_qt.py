#!/usr/bin/env python3
"""Test if Qt is working properly in WSL."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt, QTimer

def main():
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    
    print("Creating window...")
    window = QMainWindow()
    window.setWindowTitle("Qt Test")
    window.setGeometry(100, 100, 400, 300)
    
    label = QLabel("Qt is working!", window)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)
    
    print("Showing window...")
    window.show()
    
    # Auto-close after 2 seconds for testing
    QTimer.singleShot(2000, app.quit)
    
    print("Starting event loop...")
    result = app.exec()
    print(f"Application exited with code: {result}")
    return result

if __name__ == "__main__":
    sys.exit(main())