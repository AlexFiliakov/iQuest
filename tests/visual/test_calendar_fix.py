#!/usr/bin/env python3
"""Test script to visualize the calendar heatmap fixes."""

import sys
from datetime import date, timedelta
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

# Add src to path
sys.path.insert(0, 'src')

from src.ui.charts.calendar_heatmap import CalendarHeatmap, ViewMode

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Heatmap Test")
        self.setGeometry(100, 100, 1200, 600)
        
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
    sys.exit(app.exec())