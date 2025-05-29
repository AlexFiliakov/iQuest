"""
Reactive Data Binding System for Health Visualizations

This module implements a reactive data binding framework that automatically
updates visualizations when underlying health data changes. It uses a hybrid
approach combining Qt signals for UI updates and observer pattern for data layer.
"""

from __future__ import annotations

import logging
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Union, TYPE_CHECKING
)

import pandas as pd
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QMutex, QMutexLocker

if TYPE_CHECKING:
    from src.ui.charts.base_chart import BaseChart

logger = logging.getLogger(__name__)


class UpdateMethod(Enum):
    """Update strategies based on data characteristics"""
    IMMEDIATE = auto()
    BATCHED_50MS = auto()
    BATCHED_100MS = auto()
    BATCHED_500MS = auto()
    BATCHED_1S = auto()


class DataChangeType(Enum):
    """Types of data changes"""
    ADD = auto()
    UPDATE = auto()
    DELETE = auto()
    RESET = auto()


class DataChange:
    """Represents a change in the data"""
    
    def __init__(
        self,
        change_type: DataChangeType,
        data: Any,
        timestamp: datetime,
        affected_keys: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.change_type = change_type
        self.data = data
        self.timestamp = timestamp
        self.affected_keys = affected_keys or set()
        self.metadata = metadata or {}
        
    def __repr__(self) -> str:
        return f"DataChange({self.change_type.name}, keys={self.affected_keys})"


class ReactiveDataSource(QObject):
    """Base class for reactive data sources"""
    
    # Signals
    data_changed = pyqtSignal(object)  # DataChange
    batch_updated = pyqtSignal(list)   # List[DataChange]
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._data = pd.DataFrame()
        self._subscribers: Set[weakref.ref] = set()
        self._change_buffer: List[DataChange] = []
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._process_batch)
        self._batch_interval = 50  # milliseconds
        self._mutex = QMutex()
        
    @property
    def data(self) -> pd.DataFrame:
        """Get current data snapshot"""
        with QMutexLocker(self._mutex):
            return self._data.copy()
            
    def update_data(self, new_data: pd.DataFrame, change_type: DataChangeType = DataChangeType.UPDATE) -> None:
        """Update the data and notify subscribers"""
        try:
            with QMutexLocker(self._mutex):
                old_data = self._data
                self._data = new_data.copy()
                
                # Calculate what changed
                change = DataChange(
                    change_type=change_type,
                    data=new_data,
                    timestamp=datetime.now(),
                    affected_keys=self._calculate_affected_keys(old_data, new_data)
                )
                
                self._buffer_change(change)
                
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            self.error_occurred.emit(str(e))
            
    def _calculate_affected_keys(self, old_data: pd.DataFrame, new_data: pd.DataFrame) -> Set[str]:
        """Calculate which columns/keys were affected by the change"""
        if old_data.empty or new_data.empty:
            return set(new_data.columns)
            
        # Find columns with differences
        affected = set()
        for col in new_data.columns:
            if col not in old_data.columns:
                affected.add(col)
            elif not old_data[col].equals(new_data[col]):
                affected.add(col)
                
        return affected
        
    def _buffer_change(self, change: DataChange) -> None:
        """Buffer changes for batch processing"""
        self._change_buffer.append(change)
        
        if not self._batch_timer.isActive():
            self._batch_timer.start(self._batch_interval)
            
    @pyqtSlot()
    def _process_batch(self) -> None:
        """Process buffered changes"""
        if not self._change_buffer:
            self._batch_timer.stop()
            return
            
        with QMutexLocker(self._mutex):
            changes = self._change_buffer[:]
            self._change_buffer.clear()
            
        # Emit individual changes
        for change in changes:
            self.data_changed.emit(change)
            
        # Emit batch for efficient processing
        if len(changes) > 1:
            self.batch_updated.emit(changes)
            
        self._batch_timer.stop()
        
    def subscribe(self, callback: Callable[[DataChange], None]) -> None:
        """Subscribe to data changes with weak reference"""
        self._subscribers.add(weakref.ref(callback))
        
    def unsubscribe(self, callback: Callable[[DataChange], None]) -> None:
        """Unsubscribe from data changes"""
        self._subscribers.discard(weakref.ref(callback))
        
    def set_batch_interval(self, interval_ms: int) -> None:
        """Set the batching interval in milliseconds"""
        self._batch_interval = max(10, min(5000, interval_ms))


class ReactiveHealthDataStore(ReactiveDataSource):
    """Specialized reactive data store for health metrics"""
    
    def __init__(self):
        super().__init__()
        self._metric_strategies: Dict[str, UpdateMethod] = {
            'heart_rate': UpdateMethod.IMMEDIATE,
            'steps': UpdateMethod.BATCHED_100MS,
            'calories': UpdateMethod.BATCHED_100MS,
            'distance': UpdateMethod.BATCHED_500MS,
            'sleep': UpdateMethod.BATCHED_1S,
            'weight': UpdateMethod.BATCHED_1S,
        }
        
    def update_metric(self, metric_name: str, value: Any, timestamp: datetime) -> None:
        """Update a specific health metric"""
        strategy = self._metric_strategies.get(metric_name, UpdateMethod.BATCHED_500MS)
        
        # Adjust batch interval based on strategy
        if strategy == UpdateMethod.IMMEDIATE:
            self.set_batch_interval(0)
        elif strategy == UpdateMethod.BATCHED_50MS:
            self.set_batch_interval(50)
        elif strategy == UpdateMethod.BATCHED_100MS:
            self.set_batch_interval(100)
        elif strategy == UpdateMethod.BATCHED_500MS:
            self.set_batch_interval(500)
        else:
            self.set_batch_interval(1000)
            
        # Create new data with the metric update
        new_data = self.data.copy()
        # Add or update the metric
        if timestamp not in new_data.index:
            new_data.loc[timestamp] = {metric_name: value}
        else:
            new_data.loc[timestamp, metric_name] = value
            
        self.update_data(new_data, DataChangeType.UPDATE)


