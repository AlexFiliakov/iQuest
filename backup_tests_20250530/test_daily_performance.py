#!/usr/bin/env python3
"""Test script to measure Daily tab performance improvements."""

import sys
import time
from datetime import date, timedelta
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, QElapsedTimer
from src.ui.daily_dashboard_widget import DailyDashboardWidget
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """Monitor performance metrics for the Daily tab."""
    
    def __init__(self):
        self.timer = QElapsedTimer()
        self.measurements = []
        
    def start(self):
        """Start timing."""
        self.timer.start()
        
    def measure(self, operation: str):
        """Record a measurement."""
        elapsed = self.timer.elapsed()
        self.measurements.append((operation, elapsed))
        logger.info(f"{operation}: {elapsed}ms")
        return elapsed
        
    def report(self):
        """Print performance report."""
        print("\n" + "="*50)
        print("Performance Report")
        print("="*50)
        for op, time_ms in self.measurements:
            print(f"{op:<30} {time_ms:>10}ms")
        print("="*50 + "\n")

def test_performance():
    """Test the Daily tab performance."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Performance monitor
    monitor = PerformanceMonitor()
    
    # Test results display
    results_widget = QWidget()
    results_widget.setWindowTitle("Daily Tab Performance Test")
    results_layout = QVBoxLayout(results_widget)
    
    results_label = QLabel("Performance Test Results:\n")
    results_layout.addWidget(results_label)
    
    def update_results(text):
        current = results_label.text()
        results_label.setText(current + "\n" + text)
    
    # Test functions
    def test_tab_switch():
        """Test switching to Daily tab."""
        update_results("Testing tab switch performance...")
        monitor.start()
        
        # Switch to config tab first
        window.tab_widget.setCurrentIndex(0)
        QApplication.processEvents()
        
        # Then switch to Daily tab
        window.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        elapsed = monitor.measure("Tab switch to Daily")
        update_results(f"✓ Tab switch: {elapsed}ms")
        
    def test_navigation():
        """Test date navigation performance."""
        update_results("\nTesting navigation performance...")
        
        # Get daily dashboard
        if hasattr(window, 'daily_dashboard'):
            dashboard = window.daily_dashboard
            
            # Test previous day
            monitor.start()
            dashboard._go_to_previous_day()
            QApplication.processEvents()
            elapsed = monitor.measure("Navigate to previous day")
            update_results(f"✓ Previous day: {elapsed}ms")
            
            # Test next day
            monitor.start()
            dashboard._go_to_next_day()
            QApplication.processEvents()
            elapsed = monitor.measure("Navigate to next day")
            update_results(f"✓ Next day: {elapsed}ms")
            
            # Test today
            monitor.start()
            dashboard._go_to_today()
            QApplication.processEvents()
            elapsed = monitor.measure("Navigate to today")
            update_results(f"✓ Today: {elapsed}ms")
            
    def test_rapid_navigation():
        """Test rapid navigation (stress test)."""
        update_results("\nTesting rapid navigation...")
        
        if hasattr(window, 'daily_dashboard'):
            dashboard = window.daily_dashboard
            
            monitor.start()
            # Rapidly navigate 10 days
            for i in range(10):
                dashboard._go_to_previous_day()
                # Don't wait for processing
            
            # Let it catch up
            QApplication.processEvents()
            elapsed = monitor.measure("10 rapid navigations")
            update_results(f"✓ Rapid navigation: {elapsed}ms ({elapsed/10:.1f}ms avg)")
    
    # Add test buttons
    test_switch_btn = QPushButton("Test Tab Switch")
    test_switch_btn.clicked.connect(test_tab_switch)
    results_layout.addWidget(test_switch_btn)
    
    test_nav_btn = QPushButton("Test Navigation")
    test_nav_btn.clicked.connect(test_navigation)
    results_layout.addWidget(test_nav_btn)
    
    test_rapid_btn = QPushButton("Test Rapid Navigation")
    test_rapid_btn.clicked.connect(test_rapid_navigation)
    results_layout.addWidget(test_rapid_btn)
    
    def run_all_tests():
        """Run all performance tests."""
        update_results("\n" + "="*40)
        update_results("Running all performance tests...")
        update_results("="*40)
        
        # Give UI time to settle
        QTimer.singleShot(500, test_tab_switch)
        QTimer.singleShot(1500, test_navigation)
        QTimer.singleShot(3000, test_rapid_navigation)
        QTimer.singleShot(4000, lambda: monitor.report())
    
    run_all_btn = QPushButton("Run All Tests")
    run_all_btn.clicked.connect(run_all_tests)
    results_layout.addWidget(run_all_btn)
    
    # Show results window
    results_widget.resize(400, 500)
    results_widget.show()
    
    print("\n" + "="*50)
    print("Daily Tab Performance Test")
    print("="*50)
    print("\nOptimizations implemented:")
    print("- Debounced updates (100ms delay)")
    print("- Stats caching per date")
    print("- Lazy metric card creation")
    print("- Deferred chart updates")
    print("- Simplified trend calculations")
    print("- Hourly data caching")
    print("- Skip invisible widget updates")
    print("\nClick 'Run All Tests' to measure performance")
    print("="*50 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_performance())