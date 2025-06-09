#!/usr/bin/env python3
"""Test that weekly dashboard loads correctly with DataAccess in portable mode."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from ui.weekly_dashboard_widget import WeeklyDashboardWidget
from data_access import DataAccess

def main():
    app = QApplication(sys.argv)
    
    # Create data access (will use portable mode database)
    data_access = DataAccess()
    
    # Create weekly dashboard with data access
    dashboard = WeeklyDashboardWidget(data_access=data_access)
    
    # Show the dashboard
    dashboard.show()
    
    # Check if data is loaded
    print(f"Weekly dashboard created successfully")
    print(f"Available metrics: {len(dashboard._available_metrics) if hasattr(dashboard, '_available_metrics') else 0}")
    if hasattr(dashboard, '_available_metrics') and dashboard._available_metrics:
        print(f"First few metrics: {dashboard._available_metrics[:3]}")
    
    # Check if calculator was created
    if dashboard.weekly_calculator:
        print("Weekly calculator initialized successfully")
    if dashboard.daily_calculator:
        print("Daily calculator initialized successfully")
    
    # Run the app
    sys.exit(app.exec())

if __name__ == "__main__":
    main()