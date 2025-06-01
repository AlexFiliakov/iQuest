"""
Example of making a line chart accessible.

Shows how to integrate accessibility features into existing chart components.
"""

from typing import List, Dict, Any
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from ..charts.line_chart import LineChart
from .accessible_chart_mixin import AccessibleChartMixin
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class AccessibleLineChart(LineChart, AccessibleChartMixin):
    """Line chart with full accessibility support."""
    
    def __init__(self, parent=None):
        """Initialize accessible line chart."""
        LineChart.__init__(self, parent)
        AccessibleChartMixin.__init__(self)
        
        # Enable accessibility by default
        self.enable_accessibility()
        
        # Track focused data point for keyboard navigation
        self._focused_point_index = -1
    
    def get_chart_type(self) -> str:
        """Return chart type for accessibility."""
        return "line"
    
    def get_data_summary(self) -> str:
        """Provide summary of line chart data."""
        if not self._data:
            return "No data available"
        
        # Find min/max values
        values = [point.get('value', 0) for point in self._data]
        if not values:
            return "No data values"
        
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        summary = (f"Line chart showing {len(values)} data points. "
                  f"Values range from {min_val:.1f} to {max_val:.1f}, "
                  f"with an average of {avg_val:.1f}")
        
        # Add trend information
        if len(values) > 1:
            trend = "increasing" if values[-1] > values[0] else "decreasing"
            summary += f". Overall trend is {trend}"
        
        return summary
    
    def get_key_insights(self) -> List[str]:
        """Extract key insights from the data."""
        insights = []
        
        if not self._data:
            return insights
        
        values = [point.get('value', 0) for point in self._data]
        if len(values) < 2:
            return insights
        
        # Find significant changes
        max_change = 0
        max_change_idx = 0
        
        for i in range(1, len(values)):
            change = abs(values[i] - values[i-1])
            if change > max_change:
                max_change = change
                max_change_idx = i
        
        if max_change > 0:
            direction = "increase" if values[max_change_idx] > values[max_change_idx-1] else "decrease"
            insights.append(
                f"Largest {direction} of {max_change:.1f} occurred at point {max_change_idx + 1}"
            )
        
        # Check for peaks
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                insights.append(f"Peak value of {values[i]:.1f} at point {i + 1}")
                break  # Just report first peak
        
        return insights[:3]  # Limit to 3 insights
    
    def paintEvent(self, event):
        """Paint the chart with accessibility enhancements."""
        # Call parent paint method
        super().paintEvent(event)
        
        # Add focus indicator if in keyboard navigation mode
        if self._focused_point_index >= 0 and self._focused_point_index < len(self._data):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw focus ring around focused point
            point = self._get_point_position(self._focused_point_index)
            if point:
                # High contrast focus indicator
                if self._high_contrast_mode:
                    painter.setPen(QPen(QColor('#000000'), 3))
                else:
                    painter.setPen(QPen(QColor('#0066CC'), 3))
                
                painter.drawEllipse(point, 8, 8)
            
            painter.end()
    
    def _get_point_position(self, index: int):
        """Get screen position of data point at index."""
        # This would need to be implemented based on the chart's coordinate system
        # For now, return None
        return None
    
    def _create_element_announcement(self, index: int) -> str:
        """Create detailed announcement for data point."""
        if index < 0 or index >= len(self._data):
            return "No data point"
        
        point = self._data[index]
        value = point.get('value', 0)
        label = point.get('label', f'Point {index + 1}')
        
        announcement = f"{label}: {value:.1f}"
        
        # Add context
        if index > 0:
            prev_value = self._data[index - 1].get('value', 0)
            change = value - prev_value
            if change > 0:
                announcement += f", up {change:.1f} from previous"
            elif change < 0:
                announcement += f", down {abs(change):.1f} from previous"
        
        # Add position context
        announcement += f". Point {index + 1} of {len(self._data)}"
        
        return announcement
    
    def navigate(self, direction: str) -> bool:
        """Navigate through data points."""
        if direction == 'left':
            return self.navigate_previous()
        elif direction == 'right':
            return self.navigate_next()
        elif direction == 'up':
            # Could navigate to higher values
            return False
        elif direction == 'down':
            # Could navigate to lower values
            return False
        
        return False
    
    def navigate_previous(self) -> bool:
        """Navigate to previous data point."""
        if self._focused_point_index > 0:
            self._focused_point_index -= 1
            self._current_focus_index = self._focused_point_index
            self._update_focus()
            return True
        elif self._focused_point_index == -1 and self._data:
            # Start navigation
            self._focused_point_index = len(self._data) - 1
            self._current_focus_index = self._focused_point_index
            self._update_focus()
            return True
        
        return False
    
    def navigate_next(self) -> bool:
        """Navigate to next data point."""
        if self._focused_point_index < len(self._data) - 1:
            self._focused_point_index += 1
            self._current_focus_index = self._focused_point_index
            self._update_focus()
            return True
        elif self._focused_point_index == -1 and self._data:
            # Start navigation
            self._focused_point_index = 0
            self._current_focus_index = self._focused_point_index
            self._update_focus()
            return True
        
        return False


def example_usage():
    """Example of using accessible line chart."""
    app = QApplication([])
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Accessible Line Chart Example")
    
    # Create accessible chart
    chart = AccessibleLineChart()
    chart.set_title("Heart Rate Over Time")
    chart.set_subtitle("Daily average heart rate measurements")
    
    # Sample data
    data = [
        {'label': 'Monday', 'value': 72},
        {'label': 'Tuesday', 'value': 75},
        {'label': 'Wednesday', 'value': 71},
        {'label': 'Thursday', 'value': 78},
        {'label': 'Friday', 'value': 74},
        {'label': 'Saturday', 'value': 69},
        {'label': 'Sunday', 'value': 70}
    ]
    
    chart.set_data(data)
    
    # Connect accessibility signals
    chart.accessibility_announcement.connect(
        lambda msg: print(f"Screen reader: {msg}")
    )
    
    chart.focus_changed.connect(
        lambda msg: print(f"Focus: {msg}")
    )
    
    # Set up window
    central_widget = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(chart)
    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)
    
    # Show instructions
    print("Accessibility Keyboard Shortcuts:")
    print("- Left/Right arrows: Navigate between data points")
    print("- Home/End: Jump to first/last data point")
    print("- A: Announce current data point")
    print("- C: Toggle high contrast mode")
    print("- T: Show data table view")
    print()
    
    window.show()
    
    # Focus the chart
    chart.setFocus()
    
    return app.exec()


if __name__ == "__main__":
    example_usage()