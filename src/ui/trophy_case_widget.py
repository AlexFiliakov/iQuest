"""
Trophy Case Dashboard Widget for Personal Records Tracker.
Displays achievements, records, and statistics in an attractive UI.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QLabel, QFrame, QScrollArea, QGridLayout,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QGroupBox, QProgressBar, QSplitter,
                            QTextEdit, QComboBox, QCheckBox, QSpacerItem,
                            QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QBrush

from ..analytics.personal_records_tracker import (PersonalRecordsTracker, Record, 
                                                 Achievement, RecordType, CelebrationLevel)
from .celebration_manager import CelebrationManager, SocialShareManager
from ..health_database import HealthDatabase

logger = logging.getLogger(__name__)


class RecordCardWidget(QFrame):
    """Widget displaying a single record in card format."""
    
    def __init__(self, record: Record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the record card UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            RecordCardWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
            }
            RecordCardWidget:hover {
                background-color: #FFF8F0;
                border: 1px solid #FF8C42;
            }
        """)
        
        self.setFixedHeight(110)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)
        
        # Header with record type and date
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        
        type_label = QLabel(self.record.record_type.value.replace('_', ' ').title())
        type_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        type_label.setStyleSheet("color: #6C757D; background: transparent;")
        
        date_label = QLabel(self.record.date.strftime("%b %d, %Y"))
        date_label.setFont(QFont("Arial", 8))
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        date_label.setStyleSheet("color: #8B8B8B; background: transparent;")
        
        header_layout.addWidget(type_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        
        # Metric name (formatted)
        metric_name = self.record.metric.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
        # Add spaces before capital letters
        import re
        metric_name = re.sub(r'([A-Z])', r' \1', metric_name).strip()
        
        metric_label = QLabel(metric_name)
        metric_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        metric_label.setStyleSheet("color: #333333; background: transparent;")
        metric_label.setWordWrap(True)
        metric_label.setMaximumHeight(30)
        
        # Value with improvement
        value_text = f"{self.record.value:,.0f}"
        if self.record.improvement_margin:
            improvement_text = f" (+{self.record.improvement_margin:.1f}%)"
            value_text += improvement_text
            
        value_label = QLabel(value_text)
        value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #FF8C42; background: transparent;")
        
        # Source information (if available)
        if hasattr(self.record, 'source') and self.record.source:
            source_label = QLabel(f"Source: {self.record.source}")
            source_label.setFont(QFont("Arial", 8))
            source_label.setStyleSheet("color: #6C757D; background: transparent;")
            source_label.setWordWrap(True)
        else:
            source_label = None
        
        layout.addLayout(header_layout)
        layout.addWidget(metric_label)
        layout.addWidget(value_label)
        if source_label:
            layout.addWidget(source_label)
        layout.addStretch()


class AchievementBadgeWidget(QFrame):
    """Widget displaying an achievement badge."""
    
    def __init__(self, achievement: Achievement, metric_name: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self.metric_name = metric_name
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the achievement badge UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        
        # Rarity-based styling
        rarity_colors = {
            "common": "#C0C0C0",    # Silver
            "rare": "#FFD700",      # Gold
            "legendary": "#9932CC"   # Purple
        }
        
        border_color = rarity_colors.get(self.achievement.rarity, "#C0C0C0")
        
        # Check if badge is earned (has unlocked_date)
        is_earned = hasattr(self.achievement, 'unlocked_date') and self.achievement.unlocked_date is not None
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {('#FFFFFF' if is_earned else '#F9F9F9')};
                border: 2px solid {border_color if is_earned else '#D0D0D0'};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: {('#FFF8F0' if is_earned else '#F5F5F5')};
                border: 2px solid {border_color};
            }}
        """)
        
        self.setFixedSize(140, 200)  # Increased height to accommodate metric
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)  # Reduced spacing
        layout.setContentsMargins(6, 4, 6, 4)  # Reduced padding
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon based on achievement type or name
        icon_map = {
            "First Steps": "👟",
            "Marathon": "🏃",
            "Sleep Champion": "😴",
            "Heart Hero": "❤️",
            "Consistency King": "👑",
            "Weekend Warrior": "⚔️",
            "Early Bird": "🌅",
            "Night Owl": "🦉"
        }
        icon = icon_map.get(self.achievement.name, "🏆")
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 24))  # Slightly smaller icon
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"color: {'#333333' if is_earned else '#CCCCCC'}; background: transparent;")
        icon_label.setFixedHeight(30)
        
        # Badge name
        name_label = QLabel(self.achievement.name)
        name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFixedHeight(28)  # Fixed height instead of max
        name_label.setStyleSheet(f"color: {'#333333' if is_earned else '#999999'}; background: transparent;")
        
        # Description (short)
        desc_text = self.achievement.description if hasattr(self.achievement, 'description') else ""
        if len(desc_text) > 50:  # Allow slightly longer text
            desc_text = desc_text[:47] + "..."
        desc_label = QLabel(desc_text)
        desc_label.setFont(QFont("Arial", 7))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {'#666666' if is_earned else '#AAAAAA'}; background: transparent; padding: 0px 2px;")
        desc_label.setFixedHeight(35)  # Slightly reduced to make room for metric
        
        # Metric name (new)
        if self.metric_name and is_earned:
            # Format metric name
            metric_display = self.metric_name.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
            # Add spaces before capital letters
            import re
            metric_display = re.sub(r'([A-Z])', r' \1', metric_display).strip()
            metric_text = f"for {metric_display}"
        else:
            metric_text = ""
            
        metric_label = QLabel(metric_text)
        metric_label.setFont(QFont("Arial", 7))
        metric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        metric_label.setWordWrap(True)
        metric_label.setStyleSheet(f"color: {'#FF8C42' if is_earned else '#CCCCCC'}; background: transparent;")
        metric_label.setFixedHeight(20)
        
        # Rarity
        rarity_label = QLabel(self.achievement.rarity.title())
        rarity_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        rarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rarity_label.setStyleSheet(f"color: {border_color if is_earned else '#CCCCCC'}; background: transparent;")
        rarity_label.setFixedHeight(16)
        
        # Date or "Locked"
        if is_earned:
            date_text = self.achievement.unlocked_date.strftime("%m/%d/%y")
        else:
            date_text = "Locked"
        date_label = QLabel(date_text)
        date_label.setFont(QFont("Arial", 7))
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet(f"color: {'#888888' if is_earned else '#CCCCCC'}; background: transparent;")
        date_label.setFixedHeight(14)
        
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(desc_label)
        layout.addWidget(metric_label)  # Added metric label
        layout.addWidget(rarity_label)
        layout.addWidget(date_label)



class TrophyCaseWidget(QWidget):
    """Main Trophy Case dashboard widget."""
    
    record_selected = pyqtSignal(Record)
    share_requested = pyqtSignal(Record, list)  # record, achievements
    
    def __init__(self, records_tracker: PersonalRecordsTracker, parent=None):
        super().__init__(parent)
        self.tracker = records_tracker
        self.celebration_manager = CelebrationManager(self)
        self.social_manager = SocialShareManager()
        self.record_map = {}  # Initialize record map
        self.health_db = HealthDatabase()  # Initialize health database
        self.metric_mappings = {}  # Map formatted metric names to actual metric identifiers
        self.source_metric_map = {}  # Map source-specific combinations
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Create trophy case UI."""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title with statistics
        self.create_header(layout)
        
        # Tab widget for categories
        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #FFFFFF;
                top: 0px;
            }
            QTabBar {
                background-color: transparent;
                border-bottom: 1px solid #E9ECEF;
            }
            QTabBar::tab {
                background: transparent;
                color: #6C757D;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 8px 16px;
                margin-right: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #FF8C42;
                border-bottom: 2px solid #FF8C42;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                color: #495057;
            }
            QTabBar::tab:first {
                margin-left: 0;
            }
        """)
        
        # Create tabs
        self.tabs.addTab(self.create_records_tab(), "📈 Records")
        self.tabs.addTab(self.create_badges_tab(), "🏆 Badges")
        self.tabs.addTab(self.create_stats_tab(), "📊 Statistics")
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        self.create_action_buttons(layout)
        
        self.setLayout(layout)
        
    def create_header(self, layout):
        """Create header with title and summary stats."""
        header_frame = QFrame(self)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #FF8C42;
                border-radius: 10px;
                padding: 8px;
            }
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("🏆 Trophy Case")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        # Stats (will be updated in load_data)
        self.stats_label = QLabel("Loading...")
        self.stats_label.setFont(QFont("Arial", 10))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Metric filter in header
        self.header_metric_filter = QComboBox(self)
        self.header_metric_filter.setMaximumWidth(250)
        self.header_metric_filter.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333333;
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 1.0);
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.header_metric_filter.currentTextChanged.connect(self._on_header_metric_changed)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Metric:", header_frame))
        header_layout.addWidget(self.header_metric_filter)
        header_layout.addWidget(self.stats_label)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
    def create_records_tab(self) -> QWidget:
        """Create records display tab."""
        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        self.metric_filter = QComboBox(self)
        self.metric_filter.addItem("All Metrics")
        self.metric_filter.currentTextChanged.connect(self.filter_records)
        
        self.record_type_filter = QComboBox(self)
        self.record_type_filter.addItem("All Types")
        for record_type in RecordType:
            self.record_type_filter.addItem(record_type.value.replace('_', ' ').title())
        self.record_type_filter.currentTextChanged.connect(self.filter_records)
        
        filter_layout.addWidget(QLabel("Metric:"))
        filter_layout.addWidget(self.metric_filter)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.record_type_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Scrollable area for record cards
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.records_container = QWidget(self)
        self.records_layout = QGridLayout()
        self.records_layout.setSpacing(12)
        self.records_layout.setContentsMargins(8, 8, 8, 8)
        self.records_container.setLayout(self.records_layout)
        
        scroll_area.setWidget(self.records_container)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
        
    def create_badges_tab(self) -> QWidget:
        """Create badges display tab."""
        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Badge rarity filter
        filter_layout = QHBoxLayout()
        
        self.rarity_filter = QComboBox(self)
        self.rarity_filter.addItem("All Rarities")
        self.rarity_filter.addItem("Common")
        self.rarity_filter.addItem("Rare")
        self.rarity_filter.addItem("Legendary")
        self.rarity_filter.currentTextChanged.connect(self.filter_badges)
        
        filter_layout.addWidget(QLabel("Rarity:"))
        filter_layout.addWidget(self.rarity_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Scrollable area for badges
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.badges_container = QWidget(self)
        self.badges_layout = QGridLayout()
        self.badges_layout.setSpacing(12)
        self.badges_layout.setContentsMargins(8, 8, 8, 8)
        self.badges_container.setLayout(self.badges_layout)
        
        scroll_area.setWidget(self.badges_container)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
        
        
    def create_stats_tab(self) -> QWidget:
        """Create statistics display tab."""
        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Summary statistics
        stats_group = QGroupBox("📊 Summary Statistics")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #118AB2;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(4)
        self.stats_layout.setContentsMargins(4, 4, 4, 4)
        stats_group.setLayout(self.stats_layout)
        
        layout.addWidget(stats_group)
        
        widget.setLayout(layout)
        return widget
        
    def create_action_buttons(self, layout):
        """Create action buttons at bottom."""
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 Export Records")
        export_btn.clicked.connect(self.export_records)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #06FFA5;
                color: #2D3142;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #05E893;
            }
        """)
        
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def load_data(self):
        """Load data from tracker."""
        try:
            # Initialize metric mappings and detect available metrics
            self._init_metric_mappings()
            self._detect_available_metrics()
            
            # Load records
            self.records = self.tracker.get_all_records()
            
            # Create a mapping of record IDs to records for quick lookup
            self.record_map = {}
            for record_type, records in self.records.items():
                for record in records:
                    if hasattr(record, 'id') and record.id:
                        self.record_map[record.id] = record
            
            # Never use sample data - always work from user's data
            if not self.records:
                self.records = {}
                logger.info("No records found in user's data")
            
            self.populate_records()
            
            # Load achievements
            self.achievements = self.tracker.get_achievements()
            
            # Never use sample achievements - always work from user's data
            if not self.achievements:
                self.achievements = []
                logger.info("No achievements found in user's data")
            
            self.populate_badges()
            
            # Update statistics
            self.update_statistics()
            
            # Update metric filters
            self.update_metric_filter()
            self._update_header_metric_filter()
            
        except Exception as e:
            logger.error(f"Error loading trophy case data: {e}")
            import traceback
            traceback.print_exc()
            
    def _init_metric_mappings(self):
        """Initialize metric name mappings."""
        try:
            # Get all available types from the database
            metric_types = self.health_db.get_available_types()
            
            # Create mappings for display names
            import re
            for metric in metric_types:
                # Format metric name for display
                display_name = metric.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
                display_name = re.sub(r'([A-Z])', r' \1', display_name).strip()
                self.metric_mappings[display_name] = metric
                
        except Exception as e:
            logger.error(f"Error initializing metric mappings: {e}")
            
    def _detect_available_metrics(self):
        """Detect available metrics and their sources."""
        try:
            # Get all sources
            sources = self.health_db.get_available_sources()
            
            # For each source, get its available metrics
            for source in sources:
                types = self.health_db.get_types_for_source(source)
                for metric_type in types:
                    # Create formatted display name
                    import re
                    display_name = metric_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
                    display_name = re.sub(r'([A-Z])', r' \1', display_name).strip()
                    
                    # Store source-specific combination
                    combo_key = f"{display_name} - {source}"
                    self.source_metric_map[combo_key] = (metric_type, source)
                    
        except Exception as e:
            logger.error(f"Error detecting available metrics: {e}")
            
    def populate_records(self):
        """Populate records display."""
        # Clear existing records
        for i in reversed(range(self.records_layout.count())):
            child = self.records_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Get filter selections
        metric_filter = self.metric_filter.currentText()
        type_filter = self.record_type_filter.currentText()
        header_filter = self.header_metric_filter.currentText()
        
        # Parse header filter for source-specific filtering
        filter_metric = None
        filter_source = None
        if header_filter != "All Records":
            if " - " in header_filter:
                # Source-specific filter
                parts = header_filter.split(" - ")
                metric_display = parts[0]
                filter_source = parts[1]
                # Get actual metric identifier
                filter_metric = self.metric_mappings.get(metric_display, metric_display)
            else:
                # Metric-only filter
                filter_metric = self.metric_mappings.get(header_filter, header_filter)
        
        # Add record cards
        row, col = 0, 0
        cards_added = 0
        
        for record_type, records in self.records.items():
            # Apply type filter
            type_name = record_type.value if hasattr(record_type, 'value') else str(record_type)
            if type_filter != "All Types" and type_name.replace('_', ' ').title() != type_filter:
                continue
                
            for record in records:
                # Apply metric filter from dropdown
                if metric_filter != "All Metrics" and record.metric != metric_filter:
                    continue
                    
                # Apply header metric/source filter
                if filter_metric and record.metric != filter_metric:
                    continue
                    
                # Apply source filter if specified
                if filter_source and hasattr(record, 'source') and record.source != filter_source:
                    continue
                    
                card = RecordCardWidget(record)
                card.show()  # Ensure card is visible
                self.records_layout.addWidget(card, row, col)
                cards_added += 1
                
                col += 1
                if col >= 2:  # 2 cards per row for better visibility
                    col = 0
                    row += 1
        
        # Add empty state if no records
        if row == 0 and col == 0:
            empty_text = "No personal records yet. Keep tracking your health data!"
            if header_filter != "All Records":
                empty_text = f"No records found for {header_filter}"
                
            empty_label = QLabel(empty_text)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #8B7355;
                    padding: 40px;
                }
            """)
            self.records_layout.addWidget(empty_label, 0, 0, 1, 3)
            
    def _update_header_metric_filter(self):
        """Update the header metric filter with available options."""
        try:
            current = self.header_metric_filter.currentText()
            self.header_metric_filter.blockSignals(True)
            self.header_metric_filter.clear()
            
            # Add "All Records" option
            self.header_metric_filter.addItem("All Records")
            
            # Add metric-only options
            for display_name in sorted(self.metric_mappings.keys()):
                self.header_metric_filter.addItem(display_name)
                
            # Add separator
            if self.source_metric_map:
                self.header_metric_filter.insertSeparator(self.header_metric_filter.count())
                
            # Add source-specific options
            for combo_key in sorted(self.source_metric_map.keys()):
                self.header_metric_filter.addItem(combo_key)
                
            # Restore selection
            index = self.header_metric_filter.findText(current)
            if index >= 0:
                self.header_metric_filter.setCurrentIndex(index)
            else:
                self.header_metric_filter.setCurrentIndex(0)
                
            self.header_metric_filter.blockSignals(False)
            
        except Exception as e:
            logger.error(f"Error updating header metric filter: {e}")
            
    def _on_header_metric_changed(self, text: str):
        """Handle header metric filter change."""
        self.populate_records()
        self.populate_badges()
        self.update_statistics()
                    
    def populate_badges(self):
        """Populate badges display."""
        # Clear existing badges
        for i in reversed(range(self.badges_layout.count())):
            child = self.badges_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Get header filter
        header_filter = self.header_metric_filter.currentText()
        
        # Parse header filter for source-specific filtering
        filter_metric = None
        filter_source = None
        if header_filter != "All Records":
            if " - " in header_filter:
                # Source-specific filter
                parts = header_filter.split(" - ")
                metric_display = parts[0]
                filter_source = parts[1]
                # Get actual metric identifier
                filter_metric = self.metric_mappings.get(metric_display, metric_display)
            else:
                # Metric-only filter
                filter_metric = self.metric_mappings.get(header_filter, header_filter)
        
        # Add achievement badges
        row, col = 0, 0
        badges_added = 0
        
        for achievement in self.achievements:
            # Get the metric name from the associated record
            metric_name = None
            should_show = True
            
            if hasattr(achievement, 'trigger_record_id') and achievement.trigger_record_id:
                if achievement.trigger_record_id in self.record_map:
                    record = self.record_map[achievement.trigger_record_id]
                    metric_name = record.metric
                    
                    # Apply metric filter
                    if filter_metric and record.metric != filter_metric:
                        should_show = False
                        
                    # Apply source filter if specified
                    if filter_source and hasattr(record, 'source') and record.source != filter_source:
                        should_show = False
            else:
                # If no trigger record and we have a filter, don't show
                if filter_metric or filter_source:
                    should_show = False
            
            if should_show:
                badge = AchievementBadgeWidget(achievement, metric_name)
                badge.show()  # Ensure badge is visible
                self.badges_layout.addWidget(badge, row, col)
                badges_added += 1
                
                col += 1
                if col >= 4:  # 4 badges per row for better visibility
                    col = 0
                    row += 1
        
        # Add empty state if no badges
        if badges_added == 0:
            empty_text = "No achievements unlocked yet. Keep tracking your health data to earn badges!"
            if header_filter != "All Records":
                empty_text = f"No achievements found for {header_filter}"
                
            empty_label = QLabel(empty_text)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #8B7355;
                    padding: 40px;
                }
            """)
            self.badges_layout.addWidget(empty_label, 0, 0, 1, 4)
                
                
    def update_statistics(self):
        """Update summary statistics."""
        # Get header filter
        header_filter = self.header_metric_filter.currentText()
        
        # Count filtered records and achievements
        filtered_records = 0
        filtered_achievements = 0
        
        # Parse header filter
        filter_metric = None
        filter_source = None
        if header_filter != "All Records":
            if " - " in header_filter:
                parts = header_filter.split(" - ")
                metric_display = parts[0]
                filter_source = parts[1]
                filter_metric = self.metric_mappings.get(metric_display, metric_display)
            else:
                filter_metric = self.metric_mappings.get(header_filter, header_filter)
        
        # Count records based on filter
        for record_type, records in self.records.items():
            for record in records:
                if filter_metric and record.metric != filter_metric:
                    continue
                if filter_source and hasattr(record, 'source') and record.source != filter_source:
                    continue
                filtered_records += 1
                
        # Count achievements based on filter
        for achievement in self.achievements:
            if hasattr(achievement, 'trigger_record_id') and achievement.trigger_record_id:
                if achievement.trigger_record_id in self.record_map:
                    record = self.record_map[achievement.trigger_record_id]
                    if filter_metric and record.metric != filter_metric:
                        continue
                    if filter_source and hasattr(record, 'source') and record.source != filter_source:
                        continue
                    filtered_achievements += 1
            elif not filter_metric and not filter_source:
                filtered_achievements += 1
        
        # Update header stats
        if header_filter == "All Records":
            total_records = sum(len(records) for records in self.records.values())
            total_achievements = len(self.achievements)
            self.stats_label.setText(f"{total_records} Records • {total_achievements} Achievements")
        else:
            self.stats_label.setText(f"{filtered_records} Records • {filtered_achievements} Achievements")
        
        # Update stats tab
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Calculate additional statistics
        recent_records = 0
        metric_count = len(set(record.metric for records in self.records.values() for record in records))
        
        # Count recent records (last 7 days)
        from datetime import date, timedelta
        week_ago = date.today() - timedelta(days=7)
        for records in self.records.values():
            for record in records:
                if record.date >= week_ago:
                    recent_records += 1
        
        # Count achievements by rarity
        rarity_counts = {"common": 0, "rare": 0, "legendary": 0}
        for achievement in self.achievements:
            if achievement.rarity in rarity_counts:
                rarity_counts[achievement.rarity] += 1
        
        # Create statistics rows
        stats_sections = [
            ("📊 Overview", [
                ("Total Records", total_records),
                ("Total Achievements", total_achievements),
                ("Unique Metrics", metric_count),
                ("Record Types", len(self.records)),
                ("Recent Records (7 days)", recent_records)
            ]),
            ("🏆 Achievement Breakdown", [
                ("Common Badges", rarity_counts["common"]),
                ("Rare Badges", rarity_counts["rare"]),
                ("Legendary Badges", rarity_counts["legendary"])
            ])
        ]
        
        row = 0
        for section_title, stats in stats_sections:
            # Add section header
            section_label = QLabel(section_title)
            section_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            section_label.setStyleSheet("color: #FF8C42; margin-top: 10px;")
            self.stats_layout.addWidget(section_label, row, 0, 1, 2)
            row += 1
            
            # Add stats for this section
            for label, value in stats:
                name_label = QLabel(f"  {label}:")
                name_label.setFont(QFont("Arial", 10))
                
                value_label = QLabel(str(value))
                value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                value_label.setStyleSheet("color: #5D4E37;")
                
                self.stats_layout.addWidget(name_label, row, 0)
                self.stats_layout.addWidget(value_label, row, 1)
                row += 1
        
        # Add a spacer at the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.stats_layout.addItem(spacer, row, 0, 1, 2)
            
    def update_metric_filter(self):
        """Update metric filter options."""
        current_text = self.metric_filter.currentText()
        self.metric_filter.clear()
        self.metric_filter.addItem("All Metrics")
        
        # Get unique metrics from records
        metrics = set()
        for records in self.records.values():
            for record in records:
                metrics.add(record.metric)
        
        for metric in sorted(metrics):
            self.metric_filter.addItem(metric)
        
        # Restore selection if possible
        index = self.metric_filter.findText(current_text)
        if index >= 0:
            self.metric_filter.setCurrentIndex(index)
            
    def filter_records(self):
        """Filter displayed records."""
        self.populate_records()  # Re-populate with current filters
        self.update_statistics()  # Update statistics for filtered view
        
    def filter_badges(self):
        """Filter displayed badges."""
        # Use populate_badges which already handles all filtering
        self.populate_badges()
        self.update_statistics()  # Update statistics for filtered view
        
    def export_records(self):
        """Export records to file."""
        try:
            # Create export text
            export_text = self.social_manager.create_share_text(
                list(self.records.values())[0][0] if self.records else None, 
                self.achievements[:3]
            )
            
            # Copy to clipboard
            success = self.social_manager.copy_to_clipboard(export_text)
            
            if success:
                # Show confirmation
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Export Successful", 
                                      "Records summary copied to clipboard!")
            
        except Exception as e:
            logger.error(f"Error exporting records: {e}")
            
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        if hasattr(self, 'celebration_manager'):
            self.celebration_manager.resize_confetti()