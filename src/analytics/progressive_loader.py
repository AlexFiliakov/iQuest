"""Progressive loading infrastructure for responsive UI updates."""

from typing import Any, Callable, Optional, Dict, List, Generator, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
import queue
import time
import logging
from enum import Enum, auto

from .streaming_data_loader import DataChunk, StreamingDataLoader
from .computation_queue import ComputationQueue, TaskPriority

logger = logging.getLogger(__name__)


class LoadingStage(Enum):
    """Stages of progressive loading."""
    INITIAL = auto()      # Skeleton/placeholder shown
    FIRST_DATA = auto()   # First chunk loaded
    PARTIAL = auto()      # Some data loaded
    COMPLETE = auto()     # All data loaded
    ERROR = auto()        # Loading failed


@dataclass
class ProgressiveResult:
    """Result container for progressive loading."""
    stage: LoadingStage
    data: Any
    progress: float  # 0.0 to 1.0
    message: str
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if loading is complete."""
        return self.stage in (LoadingStage.COMPLETE, LoadingStage.ERROR)
    
    @property
    def has_data(self) -> bool:
        """Check if any data is available."""
        return self.data is not None and self.stage != LoadingStage.ERROR


class ProgressiveLoaderCallbacks:
    """Callbacks for progressive loading events."""
    
    def __init__(self):
        self.on_loading_started: Optional[Callable[[], None]] = None
        self.on_skeleton_ready: Optional[Callable[[dict], None]] = None
        self.on_first_data_ready: Optional[Callable[[ProgressiveResult], None]] = None
        self.on_progress_update: Optional[Callable[[ProgressiveResult], None]] = None
        self.on_loading_complete: Optional[Callable[[ProgressiveResult], None]] = None
        self.on_loading_error: Optional[Callable[[str], None]] = None


class ProgressiveLoader:
    """
    Progressive loading manager for analytics computations.
    
    Uses callbacks for UI updates at different loading stages:
    - Initial skeleton/placeholder
    - First data chunk (< 100ms)
    - Incremental updates
    - Final complete data
    """
    
    def __init__(self, 
                 data_loader: StreamingDataLoader,
                 computation_queue: ComputationQueue,
                 first_data_timeout_ms: int = 100,
                 callbacks: Optional[ProgressiveLoaderCallbacks] = None):
        """
        Initialize progressive loader.
        
        Args:
            data_loader: Streaming data loader
            computation_queue: Computation queue
            first_data_timeout_ms: Target time for first data
            callbacks: Optional callbacks for events
        """
        self.data_loader = data_loader
        self.computation_queue = computation_queue
        self.first_data_timeout_ms = first_data_timeout_ms
        self.callbacks = callbacks or ProgressiveLoaderCallbacks()
        
        # Active loading sessions
        self._sessions: Dict[str, LoadingSession] = {}
        
        # Timer simulation without Qt
        self._timer_thread = None
        
    def load_progressive(self,
                        computation_func: Callable,
                        start_date: datetime,
                        end_date: datetime,
                        metrics: Optional[List[str]] = None,
                        skeleton_config: Optional[Dict] = None) -> str:
        """
        Start progressive loading of analytics data.
        
        Args:
            computation_func: Function to compute analytics
            start_date: Start date
            end_date: End date
            metrics: Metrics to load
            skeleton_config: Configuration for skeleton UI
            
        Returns:
            Session ID for tracking
        """
        session = LoadingSession(
            loader=self,
            computation_func=computation_func,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            skeleton_config=skeleton_config
        )
        
        self._sessions[session.session_id] = session
        session.start()
        
        return session.session_id
    
    def cancel_loading(self, session_id: str):
        """Cancel a loading session."""
        session = self._sessions.get(session_id)
        if session:
            session.cancel()
            del self._sessions[session_id]
    
    def get_session_status(self, session_id: str) -> Optional[LoadingStage]:
        """Get current stage of a loading session."""
        session = self._sessions.get(session_id)
        return session.current_stage if session else None


class LoadingSession:
    """Individual progressive loading session."""
    
    def __init__(self,
                 loader: ProgressiveLoader,
                 computation_func: Callable,
                 start_date: datetime,
                 end_date: datetime,
                 metrics: Optional[List[str]] = None,
                 skeleton_config: Optional[Dict] = None):
        """Initialize loading session."""
        self.loader = loader
        self.computation_func = computation_func
        self.start_date = start_date
        self.end_date = end_date
        self.metrics = metrics
        self.skeleton_config = skeleton_config or {}
        
        # Session tracking
        self.session_id = f"session_{int(time.time() * 1000)}"
        self.current_stage = LoadingStage.INITIAL
        self.accumulated_data = []
        self.total_chunks = 0
        self.processed_chunks = 0
        
        # Threading
        self._cancel_event = threading.Event()
        self._first_data_event = threading.Event()
        self._loading_thread = None
        
        # Timing
        self.start_time = None
        self.first_data_time = None
        
    def start(self):
        """Start the loading session."""
        self.start_time = time.time()
        
        # Call loading started callback
        if self.loader.callbacks.on_loading_started:
            self.loader.callbacks.on_loading_started()
        
        # Show skeleton immediately
        self._emit_skeleton()
        
        # Start loading in background
        self._loading_thread = threading.Thread(
            target=self._load_data,
            daemon=True
        )
        self._loading_thread.start()
        
        # Set timer for first data using threading
        timer_thread = threading.Timer(
            self.loader.first_data_timeout_ms / 1000.0,
            self._check_first_data
        )
        timer_thread.daemon = True
        timer_thread.start()
    
    def cancel(self):
        """Cancel the loading session."""
        self._cancel_event.set()
        if self._loading_thread:
            self._loading_thread.join(timeout=1)
    
    def _emit_skeleton(self):
        """Emit skeleton configuration."""
        skeleton_config = {
            'type': 'analytics',
            'date_range': f"{self.start_date.date()} - {self.end_date.date()}",
            'metrics': self.metrics or ['all'],
            **self.skeleton_config
        }
        if self.loader.callbacks.on_skeleton_ready:
            self.loader.callbacks.on_skeleton_ready(skeleton_config)
    
    def _load_data(self):
        """Load data progressively in background thread."""
        try:
            # Stream data in chunks
            chunk_generator = self.data_loader.stream_data(
                start_date=self.start_date,
                end_date=self.end_date,
                metrics=self.metrics,
                progress_callback=self._chunk_progress
            )
            
            # Process chunks
            for chunk in chunk_generator:
                if self._cancel_event.is_set():
                    break
                
                # Submit computation to queue
                task_id = self.loader.computation_queue.submit(
                    self._process_chunk,
                    chunk,
                    priority=TaskPriority.CRITICAL,
                    cpu_bound=True
                )
                
                # Wait for result
                try:
                    result = self.loader.computation_queue.get_result(
                        task_id, 
                        timeout=10
                    )
                    
                    # Accumulate results
                    self.accumulated_data.append(result)
                    self.processed_chunks += 1
                    
                    # Emit first data if not done yet
                    if not self._first_data_event.is_set():
                        self._first_data_event.set()
                        self.first_data_time = time.time()
                        self._emit_first_data(result)
                    else:
                        # Emit progress update
                        self._emit_progress()
                    
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
                    self._emit_error(str(e))
                    return
            
            # All chunks processed
            if not self._cancel_event.is_set():
                self._emit_complete()
                
        except Exception as e:
            logger.error(f"Error in progressive loading: {e}")
            self._emit_error(str(e))
    
    def _process_chunk(self, chunk: DataChunk) -> Any:
        """Process a single data chunk."""
        return self.computation_func(chunk.data)
    
    def _chunk_progress(self, progress: float, chunk: DataChunk):
        """Handle chunk loading progress."""
        self.total_chunks = chunk.total_chunks
        
        if self.processed_chunks == 0:
            # Update skeleton with real chunk info
            self.skeleton_config['total_chunks'] = self.total_chunks
            self.skeleton_config['estimated_time'] = self._estimate_completion_time()
            self._emit_skeleton()
    
    def _emit_first_data(self, data: Any):
        """Emit first data result."""
        self.current_stage = LoadingStage.FIRST_DATA
        
        result = ProgressiveResult(
            stage=self.current_stage,
            data=data,
            progress=self.processed_chunks / self.total_chunks,
            message=f"Loaded {self.processed_chunks} of {self.total_chunks} chunks",
            metadata={
                'load_time_ms': int((self.first_data_time - self.start_time) * 1000),
                'chunks_loaded': self.processed_chunks
            }
        )
        
        if self.loader.callbacks.on_first_data_ready:
            self.loader.callbacks.on_first_data_ready(result)
    
    def _emit_progress(self):
        """Emit progress update."""
        self.current_stage = LoadingStage.PARTIAL
        
        # Combine accumulated data
        combined_data = self._combine_results(self.accumulated_data)
        
        result = ProgressiveResult(
            stage=self.current_stage,
            data=combined_data,
            progress=self.processed_chunks / self.total_chunks,
            message=f"Loaded {self.processed_chunks} of {self.total_chunks} chunks",
            metadata={
                'chunks_loaded': self.processed_chunks,
                'estimated_remaining': self._estimate_completion_time()
            }
        )
        
        if self.loader.callbacks.on_progress_update:
            self.loader.callbacks.on_progress_update(result)
    
    def _emit_complete(self):
        """Emit completion signal."""
        self.current_stage = LoadingStage.COMPLETE
        
        # Final combination of all results
        final_data = self._combine_results(self.accumulated_data)
        
        result = ProgressiveResult(
            stage=self.current_stage,
            data=final_data,
            progress=1.0,
            message="Loading complete",
            metadata={
                'total_time_ms': int((time.time() - self.start_time) * 1000),
                'chunks_processed': self.processed_chunks
            }
        )
        
        if self.loader.callbacks.on_loading_complete:
            self.loader.callbacks.on_loading_complete(result)
    
    def _emit_error(self, error_msg: str):
        """Emit error signal."""
        self.current_stage = LoadingStage.ERROR
        if self.loader.callbacks.on_loading_error:
            self.loader.callbacks.on_loading_error(error_msg)
    
    def _check_first_data(self):
        """Check if first data is ready within timeout."""
        if not self._first_data_event.is_set():
            # Emit partial skeleton with loading indicator
            result = ProgressiveResult(
                stage=LoadingStage.INITIAL,
                data=None,
                progress=0.0,
                message="Loading data...",
                metadata={'show_enhanced_skeleton': True}
            )
            if self.loader.callbacks.on_progress_update:
            self.loader.callbacks.on_progress_update(result)
    
    def _combine_results(self, results: List[Any]) -> Any:
        """Combine multiple chunk results."""
        if not results:
            return None
        
        # Simple concatenation for now
        # Real implementation would depend on data type
        if hasattr(results[0], 'concat'):
            return results[0].concat(results[1:])
        elif isinstance(results[0], dict):
            combined = {}
            for result in results:
                combined.update(result)
            return combined
        else:
            return results
    
    def _estimate_completion_time(self) -> float:
        """Estimate remaining time in seconds."""
        if self.processed_chunks == 0:
            return 0
        
        elapsed = time.time() - self.start_time
        rate = self.processed_chunks / elapsed
        remaining_chunks = self.total_chunks - self.processed_chunks
        
        return remaining_chunks / rate if rate > 0 else 0


class ProgressiveAnalyticsManager:
    """
    High-level manager for progressive analytics loading.
    
    Coordinates between UI components and analytics engines.
    """
    
    def __init__(self,
                 data_loader: StreamingDataLoader,
                 computation_queue: ComputationQueue):
        """Initialize manager."""
        # Create callbacks for logging
        callbacks = ProgressiveLoaderCallbacks()
        callbacks.on_loading_started = lambda: logger.info("Progressive loading started")
        callbacks.on_loading_complete = lambda r: logger.info(f"Loading complete in {r.metadata.get('total_time_ms')}ms")
        callbacks.on_loading_error = lambda e: logger.error(f"Loading error: {e}")
        
        self.loader = ProgressiveLoader(data_loader, computation_queue, callbacks=callbacks)
    
    def create_progressive_calculator(self, base_calculator: Any) -> Any:
        """
        Wrap a calculator with progressive loading support.
        
        Args:
            base_calculator: Original calculator instance
            
        Returns:
            Progressive-enabled calculator
        """
        class ProgressiveCalculator(base_calculator.__class__):
            """Calculator with progressive loading."""
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._progressive_manager = self
            
            def calculate_progressive(self, *args, **kwargs):
                """Calculate with progressive loading."""
                # Extract date range from args
                start_date = kwargs.get('start_date')
                end_date = kwargs.get('end_date')
                metrics = kwargs.get('metrics')
                
                # Create computation function
                def compute_chunk(data):
                    return self.calculate(data)
                
                # Start progressive loading
                session_id = self._progressive_manager.loader.load_progressive(
                    computation_func=compute_chunk,
                    start_date=start_date,
                    end_date=end_date,
                    metrics=metrics,
                    skeleton_config={
                        'calculator_type': self.__class__.__name__
                    }
                )
                
                return session_id
        
        # Create instance
        progressive_calc = ProgressiveCalculator()
        progressive_calc._progressive_manager = self
        
        return progressive_calc