"""
Statistics display widget for health data.
Shows record counts, date ranges, and breakdowns by type and source.
"""

from typing import Optional

import pandas as pd
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..analytics.day_of_week_analyzer import DayOfWeekAnalyzer
from ..statistics_calculator import BasicStatistics
from .component_factory import ComponentFactory
from .summary_cards import SummaryCard
from .table_components import MetricTable, TableConfig


class StatisticsWidget(QWidget):
    """Widget for displaying basic health data statistics."""
    
    # Signal emitted when user clicks on a type or source
    filter_requested = pyqtSignal(str, str)  # (filter_type, filter_value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.component_factory = ComponentFactory()
        self.setup_ui()
        self._statistics = None
    
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Data Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Summary section with cards
        self.summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        
        # Create summary cards with WSJ styling
        self.total_records_card = self.component_factory.create_metric_card(
            title="Total Records",
            value="-",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        self.date_range_card = self.component_factory.create_metric_card(
            title="Date Range",
            value="-",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        summary_layout.addWidget(self.total_records_card)
        summary_layout.addWidget(self.date_range_card)
        summary_layout.addStretch()
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # Create scrollable area for types and sources
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget(self)
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Types section
        self.types_group = QGroupBox("Record Types")
        self.types_layout = QVBoxLayout()
        
        # Create types table
        types_table_config = TableConfig(
            page_size=10,
            alternating_rows=True,
            resizable_columns=True,
            movable_columns=False,
            selection_mode='row',
            multi_select=False
        )
        self.types_table = MetricTable(types_table_config)
        # self.types_table.setMaximumHeight(300)
        self.types_layout.addWidget(self.types_table)
        
        self.types_group.setLayout(self.types_layout)
        scroll_layout.addWidget(self.types_group)
        
        # Sources section
        self.sources_group = QGroupBox("Data Sources")
        self.sources_layout = QVBoxLayout()
        
        # Create sources table
        sources_table_config = TableConfig(
            page_size=10,
            alternating_rows=True,
            resizable_columns=True,
            movable_columns=False,
            selection_mode='row',
            multi_select=False
        )
        self.sources_table = MetricTable(sources_table_config)
        # self.sources_table.setMaximumHeight(300)
        self.sources_layout.addWidget(self.sources_table)
        
        self.sources_group.setLayout(self.sources_layout)
        scroll_layout.addWidget(self.sources_group)
        
        # Add stretch to push content to top
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def update_statistics(self, stats: Optional[BasicStatistics]):
        """
        Update the display with new statistics.
        
        Args:
            stats: BasicStatistics object or None to clear
        """
        self._statistics = stats
        
        if not stats or stats.total_records == 0:
            self.clear_display()
            return
        
        # Update summary cards
        self.total_records_card.update_content({'value': f"{stats.total_records:,}"})
        
        if (stats.date_range[0] is not None and stats.date_range[1] is not None and 
            hasattr(stats.date_range[0], 'strftime') and hasattr(stats.date_range[1], 'strftime')):
            try:
                date_str = (f"{stats.date_range[0].strftime('%Y-%m-%d')} "
                           f"to {stats.date_range[1].strftime('%Y-%m-%d')}")
                self.date_range_card.update_content({'value': date_str})
            except Exception:
                self.date_range_card.update_content({'value': "Invalid dates"})
        else:
            self.date_range_card.update_content({'value': "-"})
        
        # Update types table
        types_data = []
        for type_name, count in sorted(stats.records_by_type.items(), 
                                     key=lambda x: x[1], reverse=True):
            types_data.append({
                'Type': type_name,
                'Count': f"{count:,}",
                'Percentage': f"{(count/stats.total_records)*100:.1f}%"
            })
        if types_data:
            types_df = pd.DataFrame(types_data)
            self.types_table.load_data(types_df)
        else:
            self.types_table.clear_data()
        
        # Update sources table
        sources_data = []
        for source_name, count in sorted(stats.records_by_source.items(), 
                                       key=lambda x: x[1], reverse=True):
            sources_data.append({
                'Source': source_name,
                'Count': f"{count:,}",
                'Percentage': f"{(count/stats.total_records)*100:.1f}%"
            })
        if sources_data:
            sources_df = pd.DataFrame(sources_data)
            self.sources_table.load_data(sources_df)
        else:
            self.sources_table.clear_data()
    
    def show_day_of_week_patterns(self, data):
        """Display day-of-week pattern analysis."""
        if data is None or data.empty:
            return
            
        try:
            # Create analyzer
            analyzer = DayOfWeekAnalyzer(data)
            
            # Get unique metric types
            metric_types = data['metric_type'].unique()
            
            # For now, analyze the first metric type
            if len(metric_types) > 0:
                results = analyzer.analyze_metric(metric_types[0])
                
                if results and 'patterns' in results:
                    patterns = results['patterns']
                    
                    # Create pattern display (simplified for now)
                    pattern_group = QGroupBox("Day-of-Week Patterns")
                    pattern_layout = QVBoxLayout()
                    
                    if patterns:
                        for pattern in patterns:
                            pattern_text = f"{pattern.pattern_type.replace('_', ' ').title()}: {pattern.description}"
                            pattern_label = QLabel(pattern_text)
                            pattern_layout.addWidget(pattern_label)
                    else:
                        no_patterns = QLabel("No significant patterns detected")
                        no_patterns.setStyleSheet("color: #666;")
                        pattern_layout.addWidget(no_patterns)
                    
                    pattern_group.setLayout(pattern_layout)
                    
                    # Add to main layout after sources group
                    main_layout = self.layout()
                    main_layout.addWidget(pattern_group)
        
        except Exception as e:
            # Silently handle errors - pattern analysis is optional
            pass
    
    def clear_display(self):
        """Clear all statistics from the display."""
        self.total_records_card.update_content({'value': "-"})
        self.date_range_card.update_content({'value': "-"})
        
        self.types_table.clear_data()
        self.sources_table.clear_data()
    
    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def get_statistics(self) -> Optional[BasicStatistics]:
        """Get the current statistics object."""
        return self._statistics


class ClickableLabel(QLabel):
    """Label that can be clicked like a link."""
    
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: #0066CC;
                padding: 2px;
            }
            QLabel:hover {
                color: #0052A3;
                text-decoration: underline;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)