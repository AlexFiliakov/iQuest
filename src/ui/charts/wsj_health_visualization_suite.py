"""WSJ-inspired health visualization suite with hybrid rendering approach."""

from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QFileDialog, QMessageBox,
                            QSplitter, QTabWidget, QMenu, QToolButton, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QAction

from .wsj_style_manager import WSJStyleManager
from .pyqtgraph_chart_factory import PyQtGraphChartFactory
from .matplotlib_chart_factory import MatplotlibChartFactory, MatplotlibChartWidget
from .progressive_drill_down import ProgressiveDrillDownWidget
from .shareable_dashboard import (ShareableDashboardManager, ShareDashboardDialog,
                                ShareLinkDisplay, SharedDashboardViewer)
from ...analytics.data_source_protocol import DataSourceProtocol
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class PerformanceManager:
    """Manages performance optimization for large datasets."""
    
    def __init__(self):
        self.cache = {}
        self.max_display_points = 10000
    
    def optimize_data_for_display(self, data: pd.DataFrame, 
                                 max_points: Optional[int] = None) -> pd.DataFrame:
        """Optimize data for display by downsampling if necessary."""
        max_points = max_points or self.max_display_points
        
        if len(data) <= max_points:
            return data
        
        # Downsample using LTTB algorithm (Largest Triangle Three Buckets)
        # Simplified version - in production use proper LTTB implementation
        step = len(data) // max_points
        indices = np.arange(0, len(data), step)
        
        # Always include first and last points
        if indices[-1] != len(data) - 1:
            indices = np.append(indices, len(data) - 1)
        
        return data.iloc[indices]
    
    def should_use_cached(self, cache_key: str, ttl_seconds: int = 300) -> bool:
        """Check if cached data should be used."""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', datetime.min)
        return (datetime.now() - cached_time).total_seconds() < ttl_seconds


