"""
Monthly context visualization widget for weekly health data.
Provides WSJ-style background shading, floating labels, and interactive drill-down.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGroupBox, QPushButton, QProgressBar, QToolTip,
    QSizePolicy, QGraphicsEffect, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, 
    QPainterPath, QFontMetrics, QPalette, QPixmap
)
from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from datetime import date, timedelta
import math

from ..analytics.monthly_context_provider import MonthlyContextProvider, WeekContext


class PercentileGaugeWidget(QWidget):
    """WSJ-style percentile gauge showing week's position within month."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentile = 50.0
        self.category = "average"
        self.setFixedSize(80, 80)
        self.setToolTip("Week's percentile rank within month")
        
    def set_percentile(self, percentile: float, category: str):
        """Update percentile display."""
        self.percentile = percentile
        self.category = category
        self.update()
        
    def paintEvent(self, event):
        """Custom paint for percentile gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors based on WSJ style
        colors = {
            "exceptional": QColor(255, 140, 66),      # Orange
            "above_average": QColor(255, 209, 102),   # Yellow
            "average": QColor(149, 193, 123),         # Green
            "below_average": QColor(231, 111, 81)     # Coral
        }
        
        color = colors.get(self.category, QColor(149, 193, 123))
        
        # Draw background circle
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setPen(QPen(QColor(220, 220, 220), 2))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.drawEllipse(rect)
        
        # Draw progress arc
        start_angle = 90 * 16  # Start at top
        span_angle = -(self.percentile / 100.0) * 360 * 16
        
        painter.setPen(QPen(color, 4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Draw percentile text
        painter.setPen(QColor(93, 78, 55))  # Dark brown text
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        text = f"{self.percentile:.0f}%"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = (self.width() - text_rect.width()) // 2
        text_y = (self.height() + text_rect.height()) // 2 - 2
        painter.drawText(text_x, text_y, text)


class GoalProgressWidget(QWidget):
    """Goal progress indicator with projection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.on_track = True
        self.projected_end = 0.0
        self.setFixedHeight(60)
        
    def set_progress(self, progress: float, on_track: bool, projected_end: float):
        """Update progress display."""
        self.progress = progress
        self.on_track = on_track
        self.projected_end = projected_end
        self.update()
        
    def paintEvent(self, event):
        """Custom paint for goal progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        rect = self.rect().adjusted(10, 15, -10, -15)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(250, 250, 250)))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Progress fill
        progress_width = int(rect.width() * (self.progress / 100.0))
        progress_rect = QRect(rect.x(), rect.y(), progress_width, rect.height())
        
        color = QColor(149, 193, 123) if self.on_track else QColor(231, 111, 81)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(progress_rect, 8, 8)
        
        # Progress text
        painter.setPen(QColor(93, 78, 55))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        text = f"{self.progress:.1f}% (proj: {self.projected_end:.0f}%)"
        painter.drawText(rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignCenter, text)


class FloatingLabel(QLabel):
    """Floating contextual label with smooth animations."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(245, 230, 211, 240);
                color: #5D4E37;
                border: 1px solid #D4C4B0;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        
        # Animation setup
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
    def show_at(self, position: QPoint):
        """Show label at specific position with fade-in."""
        self.move(position)
        self.show()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
    def hide_with_fade(self):
        """Hide label with fade-out."""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()


