#!/usr/bin/env python3
"""
Test script to verify calendar heatmap square consistency across months.
"""

import sys
from datetime import date
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from src.ui.charts.calendar_heatmap import CalendarHeatmapComponent

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Heatmap Consistency Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous Month")
        self.prev_btn.clicked.connect(self.prev_month)
        nav_layout.addWidget(self.prev_btn)
        
        self.month_label = QPushButton("February 2024")  # February has 29 days (leap year)
        self.month_label.setEnabled(False)
        nav_layout.addWidget(self.month_label)
        
        self.next_btn = QPushButton("Next Month")
        self.next_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Calendar heatmap
        self.calendar = CalendarHeatmapComponent()
        self.calendar._view_mode = "month_grid"
        self.calendar.set_show_controls(False)
        layout.addWidget(self.calendar)
        
        # Current date
        self.current_year = 2024
        self.current_month = 2
        
        # Load test data
        self.load_test_data()
        
    def load_test_data(self):
        """Load test data for the current month."""
        # Generate test data with varying values
        test_data = {}
        
        # Add data for several months to test consistency
        for month in range(1, 13):
            days_in_month = 31
            if month in [4, 6, 9, 11]:
                days_in_month = 30
            elif month == 2:
                days_in_month = 29 if self.current_year % 4 == 0 else 28
                
            for day in range(1, days_in_month + 1):
                try:
                    test_date = date(self.current_year, month, day)
                    # Create a pattern that's visible
                    value = (day * 1000) % 15000
                    test_data[test_date] = value
                except:
                    pass
        
        self.calendar.set_metric_data('steps', test_data)
        self.calendar.set_current_date(date(self.current_year, self.current_month, 1))
        self.update_label()
        
    def prev_month(self):
        """Navigate to previous month."""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.load_test_data()
        
    def next_month(self):
        """Navigate to next month."""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.load_test_data()
        
    def update_label(self):
        """Update month label."""
        months = ["", "January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        self.month_label.setText(f"{months[self.current_month]} {self.current_year}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("\nCalendar Heatmap Consistency Test")
    print("=================================")
    print("Navigate between months using the buttons.")
    print("The calendar squares should maintain the same size across all months.")
    print("\nKey months to check:")
    print("- February (4-5 weeks)")
    print("- March (5-6 weeks)")
    print("- Months starting on Saturday/Sunday (can have 6 weeks)")
    
    sys.exit(app.exec())