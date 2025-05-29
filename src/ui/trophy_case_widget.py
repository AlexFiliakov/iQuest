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

logger = logging.getLogger(__name__)


class RecordCardWidget(QFrame):
    """Widget displaying a single record in card format."""
    
    def __init__(self, record: Record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the record card UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: #F5E6D3;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                background: transparent;
                color: #2D3142;
                border: none;
            }
        """)
        self.setFixedHeight(100)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with record type and date
        header_layout = QHBoxLayout()
        
        type_label = QLabel(self.record.record_type.value.replace('_', ' ').title())
        type_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        date_label = QLabel(self.record.date.strftime("%b %d, %Y"))
        date_label.setFont(QFont("Arial", 9))
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        date_label.setWordWrap(False)
        date_label.setMinimumWidth(80)
        
        header_layout.addWidget(type_label)
        header_layout.addWidget(date_label)
        
        # Metric name
        metric_label = QLabel(self.record.metric)
        metric_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        # Value with improvement
        value_text = f"{self.record.value:.2f}"
        if self.record.improvement_margin:
            improvement_text = f" (+{self.record.improvement_margin:.1f}%)"
            value_text += improvement_text
            
        value_label = QLabel(value_text)
        value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #FF8C42;")
        
        layout.addLayout(header_layout)
        layout.addWidget(metric_label)
        layout.addWidget(value_label)
        
        self.setLayout(layout)


class AchievementBadgeWidget(QFrame):
    """Widget displaying an achievement badge."""
    
    def __init__(self, achievement: Achievement, parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the achievement badge UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Rarity-based styling
        rarity_colors = {
            "common": "#C0C0C0",    # Silver
            "rare": "#FFD700",      # Gold
            "legendary": "#9932CC"   # Purple
        }
        
        border_color = rarity_colors.get(self.achievement.rarity, "#C0C0C0")
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F5F5;
                border: none;
                border-radius: 10px;
                padding: 12px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            QLabel {{
                background: transparent;
                color: #2D3142;
                border: none;
            }}
        """)
        self.setFixedSize(120, 130)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon (emoji placeholder)
        icon_label = QLabel("🏆")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Badge name
        name_label = QLabel(self.achievement.name)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        
        # Rarity
        rarity_label = QLabel(self.achievement.rarity.title())
        rarity_label.setFont(QFont("Arial", 8))
        rarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rarity_label.setStyleSheet(f"color: {border_color}; font-weight: bold;")
        
        # Date
        date_label = QLabel(self.achievement.unlocked_date.strftime("%m/%d/%y"))
        date_label.setFont(QFont("Arial", 8))
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(rarity_label)
        layout.addWidget(date_label)
        
        self.setLayout(layout)


