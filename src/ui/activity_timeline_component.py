"""
Activity Timeline Component for health data visualization.
Displays hourly breakdown with radial and linear views, ML clustering, and interactive features.
Inspired by Wall Street Journal visualization style.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QScrollArea, QFrame, QSlider,
    QCheckBox, QSplitter, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QRadialGradient
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta
import math
import time
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from .comparison_overlay_widget import ComparisonOverlayWidget
import warnings
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
        'background': '#F5E6D3',      # Warm tan background
        'grid': '#A69583',            # Light brown
        'text': '#5D4E37',            # Dark brown
        'primary': '#FF8C42',         # Warm orange - primary accent
        'secondary': '#FFD166',       # Soft yellow - secondary accent
        'accent': '#95C17B',          # Soft green - success
        'heat_low': '#FFF8F0',        # Light cream
        'heat_high': '#FF8C42',       # Warm orange for intensity
        'inactive': '#E8E0D8',        # Light gray-brown
        'chart_blue': '#6C9BD1',      # Blue from chart palette
        'chart_purple': '#B79FCB'     # Purple from chart palette
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # View mode selector
        view_group = QButtonGroup(self)
        linear_btn = QRadioButton("Linear")
        radial_btn = QRadioButton("Radial")
        linear_btn.setChecked(True)
        
        linear_btn.toggled.connect(lambda checked: self.set_view_mode('linear') if checked else None)
        radial_btn.toggled.connect(lambda checked: self.set_view_mode('radial') if checked else None)
        
        view_group.addButton(linear_btn)
        view_group.addButton(radial_btn)
        
        header_layout.addWidget(QLabel("View:"))
        header_layout.addWidget(linear_btn)
        header_layout.addWidget(radial_btn)
        
        # Time grouping selector
        header_layout.addWidget(QLabel("Group by:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["15 minutes", "30 minutes", "1 hour"])
        self.time_combo.setCurrentIndex(2)
        self.time_combo.currentIndexChanged.connect(self.on_time_grouping_changed)
        header_layout.addWidget(self.time_combo)
        
        layout.addLayout(header_layout)
        
        # Options bar
        options_layout = QHBoxLayout()
        
        self.cluster_check = QCheckBox("Enable Clustering")
        self.cluster_check.stateChanged.connect(self.on_clustering_toggled)
        options_layout.addWidget(self.cluster_check)
        
        self.patterns_check = QCheckBox("Highlight Patterns")
        self.patterns_check.setChecked(True)
        self.patterns_check.stateChanged.connect(self.on_patterns_toggled)
        options_layout.addWidget(self.patterns_check)
        
        self.correlations_check = QCheckBox("Show Correlations")
        self.correlations_check.stateChanged.connect(self.on_correlations_toggled)
        options_layout.addWidget(self.correlations_check)
        
        self.overlays_check = QCheckBox("Comparison Overlays")
        self.overlays_check.setChecked(True)
        self.overlays_check.stateChanged.connect(self.on_overlays_toggled)
        options_layout.addWidget(self.overlays_check)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Main visualization area
        self.viz_widget = TimelineVisualizationWidget(self)
        self.viz_widget.setMinimumHeight(400)
        layout.addWidget(self.viz_widget)
        
        # Info panel
        self.info_panel = QGroupBox("Timeline Insights")
        info_layout = QVBoxLayout()
        
        self.active_periods_label = QLabel("Active Periods: -")
        self.rest_periods_label = QLabel("Rest Periods: -")
        self.peak_activity_label = QLabel("Peak Activity: -")
        self.patterns_label = QLabel("Patterns: None detected")
        
        info_layout.addWidget(self.active_periods_label)
        info_layout.addWidget(self.rest_periods_label)
        info_layout.addWidget(self.peak_activity_label)
        info_layout.addWidget(self.patterns_label)
        
        self.info_panel.setLayout(info_layout)
        layout.addWidget(self.info_panel)
        
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
        self.process_data()
        
    def on_clustering_toggled(self, state: int):
        """Toggle ML clustering."""
        self.clustering_enabled = state == Qt.CheckState.Checked.value
        if self.clustering_enabled and self.data is not None:
            self.perform_clustering()
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
        self.process_data()
        
    def process_data(self):
        """Process data for visualization."""
        if self.data is None or self.data.empty:
            return
            
        # Group data by time intervals
        self.grouped_data = self.aggregate_by_time_interval()
        
        # Detect activity patterns
        self.detect_activity_patterns()
        
        # Perform clustering if enabled
        if self.clustering_enabled:
            self.perform_clustering()
            
        # Calculate correlations if enabled
        if self.show_correlations:
            self.calculate_correlations()
            
        # Update visualization
        self.viz_widget.update()
        self.update_info_panel()
        
    def aggregate_by_time_interval(self) -> pd.DataFrame:
        """Aggregate data by the selected time interval."""
        if self.data is None:
            return pd.DataFrame()
            
        # Create time-based groups
        freq_map = {15: '15min', 30: '30min', 60: 'h'}
        freq = freq_map[self.time_grouping]
        
        # Group and aggregate
        grouped = self.data.resample(freq).agg({
            metric: ['mean', 'sum', 'count'] 
            for metric in self.selected_metrics
        })
        
        return grouped
        
    def detect_activity_patterns(self):
        """Detect active vs rest periods using statistical methods."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Calculate activity scores
        activity_scores = []
        for idx, row in self.grouped_data.iterrows():
            # Simple activity score based on metric values
            score = 0
            for metric in self.selected_metrics:
                if (metric, 'mean') in row.index:
                    value = row[(metric, 'mean')]
                    if pd.notna(value):
                        score += value
            activity_scores.append(score)
            
        # Determine thresholds
        scores_array = np.array(activity_scores)
        if len(scores_array) > 0:
            threshold = np.percentile(scores_array, 25)
            
            # Classify periods
            self.active_periods = []
            self.rest_periods = []
            
            for i, (idx, score) in enumerate(zip(self.grouped_data.index, activity_scores)):
                if score > threshold:
                    self.active_periods.append((idx, score))
                else:
                    self.rest_periods.append((idx, score))
                    
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
        """Update the information panel with insights."""
        if hasattr(self, 'active_periods') and self.active_periods:
            self.active_periods_label.setText(f"Active Periods: {len(self.active_periods)}")
        else:
            self.active_periods_label.setText("Active Periods: -")
            
        if hasattr(self, 'rest_periods') and self.rest_periods:
            self.rest_periods_label.setText(f"Rest Periods: {len(self.rest_periods)}")
        else:
            self.rest_periods_label.setText("Rest Periods: -")
            
        # Find peak activity time
        if hasattr(self, 'active_periods') and self.active_periods:
            peak_time, peak_score = max(self.active_periods, key=lambda x: x[1])
            self.peak_activity_label.setText(f"Peak Activity: {peak_time.strftime('%H:%M')}")
        else:
            self.peak_activity_label.setText("Peak Activity: -")
            
        # Pattern detection summary
        if self.clusters is not None:
            unique_clusters = len(np.unique(self.clusters))
            anomaly_count = np.sum(self.anomalies) if self.anomalies is not None else 0
            self.patterns_label.setText(f"Patterns: {unique_clusters} clusters, {anomaly_count} anomalies")
        else:
            self.patterns_label.setText("Patterns: None detected")


