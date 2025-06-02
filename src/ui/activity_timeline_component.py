"""
Activity Timeline Component for health data visualization.
Displays hourly breakdown with radial and linear views, ML clustering, and interactive features.
Inspired by Wall Street Journal visualization style.
"""

import logging
import math
import time
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from .comparison_overlay_widget import ComparisonOverlayWidget
from .timeline_insights_panel import TimelineInsightsPanel
from ..analytics.timeline_analytics_worker import TimelineAnalyticsWorker

warnings.filterwarnings('ignore', category=UserWarning)


class ActivityTimelineComponent(QWidget):
    """Main component for activity timeline visualization."""
    
    # Signals
    time_range_selected = pyqtSignal(datetime, datetime)
    pattern_detected = pyqtSignal(str, dict)
    
    # Animation constants (per UI specs: <300ms)
    ANIMATION_DURATION = 250  # milliseconds
    TRANSITION_DURATION = 200  # milliseconds for transitions
    
    # Color palette from UI specifications  
    COLORS = {
        'background': '#FFFFFF',      # White background (changed from tan)
        'grid': '#E0E0E0',            # Light gray (changed from brown)
        'text': '#2C3E50',            # Dark text (changed from dark brown)
        'primary': '#FF8C42',         # Warm orange - primary accent
        'secondary': '#FFD166',       # Soft yellow - secondary accent
        'accent': '#95C17B',          # Soft green - success
        'heat_low': '#FFF8F0',        # Light cream
        'heat_high': '#FF8C42',       # Warm orange for intensity
        'inactive': '#F5F5F5',        # Light gray (changed from gray-brown)
        'chart_blue': '#6C9BD1',      # Blue from chart palette
        'chart_purple': '#B79FCB'     # Purple from chart palette
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.data = None
        self.view_mode = 'linear'  # 'linear' or 'radial'
        self.time_grouping = 60  # minutes (15, 30, 60)
        self.selected_metrics = []
        self.clustering_enabled = False
        self.show_patterns = True
        self.show_correlations = False
        
        # ML components
        self.scaler = StandardScaler()
        self.kmeans = None
        self.dbscan = None
        self.clusters = None
        self.anomalies = None
        
        # Interaction state
        self.brush_start = None
        self.brush_end = None
        self.is_brushing = False
        
        # Comparison overlays
        self.comparison_overlays_enabled = True
        self.overlay_widget = None
        
        # Background analytics worker
        self.analytics_worker = TimelineAnalyticsWorker()
        self.analytics_worker.progress_updated.connect(self.on_analytics_progress)
        self.analytics_worker.insights_ready.connect(self.on_insights_ready)
        self.analytics_worker.error_occurred.connect(self.on_analytics_error)
        self.analytics_worker.finished.connect(self.on_analytics_finished)
        
        # Progress tracking
        self.is_processing = False
        self.current_date = None
        
        # Initialize grouped_data attribute
        self.grouped_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        # Title (using Poppins for display)
        title = QLabel("Activity Timeline")
        title_font = QFont("Poppins", 16, QFont.Weight.Bold)
        # setFallbackFamilies is not available in PyQt6, use setFamilies instead
        if hasattr(title_font, 'setFamilies'):
            title_font.setFamilies(["Poppins", "Segoe UI", "sans-serif"])
        elif hasattr(title_font, 'setFamily'):
            # Fallback for older Qt versions
            title_font.setFamily("Poppins")
        title.setFont(title_font)
        title.setStyleSheet(f"color: {self.COLORS['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # # View mode selector
        # view_group = QButtonGroup(self)
        # linear_btn = QRadioButton("Linear", self)
        # radial_btn = QRadioButton("Radial", self)
        # linear_btn.setChecked(True)
        
        # linear_btn.toggled.connect(lambda checked: self.set_view_mode('linear') if checked else None)
        # radial_btn.toggled.connect(lambda checked: self.set_view_mode('radial') if checked else None)
        
        # view_group.addButton(linear_btn)
        # view_group.addButton(radial_btn)
        
        # view_label = QLabel("View:", self)
        # header_layout.addWidget(view_label)
        # header_layout.addWidget(linear_btn)
        # header_layout.addWidget(radial_btn)
        
        # Time grouping selector
        group_label = QLabel("Group by:", self)
        header_layout.addWidget(group_label)
        self.time_combo = QComboBox(self)
        self.time_combo.addItems(["15 minutes", "30 minutes", "1 hour"])
        self.time_combo.setCurrentIndex(2)
        self.time_combo.currentIndexChanged.connect(self.on_time_grouping_changed)
        header_layout.addWidget(self.time_combo)
        
        layout.addLayout(header_layout)
        
        # Options bar
        options_layout = QHBoxLayout()
        
        self.cluster_check = QCheckBox("Enable Clustering", self)
        self.cluster_check.setChecked(True)
        self.cluster_check.stateChanged.connect(self.on_clustering_toggled)
        options_layout.addWidget(self.cluster_check)
        
        self.patterns_check = QCheckBox("Highlight Patterns", self)
        self.patterns_check.setChecked(True)
        self.patterns_check.stateChanged.connect(self.on_patterns_toggled)
        options_layout.addWidget(self.patterns_check)
        
        self.correlations_check = QCheckBox("Show Correlations", self)
        self.correlations_check.setChecked(True)
        self.correlations_check.stateChanged.connect(self.on_correlations_toggled)
        options_layout.addWidget(self.correlations_check)
        
        self.overlays_check = QCheckBox("Comparison Overlays", self)
        self.overlays_check.setChecked(True)
        self.overlays_check.stateChanged.connect(self.on_overlays_toggled)
        options_layout.addWidget(self.overlays_check)
        
        options_layout.addStretch()
        
        # Progress indicator
        self.progress_label = QLabel("", self)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #FF8C42;
                font-style: italic;
                padding: 0 10px;
            }
        """)
        self.progress_label.setVisible(False)
        options_layout.addWidget(self.progress_label)
        
        layout.addLayout(options_layout)
        
        # Main visualization area
        self.viz_widget = TimelineVisualizationWidget(self)
        self.viz_widget.setMinimumHeight(400)  # Reduced to make room for insights panel
        self.viz_widget.hide()  # Hide since insights panel replaces this functionality
        layout.addWidget(self.viz_widget)
        
        # New Timeline Insights Panel
        self.insights_panel = TimelineInsightsPanel(self)
        self.insights_panel.setMinimumHeight(800)  # Increased from 400 - give more space to insights
        self.insights_panel.insight_clicked.connect(self.on_insight_clicked)
        layout.addWidget(self.insights_panel)
        
        # Apply styling with proper fonts
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLORS['background']};
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
            }}
            QGroupBox {{
                border: 1px solid {self.COLORS['grid']};
                border-radius: 4px;
                margin-top: 0.5em;
                font-weight: bold;
                color: {self.COLORS['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QComboBox, QPushButton {{
                border: 1px solid {self.COLORS['grid']};
                padding: 4px 8px;
                background-color: white;
                border-radius: 2px;
            }}
            QComboBox:hover, QPushButton:hover {{
                border-color: {self.COLORS['primary']};
            }}
            QCheckBox {{
                color: {self.COLORS['text']};
            }}
            QRadioButton {{
                color: {self.COLORS['text']};
            }}
        """)
        
    def set_view_mode(self, mode: str):
        """Switch between linear and radial views."""
        if mode in ['linear', 'radial']:
            self.view_mode = mode
            self.viz_widget.update()
            
    def on_time_grouping_changed(self, index: int):
        """Handle time grouping changes."""
        groupings = [15, 30, 60]
        self.time_grouping = groupings[index]
        # Re-process data with new grouping
        if self.data is not None:
            self.update_data(self.data, self.selected_metrics)
        
    def on_clustering_toggled(self, state: int):
        """Toggle ML clustering."""
        self.clustering_enabled = state == Qt.CheckState.Checked.value
        # Analytics will be applied based on this setting in the worker
        if hasattr(self, 'viz_widget') and self.viz_widget:
            self.viz_widget.update()
        
    def on_patterns_toggled(self, state: int):
        """Toggle pattern highlighting."""
        self.show_patterns = state == Qt.CheckState.Checked.value
        self.viz_widget.update()
        
    def on_correlations_toggled(self, state: int):
        """Toggle correlation display."""
        self.show_correlations = state == Qt.CheckState.Checked.value
        self.viz_widget.update()
        
    def on_overlays_toggled(self, state: int):
        """Toggle comparison overlays display."""
        self.comparison_overlays_enabled = state == Qt.CheckState.Checked.value
        self.viz_widget.update()
        
    def update_data(self, data: pd.DataFrame, metrics: List[str]):
        """
        Update the timeline with new data.
        
        Args:
            data: DataFrame with datetime index and metric columns
            metrics: List of metric names to visualize
        """
        self.data = data
        self.selected_metrics = metrics
        
        # Cancel any ongoing analytics
        if self.analytics_worker.isRunning():
            self.analytics_worker.cancel()
            self.analytics_worker.wait()
            
        # Store current date for cache key
        if data is not None and not data.empty:
            self.current_date = data.index[0].strftime('%Y-%m-%d')
            
        # Process data immediately for basic visualization
        self.update_data_immediate()
        
        # Start background analytics
        self.start_analytics()
        
    def update_data_immediate(self):
        """Process basic data immediately for quick visualization."""
        if self.data is None or self.data.empty:
            return
            
        # Group data by time intervals
        self.grouped_data = self.aggregate_by_time_interval()
        
        # Reset analytics results
        self.active_periods = []
        self.rest_periods = []
        self.clusters = None
        self.anomalies = None
        self.correlations = None
        self.lagged_correlations = {}
        
        # Update visualization with basic data
        if hasattr(self, 'viz_widget') and self.viz_widget:
            self.viz_widget.update()
            
        # Show loading state in insights panel
        if hasattr(self, 'insights_panel'):
            self.insights_panel.show_loading_state()
            
    def start_analytics(self):
        """Start background analytics processing."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Set processing flag
        self.is_processing = True
        
        # Show progress indicator
        if hasattr(self, 'progress_label'):
            self.progress_label.setText("Analyzing...")
            self.progress_label.setVisible(True)
            
        # Configure worker with data
        self.analytics_worker.set_data(
            self.grouped_data,
            self.selected_metrics,
            self.current_date or datetime.now().strftime('%Y-%m-%d')
        )
        
        # Start background processing
        self.analytics_worker.start()
        
    def process_data(self):
        """Legacy method for compatibility - redirects to new implementation."""
        self.update_data_immediate()
        self.start_analytics()
        
    def aggregate_by_time_interval(self) -> pd.DataFrame:
        """Aggregate data by the selected time interval."""
        if self.data is None:
            return pd.DataFrame()
            
        # Create time-based groups
        freq_map = {15: '15min', 30: '30min', 60: 'h'}
        freq = freq_map[self.time_grouping]
        
        # Windows workaround: Process each metric separately to avoid access violation
        # This prevents the pandas Cython operation crash with sparse data
        result_dfs = []
        
        for metric in self.selected_metrics:
            if metric in self.data.columns:
                try:
                    # Resample each metric individually
                    # Create a deep copy to avoid Windows access violation issues
                    metric_series = self.data[metric].copy(deep=True)
                    
                    # Convert to float64 to ensure numeric stability
                    metric_series = metric_series.astype('float64')
                    
                    # Create new DataFrame with the processed series
                    metric_data = pd.DataFrame({metric: metric_series}, index=self.data.index)
                    
                    # Handle sparse data by filling NaN values before resampling on Windows
                    # This prevents access violations in pandas' Cython code
                    if metric_series.isna().any():
                        # Use interpolation for smoother results, with fallback to forward/backward fill
                        metric_series = metric_series.interpolate(method='linear', limit_direction='both')
                        # Fill any remaining NaN values
                        metric_series = metric_series.fillna(0)
                        # Update DataFrame with cleaned series
                        metric_data[metric] = metric_series
                    
                    # Use groupby instead of resample to avoid Cython issues on Windows
                    # This is more stable for sparse data
                    # NOTE: Do NOT call gc.collect() here - it causes access violations on Windows
                    grouper = pd.Grouper(freq=freq, closed='left', label='left')
                    grouped = metric_data.groupby(grouper)
                    
                    # Calculate aggregations using groupby operations
                    mean_values = grouped[metric].mean()
                    sum_values = grouped[metric].sum()
                    count_values = grouped[metric].count()
                    
                    # Create result DataFrame with MultiIndex columns
                    metric_result = pd.DataFrame({
                        (metric, 'mean'): mean_values,
                        (metric, 'sum'): sum_values,
                        (metric, 'count'): count_values
                    })
                    
                    result_dfs.append(metric_result)
                except Exception as e:
                    # Handle any remaining issues gracefully
                    self.logger.warning(f"Failed to aggregate {metric}: {e}")
                    continue
        
        if result_dfs:
            # Combine all metrics with copy to avoid Windows memory issues
            grouped = pd.concat(result_dfs, axis=1, copy=True)
            # Ensure multi-level column structure
            if not isinstance(grouped.columns, pd.MultiIndex):
                grouped.columns = pd.MultiIndex.from_tuples(grouped.columns)
            return grouped
        else:
            return pd.DataFrame()
        
    def detect_activity_patterns(self):
        """Detect active vs rest periods using statistical methods."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Calculate activity scores using vectorized operations (safer on Windows)
        activity_scores = pd.Series(0, index=self.grouped_data.index, dtype='float64')
        
        # Sum up mean values for each metric
        for metric in self.selected_metrics:
            if (metric, 'mean') in self.grouped_data.columns:
                metric_values = self.grouped_data[(metric, 'mean')].fillna(0)
                activity_scores = activity_scores + metric_values
            
        # Determine thresholds
        scores_array = np.array(activity_scores)
        if len(scores_array) > 0:
            threshold = np.percentile(scores_array, 25)
            
            # Classify periods using boolean indexing (vectorized)
            active_mask = activity_scores > threshold
            
            # Extract periods using boolean indexing
            active_indices = self.grouped_data.index[active_mask]
            active_scores = activity_scores[active_mask]
            self.active_periods = list(zip(active_indices, active_scores))
            
            rest_indices = self.grouped_data.index[~active_mask]
            rest_scores = activity_scores[~active_mask]
            self.rest_periods = list(zip(rest_indices, rest_scores))
                    
    def perform_clustering(self):
        """Perform ML clustering on activity patterns."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Prepare features for clustering
        features = []
        for idx, row in self.grouped_data.iterrows():
            feature_vec = []
            for metric in self.selected_metrics:
                if (metric, 'mean') in row.index:
                    value = row[(metric, 'mean')]
                    feature_vec.append(value if pd.notna(value) else 0)
            
            # Add temporal features
            hour = idx.hour
            feature_vec.extend([
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24)
            ])
            features.append(feature_vec)
            
        if not features:
            return
            
        # Scale features
        X = np.array(features)
        try:
            X_scaled = self.scaler.fit_transform(X)
            
            # K-means clustering
            n_clusters = min(4, len(X))  # Adaptive cluster count
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.clusters = self.kmeans.fit_predict(X_scaled)
            
            # DBSCAN for anomaly detection
            self.dbscan = DBSCAN(eps=0.5, min_samples=3)
            anomaly_labels = self.dbscan.fit_predict(X_scaled)
            self.anomalies = anomaly_labels == -1
            
        except Exception as e:
            print(f"Clustering error: {e}")
            self.clusters = None
            self.anomalies = None
            
    def calculate_correlations(self):
        """Calculate correlations between metrics."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Extract metric values
        metric_data = {}
        for metric in self.selected_metrics:
            if (metric, 'mean') in self.grouped_data.columns:
                metric_data[metric] = self.grouped_data[(metric, 'mean')].fillna(0)
                
        if len(metric_data) < 2:
            self.correlations = None
            return
            
        # Convert to DataFrame and calculate correlations
        metrics_df = pd.DataFrame(metric_data)
        self.correlations = metrics_df.corr()
        
        # Calculate time-lagged correlations
        self.lagged_correlations = {}
        for lag in [1, 2, 3]:  # Check correlations with 1-3 time period lags
            lagged_corr = {}
            for m1 in self.selected_metrics:
                for m2 in self.selected_metrics:
                    if m1 != m2 and m1 in metrics_df and m2 in metrics_df:
                        # Calculate correlation with lag
                        corr = metrics_df[m1].corr(metrics_df[m2].shift(lag))
                        if not np.isnan(corr):
                            lagged_corr[f"{m1}_vs_{m2}_lag{lag}"] = corr
            self.lagged_correlations[lag] = lagged_corr
            
    def update_info_panel(self):
        """Update the insights panel with transformed analytics data."""
        # Update the new insights panel with user-friendly visualizations
        if hasattr(self, 'insights_panel'):
            self.insights_panel.update_insights(
                self.clusters,
                self.anomalies,
                self.grouped_data,
                self.selected_metrics
            )
            
    def on_insight_clicked(self, insight_type: str, details: dict):
        """Handle clicks on insight items."""
        self.logger.info(f"Insight clicked: {insight_type}, details: {details}")
        # Emit signal or handle interaction as needed
        if insight_type == 'pattern':
            self.pattern_detected.emit(details['name'], details)
        elif insight_type == 'anomaly':
            # Could show more details or allow user to add notes
            pass
        elif insight_type == 'heatmap':
            # Could zoom to specific time period
            pass
            
    def on_analytics_progress(self, percentage: int, message: str):
        """Handle progress updates from analytics worker."""
        if hasattr(self, 'progress_label'):
            self.progress_label.setText(f"{message} ({percentage}%)")
            
    def on_insights_ready(self, insight_type: str, data: dict):
        """Handle progressive insights from analytics worker."""
        if insight_type == "patterns":
            self.active_periods = data.get("active_periods", [])
            self.rest_periods = data.get("rest_periods", [])
            
        elif insight_type == "clustering":
            clusters = data.get("clusters")
            anomalies = data.get("anomalies")
            if clusters is not None:
                self.clusters = np.array(clusters) if isinstance(clusters, list) else clusters
            if anomalies is not None:
                self.anomalies = np.array(anomalies) if isinstance(anomalies, list) else anomalies
                
        elif insight_type == "correlations":
            corr_data = data.get("correlations")
            if corr_data is not None:
                self.correlations = pd.DataFrame(corr_data)
            self.lagged_correlations = data.get("lagged_correlations", {})
            
        # Update visualizations progressively
        if hasattr(self, 'viz_widget') and self.viz_widget:
            self.viz_widget.update()
            
        # Update insights panel progressively
        if hasattr(self, 'insights_panel'):
            self.insights_panel.update_insights(
                self.clusters,
                self.anomalies,
                self.grouped_data,
                self.selected_metrics
            )
            
    def on_analytics_error(self, error_message: str):
        """Handle analytics processing errors."""
        self.logger.error(f"Analytics error: {error_message}")
        self.is_processing = False
        
        # Hide progress indicator
        if hasattr(self, 'progress_label'):
            self.progress_label.setVisible(False)
            
        # Show error state in insights panel
        if hasattr(self, 'insights_panel'):
            self.insights_panel.show_error_state(error_message)
            
    def on_analytics_finished(self):
        """Handle analytics processing completion."""
        self.is_processing = False
        
        # Hide progress indicator
        if hasattr(self, 'progress_label'):
            self.progress_label.setVisible(False)
            
        self.logger.info("Analytics processing completed")
            
    def __del__(self):
        """Clean up resources when widget is destroyed."""
        # Stop and clean up worker thread
        if hasattr(self, 'analytics_worker'):
            if self.analytics_worker.isRunning():
                self.analytics_worker.cancel()
                self.analytics_worker.wait()


