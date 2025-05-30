#!/usr/bin/env python3
"""
Comprehensive test for weekly dashboard display issues.
"""

import sys
import os
import pandas as pd
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import Qt, QTimer

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.ui.weekly_dashboard_widget import WeeklyDashboardWidget
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.utils.logging_config import setup_logging, get_logger
import time

# Set up logging
setup_logging()
logger = get_logger(__name__)

def create_comprehensive_test_data():
    """Create comprehensive test data for the weekly dashboard."""
    # Generate test data for the last 60 days
    dates = pd.date_range(end=date.today(), periods=60)
    data = []
    
    for d in dates:
        # Steps data - more realistic values
        steps = 5000 + (d.day * 100) + (d.weekday() * 500)
        data.append({
            'type': 'HKQuantityTypeIdentifierStepCount',
            'value': steps,
            'unit': 'count',
            'startDate': d,
            'endDate': d + timedelta(hours=1),
            'creationDate': d,  # Add required creationDate column
            'sourceName': 'Test Data'
        })
        
        # Distance data
        distance = 3.5 + (d.day * 0.1) + (d.weekday() * 0.2)
        data.append({
            'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
            'value': distance,
            'unit': 'km',
            'startDate': d,
            'endDate': d + timedelta(hours=1),
            'creationDate': d,  # Add required creationDate column
            'sourceName': 'Test Data'
        })
        
        # Heart rate data
        hr = 65 + (d.day % 10) + (d.weekday() * 2)
        data.append({
            'type': 'HKQuantityTypeIdentifierHeartRate',
            'value': hr,
            'unit': 'count/min',
            'startDate': d,
            'endDate': d + timedelta(minutes=5),
            'creationDate': d,  # Add required creationDate column
            'sourceName': 'Test Data'
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Created test data with shape: {df.shape}")
    logger.info(f"Data types: {df['type'].unique()}")
    return df

class WeeklyTestWindow(QMainWindow):
    """Test window for debugging weekly dashboard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weekly Dashboard Comprehensive Test")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        load_button = QPushButton("1. Load Test Data")
        load_button.clicked.connect(self.load_test_data)
        button_layout.addWidget(load_button)
        
        check_button = QPushButton("2. Check Widget State")
        check_button.clicked.connect(self.check_widget_state)
        button_layout.addWidget(check_button)
        
        refresh_button = QPushButton("3. Force Refresh")
        refresh_button.clicked.connect(self.force_refresh)
        button_layout.addWidget(refresh_button)
        
        debug_button = QPushButton("4. Debug Calculator")
        debug_button.clicked.connect(self.debug_calculator)
        button_layout.addWidget(debug_button)
        
        layout.addLayout(button_layout)
        
        # Create weekly dashboard
        logger.info("Creating weekly dashboard widget...")
        self.weekly_dashboard = WeeklyDashboardWidget()
        layout.addWidget(self.weekly_dashboard)
        
        # Debug output
        self.debug_output = QTextEdit()
        self.debug_output.setMaximumHeight(200)
        layout.addWidget(self.debug_output)
        
        self.log("Weekly dashboard created and added to layout")
    
    def log(self, message):
        """Add message to debug output."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.debug_output.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def load_test_data(self):
        """Load test data into the weekly dashboard."""
        self.log("Loading test data...")
        
        try:
            # Create test data
            data = create_comprehensive_test_data()
            self.log(f"Created {len(data)} test records")
            
            # Create calculators with timezone
            local_tz = time.tzname[0]
            self.log(f"Using timezone: {local_tz}")
            
            daily_calc = DailyMetricsCalculator(data, timezone=local_tz)
            self.log(f"Created daily calculator")
            
            weekly_calc = WeeklyMetricsCalculator(daily_calc)
            self.log(f"Created weekly calculator")
            
            # Set calculator in weekly dashboard
            self.weekly_dashboard.set_weekly_calculator(weekly_calc)
            self.log(f"Set weekly calculator in dashboard")
            
            # Force show
            self.weekly_dashboard.show()
            self.weekly_dashboard.raise_()
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            logger.error(f"Error loading test data", exc_info=True)
    
    def check_widget_state(self):
        """Check the state of all widgets."""
        self.log("\n=== Widget State Check ===")
        
        # Main widget
        self.log(f"Weekly dashboard visible: {self.weekly_dashboard.isVisible()}")
        self.log(f"Weekly dashboard size: {self.weekly_dashboard.size()}")
        self.log(f"Weekly dashboard geometry: {self.weekly_dashboard.geometry()}")
        
        # Calculator
        if hasattr(self.weekly_dashboard, 'weekly_calculator'):
            self.log(f"Has weekly calculator: {self.weekly_dashboard.weekly_calculator is not None}")
        else:
            self.log("No weekly_calculator attribute")
        
        # Metric selector
        if hasattr(self.weekly_dashboard, 'metric_selector'):
            selector = self.weekly_dashboard.metric_selector
            self.log(f"Metric selector visible: {selector.isVisible()}")
            self.log(f"Metric selector enabled: {selector.isEnabled()}")
            self.log(f"Metric selector count: {selector.count()}")
            self.log(f"Current metric: {selector.currentText()} (data: {selector.currentData()})")
            
            # List all metrics
            for i in range(selector.count()):
                self.log(f"  Metric {i}: {selector.itemText(i)} = {selector.itemData(i)}")
        
        # Available metrics
        if hasattr(self.weekly_dashboard, '_available_metrics'):
            self.log(f"Available metrics: {self.weekly_dashboard._available_metrics}")
        
        # Stat cards
        if hasattr(self.weekly_dashboard, 'stat_cards'):
            self.log(f"Stat cards count: {len(self.weekly_dashboard.stat_cards)}")
            for name, card in self.weekly_dashboard.stat_cards.items():
                self.log(f"  {name}: visible={card.isVisible()}, size={card.size()}")
        
        # No data overlay
        if hasattr(self.weekly_dashboard, 'no_data_overlay'):
            overlay = self.weekly_dashboard.no_data_overlay
            self.log(f"No data overlay exists: visible={overlay.isVisible()}")
            self.log(f"No data overlay geometry: {overlay.geometry()}")
        
        # Week labels
        if hasattr(self.weekly_dashboard, 'week_label'):
            self.log(f"Week label text: {self.weekly_dashboard.week_label.text()}")
        if hasattr(self.weekly_dashboard, 'date_range_label'):
            self.log(f"Date range: {self.weekly_dashboard.date_range_label.text()}")
    
    def force_refresh(self):
        """Force a refresh of the weekly dashboard."""
        self.log("\n=== Force Refresh ===")
        
        if hasattr(self.weekly_dashboard, '_load_weekly_data'):
            self.log("Calling _load_weekly_data()...")
            self.weekly_dashboard._load_weekly_data()
        
        self.weekly_dashboard.update()
        QApplication.processEvents()
        self.log("Refresh complete")
    
    def debug_calculator(self):
        """Debug the calculator data."""
        self.log("\n=== Calculator Debug ===")
        
        if not hasattr(self.weekly_dashboard, 'weekly_calculator'):
            self.log("No weekly calculator found")
            return
            
        calc = self.weekly_dashboard.weekly_calculator
        if not calc:
            self.log("Weekly calculator is None")
            return
            
        self.log(f"Weekly calculator exists")
        
        # Check daily calculator
        if hasattr(calc, 'daily_calculator') and calc.daily_calculator:
            daily_calc = calc.daily_calculator
            self.log(f"Daily calculator exists")
            
            if hasattr(daily_calc, 'data'):
                data = daily_calc.data
                self.log(f"Data shape: {data.shape}")
                self.log(f"Data columns: {data.columns.tolist()}")
                self.log(f"Unique types: {data['type'].unique()[:5]}...")  # First 5
                
                # Try to get weekly metrics
                if hasattr(self.weekly_dashboard, '_current_week_start'):
                    week_start = self.weekly_dashboard._current_week_start
                    self.log(f"Current week start: {week_start}")
                    
                    # Try to get metrics for first available type
                    if len(data['type'].unique()) > 0:
                        test_type = data['type'].unique()[0]
                        self.log(f"Testing with metric: {test_type}")
                        
                        try:
                            metrics = calc.get_weekly_metrics(
                                metric=test_type,
                                week_start=week_start
                            )
                            if metrics:
                                self.log(f"Got weekly metrics: avg={metrics.avg}, days={len(metrics.daily_values)}")
                            else:
                                self.log("get_weekly_metrics returned None")
                        except Exception as e:
                            self.log(f"Error getting weekly metrics: {e}")

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    window = WeeklyTestWindow()
    window.show()
    
    # Auto-load data after 500ms
    QTimer.singleShot(500, window.load_test_data)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()