class MonthlyContextVisualization(QWidget):
    """Main visualization widget with background shading and context layers."""
    
    drill_down_requested = pyqtSignal(int, int)  # week_num, year
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.week_context = None
        self.background_gradient = None
        self.floating_labels = []
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        
        # Create floating labels
        self._create_floating_labels()
        
    def set_week_context(self, context: WeekContext):
        """Update visualization with new context."""
        self.week_context = context
        self._update_background_gradient()
        self._update_floating_labels()
        self.update()
        
    def _create_floating_labels(self):
        """Create floating labels for insights."""
        labels = [
            "percentile_label",
            "rank_label", 
            "trend_label",
            "exceptional_label"
        ]
        
        for label_name in labels:
            label = FloatingLabel("", self)
            self.floating_labels.append(label)
            
    def _update_background_gradient(self):
        """Update background gradient based on context."""
        if not self.week_context:
            return
            
        # Create gradient based on percentile performance
        start_color = QColor(255, 248, 240)  # Light cream
        
        if self.week_context.percentile_rank >= 75:
            end_color = QColor(149, 193, 123, 60)  # Light green
        elif self.week_context.percentile_rank >= 25:
            end_color = QColor(255, 209, 102, 40)  # Light yellow
        else:
            end_color = QColor(231, 111, 81, 60)   # Light coral
            
        self.background_gradient = QLinearGradient(0, 0, self.width(), 0)
        self.background_gradient.setColorAt(0, start_color)
        self.background_gradient.setColorAt(1, end_color)
        
    def _update_floating_labels(self):
        """Update floating label content."""
        if not self.week_context:
            return
            
        labels_data = [
            f"Percentile: {self.week_context.percentile_rank:.0f}%",
            f"Rank: #{self.week_context.rank_within_month} of {self.week_context.total_weeks_in_month}",
            f"vs Monthly Avg: {self.week_context.vs_monthly_average_percent:+.1f}%",
            self.week_context.exceptional_reason or "Typical performance"
        ]
        
        for i, (label, text) in enumerate(zip(self.floating_labels, labels_data)):
            label.setText(text)
            
    def paintEvent(self, event):
        """Custom paint with background shading."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background gradient
        if self.background_gradient:
            painter.fillRect(self.rect(), QBrush(self.background_gradient))
        else:
            painter.fillRect(self.rect(), QColor(255, 248, 240))
            
        # Draw context visualization
        if self.week_context:
            self._draw_context_elements(painter)
            
    def _draw_context_elements(self, painter: QPainter):
        """Draw context visualization elements."""
        rect = self.rect().adjusted(20, 20, -20, -20)
        
        # Draw monthly average baseline
        baseline_y = rect.y() + rect.height() * 0.6
        painter.setPen(QPen(QColor(139, 115, 85), 2, Qt.PenStyle.DashLine))
        painter.drawLine(rect.x(), baseline_y, rect.x() + rect.width(), baseline_y)
        
        # Draw current week indicator
        week_x = rect.x() + rect.width() * 0.7  # Position in timeline
        
        if self.week_context.current_week_value > self.week_context.monthly_average:
            week_y = baseline_y - 30
            color = QColor(149, 193, 123)
        else:
            week_y = baseline_y + 30
            color = QColor(231, 111, 81)
            
        # Draw week indicator circle
        painter.setPen(QPen(color, 3))
        painter.setBrush(QBrush(color.lighter(150)))
        painter.drawEllipse(week_x - 8, week_y - 8, 16, 16)
        
        # Draw confidence band
        if self.week_context.confidence_level > 0.5:
            band_height = int(40 * self.week_context.confidence_level)
            band_rect = QRect(rect.x(), baseline_y - band_height//2, 
                            rect.width(), band_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(200, 200, 200, 50)))
            painter.drawRect(band_rect)
            
    def mouseMoveEvent(self, event):
        """Handle mouse movement for floating labels."""
        if not self.week_context:
            return
            
        pos = event.position().toPoint()
        
        # Show appropriate floating label based on mouse position
        if self.rect().adjusted(20, 20, -20, -20).contains(pos):
            # Determine which label to show based on mouse position
            label_index = min(3, pos.x() // (self.width() // 4))
            
            if label_index < len(self.floating_labels):
                label = self.floating_labels[label_index]
                label_pos = QPoint(pos.x() - label.width() // 2, pos.y() - 30)
                label.show_at(label_pos)
                
                # Hide other labels
                for i, other_label in enumerate(self.floating_labels):
                    if i != label_index and other_label.isVisible():
                        other_label.hide_with_fade()
        else:
            # Hide all labels when mouse leaves area
            for label in self.floating_labels:
                if label.isVisible():
                    label.hide_with_fade()
                    
    def mousePressEvent(self, event):
        """Handle mouse clicks for drill-down."""
        if event.button() == Qt.MouseButton.LeftButton and self.week_context:
            self.drill_down_requested.emit(
                self.week_context.week_number, 
                self.week_context.year
            )


class MonthlyContextWidget(QWidget):
    """
    Complete monthly context widget combining all elements.
    Provides WSJ-style analytics with percentile gauges, goal progress,
    and interactive visualizations.
    """
    
    drill_down_requested = pyqtSignal(int, int)  # week_num, year
    
    def __init__(self, context_provider: MonthlyContextProvider = None, parent=None):
        super().__init__(parent)
        self.context_provider = context_provider
        self.current_context = None
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Monthly Context")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #5D4E37; margin-bottom: 5px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Toggle context layers button
        self.toggle_btn = QPushButton("Toggle Layers")
        self.toggle_btn.setFixedSize(100, 28)
        header_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(header_layout)
        
        # Metrics row
        metrics_layout = QHBoxLayout()
        
        # Percentile gauge
        gauge_group = QGroupBox("Percentile Rank")
        gauge_layout = QVBoxLayout(gauge_group)
        self.percentile_gauge = PercentileGaugeWidget()
        gauge_layout.addWidget(self.percentile_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        metrics_layout.addWidget(gauge_group)
        
        # Goal progress
        goal_group = QGroupBox("Goal Progress")
        goal_layout = QVBoxLayout(goal_group)
        self.goal_progress = GoalProgressWidget()
        goal_layout.addWidget(self.goal_progress)
        metrics_layout.addWidget(goal_group)
        
        # Indicators
        indicators_group = QGroupBox("Indicators")
        indicators_layout = QVBoxLayout(indicators_group)
        
        self.best_worst_label = QLabel("—")
        self.best_worst_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicators_layout.addWidget(self.best_worst_label)
        
        self.seasonal_label = QLabel("Seasonal: —")
        self.seasonal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicators_layout.addWidget(self.seasonal_label)
        
        metrics_layout.addWidget(indicators_group)
        
        layout.addLayout(metrics_layout)
        
        # Main visualization
        viz_group = QGroupBox("Weekly Context")
        viz_layout = QVBoxLayout(viz_group)
        
        self.context_viz = MonthlyContextVisualization()
        self.context_viz.drill_down_requested.connect(self.drill_down_requested)
        viz_layout.addWidget(self.context_viz)
        
        layout.addWidget(viz_group)
        
        # Click instruction
        instruction_label = QLabel("💡 Click visualization to drill down to daily view")
        instruction_label.setStyleSheet("color: #8B7355; font-style: italic; font-size: 11px;")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction_label)
        
    def _setup_styles(self):
        """Setup widget styles."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #5D4E37;
                border: 2px solid #D4C4B0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 5px;
                background-color: rgba(255, 248, 240, 200);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #5D4E37;
                background-color: #F5E6D3;
            }
            QPushButton {
                background-color: #FF8C42;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #E57A35;
            }
            QPushButton:pressed {
                background-color: #CC6B2E;
            }
        """)
        
    def update_context(self, week_num: int, year: int, metric: str):
        """Update widget with new weekly context."""
        if not self.context_provider:
            return
            
        try:
            self.current_context = self.context_provider.get_week_context(week_num, year, metric)
            self._update_displays()
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            
    def _update_displays(self):
        """Update all display elements."""
        if not self.current_context:
            return
            
        # Update percentile gauge
        self.percentile_gauge.set_percentile(
            self.current_context.percentile_rank,
            self.current_context.percentile_category
        )
        
        # Update goal progress (mock values for now)
        self.goal_progress.set_progress(
            self.current_context.goal_progress,
            self.current_context.goal_progress >= 80,
            min(100, self.current_context.goal_progress * 1.2)
        )
        
        # Update indicators
        if self.current_context.is_best_week:
            best_worst_text = "🏆 Best Week"
            style = "color: #95C17B; font-weight: bold;"
        elif self.current_context.is_worst_week:
            best_worst_text = "⚠️ Worst Week" 
            style = "color: #E76F51; font-weight: bold;"
        else:
            best_worst_text = "📊 Typical Week"
            style = "color: #8B7355;"
            
        self.best_worst_label.setText(best_worst_text)
        self.best_worst_label.setStyleSheet(style)
        
        # Update seasonal adjustment
        factor = self.current_context.seasonal_factor
        if factor > 1.05:
            seasonal_text = f"📈 Peak Season (+{(factor-1)*100:.0f}%)"
        elif factor < 0.95:
            seasonal_text = f"📉 Off Season ({(factor-1)*100:.0f}%)"
        else:
            seasonal_text = "🔄 Normal Season"
            
        self.seasonal_label.setText(seasonal_text)
        
        # Update main visualization
        self.context_viz.set_week_context(self.current_context)
        
    def set_context_provider(self, provider: MonthlyContextProvider):
        """Set the context provider."""
        self.context_provider = provider