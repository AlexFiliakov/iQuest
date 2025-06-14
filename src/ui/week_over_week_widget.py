"""
Week-over-week trends visualization widget.
Displays slope graphs, momentum indicators, streak tracking, and mini bar charts.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGroupBox, QScrollArea, QPushButton, QProgressBar,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient
from typing import List, Optional, Dict
import numpy as np
from datetime import date, timedelta

from ..analytics.week_over_week_trends import (
    WeekOverWeekTrends, TrendResult, StreakInfo, MomentumIndicator, 
    WeekTrendData, MomentumType
)
from .summary_cards import SummaryCard
from .bar_chart_component import BarChart, BarChartConfig
from .charts.enhanced_line_chart import EnhancedLineChart
from .charts.chart_config import ChartConfig


class MomentumIndicatorWidget(QWidget):
    """Widget to display momentum indicators with visual arrows and colors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.momentum = MomentumType.STEADY
        self.acceleration_rate = 0.0
        self.confidence = 0.0
        self.setFixedSize(60, 40)
        
    def set_momentum(self, momentum: MomentumType, acceleration_rate: float, confidence: float):
        """Update momentum display."""
        self.momentum = momentum
        self.acceleration_rate = acceleration_rate
        self.confidence = confidence
        self.update()
        
    def paintEvent(self, event):
        """Custom paint for momentum indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        rect = self.rect()
        painter.fillRect(rect, QColor(245, 245, 245))
        
        # Choose color and arrow based on momentum
        if self.momentum == MomentumType.ACCELERATING:
            color = QColor(0, 150, 0)  # Green
            arrow_type = "up_double"
        elif self.momentum == MomentumType.DECELERATING:
            color = QColor(255, 100, 0)  # Orange
            arrow_type = "down_double"
        elif self.momentum == MomentumType.STEADY:
            color = QColor(100, 100, 100)  # Gray
            arrow_type = "right"
        else:
            color = QColor(150, 150, 150)  # Light gray
            arrow_type = "none"
        
        # Draw arrow
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        
        if arrow_type == "up_double":
            # Double up arrow
            points = [
                (center_x, center_y - 10),
                (center_x - 8, center_y - 2),
                (center_x + 8, center_y - 2),
                (center_x, center_y - 10)
            ]
            painter.drawPolygon([self.mapToParent(QPoint(x, y)) for x, y in points])
            
            points2 = [
                (center_x, center_y + 2),
                (center_x - 6, center_y + 8),
                (center_x + 6, center_y + 8),
                (center_x, center_y + 2)
            ]
            painter.drawPolygon([self.mapToParent(QPoint(x, y)) for x, y in points2])
            
        elif arrow_type == "down_double":
            # Double down arrow
            points = [
                (center_x, center_y + 10),
                (center_x - 8, center_y + 2),
                (center_x + 8, center_y + 2),
                (center_x, center_y + 10)
            ]
            painter.drawPolygon([self.mapToParent(QPoint(x, y)) for x, y in points])
            
            points2 = [
                (center_x, center_y - 2),
                (center_x - 6, center_y - 8),
                (center_x + 6, center_y - 8),
                (center_x, center_y - 2)
            ]
            painter.drawPolygon([self.mapToParent(QPoint(x, y)) for x, y in points2])
            
        elif arrow_type == "right":
            # Right arrow
            points = [
                (center_x + 8, center_y),
                (center_x, center_y - 6),
                (center_x, center_y + 6),
                (center_x + 8, center_y)
            ]
            painter.drawPolygon([self.mapToParent(QPoint(x, y)) for x, y in points])


class StreakTrackerWidget(QWidget):
    """Widget to display streak information with visual progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.streak_info = None
        
    def setup_ui(self):
        """Setup the streak tracker UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Streak Tracker")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Current streak
        self.current_streak_label = QLabel("No active streak")
        self.current_streak_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.current_streak_label)
        
        # Progress bar for streak
        self.streak_progress = QProgressBar(self)
        self.streak_progress.setMaximum(10)  # Will be adjusted based on best streak
        self.streak_progress.setVisible(False)
        layout.addWidget(self.streak_progress)
        
        # Best streak info
        self.best_streak_label = QLabel("Best: 0 weeks")
        self.best_streak_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.best_streak_label)
        
        layout.addStretch()
        
    def update_streak(self, streak_info: StreakInfo):
        """Update streak display."""
        self.streak_info = streak_info
        
        if streak_info.current_streak > 0:
            direction_text = "improving" if streak_info.streak_direction == "improving" else "declining"
            self.current_streak_label.setText(f"{streak_info.current_streak} weeks {direction_text}")
            
            # Show progress bar
            self.streak_progress.setVisible(True)
            self.streak_progress.setMaximum(max(streak_info.best_streak, streak_info.current_streak))
            self.streak_progress.setValue(streak_info.current_streak)
            
            # Color based on direction
            if streak_info.streak_direction == "improving":
                self.streak_progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
                self.current_streak_label.setStyleSheet("color: #4CAF50;")
            else:
                self.streak_progress.setStyleSheet("QProgressBar::chunk { background-color: #FF5722; }")
                self.current_streak_label.setStyleSheet("color: #FF5722;")
                
            # Highlight if current streak is best
            if streak_info.is_current_streak_best:
                self.current_streak_label.setText(f"🏆 {streak_info.current_streak} weeks {direction_text} (BEST!)")
        else:
            self.current_streak_label.setText("No active streak")
            self.current_streak_label.setStyleSheet("")
            self.streak_progress.setVisible(False)
        
        self.best_streak_label.setText(f"Best: {streak_info.best_streak} weeks")




class SlopeGraphWidget(QWidget):
    """Slope graph showing week progression using EnhancedLineChart."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.trend_data = []
        
    def setup_ui(self):
        """Setup the slope graph UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create enhanced line chart
        config = ChartConfig()
        config.title = "Weekly Progression"
        config.show_grid = True
        config.show_legend = True
        config.wsj_mode = True  # Enable WSJ-inspired styling
        
        self.chart = EnhancedLineChart(config)
        layout.addWidget(self.chart)
        
    def set_data(self, trend_data: List[WeekTrendData], metric_name: str):
        """Set trend data and update the slope graph."""
        self.trend_data = trend_data
        self.metric_name = metric_name
        self.update_graph()
        
    def update_graph(self):
        """Update the slope graph with current data."""
        if not self.trend_data:
            return
            
        # Clear existing series
        self.chart.clear_series()
        
        # Prepare data for line chart
        data_points = []
        for i, data in enumerate(self.trend_data):
            data_points.append({
                'x': i,
                'y': data.value,
                'label': f"Week {i+1}"
            })
        
        # Add series to chart
        self.chart.add_series(
            name=self.metric_name,
            data=data_points,
            color='#FF8C42'  # Orange from our warm color palette
        )
        self.chart.config.title = f"{self.metric_name} - Weekly Progression"


class WeekOverWeekWidget(QWidget):
    """Main widget for week-over-week trends analysis."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trends_calculator = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main widget UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Week-over-Week Trends")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create scroll area for content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        
        # Summary cards section
        summary_frame = QFrame(self)
        summary_frame.setFrameStyle(QFrame.Shape.Box)
        summary_layout = QHBoxLayout(summary_frame)
        
        # Current week summary card
        self.current_week_card = self.create_summary_card("This Week", "0.0", "No data")
        summary_layout.addWidget(self.current_week_card)
        
        # Change summary card  
        self.change_card = self.create_summary_card("Change", "0.0%", "vs last week")
        summary_layout.addWidget(self.change_card)
        
        # Momentum indicator card
        momentum_card = QGroupBox("Momentum")
        momentum_layout = QVBoxLayout(momentum_card)
        self.momentum_indicator = MomentumIndicatorWidget()
        self.momentum_label = QLabel("Steady")
        momentum_layout.addWidget(self.momentum_indicator)
        momentum_layout.addWidget(self.momentum_label)
        summary_layout.addWidget(momentum_card)
        
        # Streak tracker card
        self.streak_tracker = StreakTrackerWidget()
        summary_layout.addWidget(self.streak_tracker)
        
        content_layout.addWidget(summary_frame)
        
        # Slope graph section
        graph_group = QGroupBox("Weekly Progression")
        graph_layout = QVBoxLayout(graph_group)
        self.slope_graph = SlopeGraphWidget()
        graph_layout.addWidget(self.slope_graph)
        content_layout.addWidget(graph_group)
        
        # Narrative section
        narrative_group = QGroupBox("Insights")
        narrative_layout = QVBoxLayout(narrative_group)
        self.narrative_label = QLabel("Select a metric to view trend analysis.")
        self.narrative_label.setWordWrap(True)
        self.narrative_label.setFont(QFont("Arial", 11))
        narrative_layout.addWidget(self.narrative_label)
        content_layout.addWidget(narrative_group)
        
        # Prediction section
        prediction_group = QGroupBox("Next Week Forecast")
        prediction_layout = QVBoxLayout(prediction_group)
        self.prediction_label = QLabel("No forecast available.")
        self.prediction_label.setWordWrap(True)
        prediction_layout.addWidget(self.prediction_label)
        content_layout.addWidget(prediction_group)
        
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
    def create_summary_card(self, title: str, value: str, subtitle: str) -> SummaryCard:
        """Create a summary card with mini bar chart."""
        # Import the specific card type we need
        from .summary_cards import MiniChartCard
        
        card = MiniChartCard(size="medium")
        
        # Set the card content
        if hasattr(card, 'title_label'):
            card.title_label.setText(title)
        if hasattr(card, 'value_label'):
            card.value_label.setText(value)
        if hasattr(card, 'subtitle_label'):
            card.subtitle_label.setText(subtitle)
        
        return card
    
    def set_trends_calculator(self, calculator: WeekOverWeekTrends):
        """Set the trends calculator."""
        self.trends_calculator = calculator
        
    def update_analysis(self, metric: str, current_week: int, year: int):
        """Update the analysis for a specific metric and week."""
        if not self.trends_calculator:
            return
            
        try:
            # Get trend analysis
            trend_result = self.trends_calculator.calculate_week_change(
                metric, current_week - 1, current_week, year
            )
            
            # Get momentum analysis
            momentum = self.trends_calculator.detect_momentum(metric, current_week, year)
            
            # Get streak information
            streak_info = self.trends_calculator.get_current_streak(metric, current_week, year)
            
            # Get trend series for visualization
            trend_series = self.trends_calculator.get_trend_series(metric, 12, current_week, year)
            
            # Get prediction
            prediction = self.trends_calculator.predict_next_week(metric, current_week, year)
            
            # Update UI components
            self.update_summary_cards(trend_result, trend_series)
            self.update_momentum_display(momentum)
            self.update_streak_display(streak_info)
            self.update_slope_graph(trend_series, metric)
            self.update_narrative(metric, trend_result, streak_info, momentum)
            self.update_prediction(prediction)
            
        except Exception as e:
            print(f"Error updating analysis: {e}")
            self.show_error_state()
    
    def update_summary_cards(self, trend_result: TrendResult, trend_series: List[WeekTrendData]):
        """Update the summary cards."""
        # Current week card
        self.current_week_card.value_label.setText(f"{trend_result.current_week_avg:.1f}")
        self.current_week_card.mini_chart.set_data(trend_series)
        
        # Change card
        change_text = f"{trend_result.percent_change:+.1f}%"
        self.change_card.value_label.setText(change_text)
        
        # Color code the change
        if trend_result.percent_change > 2:
            self.change_card.value_label.setStyleSheet("color: #4CAF50;")
        elif trend_result.percent_change < -2:
            self.change_card.value_label.setStyleSheet("color: #F44336;")
        else:
            self.change_card.value_label.setStyleSheet("color: #666666;")
        
        self.change_card.mini_chart.set_data(trend_series)
        
    def update_momentum_display(self, momentum: MomentumIndicator):
        """Update momentum indicator."""
        self.momentum_indicator.set_momentum(
            momentum.momentum_type, 
            momentum.acceleration_rate, 
            momentum.confidence_level
        )
        
        momentum_text = momentum.momentum_type.value.title()
        if momentum.confidence_level > 0.7:
            momentum_text += " (High confidence)"
        elif momentum.confidence_level > 0.4:
            momentum_text += " (Medium confidence)"
        else:
            momentum_text += " (Low confidence)"
            
        self.momentum_label.setText(momentum_text)
        
    def update_streak_display(self, streak_info: StreakInfo):
        """Update streak tracker."""
        self.streak_tracker.update_streak(streak_info)
        
    def update_slope_graph(self, trend_series: List[WeekTrendData], metric: str):
        """Update the slope graph."""
        self.slope_graph.set_data(trend_series, metric)
        
    def update_narrative(self, metric: str, trend_result: TrendResult, 
                        streak_info: StreakInfo, momentum: MomentumIndicator):
        """Update the narrative text."""
        narrative = self.trends_calculator.generate_trend_narrative(
            metric, trend_result, streak_info, momentum
        )
        self.narrative_label.setText(narrative)
        
    def update_prediction(self, prediction):
        """Update the prediction display."""
        if prediction.prediction_confidence > 0.3:
            pred_text = (f"Predicted value: {prediction.predicted_value:.1f} "
                        f"(Range: {prediction.confidence_interval_lower:.1f} - "
                        f"{prediction.confidence_interval_upper:.1f})\n"
                        f"Confidence: {prediction.prediction_confidence:.0%}")
        else:
            pred_text = "Insufficient data for reliable prediction."
            
        self.prediction_label.setText(pred_text)
        
    def show_error_state(self):
        """Show error state when analysis fails."""
        self.narrative_label.setText("Unable to analyze trends for this metric. Please check data availability.")
        self.prediction_label.setText("No forecast available.")