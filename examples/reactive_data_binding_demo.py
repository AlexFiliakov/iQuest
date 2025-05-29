"""
Demonstration of Reactive Data Binding System for Health Visualizations

This example shows how to use the reactive data binding system to create
live-updating health visualizations.
"""

import sys
import random
from datetime import datetime, timedelta

import pandas as pd
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout

# Import reactive data binding components
from src.ui.reactive_data_binding import ReactiveHealthDataStore, ReactiveDataBinding
from src.ui.reactive_health_integration import ReactiveHealthDataBinding, create_reactive_heart_rate_chart
from src.ui.reactive_data_transformations import (
    TransformationPipeline, AggregationTransformation, 
    SlidingWindowTransformation, HealthMetricTransformation
)
from src.ui.charts.reactive_chart_enhancements import make_chart_reactive

# Import chart components
from src.ui.charts.line_chart import LineChart
from src.ui.charts.enhanced_line_chart import EnhancedLineChart
from src.ui.component_factory import ComponentFactory


class ReactiveHealthDashboard(QMainWindow):
    """Example dashboard with reactive data binding"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reactive Health Dashboard Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize reactive components
        self.data_store = ReactiveHealthDataStore()
        self.binding_system = ReactiveHealthDataBinding()
        
        # Setup UI
        self.setup_ui()
        
        # Setup data simulation
        self.setup_data_simulation()
        
        # Create reactive bindings
        self.create_bindings()
        
    def setup_ui(self):
        """Create the UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Control buttons
        controls = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Real-time Updates")
        self.start_btn.clicked.connect(self.start_updates)
        controls.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Updates")
        self.stop_btn.clicked.connect(self.stop_updates)
        self.stop_btn.setEnabled(False)
        controls.addWidget(self.stop_btn)
        
        self.burst_btn = QPushButton("Simulate Data Burst")
        self.burst_btn.clicked.connect(self.simulate_burst)
        controls.addWidget(self.burst_btn)
        
        layout.addLayout(controls)
        
        # Create charts using factory
        factory = ComponentFactory()
        
        # Heart rate chart with real-time updates
        self.heart_rate_chart = factory.create_line_chart(
            title="Real-time Heart Rate",
            data=pd.DataFrame(),
            config={
                'x_column': 'timestamp',
                'y_columns': ['heart_rate'],
                'show_legend': True,
                'enable_zoom': True,
                'animation_duration': 100
            }
        )
        
        # Make it reactive
        ReactiveChart = make_chart_reactive(type(self.heart_rate_chart))
        reactive_hr_chart = ReactiveChart()
        reactive_hr_chart.__dict__.update(self.heart_rate_chart.__dict__)
        self.heart_rate_chart = reactive_hr_chart
        self.heart_rate_chart.enable_reactive_updates('incremental')
        
        layout.addWidget(self.heart_rate_chart)
        
        # Activity chart with aggregation
        self.activity_chart = factory.create_bar_chart(
            title="Hourly Activity Summary",
            data=pd.DataFrame(),
            config={
                'x_column': 'hour',
                'y_column': 'steps',
                'color_column': 'activity_intensity'
            }
        )
        layout.addWidget(self.activity_chart)
        
        # Sleep quality chart
        self.sleep_chart = factory.create_enhanced_line_chart(
            title="Sleep Quality Trends",
            data=pd.DataFrame()
        )
        layout.addWidget(self.sleep_chart)
        
    def setup_data_simulation(self):
        """Setup timers for data simulation"""
        # Real-time heart rate updates (every second)
        self.hr_timer = QTimer()
        self.hr_timer.timeout.connect(self.update_heart_rate)
        
        # Activity updates (every 5 seconds)
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.update_activity)
        
        # Sleep updates (every 10 seconds)
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.update_sleep)
        
    def create_bindings(self):
        """Create reactive data bindings"""
        # Heart rate binding with sliding window
        hr_transform = TransformationPipeline([
            SlidingWindowTransformation(10, 'mean'),  # 10-second moving average
            HealthMetricTransformation('heart_rate_zones')
        ])
        
        self.hr_binding = self.binding_system.bind_chart(
            self.heart_rate_chart,
            self.data_store,
            transform=lambda df: hr_transform.transform(df)
        )
        
        # Activity binding with hourly aggregation
        activity_transform = TransformationPipeline([
            AggregationTransformation('H', 'sum'),
            HealthMetricTransformation('activity_intensity')
        ])
        
        self.activity_binding = self.binding_system.bind_chart(
            self.activity_chart,
            self.data_store,
            transform=lambda df: activity_transform.transform(df)
        )
        
        # Sleep binding
        sleep_transform = TransformationPipeline([
            HealthMetricTransformation('sleep_quality')
        ])
        
        self.sleep_binding = self.binding_system.bind_chart(
            self.sleep_chart,
            self.data_store,
            transform=lambda df: sleep_transform.transform(df)
        )
        
    def start_updates(self):
        """Start real-time data updates"""
        self.hr_timer.start(1000)  # Every second
        self.activity_timer.start(5000)  # Every 5 seconds
        self.sleep_timer.start(10000)  # Every 10 seconds
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def stop_updates(self):
        """Stop real-time data updates"""
        self.hr_timer.stop()
        self.activity_timer.stop()
        self.sleep_timer.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def update_heart_rate(self):
        """Simulate heart rate data update"""
        # Generate realistic heart rate
        base_hr = 70
        variation = random.gauss(0, 5)
        heart_rate = max(50, min(150, base_hr + variation))
        
        # Update data store
        self.data_store.update_metric('heart_rate', heart_rate, datetime.now())
        
    def update_activity(self):
        """Simulate activity data update"""
        # Generate activity data
        time_of_day = datetime.now().hour
        
        # More steps during day, fewer at night
        if 6 <= time_of_day <= 22:
            steps = random.randint(50, 500)
        else:
            steps = random.randint(0, 50)
            
        self.data_store.update_metric('steps', steps, datetime.now())
        
    def update_sleep(self):
        """Simulate sleep data update"""
        # Generate sleep duration (in hours)
        sleep_duration = random.gauss(7.5, 1.0)
        sleep_duration = max(4, min(12, sleep_duration))
        
        self.data_store.update_metric('sleep_duration', sleep_duration, datetime.now())
        
    def simulate_burst(self):
        """Simulate a burst of data updates"""
        # Generate 100 historical data points
        now = datetime.now()
        
        data_points = []
        for i in range(100):
            timestamp = now - timedelta(minutes=100-i)
            data_points.append({
                'timestamp': timestamp,
                'heart_rate': 70 + random.gauss(0, 10),
                'steps': random.randint(0, 1000),
                'sleep_duration': random.gauss(7, 1)
            })
            
        # Create DataFrame and update
        burst_data = pd.DataFrame(data_points).set_index('timestamp')
        self.data_store.update_data(burst_data)
        
        print(f"Simulated burst of {len(data_points)} data points")


