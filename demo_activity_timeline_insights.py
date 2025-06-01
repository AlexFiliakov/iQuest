"""
Demo script to test the improved Activity Timeline with insights panel.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.ui.activity_timeline_component import ActivityTimelineComponent


def generate_demo_data():
    """Generate demo health data with patterns and anomalies."""
    # Create 7 days of hourly data
    start_date = datetime.now() - timedelta(days=7)
    date_range = pd.date_range(start=start_date, periods=24*7, freq='h')
    
    # Generate realistic activity patterns
    data = []
    for timestamp in date_range:
        hour = timestamp.hour
        day = timestamp.dayofweek
        
        # Base activity patterns
        if 6 <= hour <= 9:  # Morning activity
            steps = np.random.normal(500, 100)
            heart_rate = np.random.normal(85, 10)
            active_calories = np.random.normal(50, 10)
        elif 12 <= hour <= 13:  # Lunch walk
            steps = np.random.normal(300, 50)
            heart_rate = np.random.normal(75, 8)
            active_calories = np.random.normal(30, 5)
        elif 17 <= hour <= 19:  # Evening exercise
            steps = np.random.normal(800, 150)
            heart_rate = np.random.normal(95, 15)
            active_calories = np.random.normal(80, 15)
        elif 22 <= hour or hour <= 5:  # Sleep time
            steps = np.random.normal(10, 5)
            heart_rate = np.random.normal(60, 5)
            active_calories = np.random.normal(5, 2)
        else:  # Regular activity
            steps = np.random.normal(200, 50)
            heart_rate = np.random.normal(70, 8)
            active_calories = np.random.normal(20, 5)
            
        # Add some anomalies
        if (day == 2 and hour == 23) or (day == 5 and hour == 3):
            # Late night anomaly
            steps = np.random.normal(1500, 200)
            heart_rate = np.random.normal(120, 15)
            active_calories = np.random.normal(150, 20)
            
        # Ensure non-negative values
        steps = max(0, steps)
        heart_rate = max(50, heart_rate)
        active_calories = max(0, active_calories)
        
        data.append({
            'timestamp': timestamp,
            'steps': steps,
            'heart_rate': heart_rate,
            'active_calories': active_calories
        })
        
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


class DemoWindow(QMainWindow):
    """Demo window to showcase the Activity Timeline with insights."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Activity Timeline Demo - User-Friendly Insights")
        self.setGeometry(100, 100, 1200, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Create Activity Timeline Component
        self.timeline = ActivityTimelineComponent()
        layout.addWidget(self.timeline)
        
        # Generate and load demo data
        demo_data = generate_demo_data()
        metrics = ['steps', 'heart_rate', 'active_calories']
        
        # Enable clustering to show patterns
        self.timeline.clustering_enabled = True
        self.timeline.cluster_check.setChecked(True)
        
        # Update with demo data
        self.timeline.update_data(demo_data, metrics)
        
        # Apply some styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5E6D3;
            }
        """)


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()