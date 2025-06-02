#!/usr/bin/env python3
"""
Test script for Activity Timeline background processing.

This script tests the new background analytics processing
to ensure the UI doesn't freeze during heavy ML operations.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, 'src')

from ui.activity_timeline_component import ActivityTimelineComponent


def generate_test_data():
    """Generate test health data for timeline."""
    # Create 24 hours of data with 15-minute intervals
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    times = []
    
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            times.append(base_time + timedelta(hours=hour, minutes=minute))
    
    # Generate random metrics
    np.random.seed(42)
    data = pd.DataFrame({
        'datetime': times,
        'steps': np.random.poisson(100, len(times)),
        'heart_rate': np.random.normal(70, 10, len(times)),
        'active_calories': np.random.exponential(20, len(times))
    })
    
    # Add some patterns
    # Morning activity spike
    morning_mask = (data['datetime'].dt.hour >= 6) & (data['datetime'].dt.hour <= 9)
    data.loc[morning_mask, 'steps'] *= 3
    data.loc[morning_mask, 'active_calories'] *= 2
    
    # Evening activity
    evening_mask = (data['datetime'].dt.hour >= 17) & (data['datetime'].dt.hour <= 19)
    data.loc[evening_mask, 'steps'] *= 2
    data.loc[evening_mask, 'heart_rate'] += 10
    
    # Add some anomalies
    data.loc[10, 'heart_rate'] = 120  # Anomaly
    data.loc[50, 'steps'] = 5000  # Anomaly
    
    data.set_index('datetime', inplace=True)
    return data


class TestWindow(QMainWindow):
    """Test window for Activity Timeline background processing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Activity Timeline Background Processing Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        self.info_label = QLabel("Click 'Load Data' to test background processing")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Load button
        self.load_button = QPushButton("Load Data")
        self.load_button.clicked.connect(self.load_data)
        layout.addWidget(self.load_button)
        
        # Timeline component
        self.timeline = ActivityTimelineComponent()
        layout.addWidget(self.timeline)
        
        # Connect to timeline signals
        self.timeline.analytics_worker.progress_updated.connect(self.on_progress)
        self.timeline.analytics_worker.finished.connect(self.on_finished)
        
    def load_data(self):
        """Load test data into timeline."""
        self.info_label.setText("Loading data and starting background analytics...")
        self.load_button.setEnabled(False)
        
        # Generate and load test data
        data = generate_test_data()
        metrics = ['steps', 'heart_rate', 'active_calories']
        
        self.timeline.update_data(data, metrics)
        
    def on_progress(self, percentage, message):
        """Handle progress updates."""
        self.info_label.setText(f"Processing: {message} ({percentage}%)")
        
    def on_finished(self):
        """Handle processing completion."""
        self.info_label.setText("Background processing complete! UI remained responsive.")
        self.load_button.setEnabled(True)


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()