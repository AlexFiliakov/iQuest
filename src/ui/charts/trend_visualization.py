"""WSJ-style trend visualization component."""

import numpy as np
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from ...analytics.advanced_trend_models import (
    TrendAnalysis, TrendClassification, PredictionPoint,
    ChangePoint, WSJVisualizationConfig
)
from .chart_config import ChartConfig


class TrendVisualizationWidget(QWidget):
    """WSJ-style trend visualization with progressive disclosure."""
    
    # Signals
    changePointClicked = pyqtSignal(ChangePoint)
    periodChanged = pyqtSignal(str)
    
    def __init__(self, config: Optional[ChartConfig] = None, parent=None):
        super().__init__(parent)
        self.config = config or ChartConfig()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Summary section (always visible)
        self.summary_widget = TrendSummaryWidget(self.config)
        layout.addWidget(self.summary_widget)
        
        # Main chart
        self.chart_widget = TrendChartWidget(self.config)
        layout.addWidget(self.chart_widget)
        
        # Details section (progressive disclosure)
        self.details_widget = TrendDetailsWidget(self.config)
        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)
        
        # Connect signals
        self.summary_widget.toggleDetails.connect(self._toggle_details)
        self.chart_widget.changePointClicked.connect(self.changePointClicked.emit)
        
    def update_trend(self, analysis: TrendAnalysis, 
                    data: Dict[str, Any], metric_name: str):
        """Update the visualization with new trend analysis."""
        self.summary_widget.update_summary(analysis, metric_name)
        self.chart_widget.update_chart(analysis, data, metric_name)
        self.details_widget.update_details(analysis)
        
    def _toggle_details(self):
        """Toggle visibility of details section."""
        self.details_widget.setVisible(not self.details_widget.isVisible())
        

class TrendSummaryWidget(QWidget):
    """WSJ-style trend summary with key metrics."""
    
    toggleDetails = pyqtSignal()
    
    def __init__(self, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the summary UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 10)
        
        # Main summary line
        self.summary_label = QLabel(self)
        self.summary_label.setFont(QFont(self.config.font_family, 16, QFont.Weight.Bold))
        self.summary_label.setStyleSheet(f"color: {self.config.text_color};")
        layout.addWidget(self.summary_label)
        
        # Metrics row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(30)
        
        # Trend strength
        self.strength_widget = MetricWidget("Trend Strength", self.config)
        metrics_layout.addWidget(self.strength_widget)
        
        # Confidence
        self.confidence_widget = MetricWidget("Confidence", self.config)
        metrics_layout.addWidget(self.confidence_widget)
        
        # Volatility
        self.volatility_widget = MetricWidget("Volatility", self.config)
        metrics_layout.addWidget(self.volatility_widget)
        
        # Evidence quality
        self.evidence_widget = MetricWidget("Evidence", self.config)
        metrics_layout.addWidget(self.evidence_widget)
        
        metrics_layout.addStretch()
        
        # Details toggle
        self.toggle_button = QLabel("View Details ▼")
        self.toggle_button.setFont(QFont(self.config.font_family, 10))
        self.toggle_button.setStyleSheet(f"""
            color: {self.config.accent_color};
            padding: 5px;
        """)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.mousePressEvent = lambda e: self.toggleDetails.emit()
        metrics_layout.addWidget(self.toggle_button)
        
        layout.addLayout(metrics_layout)
        
    def update_summary(self, analysis: TrendAnalysis, metric_name: str):
        """Update summary with trend analysis."""
        # Update main summary
        self.summary_label.setText(analysis.summary)
        
        # Update metrics
        self.strength_widget.update_value(
            f"{analysis.trend_strength:.0%}",
            self._get_strength_color(analysis.trend_strength)
        )
        
        self.confidence_widget.update_value(
            f"{analysis.confidence:.0f}%",
            self._get_confidence_color(analysis.confidence)
        )
        
        self.volatility_widget.update_value(
            analysis.volatility_level.title(),
            self._get_volatility_color(analysis.volatility_level)
        )
        
        self.evidence_widget.update_value(
            analysis.evidence_quality.title(),
            self._get_evidence_color(analysis.evidence_quality)
        )
        
    def _get_strength_color(self, strength: float) -> str:
        """Get color for trend strength."""
        if strength > 0.7:
            return self.config.positive_color
        elif strength > 0.3:
            return self.config.warning_color
        else:
            return self.config.muted_color
            
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence level."""
        if confidence > 80:
            return self.config.positive_color
        elif confidence > 60:
            return self.config.warning_color
        else:
            return self.config.negative_color
            
    def _get_volatility_color(self, level: str) -> str:
        """Get color for volatility level."""
        if level == "low":
            return self.config.positive_color
        elif level == "medium":
            return self.config.warning_color
        else:
            return self.config.negative_color
            
    def _get_evidence_color(self, quality: str) -> str:
        """Get color for evidence quality."""
        if quality == "strong":
            return self.config.positive_color
        elif quality == "moderate":
            return self.config.warning_color
        else:
            return self.config.negative_color


class MetricWidget(QWidget):
    """Individual metric display widget."""
    
    def __init__(self, label: str, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui(label)
        
    def _setup_ui(self, label: str):
        """Set up the metric UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setFont(QFont(self.config.font_family, 9))
        label_widget.setStyleSheet(f"color: {self.config.muted_color};")
        layout.addWidget(label_widget)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont(self.config.font_family, 12, QFont.Weight.Medium))
        layout.addWidget(self.value_label)
        
    def update_value(self, value: str, color: str):
        """Update the metric value and color."""
        self.value_label.setText(value)
        self.value_label.setStyleSheet(f"color: {color};")


