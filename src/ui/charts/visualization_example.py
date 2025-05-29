"""Example implementation using the new visualization architecture."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

from .enhanced_base_chart import EnhancedBaseChart, EnhancedChartConfig
from .wsj_style_manager import WSJStyleManager


class HealthMetricsLineChart(EnhancedBaseChart):
    """Example line chart for health metrics using the enhanced architecture."""
    
    def __init__(self, config: Optional[EnhancedChartConfig] = None, parent=None):
        """Initialize health metrics line chart."""
        # Set default config for health metrics
        if config is None:
            config = EnhancedChartConfig(
                title="Daily Health Metrics",
                subtitle="Heart Rate and Steps Analysis",
                x_label="Date",
                y_label="Value",
                renderer_type="auto",
                enable_optimization=True,
                enforce_wcag_aa=True,
                use_wsj_style=True,
                fluid_layout=True
            )
        
        super().__init__(config, parent)
        
        # Chart-specific settings
        self._viewport_margin = 0.1
        self._real_time_mode = False
    
    def get_chart_type(self) -> str:
        """Return chart type."""
        return "line"
    
    def requires_real_time(self) -> bool:
        """Check if real-time updates are needed."""
        return self._real_time_mode
    
    def requires_interactivity(self) -> bool:
        """Line charts benefit from interactivity."""
        return True
    
    def is_scientific_chart(self) -> bool:
        """Health metrics can be considered scientific data."""
        return True
    
    def _get_current_viewport(self) -> Optional[Tuple[float, float, float, float]]:
        """Get current viewport for adaptive sampling."""
        if self._data is None or self._data.empty:
            return None
        
        # For this example, use full data range
        # In practice, this would track zoom/pan state
        x_min = self._data.iloc[:, 0].min()
        x_max = self._data.iloc[:, 0].max()
        y_min = self._data.iloc[:, 1].min()
        y_max = self._data.iloc[:, 1].max()
        
        # Add margin
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        return (
            x_min - x_range * self._viewport_margin,
            x_max + x_range * self._viewport_margin,
            y_min - y_range * self._viewport_margin,
            y_max + y_range * self._viewport_margin
        )
    
    def _get_data_summary(self) -> Dict[str, Any]:
        """Get data summary for accessibility."""
        if self._data is None or self._data.empty:
            return {
                'title': self.config.title,
                'data_points': 0,
                'min_value': 'N/A',
                'max_value': 'N/A',
                'average': 'N/A',
                'trend': 'no data'
            }
        
        # Calculate statistics
        values = self._data.iloc[:, 1]
        
        # Simple trend detection
        if len(values) > 1:
            if values.iloc[-1] > values.iloc[0]:
                trend = 'increasing'
            elif values.iloc[-1] < values.iloc[0]:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient data'
        
        return {
            'title': self.config.title,
            'data_points': len(self._data),
            'min_value': f"{values.min():.1f}",
            'max_value': f"{values.max():.1f}",
            'average': f"{values.mean():.1f}",
            'trend': trend,
            'time_range': f"{(self._data.iloc[-1, 0] - self._data.iloc[0, 0]).days} days"
        }
    
    def _get_current_theme(self) -> Any:
        """Get current theme object."""
        # Use WSJ style manager
        style_manager = WSJStyleManager()
        
        # Create theme object based on current settings
        from .base_chart import ChartTheme
        
        if self.config.high_contrast_mode:
            theme = ChartTheme(
                background_color="#000000",
                text_color="#FFFFFF",
                primary_color="#FFFF00",
                secondary_color="#00FFFF",
                grid_color="#666666"
            )
        else:
            # Use WSJ warm palette
            theme = ChartTheme(
                background_color=style_manager.WARM_PALETTE['surface'],
                text_color=style_manager.WARM_PALETTE['text_primary'],
                primary_color=style_manager.WARM_PALETTE['primary'],
                secondary_color=style_manager.WARM_PALETTE['secondary'],
                grid_color=style_manager.WARM_PALETTE['grid']
            )
        
        return theme
    
    def enable_real_time_mode(self, enabled: bool = True):
        """Enable real-time updates."""
        self._real_time_mode = enabled
        
        if enabled:
            # Switch to performance-optimized renderer
            self.set_renderer('pyqtgraph')
        else:
            # Switch back to quality renderer
            self.set_renderer('matplotlib')


class ExampleApp(QMainWindow):
    """Example application demonstrating the visualization architecture."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Metrics Visualization Example")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create chart with custom config
        config = EnhancedChartConfig(
            title="Heart Rate Trends",
            subtitle="Last 30 days",
            x_label="Date",
            y_label="BPM",
            renderer_type="matplotlib",  # Start with matplotlib
            enable_optimization=True,
            max_data_points=5000,
            enforce_wcag_aa=True,
            use_wsj_style=True
        )
        
        self.chart = HealthMetricsLineChart(config)
        layout.addWidget(self.chart)
        
        # Connect signals
        self.chart.renderComplete.connect(self.on_render_complete)
        self.chart.accessibilityReport.connect(self.on_accessibility_report)
        self.chart.performanceReport.connect(self.on_performance_report)
        self.chart.deviceClassChanged.connect(self.on_device_class_changed)
        
        # Generate sample data
        self.generate_sample_data()
        
        # Simulate real-time updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        # self.update_timer.start(1000)  # Update every second
    
    def generate_sample_data(self):
        """Generate sample health data."""
        # Create 90 days of heart rate data
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        
        # Generate realistic heart rate data
        base_hr = 70
        hr_values = []
        
        for i in range(len(dates)):
            # Add daily variation
            daily_variation = np.sin(i / 7 * 2 * np.pi) * 5
            # Add random noise
            noise = np.random.normal(0, 3)
            # Add trend
            trend = i * 0.05
            
            hr = base_hr + daily_variation + noise + trend
            hr_values.append(max(50, min(100, hr)))  # Clamp to realistic range
        
        # Create dataframe
        data = pd.DataFrame({
            'date': dates,
            'heart_rate': hr_values
        })
        
        # Set data on chart
        self.chart.set_data(data)
    
    def update_data(self):
        """Simulate real-time data updates."""
        # Add new data point
        if hasattr(self, 'chart') and self.chart._data is not None:
            last_date = self.chart._data.iloc[-1, 0]
            new_date = last_date + timedelta(days=1)
            
            # Generate new heart rate value
            last_hr = self.chart._data.iloc[-1, 1]
            new_hr = last_hr + np.random.normal(0, 2)
            new_hr = max(50, min(100, new_hr))
            
            # Append to data
            new_row = pd.DataFrame({
                'date': [new_date],
                'heart_rate': [new_hr]
            })
            
            updated_data = pd.concat([self.chart._data, new_row], ignore_index=True)
            
            # Keep only last 90 days
            if len(updated_data) > 90:
                updated_data = updated_data.iloc[-90:]
            
            self.chart.set_data(updated_data)
    
    def on_render_complete(self, render_time: float):
        """Handle render completion."""
        print(f"Chart rendered in {render_time:.1f}ms")
    
    def on_accessibility_report(self, report):
        """Handle accessibility report."""
        if report.compliant:
            print(f"✓ Accessibility compliant (WCAG {report.wcag_level})")
        else:
            print(f"✗ Accessibility issues found:")
            for issue in report.issues:
                print(f"  - {issue}")
    
    def on_performance_report(self, metrics):
        """Handle performance metrics."""
        print(f"Performance: {metrics.data_points} points, "
              f"{metrics.render_time_ms:.1f}ms render, "
              f"{metrics.memory_usage_mb:.1f}MB memory")
    
    def on_device_class_changed(self, device_class):
        """Handle device class changes."""
        print(f"Device class changed to: {device_class.value}")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        if key == Qt.Key.Key_H:
            # Toggle high contrast
            current = self.chart.config.high_contrast_mode
            self.chart.enable_high_contrast_mode(not current)
            print(f"High contrast mode: {'ON' if not current else 'OFF'}")
        
        elif key == Qt.Key.Key_R:
            # Cycle through renderers
            renderers = ['matplotlib', 'qpainter', 'pyqtgraph']
            current_idx = renderers.index(self.chart.config.renderer_type)
            next_idx = (current_idx + 1) % len(renderers)
            self.chart.set_renderer(renderers[next_idx])
            print(f"Switched to {renderers[next_idx]} renderer")
        
        elif key == Qt.Key.Key_T:
            # Toggle real-time mode
            current = self.chart._real_time_mode
            self.chart.enable_real_time_mode(not current)
            
            if not current:
                self.update_timer.start(100)  # Fast updates
            else:
                self.update_timer.stop()
            
            print(f"Real-time mode: {'ON' if not current else 'OFF'}")
        
        elif key == Qt.Key.Key_Q:
            # Cycle quality modes
            qualities = ['performance', 'balanced', 'quality']
            current_idx = qualities.index(self.chart.config.render_quality)
            next_idx = (current_idx + 1) % len(qualities)
            self.chart.config.render_quality = qualities[next_idx]
            self.chart._optimize_data()
            self.chart._render_chart()
            print(f"Render quality: {qualities[next_idx]}")


def main():
    """Run the example application."""
    app = QApplication([])
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = ExampleApp()
    window.show()
    
    # Print instructions
    print("Visualization Architecture Example")
    print("==================================")
    print("Keyboard shortcuts:")
    print("  H - Toggle high contrast mode")
    print("  R - Cycle through renderers")
    print("  T - Toggle real-time mode")
    print("  Q - Cycle render quality")
    print()
    
    app.exec()


if __name__ == "__main__":
    main()