"""
Bar Chart Component Demo

This script demonstrates the capabilities of the reusable bar chart component
with various chart types and configurations inspired by Wall Street Journal styling.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PyQt6.QtCore import Qt

# Add the src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from ui.bar_chart_component import BarChart, BarChartConfig, InteractiveBarChart
from ui.style_manager import StyleManager


class BarChartDemo(QMainWindow):
    """Demo application showcasing bar chart capabilities."""
    
    def __init__(self):
        super().__init__()
        self.style_manager = StyleManager()
        self.current_chart = None
        self.setup_ui()
        self.setup_sample_data()
        self.create_default_chart()
        
    def setup_ui(self):
        """Setup the demo application UI."""
        self.setWindowTitle("Bar Chart Component Demo - WSJ Style")
        self.setMinimumSize(1200, 800)
        
        # Apply styling
        self.setStyleSheet(self.style_manager.get_main_window_style())
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title = QLabel("Apple Health Dashboard - Bar Chart Component Demo")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
                text-align: center;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Chart container
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout()
        self.chart_container.setLayout(self.chart_layout)
        main_layout.addWidget(self.chart_container)
        
    def create_control_panel(self):
        """Create control panel for demo interactions."""
        panel = QWidget()
        panel.setStyleSheet(self.style_manager.get_card_style())
        layout = QHBoxLayout()
        
        # Chart type selector
        chart_type_label = QLabel("Chart Type:")
        chart_type_label.setStyleSheet("font-weight: 500;")
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Simple", "Grouped", "Stacked"])
        self.chart_type_combo.setStyleSheet(self.style_manager.get_input_style())
        self.chart_type_combo.currentTextChanged.connect(self.change_chart_type)
        
        # Data set selector
        data_set_label = QLabel("Data Set:")
        data_set_label.setStyleSheet("font-weight: 500;")
        self.data_set_combo = QComboBox()
        self.data_set_combo.addItems(["Daily Steps", "Weekly Metrics", "Activity Minutes", "Heart Rate Zones"])
        self.data_set_combo.setStyleSheet(self.style_manager.get_input_style())
        self.data_set_combo.currentTextChanged.connect(self.change_data_set)
        
        # Animation toggle
        self.animation_btn = QPushButton("Toggle Animation")
        self.animation_btn.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.animation_btn.clicked.connect(self.toggle_animation)
        
        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.setStyleSheet(self.style_manager.get_button_style("primary"))
        export_btn.clicked.connect(self.export_current_chart)
        
        # Layout
        layout.addWidget(chart_type_label)
        layout.addWidget(self.chart_type_combo)
        layout.addWidget(data_set_label)
        layout.addWidget(self.data_set_combo)
        layout.addStretch()
        layout.addWidget(self.animation_btn)
        layout.addWidget(export_btn)
        
        panel.setLayout(layout)
        return panel
        
    def setup_sample_data(self):
        """Create sample health data for demonstration."""
        
        # Daily Steps Data (Simple)
        dates = pd.date_range(start='2024-03-10', periods=7, freq='D')
        self.daily_steps_data = pd.DataFrame({
            'Steps': [8542, 9234, 7892, 10345, 6789, 11203, 9567]
        }, index=dates.strftime('%a %m/%d'))
        
        # Weekly Metrics (Grouped)
        weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        self.weekly_metrics_data = pd.DataFrame({
            'Avg Steps': [8500, 9200, 8800, 9500],
            'Avg Heart Rate': [72, 75, 68, 74],
            'Sleep Hours': [7.2, 7.8, 6.9, 7.5]
        }, index=weeks)
        
        # Activity Minutes (Stacked)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.activity_minutes_data = pd.DataFrame({
            'Light Activity': [180, 165, 195, 170, 185, 200, 190],
            'Moderate Activity': [45, 60, 30, 75, 40, 55, 50],
            'Vigorous Activity': [15, 25, 10, 30, 20, 35, 25]
        }, index=days)
        
        # Heart Rate Zones (Grouped)
        zones = ['Resting', 'Fat Burn', 'Cardio', 'Peak']
        self.heart_rate_zones_data = pd.DataFrame({
            'This Week': [180, 120, 45, 15],
            'Last Week': [200, 110, 40, 10],
            'Average': [190, 115, 42, 13]
        }, index=zones)
        
    def create_default_chart(self):
        """Create the default chart display."""
        self.create_chart('Simple', 'Daily Steps')
        
    def create_chart(self, chart_type, data_set):
        """Create and display a chart with specified type and data."""
        
        # Clear existing chart
        if self.current_chart:
            self.chart_layout.removeWidget(self.current_chart)
            self.current_chart.deleteLater()
            
        # Get data based on selection
        if data_set == 'Daily Steps':
            data = self.daily_steps_data
            title = "Daily Step Count - Past Week"
        elif data_set == 'Weekly Metrics':
            data = self.weekly_metrics_data
            title = "Weekly Health Metrics Comparison"
        elif data_set == 'Activity Minutes':
            data = self.activity_minutes_data
            title = "Daily Activity Minutes Breakdown"
        elif data_set == 'Heart Rate Zones':
            data = self.heart_rate_zones_data
            title = "Heart Rate Zone Distribution (Minutes/Day)"
        else:
            data = self.daily_steps_data
            title = "Sample Data"
            
        # Create chart configuration
        config = BarChartConfig(
            animate=True,
            show_value_labels=True,
            show_legend=(chart_type.lower() != 'simple'),
            wsj_style=True,
            clean_spines=True,
            show_grid=True
        )
        
        # Create chart
        self.current_chart = InteractiveBarChart(config)
        
        # Connect signals for demo feedback
        self.current_chart.bar_clicked.connect(self.on_bar_clicked)
        self.current_chart.bar_hovered.connect(self.on_bar_hovered)
        
        # Plot data
        chart_type_map = {
            'Simple': 'simple',
            'Grouped': 'grouped', 
            'Stacked': 'stacked'
        }
        
        self.current_chart.plot(data, chart_type_map[chart_type])
        
        # Add title
        if self.current_chart.ax:
            self.current_chart.ax.set_title(
                title,
                fontsize=16,
                fontweight='600',
                color=StyleManager.TEXT_PRIMARY,
                pad=20
            )
            
        # Add to layout
        self.chart_layout.addWidget(self.current_chart)
        
    def change_chart_type(self, chart_type):
        """Handle chart type change."""
        data_set = self.data_set_combo.currentText()
        self.create_chart(chart_type, data_set)
        
    def change_data_set(self, data_set):
        """Handle data set change."""
        chart_type = self.chart_type_combo.currentText()
        self.create_chart(chart_type, data_set)
        
    def toggle_animation(self):
        """Toggle animation on/off."""
        if self.current_chart:
            self.current_chart.config.animate = not self.current_chart.config.animate
            self.animation_btn.setText(
                "Animation: ON" if self.current_chart.config.animate else "Animation: OFF"
            )
            
    def export_current_chart(self):
        """Export the current chart."""
        if self.current_chart:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bar_chart_export_{timestamp}.png"
            self.current_chart.export_chart(filename, dpi=300)
            print(f"Chart exported as: {filename}")
            
    def on_bar_clicked(self, category, value):
        """Handle bar click events."""
        print(f"Bar clicked - Category: {category}, Value: {value}")
        
    def on_bar_hovered(self, category, value):
        """Handle bar hover events."""
        print(f"Bar hovered - Category: {category}, Value: {value}")


def create_sample_health_data():
    """Create realistic sample health data for demonstration."""
    
    # Generate 30 days of sample data
    dates = pd.date_range(start='2024-03-01', periods=30, freq='D')
    
    # Create realistic health metrics with some variation
    np.random.seed(42)  # For reproducible demo data
    
    daily_data = pd.DataFrame({
        'Steps': np.random.normal(8500, 1500, 30).astype(int),
        'Heart Rate': np.random.normal(72, 8, 30).astype(int),
        'Sleep Hours': np.random.normal(7.5, 1.0, 30),
        'Active Minutes': np.random.normal(45, 15, 30).astype(int),
        'Calories': np.random.normal(2200, 300, 30).astype(int)
    }, index=dates)
    
    # Ensure realistic ranges
    daily_data['Steps'] = daily_data['Steps'].clip(lower=2000, upper=15000)
    daily_data['Heart Rate'] = daily_data['Heart Rate'].clip(lower=55, upper=100)
    daily_data['Sleep Hours'] = daily_data['Sleep Hours'].clip(lower=5.0, upper=10.0)
    daily_data['Active Minutes'] = daily_data['Active Minutes'].clip(lower=10, upper=120)
    daily_data['Calories'] = daily_data['Calories'].clip(lower=1500, upper=3000)
    
    return daily_data


def demonstrate_chart_types():
    """Demonstrate different chart types with sample data."""
    
    print("Creating sample health data...")
    health_data = create_sample_health_data()
    
    # Simple bar chart - Daily steps for a week
    print("\n1. Simple Bar Chart - Daily Steps (Last Week)")
    last_week = health_data.tail(7)
    steps_data = last_week[['Steps']].copy()
    steps_data.index = steps_data.index.strftime('%a %m/%d')
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    config = BarChartConfig(wsj_style=True, animate=True)
    chart = BarChart(config)
    chart.plot(steps_data, 'simple')
    
    print("✓ Simple chart created")
    
    # Grouped bar chart - Multiple metrics comparison
    print("\n2. Grouped Bar Chart - Weekly Metrics Comparison")
    
    # Group by weeks and calculate averages
    health_data['Week'] = health_data.index.isocalendar().week
    weekly_avg = health_data.groupby('Week')[['Steps', 'Heart Rate', 'Active Minutes']].mean()
    weekly_avg.index = [f'Week {w}' for w in weekly_avg.index]
    
    chart2 = BarChart(config)
    chart2.plot(weekly_avg, 'grouped')
    
    print("✓ Grouped chart created")
    
    # Stacked bar chart - Activity breakdown
    print("\n3. Stacked Bar Chart - Activity Breakdown")
    
    # Create activity categories
    activity_data = pd.DataFrame({
        'Light Activity': [180, 165, 195, 170, 185, 200, 190],
        'Moderate Activity': [45, 60, 30, 75, 40, 55, 50],
        'Vigorous Activity': [15, 25, 10, 30, 20, 35, 25]
    }, index=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    
    chart3 = BarChart(config)
    chart3.plot(activity_data, 'stacked')
    
    print("✓ Stacked chart created")
    print("\nAll chart types demonstrated successfully!")


if __name__ == '__main__':
    # Run the demo application
    app = QApplication(sys.argv)
    
    # Apply global styling
    style_manager = StyleManager()
    style_manager.apply_global_style(app)
    
    # Create and show demo window
    demo = BarChartDemo()
    demo.show()
    
    # Optional: Run chart type demonstration
    print("Bar Chart Component Demo")
    print("========================")
    print("Interactive demo window opened.")
    print("\nFeatures demonstrated:")
    print("• WSJ-inspired styling with warm color palette")
    print("• Simple, grouped, and stacked bar charts")
    print("• Smooth animations with easing")
    print("• Interactive hover and click events")
    print("• Value labels with smart positioning")
    print("• Export functionality")
    print("• Responsive design")
    
    # Start the application
    sys.exit(app.exec())