class TrendChartWidget(QWidget):
    """Main trend chart with WSJ styling."""
    
    changePointClicked = pyqtSignal(ChangePoint)
    
    def __init__(self, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Store data for interaction
        self.change_points = []
        self.data = None
        
    def update_chart(self, analysis: TrendAnalysis, 
                    data: Dict[str, Any], metric_name: str):
        """Update the chart with trend data."""
        self.change_points = analysis.change_points
        self.data = data
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Apply WSJ styling
        self._apply_wsj_style(ax)
        
        # Extract time series data
        timestamps = data['timestamps']
        values = data['values']
        
        # Plot main data
        ax.plot(timestamps, values, 
               color=self.config.primary_color,
               linewidth=2,
               label='Actual')
        
        # Plot trend line if available
        if 'trend' in data:
            ax.plot(timestamps, data['trend'],
                   color=self.config.accent_color,
                   linewidth=2,
                   linestyle='--',
                   label='Trend')
        
        # Plot predictions
        if analysis.predictions:
            pred_times = [p.timestamp for p in analysis.predictions]
            pred_values = [p.predicted_value for p in analysis.predictions]
            pred_lower = [p.lower_bound for p in analysis.predictions]
            pred_upper = [p.upper_bound for p in analysis.predictions]
            
            # Prediction line
            ax.plot(pred_times, pred_values,
                   color=self.config.accent_color,
                   linewidth=2,
                   linestyle=':',
                   label='Forecast')
            
            # Confidence interval
            ax.fill_between(pred_times, pred_lower, pred_upper,
                          color=self.config.accent_color,
                          alpha=0.1)
        
        # Mark change points
        for cp in analysis.change_points:
            if cp.confidence > 50:  # Only show high-confidence changes
                # Find the y-value at this timestamp
                idx = next((i for i, t in enumerate(timestamps) if t >= cp.timestamp), None)
                if idx is not None:
                    y_val = values[idx]
                    
                    # Add marker
                    marker_color = self.config.positive_color if cp.direction == "increase" else self.config.negative_color
                    ax.scatter([cp.timestamp], [y_val], 
                             color=marker_color,
                             s=50,
                             zorder=5,
                             alpha=0.8)
                    
                    # Add subtle annotation for major changes
                    if cp.confidence > 80:
                        ax.annotate('',
                                  xy=(cp.timestamp, y_val),
                                  xytext=(cp.timestamp, y_val + (max(values) - min(values)) * 0.1),
                                  arrowprops=dict(arrowstyle='-',
                                                color=marker_color,
                                                alpha=0.5,
                                                lw=1))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Rotate dates
        self.figure.autofmt_xdate()
        
        # Add subtle grid
        ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5)
        
        # Set title
        display_name = metric_name.replace('_', ' ').title()
        ax.set_title(f"{display_name} Trend Analysis", 
                    fontsize=14, 
                    fontweight='bold',
                    pad=20)
        
        # Add legend if needed
        if len(ax.get_lines()) > 1:
            ax.legend(loc='upper left', frameon=False, fontsize=9)
        
        # Adjust layout
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _apply_wsj_style(self, ax):
        """Apply WSJ-inspired styling to the chart."""
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Make remaining spines subtle
        ax.spines['left'].set_color(self.config.grid_color)
        ax.spines['bottom'].set_color(self.config.grid_color)
        ax.spines['left'].set_linewidth(0.5)
        ax.spines['bottom'].set_linewidth(0.5)
        
        # Set tick parameters
        ax.tick_params(colors=self.config.muted_color, labelsize=9)
        ax.tick_params(axis='both', which='major', length=0)
        
        # Set background
        ax.set_facecolor(self.config.background_color)
        self.figure.patch.set_facecolor(self.config.background_color)


