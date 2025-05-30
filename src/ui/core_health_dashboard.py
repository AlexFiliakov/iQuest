"""Core Health Metrics Dashboard following WSJ analytics design principles."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QScrollArea, QFrame,
    QButtonGroup, QSizePolicy, QTabWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from .style_manager import StyleManager
from .summary_cards import SummaryCard
from .adaptive_time_range_selector import AdaptiveTimeRangeSelector
from .metric_comparison_view import MetricComparisonView
from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MetricObserverManager:
    """Manages observers for metric updates following observer pattern."""
    
    def __init__(self):
        self._observers: Dict[str, List[callable]] = {}
        
    def subscribe(self, metric_type: str, callback: callable):
        """Subscribe to updates for a specific metric type."""
        if metric_type not in self._observers:
            self._observers[metric_type] = []
        self._observers[metric_type].append(callback)
        
    def unsubscribe(self, metric_type: str, callback: callable):
        """Unsubscribe from updates for a specific metric type."""
        if metric_type in self._observers:
            self._observers[metric_type].remove(callback)
            
    def notify(self, metric_type: str, data: Dict[str, Any]):
        """Notify all observers of a metric update."""
        if metric_type in self._observers:
            for callback in self._observers[metric_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error notifying observer: {e}")


class MetricPanelComponent(QWidget):
    """Base component for metric panels following WSJ design principles."""
    
    data_updated = pyqtSignal(str, dict)  # metric_type, data
    
    def __init__(self, metric_type: str, title: str, style_manager: StyleManager, parent=None):
        super().__init__(parent)
        self.metric_type = metric_type
        self.title = title
        self.style_manager = style_manager
        self._data = {}
        self._loading = False
        
        self.setup_ui()
        self.apply_wsj_styling()
        
    def setup_ui(self):
        """Set up the basic UI structure."""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("panel-title")
        self.layout.addWidget(self.title_label)
        
        # Content area (to be implemented by subclasses)
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content_widget)
        
    def apply_wsj_styling(self):
        """Apply WSJ design principles to component."""
        self.setStyleSheet(f"""
            MetricPanelComponent {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid {self.style_manager.TEXT_MUTED};
                border-radius: 8px;
            }}
            
            #panel-title {{
                font-size: 20px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding-bottom: 8px;
            }}
        """)
        
    @pyqtSlot(dict)
    def update_data(self, data: Dict[str, Any]):
        """Update component with new data, smooth transitions."""
        self._data = data
        self._loading = False
        self.refresh_content()
        self.data_updated.emit(self.metric_type, data)
        
    def refresh_content(self):
        """Refresh content display - to be implemented by subclasses."""
        pass
        
    def set_loading(self, loading: bool):
        """Set loading state."""
        self._loading = loading
        # Could show loading indicator here


class ActivityMetricPanel(MetricPanelComponent):
    """Activity metrics panel showing steps, distance, calories."""
    
    def __init__(self, style_manager: StyleManager, parent=None):
        super().__init__("activity", "Activity", style_manager, parent)
        self.setup_activity_content()
        
    def setup_activity_content(self):
        """Set up activity-specific content."""
        # Create summary cards for key metrics
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        
        self.steps_card = SummaryCard(
            title="Steps",
            value="0",
            unit="steps",
            parent=self
        )
        self.distance_card = SummaryCard(
            title="Distance", 
            value="0.0",
            unit="km",
            parent=self
        )
        self.calories_card = SummaryCard(
            title="Active Energy",
            value="0",
            unit="kcal",
            parent=self
        )
        self.floors_card = SummaryCard(
            title="Floors Climbed",
            value="0",
            unit="floors",
            parent=self
        )
        
        self.cards_layout.addWidget(self.steps_card)
        self.cards_layout.addWidget(self.distance_card)
        self.cards_layout.addWidget(self.calories_card)
        self.cards_layout.addWidget(self.floors_card)
        
        self.content_layout.addLayout(self.cards_layout)
        
        # Add trend indicator
        self.trend_label = QLabel("No data available")
        self.trend_label.setObjectName("trend-label")
        self.content_layout.addWidget(self.trend_label)
        
    def refresh_content(self):
        """Update activity metrics display."""
        if not self._data:
            return
            
        # Update cards
        if 'steps' in self._data:
            self.steps_card.set_value(f"{self._data['steps']:,}")
            
        if 'distance' in self._data:
            distance_km = self._data['distance'] / 1000
            self.distance_card.set_value(f"{distance_km:.1f}")
            
        if 'active_energy' in self._data:
            self.calories_card.set_value(f"{self._data['active_energy']:,}")
            
        if 'floors_climbed' in self._data:
            self.floors_card.set_value(f"{self._data['floors_climbed']:,}")
            
        # Update trend
        if 'trend' in self._data:
            self.trend_label.setText(self._data['trend'])


class HeartRatePanel(MetricPanelComponent):
    """Heart rate analysis panel with zones and trends."""
    
    def __init__(self, style_manager: StyleManager, parent=None):
        super().__init__("heart_rate", "Heart Rate", style_manager, parent)
        self.setup_heart_content()
        
    def setup_heart_content(self):
        """Set up heart rate specific content."""
        # Create cards for heart rate metrics
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        
        self.resting_hr_card = SummaryCard(
            title="Resting HR",
            value="--",
            unit="bpm",
            parent=self
        )
        self.avg_hr_card = SummaryCard(
            title="Average HR",
            value="--",
            unit="bpm",
            parent=self
        )
        self.max_hr_card = SummaryCard(
            title="Max HR",
            value="--",
            unit="bpm",
            parent=self
        )
        self.hrv_card = SummaryCard(
            title="HRV",
            value="--",
            unit="ms",
            parent=self
        )
        
        self.cards_layout.addWidget(self.resting_hr_card)
        self.cards_layout.addWidget(self.avg_hr_card)
        self.cards_layout.addWidget(self.max_hr_card)
        self.cards_layout.addWidget(self.hrv_card)
        
        self.content_layout.addLayout(self.cards_layout)
        
        # HR Zones visualization placeholder
        self.zones_widget = QWidget(self)
        self.zones_widget.setMinimumHeight(100)
        self.zones_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        self.content_layout.addWidget(self.zones_widget)
        
    def refresh_content(self):
        """Update heart rate display."""
        if not self._data:
            return
            
        if 'resting_hr' in self._data:
            self.resting_hr_card.set_value(str(self._data['resting_hr']))
            
        if 'avg_hr' in self._data:
            self.avg_hr_card.set_value(str(self._data['avg_hr']))
            
        if 'max_hr' in self._data:
            self.max_hr_card.set_value(str(self._data['max_hr']))
            
        if 'hrv' in self._data:
            self.hrv_card.set_value(f"{self._data['hrv']:.1f}")


class SleepPanel(MetricPanelComponent):
    """Sleep analytics panel with duration, efficiency, and phases."""
    
    def __init__(self, style_manager: StyleManager, parent=None):
        super().__init__("sleep", "Sleep", style_manager, parent)
        self.setup_sleep_content()
        
    def setup_sleep_content(self):
        """Set up sleep specific content."""
        # Create cards for sleep metrics
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        
        self.duration_card = SummaryCard(
            title="Duration",
            value="0h 0m",
            unit="",
            parent=self
        )
        self.quality_card = SummaryCard(
            title="Quality Score",
            value="--",
            unit="/100",
            parent=self
        )
        self.deep_sleep_card = SummaryCard(
            title="Deep Sleep",
            value="0h 0m",
            unit="",
            parent=self
        )
        self.efficiency_card = SummaryCard(
            title="Efficiency",
            value="0%",
            unit="",
            parent=self
        )
        
        self.cards_layout.addWidget(self.duration_card)
        self.cards_layout.addWidget(self.quality_card)
        self.cards_layout.addWidget(self.deep_sleep_card)
        self.cards_layout.addWidget(self.efficiency_card)
        
        self.content_layout.addLayout(self.cards_layout)
        
    def refresh_content(self):
        """Update sleep display."""
        if not self._data:
            return
            
        if 'duration_hours' in self._data:
            hours = int(self._data['duration_hours'])
            minutes = int((self._data['duration_hours'] - hours) * 60)
            self.duration_card.set_value(f"{hours}h {minutes}m")
            
        if 'quality_score' in self._data:
            self.quality_card.set_value(f"{self._data['quality_score']:.0f}")
            
        if 'efficiency' in self._data:
            self.efficiency_card.set_value(f"{self._data['efficiency']:.0%}")
            
        if 'deep_sleep_hours' in self._data:
            hours = int(self._data['deep_sleep_hours'])
            minutes = int((self._data['deep_sleep_hours'] - hours) * 60)
            self.deep_sleep_card.set_value(f"{hours}h {minutes}m")


class BodyMetricsPanel(MetricPanelComponent):
    """Body measurements panel with weight, BMI, and trends."""
    
    def __init__(self, style_manager: StyleManager, parent=None):
        super().__init__("body", "Body Measurements", style_manager, parent)
        self.setup_body_content()
        
    def setup_body_content(self):
        """Set up body metrics specific content."""
        # Create cards for body metrics
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        
        self.weight_card = SummaryCard(
            title="Weight",
            value="--",
            unit="kg",
            parent=self
        )
        self.bmi_card = SummaryCard(
            title="BMI",
            value="--",
            unit="",
            parent=self
        )
        self.body_fat_card = SummaryCard(
            title="Body Fat",
            value="--",
            unit="%",
            parent=self
        )
        
        self.cards_layout.addWidget(self.weight_card)
        self.cards_layout.addWidget(self.bmi_card)
        self.cards_layout.addWidget(self.body_fat_card)
        
        self.content_layout.addLayout(self.cards_layout)
        
    def refresh_content(self):
        """Update body metrics display."""
        if not self._data:
            return
            
        if 'weight' in self._data:
            self.weight_card.set_value(f"{self._data['weight']:.1f}")
            
        if 'bmi' in self._data:
            self.bmi_card.set_value(f"{self._data['bmi']:.1f}")
            
        if 'body_fat_percentage' in self._data:
            self.body_fat_card.set_value(f"{self._data['body_fat_percentage']:.1f}")


class CoreHealthDashboard(QWidget):
    """Main dashboard following WSJ analytics design principles."""
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.style_manager = StyleManager()
        self.observer_manager = MetricObserverManager()
        self.metric_panels = {}
        
        # Initialize calculators
        self.daily_calculator = DailyMetricsCalculator(data_manager)
        self.weekly_calculator = WeeklyMetricsCalculator(data_manager)
        self.monthly_calculator = MonthlyMetricsCalculator(data_manager)
        
        # Current time range
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=30)
        self.time_range = "30D"
        
        self.setup_ui()
        self.setup_wsj_layout()
        self.apply_warm_color_scheme()
        self.connect_signals()
        
        # Initial data load
        QTimer.singleShot(100, self.refresh_data)
        
        # Setup accessibility
        self.setup_accessibility()
        
    def setup_ui(self):
        """Create the main UI structure."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(24)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header with title and time range selector
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(16)
        
        # Dashboard title
        self.title_label = QLabel("Health Metrics Dashboard")
        self.title_label.setObjectName("dashboard-title")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        
        # Time range selector
        self.time_range_selector = AdaptiveTimeRangeSelector(parent=self)
        
        # Export button
        self.export_btn = QPushButton("Export Dashboard")
        self.export_btn.setObjectName("export-button")
        self.export_btn.clicked.connect(self.export_dashboard)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.export_btn)
        self.header_layout.addWidget(self.time_range_selector)
        
        self.main_layout.addLayout(self.header_layout)
        
        # Tab widget for overview and comparison
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        
        # Overview tab with metric panels
        self.overview_widget = QWidget(self)
        self.overview_layout = QVBoxLayout(self.overview_widget)
        self.overview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable content area for overview
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget(self)
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.content_widget)
        self.overview_layout.addWidget(self.scroll_area)
        
        # Comparison tab
        self.comparison_view = MetricComparisonView(self.data_manager, self.style_manager, self)
        
        # Add tabs
        self.tab_widget.addTab(self.overview_widget, "Overview")
        self.tab_widget.addTab(self.comparison_view, "Compare Metrics")
        
        self.main_layout.addWidget(self.tab_widget)
        
    def setup_wsj_layout(self):
        """Create clean, organized layout following WSJ principles."""
        # Create metric panels
        self.activity_panel = ActivityMetricPanel(self.style_manager, self)
        self.heart_panel = HeartRatePanel(self.style_manager, self)
        self.sleep_panel = SleepPanel(self.style_manager, self)
        self.body_panel = BodyMetricsPanel(self.style_manager, self)
        
        # Store references
        self.metric_panels = {
            'activity': self.activity_panel,
            'heart_rate': self.heart_panel,
            'sleep': self.sleep_panel,
            'body': self.body_panel
        }
        
        # Add to grid layout (2x2)
        self.content_layout.addWidget(self.activity_panel, 0, 0)
        self.content_layout.addWidget(self.heart_panel, 0, 1)
        self.content_layout.addWidget(self.sleep_panel, 1, 0)
        self.content_layout.addWidget(self.body_panel, 1, 1)
        
        # Set equal stretch factors
        for i in range(2):
            self.content_layout.setRowStretch(i, 1)
            self.content_layout.setColumnStretch(i, 1)
            
        # Make panels responsive
        for panel in self.metric_panels.values():
            panel.setMinimumSize(300, 250)
            panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
    def apply_warm_color_scheme(self):
        """Apply consistent warm color palette."""
        self.setStyleSheet(f"""
            CoreHealthDashboard {{
                background-color: {self.style_manager.PRIMARY_BG};
            }}
            
            #dashboard-title {{
                color: {self.style_manager.TEXT_PRIMARY};
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
            }}
            
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            #trend-label {{
                color: {self.style_manager.TEXT_SECONDARY};
                font-size: 14px;
                padding: 8px 0;
            }}
            
            #export-button {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                color: {self.style_manager.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            #export-button:hover {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                color: {self.style_manager.TEXT_INVERSE};
            }}
            
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            
            QTabBar::tab {{
                background-color: {self.style_manager.TERTIARY_BG};
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.style_manager.SECONDARY_BG};
                font-weight: 600;
            }}
        """)
        
    def connect_signals(self):
        """Connect signals and slots."""
        # Time range selector
        self.time_range_selector.time_range_changed.connect(self.on_time_range_changed)
        
        # Subscribe to metric updates
        for metric_type, panel in self.metric_panels.items():
            self.observer_manager.subscribe(metric_type, panel.update_data)
            
    @pyqtSlot(str, object, object)
    def on_time_range_changed(self, range_str: str, start_date, end_date):
        """Handle time range changes."""
        self.time_range = range_str
        self.start_date = start_date
        self.end_date = end_date
        self.refresh_data()
        
    def refresh_data(self):
        """Refresh all metric data based on current time range."""
        try:
            # Set loading state
            for panel in self.metric_panels.values():
                if hasattr(panel, 'set_loading'):
                    panel.set_loading(True)
                
            # Calculate metrics based on time range
            days_diff = (self.end_date - self.start_date).days
            
            if days_diff <= 1:
                # Use daily calculator
                metrics = self.daily_calculator.calculate_metrics(
                    self.start_date, self.end_date
                )
            elif days_diff <= 7:
                # Use weekly calculator
                metrics = self.weekly_calculator.calculate_metrics(
                    self.start_date, self.end_date
                )
            else:
                # Use monthly calculator
                metrics = self.monthly_calculator.calculate_metrics(
                    self.start_date, self.end_date
                )
                
            # Update panels with data
            self._update_activity_data(metrics)
            self._update_heart_data(metrics)
            self._update_sleep_data(metrics)
            self._update_body_data(metrics)
            
        except Exception as e:
            logger.error(f"Error refreshing dashboard data: {e}")
            
    def _update_activity_data(self, metrics: Dict[str, Any]):
        """Update activity panel with calculated metrics."""
        activity_data = {
            'steps': metrics.get('total_steps', 0),
            'distance': metrics.get('total_distance', 0),
            'active_energy': metrics.get('total_active_energy', 0),
            'floors_climbed': metrics.get('total_floors_climbed', 0),
            'trend': self._calculate_trend_text('steps', metrics)
        }
        self.observer_manager.notify('activity', activity_data)
        
    def _update_heart_data(self, metrics: Dict[str, Any]):
        """Update heart rate panel with calculated metrics."""
        heart_data = {
            'resting_hr': metrics.get('avg_resting_heart_rate', 0),
            'avg_hr': metrics.get('avg_heart_rate', 0),
            'max_hr': metrics.get('max_heart_rate', 0),
            'hrv': metrics.get('avg_hrv', 0)
        }
        self.observer_manager.notify('heart_rate', heart_data)
        
    def _update_sleep_data(self, metrics: Dict[str, Any]):
        """Update sleep panel with calculated metrics."""
        # Calculate sleep quality score based on multiple factors
        duration_hours = metrics.get('avg_sleep_duration', 0)
        efficiency = metrics.get('sleep_efficiency', 0)
        deep_sleep_ratio = metrics.get('deep_sleep_ratio', 0)
        
        # Quality score algorithm (0-100)
        # 40% weight on duration (optimal 7-9 hours)
        # 30% weight on efficiency
        # 30% weight on deep sleep ratio
        duration_score = min(100, max(0, (duration_hours / 8) * 100)) if duration_hours < 8 else max(0, 100 - ((duration_hours - 8) * 20))
        efficiency_score = efficiency * 100
        deep_sleep_score = min(100, (deep_sleep_ratio / 0.2) * 100)  # 20% deep sleep is optimal
        
        quality_score = (duration_score * 0.4) + (efficiency_score * 0.3) + (deep_sleep_score * 0.3)
        
        sleep_data = {
            'duration_hours': duration_hours,
            'efficiency': efficiency,
            'deep_sleep_hours': metrics.get('avg_deep_sleep', 0),
            'quality_score': quality_score
        }
        self.observer_manager.notify('sleep', sleep_data)
        
    def _update_body_data(self, metrics: Dict[str, Any]):
        """Update body metrics panel with calculated metrics."""
        body_data = {
            'weight': metrics.get('current_weight', 0),
            'bmi': metrics.get('current_bmi', 0),
            'body_fat_percentage': metrics.get('current_body_fat', 0)
        }
        self.observer_manager.notify('body', body_data)
        
    def _calculate_trend_text(self, metric_type: str, metrics: Dict[str, Any]) -> str:
        """Calculate trend text for a metric."""
        # This is a simplified version - could be expanded
        trend_value = metrics.get(f'{metric_type}_trend', 0)
        if trend_value > 0:
            return f"↑ {abs(trend_value):.1f}% from previous period"
        elif trend_value < 0:
            return f"↓ {abs(trend_value):.1f}% from previous period"
        else:
            return "No change from previous period"
            
    def setup_accessibility(self):
        """Set up accessibility features."""
        # Main widget
        self.setAccessibleName("Health Metrics Dashboard")
        self.setAccessibleDescription("Dashboard showing health metrics overview and comparisons")
        
        # Tab widget
        self.tab_widget.setAccessibleName("Dashboard Views")
        self.tab_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Time range selector
        self.time_range_selector.setAccessibleName("Time Range Selector")
        self.time_range_selector.setAccessibleDescription("Select time period for metrics display")
        
        # Metric panels
        for metric_type, panel in self.metric_panels.items():
            panel.setAccessibleName(f"{metric_type.replace('_', ' ').title()} Panel")
            panel.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
        # Enable keyboard navigation
        self.setup_keyboard_shortcuts()
        
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for navigation."""
        # Tab navigation is built-in
        # Add custom shortcuts as needed
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def keyPressEvent(self, event):
        """Handle keyboard events for accessibility."""
        if event.key() == Qt.Key.Key_F5:
            # Refresh data
            self.refresh_data()
        elif event.key() == Qt.Key.Key_Tab:
            # Let Qt handle tab navigation
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def resizeEvent(self, event):
        """Handle resize events for responsive layout."""
        super().resizeEvent(event)
        
        # Adjust layout based on window size
        width = self.width()
        
        if width < 800:
            # Switch to single column layout on small screens
            if self.content_layout.columnCount() > 1:
                # Reorganize panels in single column
                for i, panel in enumerate(self.metric_panels.values()):
                    self.content_layout.addWidget(panel, i, 0)
                    
                # Update stretch factors
                for i in range(4):
                    self.content_layout.setRowStretch(i, 1)
                self.content_layout.setColumnStretch(0, 1)
                self.content_layout.setColumnStretch(1, 0)
        else:
            # Use 2x2 grid on larger screens
            if self.content_layout.itemAtPosition(2, 0) is not None:
                # Reorganize back to 2x2
                panels = list(self.metric_panels.values())
                self.content_layout.addWidget(panels[0], 0, 0)
                self.content_layout.addWidget(panels[1], 0, 1)
                self.content_layout.addWidget(panels[2], 1, 0)
                self.content_layout.addWidget(panels[3], 1, 1)
                
                # Reset stretch factors
                for i in range(2):
                    self.content_layout.setRowStretch(i, 1)
                    self.content_layout.setColumnStretch(i, 1)
                    
    @pyqtSlot()
    def export_dashboard(self):
        """Export dashboard data to CSV file."""
        try:
            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Dashboard Data",
                f"health_metrics_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
                
            # Collect current dashboard data
            export_data = {
                'time_range': f"{self.start_date} to {self.end_date}",
                'exported_at': datetime.now().isoformat()
            }
            
            # Get data from each panel
            for metric_type, panel in self.metric_panels.items():
                if hasattr(panel, '_data') and panel._data:
                    export_data[metric_type] = panel._data
                    
            # Write to CSV
            import csv
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow(['Health Metrics Dashboard Export'])
                writer.writerow(['Time Range:', export_data['time_range']])
                writer.writerow(['Exported:', export_data['exported_at']])
                writer.writerow([])
                
                # Activity data
                if 'activity' in export_data:
                    writer.writerow(['Activity Metrics'])
                    activity = export_data['activity']
                    writer.writerow(['Steps:', activity.get('steps', 'N/A')])
                    writer.writerow(['Distance (km):', f"{activity.get('distance', 0)/1000:.1f}"])
                    writer.writerow(['Active Energy (kcal):', activity.get('active_energy', 'N/A')])
                    writer.writerow([])
                    
                # Heart rate data
                if 'heart_rate' in export_data:
                    writer.writerow(['Heart Rate Metrics'])
                    hr = export_data['heart_rate']
                    writer.writerow(['Resting HR:', hr.get('resting_hr', 'N/A')])
                    writer.writerow(['Average HR:', hr.get('avg_hr', 'N/A')])
                    writer.writerow(['Max HR:', hr.get('max_hr', 'N/A')])
                    writer.writerow([])
                    
                # Sleep data
                if 'sleep' in export_data:
                    writer.writerow(['Sleep Metrics'])
                    sleep = export_data['sleep']
                    writer.writerow(['Duration (hours):', f"{sleep.get('duration_hours', 0):.1f}"])
                    writer.writerow(['Efficiency:', f"{sleep.get('efficiency', 0):.0%}"])
                    writer.writerow(['Deep Sleep (hours):', f"{sleep.get('deep_sleep_hours', 0):.1f}"])
                    writer.writerow([])
                    
                # Body metrics
                if 'body' in export_data:
                    writer.writerow(['Body Measurements'])
                    body = export_data['body']
                    writer.writerow(['Weight (kg):', f"{body.get('weight', 0):.1f}"])
                    writer.writerow(['BMI:', f"{body.get('bmi', 0):.1f}"])
                    writer.writerow(['Body Fat %:', f"{body.get('body_fat_percentage', 0):.1f}"])
                    
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Dashboard data exported to:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Error exporting dashboard: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export dashboard data:\n{str(e)}"
            )