class StreakDisplayWidget(QFrame):
    """Widget displaying streak information."""
    
    def __init__(self, metric: str, streak_info, parent=None):
        super().__init__(parent)
        self.metric = metric
        self.streak_info = streak_info
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the streak display UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFF8DC;
                border: 1px solid #FFD166;
                border-radius: 8px;
                padding: 6px;
            }
            QLabel {
                background: transparent;
                color: #2D3142;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Metric name
        metric_label = QLabel(self.metric)
        metric_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        # Current streak
        current_text = f"Current: {self.streak_info.current_length} days"
        current_label = QLabel(current_text)
        current_label.setFont(QFont("Arial", 10))
        
        # Best streak
        best_text = f"Best: {self.streak_info.best_length} days"
        best_label = QLabel(best_text)
        best_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        best_label.setStyleSheet("color: #FF8C42;")
        
        # Progress bar for current streak vs best
        if self.streak_info.best_length > 0:
            progress_bar = QProgressBar(self)
            progress_bar.setMaximum(self.streak_info.best_length)
            progress_bar.setValue(min(self.streak_info.current_length, self.streak_info.best_length))
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #FFD166;
                    border-radius: 3px;
                    background-color: #FFFFFF;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FFD166;
                }
            """)
            layout.addWidget(progress_bar)
        
        layout.addWidget(metric_label)
        layout.addWidget(current_label)
        layout.addWidget(best_label)
        
        self.setLayout(layout)


class TrophyCaseWidget(QWidget):
    """Main Trophy Case dashboard widget."""
    
    record_selected = pyqtSignal(Record)
    share_requested = pyqtSignal(Record, list)  # record, achievements
    
    def __init__(self, records_tracker: PersonalRecordsTracker, parent=None):
        super().__init__(parent)
        self.tracker = records_tracker
        self.celebration_manager = CelebrationManager(self)
        self.social_manager = SocialShareManager()
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
                border: 1px solid #FF8C42;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F5E6D3;
                border: 1px solid #FF8C42;
                padding: 4px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFD166;
                font-weight: bold;
            }
        """)
        
        # Create tabs
        self.tabs.addTab(self.create_records_tab(), "📈 Records")
        self.tabs.addTab(self.create_badges_tab(), "🏆 Badges")
        self.tabs.addTab(self.create_streaks_tab(), "🔥 Streaks")
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
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
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
        self.records_layout.setSpacing(4)
        self.records_layout.setContentsMargins(0, 0, 0, 0)
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
        self.badges_layout.setSpacing(4)
        self.badges_layout.setContentsMargins(0, 0, 0, 0)
        self.badges_container.setLayout(self.badges_layout)
        
        scroll_area.setWidget(self.badges_container)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
        
    def create_streaks_tab(self) -> QWidget:
        """Create streaks display tab."""
        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Active streaks section
        active_group = QGroupBox("🔥 Active Streaks")
        active_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #FFD166;
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
        
        self.active_streaks_layout = QVBoxLayout()
        self.active_streaks_layout.setSpacing(4)
        self.active_streaks_layout.setContentsMargins(4, 4, 4, 4)
        active_group.setLayout(self.active_streaks_layout)
        
        # Best streaks section
        best_group = QGroupBox("🏆 Best Streaks")
        best_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #FF8C42;
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
        
        self.best_streaks_layout = QVBoxLayout()
        self.best_streaks_layout.setSpacing(4)
        self.best_streaks_layout.setContentsMargins(4, 4, 4, 4)
        best_group.setLayout(self.best_streaks_layout)
        
        layout.addWidget(active_group)
        layout.addWidget(best_group)
        
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
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #118AB2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F7A94;
            }
        """)
        
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
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def load_data(self):
        """Load data from tracker."""
        try:
            # Load records
            self.records = self.tracker.get_all_records()
            self.populate_records()
            
            # Load achievements
            self.achievements = self.tracker.get_achievements()
            self.populate_badges()
            
            # Load streak information (placeholder for now)
            self.populate_streaks()
            
            # Update statistics
            self.update_statistics()
            
            # Update metric filter
            self.update_metric_filter()
            
        except Exception as e:
            logger.error(f"Error loading trophy case data: {e}")
            
    def populate_records(self):
        """Populate records display."""
        # Clear existing records
        for i in reversed(range(self.records_layout.count())):
            child = self.records_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add record cards
        row, col = 0, 0
        for record_type, records in self.records.items():
            for record in records[:3]:  # Show top 3 per type
                card = RecordCardWidget(record)
                self.records_layout.addWidget(card, row, col)
                
                col += 1
                if col >= 3:  # 3 cards per row
                    col = 0
                    row += 1
                    
    def populate_badges(self):
        """Populate badges display."""
        # Clear existing badges
        for i in reversed(range(self.badges_layout.count())):
            child = self.badges_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add achievement badges
        row, col = 0, 0
        for achievement in self.achievements:
            badge = AchievementBadgeWidget(achievement)
            self.badges_layout.addWidget(badge, row, col)
            
            col += 1
            if col >= 5:  # 5 badges per row
                col = 0
                row += 1
                
    def populate_streaks(self):
        """Populate streaks display."""
        # Clear existing streaks
        for layout in [self.active_streaks_layout, self.best_streaks_layout]:
            for i in reversed(range(layout.count())):
                child = layout.takeAt(i).widget()
                if child:
                    child.deleteLater()
        
        # Add placeholder streak widgets
        # In a real implementation, this would use actual streak data
        from ..analytics.personal_records_tracker import StreakInfo
        
        placeholder_streaks = [
            ("Heart Rate", StreakInfo("Heart Rate", "consistency", 15, 45)),
            ("Steps", StreakInfo("Steps", "consistency", 8, 30)),
            ("Weight", StreakInfo("Weight", "consistency", 22, 22))
        ]
        
        for metric, streak_info in placeholder_streaks:
            streak_widget = StreakDisplayWidget(metric, streak_info)
            if streak_info.current_length > 0:
                self.active_streaks_layout.addWidget(streak_widget)
            else:
                self.best_streaks_layout.addWidget(streak_widget)
                
    def update_statistics(self):
        """Update summary statistics."""
        total_records = sum(len(records) for records in self.records.values())
        total_achievements = len(self.achievements)
        
        # Update header stats
        self.stats_label.setText(f"{total_records} Records • {total_achievements} Achievements")
        
        # Update stats tab
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        stats = [
            ("Total Records", total_records),
            ("Total Achievements", total_achievements),
            ("Record Types", len(self.records)),
            ("Recent Records (7 days)", 0)  # Placeholder
        ]
        
        row = 0
        for label, value in stats:
            name_label = QLabel(label + ":")
            name_label.setFont(QFont("Arial", 10))
            
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #FF8C42;")
            
            self.stats_layout.addWidget(name_label, row, 0)
            self.stats_layout.addWidget(value_label, row, 1)
            row += 1
            
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
        # Implementation would filter based on current filter selections
        pass
        
    def filter_badges(self):
        """Filter displayed badges."""
        # Implementation would filter based on rarity selection
        pass
        
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