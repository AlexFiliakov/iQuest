"""Streaming data loader for efficient processing of large health datasets."""

from typing import Iterator, Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
from contextlib import contextmanager
from queue import Queue
import threading

from ..data_access import DataAccess

logger = logging.getLogger(__name__)


@dataclass
class DataChunk:
    """Represents a chunk of data for processing."""
    data: pd.DataFrame
    start_date: datetime
    end_date: datetime
    chunk_index: int
    total_chunks: int
    metrics: List[str]
    
    @property
    def is_last_chunk(self) -> bool:
        """Check if this is the last chunk."""
        return self.chunk_index == self.total_chunks - 1
    
    @property
    def size_mb(self) -> float:
        """Get chunk size in MB."""
        return self.data.memory_usage(deep=True).sum() / (1024 * 1024)


class StreamingDataLoader:
    """
    Efficient data loader that streams large datasets in chunks.
    
    Features:
    - Configurable chunk size based on time periods or memory limits
    - Lazy loading with iterator pattern
    - Memory-aware chunking
    - Parallel chunk prefetching
    - Progress tracking
    """
    
    def __init__(self, data_access: DataAccess, 
                 chunk_days: int = 30,
                 max_memory_mb: float = 100,
                 prefetch_chunks: int = 2):
        """
        Initialize streaming data loader.
        
        Args:
            data_access: Data access layer
            chunk_days: Number of days per chunk
            max_memory_mb: Maximum memory per chunk in MB
            prefetch_chunks: Number of chunks to prefetch
        """
        self.data_access = data_access
        self.chunk_days = chunk_days
        self.max_memory_mb = max_memory_mb
        self.prefetch_chunks = prefetch_chunks
        self._prefetch_queue = Queue(maxsize=prefetch_chunks)
        self._prefetch_thread = None
        self._stop_prefetching = threading.Event()
        
    def stream_data(self, start_date: datetime, end_date: datetime,
                   metrics: Optional[List[str]] = None,
                   progress_callback: Optional[callable] = None) -> Iterator[DataChunk]:
        """
        Stream data in chunks for the specified date range.
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            metrics: Specific metrics to load (None for all)
            progress_callback: Optional callback for progress updates
            
        Yields:
            DataChunk objects
        """
        # Calculate total chunks
        total_days = (end_date - start_date).days + 1
        total_chunks = (total_days + self.chunk_days - 1) // self.chunk_days
        
        # Start prefetch thread if enabled
        if self.prefetch_chunks > 0:
            self._start_prefetching(start_date, end_date, metrics, total_chunks)
        
        try:
            chunk_index = 0
            current_date = start_date
            
            while current_date <= end_date:
                # Calculate chunk boundaries
                chunk_end = min(
                    current_date + timedelta(days=self.chunk_days - 1),
                    end_date
                )
                
                # Load chunk (from prefetch queue if available)
                if self._prefetch_thread and self._prefetch_thread.is_alive():
                    chunk = self._prefetch_queue.get()
                else:
                    chunk = self._load_chunk(
                        current_date, chunk_end, metrics,
                        chunk_index, total_chunks
                    )
                
                # Update progress
                if progress_callback:
                    progress = (chunk_index + 1) / total_chunks
                    progress_callback(progress, chunk)
                
                yield chunk
                
                # Move to next chunk
                current_date = chunk_end + timedelta(days=1)
                chunk_index += 1
                
        finally:
            # Stop prefetching
            if self._prefetch_thread:
                self._stop_prefetching.set()
                self._prefetch_thread.join()
    
    def stream_by_memory(self, start_date: datetime, end_date: datetime,
                        metrics: Optional[List[str]] = None) -> Iterator[DataChunk]:
        """
        Stream data with adaptive chunk sizes based on memory limits.
        
        This method dynamically adjusts chunk sizes to stay within memory limits.
        """
        total_days = (end_date - start_date).days + 1
        current_date = start_date
        chunk_index = 0
        
        # Estimate total chunks (will be refined as we go)
        estimated_chunks = max(1, total_days // self.chunk_days)
        
        while current_date <= end_date:
            # Start with configured chunk size
            test_days = min(self.chunk_days, (end_date - current_date).days + 1)
            
            # Adaptively find the right chunk size
            while test_days > 0:
                # Sample a small portion to estimate memory usage
                sample_end = min(
                    current_date + timedelta(days=min(7, test_days) - 1),
                    end_date
                )
                
                sample_data = self._load_data_range(
                    current_date, sample_end, metrics
                )
                
                if sample_data.empty:
                    # No data in this range, use full chunk
                    chunk_end = current_date + timedelta(days=test_days - 1)
                    break
                
                # Estimate memory for full chunk
                days_in_sample = (sample_end - current_date).days + 1
                memory_per_day = sample_data.memory_usage(deep=True).sum() / (1024 * 1024) / days_in_sample
                estimated_memory = memory_per_day * test_days
                
                if estimated_memory <= self.max_memory_mb:
                    # This chunk size is acceptable
                    chunk_end = min(
                        current_date + timedelta(days=test_days - 1),
                        end_date
                    )
                    break
                else:
                    # Reduce chunk size
                    test_days = max(1, int(self.max_memory_mb / memory_per_day))
            
            # Load the actual chunk
            chunk_data = self._load_data_range(current_date, chunk_end, metrics)
            
            yield DataChunk(
                data=chunk_data,
                start_date=current_date,
                end_date=chunk_end,
                chunk_index=chunk_index,
                total_chunks=estimated_chunks,
                metrics=metrics or []
            )
            
            current_date = chunk_end + timedelta(days=1)
            chunk_index += 1
    
    def load_optimized(self, start_date: datetime, end_date: datetime,
                      metrics: Optional[List[str]] = None,
                      aggregation: str = 'daily') -> pd.DataFrame:
        """
        Load data with optimizations for the specified aggregation level.
        
        Args:
            start_date: Start date
            end_date: End date  
            metrics: Metrics to load
            aggregation: Aggregation level ('daily', 'weekly', 'monthly')
            
        Returns:
            Optimized DataFrame
        """
        # For daily aggregation, use normal loading
        if aggregation == 'daily':
            return self._load_data_range(start_date, end_date, metrics)
        
        # For weekly/monthly, load pre-aggregated data if available
        if hasattr(self.data_access, f'get_{aggregation}_aggregated'):
            method = getattr(self.data_access, f'get_{aggregation}_aggregated')
            return method(start_date, end_date, metrics)
        
        # Otherwise, load daily and aggregate
        daily_data = self._load_data_range(start_date, end_date, metrics)
        
        if aggregation == 'weekly':
            return self._aggregate_to_weekly(daily_data)
        elif aggregation == 'monthly':
            return self._aggregate_to_monthly(daily_data)
        
        return daily_data
    
    @contextmanager
    def batch_loading_context(self):
        """Context manager for optimized batch loading."""
        # Enable any batch optimizations
        if hasattr(self.data_access, 'enable_batch_mode'):
            self.data_access.enable_batch_mode()
        
        try:
            yield self
        finally:
            # Disable batch mode
            if hasattr(self.data_access, 'disable_batch_mode'):
                self.data_access.disable_batch_mode()
    
    def _load_chunk(self, start_date: datetime, end_date: datetime,
                   metrics: Optional[List[str]], chunk_index: int,
                   total_chunks: int) -> DataChunk:
        """Load a single chunk of data."""
        logger.debug(f"Loading chunk {chunk_index + 1}/{total_chunks}: "
                    f"{start_date.date()} to {end_date.date()}")
        
        data = self._load_data_range(start_date, end_date, metrics)
        
        return DataChunk(
            data=data,
            start_date=start_date,
            end_date=end_date,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            metrics=metrics or []
        )
    
    def _load_data_range(self, start_date: datetime, end_date: datetime,
                        metrics: Optional[List[str]]) -> pd.DataFrame:
        """Load data for a specific date range."""
        try:
            # Use data access layer to load data
            data = self.data_access.get_records_by_date_range(
                start_date=start_date,
                end_date=end_date
            )
            
            # Handle None or empty results
            if data is None:
                logger.warning(f"No data returned for range {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Filter by metrics if specified
            if metrics and not data.empty:
                # Assuming data has a 'type' or 'metric' column
                if 'type' in data.columns:
                    data = data[data['type'].isin(metrics)]
                elif 'metric' in data.columns:
                    data = data[data['metric'].isin(metrics)]
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading data range: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame()
    
    def _start_prefetching(self, start_date: datetime, end_date: datetime,
                          metrics: Optional[List[str]], total_chunks: int):
        """Start background thread for chunk prefetching."""
        self._stop_prefetching.clear()
        
        def prefetch_worker():
            chunk_index = 0
            current_date = start_date
            
            while current_date <= end_date and not self._stop_prefetching.is_set():
                chunk_end = min(
                    current_date + timedelta(days=self.chunk_days - 1),
                    end_date
                )
                
                # Load chunk
                chunk = self._load_chunk(
                    current_date, chunk_end, metrics,
                    chunk_index, total_chunks
                )
                
                # Put in queue (will block if queue is full)
                if not self._stop_prefetching.is_set():
                    self._prefetch_queue.put(chunk)
                
                current_date = chunk_end + timedelta(days=1)
                chunk_index += 1
        
        self._prefetch_thread = threading.Thread(target=prefetch_worker)
        self._prefetch_thread.start()
    
    def _aggregate_to_weekly(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily data to weekly."""
        if data.empty:
            return data
            
        # Ensure date column
        if 'date' not in data.columns and data.index.name == 'date':
            data = data.reset_index()
        
        # Set week start to Monday
        data['week'] = pd.to_datetime(data['date']).dt.to_period('W-MON')
        
        # Group by week and aggregate
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        weekly = data.groupby('week')[numeric_cols].agg(['sum', 'mean', 'min', 'max'])
        
        return weekly
    
    def _aggregate_to_monthly(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily data to monthly."""
        if data.empty:
            return data
            
        # Ensure date column
        if 'date' not in data.columns and data.index.name == 'date':
            data = data.reset_index()
        
        # Extract month
        data['month'] = pd.to_datetime(data['date']).dt.to_period('M')
        
        # Group by month and aggregate
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        monthly = data.groupby('month')[numeric_cols].agg(['sum', 'mean', 'min', 'max'])
        
        return monthly