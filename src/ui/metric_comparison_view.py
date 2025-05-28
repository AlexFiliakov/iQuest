"""Metric comparison and correlation views for the dashboard."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QFrame,
    QGridLayout, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor, QPen

from .style_manager import StyleManager
from .charts.line_chart import LineChart
from ..analytics.correlation_analyzer import CorrelationAnalyzer
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class CorrelationMatrix(QWidget):
    """Visual correlation matrix widget."""
    
    cell_clicked = pyqtSignal(str, str, float)  # metric1, metric2, correlation
    
    def __init__(self, style_manager: StyleManager, parent=None):
        super().__init__(parent)
        self.style_manager = style_manager
        self.correlations = {}
        self.metrics = []
        self.cell_size = 60
        self.margin = 100
        
        self.setMinimumSize(400, 400)
        
    def set_data(self, correlations: Dict[Tuple[str, str], float], metrics: List[str]):
        """Set correlation data."""
        self.correlations = correlations
        self.metrics = metrics
        self.update()
        
    def paintEvent(self, event):
        """Paint the correlation matrix."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(self.style_manager.SECONDARY_BG))
        
        # Font for labels
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Draw cells
        for i, metric1 in enumerate(self.metrics):
            for j, metric2 in enumerate(self.metrics):
                x = self.margin + j * self.cell_size
                y = self.margin + i * self.cell_size
                
                # Get correlation value
                if i == j:
                    corr = 1.0
                else:
                    corr = self.correlations.get((metric1, metric2), 0)
                
                # Color based on correlation
                color = self._get_correlation_color(corr)
                painter.fillRect(x, y, self.cell_size - 2, self.cell_size - 2, color)
                
                # Draw correlation value
                painter.setPen(Qt.GlobalColor.black if abs(corr) < 0.5 else Qt.GlobalColor.white)
                painter.drawText(x, y, self.cell_size - 2, self.cell_size - 2,
                               Qt.AlignmentFlag.AlignCenter, f"{corr:.2f}")
        
        # Draw labels
        painter.setPen(QColor(self.style_manager.TEXT_PRIMARY))
        for i, metric in enumerate(self.metrics):
            # Row labels
            painter.drawText(5, self.margin + i * self.cell_size,
                           self.margin - 10, self.cell_size,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           self._format_metric_name(metric))
            
            # Column labels (rotated would be better, but simplified here)
            painter.drawText(self.margin + i * self.cell_size, 
                           self.margin - 10,
                           self.cell_size - 2, 20,
                           Qt.AlignmentFlag.AlignCenter,
                           self._format_metric_name(metric)[:3])
                           
    def _get_correlation_color(self, correlation: float) -> QColor:
        """Get color for correlation value."""
        # Use warm color scheme
        if correlation > 0:
            # Positive correlation: shades of orange
            intensity = int(255 * abs(correlation))
            return QColor(255, 140 + int(60 * (1 - correlation)), 66)
        else:
            # Negative correlation: shades of blue
            intensity = int(255 * abs(correlation))
            return QColor(108 + int(147 * (1 + correlation)), 155 + int(100 * (1 + correlation)), 209)
            
    def _format_metric_name(self, metric: str) -> str:
        """Format metric name for display."""
        return metric.replace('_', ' ').title()
        
    def mousePressEvent(self, event):
        """Handle mouse clicks on cells."""
        x = event.pos().x() - self.margin
        y = event.pos().y() - self.margin
        
        if x >= 0 and y >= 0:
            col = x // self.cell_size
            row = y // self.cell_size
            
            if 0 <= row < len(self.metrics) and 0 <= col < len(self.metrics):
                metric1 = self.metrics[row]
                metric2 = self.metrics[col]
                corr = self.correlations.get((metric1, metric2), 0)
                self.cell_clicked.emit(metric1, metric2, corr)