class WSJHealthVisualizationSuite(QWidget):
    """Comprehensive health visualization suite with WSJ-inspired design."""
    
    # Signals
    chartExported = pyqtSignal(str)  # Emitted when chart is exported
    dataPointSelected = pyqtSignal(dict)  # Emitted when data point is selected
    
    def __init__(self, data_source: DataSourceProtocol, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.style_manager = WSJStyleManager()
        self.performance_manager = PerformanceManager()
        
        # Initialize factories
        self.interactive_factory = PyQtGraphChartFactory(self.style_manager)
        self.export_factory = MatplotlibChartFactory(self.style_manager)
        
        # Initialize managers
        self.share_manager = ShareableDashboardManager(self.style_manager)
        
        # Current visualization state
        self.current_chart_type = None
        self.current_data = None
        self.current_config = None
        
        # Drill-down widget
        self.drill_down_widget = None
        
        # Feature flags
        self.drill_down_enabled = True
        self.date_selection_enabled = True
        self.anonymized_mode = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Create main content area with tabs
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.tab_widget)
        
        # Apply styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.WARM_PALETTE['surface']};
                color: {self.style_manager.WARM_PALETTE['text_primary']};
                font-family: Inter, Arial, sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid {self.style_manager.WARM_PALETTE['grid']};
                background-color: {self.style_manager.WARM_PALETTE['surface']};
            }}
            QTabBar::tab {{
                background-color: {self.style_manager.WARM_PALETTE['background']};
                padding: 8px 16px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.style_manager.WARM_PALETTE['surface']};
                color: {self.style_manager.WARM_PALETTE['primary']};
            }}
        """)
    
    def _create_toolbar(self) -> QWidget:
        """Create the toolbar with chart selection and export options."""
        toolbar = QWidget(self)
        toolbar.setMaximumHeight(60)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Chart type selector
        layout.addWidget(QLabel("Chart Type:"))
        self.chart_selector = QComboBox(self)
        self.chart_selector.addItems([
            "Multi-Metric Overlay",
            "Correlation Heatmap",
            "Health Sparklines",
            "Timeline View",
            "Cyclical Patterns",
            "Comparative Analysis",
            "Distribution Comparison",
            "Trend Waterfall",
            "Drill-Down Explorer"
        ])
        self.chart_selector.currentTextChanged.connect(self._on_chart_type_changed)
        layout.addWidget(self.chart_selector)
        
        layout.addStretch()
        
        # Share button
        self.share_btn = QPushButton("Share Dashboard")
        self.share_btn.clicked.connect(self._share_dashboard)
        self.share_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.WARM_PALETTE['secondary']};
                color: {self.style_manager.WARM_PALETTE['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.WARM_PALETTE['primary']};
                color: white;
            }}
        """)
        layout.addWidget(self.share_btn)
        
        # Export button with dropdown
        self.export_btn = QToolButton()
        self.export_btn.setText("Export")
        self.export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        
        export_menu = QMenu(self.export_btn)
        export_menu.addAction("Export as PNG", lambda: self._export_chart('png'))
        export_menu.addAction("Export as PDF", lambda: self._export_chart('pdf'))
        export_menu.addAction("Export as SVG", lambda: self._export_chart('svg'))
        
        self.export_btn.setMenu(export_menu)
        self.export_btn.clicked.connect(lambda: self._export_chart('png'))
        
        self.export_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {self.style_manager.WARM_PALETTE['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QToolButton:hover {{
                background-color: #E67A35;
            }}
            QToolButton::menu-indicator {{
                image: none;
                subcontrol-position: right center;
                subcontrol-origin: padding;
                padding-right: 5px;
            }}
        """)
        layout.addWidget(self.export_btn)
        
        return toolbar
    
    def _on_chart_type_changed(self, chart_type: str):
        """Handle chart type selection."""
        chart_map = {
            "Multi-Metric Overlay": self._show_multi_metric,
            "Correlation Heatmap": self._show_correlation_heatmap,
            "Health Sparklines": self._show_sparklines,
            "Timeline View": self._show_timeline,
            "Cyclical Patterns": self._show_cyclical_patterns,
            "Comparative Analysis": self._show_comparative,
            "Distribution Comparison": self._show_distribution,
            "Trend Waterfall": self._show_waterfall,
            "Drill-Down Explorer": self._show_drill_down
        }
        
        handler = chart_map.get(chart_type)
        if handler:
            handler()
    
    def create_interactive_chart(self, chart_type: str, data: Any, 
                               config: Dict[str, Any]) -> QWidget:
        """Create interactive chart optimized for dashboard use."""
        # Apply WSJ styling to config
        config.update({
            'colors': self.style_manager.get_warm_palette(),
            'typography': self.style_manager.get_typography_config(),
            'spacing': self.style_manager.get_spacing_config(),
            'accessibility': self.style_manager.get_accessibility_config()
        })
        
        # Performance optimization for large datasets
        if isinstance(data, pd.DataFrame) and len(data) > 10000:
            data = self.performance_manager.optimize_data_for_display(data)
            config['data_optimized'] = True
        elif isinstance(data, dict):
            # Check if any metric has large data
            total_points = sum(len(df) for df in data.values() if isinstance(df, pd.DataFrame))
            if total_points > 10000:
                # Optimize each metric's data
                optimized_data = {}
                for metric, df in data.items():
                    if isinstance(df, pd.DataFrame):
                        optimized_data[metric] = self.performance_manager.optimize_data_for_display(df)
                    else:
                        optimized_data[metric] = df
                data = optimized_data
                config['data_optimized'] = True
        
        # Create chart with PyQtGraph for interactivity
        chart_widget = self.interactive_factory.create_chart(chart_type, data, config)
        
        # Store current state
        self.current_chart_type = chart_type
        self.current_data = data
        self.current_config = config
        
        return chart_widget
    
    def create_export_chart(self, chart_type: str, data: Any,
                          config: Dict[str, Any], export_format: str = "png") -> bytes:
        """Create high-quality chart for export/reports."""
        # Use matplotlib for publication quality
        fig = self.export_factory.create_chart(chart_type, data, config)
        
        # Export to bytes
        buffer = io.BytesIO()
        fig.savefig(buffer, format=export_format, dpi=300, 
                   bbox_inches='tight', facecolor=fig.get_facecolor())
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _show_multi_metric(self):
        """Show multi-metric overlay visualization."""
        # Clear existing tabs
        self.tab_widget.clear()
        
        # Get available metrics from data source
        available_metrics = self.data_source.get_available_metrics()
        
        # Select a few key metrics for demo
        demo_metrics = ['steps', 'heart_rate', 'active_energy']
        metrics = [m for m in demo_metrics if m in available_metrics][:3]
        
        if not metrics:
            metrics = available_metrics[:3]
        
        # Get time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Fetch data for each metric
        data_dict = {}
        for metric in metrics:
            metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
            if metric_data is not None and not metric_data.empty:
                data_dict[metric] = metric_data
        
        if not data_dict:
            self._show_no_data_message()
            return
        
        # Configuration
        config = {
            'title': 'Health Metrics Overview',
            'subtitle': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
            'y_axes': self.style_manager.configure_independent_axes(list(data_dict.keys())),
            'colors': {metric: self.style_manager.get_metric_color(metric, i) 
                      for i, metric in enumerate(data_dict.keys())},
            'legend_position': 'top',
            'grid_style': 'subtle',
            'accessible_name': f'Multi-metric chart showing {len(data_dict)} health metrics',
            'accessible_description': f'Interactive chart displaying {", ".join(data_dict.keys())} over time'
        }
        
        # Create interactive version
        interactive_widget = self.create_interactive_chart('multi_metric_line', data_dict, config)
        self.tab_widget.addTab(interactive_widget, "Interactive View")
        
        # Create static version for preview
        static_fig = self.export_factory.create_chart('multi_metric_line', data_dict, config)
        static_widget = MatplotlibChartWidget(static_fig)
        self.tab_widget.addTab(static_widget, "Print Preview")
    
    def _show_correlation_heatmap(self):
        """Show correlation heatmap visualization."""
        self.tab_widget.clear()
        
        # Get correlation data from data source
        try:
            # Get available metrics
            metrics = self.data_source.get_available_metrics()[:10]  # Limit to 10 for readability
            
            # Calculate correlation matrix
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 3 months for better correlations
            
            # Build dataframe with all metrics
            data_frames = []
            metric_names = []
            
            for metric in metrics:
                metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
                if metric_data is not None and not metric_data.empty:
                    # Resample to daily for correlation calculation
                    daily_data = metric_data.resample('D').mean()
                    data_frames.append(daily_data)
                    metric_names.append(metric)
            
            if len(data_frames) < 2:
                self._show_no_data_message()
                return
            
            # Combine into single dataframe
            combined_df = pd.concat(data_frames, axis=1, join='inner')
            combined_df.columns = metric_names
            
            # Calculate correlations
            correlation_matrix = combined_df.corr()
            
            # Calculate p-values (simplified - in production use scipy.stats)
            n = len(combined_df)
            significance_matrix = pd.DataFrame(
                np.where(np.abs(correlation_matrix) > 0.3, 0.01, 0.1),
                index=correlation_matrix.index,
                columns=correlation_matrix.columns
            )
            
            # Configuration
            config = {
                'title': 'Health Metrics Correlations',
                'subtitle': 'Significant correlations highlighted',
                'colormap': self.style_manager.get_correlation_colormap(),
                'significance_indicators': True,
                'mask_upper': True,
                'show_values': True,
                'accessible_name': 'Correlation matrix heatmap',
                'accessible_description': f'Heatmap showing correlations between {len(metric_names)} health metrics'
            }
            
            data = {
                'correlation': correlation_matrix,
                'significance': significance_matrix
            }
            
            # Create visualizations
            interactive_widget = self.create_interactive_chart('correlation_heatmap', data, config)
            self.tab_widget.addTab(interactive_widget, "Interactive Heatmap")
            
            static_fig = self.export_factory.create_chart('correlation_heatmap', data, config)
            static_widget = MatplotlibChartWidget(static_fig)
            self.tab_widget.addTab(static_widget, "Print Preview")
            
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            self._show_error_message(str(e))
    
    def _show_sparklines(self):
        """Show health sparklines visualization."""
        self.tab_widget.clear()
        
        # Create sparklines container
        container = QWidget(self)
        layout = QVBoxLayout(container)
        
        # Add title
        title = QLabel("Health Metrics Sparklines")
        title.setStyleSheet(f"""
            font-size: {self.style_manager.TYPOGRAPHY['title']['size']}px;
            font-weight: {self.style_manager.TYPOGRAPHY['title']['weight']};
            color: {self.style_manager.TYPOGRAPHY['title']['color']};
            padding: 20px;
        """)
        layout.addWidget(title)
        
        # Get recent data for sparklines
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week
        
        # Create sparklines for key metrics
        metrics = ['steps', 'heart_rate', 'active_energy', 'distance', 'stand_hours']
        available_metrics = self.data_source.get_available_metrics()
        
        for metric in metrics:
            if metric not in available_metrics:
                continue
            
            # Get metric data
            metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
            if metric_data is None or metric_data.empty:
                continue
            
            # Create sparkline row
            row = QWidget(self)
            row_layout = QHBoxLayout(row)
            
            # Metric label
            label = QLabel(metric.replace('_', ' ').title())
            label.setMinimumWidth(150)
            label.setStyleSheet(f"""
                font-size: 14px;
                color: {self.style_manager.WARM_PALETTE['text_primary']};
            """)
            row_layout.addWidget(label)
            
            # Sparkline chart
            config = {
                'show_value': True,
                'compact': True
            }
            sparkline = self.create_interactive_chart('sparkline', metric_data, config)
            row_layout.addWidget(sparkline)
            
            layout.addWidget(row)
        
        layout.addStretch()
        self.tab_widget.addTab(container, "Sparklines Dashboard")
    
    def _show_timeline(self):
        """Show timeline visualization with events."""
        self.tab_widget.clear()
        
        # Get time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 2 months
        
        # Get background metric data
        background_metrics = {}
        for metric in ['steps', 'heart_rate']:
            metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
            if metric_data is not None and not metric_data.empty:
                background_metrics[metric] = metric_data.resample('D').mean()
        
        # Generate sample events (in production, these would come from user data)
        events = [
            {'time': start_date + timedelta(days=10), 'label': 'Started Exercise Plan', 'type': 'milestone'},
            {'time': start_date + timedelta(days=20), 'label': 'Medication Change', 'type': 'medication'},
            {'time': start_date + timedelta(days=35), 'label': 'Achieved Goal', 'type': 'milestone'},
            {'time': start_date + timedelta(days=45), 'label': 'Health Check', 'type': 'default'}
        ]
        
        data = {
            'background_metrics': background_metrics,
            'events': events
        }
        
        config = {
            'title': 'Health Timeline',
            'subtitle': 'Key events and metric trends',
            'metric_label': 'Daily Average'
        }
        
        # Create visualization
        static_fig = self.export_factory.create_chart('timeline', data, config)
        static_widget = MatplotlibChartWidget(static_fig)
        self.tab_widget.addTab(static_widget, "Timeline View")
    
    def _show_cyclical_patterns(self):
        """Show cyclical pattern visualizations."""
        self.tab_widget.clear()
        
        # Get hourly pattern data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Get heart rate data for daily pattern
        hr_data = self.data_source.get_metric_data('heart_rate', (start_date, end_date))
        
        if hr_data is not None and not hr_data.empty:
            # Calculate average by hour of day
            hr_data['hour'] = hr_data.index.hour
            hourly_avg = hr_data.groupby('hour').mean()
            
            # Ensure we have 24 hours
            full_hours = pd.DataFrame(index=range(24))
            hourly_pattern = full_hours.join(hourly_avg).fillna(method='ffill').fillna(method='bfill')
            
            config = {
                'title': 'Daily Heart Rate Pattern',
                'pattern_type': 'daily',
                'figure_size': (8, 8)
            }
            
            # Create polar chart
            static_fig = self.export_factory.create_chart('polar', hourly_pattern, config)
            static_widget = MatplotlibChartWidget(static_fig)
            self.tab_widget.addTab(static_widget, "Daily Pattern")
    
    def _show_comparative(self):
        """Show comparative analysis visualizations."""
        self.tab_widget.clear()
        
        # Create bump chart showing metric rankings over weeks
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=8)
        
        # Get weekly averages for multiple metrics
        metrics = ['steps', 'active_energy', 'distance', 'stand_hours']
        available_metrics = self.data_source.get_available_metrics()
        
        weekly_data = {}
        for metric in metrics:
            if metric not in available_metrics:
                continue
            
            metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
            if metric_data is not None and not metric_data.empty:
                # Normalize to 0-100 scale for comparison
                weekly = metric_data.resample('W').mean()
                normalized = (weekly - weekly.min()) / (weekly.max() - weekly.min()) * 100
                weekly_data[metric] = normalized.iloc[:, 0]
        
        if weekly_data:
            df = pd.DataFrame(weekly_data)
            
            config = {
                'title': 'Metric Performance Rankings',
                'subtitle': 'Weekly relative performance (normalized)',
                'figure_size': (12, 8)
            }
            
            static_fig = self.export_factory.create_chart('bump_chart', df, config)
            static_widget = MatplotlibChartWidget(static_fig)
            self.tab_widget.addTab(static_widget, "Ranking Comparison")
    
    def _show_distribution(self):
        """Show distribution comparison visualizations."""
        self.tab_widget.clear()
        
        # Get monthly distributions for a metric
        end_date = datetime.now()
        
        # Get steps data for last 3 months
        monthly_distributions = []
        month_labels = []
        
        for i in range(3):
            month_end = end_date - timedelta(days=30*i)
            month_start = month_end - timedelta(days=30)
            
            steps_data = self.data_source.get_metric_data('steps', (month_start, month_end))
            if steps_data is not None and not steps_data.empty:
                monthly_distributions.append(steps_data.iloc[:, 0].values)
                month_labels.append(month_end.strftime('%B'))
        
        if monthly_distributions:
            config = {
                'title': 'Monthly Steps Distribution',
                'subtitle': 'Comparing daily step counts across months',
                'labels': month_labels[::-1],
                'y_label': 'Steps',
                'show_means': True
            }
            
            static_fig = self.export_factory.create_chart('box_plot', 
                                                        monthly_distributions[::-1], 
                                                        config)
            static_widget = MatplotlibChartWidget(static_fig)
            self.tab_widget.addTab(static_widget, "Distribution Comparison")
    
    def _show_waterfall(self):
        """Show waterfall chart visualization."""
        self.tab_widget.clear()
        
        # Calculate week-over-week changes for a metric
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=8)
        
        steps_data = self.data_source.get_metric_data('steps', (start_date, end_date))
        
        if steps_data is not None and not steps_data.empty:
            # Calculate weekly totals
            weekly_totals = steps_data.resample('W').sum()
            
            # Calculate week-over-week changes
            changes = weekly_totals.diff().dropna()
            changes.index = [f"Week {i+1}" for i in range(len(changes))]
            
            config = {
                'title': 'Weekly Steps Changes',
                'subtitle': 'Week-over-week progress',
                'y_label': 'Steps Change'
            }
            
            static_fig = self.export_factory.create_chart('waterfall', changes, config)
            static_widget = MatplotlibChartWidget(static_fig)
            self.tab_widget.addTab(static_widget, "Progress Waterfall")
    
    def _show_no_data_message(self):
        """Show message when no data is available."""
        message = QLabel("No data available for visualization")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet(f"""
            color: {self.style_manager.WARM_PALETTE['text_secondary']};
            font-size: 16px;
            padding: 40px;
        """)
        self.tab_widget.addTab(message, "No Data")
    
    def _show_error_message(self, error: str):
        """Show error message."""
        message = QLabel(f"Error: {error}")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet(f"""
            color: {self.style_manager.WARM_PALETTE['negative']};
            font-size: 14px;
            padding: 40px;
        """)
        self.tab_widget.addTab(message, "Error")
    
    def _show_drill_down(self):
        """Show drill-down explorer."""
        self.tab_widget.clear()
        
        # Create drill-down widget if not exists
        if not self.drill_down_widget:
            self.drill_down_widget = ProgressiveDrillDownWidget(
                self.style_manager,
                self.interactive_factory
            )
            
            # Connect signals
            self.drill_down_widget.selectionChanged.connect(
                lambda sel: logger.info(f"Drill-down selection: {sel}")
            )
        
        # Get a metric for drill-down
        available_metrics = self.data_source.get_available_metrics()
        if available_metrics:
            # Use steps as default metric
            metric = 'steps' if 'steps' in available_metrics else available_metrics[0]
            
            # Get data for last year
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            metric_data = self.data_source.get_metric_data(metric, (start_date, end_date))
            
            if metric_data is not None and not metric_data.empty:
                self.drill_down_widget.load_data(metric_data, metric)
                self.tab_widget.addTab(self.drill_down_widget, "Drill-Down Explorer")
                
                # Store current state
                self.current_chart_type = 'drill_down'
                self.current_data = metric_data
                self.current_config = {'metric': metric}
            else:
                self._show_no_data_message()
        else:
            self._show_no_data_message()
    
    def _share_dashboard(self):
        """Share the current dashboard view."""
        if not self.current_data or not self.current_chart_type:
            QMessageBox.warning(self, "No Dashboard", "Please create a visualization first")
            return
        
        # Get current view configuration
        view_config = {
            'chart_type': self.current_chart_type,
            'chart_config': self.current_config,
            'timestamp': datetime.now().isoformat()
        }
        
        # If drill-down widget, get its specific config
        if self.current_chart_type == 'drill_down' and self.drill_down_widget:
            view_config['drill_down_state'] = self.drill_down_widget.get_current_view_config()
        
        # Show share dialog
        dialog = ShareDashboardDialog(view_config, self.style_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            share_config = dialog.get_share_config()
            
            # Create share link
            share_link = self.share_manager.create_share(view_config, share_config)
            
            # Show link to user
            link_dialog = ShareLinkDisplay(share_link, self.style_manager, self)
            link_dialog.exec()
    
    def _export_chart(self, format: str = 'png'):
        """Export the current chart."""
        if not self.current_data or not self.current_chart_type:
            QMessageBox.warning(self, "No Chart", "No chart to export")
            return
        
        # Get file name from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            f"health_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            f"{format.upper()} Files (*.{format})"
        )
        
        if not file_path:
            return
        
        # Ensure correct extension
        if not file_path.endswith(f'.{format}'):
            file_path += f'.{format}'
        
        try:
            # Create high-quality export
            chart_bytes = self.create_export_chart(
                self.current_chart_type,
                self.current_data,
                self.current_config,
                format
            )
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(chart_bytes)
            
            # Emit signal
            self.chartExported.emit(file_path)
            
            QMessageBox.information(self, "Export Successful", 
                                  f"Chart exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting chart: {e}")
            QMessageBox.critical(self, "Export Failed", 
                               f"Failed to export chart: {str(e)}")
    
    def set_drill_down_enabled(self, enabled: bool):
        """Enable/disable drill-down functionality."""
        self.drill_down_enabled = enabled
        if self.drill_down_widget:
            self.drill_down_widget.setEnabled(enabled)
    
    def set_date_selection_enabled(self, enabled: bool):
        """Enable/disable date selection."""
        self.date_selection_enabled = enabled
        # Apply to relevant widgets
    
    def set_anonymized_mode(self, enabled: bool):
        """Enable/disable anonymized mode."""
        self.anonymized_mode = enabled
        # Apply anonymization to displayed data
    
    def get_current_view_config(self) -> Dict[str, Any]:
        """Get current view configuration for sharing/saving."""
        config = {
            'chart_type': self.current_chart_type,
            'chart_config': self.current_config,
            'selected_tab': self.tab_widget.currentIndex() if self.tab_widget.count() > 0 else 0
        }
        
        if self.current_chart_type == 'drill_down' and self.drill_down_widget:
            config['drill_down_state'] = self.drill_down_widget.get_current_view_config()
        
        return config
    
    def restore_view_config(self, config: Dict[str, Any]):
        """Restore a saved view configuration."""
        chart_type = config.get('chart_type')
        if chart_type:
            # Find and select the chart type
            index = self.chart_selector.findText(chart_type.replace('_', ' ').title())
            if index >= 0:
                self.chart_selector.setCurrentIndex(index)
        
        # Restore drill-down state if applicable
        if chart_type == 'drill_down' and 'drill_down_state' in config and self.drill_down_widget:
            self.drill_down_widget.restore_view_config(config['drill_down_state'])
    
    def set_accessibility_mode(self, enabled: bool):
        """Enable/disable accessibility features."""
        if enabled:
            # Increase font sizes
            # Add high contrast mode
            # Enable keyboard navigation hints
            pass