#!/usr/bin/env python3
"""Test script to run the app with debug monthly widget."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_with_debug_widget():
    """Test using the debug version of monthly widget."""
    print("[TEST] Starting test with debug monthly widget")
    
    # Temporarily replace the import
    import src.ui.main_window as main_window
    
    # Monkey patch to use debug widget
    original_create = main_window.MainWindow._create_monthly_dashboard_tab
    
    def _create_monthly_dashboard_tab_debug(self):
        """Create the monthly dashboard tab with debug widget."""
        print("[TEST] Creating monthly tab with debug widget")
        try:
            from src.ui.monthly_dashboard_widget_debug import MonthlyDashboardWidgetDebug
            
            self.monthly_dashboard = MonthlyDashboardWidgetDebug(parent=self)
            self.tab_widget.addTab(self.monthly_dashboard, "Monthly (Debug)")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Monthly dashboard in debug mode")
            print("[TEST] Debug monthly tab created successfully")
            
        except Exception as e:
            print(f"[TEST ERROR] Failed to create debug monthly tab: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to placeholder
            self._create_monthly_dashboard_placeholder()
    
    # Replace the method
    main_window.MainWindow._create_monthly_dashboard_tab = _create_monthly_dashboard_tab_debug
    
    # Now run the main app
    from src.main import main
    print("[TEST] Starting main application with debug monthly widget")
    main()

def test_regular_with_logging():
    """Test using regular widget with extra logging."""
    print("[TEST] Starting test with regular monthly widget + logging")
    
    # Just run the main app - the logging is already added
    from src.main import main
    main()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        test_with_debug_widget()
    else:
        test_regular_with_logging()