class TrendDetailsWidget(QWidget):
    """Detailed trend information with progressive disclosure."""
    
    def __init__(self, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the details UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        
        # Interpretation section
        self.interpretation_label = QLabel(self)
        self.interpretation_label.setFont(QFont(self.config.font_family, 11))
        self.interpretation_label.setWordWrap(True)
        self.interpretation_label.setStyleSheet(f"color: {self.config.text_color};")
        layout.addWidget(self.interpretation_label)
        
        # Recommendations section
        self.recommendations_widget = QWidget(self)
        self.recommendations_layout = QVBoxLayout(self.recommendations_widget)
        self.recommendations_layout.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(self.recommendations_widget)
        
        # Technical details (collapsible)
        self.technical_widget = TechnicalDetailsWidget(self.config)
        layout.addWidget(self.technical_widget)
        
    def update_details(self, analysis: TrendAnalysis):
        """Update details with trend analysis."""
        # Update interpretation
        self.interpretation_label.setText(analysis.interpretation)
        
        # Clear and update recommendations
        while self.recommendations_layout.count():
            child = self.recommendations_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if analysis.recommendations:
            rec_title = QLabel("Recommendations:")
            rec_title.setFont(QFont(self.config.font_family, 10, QFont.Weight.Bold))
            rec_title.setStyleSheet(f"color: {self.config.text_color};")
            self.recommendations_layout.addWidget(rec_title)
            
            for rec in analysis.recommendations:
                rec_label = QLabel(f"• {rec}")
                rec_label.setFont(QFont(self.config.font_family, 10))
                rec_label.setWordWrap(True)
                rec_label.setStyleSheet(f"color: {self.config.text_color}; padding-left: 10px;")
                self.recommendations_layout.addWidget(rec_label)
                
        # Update technical details
        self.technical_widget.update_details(analysis)


class TechnicalDetailsWidget(QWidget):
    """Technical analysis details for advanced users."""
    
    def __init__(self, config: ChartConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self.setVisible(False)  # Hidden by default
        
    def _setup_ui(self):
        """Set up the technical details UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Toggle header
        self.header = QLabel("▶ Technical Details")
        self.header.setFont(QFont(self.config.font_family, 10))
        self.header.setStyleSheet(f"color: {self.config.muted_color};")
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self._toggle_content
        layout.addWidget(self.header)
        
        # Content widget
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 0, 0)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)
        
        # Technical info labels
        self.methods_label = QLabel(self)
        self.methods_label.setFont(QFont(self.config.font_family, 9))
        self.methods_label.setStyleSheet(f"color: {self.config.muted_color};")
        self.content_layout.addWidget(self.methods_label)
        
        self.stats_label = QLabel(self)
        self.stats_label.setFont(QFont(self.config.font_family, 9))
        self.stats_label.setStyleSheet(f"color: {self.config.muted_color};")
        self.content_layout.addWidget(self.stats_label)
        
    def _toggle_content(self, event):
        """Toggle visibility of technical content."""
        is_visible = not self.content_widget.isVisible()
        self.content_widget.setVisible(is_visible)
        self.header.setText("▼ Technical Details" if is_visible else "▶ Technical Details")
        
    def update_details(self, analysis: TrendAnalysis):
        """Update technical details."""
        # Methods used
        methods_text = f"Methods: {', '.join(analysis.methods_used)}"
        self.methods_label.setText(methods_text)
        
        # Statistical details
        stats_text = (
            f"Statistical Significance: p={analysis.statistical_significance:.4f}\n"
            f"Ensemble Agreement: {analysis.ensemble_agreement:.0%}\n"
            f"Data Quality Score: {analysis.data_quality_score:.0%}"
        )
        self.stats_label.setText(stats_text)