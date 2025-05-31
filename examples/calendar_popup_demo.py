"""Test script to verify the improved calendar popup styling."""

import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QDate

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.adaptive_date_edit import AdaptiveDateEdit
from src.ui.enhanced_date_edit import EnhancedDateEdit


class TestWindow(QMainWindow):
    """Test window to demonstrate calendar improvements."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Popup Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        
        # Add title
        title = QLabel("<h2>Calendar Popup Test</h2>")
        layout.addWidget(title)
        
        # Add enhanced date edit
        label1 = QLabel("Enhanced Date Edit (Basic Styling):")
        layout.addWidget(label1)
        
        self.enhanced_date = EnhancedDateEdit()
        self.enhanced_date.setDate(QDate.currentDate())
        layout.addWidget(self.enhanced_date)
        
        # Add adaptive date edit
        label2 = QLabel("Adaptive Date Edit (With Data Availability):")
        layout.addWidget(label2)
        
        self.adaptive_date = AdaptiveDateEdit()
        self.adaptive_date.setDate(QDate.currentDate())
        
        # Simulate some data availability
        today = date.today()
        available_dates = set()
        partial_dates = set()
        
        # Add some available dates (last 30 days)
        for i in range(30):
            d = today - timedelta(days=i)
            available_dates.add(d)
            # Make every 5th day partial
            if i % 5 == 0:
                partial_dates.add(d)
                
        # Update the calendar with availability data
        self.adaptive_date.available_dates = available_dates
        self.adaptive_date.partial_dates = partial_dates
        self.adaptive_date._update_calendar_highlighting()
        
        layout.addWidget(self.adaptive_date)
        
        # Add instructions
        instructions = QLabel(
            "<p>Click the dropdown arrows to see the improved calendar popups.</p>"
            "<p>Improvements:</p>"
            "<ul>"
            "<li>✓ All 7 days of the week are visible (including Sunday)</li>"
            "<li>✓ Days from other months are hidden</li>"
            "<li>✓ All 6 week rows are properly visible</li>"
            "<li>✓ Modern, visually appealing design</li>"
            "<li>✓ Data availability visualization (green/yellow/red)</li>"
            "</ul>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Add stretch to push everything to the top
        layout.addStretch()


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()