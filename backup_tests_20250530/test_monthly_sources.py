#!/usr/bin/env python3
"""Test the Monthly tab with source-specific metrics."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow
from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
from src.utils.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Monthly Tab - Source-Specific Metrics Test")
    
    # Create monthly dashboard widget
    monthly_widget = MonthlyDashboardWidget()
    
    # Set as central widget
    window.setCentralWidget(monthly_widget)
    
    # Show window
    window.resize(1200, 800)
    window.show()
    
    print("\nMonthly Tab Source-Specific Test:")
    print("=" * 60)
    
    # Check available sources from database
    if monthly_widget.health_db:
        sources = monthly_widget.health_db.get_available_sources()
        print(f"\nActual sources found in database: {len(sources)}")
        for source in sources[:10]:  # Show first 10
            print(f"  - {source}")
        if len(sources) > 10:
            print(f"  ... and {len(sources) - 10} more")
    else:
        print("\nNo database connection - using default metrics")
    
    # Check available metrics
    print(f"\nAvailable metric combinations: {len(monthly_widget._available_metrics)}")
    for i, (metric, source) in enumerate(monthly_widget._available_metrics[:20]):  # Show first 20
        display_name = monthly_widget._metric_display_names.get(metric, metric)
        if source:
            print(f"  {i+1}. {display_name} - {source}")
        else:
            print(f"  {i+1}. {display_name} (All Sources)")
    if len(monthly_widget._available_metrics) > 20:
        print(f"  ... and {len(monthly_widget._available_metrics) - 20} more")
    
    print("\n" + "=" * 60)
    print("\nTEST INSTRUCTIONS:")
    print("1. Check the Metric dropdown - it should show your actual data sources")
    print("2. Select different metrics and verify:")
    print("   - Data doesn't change randomly when selecting the same metric")
    print("   - The calendar title shows the correct source")
    print("   - No hardcoded 'Apple Watch' if you don't have one")
    print("3. Hover over dates to see tooltips with correct source info")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()