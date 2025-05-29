"""
Integration of Reactive Data Binding with Health Visualization System

This module provides the complete integration of reactive data binding with
the existing health visualization components, including WSJ-styled charts.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal

from src.ui.reactive_data_binding import (
    ReactiveDataSource, ReactiveHealthDataStore, ReactiveDataBinding,
    DataChange, DataChangeType, UpdateMethod
)
from src.ui.reactive_change_detection import (
    EfficientChangeDetector, ConflictResolver, UpdateScheduler,
    ChangeHistory, ChangeRecord, ConflictResolutionStrategy
)

if TYPE_CHECKING:
    from src.ui.charts.base_chart import BaseChart
    from src.analytics.data_source_protocol import DataSourceProtocol

logger = logging.getLogger(__name__)


class ReactiveHealthDataBinding(QObject):
    """
    Complete reactive data binding system for health visualizations.
    Integrates with existing chart components and data sources.
    """
    
    # Signals
    binding_created = pyqtSignal(int)  # binding_id
    binding_removed = pyqtSignal(int)  # binding_id
    performance_warning = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.reactive_store = ReactiveHealthDataStore()
        self.change_detector = EfficientChangeDetector()
        self.conflict_resolver = ConflictResolver()
        self.update_scheduler = UpdateScheduler()
        self.change_history = ChangeHistory()
        self.data_binding = ReactiveDataBinding()
        
        # Performance monitoring
        self._update_counts = defaultdict(int)
        self._last_performance_check = datetime.now()
        
        # Connect scheduler to update processor
        self.update_scheduler.update_ready.connect(self._process_scheduled_updates)
        
    def create_reactive_source(self, data_source: DataSourceProtocol) -> ReactiveDataSource:
        """
        Create a reactive wrapper for existing data sources.
        Maintains compatibility with DataSourceProtocol.
        """
        class ReactiveDataSourceAdapter(ReactiveDataSource):
            def __init__(self, source: DataSourceProtocol):
                super().__init__()
                self.source = source
                self._last_data = pd.DataFrame()
                
            def refresh_data(self):
                """Fetch latest data from source and emit changes"""
                try:
                    # Get data based on source capabilities
                    if hasattr(self.source, 'get_dataframe'):
                        new_data = self.source.get_dataframe()
                    elif hasattr(self.source, 'get_data'):
                        data_dict = self.source.get_data()
                        new_data = pd.DataFrame(data_dict)
                    else:
                        logger.warning("Data source has no compatible data method")
                        return
                        
                    # Detect changes
                    changes = self.change_detector.detect_changes(self._last_data, new_data)
                    
                    if changes["type"] != "none":
                        self.update_data(new_data, DataChangeType.UPDATE)
                        self._last_data = new_data
                        
                except Exception as e:
                    logger.error(f"Error refreshing data: {e}")
                    self.error_occurred.emit(str(e))
                    
        return ReactiveDataSourceAdapter(data_source)
        
    def bind_chart(
        self,
        chart: BaseChart,
        data_source: Union[ReactiveDataSource, DataSourceProtocol],
        transform: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
        update_strategy: Optional[UpdateMethod] = None
    ) -> int:
        """
        Bind a chart to a data source with optional transformation.
        Returns binding ID for management.
        """
        # Convert to reactive source if needed
        if not isinstance(data_source, ReactiveDataSource):
            data_source = self.create_reactive_source(data_source)
            
        # Apply update strategy if specified
        if update_strategy:
            interval_map = {
                UpdateMethod.IMMEDIATE: 0,
                UpdateMethod.BATCHED_50MS: 50,
                UpdateMethod.BATCHED_100MS: 100,
                UpdateMethod.BATCHED_500MS: 500,
                UpdateMethod.BATCHED_1S: 1000
            }
            data_source.set_batch_interval(interval_map.get(update_strategy, 100))
            
        # Create binding
        binding_id = self.data_binding.bind(data_source, chart, transform)
        
        # Track performance
        self._track_binding_performance(binding_id)
        
        self.binding_created.emit(binding_id)
        return binding_id
        
    def bind_visualization(
        self,
        viz: BaseChart,
        query: HealthDataQuery,
        apply_wsj_theme: bool = True
    ) -> DataBinding:
        """
        High-level binding for health visualizations with WSJ theming.
        """
        # Create reactive query
        reactive_query = self.create_reactive_query(query)
        
        # Apply WSJ theme if requested
        if apply_wsj_theme and hasattr(viz, 'apply_theme'):
            from src.ui.charts.wsj_style_manager import WSJThemeManager
            wsj_theme = WSJThemeManager()
            viz.apply_theme(wsj_theme)
            
        # Create binding with appropriate update strategy
        update_strategy = self._determine_update_strategy(query)
        binding_id = self.bind_chart(viz, reactive_query, update_strategy=update_strategy)
        
        # Create and return binding object
        return DataBinding(binding_id, viz, reactive_query)
        
    def create_reactive_query(self, query: HealthDataQuery) -> ReactiveQuery:
        """
        Create a reactive query that automatically updates when data changes.
        """
        return ReactiveQuery(query, self.reactive_store, self.change_detector)
        
    def _determine_update_strategy(self, query: HealthDataQuery) -> UpdateMethod:
        """Determine optimal update strategy based on query characteristics"""
        # Analyze query to determine strategy
        if query.is_real_time:
            return UpdateMethod.IMMEDIATE
        elif query.data_type in ['heart_rate', 'steps']:
            return UpdateMethod.BATCHED_100MS
        elif query.aggregation_level == 'minute':
            return UpdateMethod.BATCHED_500MS
        else:
            return UpdateMethod.BATCHED_1S
            
    def _track_binding_performance(self, binding_id: int) -> None:
        """Track performance metrics for bindings"""
        self._update_counts[binding_id] = 0
        
        # Check performance periodically
        now = datetime.now()
        if (now - self._last_performance_check).total_seconds() > 10:
            self._check_performance()
            self._last_performance_check = now
            
    def _check_performance(self) -> None:
        """Check for performance issues"""
        for binding_id, count in self._update_counts.items():
            if count > 100:  # More than 100 updates in 10 seconds
                self.performance_warning.emit(
                    f"High update frequency detected for binding {binding_id}"
                )
                
        # Reset counts
        self._update_counts.clear()
        
    def _process_scheduled_updates(self, updates: List[Any]) -> None:
        """Process a batch of scheduled updates"""
        try:
            # Group updates by type
            grouped = defaultdict(list)
            for update in updates:
                if hasattr(update, 'data_type'):
                    grouped[update.data_type].append(update)
                else:
                    grouped['unknown'].append(update)
                    
            # Process each group
            for data_type, type_updates in grouped.items():
                self._process_update_group(data_type, type_updates)
                
        except Exception as e:
            logger.error(f"Error processing scheduled updates: {e}")


class ReactiveQuery:
    """
    A query that automatically updates when underlying data changes.
    """
    
    def __init__(
        self,
        query: HealthDataQuery,
        data_store: ReactiveHealthDataStore,
        change_detector: EfficientChangeDetector
    ):
        self.query = query
        self.data_store = data_store
        self.change_detector = change_detector
        self._callbacks: List[Callable[[pd.DataFrame], None]] = []
        self._last_result: Optional[pd.DataFrame] = None
        
        # Subscribe to relevant data changes
        self._setup_subscriptions()
        
    def _setup_subscriptions(self) -> None:
        """Set up subscriptions to relevant data changes"""
        # Subscribe to data store changes
        self.data_store.data_changed.connect(self._on_data_changed)
        
    def _on_data_changed(self, change: DataChange) -> None:
        """Handle data changes that might affect this query"""
        # Check if change affects this query
        if self._is_relevant_change(change):
            # Re-execute query
            new_result = self.execute()
            
            # Check if result actually changed
            if self._last_result is None or not self._last_result.equals(new_result):
                self._last_result = new_result
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(new_result)
                    except Exception as e:
                        logger.error(f"Error in query callback: {e}")
                        
    def _is_relevant_change(self, change: DataChange) -> bool:
        """Determine if a change affects this query"""
        # Check if affected keys overlap with query parameters
        query_keys = set(self.query.get_affected_columns())
        return bool(change.affected_keys & query_keys)
        
    def execute(self) -> pd.DataFrame:
        """Execute the query and return results"""
        # This would integrate with your existing query execution logic
        # For now, returning mock implementation
        return self.data_store.data
        
    def on_update(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Register a callback for query updates"""
        self._callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[pd.DataFrame], None]) -> None:
        """Remove a registered callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


class DataBinding:
    """Represents a binding between a visualization and data source"""
    
    def __init__(self, binding_id: int, visualization: BaseChart, query: ReactiveQuery):
        self.binding_id = binding_id
        self.visualization = visualization
        self.query = query
        self.created_at = datetime.now()
        self.update_count = 0
        
    def refresh(self) -> None:
        """Manually refresh the binding"""
        data = self.query.execute()
        self.visualization.data = data
        self.visualization.update()
        self.update_count += 1
        
    def pause(self) -> None:
        """Pause automatic updates"""
        # Implementation would pause the reactive updates
        pass
        
    def resume(self) -> None:
        """Resume automatic updates"""
        # Implementation would resume the reactive updates
        pass


class HealthDataQuery:
    """Mock health data query class for type hints"""
    
    def __init__(self, data_type: str, aggregation_level: str = 'hour', is_real_time: bool = False):
        self.data_type = data_type
        self.aggregation_level = aggregation_level
        self.is_real_time = is_real_time
        
    def get_affected_columns(self) -> List[str]:
        """Get columns affected by this query"""
        # Mock implementation
        return [self.data_type]


# Convenience functions for common use cases

def create_reactive_heart_rate_chart(chart: BaseChart) -> DataBinding:
    """Create a reactive binding for heart rate visualization"""
    binding_system = ReactiveHealthDataBinding()
    query = HealthDataQuery('heart_rate', 'minute', is_real_time=True)
    return binding_system.bind_visualization(chart, query)


def create_reactive_activity_chart(chart: BaseChart) -> DataBinding:
    """Create a reactive binding for activity visualization"""
    binding_system = ReactiveHealthDataBinding()
    query = HealthDataQuery('steps', 'hour', is_real_time=False)
    return binding_system.bind_visualization(chart, query)


def create_reactive_sleep_chart(chart: BaseChart) -> DataBinding:
    """Create a reactive binding for sleep visualization"""
    binding_system = ReactiveHealthDataBinding()
    query = HealthDataQuery('sleep', 'day', is_real_time=False)
    return binding_system.bind_visualization(chart, query)