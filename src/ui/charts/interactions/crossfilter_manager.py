"""
Crossfilter manager for coordinating interactions between multiple charts.

Enables filtering and highlighting across related visualizations.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FilterDefinition:
    """Definition of a crossfilter"""
    filter_id: str
    filter_type: str  # 'range', 'value', 'set'
    value: Any
    source_chart: Optional[str] = None
    timestamp: Optional[datetime] = None


class CrossfilterManager(QObject):
    """Manages crossfilter state and propagation between charts"""
    
    # Signals
    filters_changed = pyqtSignal(dict)  # All active filters
    filter_applied = pyqtSignal(str, object)  # filter_id, filter_value
    filter_removed = pyqtSignal(str)  # filter_id
    highlight_changed = pyqtSignal(set)  # Set of highlighted items
    
    def __init__(self):
        super().__init__()
        
        # Active filters
        self.active_filters: Dict[str, FilterDefinition] = {}
        
        # Registered charts
        self.registered_charts: Dict[str, QObject] = {}
        
        # Filter dependencies
        self.filter_dependencies: Dict[str, Set[str]] = {}
        
        # Highlighted items
        self.highlighted_items: Set[str] = set()
        
        # Filter callbacks
        self.filter_callbacks: Dict[str, List[Callable]] = {}
        
    def register_chart(self, chart_id: str, chart_object: QObject):
        """Register a chart for crossfilter coordination"""
        self.registered_charts[chart_id] = chart_object
        
        # Connect to chart's selection signals if available
        if hasattr(chart_object, 'selection_changed'):
            chart_object.selection_changed.connect(
                lambda selection: self._handle_chart_selection(chart_id, selection)
            )
            
    def unregister_chart(self, chart_id: str):
        """Unregister a chart"""
        if chart_id in self.registered_charts:
            # Disconnect signals
            chart = self.registered_charts[chart_id]
            if hasattr(chart, 'selection_changed'):
                try:
                    chart.selection_changed.disconnect()
                except:
                    pass
                    
            del self.registered_charts[chart_id]
            
            # Remove any filters from this chart
            filters_to_remove = [
                fid for fid, fdef in self.active_filters.items()
                if fdef.source_chart == chart_id
            ]
            for filter_id in filters_to_remove:
                self.remove_filter(filter_id)
                
    def apply_filter(self, filter_id: str, filter_value: Any, 
                    filter_type: str = 'value', source_chart: Optional[str] = None):
        """Apply a crossfilter"""
        # Create filter definition
        filter_def = FilterDefinition(
            filter_id=filter_id,
            filter_type=filter_type,
            value=filter_value,
            source_chart=source_chart,
            timestamp=datetime.now()
        )
        
        # Check if this is an update or new filter
        is_update = filter_id in self.active_filters
        
        # Store filter
        self.active_filters[filter_id] = filter_def
        
        # Notify all charts except source
        for chart_id, chart in self.registered_charts.items():
            if chart_id != source_chart:
                self._apply_filter_to_chart(chart, filter_def)
                
        # Trigger callbacks
        if filter_id in self.filter_callbacks:
            for callback in self.filter_callbacks[filter_id]:
                callback(filter_value)
                
        # Emit signals
        self.filter_applied.emit(filter_id, filter_value)
        self.filters_changed.emit(self.get_active_filters())
        
    def remove_filter(self, filter_id: str):
        """Remove a crossfilter"""
        if filter_id not in self.active_filters:
            return
            
        source_chart = self.active_filters[filter_id].source_chart
        del self.active_filters[filter_id]
        
        # Notify all charts
        for chart_id, chart in self.registered_charts.items():
            if chart_id != source_chart:
                self._remove_filter_from_chart(chart, filter_id)
                
        # Emit signals
        self.filter_removed.emit(filter_id)
        self.filters_changed.emit(self.get_active_filters())
        
    def clear_all_filters(self):
        """Clear all active filters"""
        filter_ids = list(self.active_filters.keys())
        for filter_id in filter_ids:
            self.remove_filter(filter_id)
            
    def get_active_filters(self) -> Dict[str, Any]:
        """Get all active filter values"""
        return {
            fid: fdef.value 
            for fid, fdef in self.active_filters.items()
        }
        
    def get_filter(self, filter_id: str) -> Optional[Any]:
        """Get a specific filter value"""
        if filter_id in self.active_filters:
            return self.active_filters[filter_id].value
        return None
        
    def has_filter(self, filter_id: str) -> bool:
        """Check if a filter is active"""
        return filter_id in self.active_filters
        
    def set_filter_dependency(self, dependent_filter: str, required_filters: Set[str]):
        """Set dependencies between filters"""
        self.filter_dependencies[dependent_filter] = required_filters
        
    def can_apply_filter(self, filter_id: str) -> bool:
        """Check if a filter can be applied based on dependencies"""
        if filter_id not in self.filter_dependencies:
            return True
            
        required = self.filter_dependencies[filter_id]
        return all(req in self.active_filters for req in required)
        
    def highlight_items(self, item_ids: Set[str], source_chart: Optional[str] = None):
        """Highlight items across all charts"""
        self.highlighted_items = item_ids
        
        # Notify all charts except source
        for chart_id, chart in self.registered_charts.items():
            if chart_id != source_chart and hasattr(chart, 'highlight_items'):
                chart.highlight_items(item_ids)
                
        self.highlight_changed.emit(item_ids)
        
    def clear_highlights(self):
        """Clear all highlights"""
        self.highlighted_items.clear()
        
        # Notify all charts
        for chart in self.registered_charts.values():
            if hasattr(chart, 'clear_highlights'):
                chart.clear_highlights()
                
        self.highlight_changed.emit(set())
        
    def register_filter_callback(self, filter_id: str, callback: Callable):
        """Register a callback for when a specific filter changes"""
        if filter_id not in self.filter_callbacks:
            self.filter_callbacks[filter_id] = []
        self.filter_callbacks[filter_id].append(callback)
        
    def _handle_chart_selection(self, chart_id: str, selection: Any):
        """Handle selection from a chart"""
        # Determine filter type based on selection
        if isinstance(selection, (list, tuple)) and len(selection) == 2:
            # Range selection
            filter_type = 'range'
            filter_id = f'{chart_id}_range'
        elif isinstance(selection, (list, set)):
            # Multiple value selection
            filter_type = 'set'
            filter_id = f'{chart_id}_values'
        else:
            # Single value selection
            filter_type = 'value'
            filter_id = f'{chart_id}_value'
            
        # Apply the filter
        if selection:
            self.apply_filter(filter_id, selection, filter_type, chart_id)
        else:
            self.remove_filter(filter_id)
            
    def _apply_filter_to_chart(self, chart: QObject, filter_def: FilterDefinition):
        """Apply a filter to a specific chart"""
        if hasattr(chart, 'apply_crossfilter'):
            chart.apply_crossfilter(filter_def.filter_id, filter_def.value, filter_def.filter_type)
        elif hasattr(chart, 'set_filter'):
            chart.set_filter(filter_def.value)
            
    def _remove_filter_from_chart(self, chart: QObject, filter_id: str):
        """Remove a filter from a specific chart"""
        if hasattr(chart, 'remove_crossfilter'):
            chart.remove_crossfilter(filter_id)
        elif hasattr(chart, 'clear_filter'):
            chart.clear_filter()
            
    def get_filter_summary(self) -> str:
        """Get a human-readable summary of active filters"""
        if not self.active_filters:
            return "No active filters"
            
        summary_parts = []
        for filter_id, filter_def in self.active_filters.items():
            if filter_def.filter_type == 'range':
                start, end = filter_def.value
                summary_parts.append(f"{filter_id}: {start} to {end}")
            elif filter_def.filter_type == 'set':
                count = len(filter_def.value)
                summary_parts.append(f"{filter_id}: {count} items selected")
            else:
                summary_parts.append(f"{filter_id}: {filter_def.value}")
                
        return ", ".join(summary_parts)