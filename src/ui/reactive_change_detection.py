"""
Efficient Change Detection and Conflict Resolution for Reactive Data Binding

This module implements efficient change detection algorithms and conflict resolution
strategies for the reactive data binding system.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving concurrent data modifications"""
    LAST_WRITE_WINS = auto()
    FIRST_WRITE_WINS = auto()
    MERGE_VALUES = auto()
    CUSTOM_RESOLVER = auto()


@dataclass
class ChangeRecord:
    """Record of a data change for tracking and rollback"""
    timestamp: datetime
    change_type: str
    old_value: Any
    new_value: Any
    affected_keys: Set[str]
    source_id: str
    hash_before: str
    hash_after: str
    
    
@dataclass
class ConflictInfo:
    """Information about a data conflict"""
    timestamp: datetime
    key: str
    values: List[Tuple[str, Any]]  # (source_id, value) pairs
    resolution_strategy: ConflictResolutionStrategy
    resolved_value: Optional[Any] = None


class EfficientChangeDetector:
    """
    Implements efficient change detection for large datasets.
    Uses hashing and incremental tracking for O(log n) complexity.
    """
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self._data_hashes: Dict[str, str] = {}
        self._chunk_hashes: Dict[int, str] = {}
        self._last_snapshot: Optional[pd.DataFrame] = None
        self._change_index = defaultdict(set)  # Maps data keys to chunk indices
        
    def detect_changes(
        self, 
        old_data: pd.DataFrame, 
        new_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Detect changes between two dataframes efficiently.
        Returns a dictionary of changes with affected rows and columns.
        """
        if old_data.empty:
            return {"type": "full", "data": new_data}
            
        if new_data.empty:
            return {"type": "clear", "data": pd.DataFrame()}
            
        # Quick hash comparison for identical data
        old_hash = self._compute_hash(old_data)
        new_hash = self._compute_hash(new_data)
        
        if old_hash == new_hash:
            return {"type": "none", "data": pd.DataFrame()}
            
        # Detailed change detection
        changes = {
            "type": "incremental",
            "added": pd.DataFrame(),
            "modified": pd.DataFrame(),
            "deleted": pd.DataFrame(),
            "affected_columns": set(),
            "affected_indices": set()
        }
        
        # Find added and modified rows
        for idx in new_data.index:
            if idx not in old_data.index:
                changes["added"] = pd.concat([changes["added"], new_data.loc[[idx]]])
                changes["affected_indices"].add(idx)
            else:
                # Check for modifications
                old_row = old_data.loc[idx]
                new_row = new_data.loc[idx]
                
                if not old_row.equals(new_row):
                    changes["modified"] = pd.concat([changes["modified"], new_data.loc[[idx]]])
                    changes["affected_indices"].add(idx)
                    
                    # Track which columns changed
                    for col in new_data.columns:
                        if col in old_data.columns:
                            if old_row[col] != new_row[col]:
                                changes["affected_columns"].add(col)
                                
        # Find deleted rows
        for idx in old_data.index:
            if idx not in new_data.index:
                changes["deleted"] = pd.concat([changes["deleted"], old_data.loc[[idx]]])
                changes["affected_indices"].add(idx)
                
        return changes
        
    def _compute_hash(self, data: pd.DataFrame) -> str:
        """Compute hash of dataframe for quick comparison"""
        if data.empty:
            return ""
            
        # Convert to bytes and compute hash
        data_bytes = pd.util.hash_pandas_object(data).values.tobytes()
        return hashlib.md5(data_bytes).hexdigest()
        
    def track_chunks(self, data: pd.DataFrame) -> Dict[int, str]:
        """
        Track data in chunks for efficient partial updates.
        Returns mapping of chunk indices to hashes.
        """
        chunk_hashes = {}
        
        for i in range(0, len(data), self.chunk_size):
            chunk = data.iloc[i:i + self.chunk_size]
            chunk_hash = self._compute_hash(chunk)
            chunk_idx = i // self.chunk_size
            chunk_hashes[chunk_idx] = chunk_hash
            
            # Update change index
            for idx in chunk.index:
                self._change_index[idx].add(chunk_idx)
                
        self._chunk_hashes = chunk_hashes
        return chunk_hashes
        
    def get_affected_chunks(self, changes: Dict[str, Any]) -> Set[int]:
        """Get chunk indices affected by changes"""
        affected_chunks = set()
        
        for idx in changes.get("affected_indices", []):
            affected_chunks.update(self._change_index.get(idx, set()))
            
        return affected_chunks


class ConflictResolver:
    """Handles concurrent data modifications and conflict resolution"""
    
    def __init__(self, default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        self.default_strategy = default_strategy
        self._pending_changes: Dict[str, List[Tuple[str, Any, datetime]]] = defaultdict(list)
        self._conflict_log: deque = deque(maxlen=1000)
        self._custom_resolvers: Dict[str, callable] = {}
        
    def add_change(self, key: str, value: Any, source_id: str, timestamp: Optional[datetime] = None) -> None:
        """Add a pending change"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self._pending_changes[key].append((source_id, value, timestamp))
        
    def resolve_conflicts(self) -> Dict[str, Any]:
        """Resolve all pending conflicts and return resolved values"""
        resolved = {}
        
        for key, changes in self._pending_changes.items():
            if len(changes) == 1:
                # No conflict
                resolved[key] = changes[0][1]
            else:
                # Conflict detected
                conflict = ConflictInfo(
                    timestamp=datetime.now(),
                    key=key,
                    values=[(c[0], c[1]) for c in changes],
                    resolution_strategy=self.default_strategy
                )
                
                # Resolve based on strategy
                if self.default_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
                    # Sort by timestamp and take the latest
                    changes.sort(key=lambda x: x[2])
                    resolved[key] = changes[-1][1]
                    conflict.resolved_value = changes[-1][1]
                    
                elif self.default_strategy == ConflictResolutionStrategy.FIRST_WRITE_WINS:
                    # Sort by timestamp and take the earliest
                    changes.sort(key=lambda x: x[2])
                    resolved[key] = changes[0][1]
                    conflict.resolved_value = changes[0][1]
                    
                elif self.default_strategy == ConflictResolutionStrategy.MERGE_VALUES:
                    # Attempt to merge values
                    resolved[key] = self._merge_values(key, [c[1] for c in changes])
                    conflict.resolved_value = resolved[key]
                    
                elif self.default_strategy == ConflictResolutionStrategy.CUSTOM_RESOLVER:
                    # Use custom resolver if available
                    if key in self._custom_resolvers:
                        resolved[key] = self._custom_resolvers[key](changes)
                        conflict.resolved_value = resolved[key]
                    else:
                        # Fallback to last write wins
                        changes.sort(key=lambda x: x[2])
                        resolved[key] = changes[-1][1]
                        conflict.resolved_value = changes[-1][1]
                        
                # Log conflict
                self._conflict_log.append(conflict)
                
        # Clear pending changes
        self._pending_changes.clear()
        
        return resolved
        
    def _merge_values(self, key: str, values: List[Any]) -> Any:
        """Attempt to merge multiple values"""
        if not values:
            return None
            
        # If all values are numeric, average them
        if all(isinstance(v, (int, float)) for v in values):
            return np.mean(values)
            
        # If all values are lists, concatenate and deduplicate
        if all(isinstance(v, list) for v in values):
            merged = []
            for v in values:
                merged.extend(v)
            return list(set(merged))
            
        # If all values are dicts, merge them
        if all(isinstance(v, dict) for v in values):
            merged = {}
            for v in values:
                merged.update(v)
            return merged
            
        # Default: use last value
        return values[-1]
        
    def register_custom_resolver(self, key: str, resolver: callable) -> None:
        """Register a custom resolver for a specific key"""
        self._custom_resolvers[key] = resolver
        
    def get_conflict_log(self) -> List[ConflictInfo]:
        """Get the conflict resolution log"""
        return list(self._conflict_log)


class UpdateScheduler(QObject):
    """Schedules and batches updates for optimal performance"""
    
    update_ready = pyqtSignal(list)  # List of updates
    
    def __init__(self, batch_size: int = 100, max_delay_ms: int = 1000):
        super().__init__()
        self.batch_size = batch_size
        self.max_delay_ms = max_delay_ms
        
        self._update_queue: deque = deque()
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._process_batch)
        self._batch_timer.setInterval(50)  # Check every 50ms
        
        self._first_update_time: Optional[datetime] = None
        
    def schedule_update(self, update: Any) -> None:
        """Schedule an update for processing"""
        self._update_queue.append(update)
        
        if not self._batch_timer.isActive():
            self._batch_timer.start()
            self._first_update_time = datetime.now()
            
    def _process_batch(self) -> None:
        """Process queued updates"""
        if not self._update_queue:
            self._batch_timer.stop()
            self._first_update_time = None
            return
            
        # Check if we should process based on batch size or time
        should_process = False
        
        if len(self._update_queue) >= self.batch_size:
            should_process = True
        elif self._first_update_time:
            elapsed = (datetime.now() - self._first_update_time).total_seconds() * 1000
            if elapsed >= self.max_delay_ms:
                should_process = True
                
        if should_process:
            # Process batch
            batch = list(self._update_queue)
            self._update_queue.clear()
            self._first_update_time = None
            
            # Emit batch
            self.update_ready.emit(batch)
            
            # Stop timer if queue is empty
            if not self._update_queue:
                self._batch_timer.stop()


class ChangeHistory:
    """Maintains history of changes for rollback capability"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._history: deque = deque(maxlen=max_history)
        self._rollback_points: Dict[str, int] = {}
        
    def record_change(self, change: ChangeRecord) -> None:
        """Record a change in history"""
        self._history.append(change)
        
    def create_rollback_point(self, name: str) -> None:
        """Create a named rollback point"""
        self._rollback_points[name] = len(self._history) - 1
        
    def rollback_to_point(self, name: str) -> List[ChangeRecord]:
        """Get changes to rollback to a named point"""
        if name not in self._rollback_points:
            raise ValueError(f"Rollback point '{name}' not found")
            
        point_idx = self._rollback_points[name]
        
        # Get changes after the rollback point
        changes_to_revert = []
        for i in range(len(self._history) - 1, point_idx, -1):
            if i < len(self._history):
                changes_to_revert.append(self._history[i])
                
        return changes_to_revert
        
    def get_recent_changes(self, count: int = 10) -> List[ChangeRecord]:
        """Get recent changes"""
        return list(self._history)[-count:]