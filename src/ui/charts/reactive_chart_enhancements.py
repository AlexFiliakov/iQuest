"""
Enhancements to Base Chart for Reactive Data Binding Support

This module provides mixins and enhancements to make charts reactive-ready
without modifying the existing base chart implementation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

import pandas as pd
from PyQt6.QtCore import QObject, QPropertyAnimation, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from src.ui.charts.base_chart import BaseChart
    from src.ui.reactive_data_binding import ReactiveDataSource, DataChange

logger = logging.getLogger(__name__)


class ReactiveChartMixin:
    """
    Mixin to add reactive capabilities to chart widgets.
    This can be mixed into any chart class that inherits from BaseChart.
    """
    
    # Additional signals for reactive behavior
    data_binding_created = pyqtSignal(int)  # binding_id
    data_binding_removed = pyqtSignal(int)  # binding_id
    incremental_update_applied = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Reactive state
        self._reactive_source: Optional[ReactiveDataSource] = None
        self._binding_id: Optional[int] = None
        self._update_strategy: str = 'full_refresh'
        self._last_update_time: Optional[datetime] = None
        self._pending_updates: List[DataChange] = []
        self._incremental_update_enabled: bool = True
        
        # Performance tracking
        self._update_count: int = 0
        self._total_update_time: float = 0
        
    def enable_reactive_updates(self, strategy: str = 'auto') -> None:
        """
        Enable reactive update capabilities.
        
        Args:
            strategy: Update strategy ('full_refresh', 'incremental', 'progressive', 'auto')
        """
        self._update_strategy = strategy
        self._incremental_update_enabled = strategy in ['incremental', 'progressive', 'auto']
        
    def disable_reactive_updates(self) -> None:
        """Disable reactive updates"""
        if self._reactive_source:
            self._disconnect_reactive_source()
            
    def bind_to_reactive_source(self, source: ReactiveDataSource) -> int:
        """
        Bind this chart to a reactive data source.
        
        Returns:
            binding_id for managing the binding
        """
        # Disconnect previous source if any
        if self._reactive_source:
            self._disconnect_reactive_source()
            
        # Store reference and connect
        self._reactive_source = source
        source.data_changed.connect(self._on_reactive_data_change)
        source.batch_updated.connect(self._on_batch_update)
        
        # Generate binding ID
        import random
        self._binding_id = random.randint(1000, 9999)
        
        # Initial data load
        self.data = source.data
        self.update()
        
        self.data_binding_created.emit(self._binding_id)
        return self._binding_id
        
    def _disconnect_reactive_source(self) -> None:
        """Disconnect from reactive data source"""
        if self._reactive_source:
            self._reactive_source.data_changed.disconnect(self._on_reactive_data_change)
            self._reactive_source.batch_updated.disconnect(self._on_batch_update)
            self._reactive_source = None
            
            if self._binding_id:
                self.data_binding_removed.emit(self._binding_id)
                self._binding_id = None
                
    @pyqtSlot(object)
    def _on_reactive_data_change(self, change: DataChange) -> None:
        """Handle single data change from reactive source"""
        if self._update_strategy == 'auto':
            strategy = self._determine_update_strategy(change)
        else:
            strategy = self._update_strategy
            
        if strategy == 'full_refresh':
            self._apply_full_refresh(change.data)
        elif strategy == 'incremental':
            self._pending_updates.append(change)
            QTimer.singleShot(50, self._apply_incremental_updates)
        elif strategy == 'progressive':
            self._apply_progressive_update(change)
            
    @pyqtSlot(list)
    def _on_batch_update(self, changes: List[DataChange]) -> None:
        """Handle batch of data changes"""
        # For batch updates, use incremental strategy
        self._pending_updates.extend(changes)
        self._apply_incremental_updates()
        
    def _determine_update_strategy(self, change: DataChange) -> str:
        """Automatically determine best update strategy"""
        if not hasattr(self, 'data') or self.data is None:
            return 'full_refresh'
            
        data_size = len(self.data) if isinstance(self.data, pd.DataFrame) else 0
        
        # Small datasets or major changes: full refresh
        if data_size < 1000 or change.change_type.name == 'RESET':
            return 'full_refresh'
        # Medium datasets: incremental
        elif data_size < 10000:
            return 'incremental'
        # Large datasets: progressive
        else:
            return 'progressive'
            
    def _apply_full_refresh(self, new_data: pd.DataFrame) -> None:
        """Apply full data refresh with animation"""
        start_time = datetime.now()
        
        # Animate opacity for smooth transition
        if hasattr(self, 'setWindowOpacity'):
            self._fade_transition(lambda: self._update_data_internal(new_data))
        else:
            self._update_data_internal(new_data)
            
        # Track performance
        self._update_count += 1
        self._total_update_time += (datetime.now() - start_time).total_seconds()
        
    def _update_data_internal(self, new_data: pd.DataFrame) -> None:
        """Internal method to update data"""
        self.data = new_data
        self.update()
        
    def _apply_incremental_updates(self) -> None:
        """Apply pending incremental updates"""
        if not self._pending_updates:
            return
            
        start_time = datetime.now()
        
        # Process all pending updates
        for change in self._pending_updates:
            self._apply_single_incremental_update(change)
            
        self._pending_updates.clear()
        
        # Trigger chart update
        self.update()
        self.incremental_update_applied.emit()
        
        # Track performance
        self._update_count += 1
        self._total_update_time += (datetime.now() - start_time).total_seconds()
        
    def _apply_single_incremental_update(self, change: DataChange) -> None:
        """Apply a single incremental update"""
        # This would be implemented based on the specific chart type
        # For now, fall back to full update
        if hasattr(self, 'data') and isinstance(self.data, pd.DataFrame):
            # Apply change to existing data
            # This is a simplified implementation
            self.data = change.data
            
    def _apply_progressive_update(self, change: DataChange) -> None:
        """Apply progressive update for large datasets"""
        # Implementation would load data in chunks
        # For now, use full refresh
        self._apply_full_refresh(change.data)
        
    def _fade_transition(self, update_func: Callable) -> None:
        """Apply fade transition during update"""
        # Fade out
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(100)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.7)
        
        # Update data when faded
        fade_out.finished.connect(update_func)
        
        # Fade back in
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(100)
        fade_in.setStartValue(0.7)
        fade_in.setEndValue(1.0)
        
        fade_out.finished.connect(fade_in.start)
        fade_out.start()
        
    def get_update_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for updates"""
        avg_time = self._total_update_time / self._update_count if self._update_count > 0 else 0
        
        return {
            'total_updates': self._update_count,
            'average_update_time': avg_time,
            'total_update_time': self._total_update_time,
            'update_strategy': self._update_strategy,
            'incremental_enabled': self._incremental_update_enabled
        }


