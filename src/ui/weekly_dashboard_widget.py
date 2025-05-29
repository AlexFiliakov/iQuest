"""
Weekly dashboard widget for viewing weekly health metrics and trends.

This widget provides comprehensive weekly health data analysis including:
- 7-day rolling statistics
- Week-over-week comparisons
- Weekly patterns and trends
- Day-of-week analysis
- Volatility scoring
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QGroupBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from .summary_cards import SummaryCard
from .week_over_week_widget import WeekOverWeekWidget
from .charts.line_chart import LineChart
from .bar_chart_component import BarChart as BarChartComponent
from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator, WeeklyMetrics, TrendInfo
from ..analytics.day_of_week_analyzer import DayOfWeekAnalyzer, DayOfWeekPattern
from ..analytics.week_over_week_trends import WeekOverWeekTrendAnalyzer
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class WeeklyStatCard(QFrame):
    """Statistical card for weekly metrics."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the card UI."""
        self.setFixedHeight(100)
        from .style_manager import StyleManager
        style_manager = StyleManager()
        shadow = style_manager.get_shadow_style('md')
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style_manager.PRIMARY_BG};
                border: {shadow['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(QFont('Segoe UI Emoji', 14))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont('Inter', 11))
        title_label.setStyleSheet(f"color: {style_manager.TEXT_SECONDARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Main value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont('Inter', 20, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {style_manager.ACCENT_PRIMARY};")
        layout.addWidget(self.value_label)
        
        # Sub-label
        self.sub_label = QLabel("")
        self.sub_label.setFont(QFont('Inter', 10))
        self.sub_label.setStyleSheet(f"color: {style_manager.TEXT_MUTED};")
        layout.addWidget(self.sub_label)
        
    def update_value(self, value: str, sub_label: str = ""):
        """Update the displayed values."""
        self.value_label.setText(value)
        self.sub_label.setText(sub_label)


class WeeklyDashboardWidget(QWidget):
    """
    Weekly dashboard widget showing 7-day rolling statistics and trends.
    
    Features:
    - Week-at-a-glance summary
    - Week-over-week comparisons
    - Day-of-week patterns
    - Trend analysis
    - Best/worst day tracking
    - Volatility scoring
    """
    
    # Signals
    week_changed = pyqtSignal(date, date)  # start_date, end_date
    metric_selected = pyqtSignal(str)
    
    def __init__(self, weekly_calculator=None, daily_calculator=None, parent=None):
        """Initialize the weekly dashboard widget."""
        super().__init__(parent)
        
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator
        self.wow_analyzer = WeekOverWeekTrendAnalyzer(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(daily_calculator) if daily_calculator else None
        
        # Calculate current week boundaries
        today = date.today()
        self._current_week_start = today - timedelta(days=today.weekday())  # Monday
        self._current_week_end = self._current_week_start + timedelta(days=6)  # Sunday
        
        self._available_metrics = []
        self._selected_metric = "steps"
        
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        if self.weekly_calculator:
            self._detect_available_metrics()
            self._load_weekly_data()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area with scroll
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F5E6D3;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #FF8C42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #E67A35;
            }
        """)
        
        # Content widget
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Weekly summary section
        summary_section = self._create_summary_section()
        content_layout.addWidget(summary_section)
        
        # Week-over-week comparison
        wow_section = self._create_wow_section()
        content_layout.addWidget(wow_section)
        
        # Day patterns section
        patterns_section = self._create_patterns_section()
        content_layout.addWidget(patterns_section)
        
        # Detailed charts section
        charts_section = self._create_charts_section()
        content_layout.addWidget(charts_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_header(self) -> QWidget:
        """Create the dashboard header with week navigation."""
        header = QFrame(self)
        header.setStyleSheet("""
            QFrame {
                background-color: #FFF8F0;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(20)
        
        # Week navigation
        nav_layout = QHBoxLayout()
        
        # Previous week button
        self.prev_week_btn = QPushButton("◀")
        self.prev_week_btn.setFixedSize(40, 40)
        self.prev_week_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #E8DCC8;
                border-radius: 20px;
                color: #5D4E37;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border-color: #FF8C42;
                color: #FF8C42;
            }
        """)
        self.prev_week_btn.setToolTip("Previous week")
        nav_layout.addWidget(self.prev_week_btn)
        
        # Week label
        week_layout = QVBoxLayout()
        
        self.week_label = QLabel()
        self.week_label.setFont(QFont('Poppins', 18, QFont.Weight.Bold))
        self.week_label.setStyleSheet("color: #5D4E37;")
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.week_label)
        
        self.date_range_label = QLabel()
        self.date_range_label.setFont(QFont('Inter', 12))
        self.date_range_label.setStyleSheet("color: #8B7355;")
        self.date_range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.date_range_label)
        
        nav_layout.addLayout(week_layout)
        
        # Next week button
        self.next_week_btn = QPushButton("▶")
        self.next_week_btn.setFixedSize(40, 40)
        self.next_week_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #E8DCC8;
                border-radius: 20px;
                color: #5D4E37;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border-color: #FF8C42;
                color: #FF8C42;
            }
        """)
        self.next_week_btn.setToolTip("Next week")
        nav_layout.addWidget(self.next_week_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # This week button
        self.this_week_btn = QPushButton("This Week")
        self.this_week_btn.setFixedSize(100, 40)
        self.this_week_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C42;
                color: white;
                border-radius: 20px;
                font-family: Poppins;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E67A35;
            }
            QPushButton:disabled {
                background-color: rgba(255, 140, 66, 0.5);
            }
        """)
        layout.addWidget(self.this_week_btn)
        
        self._update_week_labels()
        
        return header
    
    def _create_summary_section(self) -> QWidget:
        """Create the weekly summary section."""
        section = QGroupBox("Week at a Glance")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Metric selector
        selector_layout = QHBoxLayout()
        
        metric_label = QLabel("Metric:")
        metric_label.setFont(QFont('Inter', 12))
        metric_label.setStyleSheet("color: #5D4E37;")
        selector_layout.addWidget(metric_label)
        
        self.metric_selector = QComboBox()
        self.metric_selector.setMinimumWidth(200)
        self.metric_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Poppins;
                color: #5D4E37;
            }
        """)
        selector_layout.addWidget(self.metric_selector)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Statistics cards grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Create stat cards
        self.stat_cards = {
            'average': WeeklyStatCard("Weekly Average", "📊"),
            'total': WeeklyStatCard("Weekly Total", "Σ"),
            'best': WeeklyStatCard("Best Day", "🏆"),
            'worst': WeeklyStatCard("Worst Day", "📉"),
            'trend': WeeklyStatCard("Trend", "📈"),
            'volatility': WeeklyStatCard("Volatility", "📊")
        }
        
        # Arrange cards in grid
        positions = [
            ('average', 0, 0), ('total', 0, 1), ('best', 0, 2),
            ('worst', 1, 0), ('trend', 1, 1), ('volatility', 1, 2)
        ]
        
        for key, row, col in positions:
            stats_grid.addWidget(self.stat_cards[key], row, col)
        
        layout.addLayout(stats_grid)
        
        return section
    
    def _create_wow_section(self) -> QWidget:
        """Create the week-over-week comparison section."""
        section = QGroupBox("Week-over-Week Comparison")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # WoW widget
        self.wow_widget = WeekOverWeekWidget()
        self.wow_widget.setMinimumHeight(300)
        layout.addWidget(self.wow_widget)
        
        return section
    
    def _create_patterns_section(self) -> QWidget:
        """Create the day-of-week patterns section."""
        section = QGroupBox("Weekly Patterns")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Day-of-week chart
        self.dow_chart = BarChartComponent()
        self.dow_chart.setMinimumHeight(250)
        
        # Configure chart styling will be done when plotting
        
        layout.addWidget(self.dow_chart)
        
        # Pattern insights
        self.pattern_label = QLabel("Loading patterns...")
        self.pattern_label.setFont(QFont('Inter', 12))
        self.pattern_label.setStyleSheet("color: #8B7355; padding: 10px;")
        self.pattern_label.setWordWrap(True)
        layout.addWidget(self.pattern_label)
        
        return section
    
    def _create_charts_section(self) -> QWidget:
        """Create the detailed charts section."""
        section = QGroupBox("Weekly Trend")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # View options
        view_layout = QHBoxLayout()
        
        view_label = QLabel("View:")
        view_label.setFont(QFont('Inter', 12))
        view_label.setStyleSheet("color: #5D4E37;")
        view_layout.addWidget(view_label)
        
        # Radio buttons for view selection
        self.view_group = QButtonGroup(self)
        
        self.daily_view_rb = QRadioButton("Daily Values")
        self.daily_view_rb.setChecked(True)
        self.view_group.addButton(self.daily_view_rb, 0)
        view_layout.addWidget(self.daily_view_rb)
        
        self.cumulative_view_rb = QRadioButton("Cumulative")
        self.view_group.addButton(self.cumulative_view_rb, 1)
        view_layout.addWidget(self.cumulative_view_rb)
        
        self.rolling_view_rb = QRadioButton("7-Day Average")
        self.view_group.addButton(self.rolling_view_rb, 2)
        view_layout.addWidget(self.rolling_view_rb)
        
        view_layout.addStretch()
        layout.addLayout(view_layout)
        
        # Trend chart
        self.trend_chart = LineChart()
        self.trend_chart.setMinimumHeight(300)
        
        # Configure chart
        self.trend_chart.set_labels(title="", x_label="Date", y_label="Value")
        self.trend_chart.show_grid = True
        
        layout.addWidget(self.trend_chart)
        
        return section
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.prev_week_btn.clicked.connect(self._go_to_previous_week)
        self.next_week_btn.clicked.connect(self._go_to_next_week)
        self.this_week_btn.clicked.connect(self._go_to_current_week)
        
        self.metric_selector.currentTextChanged.connect(self._on_metric_changed)
        self.view_group.buttonClicked.connect(self._update_trend_chart)
    
    def _detect_available_metrics(self):
        """Detect available metrics from the data."""
        if not self.weekly_calculator or not self.weekly_calculator.daily_calculator:
            return
            
        try:
            # Get unique metric types
            data = self.weekly_calculator.daily_calculator.data
            available_types = data['type'].unique()
            
            # Map to display names
            metric_mapping = {
                'HKQuantityTypeIdentifierStepCount': ('Steps', 'steps'),
                'HKQuantityTypeIdentifierDistanceWalkingRunning': ('Distance (km)', 'distance'),
                'HKQuantityTypeIdentifierFlightsClimbed': ('Floors Climbed', 'flights'),
                'HKQuantityTypeIdentifierActiveEnergyBurned': ('Active Calories', 'calories'),
                'HKQuantityTypeIdentifierHeartRate': ('Heart Rate', 'heart_rate'),
                'HKQuantityTypeIdentifierRestingHeartRate': ('Resting HR', 'resting_hr'),
                'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': ('HRV', 'hrv'),
                'HKQuantityTypeIdentifierBodyMass': ('Weight', 'weight')
            }
            
            self._available_metrics = []
            self.metric_selector.clear()
            
            for hk_type, (display_name, metric_key) in metric_mapping.items():
                if hk_type in available_types:
                    self._available_metrics.append((hk_type, metric_key))
                    self.metric_selector.addItem(display_name, hk_type)
            
            if self._available_metrics:
                self._selected_metric = self._available_metrics[0][0]
                
        except Exception as e:
            logger.error(f"Error detecting available metrics: {e}")
    
    def _update_week_labels(self):
        """Update the week display labels."""
        # Calculate week number
        week_num = self._current_week_start.isocalendar()[1]
        year = self._current_week_start.year
        
        # Check if this is the current week
        today = date.today()
        is_current_week = (self._current_week_start <= today <= self._current_week_end)
        
        # Update labels
        if is_current_week:
            self.week_label.setText("This Week")
        else:
            self.week_label.setText(f"Week {week_num}, {year}")
        
        # Format date range
        if self._current_week_start.month == self._current_week_end.month:
            date_range = f"{self._current_week_start.strftime('%b %d')} - {self._current_week_end.strftime('%d, %Y')}"
        else:
            date_range = f"{self._current_week_start.strftime('%b %d')} - {self._current_week_end.strftime('%b %d, %Y')}"
        
        self.date_range_label.setText(date_range)
        
        # Update button states
        self.this_week_btn.setEnabled(not is_current_week)
    
    def _load_weekly_data(self):
        """Load data for the current week."""
        if not self.weekly_calculator:
            return
            
        try:
            # Get selected metric
            metric_type = self.metric_selector.currentData()
            if not metric_type:
                return
            
            # Calculate weekly statistics
            self._update_summary_stats(metric_type)
            
            # Update week-over-week comparison
            self._update_wow_comparison(metric_type)
            
            # Update day-of-week patterns
            self._update_dow_patterns(metric_type)
            
            # Update trend chart
            self._update_trend_chart()
            
        except Exception as e:
            logger.error(f"Error loading weekly data: {e}")
    
    def _update_summary_stats(self, metric_type: str):
        """Update the summary statistics cards."""
        try:
            # Get weekly data
            weekly_data = self.weekly_calculator.get_weekly_metrics(
                metric=metric_type,
                week_start=self._current_week_start
            )
            
            if not weekly_data:
                return
            
            # Update average
            avg_value = weekly_data.avg
            self.stat_cards['average'].update_value(
                f"{avg_value:,.0f}" if avg_value >= 100 else f"{avg_value:.1f}",
                "daily average"
            )
            
            # Update total
            total = sum(weekly_data.daily_values.values())
            self.stat_cards['total'].update_value(
                f"{total:,.0f}" if total >= 100 else f"{total:.1f}",
                "weekly total"
            )
            
            # Update best/worst days
            if weekly_data.daily_values:
                best_date = max(weekly_data.daily_values, key=weekly_data.daily_values.get)
                worst_date = min(weekly_data.daily_values, key=weekly_data.daily_values.get)
                
                self.stat_cards['best'].update_value(
                    f"{weekly_data.daily_values[best_date]:,.0f}",
                    best_date.strftime("%a")
                )
                
                self.stat_cards['worst'].update_value(
                    f"{weekly_data.daily_values[worst_date]:,.0f}",
                    worst_date.strftime("%a")
                )
            
            # Update trend
            trend_symbol = "↑" if weekly_data.trend_direction == "up" else "↓" if weekly_data.trend_direction == "down" else "→"
            self.stat_cards['trend'].update_value(
                trend_symbol,
                weekly_data.trend_direction
            )
            
            # Calculate volatility
            if weekly_data.daily_values:
                values = list(weekly_data.daily_values.values())
                if len(values) > 1:
                    volatility = np.std(values) / np.mean(values) * 100 if np.mean(values) > 0 else 0
                    self.stat_cards['volatility'].update_value(
                        f"{volatility:.1f}%",
                        "coefficient of variation"
                    )
                    
        except Exception as e:
            logger.error(f"Error updating summary stats: {e}")
    
    def _update_wow_comparison(self, metric_type: str):
        """Update week-over-week comparison."""
        if not self.wow_analyzer:
            return
            
        try:
            # Get WoW data
            comparison = self.wow_analyzer.get_week_over_week_comparison(
                metric=metric_type,
                target_week=self._current_week_start,
                weeks_back=4
            )
            
            if comparison:
                # Update WoW widget
                self.wow_widget.set_comparison_data(comparison)
                
        except Exception as e:
            logger.error(f"Error updating WoW comparison: {e}")
    
    def _update_dow_patterns(self, metric_type: str):
        """Update day-of-week patterns."""
        if not self.dow_analyzer:
            return
            
        try:
            # Get day-of-week pattern
            pattern = self.dow_analyzer.analyze_day_patterns(
                metric=metric_type,
                start_date=self._current_week_start - timedelta(weeks=12),
                end_date=self._current_week_end
            )
            
            if pattern:
                # Update bar chart
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                values = [pattern.average_by_day.get(i, 0) for i in range(7)]
                
                # Prepare data for bar chart
                import pandas as pd
                df = pd.DataFrame({
                    'Day': days,
                    'Value': values
                })
                df['Color'] = ['#FF8C42' if i < 5 else '#FFD166' for i in range(7)]  # Weekday vs weekend colors
                
                self.dow_chart.plot(df, chart_type='simple', x='Day', y='Value', color_column='Color')
                
                # Update pattern insights
                insights = self._generate_pattern_insights(pattern)
                self.pattern_label.setText(insights)
                
        except Exception as e:
            logger.error(f"Error updating DoW patterns: {e}")
    
    def _generate_pattern_insights(self, pattern: DayOfWeekPattern) -> str:
        """Generate insights from day-of-week patterns."""
        insights = []
        
        # Best/worst days
        if pattern.best_day is not None and pattern.worst_day is not None:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            insights.append(f"Best day: {days[pattern.best_day]} | Worst day: {days[pattern.worst_day]}")
        
        # Weekend vs weekday
        if pattern.weekend_avg is not None and pattern.weekday_avg is not None:
            diff = ((pattern.weekend_avg - pattern.weekday_avg) / pattern.weekday_avg * 100) if pattern.weekday_avg > 0 else 0
            if abs(diff) > 10:
                comparison = "higher" if diff > 0 else "lower"
                insights.append(f"Weekend average is {abs(diff):.0f}% {comparison} than weekdays")
        
        # Consistency
        if pattern.consistency_score is not None:
            if pattern.consistency_score > 0.8:
                insights.append("Very consistent throughout the week")
            elif pattern.consistency_score < 0.5:
                insights.append("High variability between days")
        
        return " • ".join(insights) if insights else "Analyzing patterns..."
    
    def _update_trend_chart(self):
        """Update the trend chart based on selected view."""
        if not self.weekly_calculator:
            return
            
        try:
            metric_type = self.metric_selector.currentData()
            if not metric_type:
                return
            
            # Get daily data for the week
            start_date = self._current_week_start
            end_date = self._current_week_end
            
            # Get data based on view selection
            view_id = self.view_group.checkedId()
            
            if view_id == 0:  # Daily values
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    x_data = [d.strftime("%a") for d in data.index]
                    y_data = data.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = min(y_data) * 0.9
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
            elif view_id == 1:  # Cumulative
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    cumulative = data.cumsum()
                    x_data = [d.strftime("%a") for d in cumulative.index]
                    y_data = cumulative.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = 0  # Cumulative starts at 0
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
            elif view_id == 2:  # 7-day rolling average
                # Get extended data for rolling average
                extended_start = start_date - timedelta(days=6)
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=extended_start,
                    end_date=end_date
                )
                
                if not data.empty:
                    rolling = data.rolling(window=7, min_periods=1).mean()
                    # Filter to current week
                    rolling = rolling[rolling.index >= pd.to_datetime(start_date)]
                    
                    x_data = [d.strftime("%a") for d in rolling.index]
                    y_data = rolling.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = min(y_data) * 0.9
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
        except Exception as e:
            logger.error(f"Error updating trend chart: {e}")
    
    def _go_to_previous_week(self):
        """Navigate to the previous week."""
        self._current_week_start -= timedelta(weeks=1)
        self._current_week_end -= timedelta(weeks=1)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _go_to_next_week(self):
        """Navigate to the next week."""
        self._current_week_start += timedelta(weeks=1)
        self._current_week_end += timedelta(weeks=1)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _go_to_current_week(self):
        """Navigate to the current week."""
        today = date.today()
        self._current_week_start = today - timedelta(days=today.weekday())
        self._current_week_end = self._current_week_start + timedelta(days=6)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _on_metric_changed(self):
        """Handle metric selection change."""
        self._load_weekly_data()
        metric_key = self.metric_selector.currentData()
        if metric_key:
            self.metric_selected.emit(metric_key)
    
    def set_calculators(self, weekly_calculator: WeeklyMetricsCalculator, 
                       daily_calculator=None):
        """Set the calculator instances."""
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator or (
            weekly_calculator.daily_calculator if weekly_calculator else None
        )
        
        self.wow_analyzer = WeekOverWeekTrendAnalyzer(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(self.daily_calculator) if self.daily_calculator else None
        
        self._detect_available_metrics()
        self._load_weekly_data()
    
    def get_current_week(self) -> Tuple[date, date]:
        """Get the current week's start and end dates."""
        return self._current_week_start, self._current_week_end