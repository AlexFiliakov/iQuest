#!/usr/bin/env python3
"""Test script for the loading screen implementation."""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.insert(0, '.')

from src.ui.loading_screen import LoadingScreen


def test_loading_screen():
    """Test the loading screen with sample messages."""
    app = QApplication(sys.argv)
    
    loading_screen = LoadingScreen()
    loading_screen.show()
    
    # Simulate initialization messages
    messages = [
        ("Initializing application...", 0.1),
        ("Loading configuration files...", 0.2),
        ("Connecting to database...", 0.3),
        ("Setting up analytics engine...", 0.4),
        ("Loading user interface components...", 0.5),
        ("Initializing visualization system...", 0.6),
        ("Preparing dashboard widgets...", 0.7),
        ("Finalizing setup...", 0.8),
        ("Almost ready...", 0.9),
        ("Application ready!", 1.0)
    ]
    
    def add_next_message(index=0):
        if index < len(messages):
            msg, progress = messages[index]
            loading_screen.add_message(msg)
            loading_screen.set_progress(progress)
            QTimer.singleShot(500, lambda: add_next_message(index + 1))
        else:
            # Close after a short delay
            QTimer.singleShot(1000, loading_screen.close)
            QTimer.singleShot(1500, app.quit)
    
    # Start adding messages
    QTimer.singleShot(100, lambda: add_next_message())
    
    app.exec()


if __name__ == "__main__":
    test_loading_screen()