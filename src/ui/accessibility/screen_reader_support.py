"""
Screen reader support for health visualizations.

Provides comprehensive screen reader functionality for charts and data.
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QAccessible, QAccessibleEvent
import pandas as pd
from datetime import datetime

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class ScreenReaderManager(QObject):
    """Manages screen reader interactions for visualizations."""
    
    # Signals
    announcement = pyqtSignal(str)  # Text to announce
    
    def __init__(self):
        super().__init__()
        self.announcement_queue = []
        self.announcement_timer = QTimer()
        self.announcement_timer.timeout.connect(self._process_announcement_queue)
        self.announcement_timer.setInterval(500)  # 500ms between announcements
        
        logger.info("Initialized ScreenReaderManager")
    
    def create_chart_description(self, chart_type: str, data_summary: str, 
                                key_insights: List[str]) -> str:
        """Create comprehensive chart description for screen readers."""
        parts = [
            f"{chart_type} chart",
            data_summary
        ]
        
        if key_insights:
            insights_text = "Key insights: " + ". ".join(key_insights[:3])
            parts.append(insights_text)
        
        return ". ".join(parts)
    
    def announce(self, text: str, priority: bool = False) -> None:
        """Queue announcement for screen reader."""
        if priority:
            self.announcement_queue.insert(0, text)
        else:
            self.announcement_queue.append(text)
        
        if not self.announcement_timer.isActive():
            self.announcement_timer.start()
        
        # Also emit signal for any listeners
        self.announcement.emit(text)
    
    def enable_live_region(self, widget: QWidget) -> None:
        """Enable live region announcements for dynamic content."""
        try:
            widget.setProperty("aria-live", "polite")
            widget.setProperty("aria-atomic", "true")
            
            # Connect to any update signals if available
            if hasattr(widget, 'dataChanged'):
                widget.dataChanged.connect(
                    lambda: self._announce_data_change(widget)
                )
            
            logger.debug(f"Enabled live region for widget: {widget}")
            
        except Exception as e:
            logger.error(f"Error enabling live region: {e}")
    
    def _announce_data_change(self, widget: QWidget) -> None:
        """Announce data changes in widget."""
        try:
            if hasattr(widget, 'get_change_summary'):
                summary = widget.get_change_summary()
                self.announce(f"Data updated: {summary}")
            else:
                self.announce("Chart data has been updated")
                
        except Exception as e:
            logger.error(f"Error announcing data change: {e}")
    
    def _process_announcement_queue(self) -> None:
        """Process queued announcements."""
        if not self.announcement_queue:
            self.announcement_timer.stop()
            return
        
        text = self.announcement_queue.pop(0)
        
        # Use Qt accessibility if available
        try:
            event = QAccessibleEvent(
                self,
                QAccessible.Event.NameChanged
            )
            event.setAccessibleDescription(text)
            QAccessible.updateAccessibility(event)
        except Exception as e:
            logger.error(f"Error in accessibility announcement: {e}")


class HealthDataNarrator:
    """Creates narrative descriptions of health data for screen readers."""
    
    def __init__(self):
        self.templates = {
            'summary': "This {chart_type} shows {metric} data {time_period}. {main_insight}",
            'trend': "{metric} has {trend_direction} by {change_amount} {time_comparison}",
            'anomaly': "Unusual {metric} value of {value} detected on {date}",
            'achievement': "New personal {record_type} for {metric}: {value} on {date}",
            'comparison': "{metric} is {comparison} than {reference_period} by {difference}"
        }
    
    def create_detailed_summary(self, chart_data: pd.DataFrame, 
                               insights: List[str], 
                               trends: Dict[str, Any]) -> str:
        """Create detailed narrative summary of chart data."""
        sections = []
        
        # Data overview
        if not chart_data.empty:
            overview = self._create_data_overview(chart_data)
            sections.append(overview)
        
        # Key statistics
        stats = self._create_statistics_summary(chart_data)
        if stats:
            sections.append(stats)
        
        # Trends
        if trends:
            trend_summary = self._create_trend_summary(trends)
            sections.append(trend_summary)
        
        # Insights
        if insights:
            insights_summary = "Important findings: " + ". ".join(insights[:3])
            sections.append(insights_summary)
        
        return " ".join(sections)
    
    def describe_data_point(self, metric: str, value: float, 
                           timestamp: datetime, 
                           context: Optional[Dict[str, Any]] = None) -> str:
        """Create accessible description for a data point."""
        parts = [
            f"{metric}: {self._format_value(value, metric)}",
            f"at {timestamp.strftime('%B %d, %I:%M %p')}"
        ]
        
        if context:
            if context.get('is_anomaly'):
                parts.append("This is an unusual value")
            
            if context.get('is_achievement'):
                parts.append("Personal record achieved")
            
            if 'percentile' in context:
                parts.append(f"{context['percentile']}th percentile for this metric")
            
            if 'trend' in context:
                parts.append(f"Part of {context['trend']} trend")
        
        return ". ".join(parts)
    
    def _create_data_overview(self, data: pd.DataFrame) -> str:
        """Create overview of data contents."""
        num_records = len(data)
        
        if 'timestamp' in data.columns:
            date_range = (
                f"from {data['timestamp'].min().strftime('%B %d, %Y')} "
                f"to {data['timestamp'].max().strftime('%B %d, %Y')}"
            )
        else:
            date_range = ""
        
        metrics = [col for col in data.columns if col != 'timestamp']
        metrics_text = ", ".join(metrics[:3])
        if len(metrics) > 3:
            metrics_text += f" and {len(metrics) - 3} more"
        
        return f"Displaying {num_records} data points {date_range} for {metrics_text}"
    
    def _create_statistics_summary(self, data: pd.DataFrame) -> Optional[str]:
        """Create summary of key statistics."""
        if data.empty:
            return None
        
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) == 0:
            return None
        
        stats_parts = []
        for col in numeric_cols[:2]:  # Limit to first 2 metrics
            mean_val = data[col].mean()
            min_val = data[col].min()
            max_val = data[col].max()
            
            stats_parts.append(
                f"{col} ranges from {self._format_value(min_val, col)} "
                f"to {self._format_value(max_val, col)}, "
                f"averaging {self._format_value(mean_val, col)}"
            )
        
        return "Statistics: " + ". ".join(stats_parts)
    
    def _create_trend_summary(self, trends: Dict[str, Any]) -> str:
        """Create summary of trends."""
        trend_parts = []
        
        if 'direction' in trends:
            direction = trends['direction']
            if direction == 'increasing':
                trend_parts.append("showing an upward trend")
            elif direction == 'decreasing':
                trend_parts.append("showing a downward trend")
            else:
                trend_parts.append("remaining stable")
        
        if 'change_percent' in trends:
            change = trends['change_percent']
            trend_parts.append(f"with {abs(change):.1f}% change")
        
        if 'pattern' in trends:
            trend_parts.append(f"following a {trends['pattern']} pattern")
        
        return "Trend analysis: " + ", ".join(trend_parts) if trend_parts else ""
    
    def _format_value(self, value: float, metric: str) -> str:
        """Format value with appropriate units and precision."""
        # This would be enhanced with actual unit mapping
        if 'heart' in metric.lower():
            return f"{value:.0f} bpm"
        elif 'step' in metric.lower():
            return f"{value:,.0f} steps"
        elif 'distance' in metric.lower():
            return f"{value:.2f} km"
        elif 'calorie' in metric.lower():
            return f"{value:.0f} calories"
        else:
            return f"{value:.2f}"