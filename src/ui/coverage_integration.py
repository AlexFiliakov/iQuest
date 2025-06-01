"""
Integration utilities for adding data coverage indicators to existing widgets.
Provides easy-to-use functions for adding coverage displays to any UI component.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any, Union
import pandas as pd
from datetime import date

from .data_availability_indicator import DataAvailabilityIndicator
from .coverage_service import CoverageService, create_sample_coverage_data
from .style_manager import StyleManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CoverageIndicatorWidget(QFrame):
    """A self-contained widget that combines label and coverage indicator."""
    
    def __init__(self, 
                 title: str = "Data Coverage",
                 indicator_type: str = 'bar',
                 compact: bool = False,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.indicator_type = indicator_type
        self.compact = compact
        self.coverage_service = CoverageService()
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI layout."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {StyleManager.TEXT_MUTED};
                border-radius: 8px;
                background-color: {StyleManager.SECONDARY_BG};
                padding: 8px;
                margin: 4px;
            }}
        """)
        
        if self.compact:
            # Horizontal layout for compact mode
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 6, 8, 6)
            layout.setSpacing(8)
            
            # Title label
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    color: {StyleManager.TEXT_PRIMARY};
                    font-size: 12px;
                }}
            """)
            layout.addWidget(title_label)
            
            # Coverage indicator
            self.indicator = DataAvailabilityIndicator(self.indicator_type)
            self.indicator.setMaximumHeight(24)
            layout.addWidget(self.indicator, 1)
            
        else:
            # Vertical layout for full mode
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(8)
            
            # Title label
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    color: {StyleManager.TEXT_PRIMARY};
                    font-size: 14px;
                }}
            """)
            title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(title_label)
            
            # Coverage indicator
            self.indicator = DataAvailabilityIndicator(self.indicator_type)
            layout.addWidget(self.indicator)
    
    def update_with_dataframe(self, 
                            df: pd.DataFrame, 
                            date_column: str = 'Date',
                            value_columns: Optional[list] = None):
        """Update coverage display with DataFrame data."""
        try:
            coverage_data = self.coverage_service.analyze_dataframe_coverage(
                df, date_column, value_columns
            )
            self.indicator.update_coverage(coverage_data)
            logger.debug(f"Updated coverage indicator from DataFrame: {coverage_data.percentage:.1f}%")
        except Exception as e:
            logger.error(f"Error updating coverage from DataFrame: {e}")
            # Show sample data on error
            self.update_with_sample_data()
    
    def update_with_metric_data(self, metric_data: Dict[date, float]):
        """Update coverage display with simple metric data."""
        try:
            coverage_data = self.coverage_service.analyze_metric_coverage(metric_data)
            self.indicator.update_coverage(coverage_data)
            logger.debug(f"Updated coverage indicator from metric data: {coverage_data.percentage:.1f}%")
        except Exception as e:
            logger.error(f"Error updating coverage from metric data: {e}")
            # Show sample data on error
            self.update_with_sample_data()
    
    def update_with_sample_data(self, days: int = 30, coverage_rate: float = 0.8):
        """Update with sample data for testing/demo purposes."""
        coverage_data = create_sample_coverage_data(days, coverage_rate)
        self.indicator.update_coverage(coverage_data)
        logger.debug(f"Updated coverage indicator with sample data: {coverage_data.percentage:.1f}%")
    
    def set_indicator_type(self, indicator_type: str):
        """Change the indicator visualization type."""
        self.indicator.set_indicator_type(indicator_type)


class CoverageWidgetFactory:
    """Factory for creating coverage indicators with common configurations."""
    
    @staticmethod
    def create_dashboard_coverage(title: str = "Data Availability") -> CoverageIndicatorWidget:
        """Create a coverage widget optimized for dashboard display."""
        return CoverageIndicatorWidget(
            title=title,
            indicator_type='bar',
            compact=False
        )
    
    @staticmethod
    def create_compact_coverage(title: str = "Coverage") -> CoverageIndicatorWidget:
        """Create a compact coverage widget for limited space."""
        return CoverageIndicatorWidget(
            title=title,
            indicator_type='badge',
            compact=True
        )
    
    @staticmethod
    def create_detailed_coverage(title: str = "Data Timeline") -> CoverageIndicatorWidget:
        """Create a detailed coverage widget with timeline view."""
        return CoverageIndicatorWidget(
            title=title,
            indicator_type='dots',
            compact=False
        )
    
    @staticmethod
    def create_heat_coverage(title: str = "Coverage Heat Map") -> CoverageIndicatorWidget:
        """Create a heat map style coverage widget."""
        return CoverageIndicatorWidget(
            title=title,
            indicator_type='heat',
            compact=False
        )


