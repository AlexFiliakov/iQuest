"""Example usage of the MetricTable component."""

import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

# Add src directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from ui.table_components import MetricTable, TableConfig


class TableExampleWindow(QMainWindow):
    """Example window demonstrating table component usage."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Metrics Table Example")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        self.load_sample_btn = QPushButton("Load Sample Data")
        self.load_sample_btn.clicked.connect(self.load_sample_data)
        
        self.load_large_btn = QPushButton("Load Large Dataset (10k rows)")
        self.load_large_btn.clicked.connect(self.load_large_dataset)
        
        self.clear_btn = QPushButton("Clear Data")
        self.clear_btn.clicked.connect(self.clear_data)
        
        controls_layout.addWidget(self.load_sample_btn)
        controls_layout.addWidget(self.load_large_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Create table with custom configuration
        config = TableConfig(
            page_size=25,
            alternating_rows=True,
            multi_select=True,
            export_formats=['csv', 'excel', 'json']
        )
        
        self.table = MetricTable(config)
        self.table.row_selected.connect(self.on_row_selected)
        self.table.data_exported.connect(self.on_data_exported)
        
        layout.addWidget(self.table)
        
        central_widget.setLayout(layout)
        
        # Load initial sample data
        self.load_sample_data()
    
    def create_sample_data(self, num_rows=100):
        """Create sample health data."""
        np.random.seed(42)
        
        start_date = pd.Timestamp('2024-01-01')
        dates = [start_date + pd.Timedelta(days=i) for i in range(num_rows)]
        
        data = {
            'Date': dates,
            'Heart Rate (bpm)': np.random.normal(70, 10, num_rows).astype(int),
            'Steps': np.random.normal(8000, 2000, num_rows).astype(int),
            'Sleep Hours': np.random.normal(7.5, 1, num_rows).round(1),
            'Weight (kg)': np.random.normal(70, 5, num_rows).round(1),
            'Active Energy (kcal)': np.random.normal(400, 150, num_rows).astype(int),
            'Exercise Minutes': np.random.poisson(30, num_rows),
            'Source Device': np.random.choice(['iPhone 14', 'Apple Watch Series 8', 'iPad', 'Third Party App'], num_rows),
            'Data Quality': np.random.choice(['High', 'Medium', 'Low'], num_rows, p=[0.7, 0.2, 0.1]),
            'Resting HR (bpm)': np.random.normal(60, 8, num_rows).astype(int),
            'VO2 Max': np.random.normal(35, 8, num_rows).round(1),
            'Blood Pressure Systolic': np.random.normal(120, 15, num_rows).astype(int),
            'Blood Pressure Diastolic': np.random.normal(80, 10, num_rows).astype(int),
            'Body Fat %': np.random.normal(18, 5, num_rows).round(1),
            'Hydration (L)': np.random.normal(2.5, 0.5, num_rows).round(1)
        }
        
        df = pd.DataFrame(data)
        
        # Add some realistic constraints
        df.loc[df['Heart Rate (bpm)'] < 50, 'Heart Rate (bpm)'] = 50
        df.loc[df['Heart Rate (bpm)'] > 200, 'Heart Rate (bpm)'] = 200
        df.loc[df['Steps'] < 0, 'Steps'] = 0
        df.loc[df['Sleep Hours'] < 0, 'Sleep Hours'] = 0
        df.loc[df['Sleep Hours'] > 12, 'Sleep Hours'] = 12
        df.loc[df['Weight (kg)'] < 40, 'Weight (kg)'] = 40
        df.loc[df['Weight (kg)'] > 150, 'Weight (kg)'] = 150
        
        return df
    
    def load_sample_data(self):
        """Load sample data into the table."""
        data = self.create_sample_data(100)
        self.table.load_data(data)
        print(f"Loaded {len(data)} rows of sample health data")
    
    def load_large_dataset(self):
        """Load a large dataset to demonstrate performance."""
        data = self.create_sample_data(10000)
        self.table.load_data(data)
        print(f"Loaded {len(data)} rows of health data")
    
    def clear_data(self):
        """Clear all data from the table."""
        self.table.clear_data()
        print("Table data cleared")
    
    def on_row_selected(self, row_index):
        """Handle row selection."""
        selected_data = self.table.get_selected_data()
        if selected_data is not None and len(selected_data) > 0:
            first_row = selected_data.iloc[0]
            print(f"Selected row {row_index}: Date={first_row['Date']}, HR={first_row['Heart Rate (bpm)']} bpm")
    
    def on_data_exported(self, filename):
        """Handle successful data export."""
        print(f"Data successfully exported to: {filename}")


def main():
    """Run the table example application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Health Metrics Table Example")
    app.setApplicationVersion("1.0")
    
    # Create and show window
    window = TableExampleWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()