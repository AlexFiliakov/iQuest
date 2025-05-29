"""Demo of the health insight annotation system"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import Qt

# Add parent directory to path for imports
sys.path.append('..')

from src.ui.charts.annotated_chart_widget import AnnotatedHealthChart, AnnotationPreferencesWidget
from src.ui.charts.annotation_integration import add_annotations_to_chart
from src.ui.charts.enhanced_line_chart import EnhancedLineChart


def generate_sample_health_data(days: int = 180) -> pd.DataFrame:
    """Generate sample health data with patterns for annotation demo"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate base pattern with weekly cycles
    base_values = 8000 + 2000 * np.sin(np.arange(days) * 2 * np.pi / 7)
    
    # Add trend
    trend = np.linspace(0, 1000, days)
    
    # Add noise
    noise = np.random.normal(0, 500, days)
    
    # Add some anomalies
    values = base_values + trend + noise
    
    # Insert specific patterns for demonstration
    # Achievement: Personal record
    values[150] = 15000  # Big spike for achievement
    
    # Anomaly: Unusual low
    values[100] = 3000  # Unusual drop
    
    # Streak: Consistent high performance
    values[160:167] = 12000  # Week of high performance
    
    # Goal milestone
    values[170] = 10000  # Hit 10k goal
    
    return pd.DataFrame({
        'date': dates,
        'value': values
    })


class AnnotationDemoWindow(QMainWindow):
    """Demo window showing annotation system capabilities"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Insight Annotations Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Tab 1: Annotated chart with controls
        self.annotated_chart = AnnotatedHealthChart()
        tabs.addTab(self.annotated_chart, "Annotated Health Chart")
        
        # Tab 2: Comparison - with and without annotations
        comparison_widget = self._create_comparison_tab()
        tabs.addTab(comparison_widget, "With/Without Annotations")
        
        # Tab 3: Annotation preferences
        self.preferences = AnnotationPreferencesWidget()
        self.preferences.preferences_changed.connect(self._on_preferences_changed)
        tabs.addTab(self.preferences, "Annotation Preferences")
        
        # Load sample data
        self._load_sample_data()
        
        # Connect signals
        self.annotated_chart.annotation_clicked.connect(self._on_annotation_clicked)
    
    def _create_comparison_tab(self) -> QWidget:
        """Create comparison tab showing charts with and without annotations"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chart without annotations
        self.plain_chart = EnhancedLineChart()
        self.plain_chart.setFixedHeight(350)
        layout.addWidget(self.plain_chart)
        
        # Chart with annotations (using integration)
        base_chart = EnhancedLineChart()
        self.integrated_chart = add_annotations_to_chart(base_chart)
        self.integrated_chart.setFixedHeight(350)
        layout.addWidget(self.integrated_chart)
        
        return widget
    
    def _load_sample_data(self):
        """Load sample data into all charts"""
        # Generate sample data
        data = generate_sample_health_data()
        
        # Load into annotated chart
        self.annotated_chart.set_data(data, metric_type='steps')
        
        # Load into comparison charts
        self.plain_chart.set_data(data, title="Steps (No Annotations)")
        self.integrated_chart.set_data(data, title="Steps (With Annotations)")
    
    def _on_annotation_clicked(self, annotation_id: str):
        """Handle annotation click"""
        annotation = self.annotated_chart.get_annotation_by_id(annotation_id)
        if annotation:
            print(f"Clicked annotation: {annotation.title}")
            print(f"Description: {annotation.description}")
            print(f"Type: {annotation.type.value}")
            print(f"Date: {annotation.data_point}")
            print(f"Value: {annotation.value}")
            print("-" * 50)
    
    def _on_preferences_changed(self, preferences: dict):
        """Handle preference changes"""
        print("Preferences updated:", preferences)
        # Apply preferences to charts
        # This would update annotation display settings


def main():
    """Run the annotation demo"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    window = AnnotationDemoWindow()
    window.show()
    
    # Print demo information
    print("Health Insight Annotations Demo")
    print("=" * 50)
    print("This demo shows the following annotation features:")
    print("1. Automatic anomaly detection (unusual patterns)")
    print("2. Achievement markers (personal records)")
    print("3. Trend indicators (improving/declining trends)")
    print("4. Contextual insights (helpful explanations)")
    print("5. Goal milestones (10K steps achievement)")
    print("6. WSJ-styled visual hierarchy")
    print("7. Interactive annotations (click to expand)")
    print("8. Customizable preferences")
    print()
    print("Try clicking on annotations to see details!")
    print("=" * 50)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()