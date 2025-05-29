#!/usr/bin/env python3
"""Direct test of calendar heatmap fixes."""

import sys
import os
from datetime import date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

# Import directly
from src.ui.charts.calendar_heatmap import CalendarHeatmap, ViewMode

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Heatmap Test - GitHub Style")
        self.setGeometry(100, 100, 1400, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create calendar heatmap
        self.heatmap = CalendarHeatmap()
        layout.addWidget(self.heatmap)
        
        # Generate test data for the last 365 days
        test_data = {}
        today = date.today()
        for i in range(365):
            day = today - timedelta(days=i)
            # Generate varying values with some patterns
            base_value = 5000 + random.randint(-2000, 3000)
            if day.weekday() in [5, 6]:  # Weekends
                base_value *= 1.2
            # Add some gaps to test empty cells
            if random.random() > 0.9:
                continue
            test_data[day] = base_value
            
        # Set data and configure
        self.heatmap.set_metric_data(test_data, "Steps")
        self.heatmap.set_view_mode(ViewMode.GITHUB_STYLE)
        self.heatmap.toggle_today_marker(True)
        
        # Timer to update animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.heatmap.update_animation)
        self.timer.start(50)  # 20 FPS

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("Calendar heatmap test window opened.")
    print("The GitHub-style view should show:")
    print("- Last 52 weeks of data in a grid")
    print("- Proper spacing between cells")
    print("- Today's date highlighted with a pulsing border")
    print("- Month labels at the top")
    print("- Day labels on the left")
    
    sys.exit(app.exec())