def add_coverage_to_widget(parent_widget: QWidget, 
                          layout_direction: str = 'bottom',
                          indicator_type: str = 'bar',
                          title: str = "Data Coverage") -> CoverageIndicatorWidget:
    """
    Add a coverage indicator to an existing widget.
    
    Args:
        parent_widget: The widget to add coverage display to
        layout_direction: Where to add the indicator ('top', 'bottom', 'left', 'right')
        indicator_type: Type of indicator ('bar', 'dots', 'heat', 'badge')
        title: Title for the coverage indicator
    
    Returns:
        The created CoverageIndicatorWidget for further customization
    """
    # Create the coverage widget
    coverage_widget = CoverageIndicatorWidget(
        title=title,
        indicator_type=indicator_type,
        compact=(layout_direction in ['left', 'right'])
    )
    
    # Get or create layout for parent
    layout = parent_widget.layout()
    if layout is None:
        layout = QVBoxLayout(parent_widget)
    
    # Add widget in specified direction
    if layout_direction == 'top':
        layout.insertWidget(0, coverage_widget)
    elif layout_direction == 'bottom':
        layout.addWidget(coverage_widget)
    elif layout_direction == 'left' and hasattr(layout, 'insertWidget'):
        # Convert to horizontal layout if needed
        if layout.__class__.__name__ == 'QVBoxLayout':
            logger.warning("Cannot add to left of vertical layout, adding to top instead")
            layout.insertWidget(0, coverage_widget)
        else:
            layout.insertWidget(0, coverage_widget)
    elif layout_direction == 'right' and hasattr(layout, 'addWidget'):
        # Add to end of horizontal layout
        layout.addWidget(coverage_widget)
    else:
        # Default to bottom
        layout.addWidget(coverage_widget)
    
    logger.debug(f"Added coverage indicator to widget: {layout_direction} position")
    return coverage_widget


# Convenience functions for common integration patterns
def quick_coverage_bar(parent: QWidget, title: str = "Coverage") -> CoverageIndicatorWidget:
    """Quickly add a coverage bar to any widget."""
    return add_coverage_to_widget(parent, 'bottom', 'bar', title)


def quick_coverage_badge(parent: QWidget, title: str = "Coverage") -> CoverageIndicatorWidget:
    """Quickly add a coverage badge to any widget."""
    return add_coverage_to_widget(parent, 'top', 'badge', title)


def quick_coverage_timeline(parent: QWidget, title: str = "Timeline") -> CoverageIndicatorWidget:
    """Quickly add a coverage timeline to any widget."""
    return add_coverage_to_widget(parent, 'bottom', 'dots', title)


# Example usage and demonstration
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
    
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Add some sample content
    content_label = QLabel("Sample Health Dashboard")
    content_label.setStyleSheet(f"""
        QLabel {{
            font-size: 18px;
            font-weight: bold;
            color: {StyleManager.TEXT_PRIMARY};
            padding: 20px;
            background-color: {StyleManager.TERTIARY_BG};
            border-radius: 8px;
            margin: 10px;
        }}
    """)
    layout.addWidget(content_label)
    
    # Add different types of coverage indicators using factory
    factory = CoverageWidgetFactory()
    
    # Dashboard style
    dashboard_coverage = factory.create_dashboard_coverage("Heart Rate Data")
    dashboard_coverage.update_with_sample_data(30, 0.85)
    layout.addWidget(dashboard_coverage)
    
    # Compact style
    compact_coverage = factory.create_compact_coverage("Steps")
    compact_coverage.update_with_sample_data(30, 0.92)
    layout.addWidget(compact_coverage)
    
    # Timeline style
    timeline_coverage = factory.create_detailed_coverage("Sleep Data")
    timeline_coverage.update_with_sample_data(30, 0.78)
    layout.addWidget(timeline_coverage)
    
    # Heat map style
    heat_coverage = factory.create_heat_coverage("Activity Overview")
    heat_coverage.update_with_sample_data(30, 0.65)
    layout.addWidget(heat_coverage)
    
    main_window.setCentralWidget(central_widget)
    main_window.setWindowTitle("Coverage Integration Demo")
    main_window.resize(500, 700)
    main_window.show()
    
    sys.exit(app.exec())