def demonstrate_conflict_resolution():
    """Demonstrate conflict resolution in concurrent updates"""
    from src.ui.reactive_change_detection import ConflictResolver, ConflictResolutionStrategy
    
    print("\n=== Conflict Resolution Demo ===")
    
    # Create resolver with last-write-wins strategy
    resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
    
    # Simulate concurrent updates
    resolver.add_change('heart_rate', 75, 'sensor1', datetime.now())
    resolver.add_change('heart_rate', 78, 'sensor2', datetime.now() + timedelta(seconds=1))
    resolver.add_change('heart_rate', 76, 'sensor3', datetime.now() + timedelta(seconds=2))
    
    # Resolve conflicts
    resolved = resolver.resolve_conflicts()
    print(f"Resolved heart_rate: {resolved['heart_rate']} (using last-write-wins)")
    
    # Show conflict log
    conflicts = resolver.get_conflict_log()
    for conflict in conflicts:
        print(f"Conflict at {conflict.timestamp}: {conflict.key} = {conflict.values}")


def demonstrate_performance_optimization():
    """Demonstrate performance optimization features"""
    from src.ui.reactive_change_detection import UpdateScheduler
    
    print("\n=== Performance Optimization Demo ===")
    
    # Create update scheduler
    scheduler = UpdateScheduler(batch_size=50, max_delay_ms=100)
    
    # Track when updates are processed
    processed_count = 0
    
    def process_updates(updates):
        nonlocal processed_count
        processed_count += 1
        print(f"Processing batch {processed_count}: {len(updates)} updates")
        
    scheduler.update_ready.connect(process_updates)
    
    # Schedule many updates rapidly
    print("Scheduling 200 updates...")
    for i in range(200):
        scheduler.schedule_update(f"update_{i}")
        
    # Wait for processing
    import time
    time.sleep(0.5)
    
    print(f"Total batches processed: {processed_count}")


def main():
    """Run the demo application"""
    app = QApplication(sys.argv)
    
    # Apply warm color theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5E6D3;
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
            background-color: #FF7A2F;
        }
        QPushButton:disabled {
            background-color: #CCCCCC;
        }
    """)
    
    # Create and show dashboard
    dashboard = ReactiveHealthDashboard()
    dashboard.show()
    
    # Run additional demos
    demonstrate_conflict_resolution()
    demonstrate_performance_optimization()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()