class ReactiveDataBinding(QObject):
    """Manages the binding between data sources and visualizations"""
    
    def __init__(self):
        super().__init__()
        self._bindings: Dict[int, Tuple[ReactiveDataSource, BaseChart]] = {}
        self._binding_counter = 0
        
    def bind(
        self, 
        data_source: ReactiveDataSource, 
        chart: BaseChart,
        transform: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None
    ) -> int:
        """Create a binding between data source and chart"""
        binding_id = self._binding_counter
        self._binding_counter += 1
        
        # Store the binding
        self._bindings[binding_id] = (data_source, chart)
        
        # Create update handler
        def handle_data_change(change: DataChange):
            try:
                # Get latest data
                data = data_source.data
                
                # Apply transformation if provided
                if transform:
                    data = transform(data)
                    
                # Update chart
                chart.data = data
                chart.update()
                
            except Exception as e:
                logger.error(f"Error updating chart: {e}")
                
        # Connect to data changes
        data_source.data_changed.connect(handle_data_change)
        
        # Store connection for cleanup
        chart.destroyed.connect(lambda: self.unbind(binding_id))
        
        # Initial update
        handle_data_change(DataChange(
            DataChangeType.RESET,
            data_source.data,
            datetime.now()
        ))
        
        return binding_id
        
    def unbind(self, binding_id: int) -> None:
        """Remove a data binding"""
        if binding_id in self._bindings:
            del self._bindings[binding_id]
            
    def unbind_all(self) -> None:
        """Remove all data bindings"""
        self._bindings.clear()


class HealthDataUpdateStrategy:
    """Determines optimal update strategies for health data"""
    
    @staticmethod
    def determine_strategy(data_type: str, update_size: int) -> UpdateMethod:
        """Determine the best update method based on data characteristics"""
        if data_type == 'heart_rate' and update_size < 100:
            return UpdateMethod.IMMEDIATE
        elif data_type in ['steps', 'calories'] and update_size < 1000:
            return UpdateMethod.BATCHED_100MS
        elif data_type in ['distance', 'floors'] and update_size < 5000:
            return UpdateMethod.BATCHED_500MS
        else:
            return UpdateMethod.BATCHED_1S


class ReactiveChartWidget(QObject):
    """Chart widget with reactive data binding capabilities"""
    
    # Signals
    data_updated = pyqtSignal(pd.DataFrame)
    update_error = pyqtSignal(str)
    
    def __init__(self, chart_component: BaseChart):
        super().__init__()
        self.chart = chart_component
        self._data_buffer: List[pd.DataFrame] = []
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._process_buffered_updates)
        self._update_timer.setInterval(50)  # 50ms batching
        self._current_subscription: Optional[ReactiveDataSource] = None
        
    def bind_to_data_source(self, data_source: ReactiveDataSource) -> None:
        """Bind chart to reactive data source"""
        # Unbind previous source if any
        if self._current_subscription:
            self._current_subscription.data_changed.disconnect(self._on_data_changed)
            
        # Subscribe to data changes
        data_source.data_changed.connect(self._on_data_changed)
        self._current_subscription = data_source
        
        # Handle cleanup
        self.destroyed.connect(
            lambda: data_source.data_changed.disconnect(self._on_data_changed)
        )
        
        # Initial data load
        self._on_data_changed(DataChange(
            DataChangeType.RESET,
            data_source.data,
            datetime.now()
        ))
        
    @pyqtSlot(object)
    def _on_data_changed(self, change: DataChange) -> None:
        """Handle incoming data changes"""
        # Buffer updates for batch processing
        self._data_buffer.append(change.data)
        
        # Start timer if not running
        if not self._update_timer.isActive():
            self._update_timer.start()
            
    @pyqtSlot()
    def _process_buffered_updates(self) -> None:
        """Process buffered data updates"""
        if not self._data_buffer:
            self._update_timer.stop()
            return
            
        try:
            # Merge buffered updates
            merged_data = self._merge_updates(self._data_buffer)
            self._data_buffer.clear()
            
            # Update chart
            self.chart.data = merged_data
            self.chart.update()
            self.data_updated.emit(merged_data)
            
        except Exception as e:
            self.update_error.emit(str(e))
            logger.error(f"Chart update failed: {e}")
            
    def _merge_updates(self, updates: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge multiple data updates efficiently"""
        if len(updates) == 1:
            return updates[0]
            
        # Concatenate and deduplicate
        merged = pd.concat(updates, ignore_index=True)
        
        # Keep latest values for duplicate timestamps
        if 'timestamp' in merged.columns:
            merged = merged.sort_values('timestamp')
            merged = merged.drop_duplicates(subset=['timestamp'], keep='last')
            
        return merged