#!/usr/bin/env python3
"""
Test script to demonstrate the source-specific records and achievements feature
in the Trophy Case widget.
"""

import sys
import os
from datetime import date, datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from src.database import DatabaseManager
from src.analytics.personal_records_tracker import PersonalRecordsTracker, Record, RecordType
from src.ui.trophy_case_widget import TrophyCaseWidget


def create_test_records():
    """Create some test records with different sources."""
    db = DatabaseManager()
    tracker = PersonalRecordsTracker(db)
    
    # Create some test records with different sources
    test_records = [
        # Steps records from different sources
        {
            'metric': 'HKQuantityTypeIdentifierStepCount',
            'value': 15000,
            'date': date(2024, 1, 15),
            'source': 'iPhone',
            'type': RecordType.SINGLE_DAY_MAX
        },
        {
            'metric': 'HKQuantityTypeIdentifierStepCount',
            'value': 18000,
            'date': date(2024, 1, 20),
            'source': 'Apple Watch',
            'type': RecordType.SINGLE_DAY_MAX
        },
        # Heart rate records
        {
            'metric': 'HKQuantityTypeIdentifierHeartRate',
            'value': 180,
            'date': date(2024, 1, 10),
            'source': 'Apple Watch',
            'type': RecordType.SINGLE_DAY_MAX
        },
        {
            'metric': 'HKQuantityTypeIdentifierHeartRate',
            'value': 45,
            'date': date(2024, 1, 12),
            'source': 'Apple Watch',
            'type': RecordType.SINGLE_DAY_MIN
        },
        # Active energy records
        {
            'metric': 'HKQuantityTypeIdentifierActiveEnergyBurned',
            'value': 850,
            'date': date(2024, 1, 25),
            'source': 'Apple Watch',
            'type': RecordType.SINGLE_DAY_MAX
        },
        # Sleep records
        {
            'metric': 'HKCategoryTypeIdentifierSleepAnalysis',
            'value': 9.5,
            'date': date(2024, 1, 8),
            'source': 'iPhone',
            'type': RecordType.SINGLE_DAY_MAX
        }
    ]
    
    # Process records
    for record_data in test_records:
        record = Record(
            record_type=record_data['type'],
            metric=record_data['metric'],
            value=record_data['value'],
            date=record_data['date'],
            source=record_data['source']
        )
        tracker.process_new_record(record)
    
    print(f"Created {len(test_records)} test records with different sources")
    return tracker


class TestWindow(QMainWindow):
    """Test window to display the Trophy Case widget."""
    
    def __init__(self):
        super().__init__()
        
        # Create test records
        self.tracker = create_test_records()
        
        # Setup UI
        self.setWindowTitle("Trophy Case - Source Filter Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create trophy case widget
        self.trophy_case = TrophyCaseWidget(self.tracker)
        layout.addWidget(self.trophy_case)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D3142;
            }
            QWidget {
                background-color: #2D3142;
                color: #E9ECEF;
            }
        """)


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    window = TestWindow()
    window.show()
    
    # Print instructions
    print("\n" + "="*60)
    print("Trophy Case Source Filter Test")
    print("="*60)
    print("\nThe Trophy Case widget now supports source-specific filtering:")
    print("1. The header dropdown shows all available metrics and source combinations")
    print("2. Select 'All Records' to see all records and achievements")
    print("3. Select a metric (e.g., 'Step Count') to see records from all sources for that metric")
    print("4. Select a source-specific option (e.g., 'Step Count - iPhone') to see only those records")
    print("5. Achievements show which metric they were earned for")
    print("\nTry different filter options to see how records and achievements are filtered!")
    print("="*60 + "\n")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()