class ReactiveLineChart(ReactiveChartMixin):
    """
    Example of how to create a reactive version of a specific chart type.
    This would be used with the existing LineChart class.
    """
    
    def _apply_single_incremental_update(self, change: DataChange) -> None:
        """Specialized incremental update for line charts"""
        if not hasattr(self, 'data') or not isinstance(self.data, pd.DataFrame):
            return
            
        # For line charts, we can append new points efficiently
        if change.change_type.name == 'ADD':
            # Append new data points
            self.data = pd.concat([self.data, change.data])
            
            # Keep only recent data if needed (sliding window)
            if hasattr(self, 'max_points') and len(self.data) > self.max_points:
                self.data = self.data.iloc[-self.max_points:]
                
        elif change.change_type.name == 'UPDATE':
            # Update existing points
            for idx in change.data.index:
                if idx in self.data.index:
                    self.data.loc[idx] = change.data.loc[idx]
                    
        elif change.change_type.name == 'DELETE':
            # Remove points
            indices_to_remove = change.data.index
            self.data = self.data.drop(indices_to_remove, errors='ignore')


def make_chart_reactive(chart_class: type) -> type:
    """
    Factory function to create a reactive version of any chart class.
    
    Usage:
        ReactiveLineChart = make_chart_reactive(LineChart)
        chart = ReactiveLineChart()
        chart.enable_reactive_updates()
    """
    class ReactiveChart(ReactiveChartMixin, chart_class):
        pass
        
    ReactiveChart.__name__ = f"Reactive{chart_class.__name__}"
    return ReactiveChart


# Utility functions for common reactive patterns

def create_reactive_heart_rate_monitor(chart: BaseChart) -> None:
    """Configure a chart for real-time heart rate monitoring"""
    if hasattr(chart, 'enable_reactive_updates'):
        chart.enable_reactive_updates('incremental')
        
        # Configure for real-time display
        if hasattr(chart, 'max_points'):
            chart.max_points = 300  # Show last 5 minutes at 1Hz
            
        # Set update animations
        if hasattr(chart, 'setAnimationDuration'):
            chart.setAnimationDuration(50)  # Fast animations
            
            
def create_reactive_activity_dashboard(chart: BaseChart) -> None:
    """Configure a chart for activity dashboard with hourly updates"""
    if hasattr(chart, 'enable_reactive_updates'):
        chart.enable_reactive_updates('auto')
        
        # Configure for dashboard display
        if hasattr(chart, 'setUpdateInterval'):
            chart.setUpdateInterval(1000)  # Update every second
            
            
def create_reactive_sleep_tracker(chart: BaseChart) -> None:
    """Configure a chart for sleep tracking with daily updates"""
    if hasattr(chart, 'enable_reactive_updates'):
        chart.enable_reactive_updates('full_refresh')
        
        # Configure for daily updates
        if hasattr(chart, 'setAnimationDuration'):
            chart.setAnimationDuration(500)  # Smooth transitions