class MetricComparisonView(QWidget):
    """Side-by-side metric comparison view."""
    
    def __init__(self, data_manager, style_manager: StyleManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.style_manager = style_manager
        self.correlation_analyzer = CorrelationAnalyzer(data_manager)
        
        self.selected_metrics = []
        self.comparison_mode = "overlay"  # overlay, side-by-side, correlation
        
        self.setup_ui()
        self.apply_styling()
        
    def setup_ui(self):
        """Set up the comparison view UI."""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        
        # Header with controls
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(12)
        
        # Title
        self.title_label = QLabel("Metric Comparison")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        
        # Metric selectors
        self.metric1_combo = QComboBox()
        self.metric1_combo.addItems([
            "Steps", "Distance", "Active Energy", "Heart Rate",
            "Sleep Duration", "Weight", "BMI"
        ])
        
        self.metric2_combo = QComboBox()
        self.metric2_combo.addItems([
            "Steps", "Distance", "Active Energy", "Heart Rate",
            "Sleep Duration", "Weight", "BMI"
        ])
        self.metric2_combo.setCurrentIndex(1)  # Default to different metric
        
        # Comparison mode selector
        self.mode_group = QButtonGroup()
        self.overlay_btn = QRadioButton("Overlay")
        self.sidebyside_btn = QRadioButton("Side by Side")
        self.correlation_btn = QRadioButton("Correlation")
        
        self.overlay_btn.setChecked(True)
        self.mode_group.addButton(self.overlay_btn)
        self.mode_group.addButton(self.sidebyside_btn)
        self.mode_group.addButton(self.correlation_btn)
        
        # Add to header
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(QLabel("Compare:"))
        self.header_layout.addWidget(self.metric1_combo)
        self.header_layout.addWidget(QLabel("with"))
        self.header_layout.addWidget(self.metric2_combo)
        self.header_layout.addWidget(self.overlay_btn)
        self.header_layout.addWidget(self.sidebyside_btn)
        self.header_layout.addWidget(self.correlation_btn)
        
        self.layout.addLayout(self.header_layout)
        
        # Comparison content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.content_widget)
        
        self.layout.addWidget(self.scroll_area)
        
        # Initialize views
        self.setup_comparison_views()
        
        # Connect signals
        self.metric1_combo.currentTextChanged.connect(self.update_comparison)
        self.metric2_combo.currentTextChanged.connect(self.update_comparison)
        self.mode_group.buttonClicked.connect(self.on_mode_changed)
        
    def setup_comparison_views(self):
        """Set up different comparison view widgets."""
        # Overlay chart
        self.overlay_chart = LineChart(parent=self)
        self.overlay_chart.setMinimumHeight(400)
        
        # Side by side charts
        self.sidebyside_widget = QWidget()
        self.sidebyside_layout = QHBoxLayout(self.sidebyside_widget)
        self.sidebyside_layout.setSpacing(16)
        
        self.chart1 = LineChart(parent=self)
        self.chart2 = LineChart(parent=self)
        self.chart1.setMinimumHeight(400)
        self.chart2.setMinimumHeight(400)
        
        self.sidebyside_layout.addWidget(self.chart1)
        self.sidebyside_layout.addWidget(self.chart2)
        
        # Correlation matrix
        self.correlation_widget = QWidget()
        self.correlation_layout = QVBoxLayout(self.correlation_widget)
        
        self.correlation_matrix = CorrelationMatrix(self.style_manager, self)
        self.correlation_info = QLabel("Click on a cell to see detailed correlation analysis")
        self.correlation_info.setWordWrap(True)
        
        self.correlation_layout.addWidget(self.correlation_matrix)
        self.correlation_layout.addWidget(self.correlation_info)
        
        # Connect correlation matrix signals
        self.correlation_matrix.cell_clicked.connect(self.on_correlation_cell_clicked)
        
        # Initially show overlay
        self.content_layout.addWidget(self.overlay_chart)
        self.sidebyside_widget.hide()
        self.correlation_widget.hide()
        
    def apply_styling(self):
        """Apply consistent styling."""
        self.setStyleSheet(f"""
            MetricComparisonView {{
                background-color: {self.style_manager.PRIMARY_BG};
            }}
            
            QLabel {{
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            
            QComboBox {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid {self.style_manager.TEXT_MUTED};
                border-radius: 4px;
                padding: 6px;
                min-width: 120px;
            }}
            
            QRadioButton {{
                color: {self.style_manager.TEXT_PRIMARY};
                spacing: 5px;
            }}
            
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            
            QRadioButton::indicator:checked {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                border: 2px solid {self.style_manager.ACCENT_PRIMARY};
                border-radius: 8px;
            }}
        """)
        
    @pyqtSlot()
    def on_mode_changed(self):
        """Handle comparison mode change."""
        if self.overlay_btn.isChecked():
            self.comparison_mode = "overlay"
            self.show_overlay_view()
        elif self.sidebyside_btn.isChecked():
            self.comparison_mode = "side-by-side"
            self.show_sidebyside_view()
        else:
            self.comparison_mode = "correlation"
            self.show_correlation_view()
            
        self.update_comparison()
        
    def show_overlay_view(self):
        """Show overlay comparison view."""
        self.sidebyside_widget.hide()
        self.correlation_widget.hide()
        
        if self.overlay_chart.parent() != self.content_widget:
            self.content_layout.addWidget(self.overlay_chart)
        self.overlay_chart.show()
        
    def show_sidebyside_view(self):
        """Show side-by-side comparison view."""
        self.overlay_chart.hide()
        self.correlation_widget.hide()
        
        if self.sidebyside_widget.parent() != self.content_widget:
            self.content_layout.addWidget(self.sidebyside_widget)
        self.sidebyside_widget.show()
        
    def show_correlation_view(self):
        """Show correlation matrix view."""
        self.overlay_chart.hide()
        self.sidebyside_widget.hide()
        
        if self.correlation_widget.parent() != self.content_widget:
            self.content_layout.addWidget(self.correlation_widget)
        self.correlation_widget.show()
        
        # Update correlation data
        self.update_correlation_matrix()
        
    @pyqtSlot()
    def update_comparison(self):
        """Update the comparison based on selected metrics."""
        metric1 = self.metric1_combo.currentText().lower().replace(' ', '_')
        metric2 = self.metric2_combo.currentText().lower().replace(' ', '_')
        
        if self.comparison_mode == "overlay":
            self.update_overlay_chart(metric1, metric2)
        elif self.comparison_mode == "side-by-side":
            self.update_sidebyside_charts(metric1, metric2)
        else:
            self.update_correlation_matrix()
            
    def update_overlay_chart(self, metric1: str, metric2: str):
        """Update overlay chart with two metrics."""
        try:
            # Get data for both metrics
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)  # First day of month
            
            # This is simplified - would need actual data retrieval
            dates = []
            values1 = []
            values2 = []
            
            # Update chart
            self.overlay_chart.clear()
            self.overlay_chart.plot_series(dates, values1, label=self.metric1_combo.currentText())
            self.overlay_chart.plot_series(dates, values2, label=self.metric2_combo.currentText())
            self.overlay_chart.set_title(f"{self.metric1_combo.currentText()} vs {self.metric2_combo.currentText()}")
            
        except Exception as e:
            logger.error(f"Error updating overlay chart: {e}")
            
    def update_sidebyside_charts(self, metric1: str, metric2: str):
        """Update side-by-side charts."""
        try:
            # Similar to overlay but separate charts
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)
            
            # Update individual charts
            self.chart1.clear()
            self.chart1.set_title(self.metric1_combo.currentText())
            
            self.chart2.clear()
            self.chart2.set_title(self.metric2_combo.currentText())
            
        except Exception as e:
            logger.error(f"Error updating side-by-side charts: {e}")
            
    def update_correlation_matrix(self):
        """Update correlation matrix with all metrics."""
        try:
            # Calculate correlations
            metrics = ['steps', 'distance', 'active_energy', 'heart_rate',
                      'sleep_duration', 'weight', 'bmi']
            
            correlations = self.correlation_analyzer.calculate_correlations(
                metrics,
                datetime.now().date().replace(day=1),
                datetime.now().date()
            )
            
            self.correlation_matrix.set_data(correlations, metrics)
            
        except Exception as e:
            logger.error(f"Error updating correlation matrix: {e}")
            
    @pyqtSlot(str, str, float)
    def on_correlation_cell_clicked(self, metric1: str, metric2: str, correlation: float):
        """Handle correlation cell click."""
        info_text = f"Correlation between {metric1.replace('_', ' ').title()} and {metric2.replace('_', ' ').title()}: {correlation:.3f}\n\n"
        
        if abs(correlation) > 0.7:
            info_text += "Strong correlation detected. These metrics are highly related."
        elif abs(correlation) > 0.4:
            info_text += "Moderate correlation detected. These metrics show some relationship."
        else:
            info_text += "Weak or no correlation detected. These metrics appear independent."
            
        self.correlation_info.setText(info_text)