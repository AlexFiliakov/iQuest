"""Demonstrate the calendar popup improvements."""

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QDateEdit
from PyQt6.QtCore import QDate, QTimer

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.styled_calendar_widget import StyledCalendarWidget


def main():
    """Create and display improved calendar popup."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Create main widget
    widget = QWidget()
    widget.setWindowTitle("Improved Calendar Popup")
    widget.setGeometry(100, 100, 400, 200)
    
    layout = QVBoxLayout(widget)
    
    # Add label
    label = QLabel("<h3>Fixed Calendar Popup Issues:</h3>")
    layout.addWidget(label)
    
    # Create date edit with styled calendar
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDate(QDate(2025, 5, 21))  # Match the date from the screenshot
    
    # Set our custom calendar
    calendar = StyledCalendarWidget()
    calendar.setHideDaysFromOtherMonths(True)
    date_edit.setCalendarWidget(calendar)
    
    layout.addWidget(date_edit)
    
    # Add description
    desc = QLabel(
        "• All 7 days visible (including Sunday)\n"
        "• No extra days from other months\n"
        "• All 6 rows properly displayed\n"
        "• Clean, modern design"
    )
    layout.addWidget(desc)
    
    widget.show()
    
    # Auto-open calendar after a short delay for demonstration
    def open_calendar():
        # Find the dropdown button and click it
        for child in date_edit.children():
            if hasattr(child, 'click'):
                child.click()
                break
    
    QTimer.singleShot(500, open_calendar)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()