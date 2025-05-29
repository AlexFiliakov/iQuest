"""Progressive drill-down functionality for health visualizations."""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QStackedWidget, QToolButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon

from .wsj_style_manager import WSJStyleManager
from .pyqtgraph_chart_factory import PyQtGraphChartFactory
from .matplotlib_chart_factory import MatplotlibChartFactory
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class DrillDownLevel:
    """Represents a level in the drill-down hierarchy."""
    
    def __init__(self, name: str, level: int, 
                 time_granularity: str, aggregation: str):
        self.name = name
        self.level = level
        self.time_granularity = time_granularity  # 'monthly', 'weekly', 'daily', 'hourly'
        self.aggregation = aggregation  # 'mean', 'sum', 'max', 'min'
        self.parent_selection = None
        self.data = None


class ProgressiveDrillDownWidget(QWidget):
    """Widget enabling progressive drill-down through health data."""
    
    # Signals
    levelChanged = pyqtSignal(int)  # Emitted when drill level changes
    selectionChanged = pyqtSignal(dict)  # Emitted when data selection changes
    
    def __init__(self, style_manager: WSJStyleManager, 
                 chart_factory: PyQtGraphChartFactory,
                 parent=None):
        super().__init__(parent)
        self.style_manager = style_manager
        self.chart_factory = chart_factory
        
        # Drill-down configuration
        self.levels = self._create_drill_levels()
        self.current_level = 0
        self.navigation_stack = []  # For back navigation
        
        # UI components
        self.stacked_widget = QStackedWidget(self)
        self.breadcrumb = QWidget(self)
        self.chart_container = QWidget(self)
        
        self._setup_ui()
    
    def _create_drill_levels(self) -> List[DrillDownLevel]:
        """Create the drill-down hierarchy."""
        return [
            DrillDownLevel("Year Overview", 0, "monthly", "mean"),
            DrillDownLevel("Month Detail", 1, "daily", "mean"),
            DrillDownLevel("Week Focus", 2, "daily", "sum"),
            DrillDownLevel("Day Analysis", 3, "hourly", "mean"),
            DrillDownLevel("Hour Detail", 4, "5min", "mean")
        ]
    
    def _setup_ui(self):
        """Set up the UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create navigation header
        nav_header = self._create_navigation_header()
        layout.addWidget(nav_header)
        
        # Create breadcrumb trail
        self._setup_breadcrumb()
        layout.addWidget(self.breadcrumb)
        
        # Add separator
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {self.style_manager.WARM_PALETTE['grid']};")
        layout.addWidget(separator)
        
        # Chart container with stacked widget for smooth transitions
        layout.addWidget(self.stacked_widget, 1)
        
        # Apply WSJ styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.WARM_PALETTE['surface']};
                color: {self.style_manager.WARM_PALETTE['text_primary']};
            }}
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self.style_manager.WARM_PALETTE['grid']};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.WARM_PALETTE['background']};
                border-color: {self.style_manager.WARM_PALETTE['primary']};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.WARM_PALETTE['primary']};
                color: white;
            }}
        """)
    
    def _create_navigation_header(self) -> QWidget:
        """Create navigation header with back/forward buttons."""
        header = QWidget(self)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Back button
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.navigate_back)
        self.back_btn.setEnabled(False)
        layout.addWidget(self.back_btn)
        
        # Level indicator
        self.level_label = QLabel("Year Overview")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setStyleSheet(f"""
            font-size: {self.style_manager.TYPOGRAPHY['subtitle']['size']}px;
            font-weight: {self.style_manager.TYPOGRAPHY['subtitle']['weight']};
            color: {self.style_manager.TYPOGRAPHY['subtitle']['color']};
        """)
        layout.addWidget(self.level_label, 1)
        
        # Reset button
        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.clicked.connect(self.reset_to_overview)
        self.reset_btn.setEnabled(False)
        layout.addWidget(self.reset_btn)
        
        return header
    
    def _setup_breadcrumb(self):
        """Set up breadcrumb navigation."""
        layout = QHBoxLayout(self.breadcrumb)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(10)
        
        # Will be populated dynamically
        self.breadcrumb_buttons = []
    
    def load_data(self, metric_data: pd.DataFrame, metric_name: str):
        """Load data for drill-down navigation."""
        self.metric_data = metric_data
        self.metric_name = metric_name
        
        # Start at overview level
        self.show_level(0)
    
    def show_level(self, level: int, parent_selection: Optional[Dict[str, Any]] = None):
        """Show a specific drill-down level."""
        if level < 0 or level >= len(self.levels):
            return
        
        self.current_level = level
        current = self.levels[level]
        current.parent_selection = parent_selection
        
        # Update navigation state
        self._update_navigation_state()
        
        # Prepare data for this level
        level_data = self._prepare_level_data(current, parent_selection)
        current.data = level_data
        
        # Create appropriate visualization
        chart_widget = self._create_level_chart(current, level_data)
        
        # Add to stacked widget with animation
        self._transition_to_chart(chart_widget)
        
        # Update breadcrumb
        self._update_breadcrumb()
        
        # Emit signal
        self.levelChanged.emit(level)
    
    def _prepare_level_data(self, level: DrillDownLevel, 
                           parent_selection: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare data for a specific level."""
        data = self.metric_data.copy()
        
        # Apply parent selection filter if any
        if parent_selection:
            start_date = parent_selection.get('start_date')
            end_date = parent_selection.get('end_date')
            if start_date and end_date:
                mask = (data.index >= start_date) & (data.index <= end_date)
                data = data[mask]
        
        # Resample based on level granularity
        resample_map = {
            'monthly': 'M',
            'weekly': 'W',
            'daily': 'D',
            'hourly': 'H',
            '5min': '5T'
        }
        
        rule = resample_map.get(level.time_granularity, 'D')
        
        # Apply aggregation
        if level.aggregation == 'mean':
            resampled = data.resample(rule).mean()
        elif level.aggregation == 'sum':
            resampled = data.resample(rule).sum()
        elif level.aggregation == 'max':
            resampled = data.resample(rule).max()
        elif level.aggregation == 'min':
            resampled = data.resample(rule).min()
        else:
            resampled = data.resample(rule).mean()
        
        return resampled.dropna()
    
    def _create_level_chart(self, level: DrillDownLevel, 
                           data: pd.DataFrame) -> QWidget:
        """Create appropriate chart for the level."""
        config = {
            'title': f"{self.metric_name} - {level.name}",
            'subtitle': self._generate_level_subtitle(level, data),
            'clickable': level.level < len(self.levels) - 1,  # Can drill down further
            'show_hover': True,
            'accessible_name': f"{level.name} chart showing {self.metric_name}",
            'accessible_description': f"Interactive chart at {level.time_granularity} granularity"
        }
        
        # Create chart based on level
        if level.level == 0:  # Year overview
            chart = self._create_year_overview(data, config)
        elif level.level == 1:  # Month detail
            chart = self._create_month_detail(data, config)
        elif level.level == 2:  # Week focus
            chart = self._create_week_focus(data, config)
        elif level.level == 3:  # Day analysis
            chart = self._create_day_analysis(data, config)
        else:  # Hour detail
            chart = self._create_hour_detail(data, config)
        
        # Connect click handler for drill-down
        if hasattr(chart, 'dataPointClicked'):
            chart.dataPointClicked.connect(lambda point: self._on_data_click(point, level))
        
        return chart
    
    def _create_year_overview(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create year overview visualization."""
        # Use bar chart for monthly data
        chart_data = {
            'values': data,
            'labels': [d.strftime('%b') for d in data.index]
        }
        
        config.update({
            'chart_type': 'bar',
            'color': self.style_manager.WARM_PALETTE['primary'],
            'hover_template': '{label}: {value:.1f}'
        })
        
        return self.chart_factory.create_chart('bar', chart_data, config)
    
    def _create_month_detail(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create month detail visualization."""
        # Use line chart for daily data
        config.update({
            'show_points': True,
            'point_size': 8,
            'line_width': 2
        })
        
        return self.chart_factory.create_chart('multi_metric_line', 
                                             {self.metric_name: data}, config)
    
    def _create_week_focus(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create week focus visualization."""
        # Use area chart for week view
        config.update({
            'fill_under': True,
            'fill_alpha': 0.3
        })
        
        return self.chart_factory.create_chart('multi_metric_line',
                                             {self.metric_name: data}, config)
    
    def _create_day_analysis(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create day analysis visualization."""
        # Use line chart with markers for hourly data
        config.update({
            'show_points': True,
            'point_size': 10,
            'show_values': len(data) <= 24
        })
        
        return self.chart_factory.create_chart('multi_metric_line',
                                             {self.metric_name: data}, config)
    
    def _create_hour_detail(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create hour detail visualization."""
        # Use sparkline-style for 5-minute data
        config.update({
            'minimal': True,
            'show_range': True
        })
        
        return self.chart_factory.create_chart('sparkline', data, config)
    
    def _generate_level_subtitle(self, level: DrillDownLevel, data: pd.DataFrame) -> str:
        """Generate informative subtitle for the level."""
        if data.empty:
            return "No data available"
        
        start = data.index[0].strftime('%b %d, %Y')
        end = data.index[-1].strftime('%b %d, %Y')
        
        stats = f"Average: {data.mean().iloc[0]:.1f}, "
        stats += f"Range: {data.min().iloc[0]:.1f} - {data.max().iloc[0]:.1f}"
        
        return f"{start} to {end} | {stats}"
    
    def _on_data_click(self, point: Dict[str, Any], current_level: DrillDownLevel):
        """Handle click on data point for drill-down."""
        if current_level.level >= len(self.levels) - 1:
            return  # Can't drill down further
        
        # Determine date range for drill-down
        clicked_date = point.get('date', point.get('x'))
        if not clicked_date:
            return
        
        # Calculate appropriate date range based on current granularity
        if current_level.time_granularity == 'monthly':
            # Drill down to the clicked month
            start_date = clicked_date.replace(day=1)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1) - timedelta(days=1)
        elif current_level.time_granularity == 'daily':
            # Drill down to week containing the clicked day
            start_date = clicked_date - timedelta(days=clicked_date.weekday())
            end_date = start_date + timedelta(days=6)
        elif current_level.time_granularity == 'hourly':
            # Drill down to the clicked hour
            start_date = clicked_date
            end_date = clicked_date + timedelta(hours=1)
        else:
            # Default to day range
            start_date = clicked_date
            end_date = clicked_date + timedelta(days=1)
        
        # Store navigation state
        self.navigation_stack.append({
            'level': current_level.level,
            'selection': current_level.parent_selection
        })
        
        # Navigate to next level
        selection = {
            'start_date': start_date,
            'end_date': end_date,
            'value': point.get('value', point.get('y'))
        }
        
        self.show_level(current_level.level + 1, selection)
        self.selectionChanged.emit(selection)
    
    def navigate_back(self):
        """Navigate back to previous level."""
        if not self.navigation_stack:
            return
        
        prev_state = self.navigation_stack.pop()
        self.show_level(prev_state['level'], prev_state['selection'])
    
    def reset_to_overview(self):
        """Reset to top-level overview."""
        self.navigation_stack.clear()
        self.show_level(0)
    
    def _transition_to_chart(self, new_chart: QWidget):
        """Animate transition to new chart."""
        # Add new chart to stacked widget
        index = self.stacked_widget.addWidget(new_chart)
        
        # Animate transition
        self.stacked_widget.setCurrentIndex(index)
        
        # Clean up old widgets (keep only last 3 for back navigation)
        while self.stacked_widget.count() > 3:
            old_widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(old_widget)
            old_widget.deleteLater()
    
    def _update_navigation_state(self):
        """Update navigation button states."""
        self.back_btn.setEnabled(len(self.navigation_stack) > 0)
        self.reset_btn.setEnabled(self.current_level > 0)
        self.level_label.setText(self.levels[self.current_level].name)
    
    def _update_breadcrumb(self):
        """Update breadcrumb trail."""
        # Clear existing breadcrumbs
        for btn in self.breadcrumb_buttons:
            btn.deleteLater()
        self.breadcrumb_buttons.clear()
        
        # Add breadcrumb for each level up to current
        for i in range(self.current_level + 1):
            if i > 0:
                # Add separator
                sep = QLabel("›")
                sep.setStyleSheet(f"color: {self.style_manager.WARM_PALETTE['text_secondary']};")
                self.breadcrumb.layout().addWidget(sep)
                self.breadcrumb_buttons.append(sep)
            
            # Add level button
            btn = QPushButton(self.levels[i].name)
            btn.setFlat(True)
            
            if i == self.current_level:
                # Current level - not clickable
                btn.setEnabled(False)
                btn.setStyleSheet(f"""
                    color: {self.style_manager.WARM_PALETTE['primary']};
                    font-weight: 600;
                    border: none;
                    padding: 4px 8px;
                """)
            else:
                # Previous level - clickable
                btn.clicked.connect(lambda checked, level=i: self._breadcrumb_navigate(level))
                btn.setStyleSheet(f"""
                    color: {self.style_manager.WARM_PALETTE['text_secondary']};
                    border: none;
                    padding: 4px 8px;
                    text-decoration: underline;
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            self.breadcrumb.layout().addWidget(btn)
            self.breadcrumb_buttons.append(btn)
        
        # Add stretch at end
        self.breadcrumb.layout().addStretch()
    
    def _breadcrumb_navigate(self, level: int):
        """Navigate to a specific level via breadcrumb."""
        if level >= self.current_level:
            return
        
        # Remove navigation states after the target level
        while len(self.navigation_stack) > level:
            self.navigation_stack.pop()
        
        # Navigate to the level
        if level == 0:
            self.reset_to_overview()
        else:
            # Get the parent selection for this level
            if self.navigation_stack:
                prev_state = self.navigation_stack[-1]
                self.show_level(level, prev_state['selection'])
            else:
                self.show_level(level)
    
    def get_current_view_config(self) -> Dict[str, Any]:
        """Get configuration of current view for sharing."""
        return {
            'metric': self.metric_name,
            'level': self.current_level,
            'level_name': self.levels[self.current_level].name,
            'parent_selection': self.levels[self.current_level].parent_selection,
            'navigation_stack': self.navigation_stack.copy()
        }
    
    def restore_view_config(self, config: Dict[str, Any]):
        """Restore a previously saved view configuration."""
        # Restore navigation stack
        self.navigation_stack = config.get('navigation_stack', []).copy()
        
        # Navigate to the saved level
        self.show_level(
            config.get('level', 0),
            config.get('parent_selection')
        )