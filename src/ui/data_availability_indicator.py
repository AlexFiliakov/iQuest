"""
Data availability indicators for health data coverage visualization.
Provides various visual representations of data coverage, gaps, and quality.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QProgressBar, QToolTip, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPolygon
from typing import Dict, List, Optional, Union, NamedTuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from .style_manager import StyleManager
from .summary_cards import SummaryCard
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DateGap:
    """Represents a gap in data coverage."""
    start: datetime
    end: datetime
    
    def __str__(self) -> str:
        if self.start.date() == self.end.date():
            return self.start.strftime('%b %d')
        return f"{self.start.strftime('%b %d')} - {self.end.strftime('%b %d')}"


@dataclass
class CoverageData:
    """Container for data coverage information."""
    percentage: float
    total_days: int
    days_with_data: int
    partial_days: int
    quality_scores: Dict[datetime, float]  # 0.0 to 1.0
    gaps: List[DateGap]
    date_range: tuple[datetime, datetime]
    
    def has_data(self, date: datetime) -> bool:
        """Check if data exists for a specific date."""
        return date in self.quality_scores
    
    def get_quality(self, date: datetime) -> float:
        """Get quality score for a specific date."""
        return self.quality_scores.get(date, 0.0)


class IndicatorStyles:
    """Style definitions for data availability indicators."""
    
    COVERAGE_COLORS = {
        'excellent': StyleManager.ACCENT_SUCCESS,    # 90%+ coverage
        'good': '#8BC34A',                          # 75-89% coverage  
        'fair': StyleManager.ACCENT_WARNING,        # 50-74% coverage
        'poor': StyleManager.ACCENT_ERROR,          # 1-49% coverage
        'none': '#9E9E9E'                          # 0% coverage
    }
    
    QUALITY_COLORS = {
        'complete': StyleManager.ACCENT_SUCCESS,     # >90% data points
        'partial': StyleManager.ACCENT_WARNING,     # 10-90% data points
        'sparse': StyleManager.ACCENT_ERROR,        # <10% data points
        'missing': '#E0E0E0'                       # No data points
    }
    
    @staticmethod
    def get_coverage_color(percentage: float) -> str:
        """Get color based on coverage percentage."""
        if percentage >= 90:
            return IndicatorStyles.COVERAGE_COLORS['excellent']
        elif percentage >= 75:
            return IndicatorStyles.COVERAGE_COLORS['good']
        elif percentage >= 50:
            return IndicatorStyles.COVERAGE_COLORS['fair']
        elif percentage > 0:
            return IndicatorStyles.COVERAGE_COLORS['poor']
        else:
            return IndicatorStyles.COVERAGE_COLORS['none']
    
    @staticmethod
    def get_quality_color(quality_score: float) -> str:
        """Get color based on data quality score."""
        if quality_score > 0.9:
            return IndicatorStyles.QUALITY_COLORS['complete']
        elif quality_score >= 0.1:
            return IndicatorStyles.QUALITY_COLORS['partial']
        elif quality_score > 0:
            return IndicatorStyles.QUALITY_COLORS['sparse']
        else:
            return IndicatorStyles.QUALITY_COLORS['missing']


class CoverageTooltip:
    """Generates detailed tooltip content for coverage indicators."""
    
    def __init__(self, coverage_data: CoverageData):
        self.coverage_data = coverage_data
    
    def generate_content(self) -> str:
        """Generate detailed tooltip content."""
        lines = []
        
        # Summary line
        lines.append(f"<b>Coverage: {self.coverage_data.percentage:.1f}%</b>")
        lines.append(f"{self.coverage_data.days_with_data} of {self.coverage_data.total_days} days")
        
        # Quality breakdown
        if self.coverage_data.partial_days > 0:
            lines.append(f"<br><i>Partial data: {self.coverage_data.partial_days} days</i>")
        
        # Gap summary
        if self.coverage_data.gaps:
            lines.append("<br><b>Missing periods:</b>")
            for gap in self.coverage_data.gaps[:3]:  # Show first 3
                lines.append(f"• {gap}")
            if len(self.coverage_data.gaps) > 3:
                lines.append(f"• ... and {len(self.coverage_data.gaps) - 3} more")
        
        # Suggestions
        if self.coverage_data.percentage < 80:
            lines.append("<br><i>💡 Import more data for better insights</i>")
        
        return "<br>".join(lines)


class CoverageBar(QProgressBar):
    """Horizontal coverage bar with color coding."""
    
    def __init__(self, coverage_data: CoverageData):
        super().__init__()
        self.coverage_data = coverage_data
        self.setup_bar()
    
    def setup_bar(self):
        """Configure the progress bar appearance."""
        self.setRange(0, 100)
        self.setValue(int(self.coverage_data.percentage))
        self.setTextVisible(True)
        self.setFormat(f"{self.coverage_data.percentage:.1f}%")
        
        # Apply color based on coverage level
        color = IndicatorStyles.get_coverage_color(self.coverage_data.percentage)
        
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {StyleManager.TEXT_MUTED};
                border-radius: 8px;
                background-color: {StyleManager.TERTIARY_BG};
                text-align: center;
                font-weight: bold;
                color: {StyleManager.TEXT_PRIMARY};
                min-height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 7px;
                margin: 1px;
            }}
        """)
        
        # Set up tooltip
        tooltip = CoverageTooltip(self.coverage_data)
        self.setToolTip(tooltip.generate_content())


