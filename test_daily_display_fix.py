#!/usr/bin/env python3
"""Test script to verify Daily tab display fixes."""

import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_daily_display():
    """Test the Daily tab display functionality."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Test results display
    results_widget = QWidget()
    results_widget.setWindowTitle("Daily Tab Display Test")
    results_layout = QVBoxLayout(results_widget)
    
    results_label = QLabel("Daily Tab Display Test\n\nTesting data display and UI refresh...")
    results_layout.addWidget(results_label)
    
    def update_results(text):
        current = results_label.text()
        results_label.setText(current + "\n" + text)
    
    # Test functions
    def test_tab_switch():
        """Test switching to Daily tab."""
        update_results("\n1. Testing tab switch...")
        
        # Switch to config tab first
        window.tab_widget.setCurrentIndex(0)
        QApplication.processEvents()
        
        # Then switch to Daily tab
        window.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        if hasattr(window, 'daily_dashboard'):
            update_results("✓ Daily tab loaded successfully")
        else:
            update_results("✗ Daily tab failed to load")
    
    def test_data_display():
        """Test data display functionality."""
        update_results("\n2. Testing data display...")
        
        if hasattr(window, 'daily_dashboard'):
            dashboard = window.daily_dashboard
            
            # Check if metric cards are visible
            if hasattr(dashboard, '_metric_cards') and dashboard._metric_cards:
                update_results(f"✓ Found {len(dashboard._metric_cards)} metric cards")
                
                # Check for data in cards
                cards_with_data = 0
                for metric_name, card in dashboard._metric_cards.items():
                    if card.value_label.text() != "--":
                        cards_with_data += 1
                
                update_results(f"✓ {cards_with_data} cards displaying data")
            else:
                update_results("✗ No metric cards found")
                
            # Check summary cards
            if hasattr(dashboard, 'activity_score'):
                update_results("✓ Summary cards initialized")
            else:
                update_results("✗ Summary cards not initialized")
    
    def test_date_navigation():
        """Test date navigation and data refresh."""
        update_results("\n3. Testing date navigation...")
        
        if hasattr(window, 'daily_dashboard'):
            dashboard = window.daily_dashboard
            current_date = dashboard._current_date
            
            # Navigate to previous day
            dashboard._go_to_previous_day()
            QApplication.processEvents()
            
            if dashboard._current_date == current_date - timedelta(days=1):
                update_results("✓ Previous day navigation works")
            else:
                update_results("✗ Previous day navigation failed")
            
            # Navigate back to today
            dashboard._go_to_today()
            QApplication.processEvents()
            
            if dashboard._current_date == date.today():
                update_results("✓ Today navigation works")
            else:
                update_results("✗ Today navigation failed")
    
    def test_refresh():
        """Test data refresh functionality."""
        update_results("\n4. Testing refresh functionality...")
        
        if hasattr(window, 'daily_dashboard'):
            dashboard = window.daily_dashboard
            
            # Clear cache
            dashboard._stats_cache.clear()
            
            # Trigger refresh
            dashboard._refresh_data()
            QApplication.processEvents()
            
            update_results("✓ Refresh completed without errors")
    
    def run_all_tests():
        """Run all tests in sequence."""
        update_results("\n" + "="*40)
        update_results("Running Daily Tab Display Tests")
        update_results("="*40)
        
        # Give UI time to settle
        QTimer.singleShot(500, test_tab_switch)
        QTimer.singleShot(1500, test_data_display)
        QTimer.singleShot(2500, test_date_navigation)
        QTimer.singleShot(3500, test_refresh)
        QTimer.singleShot(4500, lambda: update_results("\n✅ All tests completed!"))
    
    # Add test button
    run_tests_btn = QPushButton("Run All Tests")
    run_tests_btn.clicked.connect(run_all_tests)
    results_layout.addWidget(run_tests_btn)
    
    # Show results window
    results_widget.resize(400, 500)
    results_widget.show()
    
    print("\n" + "="*50)
    print("Daily Tab Display Test")
    print("="*50)
    print("\nFixes implemented:")
    print("- Clear cache when date changes")
    print("- Immediate data loading (no deferred updates)")
    print("- Force refresh on showEvent")
    print("- Enhanced debug logging")
    print("\nClick 'Run All Tests' to verify fixes")
    print("="*50 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_daily_display())