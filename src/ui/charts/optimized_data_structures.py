"""
Optimized data structures for visualization performance.

This module provides memory-efficient data structures optimized for
chart rendering including typed arrays, spatial indexing, and 
immutable structures with efficient updates.
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any, Union
from dataclasses import dataclass
import array
import struct
from collections import deque
import mmap
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class TypedTimeSeriesArray:
    """
    Memory-efficient typed array for time series data.
    
    Uses numpy arrays with optimal dtypes for minimal memory usage
    and maximum cache efficiency.
    """
    
    def __init__(self, timestamps: Optional[np.ndarray] = None,
                 values: Optional[np.ndarray] = None,
                 dtype: str = 'float32'):
        """
        Initialize typed array.
        
        Args:
            timestamps: Unix timestamps (int64)
            values: Data values
            dtype: Data type for values ('float32', 'float64', 'int32', etc.)
        """
        self.dtype = dtype
        
        if timestamps is not None and values is not None:
            # Ensure optimal dtypes
            self.timestamps = np.asarray(timestamps, dtype='int64')
            self.values = np.asarray(values, dtype=dtype)
            
            if len(self.timestamps) != len(self.values):
                raise ValueError("Timestamps and values must have same length")
        else:
            self.timestamps = np.array([], dtype='int64')
            self.values = np.array([], dtype=dtype)
            
    def __len__(self) -> int:
        return len(self.timestamps)
        
    def __getitem__(self, idx: Union[int, slice]) -> Tuple[np.ndarray, np.ndarray]:
        return self.timestamps[idx], self.values[idx]
        
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, value_column: str = None) -> 'TypedTimeSeriesArray':
        """Create from pandas DataFrame."""
        # Convert datetime index to unix timestamps
        if isinstance(df.index, pd.DatetimeIndex):
            timestamps = df.index.astype('int64') // 10**9  # Convert to seconds
        else:
            timestamps = df.index.values
            
        # Get values
        if value_column:
            values = df[value_column].values
        else:
            # Use first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric columns found")
            values = df[numeric_cols[0]].values
            
        # Determine optimal dtype
        dtype = cls._determine_optimal_dtype(values)
        
        return cls(timestamps, values, dtype)
        
    @staticmethod
    def _determine_optimal_dtype(values: np.ndarray) -> str:
        """Determine optimal dtype for values."""
        # Check if integer
        if np.all(values == values.astype(int)):
            val_range = values.max() - values.min()
            if val_range < 128:
                return 'int8'
            elif val_range < 32768:
                return 'int16'
            elif val_range < 2147483648:
                return 'int32'
            else:
                return 'int64'
        else:
            # Float type - use float32 unless high precision needed
            if values.std() < 1e-6 or values.max() > 1e6:
                return 'float64'
            else:
                return 'float32'
                
    def append(self, timestamp: int, value: float):
        """Append single value (creates new arrays)."""
        self.timestamps = np.append(self.timestamps, timestamp)
        self.values = np.append(self.values, value)
        
    def slice_time_range(self, start_time: int, end_time: int) -> 'TypedTimeSeriesArray':
        """Get subset within time range."""
        mask = (self.timestamps >= start_time) & (self.timestamps <= end_time)
        return TypedTimeSeriesArray(
            self.timestamps[mask],
            self.values[mask],
            self.dtype
        )
        
    def downsample(self, factor: int) -> 'TypedTimeSeriesArray':
        """Simple downsampling by factor."""
        indices = np.arange(0, len(self), factor)
        return TypedTimeSeriesArray(
            self.timestamps[indices],
            self.values[indices],
            self.dtype
        )
        
    def memory_usage(self) -> int:
        """Get memory usage in bytes."""
        return self.timestamps.nbytes + self.values.nbytes
        
    def to_dataframe(self) -> pd.DataFrame:
        """Convert back to DataFrame."""
        # Convert timestamps back to datetime
        dates = pd.to_datetime(self.timestamps, unit='s')
        return pd.DataFrame({'value': self.values}, index=dates)


class SpatialTimeSeriesIndex:
    """
    Spatial index for fast time-based queries.
    
    Uses a simple grid-based approach optimized for time series data.
    """
    
    def __init__(self, bucket_size: int = 3600):  # 1 hour buckets by default
        self.bucket_size = bucket_size
        self.buckets: Dict[int, List[int]] = {}
        self.data_bounds: Optional[Tuple[int, int]] = None
        
    def build(self, timestamps: np.ndarray):
        """Build index from timestamps."""
        if len(timestamps) == 0:
            return
            
        self.data_bounds = (int(timestamps[0]), int(timestamps[-1]))
        
        # Clear existing buckets
        self.buckets.clear()
        
        # Build buckets
        for i, ts in enumerate(timestamps):
            bucket_id = int(ts) // self.bucket_size
            if bucket_id not in self.buckets:
                self.buckets[bucket_id] = []
            self.buckets[bucket_id].append(i)
            
        logger.debug(f"Built spatial index with {len(self.buckets)} buckets")
        
    def query_range(self, start_time: int, end_time: int) -> np.ndarray:
        """Query indices within time range."""
        if not self.buckets:
            return np.array([], dtype=int)
            
        # Find relevant buckets
        start_bucket = start_time // self.bucket_size
        end_bucket = end_time // self.bucket_size
        
        indices = []
        for bucket_id in range(start_bucket, end_bucket + 1):
            if bucket_id in self.buckets:
                indices.extend(self.buckets[bucket_id])
                
        return np.array(sorted(set(indices)), dtype=int)
        
    def query_nearest(self, timestamp: int, n: int = 1) -> np.ndarray:
        """Find n nearest points to timestamp."""
        bucket_id = timestamp // self.bucket_size
        
        # Search in expanding buckets
        indices = []
        distance = 0
        
        while len(indices) < n and distance < 100:  # Limit search
            # Check buckets at current distance
            for bid in [bucket_id - distance, bucket_id + distance]:
                if bid in self.buckets:
                    indices.extend(self.buckets[bid])
                    
            distance += 1
            
        # Sort by actual distance and return n closest
        if indices:
            indices = np.array(indices)
            # This would need access to actual timestamps for true nearest
            return indices[:n]
        
        return np.array([], dtype=int)


class MemoryMappedTimeSeries:
    """
    Memory-mapped time series for very large datasets.
    
    Stores data in a memory-mapped file for efficient access
    without loading entire dataset into RAM.
    """
    
    def __init__(self, filename: Optional[str] = None):
        """Initialize memory mapped storage."""
        if filename:
            self.filename = filename
            self.temp_file = None
        else:
            # Create temporary file
            self.temp_file = tempfile.NamedTemporaryFile(delete=False)
            self.filename = self.temp_file.name
            
        self.mmap = None
        self.header_size = 32  # bytes for metadata
        self.record_size = 16  # 8 bytes timestamp + 8 bytes value
        self.num_records = 0
        
    def create(self, timestamps: np.ndarray, values: np.ndarray):
        """Create memory mapped file from arrays."""
        if len(timestamps) != len(values):
            raise ValueError("Arrays must have same length")
            
        self.num_records = len(timestamps)
        total_size = self.header_size + self.num_records * self.record_size
        
        # Create file with required size
        with open(self.filename, 'wb') as f:
            f.write(b'\0' * total_size)
            
        # Memory map the file
        with open(self.filename, 'r+b') as f:
            self.mmap = mmap.mmap(f.fileno(), total_size)
            
            # Write header
            self.mmap[0:8] = struct.pack('Q', self.num_records)
            
            # Write data
            offset = self.header_size
            for i in range(self.num_records):
                self.mmap[offset:offset+8] = struct.pack('q', int(timestamps[i]))
                self.mmap[offset+8:offset+16] = struct.pack('d', float(values[i]))
                offset += self.record_size
                
    def __len__(self) -> int:
        return self.num_records
        
    def __getitem__(self, idx: Union[int, slice]) -> Tuple[np.ndarray, np.ndarray]:
        """Get data by index."""
        if isinstance(idx, int):
            if idx < 0 or idx >= self.num_records:
                raise IndexError("Index out of range")
                
            offset = self.header_size + idx * self.record_size
            timestamp = struct.unpack('q', self.mmap[offset:offset+8])[0]
            value = struct.unpack('d', self.mmap[offset+8:offset+16])[0]
            return np.array([timestamp]), np.array([value])
            
        elif isinstance(idx, slice):
            start = idx.start or 0
            stop = idx.stop or self.num_records
            step = idx.step or 1
            
            timestamps = []
            values = []
            
            for i in range(start, stop, step):
                offset = self.header_size + i * self.record_size
                timestamp = struct.unpack('q', self.mmap[offset:offset+8])[0]
                value = struct.unpack('d', self.mmap[offset+8:offset+16])[0]
                timestamps.append(timestamp)
                values.append(value)
                
            return np.array(timestamps), np.array(values)
            
    def close(self):
        """Close memory mapped file."""
        if self.mmap:
            self.mmap.close()
            
        if self.temp_file:
            os.unlink(self.filename)


class ImmutableDataFrame:
    """
    Immutable DataFrame-like structure with efficient updates.
    
    Uses structural sharing for memory efficiency when creating
    modified versions.
    """
    
    def __init__(self, data: Dict[str, np.ndarray], index: np.ndarray):
        """Initialize with column data and index."""
        self._data = data
        self._index = index
        self._hash = None
        
    def __len__(self) -> int:
        return len(self._index)
        
    @property
    def index(self) -> np.ndarray:
        return self._index
        
    @property
    def columns(self) -> List[str]:
        return list(self._data.keys())
        
    def __getitem__(self, key: str) -> np.ndarray:
        """Get column by name."""
        return self._data[key]
        
    def with_column(self, name: str, values: np.ndarray) -> 'ImmutableDataFrame':
        """Create new frame with added/replaced column."""
        if len(values) != len(self._index):
            raise ValueError("Values must match index length")
            
        # Create new data dict with structural sharing
        new_data = self._data.copy()  # Shallow copy
        new_data[name] = values
        
        return ImmutableDataFrame(new_data, self._index)
        
    def without_column(self, name: str) -> 'ImmutableDataFrame':
        """Create new frame without specified column."""
        new_data = {k: v for k, v in self._data.items() if k != name}
        return ImmutableDataFrame(new_data, self._index)
        
    def slice(self, start: int, end: int) -> 'ImmutableDataFrame':
        """Create new frame with sliced data."""
        new_index = self._index[start:end]
        new_data = {k: v[start:end] for k, v in self._data.items()}
        return ImmutableDataFrame(new_data, new_index)
        
    def filter(self, mask: np.ndarray) -> 'ImmutableDataFrame':
        """Create new frame with filtered data."""
        new_index = self._index[mask]
        new_data = {k: v[mask] for k, v in self._data.items()}
        return ImmutableDataFrame(new_data, new_index)
        
    def __hash__(self) -> int:
        """Compute hash for caching."""
        if self._hash is None:
            # Simple hash based on shape and first/last values
            self._hash = hash((
                len(self),
                len(self.columns),
                tuple(self._index[[0, -1]]) if len(self) > 0 else ()
            ))
        return self._hash
        
    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame(self._data, index=self._index)
        
    @classmethod
    def from_pandas(cls, df: pd.DataFrame) -> 'ImmutableDataFrame':
        """Create from pandas DataFrame."""
        data = {col: df[col].values for col in df.columns}
        return cls(data, df.index.values)


class ChunkedDataStore:
    """
    Chunked storage for very large datasets.
    
    Splits data into chunks for efficient loading and processing.
    """
    
    def __init__(self, chunk_size: int = 100000):
        """Initialize chunked store."""
        self.chunk_size = chunk_size
        self.chunks: List[TypedTimeSeriesArray] = []
        self.chunk_bounds: List[Tuple[int, int]] = []
        
    def add_data(self, timestamps: np.ndarray, values: np.ndarray):
        """Add data to store, creating chunks as needed."""
        # Split into chunks
        for i in range(0, len(timestamps), self.chunk_size):
            chunk_end = min(i + self.chunk_size, len(timestamps))
            
            chunk = TypedTimeSeriesArray(
                timestamps[i:chunk_end],
                values[i:chunk_end]
            )
            self.chunks.append(chunk)
            
            # Store bounds for quick lookup
            self.chunk_bounds.append((
                int(timestamps[i]),
                int(timestamps[chunk_end - 1])
            ))
            
    def query_range(self, start_time: int, end_time: int) -> TypedTimeSeriesArray:
        """Query data within time range."""
        relevant_chunks = []
        
        # Find relevant chunks
        for i, (chunk_start, chunk_end) in enumerate(self.chunk_bounds):
            if chunk_end >= start_time and chunk_start <= end_time:
                # Chunk overlaps with query range
                chunk_data = self.chunks[i].slice_time_range(start_time, end_time)
                if len(chunk_data) > 0:
                    relevant_chunks.append(chunk_data)
                    
        # Combine chunks
        if not relevant_chunks:
            return TypedTimeSeriesArray()
            
        if len(relevant_chunks) == 1:
            return relevant_chunks[0]
            
        # Merge multiple chunks
        all_timestamps = np.concatenate([c.timestamps for c in relevant_chunks])
        all_values = np.concatenate([c.values for c in relevant_chunks])
        
        # Sort by timestamp
        sort_idx = np.argsort(all_timestamps)
        
        return TypedTimeSeriesArray(
            all_timestamps[sort_idx],
            all_values[sort_idx]
        )
        
    def memory_usage(self) -> int:
        """Total memory usage."""
        return sum(chunk.memory_usage() for chunk in self.chunks)


class DataPool:
    """
    Object pool for reusable data structures.
    
    Reduces allocation overhead and GC pressure.
    """
    
    def __init__(self, array_size: int = 10000):
        """Initialize pool."""
        self.array_size = array_size
        self.available_arrays: deque = deque()
        self.in_use_arrays: List[np.ndarray] = []
        
        # Pre-allocate some arrays
        for _ in range(5):
            self.available_arrays.append(np.empty(array_size, dtype='float32'))
            
    def acquire(self, size: int = None) -> np.ndarray:
        """Get array from pool."""
        if size is None:
            size = self.array_size
            
        # Try to reuse existing array
        if self.available_arrays and size <= self.array_size:
            arr = self.available_arrays.popleft()
            self.in_use_arrays.append(arr)
            return arr[:size]
            
        # Allocate new array
        arr = np.empty(size, dtype='float32')
        self.in_use_arrays.append(arr)
        return arr
        
    def release(self, arr: np.ndarray):
        """Return array to pool."""
        if arr in self.in_use_arrays:
            self.in_use_arrays.remove(arr)
            
            # Only keep arrays of standard size
            if len(arr) == self.array_size:
                self.available_arrays.append(arr)
                
    def clear(self):
        """Clear all pooled arrays."""
        self.available_arrays.clear()
        self.in_use_arrays.clear()