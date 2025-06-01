"""
Demo of the reusable line chart component with WSJ-inspired styling.

This example shows how to use the EnhancedLineChart with:
- Multiple data series
- Wall Street Journal styling
- Interactive features (zoom, pan)
- Export functionality
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))
from ui.charts import EnhancedLineChart, LineChartBuilder


def generate_sample_data():
    """Generate sample health data for demonstration."""
    # Generate dates
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    # Generate heart rate data (with daily variation)
    base_hr = 70
    heart_rate = base_hr + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
    heart_rate += np.random.normal(0, 5, len(dates))
    heart_rate = np.clip(heart_rate, 50, 100)
    
    # Generate steps data (with weekly patterns)
    base_steps = 8000
    steps = base_steps + 2000 * np.sin(np.arange(len(dates)) * 2 * np.pi / 7)
    steps += np.random.normal(0, 1000, len(dates))
    steps = np.clip(steps, 2000, 15000)
    
    # Generate sleep hours (with some randomness)
    sleep_hours = 7.5 + 0.5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 30)
    sleep_hours += np.random.normal(0, 0.5, len(dates))
    sleep_hours = np.clip(sleep_hours, 4, 10)
    
    return dates, heart_rate, steps, sleep_hours


class LineChartDemo(QMainWindow):
    """Demo window showing different line chart configurations."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Line Chart Component Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout
        layout = QVBoxLayout(central)
        
        # Create chart with WSJ style
        self.wsj_chart = self._create_wsj_chart()
        layout.addWidget(self.wsj_chart)
        
        # Create chart with warm theme
        self.warm_chart = self._create_warm_chart()
        layout.addWidget(self.warm_chart)
        
        # Control buttons
        controls = self._create_controls()
        layout.addLayout(controls)
        
    def _create_wsj_chart(self):
        """Create a chart with Wall Street Journal styling."""
        # Build chart with WSJ style
        chart = (LineChartBuilder()
                .with_title("Health Metrics Over Time", "Daily averages for 2024")
                .with_wsj_style()
                .with_labels("Date", "Value")
                .with_size(1150, 350)
                .with_legend(True, 'top')
                .build())
        
        # Generate and add data
        dates, heart_rate, steps, sleep = generate_sample_data()
        
        # Add heart rate series
        hr_data = [{'x': i, 'y': hr, 'date': date.strftime('%Y-%m-%d')} 
                   for i, (date, hr) in enumerate(zip(dates[:90], heart_rate[:90]))]
        chart.add_series("Resting Heart Rate (bpm)", hr_data, color='#0066CC')
        
        # Add sleep series (scaled for visibility)
        sleep_data = [{'x': i, 'y': sleep * 10, 'date': date.strftime('%Y-%m-%d')} 
                      for i, (date, sleep) in enumerate(zip(dates[:90], sleep_hours[:90]))]
        chart.add_series("Sleep Hours (×10)", sleep_data, color='#DC143C')
        
        chart.set_labels(
            "Health Trends - Q1 2024",
            "Inspired by Wall Street Journal data visualization style",
            "Days", 
            "Metric Value"
        )
        
        return chart
        
    def _create_warm_chart(self):
        """Create a chart with the warm theme."""
        # Build chart with warm theme
        chart = (LineChartBuilder()
                .with_title("Activity Tracking", "Steps taken throughout the year")
                .with_warm_theme()
                .with_animation(True, 800)
                .with_labels("Month", "Steps")
                .with_size(1150, 350)
                .build())
        
        # Generate monthly aggregated data
        dates, _, steps, _ = generate_sample_data()
        
        # Aggregate by month
        df = pd.DataFrame({'date': dates, 'steps': steps})
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby('month')['steps'].agg(['mean', 'min', 'max']).reset_index()
        
        # Add average steps
        avg_data = [{'x': i, 'y': row['mean'], 'month': str(row['month'])} 
                    for i, row in monthly.iterrows()]
        chart.add_series("Average Steps", avg_data)
        
        # Add min/max as additional series
        min_data = [{'x': i, 'y': row['min'], 'month': str(row['month'])} 
                    for i, row in monthly.iterrows()]
        chart.add_series("Minimum Steps", min_data)
        
        max_data = [{'x': i, 'y': row['max'], 'month': str(row['month'])} 
                    for i, row in monthly.iterrows()]
        chart.add_series("Maximum Steps", max_data)
        
        return chart
        
    def _create_controls(self):
        """Create control buttons for the demo."""
        layout = QHBoxLayout()
        
        # Add sample data button
        btn_add_data = QPushButton("Add Random Series")
        btn_add_data.clicked.connect(self._add_random_series)
        layout.addWidget(btn_add_data)
        
        # Clear data button
        btn_clear = QPushButton("Clear All Series")
        btn_clear.clicked.connect(self._clear_series)
        layout.addWidget(btn_clear)
        
        # Toggle animation
        btn_animate = QPushButton("Toggle Animation")
        btn_animate.clicked.connect(self._toggle_animation)
        layout.addWidget(btn_animate)
        
        # Export button
        btn_export = QPushButton("Export Charts")
        btn_export.clicked.connect(self._export_charts)
        layout.addWidget(btn_export)
        
        layout.addStretch()
        
        return layout
        
    def _add_random_series(self):
        """Add a random data series to demonstrate multi-series support."""
        # Generate random data
        n_points = 50
        data = [{'x': i, 'y': np.random.randint(40, 100)} for i in range(n_points)]
        
        # Add to warm chart
        series_name = f"Random Series {len(self.warm_chart.series) + 1}"
        self.warm_chart.add_series(series_name, data)
        
    def _clear_series(self):
        """Clear all data series."""
        self.warm_chart.clear_series()
        
    def _toggle_animation(self):
        """Toggle animation on/off."""
        self.warm_chart.config.animate = not self.warm_chart.config.animate
        self.wsj_chart.config.animate = not self.wsj_chart.config.animate
        
    def _export_charts(self):
        """Export both charts."""
        self.wsj_chart.save_to_file("wsj_style_chart.png")
        self.warm_chart.save_to_file("warm_theme_chart.png")
        print("Charts exported to wsj_style_chart.png and warm_theme_chart.png")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo
    demo = LineChartDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()