class TimelineVisualizationWidget(QWidget):
    """Custom widget for rendering timeline visualizations."""
    
    def __init__(self, parent: ActivityTimelineComponent):
        super().__init__(parent)
        self.timeline = parent
        self.setMinimumHeight(400)
        self.setMouseTracking(True)
        
        # Matplotlib figure for linear view - increased size
        self.figure = Figure(figsize=(12, 6), facecolor=parent.COLORS['background'])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Initialize comparison overlay widget
        self.overlay_widget = None
        
    def paintEvent(self, event):
        """Custom paint event for radial visualization."""
        if self.timeline.view_mode == 'radial':
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.draw_radial_timeline(painter)
            self.canvas.hide()
        else:
            self.canvas.show()
            self.draw_linear_timeline()
            
    def draw_linear_timeline(self):
        """Draw linear timeline using matplotlib."""
        import time
        start_time = time.time()
        
        self.figure.clear()
        
        if not hasattr(self.timeline, 'grouped_data') or self.timeline.grouped_data is None or self.timeline.grouped_data.empty:
            # Draw empty state message
            ax = self.figure.add_subplot(111)
            ax.set_facecolor(self.timeline.COLORS['background'])
            ax.text(0.5, 0.5, 'No data available for the selected time range', 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=14, color=self.timeline.COLORS['text'])
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
            
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(self.timeline.COLORS['background'])
        
        # Style axis
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.timeline.COLORS['grid'])
        ax.spines['bottom'].set_color(self.timeline.COLORS['grid'])
        ax.tick_params(colors=self.timeline.COLORS['text'])
        
        # Prepare data
        times = self.timeline.grouped_data.index
        
        # Plot each metric with improved visibility
        metric_height = 0.8  # Height of each metric bar
        metric_spacing = 1.0  # Spacing between metrics
        
        # Create a colormap for each metric
        metric_colors = {
            'steps': '#FF8C42',      # Warm orange
            'heart_rate': '#6C9BD1',  # Blue
            'active_calories': '#95C17B'  # Green
        }
        
        for i, metric in enumerate(self.timeline.selected_metrics):
            if (metric, 'mean') in self.timeline.grouped_data.columns:
                values = self.timeline.grouped_data[(metric, 'mean')].fillna(0)
                
                # Get base color for this metric
                base_color = metric_colors.get(metric, self.timeline.COLORS['primary'])
                
                # Plot as a line chart with filled area
                y_base = i * metric_spacing
                y_values = values / values.max() * metric_height if values.max() > 0 else values
                
                # Create x values for plotting
                x_values = [mdates.date2num(t) for t in times]
                
                # Plot filled area
                ax.fill_between(x_values, y_base, y_base + y_values, 
                              color=base_color, alpha=0.6, label=metric)
                
                # Plot line on top
                ax.plot(x_values, y_base + y_values, color=base_color, 
                       linewidth=2, alpha=0.9)
                
                # Add metric label on the left
                ax.text(ax.get_xlim()[0] - 0.01, y_base + metric_height/2, metric,
                       ha='right', va='center', fontsize=10, 
                       color=self.timeline.COLORS['text'],
                       transform=ax.get_yaxis_transform())
        
        # Set y-axis limits
        ax.set_ylim(-0.2, len(self.timeline.selected_metrics) * metric_spacing)
                        
        # Show cluster assignments if clustering is enabled
        if self.timeline.clustering_enabled and self.timeline.clusters is not None:
            # Create cluster color map
            cluster_colors = ['#6C9BD1', '#B79FCB', '#95C17B', '#FFD166']  # Chart palette colors
            
            # Draw cluster backgrounds
            for j, (time, cluster) in enumerate(zip(times, self.timeline.clusters)):
                if cluster >= 0:  # Valid cluster (not noise)
                    color = cluster_colors[cluster % len(cluster_colors)]
                    ax.axvspan(
                        mdates.date2num(time),
                        mdates.date2num(time + timedelta(minutes=self.timeline.time_grouping)),
                        alpha=0.1,
                        color=color,
                        zorder=0
                    )
        
        # Highlight anomalies if enabled
        if self.timeline.show_patterns and self.timeline.anomalies is not None:
            anomaly_times = []
            for j, (time, is_anomaly) in enumerate(zip(times, self.timeline.anomalies)):
                if is_anomaly:
                    anomaly_times.append(time)
                    # Draw red border around anomaly periods
                    ax.axvspan(
                        mdates.date2num(time),
                        mdates.date2num(time + timedelta(minutes=self.timeline.time_grouping)),
                        alpha=0.3,
                        color='red',
                        edgecolor='red',
                        linewidth=2,
                        zorder=10
                    )
            
            # Add anomaly markers at the top
            if anomaly_times:
                for anom_time in anomaly_times:
                    ax.annotate('⚠', xy=(mdates.date2num(anom_time), ax.get_ylim()[1]*0.95),
                              fontsize=16, color='red', ha='center', va='top')
                    
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        
        # Labels
        ax.set_xlabel('Time of Day', fontsize=11, color=self.timeline.COLORS['text'])
        ax.set_ylabel('Metrics', fontsize=11, color=self.timeline.COLORS['text'])
        ax.set_title('24-Hour Activity Pattern with Clustering Analysis', fontsize=14, fontweight='bold', 
                     color=self.timeline.COLORS['text'], pad=20)
        
        # Hide y-axis ticks since we're using custom labels
        ax.set_yticks([])
        
        # Grid
        ax.grid(True, axis='y', linestyle=':', color=self.timeline.COLORS['grid'], alpha=0.5)
        
        # Add legend for clusters if enabled
        if self.timeline.clustering_enabled and self.timeline.clusters is not None:
            from matplotlib.patches import Patch
            cluster_colors = ['#6C9BD1', '#B79FCB', '#95C17B', '#FFD166']
            unique_clusters = np.unique(self.timeline.clusters[self.timeline.clusters >= 0])
            legend_elements = []
            
            for cluster in unique_clusters:
                color = cluster_colors[cluster % len(cluster_colors)]
                legend_elements.append(Patch(facecolor=color, alpha=0.3, label=f'Cluster {cluster + 1}'))
            
            if self.timeline.anomalies is not None and np.any(self.timeline.anomalies):
                legend_elements.append(Patch(facecolor='red', alpha=0.3, label='Anomaly'))
            
            if legend_elements:
                ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
                         facecolor='white', edgecolor=self.timeline.COLORS['grid'])
        
        # Show correlations if enabled
        if self.timeline.show_correlations and hasattr(self.timeline, 'correlations') and self.timeline.correlations is not None:
            # Add correlation text
            corr_text = "Correlations:\n"
            for i, m1 in enumerate(self.timeline.selected_metrics):
                for j, m2 in enumerate(self.timeline.selected_metrics):
                    if i < j:  # Only show upper triangle
                        corr_val = self.timeline.correlations.loc[m1, m2]
                        if abs(corr_val) > 0.5:  # Only show strong correlations
                            corr_text += f"{m1} ↔ {m2}: {corr_val:.2f}\n"
                            
            # Add text annotation
            ax.text(0.02, 0.98, corr_text, transform=ax.transAxes,
                   verticalalignment='top', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                   fontsize=9, color=self.timeline.COLORS['text'])
        
        # Add comparison overlays if enabled
        if self.timeline.comparison_overlays_enabled and self.timeline.view_mode == 'linear':
            self.add_comparison_overlays(ax)
        
        # Adjust layout
        self.figure.tight_layout()
        self.canvas.draw()
        
        # Performance monitoring
        render_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if render_time > 500:
            print(f"Warning: Chart rendering took {render_time:.2f}ms (target: <500ms)")
        else:
            print(f"Chart rendered in {render_time:.2f}ms")
            
    def add_comparison_overlays(self, ax):
        """Add comparison overlays to the linear chart."""
        try:
            # Initialize overlay widget if not already done
            if self.overlay_widget is None:
                self.overlay_widget = ComparisonOverlayWidget(self.figure, ax, self)
                # Add to layout
                layout = self.layout()
                layout.addWidget(self.overlay_widget)
                
            # Update chart styling for WSJ aesthetic
            self.overlay_widget.update_chart_style()
            
            # Clear existing overlays
            self.overlay_widget.clear_all_overlays()
            
            # Get current data for overlays
            if (self.timeline.data is not None and 
                not self.timeline.data.empty and 
                self.timeline.selected_metrics):
                
                current_date = datetime.now()
                
                # Add overlays for each selected metric
                for metric in self.timeline.selected_metrics:
                    if metric in self.timeline.data.columns:
                        metric_data = self.timeline.data[metric].dropna()
                        
                        if len(metric_data) > 0:
                            # Add weekly average overlay
                            self.overlay_widget.add_weekly_average_overlay(metric_data, current_date)
                            
                            # Add monthly average overlay
                            self.overlay_widget.add_monthly_average_overlay(metric_data, current_date)
                            
                            # Add personal best overlay (assuming higher is better for most health metrics)
                            higher_is_better = metric.lower() not in ['weight', 'body_fat', 'resting_heart_rate']
                            self.overlay_widget.add_personal_best_overlay(
                                metric_data, metric, higher_is_better
                            )
                            
                            # Add historical comparison overlays
                            self.overlay_widget.add_historical_comparison_overlays(
                                metric_data, current_date, ['week', 'month']
                            )
                            
        except Exception as e:
            self.timeline.logger.error(f"Error adding comparison overlays: {e}")
        
    def draw_radial_timeline(self, painter: QPainter):
        """Draw radial (clock face) timeline."""
        # Get widget dimensions
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(center_x, center_y) - 50
        
        # Draw clock face background
        painter.setBrush(QBrush(QColor(self.timeline.COLORS['background'])))
        painter.setPen(QPen(QColor(self.timeline.COLORS['grid']), 1))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw hour marks and labels
        font = QFont("Inter", 10)
        font.setFallbackFamilies(["Segoe UI", "sans-serif"])
        painter.setFont(font)
        painter.setPen(QPen(QColor(self.timeline.COLORS['text']), 1))
        
        for hour in range(24):
            angle = (hour - 6) * 15  # Convert to degrees (0 = 3 o'clock)
            angle_rad = math.radians(angle)
            
            # Hour marks
            x1 = center_x + (radius - 10) * math.cos(angle_rad)
            y1 = center_y + (radius - 10) * math.sin(angle_rad)
            x2 = center_x + radius * math.cos(angle_rad)
            y2 = center_y + radius * math.sin(angle_rad)
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Hour labels
            if hour % 3 == 0:
                label_x = center_x + (radius + 20) * math.cos(angle_rad)
                label_y = center_y + (radius + 20) * math.sin(angle_rad)
                painter.drawText(int(label_x - 10), int(label_y - 10), 20, 20,
                               Qt.AlignmentFlag.AlignCenter, str(hour))
                
        # Draw data if available
        if self.timeline.grouped_data is not None and not self.timeline.grouped_data.empty:
            # Draw activity rings
            for metric_idx, metric in enumerate(self.timeline.selected_metrics):
                if (metric, 'mean') in self.timeline.grouped_data.columns:
                    self.draw_radial_metric(painter, center_x, center_y, radius, 
                                          metric_idx, metric)
                    
    def draw_radial_metric(self, painter: QPainter, cx: int, cy: int, 
                          radius: int, metric_idx: int, metric: str):
        """Draw a single metric on the radial timeline."""
        values = self.timeline.grouped_data[(metric, 'mean')].fillna(0)
        max_val = values.max() if values.max() > 0 else 1
        
        # Calculate ring radius
        ring_width = radius / (len(self.timeline.selected_metrics) + 1)
        inner_radius = ring_width * (metric_idx + 0.5)
        
        # Draw segments
        for i, (time, value) in enumerate(zip(self.timeline.grouped_data.index, values)):
            if value > 0:
                # Calculate angles
                hour = time.hour + time.minute / 60
                start_angle = (hour - 6) * 15 - (self.timeline.time_grouping / 60 * 15 / 2)
                span_angle = self.timeline.time_grouping / 60 * 15
                
                # Calculate color
                intensity = value / max_val
                color = self.interpolate_color(
                    self.timeline.COLORS['heat_low'],
                    self.timeline.COLORS['heat_high'],
                    intensity
                )
                
                # Draw arc
                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                
                path = QPainterPath()
                path.moveTo(cx, cy)
                rect = QRectF(cx - inner_radius - ring_width/2, 
                            cy - inner_radius - ring_width/2,
                            (inner_radius + ring_width/2) * 2,
                            (inner_radius + ring_width/2) * 2)
                path.arcTo(rect, -start_angle, -span_angle)
                path.closeSubpath()
                
                painter.drawPath(path)
                
    def interpolate_color(self, color1: str, color2: str, factor: float) -> str:
        """Interpolate between two colors."""
        c1 = QColor(color1)
        c2 = QColor(color2)
        
        r = int(c1.red() + (c2.red() - c1.red()) * factor)
        g = int(c1.green() + (c2.green() - c1.green()) * factor)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
        
        return QColor(r, g, b).name()
        
    def mousePressEvent(self, event):
        """Handle mouse press for brushing interaction."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.timeline.brush_start = event.position()
            self.timeline.is_brushing = True
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for brushing."""
        if self.timeline.is_brushing:
            self.timeline.brush_end = event.position()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release to complete brushing."""
        if event.button() == Qt.MouseButton.LeftButton and self.timeline.is_brushing:
            self.timeline.is_brushing = False
            self.timeline.brush_end = event.position()
            
            # Convert pixel coordinates to time range
            if self.timeline.view_mode == 'linear' and self.timeline.grouped_data is not None:
                self.handle_linear_brush_selection()
            elif self.timeline.view_mode == 'radial':
                self.handle_radial_brush_selection()
                
            self.update()
            
    def handle_linear_brush_selection(self):
        """Convert linear brush selection to time range."""
        if not self.timeline.brush_start or not self.timeline.brush_end:
            return
            
        # Get axes from matplotlib
        if self.figure.axes:
            ax = self.figure.axes[0]
            
            # Convert pixel to data coordinates
            start_x = min(self.timeline.brush_start.x(), self.timeline.brush_end.x())
            end_x = max(self.timeline.brush_start.x(), self.timeline.brush_end.x())
            
            # Transform to data coordinates
            inv = ax.transData.inverted()
            start_data, _ = inv.transform((start_x, 0))
            end_data, _ = inv.transform((end_x, 0))
            
            # Convert matplotlib dates to datetime
            start_time = mdates.num2date(start_data)
            end_time = mdates.num2date(end_data)
            
            # Emit signal
            self.timeline.time_range_selected.emit(start_time, end_time)
            
    def handle_radial_brush_selection(self):
        """Convert radial brush selection to time range."""
        if not self.timeline.brush_start or not self.timeline.brush_end:
            return
            
        # Calculate angles from center
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        
        # Start angle
        dx1 = self.timeline.brush_start.x() - center_x
        dy1 = self.timeline.brush_start.y() - center_y
        angle1 = math.degrees(math.atan2(dy1, dx1))
        
        # End angle
        dx2 = self.timeline.brush_end.x() - center_x
        dy2 = self.timeline.brush_end.y() - center_y
        angle2 = math.degrees(math.atan2(dy2, dx2))
        
        # Convert angles to hours (adjusting for clock orientation)
        hour1 = ((angle1 + 90) % 360) / 15
        hour2 = ((angle2 + 90) % 360) / 15
        
        # Create datetime objects for today
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=min(hour1, hour2))
        end_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=max(hour1, hour2))
        
        # Emit signal
        self.timeline.time_range_selected.emit(start_time, end_time)
        
    def paintEvent(self, event):
        """Custom paint event for radial visualization."""
        if self.timeline.view_mode == 'radial':
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.draw_radial_timeline(painter)
            
            # Draw brush selection
            if self.timeline.is_brushing and self.timeline.brush_start and self.timeline.brush_end:
                self.draw_brush_selection(painter)
                
            self.canvas.hide()
        else:
            self.canvas.show()
            self.draw_linear_timeline()
            
    def draw_brush_selection(self, painter: QPainter):
        """Draw the brush selection overlay."""
        if self.timeline.view_mode == 'linear':
            # Draw rectangle for linear selection
            brush_color = QColor(self.timeline.COLORS['primary'])
            brush_color.setAlpha(50)
            painter.fillRect(
                int(min(self.timeline.brush_start.x(), self.timeline.brush_end.x())),
                0,
                int(abs(self.timeline.brush_end.x() - self.timeline.brush_start.x())),
                self.height(),
                brush_color
            )
        else:
            # Draw arc for radial selection
            rect = self.rect()
            center_x = rect.width() // 2
            center_y = rect.height() // 2
            radius = min(center_x, center_y) - 50
            
            # Calculate angles
            dx1 = self.timeline.brush_start.x() - center_x
            dy1 = self.timeline.brush_start.y() - center_y
            angle1 = math.degrees(math.atan2(dy1, dx1))
            
            dx2 = self.timeline.brush_end.x() - center_x
            dy2 = self.timeline.brush_end.y() - center_y
            angle2 = math.degrees(math.atan2(dy2, dx2))
            
            # Draw selection arc
            brush_color = QColor(self.timeline.COLORS['primary'])
            brush_color.setAlpha(50)
            painter.setBrush(QBrush(brush_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            
            span_angle = angle2 - angle1
            if span_angle < 0:
                span_angle += 360
                
            painter.drawPie(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2,
                          int(angle1 * 16), int(span_angle * 16))