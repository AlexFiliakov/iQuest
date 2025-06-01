"""
Timeline Insights Panel for Activity Timeline Component.

This module provides a user-friendly panel that transforms technical analytics
data (clusters, anomalies, patterns) into plain language insights and
visualizations that users can understand and act upon.

Follows the project's warm earth tone design system and implements progressive
disclosure for complex data.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging


class TimelineInsightsPanel(QWidget):
    """
    Main insights panel that converts technical analytics to user-friendly displays.
    
    This panel contains multiple sub-panels that each focus on a specific aspect
    of the activity data (patterns, anomalies, correlations, etc.) and presents
    them in an accessible, non-technical way.
    
    Attributes:
        pattern_card: Widget showing activity pattern insights
        anomaly_card: Widget showing unusual activity alerts
        heatmap_widget: Widget showing activity intensity heatmap
    """
    
    # Signals
    insight_clicked = pyqtSignal(str, dict)  # type, details
    
    # Color palette from project design system
    COLORS = {
        'background': '#F5E6D3',      # Warm tan background
        'card_bg': '#FFFFFF',         # White card background
        'text_primary': '#2C3E50',    # Dark text
        'text_secondary': '#5D6D7E',  # Secondary text
        'accent_orange': '#FF8C42',   # Primary accent
        'accent_yellow': '#FFD166',   # Secondary accent
        'accent_green': '#95C17B',    # Success/positive
        'accent_red': '#FF6B6B',      # Alert/negative
        'border': '#E0E0E0',          # Card borders
        'shadow': 'rgba(0, 0, 0, 0.1)'
    }
    
    def __init__(self, parent=None):
        """Initialize the Timeline Insights Panel."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.clusters = None
        self.anomalies = None
        self.grouped_data = None
        self.selected_metrics = []
        
        # Pattern descriptions mapping
        self.pattern_descriptions = {
            0: "Early Bird Pattern",
            1: "Midday Mover",
            2: "Evening Exerciser", 
            3: "Night Owl Activity"
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout with scroll area for multiple panels
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for panels
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container widget for scrollable content
        scroll_content = QWidget()
        self.panels_layout = QVBoxLayout(scroll_content)
        self.panels_layout.setContentsMargins(10, 10, 10, 10)
        self.panels_layout.setSpacing(15)
        
        # Create insight panels (Phase 1: Start with 3 core panels)
        self.create_pattern_recognition_panel()
        self.create_anomaly_alert_panel()
        self.create_activity_heatmap_panel()
        
        # Add stretch to push panels to top
        self.panels_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Apply styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLORS['background']};
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }}
            QScrollArea {{
                border: none;
                background-color: {self.COLORS['background']};
            }}
            QScrollBar:vertical {{
                background: {self.COLORS['background']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.COLORS['border']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.COLORS['text_secondary']};
            }}
        """)
        
    def create_pattern_recognition_panel(self):
        """Create the pattern recognition insights panel."""
        from .pattern_recognition_card import PatternRecognitionCard
        
        self.pattern_card = PatternRecognitionCard(self)
        self.pattern_card.pattern_clicked.connect(
            lambda pattern, details: self.insight_clicked.emit('pattern', details)
        )
        self.panels_layout.addWidget(self.pattern_card)
        
    def create_anomaly_alert_panel(self):
        """Create the anomaly alert panel."""
        from .anomaly_alert_card import AnomalyAlertCard
        
        self.anomaly_card = AnomalyAlertCard(self)
        self.anomaly_card.anomaly_clicked.connect(
            lambda anomaly, details: self.insight_clicked.emit('anomaly', details)
        )
        self.panels_layout.addWidget(self.anomaly_card)
        
    def create_activity_heatmap_panel(self):
        """Create the activity heatmap panel."""
        from .activity_heatmap_widget import ActivityHeatmapWidget
        
        self.heatmap_widget = ActivityHeatmapWidget(self)
        self.heatmap_widget.time_clicked.connect(
            lambda time, details: self.insight_clicked.emit('heatmap', details)
        )
        self.panels_layout.addWidget(self.heatmap_widget)
        
    def update_insights(self, clusters: Optional[np.ndarray], 
                       anomalies: Optional[np.ndarray],
                       grouped_data: Optional[pd.DataFrame],
                       selected_metrics: List[str]):
        """
        Update all insight panels with new data.
        
        Args:
            clusters: Array of cluster IDs for each time period
            anomalies: Boolean array indicating anomalies
            grouped_data: DataFrame with aggregated time-based data
            selected_metrics: List of selected metric names
        """
        self.clusters = clusters
        self.anomalies = anomalies
        self.grouped_data = grouped_data
        self.selected_metrics = selected_metrics
        
        # Update each panel with transformed data
        if hasattr(self, 'pattern_card'):
            self.update_pattern_insights()
            
        if hasattr(self, 'anomaly_card'):
            self.update_anomaly_insights()
            
        if hasattr(self, 'heatmap_widget'):
            self.update_heatmap_data()
            
    def update_pattern_insights(self):
        """Transform cluster data into user-friendly pattern insights."""
        if self.clusters is None or self.grouped_data is None:
            return
            
        # Analyze cluster characteristics
        patterns = []
        
        for cluster_id in range(4):  # Assuming 4 clusters from KMeans
            if cluster_id >= len(np.unique(self.clusters)):
                continue
                
            # Find time periods in this cluster
            mask = self.clusters == cluster_id
            if not np.any(mask):
                continue
                
            times = self.grouped_data.index[mask]
            if len(times) == 0:
                continue
                
            # Analyze pattern characteristics
            hours = [t.hour for t in times]
            avg_hour = np.mean(hours)
            frequency = len(times) / len(self.clusters) * 100
            
            # Determine pattern description based on timing
            if avg_hour < 9:
                description = "Early Bird Pattern"
                detail = f"Most active between 5-9 AM ({frequency:.0f}% of the time)"
                icon = "🌅"
            elif avg_hour < 14:
                description = "Midday Mover"
                detail = f"Peak activity 11 AM-2 PM ({frequency:.0f}% of the time)"
                icon = "☀️"
            elif avg_hour < 20:
                description = "Evening Exerciser"
                detail = f"Prefers 5-8 PM workouts ({frequency:.0f}% of the time)"
                icon = "🌆"
            else:
                description = "Night Owl Activity"
                detail = f"Active after 8 PM ({frequency:.0f}% of the time)"
                icon = "🌙"
                
            # Calculate average intensity for this pattern
            intensity_data = []
            for metric in self.selected_metrics:
                if (metric, 'mean') in self.grouped_data.columns:
                    values = self.grouped_data.loc[times, (metric, 'mean')]
                    intensity_data.extend(values.dropna().values)
                    
            avg_intensity = np.mean(intensity_data) if intensity_data else 0
            
            patterns.append({
                'id': cluster_id,
                'name': description,
                'detail': detail,
                'icon': icon,
                'frequency': frequency,
                'intensity': avg_intensity,
                'times': times
            })
            
        # Sort patterns by frequency
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Update pattern card
        self.pattern_card.update_patterns(patterns)
        
    def update_anomaly_insights(self):
        """Transform anomaly data into user-friendly alerts."""
        if self.anomalies is None or self.grouped_data is None:
            return
            
        # Find anomalous time periods
        anomaly_indices = np.where(self.anomalies)[0]
        if len(anomaly_indices) == 0:
            self.anomaly_card.update_anomalies([])
            return
            
        alerts = []
        
        for idx in anomaly_indices[:5]:  # Show top 5 anomalies
            if idx >= len(self.grouped_data):
                continue
                
            time = self.grouped_data.index[idx]
            
            # Analyze why this is anomalous
            anomaly_data = {}
            for metric in self.selected_metrics:
                if (metric, 'mean') in self.grouped_data.columns:
                    value = self.grouped_data.iloc[idx][(metric, 'mean')]
                    if pd.notna(value):
                        anomaly_data[metric] = value
                        
            if not anomaly_data:
                continue
                
            # Generate user-friendly explanation
            explanations = []
            severity = 'low'
            
            for metric, value in anomaly_data.items():
                # Compare to typical values
                metric_values = self.grouped_data[(metric, 'mean')].dropna()
                if len(metric_values) > 0:
                    mean_val = metric_values.mean()
                    std_val = metric_values.std()
                    
                    if std_val > 0:
                        z_score = abs((value - mean_val) / std_val)
                        
                        if z_score > 3:
                            severity = 'high'
                            if value > mean_val:
                                explanations.append(f"Unusually high {metric}: {value:.0f} (typical: {mean_val:.0f})")
                            else:
                                explanations.append(f"Unusually low {metric}: {value:.0f} (typical: {mean_val:.0f})")
                        elif z_score > 2:
                            if severity != 'high':
                                severity = 'medium'
                            if value > mean_val:
                                explanations.append(f"Above average {metric}: {value:.0f}")
                            else:
                                explanations.append(f"Below average {metric}: {value:.0f}")
                                
            if explanations:
                alerts.append({
                    'time': time,
                    'severity': severity,
                    'explanations': explanations,
                    'data': anomaly_data
                })
                
        # Sort by severity and time
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: (severity_order[x['severity']], x['time']))
        
        # Update anomaly card
        self.anomaly_card.update_anomalies(alerts)
        
    def update_heatmap_data(self):
        """Update the activity heatmap with current data."""
        if self.grouped_data is None:
            return
            
        # Prepare data for heatmap
        heatmap_data = {}
        
        for idx, time in enumerate(self.grouped_data.index):
            hour = time.hour
            day = time.strftime('%a')  # Day abbreviation
            
            # Calculate intensity as average across all metrics
            intensity_values = []
            for metric in self.selected_metrics:
                if (metric, 'mean') in self.grouped_data.columns:
                    value = self.grouped_data.iloc[idx][(metric, 'mean')]
                    if pd.notna(value):
                        intensity_values.append(value)
                        
            if intensity_values:
                intensity = np.mean(intensity_values)
                key = (day, hour)
                
                # Average if multiple values for same hour/day
                if key in heatmap_data:
                    heatmap_data[key] = (heatmap_data[key] + intensity) / 2
                else:
                    heatmap_data[key] = intensity
                    
        # Update heatmap widget
        self.heatmap_widget.update_data(heatmap_data)