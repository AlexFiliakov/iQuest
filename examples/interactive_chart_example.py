"""
Interactive Chart Controls Example

Demonstrates the new interactive features for health charts including:
- Zoom and pan with momentum
- Brush selection for filtering
- WSJ-styled tooltips
- Keyboard navigation
- Drill-down exploration
- Cross-chart filtering
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Add parent directory to path for imports
sys.path.append('..')

from src.ui.charts import EnhancedLineChart
from src.ui.charts.enhanced_base_chart import EnhancedChartConfig


def generate_sample_health_data():
    """Generate sample health data for demonstration."""
    # Generate 90 days of data
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    
    # Generate realistic health metrics
    np.random.seed(42)
    
    # Steps data with weekly pattern
    steps_base = 8000
    steps_variation = 2000
    weekly_pattern = np.array([0.9, 1.0, 1.1, 1.0, 1.2, 0.7, 0.8])  # Less on weekends
    steps = []
    
    for i, date in enumerate(dates):
        day_of_week = date.dayofweek
        daily_steps = steps_base + steps_variation * (
            weekly_pattern[day_of_week] + 
            0.3 * np.random.randn() +  # Random variation
            0.2 * np.sin(2 * np.pi * i / 30)  # Monthly cycle
        )
        steps.append(max(0, int(daily_steps)))
    
    # Heart rate data
    hr_base = 65
    heart_rate = hr_base + 5 * np.random.randn(len(dates))
    heart_rate = np.clip(heart_rate, 50, 90)
    
    # Sleep hours
    sleep_base = 7.5
    sleep_hours = sleep_base + 1.5 * np.random.randn(len(dates))
    sleep_hours = np.clip(sleep_hours, 4, 10)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'steps': steps,
        'heart_rate': heart_rate,
        'sleep_hours': sleep_hours,
        'calories': steps * 0.04 + np.random.randint(-50, 50, len(dates)),
        'distance_km': steps * 0.0008 + np.random.uniform(-0.1, 0.1, len(dates))
    })
    
    return df


class InteractiveHealthDashboard(QMainWindow):
    """Main window demonstrating interactive chart features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Health Charts Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Add charts
        charts_layout = QHBoxLayout()
        
        # Create interactive charts
        self.steps_chart = self.create_steps_chart()
        self.heart_rate_chart = self.create_heart_rate_chart()
        
        charts_layout.addWidget(self.steps_chart)
        charts_layout.addWidget(self.heart_rate_chart)
        
        main_layout.addLayout(charts_layout)
        
        # Add controls
        controls = self.create_controls()
        main_layout.addWidget(controls)
        
        # Load sample data
        self.data = generate_sample_health_data()
        self.update_charts()
        
        # Setup cross-chart filtering
        self.setup_crossfilter()
        
    def create_header(self):
        """Create header with title and instructions."""
        header = QWidget()
        layout = QVBoxLayout(header)
        
        title = QLabel("<h2>Interactive Health Charts Demo</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel(
            "<p><b>Interactions:</b><br>"
            "• <b>Zoom:</b> Mouse wheel or +/- keys<br>"
            "• <b>Pan:</b> Click and drag or arrow keys<br>"
            "• <b>Select:</b> Shift+Click and drag<br>"
            "• <b>Reset:</b> Press 0 or click Reset button<br>"
            "• <b>Tooltip:</b> Hover over data points<br>"
            "• <b>Drill-down:</b> Double-click on data<br>"
            "• <b>Help:</b> Press F1 or ?</p>"
        )
        instructions.setStyleSheet("QLabel { background-color: #F5E6D3; padding: 10px; }")
        layout.addWidget(instructions)
        
        return header
        
    def create_steps_chart(self):
        """Create interactive steps chart."""
        config = EnhancedChartConfig(
            title="Daily Steps",
            subtitle="90-day trend with weekly patterns",
            x_label="Date",
            y_label="Steps",
            use_wsj_style=True,
            # Enable all interactions
            enable_interactions=True,
            enable_zoom=True,
            enable_pan=True,
            enable_selection=True,
            enable_tooltips=True,
            enable_keyboard_nav=True,
            enable_drill_down=True,
            enable_crossfilter=True
        )
        
        chart = EnhancedLineChart(config)
        chart.setMinimumHeight(400)
        return chart
        
    def create_heart_rate_chart(self):
        """Create interactive heart rate chart."""
        config = EnhancedChartConfig(
            title="Resting Heart Rate",
            subtitle="Daily measurements",
            x_label="Date",
            y_label="BPM",
            use_wsj_style=True,
            # Enable all interactions
            enable_interactions=True,
            enable_zoom=True,
            enable_pan=True,
            enable_selection=True,
            enable_tooltips=True,
            enable_keyboard_nav=True,
            enable_drill_down=True,
            enable_crossfilter=True
        )
        
        chart = EnhancedLineChart(config)
        chart.setMinimumHeight(400)
        return chart
        
    def create_controls(self):
        """Create control buttons."""
        controls = QWidget()
        layout = QHBoxLayout(controls)
        
        # Reset button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_all_views)
        layout.addWidget(reset_btn)
        
        # Zoom buttons
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self.zoom_all(1.5))
        layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self.zoom_all(0.67))
        layout.addWidget(zoom_out_btn)
        
        # Filter info
        self.filter_info = QLabel("No active filters")
        self.filter_info.setStyleSheet("QLabel { padding: 5px; }")
        layout.addWidget(self.filter_info)
        
        layout.addStretch()
        
        return controls
        
    def update_charts(self):
        """Update charts with data."""
        # Prepare data for steps chart
        steps_data = self.data[['date', 'steps']].copy()
        self.steps_chart.set_data(steps_data)
        
        # Prepare data for heart rate chart
        hr_data = self.data[['date', 'heart_rate']].copy()
        self.heart_rate_chart.set_data(hr_data)
        
    def setup_crossfilter(self):
        """Setup cross-chart filtering."""
        # When a range is selected in one chart, filter the other
        if hasattr(self.steps_chart, '_interaction_manager'):
            self.steps_chart._interaction_manager.range_selected.connect(
                lambda start, end: self.filter_heart_rate(start, end)
            )
            
        if hasattr(self.heart_rate_chart, '_interaction_manager'):
            self.heart_rate_chart._interaction_manager.range_selected.connect(
                lambda start, end: self.filter_steps(start, end)
            )
            
    def filter_heart_rate(self, start, end):
        """Filter heart rate chart based on steps selection."""
        # Filter data
        mask = (self.data['date'] >= pd.Timestamp(start)) & (self.data['date'] <= pd.Timestamp(end))
        filtered_data = self.data[mask][['date', 'heart_rate']]
        
        # Update chart
        self.heart_rate_chart.set_data(filtered_data)
        
        # Update filter info
        self.filter_info.setText(f"Filtered: {pd.Timestamp(start).strftime('%Y-%m-%d')} to {pd.Timestamp(end).strftime('%Y-%m-%d')}")
        
    def filter_steps(self, start, end):
        """Filter steps chart based on heart rate selection."""
        # Filter data
        mask = (self.data['date'] >= pd.Timestamp(start)) & (self.data['date'] <= pd.Timestamp(end))
        filtered_data = self.data[mask][['date', 'steps']]
        
        # Update chart
        self.steps_chart.set_data(filtered_data)
        
        # Update filter info
        self.filter_info.setText(f"Filtered: {pd.Timestamp(start).strftime('%Y-%m-%d')} to {pd.Timestamp(end).strftime('%Y-%m-%d')}")
        
    def reset_all_views(self):
        """Reset all chart views."""
        self.steps_chart.reset_view()
        self.heart_rate_chart.reset_view()
        self.filter_info.setText("No active filters")
        
    def zoom_all(self, factor):
        """Zoom all charts."""
        current_zoom_steps = getattr(self.steps_chart._interaction_manager.zoom_controller, 'zoom_level', 1.0)
        current_zoom_hr = getattr(self.heart_rate_chart._interaction_manager.zoom_controller, 'zoom_level', 1.0)
        
        self.steps_chart.set_zoom_level(current_zoom_steps * factor)
        self.heart_rate_chart.set_zoom_level(current_zoom_hr * factor)


def main():
    """Run the interactive demo."""
    app = QApplication(sys.argv)
    
    # Apply global styles
    app.setStyleSheet("""
        QMainWindow {
            background-color: #FFFFFF;
        }
        QPushButton {
            background-color: #FF8C42;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #E67A3A;
        }
        QPushButton:pressed {
            background-color: #CC6A32;
        }
    """)
    
    window = InteractiveHealthDashboard()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()