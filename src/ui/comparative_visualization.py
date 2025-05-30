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
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QGroupBox, QProgressBar, QToolTip,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont

from ..analytics.comparative_analytics import (
    ComparisonResult, HistoricalComparison, ComparisonType
)
# from ..analytics.peer_group_comparison import GroupComparison  # Removed group comparison feature

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
        try:
            self.value_label.setText(f"{value:,.0f}")
        except (TypeError, ValueError):
            # Handle case where value is not a valid number (e.g., MagicMock in tests)
            self.value_label.setText("--")
        
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
    
    metric_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comparative_engine = None
        self.current_metric = None
        self.metric_mapping = {
            "Steps": "HKQuantityTypeIdentifierStepCount",
            "Active Energy": "HKQuantityTypeIdentifierActiveEnergyBurned",
            "Heart Rate": "HKQuantityTypeIdentifierRestingHeartRate",
            "Sleep": "HKCategoryTypeIdentifierSleepAnalysis",
            "Exercise Minutes": "HKQuantityTypeIdentifierAppleExerciseTime",
            "Stand Hours": "HKQuantityTypeIdentifierAppleStandHour",
            "Walking Speed": "HKQuantityTypeIdentifierWalkingSpeed"
        }
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Header with title and metric selector
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Personal Progress")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
            padding: 10px 0;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Metric selector
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet("font-size: 12px; color: #666666;")
        header_layout.addWidget(metric_label)
        
        from PyQt6.QtWidgets import QComboBox
        self.metric_selector = QComboBox()
        self.metric_selector.setMinimumWidth(200)
        self.metric_selector.addItems([
            "Steps", "Active Energy", "Heart Rate", "Sleep",
            "Exercise Minutes", "Stand Hours", "Walking Speed"
        ])
        self.metric_selector.currentTextChanged.connect(self.on_metric_changed)
        header_layout.addWidget(self.metric_selector)
        
        layout.addLayout(header_layout)
        
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
        self.trend_label = QLabel("Initializing...")
        self.trend_label.setStyleSheet("color: #666666;")
        
        # Add a progress indicator
        from PyQt6.QtWidgets import QProgressBar
        self.trend_progress = QProgressBar()
        self.trend_progress.setMaximumHeight(4)
        self.trend_progress.setTextVisible(False)
        self.trend_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E0E0E0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #FF8C42;
                border-radius: 2px;
            }
        """)
        self.trend_progress.hide()
        
        trend_layout.addWidget(self.trend_icon)
        trend_layout.addWidget(self.trend_label)
        trend_layout.addStretch()
        
        layout.addWidget(self.trend_frame)
        layout.addWidget(self.trend_progress)
        
    def on_metric_changed(self, metric_name: str):
        """Handle metric selection change."""
        if metric_name in self.metric_mapping:
            self.current_metric = self.metric_mapping[metric_name]
            self.metric_changed.emit(self.current_metric)
            self.update_data()
    
    def set_comparative_engine(self, engine):
        """Set the comparative analytics engine."""
        self.comparative_engine = engine
        
    def update_data(self):
        """Update the comparison data for current metric."""
        if not self.comparative_engine or not self.current_metric:
            self._update_status("No data source available")
            return
            
        # Show loading state
        self._update_status("Loading historical data...")
        self.week_card.set_loading(True)
        self.month_card.set_loading(True)
        self.quarter_card.set_loading(True)
        self.year_card.set_loading(True)
        
        # Show progress bar
        self.trend_progress.show()
        self.trend_progress.setRange(0, 4)  # 4 time periods to calculate
        self.trend_progress.setValue(0)
        
        try:
            # Get comparison data
            self._update_status("Checking for cached trends...")
            comparison = self.comparative_engine.compare_to_historical(
                self.current_metric,
                datetime.now()
            )
            
            if comparison:
                self._update_status("Processing comparison data...")
                # compare_to_historical returns HistoricalComparison directly
                self.update_comparison(comparison, 0)  # We'll get current value from the comparison
            else:
                # Try to get basic statistics if comparison fails
                self._update_status("Calculating statistics from raw data...")
                self._update_from_basic_stats()
                
        except Exception as e:
            logger.error(f"Error updating comparison data: {e}")
            self._update_status(f"Error: {str(e)}", is_error=True)
            self._show_no_data()
        finally:
            # Hide progress bar after a short delay
            QTimer.singleShot(500, self.trend_progress.hide)
    
    def _update_status(self, message: str, is_error: bool = False):
        """Update the status message."""
        self.trend_label.setText(message)
        if is_error:
            self.trend_label.setStyleSheet("color: #d32f2f;")
            self.trend_icon.setText("❌")
        else:
            self.trend_label.setStyleSheet("color: #666666;")
            self.trend_icon.setText("⏳")
    
    def _update_from_basic_stats(self):
        """Update cards with basic statistics."""
        if not self.comparative_engine:
            return
            
        try:
            # Get data for different periods
            from datetime import datetime, timedelta
            now = datetime.now()
            
            # 7-day average
            self._update_status("Calculating 7-day average...")
            self.trend_progress.setValue(1)
            QApplication.processEvents()  # Update UI
            
            week_ago = now - timedelta(days=7)
            week_stats = self._get_period_stats(week_ago, now, "7-day")
            if week_stats:
                self.week_card.set_value(week_stats['mean'], self._determine_trend(week_stats))
            else:
                self.week_card.set_loading(False)
                self.week_card.value_label.setText("--")
                
            # 30-day average
            self._update_status("Calculating 30-day average...")
            self.trend_progress.setValue(2)
            QApplication.processEvents()
            
            month_ago = now - timedelta(days=30)
            month_stats = self._get_period_stats(month_ago, now, "30-day")
            if month_stats:
                self.month_card.set_value(month_stats['mean'], self._determine_trend(month_stats))
            else:
                self.month_card.set_loading(False)
                self.month_card.value_label.setText("--")
                
            # 90-day average
            self._update_status("Calculating 90-day average...")
            self.trend_progress.setValue(3)
            QApplication.processEvents()
            
            quarter_ago = now - timedelta(days=90)
            quarter_stats = self._get_period_stats(quarter_ago, now, "90-day")
            if quarter_stats:
                self.quarter_card.set_value(quarter_stats['mean'], self._determine_trend(quarter_stats))
            else:
                self.quarter_card.set_loading(False)
                self.quarter_card.value_label.setText("--")
                
            # 365-day average
            self._update_status("Calculating yearly average...")
            self.trend_progress.setValue(4)
            QApplication.processEvents()
            
            year_ago = now - timedelta(days=365)
            year_stats = self._get_period_stats(year_ago, now, "365-day")
            if year_stats:
                self.year_card.set_value(year_stats['mean'], self._determine_trend(year_stats))
            else:
                self.year_card.set_loading(False)
                self.year_card.value_label.setText("--")
            
            # Update final status
            self._update_status("Analysis complete")
            self.trend_icon.setText("✓")
            self.trend_label.setStyleSheet("color: #4CAF50;")
                
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            self._update_status(f"Calculation error: {str(e)}", is_error=True)
            self._show_no_data()
    
    def _get_period_stats(self, start_date, end_date, period_name):
        """Get statistics for a specific period."""
        try:
            if self.comparative_engine:
                # Update status with period details
                self._update_status(f"Accessing {period_name} data ({start_date.strftime('%m/%d')} to {end_date.strftime('%m/%d')})...")
                
                # Try to get stats from daily calculator
                if hasattr(self.comparative_engine, 'daily_calculator') and self.comparative_engine.daily_calculator:
                    calc = self.comparative_engine.daily_calculator
                    
                    # Try different methods to get data
                    data = None
                    if hasattr(calc, 'calculate_statistics'):
                        self._update_status(f"Retrieving {period_name} aggregated statistics...")
                        # Get aggregated stats for the period
                        try:
                            stats = calc.calculate_statistics(self.current_metric, start_date, end_date)
                            if stats and hasattr(stats, 'mean'):
                                return {
                                    'mean': stats.mean,
                                    'std': stats.std if hasattr(stats, 'std') else 0,
                                    'count': stats.count if hasattr(stats, 'count') else 0,
                                    'period': period_name
                                }
                        except Exception as e:
                            logger.debug(f"calculate_statistics failed: {e}")
                    
                    if hasattr(calc, 'get_daily_summary'):
                        self._update_status(f"Loading {period_name} daily summaries...")
                        # Get daily summaries and calculate average
                        try:
                            summaries = calc.get_daily_summary(start_date, end_date)
                            if summaries and not summaries.empty:
                                # Find the column for our metric
                                metric_col = None
                                for col in summaries.columns:
                                    if self.current_metric in col or col == self.current_metric:
                                        metric_col = col
                                        break
                                
                                if metric_col and metric_col in summaries.columns:
                                    valid_data = summaries[metric_col].dropna()
                                    if len(valid_data) > 0:
                                        self._update_status(f"Processing {len(valid_data)} days of {period_name} data...")
                                        return {
                                            'mean': valid_data.mean(),
                                            'std': valid_data.std(),
                                            'count': len(valid_data),
                                            'period': period_name
                                        }
                        except Exception as e:
                            logger.debug(f"get_daily_summary failed: {e}")
                    
                    # Fallback: try to get raw data
                    if hasattr(calc, 'data') and calc.data is not None:
                        self._update_status(f"Analyzing raw {period_name} data...")
                        import pandas as pd
                        df = calc.data
                        if isinstance(df, pd.DataFrame) and 'type' in df.columns:
                            # Filter by metric type and date range
                            mask = (df['type'] == self.current_metric)
                            if 'creationDate' in df.columns:
                                dates = pd.to_datetime(df['creationDate'])
                                mask &= (dates >= pd.to_datetime(start_date)) & (dates <= pd.to_datetime(end_date))
                            
                            metric_data = df[mask]
                            if len(metric_data) > 0 and 'value' in metric_data.columns:
                                self._update_status(f"Processing {len(metric_data)} {period_name} records...")
                                values = pd.to_numeric(metric_data['value'], errors='coerce').dropna()
                                if len(values) > 0:
                                    return {
                                        'mean': values.mean(),
                                        'std': values.std(),
                                        'count': len(values),
                                        'period': period_name
                                    }
                            else:
                                self._update_status(f"No {period_name} data found for selected metric")
                    
        except Exception as e:
            logger.error(f"Error getting {period_name} stats: {e}")
            self._update_status(f"Error processing {period_name}: {str(e)}", is_error=True)
        return None
    
    def _determine_trend(self, stats):
        """Determine trend based on statistics."""
        # Simple trend determination - could be enhanced
        if stats and stats.get('count', 0) > 3:
            return 'stable'
        return 'stable'
    
    def _show_no_data(self):
        """Show no data state for all cards."""
        for card in [self.week_card, self.month_card, self.quarter_card, self.year_card]:
            card.set_loading(False)
            card.value_label.setText("--")
            card.comparison_label.setText("No data available")
            card.insight_label.setText("")
        
    def update_comparison(self, historical: HistoricalComparison, 
                         current_value: float = None):
        """Update the historical comparison display."""
        self._update_status("Updating comparison displays...")
        self.trend_progress.setValue(1)
        
        # Get current value from the most recent data if not provided
        if current_value is None or current_value == 0:
            if historical.rolling_7_day and historical.rolling_7_day.mean is not None:
                current_value = historical.rolling_7_day.mean
            elif historical.rolling_30_day and historical.rolling_30_day.mean is not None:
                current_value = historical.rolling_30_day.mean
            else:
                current_value = 0
        
        # Update 7-day
        if historical.rolling_7_day and historical.rolling_7_day.mean is not None:
            self.week_card.set_value(historical.rolling_7_day.mean, 'stable')
        else:
            self.week_card.value_label.setText("--")
            self.week_card.comparison_label.setText("No historical data")
        
        self.trend_progress.setValue(2)
        
        # Update 30-day
        if historical.rolling_30_day and historical.rolling_30_day.mean is not None:
            self.month_card.set_value(historical.rolling_30_day.mean, 'stable')
        else:
            self.month_card.value_label.setText("--")
            self.month_card.comparison_label.setText("No historical data")
        
        self.trend_progress.setValue(3)
        
        # Update 90-day
        if historical.rolling_90_day and historical.rolling_90_day.mean is not None:
            self.quarter_card.set_value(historical.rolling_90_day.mean, 'stable')
        else:
            self.quarter_card.value_label.setText("--")
            self.quarter_card.comparison_label.setText("No historical data")
        
        self.trend_progress.setValue(4)
        
        # Update 365-day
        if historical.rolling_365_day and historical.rolling_365_day.mean is not None:
            self.year_card.set_value(historical.rolling_365_day.mean, 'stable')
            if historical.personal_best:
                self.year_card.set_insight(
                    f"Personal best: {historical.personal_best[1]:,.0f}"
                )
        else:
            self.year_card.value_label.setText("--")
            self.year_card.comparison_label.setText("No historical data")
        
        # Update trend analysis
        self._update_status("Analyzing trends...")
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
        else:
            self._update_status("Analysis complete")

# PeerGroupComparisonWidget class removed - Group comparison feature no longer supported
# class PeerGroupComparisonWidget(QWidget):
#     """Widget for displaying peer group comparisons."""
#     
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setup_ui()
#         
#     def setup_ui(self):
#         """Initialize the UI."""
#         layout = QVBoxLayout(self)
#         
#         # Title section
#         title_layout = QHBoxLayout()
#         
#         title = QLabel("Group Comparison")
#         title.setStyleSheet("""
#             font-size: 16px;
#             font-weight: bold;
#             color: #333333;
#         """)
#         title_layout.addWidget(title)
#         
#         # Privacy indicator
#         self.privacy_label = QLabel("🔒 Anonymous")
#         self.privacy_label.setStyleSheet("""
#             font-size: 12px;
#             color: #666666;
#             background-color: #F5F5F5;
#             padding: 4px 8px;
#             border-radius: 4px;
#         """)
#         title_layout.addWidget(self.privacy_label)
#         title_layout.addStretch()
#         
#         layout.addLayout(title_layout)
#         
#         # Main content
#         content_layout = QHBoxLayout()
#         
#         # Percentile gauge
#         self.gauge = PercentileGauge()
#         content_layout.addWidget(self.gauge)
#         
#         # Stats panel
#         stats_frame = QFrame(self)
#         stats_frame.setFrameStyle(QFrame.Shape.Box)
#         stats_frame.setStyleSheet("""
#             background-color: #FAFAFA;
#             border: 1px solid #E0E0E0;
#             border-radius: 4px;
#             padding: 10px;
#         """)
#         
#         stats_layout = QVBoxLayout(stats_frame)
#         
#         self.group_name_label = QLabel("Group: --")
#         self.group_name_label.setStyleSheet("font-weight: bold;")
#         stats_layout.addWidget(self.group_name_label)
#         
#         self.members_label = QLabel("Members: --")
#         stats_layout.addWidget(self.members_label)
#         
#         stats_layout.addSpacing(10)
#         
#         self.avg_label = QLabel("Group Average: --")
#         stats_layout.addWidget(self.avg_label)
#         
#         self.range_label = QLabel("Range: --")
#         stats_layout.addWidget(self.range_label)
#         
#         stats_layout.addStretch()
#         
#         content_layout.addWidget(stats_frame)
#         
#         layout.addLayout(content_layout)
#         
#         # Insights
#         self.insights_frame = QGroupBox("Insights")
#         self.insights_frame.setStyleSheet("""
#             QGroupBox {
#                 font-weight: bold;
#                 border: 1px solid #E0E0E0;
#                 border-radius: 4px;
#                 margin-top: 10px;
#                 padding-top: 10px;
#             }
#             QGroupBox::title {
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 5px 0 5px;
#             }
#         """)
#         
#         self.insights_layout = QVBoxLayout(self.insights_frame)
#         layout.addWidget(self.insights_frame)
#         
#     def update_comparison(self, comparison: GroupComparison, group_name: str):
#         """Update the peer group comparison display."""
#         if comparison.error:
#             # Show error state
#             self.gauge.set_value(0)
#             self.gauge.set_label("No Data")
#             self.gauge.set_subtitle(comparison.error)
#             return
#             
#         # Update group info
#         self.group_name_label.setText(f"Group: {group_name}")
#         self.members_label.setText(
#             f"Members: {comparison.group_stats.get('member_count', 0)}"
#         )
#         
#         # Update stats
#         stats = comparison.group_stats
#         self.avg_label.setText(f"Group Average: {stats.get('mean', 0):,.0f}")
#         self.range_label.setText(
#             f"Range: {stats.get('min', 0):,.0f} - {stats.get('max', 0):,.0f}"
#         )
#         
#         # Calculate and update percentile
#         if comparison.user_value and stats.get('mean'):
#             # Simple percentile calculation
#             percentile = self._estimate_percentile(
#                 comparison.user_value, stats
#             )
#             self.gauge.set_value(percentile)
#             
#             # Set color based on ranking
#             if comparison.anonymous_ranking == "top quarter":
#                 self.gauge.set_color('#4CAF50')
#             elif comparison.anonymous_ranking == "upper half":
#                 self.gauge.set_color('#2196F3')
#             elif comparison.anonymous_ranking == "middle range":
#                 self.gauge.set_color('#FF9800')
#             else:
#                 self.gauge.set_color('#9C27B0')
#                 
#             self.gauge.set_label(comparison.anonymous_ranking.title())
#             
#         # Update insights
#         # Clear old insights
#         while self.insights_layout.count():
#             child = self.insights_layout.takeAt(0)
#             if child.widget():
#                 child.widget().deleteLater()
#                 
#         # Add new insights
#         for insight in comparison.insights[:3]:  # Show top 3
#             insight_label = QLabel(f"• {insight}")
#             insight_label.setWordWrap(True)
#             insight_label.setStyleSheet("""
#                 color: #666666;
#                 padding: 2px 0;
#             """)
#             self.insights_layout.addWidget(insight_label)
#             
#     def _estimate_percentile(self, value: float, stats: Dict) -> float:
#         """Estimate percentile from stats."""
#         # Simple linear interpolation
#         if value <= stats.get('min', 0):
#             return 5
#         elif value >= stats.get('max', 0):
#             return 95
#         elif value <= stats.get('percentile_25', 0):
#             return 25 * (value - stats['min']) / (stats['percentile_25'] - stats['min'])
#         elif value <= stats.get('median', 0):
#             return 25 + 25 * (value - stats['percentile_25']) / (stats['median'] - stats['percentile_25'])
#         elif value <= stats.get('percentile_75', 0):
#             return 50 + 25 * (value - stats['median']) / (stats['percentile_75'] - stats['median'])
#         else:
#             return 75 + 20 * (value - stats['percentile_75']) / (stats['max'] - stats['percentile_75'])