class DotMatrixWidget(QWidget):
    """Grid-based visualization showing individual days as dots."""
    
    def __init__(self, coverage_data: CoverageData, days_per_row: int = 14):
        super().__init__()
        self.coverage_data = coverage_data
        self.days_per_row = days_per_row
        self.dot_size = 8
        self.dot_spacing = 12
        self.setup_widget()
    
    def setup_widget(self):
        """Setup the widget dimensions and tooltip."""
        rows = (self.coverage_data.total_days + self.days_per_row - 1) // self.days_per_row
        width = self.days_per_row * self.dot_spacing + 20
        height = rows * self.dot_spacing + 20
        
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        
        # Set up tooltip
        tooltip = CoverageTooltip(self.coverage_data)
        self.setToolTip(tooltip.generate_content())
    
    def paintEvent(self, event):
        """Paint the dot matrix."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        current_date = self.coverage_data.date_range[0]
        end_date = self.coverage_data.date_range[1]
        
        row = 0
        col = 0
        
        while current_date <= end_date:
            x = 10 + col * self.dot_spacing
            y = 10 + row * self.dot_spacing
            
            # Determine dot color based on data quality
            if self.coverage_data.has_data(current_date):
                quality = self.coverage_data.get_quality(current_date)
                color = IndicatorStyles.get_quality_color(quality)
            else:
                color = IndicatorStyles.QUALITY_COLORS['missing']
            
            # Draw dot
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor(StyleManager.TEXT_MUTED), 1))
            painter.drawEllipse(x, y, self.dot_size, self.dot_size)
            
            # Move to next position
            col += 1
            if col >= self.days_per_row:
                col = 0
                row += 1
            
            current_date += timedelta(days=1)


class HeatStripWidget(QWidget):
    """Continuous color gradient showing data density."""
    
    def __init__(self, coverage_data: CoverageData):
        super().__init__()
        self.coverage_data = coverage_data
        self.setup_widget()
    
    def setup_widget(self):
        """Setup the widget dimensions and tooltip."""
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
        self.setMinimumWidth(200)
        
        # Set up tooltip
        tooltip = CoverageTooltip(self.coverage_data)
        self.setToolTip(tooltip.generate_content())
    
    def paintEvent(self, event):
        """Paint the heat strip."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        if self.coverage_data.total_days == 0:
            return
        
        pixels_per_day = width / self.coverage_data.total_days
        current_date = self.coverage_data.date_range[0]
        
        for day in range(self.coverage_data.total_days):
            x = int(day * pixels_per_day)
            segment_width = max(1, int(pixels_per_day))
            
            # Determine color based on data quality
            if self.coverage_data.has_data(current_date):
                quality = self.coverage_data.get_quality(current_date)
                color = IndicatorStyles.get_quality_color(quality)
            else:
                color = IndicatorStyles.QUALITY_COLORS['missing']
            
            # Draw segment
            painter.fillRect(x, 0, segment_width, height, QColor(color))
            
            current_date += timedelta(days=1)


