"""Coordinate interactions between dashboard charts."""

from PyQt6.QtCore import QObject, pyqtSignal, QDateTime
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DashboardInteractionCoordinator(QObject):
    """Coordinates interactions and synchronization between dashboard charts."""
    
    # Signals for broadcasting interactions
    time_range_synchronized = pyqtSignal(object, object)  # start, end
    metric_highlighted = pyqtSignal(str, object)  # metric_name, timestamp
    zoom_level_changed = pyqtSignal(float)  # zoom_factor
    filter_applied = pyqtSignal(dict)  # filter_criteria
    chart_linked = pyqtSignal(str, str)  # source_chart_id, target_chart_id
    
    def __init__(self):
        super().__init__()
        self._linked_charts: Dict[str, List[str]] = {}
        self._synchronized_time_range: Optional[Tuple[QDateTime, QDateTime]] = None
        self._active_filters: Dict[str, Any] = {}
        self._highlighted_metrics: Dict[str, Any] = {}
        self._zoom_level: float = 1.0
        
    def link_charts(self, source_id: str, target_id: str, bidirectional: bool = True):
        """Link two charts for synchronized interactions."""
        # Add link from source to target
        if source_id not in self._linked_charts:
            self._linked_charts[source_id] = []
        if target_id not in self._linked_charts[source_id]:
            self._linked_charts[source_id].append(target_id)
            
        # Add reverse link if bidirectional
        if bidirectional:
            if target_id not in self._linked_charts:
                self._linked_charts[target_id] = []
            if source_id not in self._linked_charts[target_id]:
                self._linked_charts[target_id].append(source_id)
                
        self.chart_linked.emit(source_id, target_id)
        logger.info(f"Linked charts: {source_id} <-> {target_id}")
        
    def unlink_charts(self, source_id: str, target_id: str):
        """Remove link between two charts."""
        if source_id in self._linked_charts:
            if target_id in self._linked_charts[source_id]:
                self._linked_charts[source_id].remove(target_id)
                
        if target_id in self._linked_charts:
            if source_id in self._linked_charts[target_id]:
                self._linked_charts[target_id].remove(source_id)
                
    def get_linked_charts(self, chart_id: str) -> List[str]:
        """Get all charts linked to the specified chart."""
        return self._linked_charts.get(chart_id, [])
        
    def synchronize_time_range(self, start: QDateTime, end: QDateTime, 
                             source_chart_id: Optional[str] = None):
        """Synchronize time range across all linked charts."""
        self._synchronized_time_range = (start, end)
        
        # Notify all linked charts
        if source_chart_id:
            linked = self.get_linked_charts(source_chart_id)
            logger.debug(f"Synchronizing time range from {source_chart_id} to {linked}")
        
        self.time_range_synchronized.emit(start, end)
        
    def highlight_metric(self, metric_name: str, timestamp: QDateTime,
                        source_chart_id: Optional[str] = None):
        """Highlight a specific metric point across linked charts."""
        self._highlighted_metrics[metric_name] = {
            'timestamp': timestamp,
            'source': source_chart_id
        }
        
        self.metric_highlighted.emit(metric_name, timestamp)
        
    def apply_filter(self, filter_name: str, filter_value: Any,
                    source_chart_id: Optional[str] = None):
        """Apply a filter across all linked charts."""
        self._active_filters[filter_name] = {
            'value': filter_value,
            'source': source_chart_id
        }
        
        self.filter_applied.emit(self._active_filters)
        
    def remove_filter(self, filter_name: str):
        """Remove a filter from all charts."""
        if filter_name in self._active_filters:
            del self._active_filters[filter_name]
            self.filter_applied.emit(self._active_filters)
            
    def clear_all_filters(self):
        """Clear all active filters."""
        self._active_filters.clear()
        self.filter_applied.emit(self._active_filters)
        
    def set_zoom_level(self, zoom_factor: float, source_chart_id: Optional[str] = None):
        """Set zoom level for all linked charts."""
        self._zoom_level = max(0.1, min(10.0, zoom_factor))  # Clamp between 0.1 and 10
        self.zoom_level_changed.emit(self._zoom_level)
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get current coordination state."""
        return {
            'linked_charts': self._linked_charts.copy(),
            'time_range': self._synchronized_time_range,
            'active_filters': self._active_filters.copy(),
            'highlighted_metrics': self._highlighted_metrics.copy(),
            'zoom_level': self._zoom_level
        }
        
    def restore_state(self, state: Dict[str, Any]):
        """Restore coordination state."""
        self._linked_charts = state.get('linked_charts', {})
        self._synchronized_time_range = state.get('time_range')
        self._active_filters = state.get('active_filters', {})
        self._highlighted_metrics = state.get('highlighted_metrics', {})
        self._zoom_level = state.get('zoom_level', 1.0)
        
        # Emit signals to update charts
        if self._synchronized_time_range:
            self.time_range_synchronized.emit(*self._synchronized_time_range)
        if self._active_filters:
            self.filter_applied.emit(self._active_filters)
        if self._zoom_level != 1.0:
            self.zoom_level_changed.emit(self._zoom_level)
            
    def create_link_group(self, chart_ids: List[str], group_name: str = "default"):
        """Create a group of fully linked charts."""
        for i, source_id in enumerate(chart_ids):
            for target_id in chart_ids[i+1:]:
                self.link_charts(source_id, target_id, bidirectional=True)
                
        logger.info(f"Created link group '{group_name}' with charts: {chart_ids}")
        
    def broadcast_interaction(self, interaction_type: str, data: Dict[str, Any],
                            source_chart_id: str):
        """Broadcast a generic interaction to linked charts."""
        linked_charts = self.get_linked_charts(source_chart_id)
        
        # Handle specific interaction types
        if interaction_type == 'hover':
            if 'metric' in data and 'timestamp' in data:
                self.highlight_metric(data['metric'], data['timestamp'], source_chart_id)
        elif interaction_type == 'zoom':
            if 'factor' in data:
                self.set_zoom_level(data['factor'], source_chart_id)
        elif interaction_type == 'pan':
            if 'start' in data and 'end' in data:
                self.synchronize_time_range(data['start'], data['end'], source_chart_id)
        elif interaction_type == 'select':
            if 'filter' in data:
                for key, value in data['filter'].items():
                    self.apply_filter(key, value, source_chart_id)
                    
        logger.debug(f"Broadcast {interaction_type} from {source_chart_id} to {linked_charts}")