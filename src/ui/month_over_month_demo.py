"""
Demo script for Month-over-Month Trends Analysis.

This script demonstrates the complete functionality of the month-over-month
trends analysis system with sample data.
"""

import sys
import numpy as np
from datetime import datetime, timedelta
from typing import List

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# Mock the analytics components for demonstration
class MockMonthlyMetrics:
    def __init__(self, month_start: datetime, avg: float):
        self.month_start = month_start
        self.avg = avg
        self.median = avg * 0.95
        self.std = avg * 0.1
        self.min = avg * 0.8
        self.max = avg * 1.2
        self.count = 30

class MockMonthlyMetricsCalculator:
    def __init__(self):
        pass
    
    def get_monthly_metrics(self, metric: str, months: int) -> List[MockMonthlyMetrics]:
        """Generate mock monthly data with realistic trends."""
        data = []
        start_date = datetime.now() - timedelta(days=30 * months)
        base_value = 100
        
        for i in range(months):
            current_date = start_date + timedelta(days=30 * i)
            
            # Add trend and seasonality
            trend = i * 2  # Slight upward trend
            seasonal = 10 * np.sin(2 * np.pi * i / 12)  # Annual cycle
            noise = np.random.normal(0, 5)  # Random variation
            
            value = base_value + trend + seasonal + noise
            data.append(MockMonthlyMetrics(current_date, value))
        
        return data

def main():
    """Run the month-over-month trends demo."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Month-over-Month Trends Analysis - Demo")
    window.setGeometry(100, 100, 1400, 900)
    
    # Create central widget
    central_widget = QWidget(self)
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    try:
        # Import the actual components
        from month_over_month_widget import MonthOverMonthWidget
        
        # Create mock calculator
        mock_calculator = MockMonthlyMetricsCalculator()
        
        # Create the month-over-month widget
        mom_widget = MonthOverMonthWidget(mock_calculator)
        
        # Set sample metrics
        sample_metrics = [
            "Heart Rate (bpm)",
            "Step Count",
            "Sleep Duration (hours)",
            "Body Weight (lbs)",
            "Exercise Minutes"
        ]
        mom_widget.set_available_metrics(sample_metrics)
        
        # Add to layout
        layout.addWidget(mom_widget)
        
        # Show instructions
        print("Month-over-Month Trends Demo")
        print("=" * 40)
        print("1. Select a metric from the dropdown")
        print("2. Choose the number of months to analyze")
        print("3. Click 'Analyze Trends' to generate visualizations")
        print("4. Explore different tabs:")
        print("   - Waterfall: Month-to-month changes")
        print("   - Rankings: Performance ranking over time")
        print("   - Composition: Metric composition (for single metric, shows 100%)")
        print("   - Multiple Views: Small multiples with different perspectives")
        print("   - Calendar: Calendar heatmap of monthly values")
        print("5. Check the insights panel for generated insights and milestones")
        
    except ImportError as e:
        # Fallback demo without full functionality
        from PyQt6.QtWidgets import QLabel
        error_label = QLabel(f"Demo Error: {e}\n\nThis is a simplified demo of the Month-over-Month Trends system.")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("font-size: 14px; color: #E74C3C; padding: 20px;")
        layout.addWidget(error_label)
        
        # Show feature overview
        features_text = """
        Month-over-Month Trends Analysis Features:
        
        📊 VISUALIZATIONS:
        • Waterfall Charts - Show cumulative month-to-month changes
        • Bump Charts - Track ranking changes over time
        • Stream Graphs - Display composition changes (for multi-metric analysis)
        • Small Multiples - Multiple views for comprehensive analysis
        • Calendar Heatmaps - Monthly values in calendar format
        
        🔍 STATISTICAL ANALYSIS:
        • Seasonal Decomposition - Separate trend, seasonal, and residual components
        • Change Point Detection - Identify significant shifts in data
        • Momentum Scoring - Measure trend strength and direction
        • Forecasting - Generate predictions with confidence intervals
        
        💡 INSIGHTS GENERATION:
        • Automated insight narratives
        • Milestone detection (records, streaks, improvements)
        • Trend descriptions and recommendations
        • Statistical significance testing
        
        🎨 DESIGN FEATURES:
        • Wall Street Journal inspired styling
        • Interactive controls and filters
        • Export capabilities for all visualizations
        • Responsive design with professional aesthetics
        """
        
        features_label = QLabel(features_text)
        features_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        features_label.setStyleSheet("font-size: 12px; color: #2C3E50; padding: 20px; background-color: #F8F9FA; border-radius: 8px;")
        layout.addWidget(features_label)
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()