class CoverageBadge(QLabel):
    """Percentage badge with quality indicator."""
    
    def __init__(self, coverage_data: CoverageData, badge_type: str = 'percentage'):
        super().__init__()
        self.coverage_data = coverage_data
        self.badge_type = badge_type
        self.setup_badge()
    
    def setup_badge(self):
        """Configure the badge appearance."""
        if self.badge_type == 'percentage':
            text = f"{self.coverage_data.percentage:.0f}%"
        elif self.badge_type == 'quality':
            if self.coverage_data.percentage >= 90:
                text = "Excellent"
            elif self.coverage_data.percentage >= 75:
                text = "Good"
            elif self.coverage_data.percentage >= 50:
                text = "Fair"
            else:
                text = "Poor"
        else:
            text = "N/A"
        
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Apply styling
        color = IndicatorStyles.get_coverage_color(self.coverage_data.percentage)
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;
                min-width: 40px;
            }}
        """)
        
        # Set up tooltip
        tooltip = CoverageTooltip(self.coverage_data)
        self.setToolTip(tooltip.generate_content())


class DataAvailabilityCard(SummaryCard):
    """Main card widget for displaying data availability indicators extending SummaryCard."""
    
    coverage_clicked = pyqtSignal(dict)  # Emits coverage data when clicked
    
    def __init__(self, indicator_type: str = 'bar', size: str = 'medium', parent=None):
        super().__init__(card_type='coverage', size=size, card_id=f"coverage_{indicator_type}")
        self.indicator_type = indicator_type
        self.coverage_data = None
        self.indicator_widget = None
        self.setup_coverage_ui()
    
    def setup_coverage_ui(self):
        """Initialize the coverage-specific UI layout."""
        # Use the existing card layout from SummaryCard
        content_layout = QVBoxLayout()
        
        # Placeholder widget when no data
        self.placeholder_label = QLabel("No data available")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                color: {StyleManager.TEXT_MUTED};
                font-style: italic;
                padding: 20px;
            }}
        """)
        content_layout.addWidget(self.placeholder_label)
        
        # Add to card's content area
        self.content_layout.addLayout(content_layout)
    
    def update_coverage(self, coverage_data: CoverageData):
        """Update indicator with new coverage data."""
        self.coverage_data = coverage_data
        metrics = self.calculate_metrics()
        self.update_visual()
        
        # Update card title and value using SummaryCard methods
        self.update_title("Data Coverage")
        self.update_value(f"{coverage_data.percentage:.1f}%")
        
        logger.debug(f"Updated coverage indicator: {coverage_data.percentage:.1f}% coverage")
    
    def calculate_metrics(self) -> Dict:
        """Calculate coverage metrics."""
        if not self.coverage_data:
            return {}
        
        metrics = {
            'simple_coverage': self.coverage_data.percentage,
            'quality_score': sum(self.coverage_data.quality_scores.values()) / len(self.coverage_data.quality_scores) if self.coverage_data.quality_scores else 0,
            'gap_count': len(self.coverage_data.gaps),
            'partial_percentage': (self.coverage_data.partial_days / self.coverage_data.total_days * 100) if self.coverage_data.total_days > 0 else 0
        }
        
        return metrics
    
    def update_visual(self):
        """Update the visual representation."""
        if not self.coverage_data:
            return
        
        # Remove existing indicator widget from content layout
        if self.indicator_widget:
            self.content_layout.removeWidget(self.indicator_widget)
            self.indicator_widget.deleteLater()
        
        # Hide placeholder
        self.placeholder_label.hide()
        
        # Create new indicator based on type
        if self.indicator_type == 'bar':
            self.indicator_widget = CoverageBar(self.coverage_data)
        elif self.indicator_type == 'dots':
            self.indicator_widget = DotMatrixWidget(self.coverage_data)
        elif self.indicator_type == 'heat':
            self.indicator_widget = HeatStripWidget(self.coverage_data)
        elif self.indicator_type == 'badge':
            self.indicator_widget = CoverageBadge(self.coverage_data)
        else:
            logger.warning(f"Unknown indicator type: {self.indicator_type}")
            return
        
        self.content_layout.addWidget(self.indicator_widget)
    
    def set_indicator_type(self, indicator_type: str):
        """Change the indicator type and refresh display."""
        self.indicator_type = indicator_type
        if self.coverage_data:
            self.update_visual()
    
    def mousePressEvent(self, event):
        """Handle mouse click events."""
        if self.coverage_data and event.button() == Qt.MouseButton.LeftButton:
            metrics = self.calculate_metrics()
            self.coverage_clicked.emit(metrics)
        super().mousePressEvent(event)


# Legacy wrapper for backwards compatibility
class DataAvailabilityIndicator(DataAvailabilityCard):
    """Legacy wrapper - use DataAvailabilityCard instead."""
    
    def __init__(self, indicator_type: str = 'bar', parent=None):
        super().__init__(indicator_type=indicator_type, size='medium', parent=parent)


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from datetime import datetime, timedelta
    
    app = QApplication(sys.argv)
    
    # Create sample coverage data
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    quality_scores = {}
    current = start_date
    while current <= end_date:
        # Simulate some missing days and varying quality
        if current.day % 7 != 0:  # Skip Sundays
            quality_scores[current] = min(1.0, 0.5 + (current.day % 4) * 0.2)
        current += timedelta(days=1)
    
    gaps = [DateGap(datetime(2024, 1, 7), datetime(2024, 1, 7)),
            DateGap(datetime(2024, 1, 14), datetime(2024, 1, 14))]
    
    coverage_data = CoverageData(
        percentage=75.0,
        total_days=31,
        days_with_data=25,
        partial_days=5,
        quality_scores=quality_scores,
        gaps=gaps,
        date_range=(start_date, end_date)
    )
    
    # Create main window with indicators
    main_window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Add different indicator types
    indicators = [
        ('bar', 'Coverage Bar'),
        ('dots', 'Dot Matrix'),
        ('heat', 'Heat Strip'),
        ('badge', 'Badge')
    ]
    
    for indicator_type, label in indicators:
        layout.addWidget(QLabel(label))
        indicator = DataAvailabilityIndicator(indicator_type)
        indicator.update_coverage(coverage_data)
        layout.addWidget(indicator)
    
    main_window.setCentralWidget(central_widget)
    main_window.setWindowTitle("Data Availability Indicators")
    main_window.resize(400, 600)
    main_window.show()
    
    sys.exit(app.exec())