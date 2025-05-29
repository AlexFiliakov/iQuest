"""
Modern monthly dashboard widget with improved UI design.

This widget provides a modern, Wall Street Journal-inspired monthly view of health metrics
with tighter layout, better visual hierarchy, and modern design patterns.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from calendar import monthrange

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPen

from .charts.calendar_heatmap import CalendarHeatmapComponent
from .statistics_widget import StatisticsWidget
from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from ..utils.logging_config import get_logger
from .style_manager import StyleManager

logger = get_logger(__name__)


class ModernMonthlyDashboardWidget(QWidget):
    """
    Modern monthly dashboard widget with improved UI design.
    
    Features:
    - Modern, clean visual design with better use of space
    - Smooth animations and transitions
    - Improved visual hierarchy
    - Wall Street Journal-inspired typography
    - Tighter layout without excessive borders
    """
    
    # Signals
    month_changed = pyqtSignal(int, int)  # year, month
    metric_changed = pyqtSignal(str)
    
    def __init__(self, monthly_calculator=None, parent=None):
        """Initialize the monthly dashboard widget."""
        super().__init__(parent)
        
        self.monthly_calculator = monthly_calculator
        self.style_manager = StyleManager()
        
        # Always initialize to current date
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Initializing ModernMonthlyDashboardWidget with date: {self._current_month}/{self._current_year}")
        
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
        """Set up the modern user interface."""
        # Main layout - Tighter margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(16)
        
        # Apply background color
        self.setStyleSheet(f"background-color: {self.style_manager.SECONDARY_BG};")
        
        # Header section
        header = self._create_modern_header()
        main_layout.addWidget(header)
        
        # Content area - No scroll area for cleaner look
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        
        # Main content grid for better space utilization
        content_grid = QGridLayout()
        content_grid.setSpacing(16)
        
        # Calendar heatmap section (spans 2 columns)
        heatmap_section = self._create_modern_heatmap_section()
        content_grid.addWidget(heatmap_section, 0, 0, 1, 2)
        
        # Summary statistics section
        stats_section = self._create_modern_statistics_section()
        content_grid.addWidget(stats_section, 1, 0, 1, 2)
        
        content_layout.addLayout(content_grid)
        content_layout.addStretch()
        
        main_layout.addLayout(content_layout)
        
    def _create_modern_header(self) -> QWidget:
        """Create the modern dashboard header."""
        header = QWidget(self)
        header.setMaximumHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)
        
        # Month navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        # Previous month button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setStyleSheet(self._get_modern_nav_button_style())
        self.prev_btn.setToolTip("Previous month")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(self.prev_btn)
        
        # Current month/year label
        self.month_label = QLabel(self)
        self.month_label.setFont(QFont('Inter', 22, QFont.Weight.Bold))
        self.month_label.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY}; padding: 0 12px;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setFixedWidth(200)
        nav_layout.addWidget(self.month_label)
        
        # Next month button
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setStyleSheet(self._get_modern_nav_button_style())
        self.next_btn.setToolTip("Next month")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(self.next_btn)
        
        # Today button
        self.today_btn = QPushButton("Today")
        self.today_btn.setFixedSize(64, 36)
        self.today_btn.setStyleSheet(self._get_modern_today_button_style())
        self.today_btn.setToolTip("Go to current month")
        self.today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(self.today_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # Metric selector with modern styling
        metric_layout = QHBoxLayout()
        metric_layout.setSpacing(8)
        
        metric_label = QLabel("Metric:", self)
        metric_label.setFont(QFont('Inter', 13, QFont.Weight.Medium))
        metric_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        metric_layout.addWidget(metric_label)
        
        self.metric_combo = QComboBox(self)
        self.metric_combo.addItems([
            "Steps", "Heart Rate", "Sleep Hours", "Distance"
        ])
        self.metric_combo.setStyleSheet(self._get_modern_combo_style())
        self.metric_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        metric_layout.addWidget(self.metric_combo)
        
        layout.addLayout(metric_layout)
        
        # Update month label
        self._update_month_label()
        
        return header
        
    def _create_modern_heatmap_section(self) -> QWidget:
        """Create the modern calendar heatmap section."""
        section = QFrame(self)
        section.setObjectName("modernSection")
        
        # Apply modern card styling with shadow effect
        section.setStyleSheet(f"""
            QFrame#modernSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        section.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Calendar heatmap
        self.calendar_heatmap = CalendarHeatmapComponent()
        self.calendar_heatmap.setMinimumHeight(320)
        # Set to Month Grid view by default for monthly dashboard
        self.calendar_heatmap._view_mode = "month_grid"
        # Hide view mode controls since we want Month Grid only
        self.calendar_heatmap.set_show_controls(False)
        layout.addWidget(self.calendar_heatmap)
        
        return section
        
    def _create_modern_statistics_section(self) -> QWidget:
        """Create the modern summary statistics section."""
        section = QWidget(self)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Section title with modern typography
        title = QLabel("Monthly Summary")
        title.setFont(QFont('Inter', 14, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY}; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # Statistics grid - 2x2 layout
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        
        # Create modern statistics cards
        self.stats_cards = {}
        stats_info = [
            ("average", "Average", self.style_manager.DATA_ORANGE),
            ("total", "Total", self.style_manager.DATA_PURPLE),
            ("best_day", "Best Day", self.style_manager.ACCENT_SUCCESS),
            ("trend", "Trend", self.style_manager.ACCENT_SECONDARY)
        ]
        
        for i, (key, label, color) in enumerate(stats_info):
            card = self._create_modern_stat_card(label, "0", color)
            self.stats_cards[key] = card
            row, col = divmod(i, 2)
            stats_grid.addWidget(card, row, col)
            
        layout.addLayout(stats_grid)
        
        return section
        
    def _create_modern_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a modern summary statistic card."""
        card = QFrame(self)
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 10px;
                padding: 16px;
                border-left: 3px solid {color};
            }}
            QFrame#statCard:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
            }}
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont('Inter', 11, QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        layout.addWidget(title_label)
        
        # Value with larger font
        value_label = QLabel(value)
        value_label.setFont(QFont('Inter', 22, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
        
    def _get_modern_nav_button_style(self) -> str:
        """Get modern navigation button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: none;
                border-radius: 18px;
                color: {self.style_manager.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.ACCENT_LIGHT};
            }}
        """
        
    def _get_modern_today_button_style(self) -> str:
        """Get modern today button stylesheet."""
        return f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border: none;
                border-radius: 18px;
                color: {self.style_manager.TEXT_INVERSE};
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
            QPushButton:pressed {{
                background-color: #1E40AF;
            }}
        """
        
    def _get_modern_combo_style(self) -> str:
        """Get modern combobox stylesheet."""
        return f"""
            QComboBox {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 8px 12px;
                color: {self.style_manager.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 500;
                min-width: 140px;
            }}
            QComboBox:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QComboBox:focus {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.style_manager.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QComboBox:hover::down-arrow {{
                border-top-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 4px;
                selection-background-color: {self.style_manager.TERTIARY_BG};
                selection-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                min-height: 28px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
            }}
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
        
    def reset_to_current_month(self):
        """Reset the view to the current month."""
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Resetting to current month: {self._current_month}/{self._current_year}")
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
        """Update the summary statistics cards with animations."""
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
        trend_text = "Trending Up" if second_half_avg > first_half_avg else "Trending Down"
        
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
            
        # Update cards with animation effect
        self.stats_cards["average"].value_label.setText(avg_text)
        self.stats_cards["total"].value_label.setText(total_text)
        self.stats_cards["best_day"].value_label.setText(f"{best_text}")
        self.stats_cards["trend"].value_label.setText(f"{trend} {trend_text}")
        
        # Add subtle fade animation
        for card in self.stats_cards.values():
            self._animate_card_update(card)
            
    def _animate_card_update(self, card: QWidget):
        """Animate card update with fade effect."""
        # Create opacity animation
        self.fade_animation = QPropertyAnimation(card, b"windowOpacity")
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(0.7)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.start()
        
    def _on_date_clicked(self, clicked_date: date):
        """Handle date click in calendar heatmap."""
        # TODO: Show detailed daily view
        logger.info(f"Date clicked: {clicked_date}")
        
    def _on_date_range_selected(self, start_date: date, end_date: date):
        """Handle date range selection in calendar heatmap."""
        # TODO: Show range statistics
        logger.info(f"Date range selected: {start_date} to {end_date}")
        
    def set_data_source(self, monthly_calculator):
        """Set the monthly metrics calculator data source."""
        self.monthly_calculator = monthly_calculator
        self._load_month_data()
        
    def get_current_month(self) -> tuple[int, int]:
        """Get the current year and month being displayed."""
        return self._current_year, self._current_month
    
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
            self.update()
        
        # Import QApplication for event processing
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Schedule another update after a short delay to ensure complete rendering
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_refresh)
    
    def _delayed_refresh(self):
        """Delayed refresh to ensure complete rendering."""
        self.calendar_heatmap.update()
        self.update()