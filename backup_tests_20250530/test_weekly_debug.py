#!/usr/bin/env python3
"""
Debug script for weekly tab display issues.
"""

import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.ui.weekly_dashboard_widget import WeeklyDashboardWidget
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.utils.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

def create_test_data():
    """Create some test data for the weekly dashboard."""
    # Generate test data for the last 30 days
    dates = pd.date_range(end=date.today(), periods=30)
    data = []
    
    for d in dates:
        # Steps data
        data.append({
            'type': 'HKQuantityTypeIdentifierStepCount',
            'value': 5000 + (d.day * 100),  # Vary by day
            'unit': 'count',
            'startDate': d,
            'endDate': d + timedelta(hours=1)
        })
        
        # Distance data
        data.append({
            'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
            'value': 3.5 + (d.day * 0.1),
            'unit': 'km',
            'startDate': d,
            'endDate': d + timedelta(hours=1)
        })
    
    return pd.DataFrame(data)

class TestWindow(QMainWindow):
    """Test window for debugging weekly dashboard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weekly Dashboard Debug")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create weekly dashboard
        self.weekly_dashboard = WeeklyDashboardWidget()
        layout.addWidget(self.weekly_dashboard)
        
        # Debug info label
        self.debug_label = QLabel("Debug Info:")
        layout.addWidget(self.debug_label)
        
        # Load data button
        load_button = QPushButton("Load Test Data")
        load_button.clicked.connect(self.load_test_data)
        layout.addWidget(load_button)
        
        # Check visibility button
        check_button = QPushButton("Check Widget Visibility")
        check_button.clicked.connect(self.check_visibility)
        layout.addWidget(check_button)
    
    def load_test_data(self):
        """Load test data into the weekly dashboard."""
        logger.info("Loading test data...")
        
        try:
            # Create test data
            data = create_test_data()
            logger.info(f"Created {len(data)} test records")
            
            # Create calculators
            daily_calc = DailyMetricsCalculator(data)
            weekly_calc = WeeklyMetricsCalculator(daily_calc)
            
            # Set calculator in weekly dashboard
            self.weekly_dashboard.set_weekly_calculator(weekly_calc)
            
            self.debug_label.setText(f"Debug Info: Loaded {len(data)} records")
            
        except Exception as e:
            logger.error(f"Error loading test data: {e}", exc_info=True)
            self.debug_label.setText(f"Error: {str(e)}")
    
    def check_visibility(self):
        """Check visibility of key widgets."""
        info = []
        
        # Check main widget
        info.append(f"Weekly dashboard visible: {self.weekly_dashboard.isVisible()}")
        info.append(f"Weekly dashboard size: {self.weekly_dashboard.size()}")
        
        # Check metric selector
        if hasattr(self.weekly_dashboard, 'metric_selector'):
            info.append(f"Metric selector visible: {self.weekly_dashboard.metric_selector.isVisible()}")
            info.append(f"Metric selector count: {self.weekly_dashboard.metric_selector.count()}")
            info.append(f"Current metric: {self.weekly_dashboard.metric_selector.currentText()}")
        
        # Check stat cards
        if hasattr(self.weekly_dashboard, 'stat_cards'):
            info.append(f"Stat cards count: {len(self.weekly_dashboard.stat_cards)}")
            for name, card in self.weekly_dashboard.stat_cards.items():
                info.append(f"  {name} visible: {card.isVisible()}")
        
        # Check no data overlay
        if hasattr(self.weekly_dashboard, 'no_data_overlay'):
            info.append(f"No data overlay visible: {self.weekly_dashboard.no_data_overlay.isVisible()}")
        
        self.debug_label.setText("Debug Info:\n" + "\n".join(info))

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()