class SeasonalTrendsWidget(QWidget):
    """Widget for displaying seasonal trends with loading state."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comparative_engine = None
        self.current_metric = None
        self.is_loading = True
        self.seasonal_data = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Loading state
        self.loading_label = QLabel("Seasonal Trends (caching...)")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 18px;
            color: #666666;
            padding: 40px;
        """)
        layout.addWidget(self.loading_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Content widget (hidden initially)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_widget.hide()
        layout.addWidget(self.content_widget)
        
        layout.addStretch()
        
    def set_comparative_engine(self, engine):
        """Set the comparative analytics engine."""
        self.comparative_engine = engine
        
    def set_current_metric(self, metric: str):
        """Set the current metric."""
        self.current_metric = metric
        
    def update_metric(self, metric: str):
        """Update the displayed metric and start loading seasonal data."""
        self.current_metric = metric
        self.show_loading()
        
        # Start loading seasonal data
        if self.comparative_engine:
            # Simulate async loading - in real implementation this would be async
            QTimer.singleShot(2000, self.load_seasonal_data)
        
    def show_loading(self):
        """Show loading state."""
        self.is_loading = True
        self.loading_label.show()
        self.progress_bar.show()
        self.content_widget.hide()
        
    def load_seasonal_data(self):
        """Load seasonal pattern data."""
        if not self.comparative_engine:
            self.show_no_data()
            return
            
        try:
            # Get seasonal analyzer
            if hasattr(self.comparative_engine, 'seasonal_analyzer'):
                analyzer = self.comparative_engine.seasonal_analyzer
                
                # Analyze seasonal patterns
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                patterns = analyzer.analyze_seasonal_patterns(
                    self.current_metric,
                    start_date,
                    end_date
                )
                
                self.seasonal_data = patterns
                self.show_seasonal_patterns()
            else:
                self.show_no_data()
                
        except Exception as e:
            logger.error(f"Error loading seasonal data: {e}")
            self.show_error()
    
    def show_seasonal_patterns(self):
        """Display the loaded seasonal patterns."""
        self.is_loading = False
        self.loading_label.hide()
        self.progress_bar.hide()
        
        # Clear content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add title
        title = QLabel("Seasonal Trends")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #333333;
            padding: 10px 0;
        """)
        self.content_layout.addWidget(title)
        
        # Add seasonal pattern visualization
        if self.seasonal_data:
            # Pattern strength indicator
            strength_widget = self._create_strength_widget()
            self.content_layout.addWidget(strength_widget)
            
            # Key findings
            findings_widget = self._create_findings_widget()
            self.content_layout.addWidget(findings_widget)
            
            # Seasonal chart placeholder
            chart_label = QLabel("Seasonal pattern visualization coming soon...")
            chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_label.setStyleSheet("""
                background: #f5f5f5;
                border: 1px solid #ddd;
                padding: 60px;
                color: #666;
            """)
            self.content_layout.addWidget(chart_label)
        
        self.content_layout.addStretch()
        self.content_widget.show()
        
    def _create_strength_widget(self) -> QWidget:
        """Create seasonal strength indicator."""
        widget = QGroupBox("Pattern Strength")
        layout = QHBoxLayout(widget)
        
        if self.seasonal_data and hasattr(self.seasonal_data, 'seasonal_strength'):
            strength_label = QLabel(f"Strength: {self.seasonal_data.seasonal_strength.value}")
            strength_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(strength_label)
        
        return widget
        
    def _create_findings_widget(self) -> QWidget:
        """Create key findings widget."""
        widget = QGroupBox("Key Findings")
        layout = QVBoxLayout(widget)
        
        if self.seasonal_data and hasattr(self.seasonal_data, 'insights'):
            for insight in self.seasonal_data.insights[:3]:
                label = QLabel(f"• {insight}")
                label.setWordWrap(True)
                layout.addWidget(label)
        else:
            label = QLabel("Analyzing seasonal patterns...")
            layout.addWidget(label)
        
        return widget
        
    def show_no_data(self):
        """Show no data available state."""
        self.is_loading = False
        self.loading_label.setText("No seasonal data available")
        self.progress_bar.hide()
        
    def show_error(self):
        """Show error state."""
        self.is_loading = False
        self.loading_label.setText("Error loading seasonal trends")
        self.loading_label.setStyleSheet("""
            font-size: 18px;
            color: #d32f2f;
            padding: 40px;
        """)
        self.progress_bar.hide()


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
        
        # Group comparison button removed
        # self.group_btn = QPushButton("Group Comparison")
        # self.group_btn.setCheckable(True)
        
        self.seasonal_btn = QPushButton("Seasonal Trends")
        self.seasonal_btn.setCheckable(True)
        
        nav_layout.addWidget(self.personal_btn)
        # nav_layout.addWidget(self.group_btn)  # Group comparison removed
        nav_layout.addWidget(self.seasonal_btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # Content area
        self.content_stack = QVBoxLayout()
        
        # Personal comparison
        self.historical_widget = HistoricalComparisonWidget()
        self.historical_widget.metric_changed.connect(self.on_metric_changed)
        
        # Group comparison removed
        # self.group_widget = PeerGroupComparisonWidget()
        # self.group_widget.hide()
        
        self.content_stack.addWidget(self.historical_widget)
        # self.content_stack.addWidget(self.group_widget)  # Group comparison removed
        
        layout.addLayout(self.content_stack)
        layout.addStretch()
        
        # Connect buttons
        self.personal_btn.clicked.connect(self.show_personal)
        # self.group_btn.clicked.connect(self.show_group)  # Group comparison removed
        self.seasonal_btn.clicked.connect(self.show_seasonal)
        
    def show_personal(self):
        """Show personal comparison view."""
        self.personal_btn.setChecked(True)
        # self.group_btn.setChecked(False)  # Group comparison removed
        self.seasonal_btn.setChecked(False)
        
        self.historical_widget.show()
        # self.group_widget.hide()  # Group comparison removed
        
        # Hide seasonal widget if it exists
        if hasattr(self, 'seasonal_widget'):
            self.seasonal_widget.hide()
        
    # Group comparison method removed
    # def show_group(self):
    #     """Show group comparison view."""
    #     self.personal_btn.setChecked(False)
    #     self.group_btn.setChecked(True)
    #     self.seasonal_btn.setChecked(False)
    #     
    #     self.historical_widget.hide()
    #     self.group_widget.show()
        
    def show_seasonal(self):
        """Show seasonal trends view."""
        self.personal_btn.setChecked(False)
        # self.group_btn.setChecked(False)  # Group comparison removed
        self.seasonal_btn.setChecked(True)
        
        # Hide other widgets
        self.historical_widget.hide()
        # self.group_widget.hide()  # Group comparison removed
        
        # Check if seasonal widget exists
        if not hasattr(self, 'seasonal_widget'):
            # Create seasonal widget with loading state
            self.seasonal_widget = SeasonalTrendsWidget()
            self.content_stack.addWidget(self.seasonal_widget)
            
            # Connect to comparative engine if available
            if self.comparative_engine:
                self.seasonal_widget.set_comparative_engine(self.comparative_engine)
                self.seasonal_widget.set_current_metric(self.current_metric)
        
        # Show seasonal widget
        self.seasonal_widget.show()
        
        # Update with current metric
        if hasattr(self, 'current_metric'):
            self.seasonal_widget.update_metric(self.current_metric)
    
    def on_metric_changed(self, metric: str):
        """Handle metric change from historical widget."""
        self.current_metric = metric
        self.set_current_metric(metric)
    
    def set_comparative_engine(self, engine):
        """Set the comparative analytics engine."""
        self.comparative_engine = engine
        logger.info("Comparative engine set for visualization widget")
        
        # Pass engine to historical widget
        self.historical_widget.set_comparative_engine(engine)
        
        # Pass engine to seasonal widget if it exists
        if hasattr(self, 'seasonal_widget'):
            self.seasonal_widget.set_comparative_engine(engine)
        
        # Trigger initial trend calculation for default metric
        if engine and hasattr(engine, 'background_processor') and engine.background_processor:
            engine.background_processor.queue_trend_calculation(self.current_metric, priority=10)
            
        # Initialize historical widget with default metric
        self.historical_widget.on_metric_changed("Steps")
            
    def set_current_metric(self, metric: str):
        """Set the current metric and update display."""
        self.current_metric = metric
        self.update_comparisons()
        
        # Update seasonal widget if it exists
        if hasattr(self, 'seasonal_widget'):
            self.seasonal_widget.update_metric(metric)
        
    def update_comparisons(self):
        """Update comparison displays using cached trends."""
        if not self.comparative_engine:
            logger.warning("No comparative engine set")
            return
            
        # Get cached trend data
        trend_data = self.comparative_engine.get_trend_analysis(self.current_metric, use_cache=True)
        
        # Check if trend_data exists and is not an empty DataFrame
        has_trend_data = (
            trend_data is not None and 
            (not isinstance(trend_data, pd.DataFrame) or not trend_data.empty)
        )
        
        if has_trend_data:
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