class TimelineVisualizationWidget(QWidget):
    """Custom widget for rendering timeline visualizations."""
    
    def __init__(self, parent: ActivityTimelineComponent):
        super().__init__(parent)
        self.timeline = parent
        self.setMinimumHeight(400)
        self.setMouseTracking(True)
        
        # Matplotlib figure for linear view
        self.figure = Figure(figsize=(10, 4), facecolor=parent.COLORS['background'])
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
        
        # Plot each metric
        for i, metric in enumerate(self.timeline.selected_metrics):
            if (metric, 'mean') in self.timeline.grouped_data.columns:
                values = self.timeline.grouped_data[(metric, 'mean')].fillna(0)
                
                # Create heat gradient effect
                for j, (time, value) in enumerate(zip(times, values)):
                    if value > 0:
                        # Calculate color intensity
                        max_val = values.max() if values.max() > 0 else 1
                        intensity = value / max_val
                        
                        # Create gradient color
                        color = self.interpolate_color(
                            self.timeline.COLORS['heat_low'],
                            self.timeline.COLORS['heat_high'],
                            intensity
                        )
                        
                        # Draw bar
                        width = 1.0 / (24 * 60 / self.timeline.time_grouping)
                        rect = Rectangle(
                            (mdates.date2num(time), i),
                            width,
                            intensity,
                            facecolor=color,
                            edgecolor='none',
                            alpha=0.8
                        )
                        ax.add_patch(rect)
                        
        # Highlight patterns if enabled
        if self.timeline.show_patterns and self.timeline.anomalies is not None:
            for j, (time, is_anomaly) in enumerate(zip(times, self.timeline.anomalies)):
                if is_anomaly:
                    ax.axvspan(
                        mdates.date2num(time),
                        mdates.date2num(time + timedelta(minutes=self.timeline.time_grouping)),
                        alpha=0.2,
                        color=self.timeline.COLORS['secondary']
                    )
                    
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        
        # Labels
        ax.set_xlabel('Time of Day', fontsize=11, color=self.timeline.COLORS['text'])
        ax.set_ylabel('Activity Intensity', fontsize=11, color=self.timeline.COLORS['text'])
        ax.set_title('24-Hour Activity Pattern', fontsize=14, fontweight='bold', 
                     color=self.timeline.COLORS['text'], pad=20)
        
        # Grid
        ax.grid(True, axis='y', linestyle=':', color=self.timeline.COLORS['grid'], alpha=0.5)
        
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
            logger.error(f"Error adding comparison overlays: {e}")
        
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