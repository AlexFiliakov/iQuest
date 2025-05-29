"""
Comparative Analytics Visualization Components.

Provides respectful, encouraging visualizations for:
- Personal progress comparisons
- Demographic comparisons (when permitted)
- Seasonal trend comparisons
- Peer group comparisons
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QGroupBox, QProgressBar, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont

from ..analytics.comparative_analytics import (
    ComparisonResult, HistoricalComparison, ComparisonType
)
from ..analytics.peer_group_comparison import GroupComparison

logger = logging.getLogger(__name__)


class PercentileGauge(QWidget):
    """Animated percentile gauge with encouraging messaging."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentile = 0
        self.target_percentile = 0
        self.gauge_color = QColor('#4CAF50')
        self.label = ""
        self.subtitle = ""
        self.setMinimumSize(200, 200)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"percentile")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def set_value(self, percentile: float):
        """Set the percentile value with animation."""
        self.target_percentile = max(0, min(100, percentile))
        self.animation.setStartValue(self.percentile)
        self.animation.setEndValue(self.target_percentile)
        self.animation.start()
        
    def set_color(self, color: str):
        """Set the gauge color."""
        self.gauge_color = QColor(color)
        self.update()
        
    def set_label(self, label: str):
        """Set the main label."""
        self.label = label
        self.update()
        
    def set_subtitle(self, subtitle: str):
        """Set the encouraging subtitle."""
        self.subtitle = subtitle
        self.update()
        
    def paintEvent(self, event):
        """Paint the percentile gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 20
        
        # Draw background arc
        painter.setPen(QPen(QColor('#E0E0E0'), 10))
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            -225 * 16, 270 * 16  # 3/4 circle
        )
        
        # Draw value arc
        if self.percentile > 0:
            painter.setPen(QPen(self.gauge_color, 10))
            arc_length = int(270 * self.percentile / 100)
            painter.drawArc(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                -225 * 16, arc_length * 16
            )
            
        # Draw center text
        painter.setPen(QPen(Qt.GlobalColor.black))
        
        # Percentile value
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        percentile_text = f"{int(self.percentile)}%"
        painter.drawText(
            0, center_y - 20, width, 40,
            Qt.AlignmentFlag.AlignCenter,
            percentile_text
        )
        
        # Label
        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            0, center_y + 10, width, 20,
            Qt.AlignmentFlag.AlignCenter,
            self.label
        )
        
        # Subtitle (encouraging message)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(QColor('#666666')))
        painter.drawText(
            10, height - 30, width - 20, 20,
            Qt.AlignmentFlag.AlignCenter,
            self.subtitle
        )
        
    def get_percentile(self):
        return self._percentile
        
    def set_percentile(self, value):
        self._percentile = value
        self.update()
        
    percentile = property(get_percentile, set_percentile)


class ComparisonCard(QFrame):
    """Card widget for displaying comparison results."""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_loading = False
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            ComparisonCard {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
            }
            ComparisonCard:hover {
                border: 1px solid #FF8C42;
                background-color: #FFF9F5;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #333333;
        """)
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #FF8C42;
        """)
        layout.addWidget(self.value_label)
        
        # Comparison
        self.comparison_label = QLabel("")
        self.comparison_label.setStyleSheet("""
            font-size: 12px;
            color: #666666;
        """)
        layout.addWidget(self.comparison_label)
        
        # Insight
        self.insight_label = QLabel("")
        self.insight_label.setStyleSheet("""
            font-size: 11px;
            color: #888888;
            font-style: italic;
        """)
        self.insight_label.setWordWrap(True)
        layout.addWidget(self.insight_label)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def set_comparison(self, current: float, comparison: float, 
                      format_str: str = "{:,.0f}"):
        """Set the comparison values."""
        self.value_label.setText(format_str.format(current))
        
        # Calculate difference
        if comparison > 0:
            diff = current - comparison
            pct_change = (diff / comparison) * 100
            
            if diff > 0:
                self.comparison_label.setText(
                    f"↑ {format_str.format(abs(diff))} ({pct_change:+.1f}%)"
                )
                self.comparison_label.setStyleSheet("""
                    font-size: 12px;
                    color: #4CAF50;
                """)
            elif diff < 0:
                self.comparison_label.setText(
                    f"↓ {format_str.format(abs(diff))} ({pct_change:+.1f}%)"
                )
                self.comparison_label.setStyleSheet("""
                    font-size: 12px;
                    color: #FF5252;
                """)
            else:
                self.comparison_label.setText("No change")
                
    def set_insight(self, insight: str):
        """Set the insight text."""
        self.insight_label.setText(insight)
        
    def set_loading(self, loading: bool):
        """Set loading state."""
        self.is_loading = loading
        if loading:
            self.value_label.setText("...")
            self.comparison_label.setText("Calculating trends")
            self.insight_label.setText("")
        else:
            self.value_label.setText("--")
            self.comparison_label.setText("")
            self.insight_label.setText("")
            
    def set_value(self, value: float, trend: str = 'stable'):
        """Set the comparison value and trend."""
        self.is_loading = False
        self.value_label.setText(f"{value:,.0f}")
        
        # Set trend indicator
        if trend == 'improving':
            self.comparison_label.setText("↑ Improving trend")
            self.comparison_label.setStyleSheet("font-size: 12px; color: #4CAF50;")
        elif trend == 'declining':
            self.comparison_label.setText("↓ Declining trend")
            self.comparison_label.setStyleSheet("font-size: 12px; color: #FF5252;")
        else:
            self.comparison_label.setText("→ Stable trend")
            self.comparison_label.setStyleSheet("font-size: 12px; color: #666666;")
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.clicked.emit()
        super().mousePressEvent(event)


class HistoricalComparisonWidget(QWidget):
    """Widget for displaying historical comparisons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Personal Progress")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
            padding: 10px 0;
        """)
        layout.addWidget(title)
        
        # Cards grid
        self.cards_layout = QGridLayout()
        
        # Create comparison cards
        self.week_card = ComparisonCard("7-Day Average")
        self.month_card = ComparisonCard("30-Day Average")
        self.quarter_card = ComparisonCard("90-Day Average")
        self.year_card = ComparisonCard("365-Day Average")
        
        self.cards_layout.addWidget(self.week_card, 0, 0)
        self.cards_layout.addWidget(self.month_card, 0, 1)
        self.cards_layout.addWidget(self.quarter_card, 1, 0)
        self.cards_layout.addWidget(self.year_card, 1, 1)
        
        layout.addLayout(self.cards_layout)
        
        # Trend indicator
        self.trend_frame = QFrame(self)
        self.trend_frame.setFrameStyle(QFrame.Shape.Box)
        self.trend_frame.setStyleSheet("""
            background-color: #F5F5F5;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 10px;
        """)
        
        trend_layout = QHBoxLayout(self.trend_frame)
        
        self.trend_icon = QLabel(self)
        self.trend_label = QLabel("Calculating trend...")
        self.trend_label.setStyleSheet("color: #666666;")
        
        trend_layout.addWidget(self.trend_icon)
        trend_layout.addWidget(self.trend_label)
        trend_layout.addStretch()
        
        layout.addWidget(self.trend_frame)
        
    def update_comparison(self, historical: HistoricalComparison, 
                         current_value: float):
        """Update the historical comparison display."""
        # Update 7-day
        if historical.rolling_7_day and historical.rolling_7_day.mean is not None:
            self.week_card.set_comparison(
                current_value, 
                historical.rolling_7_day.mean
            )
        else:
            self.week_card.value_label.setText(f"{current_value:,.0f}")
            self.week_card.comparison_label.setText("No historical data")
            
        # Update 30-day
        if historical.rolling_30_day and historical.rolling_30_day.mean is not None:
            self.month_card.set_comparison(
                current_value,
                historical.rolling_30_day.mean
            )
        else:
            self.month_card.value_label.setText(f"{current_value:,.0f}")
            self.month_card.comparison_label.setText("No historical data")
            
        # Update 90-day
        if historical.rolling_90_day and historical.rolling_90_day.mean is not None:
            self.quarter_card.set_comparison(
                current_value,
                historical.rolling_90_day.mean
            )
        else:
            self.quarter_card.value_label.setText(f"{current_value:,.0f}")
            self.quarter_card.comparison_label.setText("No historical data")
            
        # Update 365-day
        if historical.rolling_365_day and historical.rolling_365_day.mean is not None:
            self.year_card.set_comparison(
                current_value,
                historical.rolling_365_day.mean
            )
            if historical.personal_best:
                self.year_card.set_insight(
                    f"Personal best: {historical.personal_best[1]:,.0f}"
                )
        else:
            self.year_card.value_label.setText(f"{current_value:,.0f}")
            self.year_card.comparison_label.setText("No historical data")
                
        # Update trend
        if historical.trend_direction:
            if historical.trend_direction == "improving":
                self.trend_icon.setText("📈")
                self.trend_label.setText("Your trend is improving!")
                self.trend_frame.setStyleSheet("""
                    background-color: #E8F5E9;
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    padding: 10px;
                """)
            elif historical.trend_direction == "stable":
                self.trend_icon.setText("📊")
                self.trend_label.setText("You're maintaining consistency!")
                self.trend_frame.setStyleSheet("""
                    background-color: #E3F2FD;
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    padding: 10px;
                """)
            else:
                self.trend_icon.setText("💪")
                self.trend_label.setText("Every journey has ups and downs - keep going!")
                self.trend_frame.setStyleSheet("""
                    background-color: #FFF3E0;
                    border: 1px solid #FF9800;
                    border-radius: 4px;
                    padding: 10px;
                """)


class PeerGroupComparisonWidget(QWidget):
    """Widget for displaying peer group comparisons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Title section
        title_layout = QHBoxLayout()
        
        title = QLabel("Group Comparison")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
        """)
        title_layout.addWidget(title)
        
        # Privacy indicator
        self.privacy_label = QLabel("🔒 Anonymous")
        self.privacy_label.setStyleSheet("""
            font-size: 12px;
            color: #666666;
            background-color: #F5F5F5;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        title_layout.addWidget(self.privacy_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Percentile gauge
        self.gauge = PercentileGauge()
        content_layout.addWidget(self.gauge)
        
        # Stats panel
        stats_frame = QFrame(self)
        stats_frame.setFrameStyle(QFrame.Shape.Box)
        stats_frame.setStyleSheet("""
            background-color: #FAFAFA;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 10px;
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        
        self.group_name_label = QLabel("Group: --")
        self.group_name_label.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.group_name_label)
        
        self.members_label = QLabel("Members: --")
        stats_layout.addWidget(self.members_label)
        
        stats_layout.addSpacing(10)
        
        self.avg_label = QLabel("Group Average: --")
        stats_layout.addWidget(self.avg_label)
        
        self.range_label = QLabel("Range: --")
        stats_layout.addWidget(self.range_label)
        
        stats_layout.addStretch()
        
        content_layout.addWidget(stats_frame)
        
        layout.addLayout(content_layout)
        
        # Insights
        self.insights_frame = QGroupBox("Insights")
        self.insights_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.insights_layout = QVBoxLayout(self.insights_frame)
        layout.addWidget(self.insights_frame)
        
    def update_comparison(self, comparison: GroupComparison, group_name: str):
        """Update the peer group comparison display."""
        if comparison.error:
            # Show error state
            self.gauge.set_value(0)
            self.gauge.set_label("No Data")
            self.gauge.set_subtitle(comparison.error)
            return
            
        # Update group info
        self.group_name_label.setText(f"Group: {group_name}")
        self.members_label.setText(
            f"Members: {comparison.group_stats.get('member_count', 0)}"
        )
        
        # Update stats
        stats = comparison.group_stats
        self.avg_label.setText(f"Group Average: {stats.get('mean', 0):,.0f}")
        self.range_label.setText(
            f"Range: {stats.get('min', 0):,.0f} - {stats.get('max', 0):,.0f}"
        )
        
        # Calculate and update percentile
        if comparison.user_value and stats.get('mean'):
            # Simple percentile calculation
            percentile = self._estimate_percentile(
                comparison.user_value, stats
            )
            self.gauge.set_value(percentile)
            
            # Set color based on ranking
            if comparison.anonymous_ranking == "top quarter":
                self.gauge.set_color('#4CAF50')
            elif comparison.anonymous_ranking == "upper half":
                self.gauge.set_color('#2196F3')
            elif comparison.anonymous_ranking == "middle range":
                self.gauge.set_color('#FF9800')
            else:
                self.gauge.set_color('#9C27B0')
                
            self.gauge.set_label(comparison.anonymous_ranking.title())
            
        # Update insights
        # Clear old insights
        while self.insights_layout.count():
            child = self.insights_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add new insights
        for insight in comparison.insights[:3]:  # Show top 3
            insight_label = QLabel(f"• {insight}")
            insight_label.setWordWrap(True)
            insight_label.setStyleSheet("""
                color: #666666;
                padding: 2px 0;
            """)
            self.insights_layout.addWidget(insight_label)
            
    def _estimate_percentile(self, value: float, stats: Dict) -> float:
        """Estimate percentile from stats."""
        # Simple linear interpolation
        if value <= stats.get('min', 0):
            return 5
        elif value >= stats.get('max', 0):
            return 95
        elif value <= stats.get('percentile_25', 0):
            return 25 * (value - stats['min']) / (stats['percentile_25'] - stats['min'])
        elif value <= stats.get('median', 0):
            return 25 + 25 * (value - stats['percentile_25']) / (stats['median'] - stats['percentile_25'])
        elif value <= stats.get('percentile_75', 0):
            return 50 + 25 * (value - stats['median']) / (stats['percentile_75'] - stats['median'])
        else:
            return 75 + 20 * (value - stats['percentile_75']) / (stats['max'] - stats['percentile_75'])


class ComparativeAnalyticsWidget(QWidget):
    """Main widget for comparative analytics display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comparative_engine = None
        self.current_metric = 'HKQuantityTypeIdentifierStepCount'
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Comparative Analytics")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #333333;
            padding: 10px 0;
        """)
        layout.addWidget(header)
        
        # Tab-like navigation (using buttons for simplicity)
        nav_layout = QHBoxLayout()
        
        self.personal_btn = QPushButton("Personal Progress")
        self.personal_btn.setCheckable(True)
        self.personal_btn.setChecked(True)
        
        self.group_btn = QPushButton("Group Comparison")
        self.group_btn.setCheckable(True)
        
        self.seasonal_btn = QPushButton("Seasonal Trends")
        self.seasonal_btn.setCheckable(True)
        
        nav_layout.addWidget(self.personal_btn)
        nav_layout.addWidget(self.group_btn)
        nav_layout.addWidget(self.seasonal_btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # Content area
        self.content_stack = QVBoxLayout()
        
        # Personal comparison
        self.historical_widget = HistoricalComparisonWidget()
        
        # Group comparison
        self.group_widget = PeerGroupComparisonWidget()
        self.group_widget.hide()
        
        self.content_stack.addWidget(self.historical_widget)
        self.content_stack.addWidget(self.group_widget)
        
        layout.addLayout(self.content_stack)
        layout.addStretch()
        
        # Connect buttons
        self.personal_btn.clicked.connect(self.show_personal)
        self.group_btn.clicked.connect(self.show_group)
        
    def show_personal(self):
        """Show personal comparison view."""
        self.personal_btn.setChecked(True)
        self.group_btn.setChecked(False)
        self.seasonal_btn.setChecked(False)
        
        self.historical_widget.show()
        self.group_widget.hide()
        
    def show_group(self):
        """Show group comparison view."""
        self.personal_btn.setChecked(False)
        self.group_btn.setChecked(True)
        self.seasonal_btn.setChecked(False)
        
        self.historical_widget.hide()
        self.group_widget.show()
    
    def set_comparative_engine(self, engine):
        """Set the comparative analytics engine."""
        self.comparative_engine = engine
        logger.info("Comparative engine set for visualization widget")
        
        # Trigger initial trend calculation for default metric
        if engine and hasattr(engine, 'background_processor') and engine.background_processor:
            engine.background_processor.queue_trend_calculation(self.current_metric, priority=10)
            
    def set_current_metric(self, metric: str):
        """Set the current metric and update display."""
        self.current_metric = metric
        self.update_comparisons()
        
    def update_comparisons(self):
        """Update comparison displays using cached trends."""
        if not self.comparative_engine:
            logger.warning("No comparative engine set")
            return
            
        # Get cached trend data
        trend_data = self.comparative_engine.get_trend_analysis(self.current_metric, use_cache=True)
        
        if trend_data:
            # Update historical comparison with cached data
            self._update_historical_display(trend_data)
        else:
            # Show loading state and queue calculation
            self._show_loading_state()
            if hasattr(self.comparative_engine, 'background_processor') and self.comparative_engine.background_processor:
                self.comparative_engine.background_processor.queue_trend_calculation(
                    self.current_metric, 
                    priority=10
                )
                # Set up a timer to check for results
                QTimer.singleShot(1000, self._check_for_trend_results)
                
    def _update_historical_display(self, trend_data):
        """Update the historical comparison display with trend data."""
        if hasattr(trend_data, 'comparative_data') and trend_data.comparative_data:
            comp_data = trend_data.comparative_data
            
            # Update comparison cards
            if comp_data.get('rolling_7_day'):
                self.historical_widget.week_card.set_value(
                    comp_data['rolling_7_day'].mean if hasattr(comp_data['rolling_7_day'], 'mean') else 0,
                    trend_data.trend_direction if hasattr(trend_data, 'trend_direction') else 'stable'
                )
                
            if comp_data.get('rolling_30_day'):
                self.historical_widget.month_card.set_value(
                    comp_data['rolling_30_day'].mean if hasattr(comp_data['rolling_30_day'], 'mean') else 0,
                    trend_data.trend_direction if hasattr(trend_data, 'trend_direction') else 'stable'
                )
                
            # Add trend insights
            if hasattr(trend_data, 'insights') and trend_data.insights:
                self._display_insights(trend_data.insights)
                
    def _show_loading_state(self):
        """Show loading state while trends are being calculated."""
        # Update cards to show loading
        self.historical_widget.week_card.set_loading(True)
        self.historical_widget.month_card.set_loading(True)
        self.historical_widget.quarter_card.set_loading(True)
        self.historical_widget.year_card.set_loading(True)
        
    def _check_for_trend_results(self):
        """Check if trend results are ready."""
        if not self.comparative_engine:
            return
            
        trend_data = self.comparative_engine.get_trend_analysis(self.current_metric, use_cache=True)
        if trend_data:
            self._update_historical_display(trend_data)
        else:
            # Check again in a bit
            QTimer.singleShot(2000, self._check_for_trend_results)
            
    def _display_insights(self, insights: List[str]):
        """Display trend insights."""
        # This would update an insights panel in the UI
        logger.info(f"Displaying {len(insights)} insights")