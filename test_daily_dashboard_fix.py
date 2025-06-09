#!/usr/bin/env python3
"""Test that daily dashboard loads data correctly in portable mode."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from ui.daily_dashboard_widget import DailyDashboardWidget
from data_access import DataAccess

def main():
    app = QApplication(sys.argv)
    
    # Create data access (will use portable mode database)
    data_access = DataAccess()
    
    # Create daily dashboard with data access
    dashboard = DailyDashboardWidget(data_access=data_access)
    
    # Show the dashboard
    dashboard.show()
    
    # Check if data is loaded
    print(f"Available metrics: {len(dashboard._available_metrics)}")
    if dashboard._available_metrics:
        print(f"First few metrics: {dashboard._available_metrics[:3]}")
    
    # Check if metric cards were created
    if hasattr(dashboard, '_metric_cards'):
        print(f"Metric cards created: {len(dashboard._metric_cards)}")
    
    # Run the app
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
