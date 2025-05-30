"""
Monthly dashboard widget containing the calendar heatmap and related components.

This widget provides the monthly view of health metrics with calendar heatmap visualization,
summary statistics, and month navigation controls.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from calendar import monthrange

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QIcon

from .charts.calendar_heatmap import CalendarHeatmapComponent
from .statistics_widget import StatisticsWidget
from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MonthlyDashboardWidget(QWidget):
    """
    Monthly dashboard widget with calendar heatmap and analytics.
    
    Features:
    - Calendar heatmap visualization
    - Monthly summary statistics
    - Month navigation controls
    - Metric selection dropdown
    - Journal entry integration
    """
    
    # Signals
    month_changed = pyqtSignal(int, int)  # year, month
    metric_changed = pyqtSignal(str)
    
    def __init__(self, monthly_calculator=None, parent=None):
        """Initialize the monthly dashboard widget."""
        super().__init__(parent)
        
        self.monthly_calculator = monthly_calculator
        
        # Always initialize to current date
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Initializing MonthlyDashboardWidget with date: {self._current_month}/{self._current_year}")
        
        self._current_metric = "steps"
        self._available_metrics = ["steps", "heart_rate", "sleep_hours", "distance"]
        
        # Data storage
        self._metric_data = {}
        self._summary_stats = {}
        
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        self._load_month_data()
        
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
                background-color: #F8F9FA;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ADB5BD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6C757D;
            }
        """)
        
        # Content widget
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Calendar heatmap section
        heatmap_section = self._create_heatmap_section()
        content_layout.addWidget(heatmap_section)
        
        # Summary statistics section
        stats_section = self._create_statistics_section()
        content_layout.addWidget(stats_section)
        
        # Journal section placeholder
        journal_section = self._create_journal_section()
        content_layout.addWidget(journal_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_header(self) -> QWidget:
        """Create the dashboard header with navigation and controls."""
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
        
        # Month navigation
        nav_layout = QHBoxLayout()
        
        # Previous month button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setStyleSheet(self._get_nav_button_style())
        self.prev_btn.setToolTip("Previous month")
        nav_layout.addWidget(self.prev_btn)
        
        # Current month/year label
        self.month_label = QLabel(self)
        self.month_label.setFont(QFont('Poppins', 18, QFont.Weight.Bold))
        self.month_label.setStyleSheet("color: #5D4E37; padding: 0 20px;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set fixed width to accommodate longest month name (September) plus year
        # Typical width: "September 2023" with padding
        self.month_label.setFixedWidth(250)
        nav_layout.addWidget(self.month_label)
        
        # Next month button
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet(self._get_nav_button_style())
        self.next_btn.setToolTip("Next month")
        nav_layout.addWidget(self.next_btn)
        
        # Today button
        self.today_btn = QPushButton("Today")
        self.today_btn.setFixedSize(70, 40)
        self.today_btn.setStyleSheet(self._get_nav_button_style())
        self.today_btn.setToolTip("Go to current month")
        nav_layout.addWidget(self.today_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # Metric selector
        metric_layout = QHBoxLayout()
        
        metric_label = QLabel("Metric:", self)
        metric_label.setFont(QFont('Inter', 12, QFont.Weight.Medium))
        metric_label.setStyleSheet("color: #5D4E37;")
        metric_layout.addWidget(metric_label)
        
        self.metric_combo = QComboBox(self)
        self.metric_combo.addItems([
            "Steps", "Heart Rate", "Sleep Hours", "Distance"
        ])
        self.metric_combo.setStyleSheet(self._get_combo_style())
        metric_layout.addWidget(self.metric_combo)
        
        layout.addLayout(metric_layout)
        
        # Update month label
        self._update_month_label()
        
        return header
        
    def _create_heatmap_section(self) -> QWidget:
        """Create the calendar heatmap section."""
        section = QFrame(self)
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Header with title and style toggle
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Activity Calendar")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Style toggle buttons
        self.style_button_group = QButtonGroup()
        
        self.classic_btn = QPushButton("Classic")
        self.classic_btn.setCheckable(True)
        self.classic_btn.setChecked(True)
        self.classic_btn.setFixedSize(80, 32)
        self.classic_btn.clicked.connect(lambda: self._set_calendar_style("classic"))
        self.style_button_group.addButton(self.classic_btn)
        
        self.github_btn = QPushButton("GitHub")
        self.github_btn.setCheckable(True)
        self.github_btn.setChecked(False)
        self.github_btn.setFixedSize(80, 32)
        self.github_btn.clicked.connect(lambda: self._set_calendar_style("github"))
        self.style_button_group.addButton(self.github_btn)
        
        # Style the toggle buttons
        toggle_style = """
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 16px;
                color: #5D4E37;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                border-color: #FF8C42;
                background-color: #FFF8F0;
            }
            QPushButton:checked {
                background-color: #FF8C42;
                border-color: #FF8C42;
                color: #FFFFFF;
            }
        """
        
        self.classic_btn.setStyleSheet(toggle_style)
        self.github_btn.setStyleSheet(toggle_style)
        
        header_layout.addWidget(self.classic_btn)
        header_layout.addWidget(self.github_btn)
        
        layout.addLayout(header_layout)
        
        # Calendar heatmap
        self.calendar_heatmap = CalendarHeatmapComponent()
        self.calendar_heatmap.setMinimumHeight(350)  # Reduced minimum height
        # Set to Month Grid view by default for monthly dashboard
        self.calendar_heatmap._view_mode = "month_grid"
        # Hide view mode controls since we want our own toggle
        self.calendar_heatmap.set_show_controls(False)
        layout.addWidget(self.calendar_heatmap)
        
        return section
        
    def _create_statistics_section(self) -> QWidget:
        """Create the summary statistics section."""
        section = QFrame(self)
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Summary")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Statistics grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Create statistics cards
        self.stats_cards = {}
        stats_info = [
            ("average", "Average", "#FF8C42"),
            ("total", "Total", "#FFD166"),
            ("best_day", "Best Day", "#95C17B"),
            ("trend", "Trend", "#6C9BD1")
        ]
        
        for i, (key, label, color) in enumerate(stats_info):
            card = self._create_stat_card(label, "0", color)
            self.stats_cards[key] = card
            row, col = divmod(i, 2)
            stats_grid.addWidget(card, row, col)
            
        layout.addLayout(stats_grid)
        
        return section
        
    def _create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a summary statistic card."""
        card = QFrame(self)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFF8F0;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont('Inter', 12, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #8B7355;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont('Poppins', 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
        
    def _create_journal_section(self) -> QWidget:
        """Create the journal section placeholder."""
        section = QFrame(self)
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Reflection")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Placeholder content
        placeholder = QLabel("Journal feature coming soon...")
        placeholder.setStyleSheet("color: #A69583; font-style: italic;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)
        
        return section
        
    def _get_nav_button_style(self) -> str:
        """Get navigation button stylesheet."""
        return """
            QPushButton {
                background-color: #FFFFFF;
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
            QPushButton:pressed {
                background-color: #FFE8D1;
            }
        """
        
    def _get_combo_style(self) -> str:
        """Get combobox stylesheet."""
        return """
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 6px;
                padding: 8px 12px;
                color: #5D4E37;
                font-size: 12px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #FF8C42;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """
        
    def _setup_connections(self):
        """Set up signal connections."""
        # Navigation buttons
        self.prev_btn.clicked.connect(self._go_to_previous_month)
        self.next_btn.clicked.connect(self._go_to_next_month)
        self.today_btn.clicked.connect(self.reset_to_current_month)
        
        # Metric selection
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        
        # Calendar heatmap signals
        if hasattr(self.calendar_heatmap, 'date_clicked'):
            self.calendar_heatmap.date_clicked.connect(self._on_date_clicked)
        if hasattr(self.calendar_heatmap, 'date_range_selected'):
            self.calendar_heatmap.date_range_selected.connect(self._on_date_range_selected)
            
    def _update_month_label(self):
        """Update the month/year label."""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        month_name = month_names[self._current_month - 1]
        self.month_label.setText(f"{month_name} {self._current_year}")
        
    def _go_to_previous_month(self):
        """Navigate to the previous month."""
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
            
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _go_to_next_month(self):
        """Navigate to the next month."""
        # Get current date to prevent navigating to future
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # Calculate next month
        next_year = self._current_year
        next_month = self._current_month + 1
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        # Check if next month is in the future
        if next_year > current_year or (next_year == current_year and next_month > current_month):
            logger.warning(f"Cannot navigate to future month: {next_month}/{next_year}")
            return
            
        self._current_month = next_month
        self._current_year = next_year
            
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _on_metric_changed(self, text: str):
        """Handle metric selection change."""
        metric_map = {
            "Steps": "steps",
            "Heart Rate": "heart_rate", 
            "Sleep Hours": "sleep_hours",
            "Distance": "distance"
        }
        
        if text in metric_map:
            self._current_metric = metric_map[text]
            self._load_month_data()
            self.metric_changed.emit(self._current_metric)
            
    def _load_month_data(self):
        """Load data for the current month and metric."""
        data = {}
        
        if self.monthly_calculator:
            # Use real data from the calculator
            try:
                # Map display metric names to HK types
                metric_mapping = {
                    "steps": "HKQuantityTypeIdentifierStepCount",
                    "heart_rate": "HKQuantityTypeIdentifierHeartRate",
                    "sleep_hours": "HKCategoryTypeIdentifierSleepAnalysis",
                    "distance": "HKQuantityTypeIdentifierDistanceWalkingRunning"
                }
                
                hk_type = metric_mapping.get(self._current_metric)
                if hk_type:
                    # Get data for the entire month
                    days_in_month = monthrange(self._current_year, self._current_month)[1]
                    
                    for day in range(1, days_in_month + 1):
                        current_date = date(self._current_year, self._current_month, day)
                        
                        # Get daily aggregate value
                        daily_value = self.monthly_calculator.get_daily_aggregate(
                            metric=hk_type,
                            date=current_date
                        )
                        
                        if daily_value is not None and daily_value > 0:
                            # Convert values for display
                            if self._current_metric == "distance" and daily_value:
                                daily_value = daily_value / 1000  # Convert meters to km
                            elif self._current_metric == "sleep_hours" and daily_value:
                                daily_value = daily_value / 3600  # Convert seconds to hours
                                
                            data[current_date] = daily_value
                            
            except Exception as e:
                logger.error(f"Error loading month data: {e}")
                # Fall back to sample data
                data = self._generate_sample_data()
        else:
            # Use sample data if no calculator available
            data = self._generate_sample_data()
        
        # Update calendar heatmap
        self.calendar_heatmap.set_metric_data(self._current_metric, data)
        self.calendar_heatmap.set_current_date(date(self._current_year, self._current_month, 1))
        
        # Update summary statistics
        self._update_summary_stats(data)
        
    def _generate_sample_data(self) -> Dict[date, float]:
        """Generate sample data for demonstration."""
        # This is placeholder data - in production would come from monthly_calculator
        import random
        
        sample_data = {}
        days_in_month = monthrange(self._current_year, self._current_month)[1]
        
        for day in range(1, days_in_month + 1):
            current_date = date(self._current_year, self._current_month, day)
            
            # Generate realistic sample values based on metric type
            if self._current_metric == "steps":
                value = random.randint(2000, 15000)
            elif self._current_metric == "heart_rate":
                value = random.randint(60, 100)
            elif self._current_metric == "sleep_hours":
                value = random.uniform(5.0, 9.0)
            else:  # distance
                value = random.uniform(1.0, 10.0)
                
            sample_data[current_date] = value
            
        return sample_data
        
    def _update_summary_stats(self, data: Dict[date, float]):
        """Update the summary statistics cards."""
        if not data:
            return
            
        values = list(data.values())
        
        # Calculate statistics
        average = sum(values) / len(values)
        total = sum(values)
        best_day = max(data, key=data.get)
        best_value = data[best_day]
        
        # Determine trend (simplified)
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point) if len(values) > mid_point else 0
        trend = "↑" if second_half_avg > first_half_avg else "↓"
        
        # Format values based on metric type
        if self._current_metric == "steps":
            avg_text = f"{int(average):,}"
            total_text = f"{int(total):,}"
            best_text = f"{int(best_value):,}"
        elif self._current_metric == "heart_rate":
            avg_text = f"{int(average)} bpm"
            total_text = f"{int(average)} avg"  # Average makes more sense for heart rate
            best_text = f"{int(best_value)} bpm"
        elif self._current_metric == "sleep_hours":
            avg_text = f"{average:.1f} hrs"
            total_text = f"{total:.1f} hrs"
            best_text = f"{best_value:.1f} hrs"
        else:  # distance
            avg_text = f"{average:.1f} km"
            total_text = f"{total:.1f} km"
            best_text = f"{best_value:.1f} km"
            
        # Update cards
        self.stats_cards["average"].value_label.setText(avg_text)
        self.stats_cards["total"].value_label.setText(total_text)
        self.stats_cards["best_day"].value_label.setText(f"{best_text}")
        self.stats_cards["trend"].value_label.setText(f"{trend} Trending")
        
    def _on_date_clicked(self, clicked_date: date):
        """Handle date click in calendar heatmap."""
        # TODO: Show detailed daily view
        print(f"Date clicked: {clicked_date}")
        
    def _on_date_range_selected(self, start_date: date, end_date: date):
        """Handle date range selection in calendar heatmap."""
        # TODO: Show range statistics
        print(f"Date range selected: {start_date} to {end_date}")
        
    def set_data_source(self, monthly_calculator):
        """Set the monthly metrics calculator data source."""
        self.monthly_calculator = monthly_calculator
        self._load_month_data()
        
    def get_current_month(self) -> tuple[int, int]:
        """Get the current year and month being displayed."""
        return self._current_year, self._current_month
    
    def reset_to_current_month(self):
        """Reset the view to the current month."""
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Resetting to current month: {self._current_month}/{self._current_year}")
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _set_calendar_style(self, style: str):
        """Set the calendar heatmap style."""
        if style == "classic":
            self.calendar_heatmap._view_mode = "month_grid"
            self.classic_btn.setChecked(True)
            self.github_btn.setChecked(False)
        elif style == "github":
            self.calendar_heatmap._view_mode = "github_style"
            self.classic_btn.setChecked(False)
            self.github_btn.setChecked(True)
        
        # Force redraw
        self.calendar_heatmap.update()
        
    def showEvent(self, event):
        """Handle widget show event to ensure UI is refreshed."""
        super().showEvent(event)
        
        # Check if we're showing a future month and reset if needed
        now = datetime.now()
        if self._current_year > now.year or (self._current_year == now.year and self._current_month > now.month):
            logger.warning(f"Widget showing future month {self._current_month}/{self._current_year}, resetting to current")
            self.reset_to_current_month()
        else:
            # Force a refresh when the widget is shown
            self._load_month_data()
            self._update_month_label()