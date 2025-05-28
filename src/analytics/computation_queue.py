"""Priority-based computation queue for analytics tasks."""

from typing import Any, Callable, Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue, Queue, Empty
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from enum import Enum, auto
import threading
import logging
import time
import uuid
from functools import wraps
import multiprocessing as mp

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1  # User-initiated, interactive
    HIGH = 2      # Important background tasks
    NORMAL = 3    # Regular computations
    LOW = 4       # Background refresh, cache warming
    IDLE = 5      # Only run when system is idle


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass(order=True)
class ComputationTask:
    """Represents a computation task in the queue."""
    priority: int = field(compare=True)
    created_at: datetime = field(default_factory=datetime.now, compare=True)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    callback: Optional[Callable] = field(default=None, compare=False)
    error_callback: Optional[Callable] = field(default=None, compare=False)
    cpu_bound: bool = field(default=False, compare=False)
    cancellable: bool = field(default=True, compare=False)
    timeout: Optional[float] = field(default=None, compare=False)
    
    def __post_init__(self):
        """Ensure priority is an integer."""
        if isinstance(self.priority, TaskPriority):
            self.priority = self.priority.value


class ComputationQueue:
    """
    Priority-based computation queue with intelligent scheduling.
    
    Features:
    - Priority-based task scheduling
    - Separate executors for I/O and CPU-bound tasks
    - Task cancellation support
    - Progress tracking
    - Resource monitoring
    - Automatic executor sizing based on system resources
    """
    
    def __init__(self, 
                 max_io_workers: Optional[int] = None,
                 max_cpu_workers: Optional[int] = None,
                 enable_monitoring: bool = True):
        """
        Initialize computation queue.
        
        Args:
            max_io_workers: Maximum I/O workers (None for auto)
            max_cpu_workers: Maximum CPU workers (None for auto)
            enable_monitoring: Enable resource monitoring
        """
        # Task queue
        self._queue = PriorityQueue()
        self._tasks: Dict[str, ComputationTask] = {}
        self._task_status: Dict[str, TaskStatus] = {}
        self._task_results: Dict[str, Any] = {}
        self._task_futures: Dict[str, Future] = {}
        
        # Executors
        self._io_workers = max_io_workers or min(32, mp.cpu_count() * 4)
        self._cpu_workers = max_cpu_workers or max(1, mp.cpu_count() - 1)
        
        self._io_executor = ThreadPoolExecutor(
            max_workers=self._io_workers,
            thread_name_prefix="analytics_io"
        )
        self._cpu_executor = ProcessPoolExecutor(
            max_workers=self._cpu_workers
        )
        
        # Control
        self._shutdown = False
        self._worker_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._worker_thread.start()
        
        # Monitoring
        self.enable_monitoring = enable_monitoring
        if enable_monitoring:
            self._monitor_thread = threading.Thread(
                target=self._monitor_resources,
                daemon=True
            )
            self._monitor_thread.start()
        
        # Statistics
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'total_execution_time': 0.0,
            'average_wait_time': 0.0
        }
        
    def submit(self, func: Callable, *args,
              priority: Union[TaskPriority, int] = TaskPriority.NORMAL,
              callback: Optional[Callable] = None,
              error_callback: Optional[Callable] = None,
              cpu_bound: bool = False,
              cancellable: bool = True,
              timeout: Optional[float] = None,
              **kwargs) -> str:
        """
        Submit a task to the computation queue.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            priority: Task priority
            callback: Success callback
            error_callback: Error callback
            cpu_bound: Whether task is CPU-bound
            cancellable: Whether task can be cancelled
            timeout: Task timeout in seconds
            **kwargs: Keyword arguments for func
            
        Returns:
            Task ID
        """
        if self._shutdown:
            raise RuntimeError("Queue is shutting down")
        
        # Create task
        task = ComputationTask(
            priority=priority.value if isinstance(priority, TaskPriority) else priority,
            func=func,
            args=args,
            kwargs=kwargs,
            callback=callback,
            error_callback=error_callback,
            cpu_bound=cpu_bound,
            cancellable=cancellable,
            timeout=timeout
        )
        
        # Track task
        self._tasks[task.task_id] = task
        self._task_status[task.task_id] = TaskStatus.PENDING
        
        # Add to queue
        self._queue.put(task)
        
        # Update stats
        self._stats['tasks_submitted'] += 1
        
        logger.debug(f"Task {task.task_id} submitted with priority {task.priority}")
        
        return task.task_id
    
    def submit_interactive(self, func: Callable, *args, **kwargs) -> str:
        """Submit an interactive (high priority) task."""
        return self.submit(func, *args, priority=TaskPriority.CRITICAL, **kwargs)
    
    def submit_background(self, func: Callable, *args, **kwargs) -> str:
        """Submit a background (low priority) task."""
        return self.submit(func, *args, priority=TaskPriority.LOW, **kwargs)
    
    def cancel(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        status = self._task_status.get(task_id)
        
        if status == TaskStatus.PENDING:
            # Remove from queue if still pending
            self._task_status[task_id] = TaskStatus.CANCELLED
            self._stats['tasks_cancelled'] += 1
            return True
        
        elif status == TaskStatus.RUNNING and task.cancellable:
            # Cancel running task
            future = self._task_futures.get(task_id)
            if future and not future.done():
                future.cancel()
                self._task_status[task_id] = TaskStatus.CANCELLED
                self._stats['tasks_cancelled'] += 1
                return True
        
        return False
    
    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status."""
        return self._task_status.get(task_id)
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get task result (blocking).
        
        Args:
            task_id: Task ID
            timeout: Maximum wait time
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        start_time = time.time()
        
        while True:
            status = self._task_status.get(task_id)
            
            if status == TaskStatus.COMPLETED:
                return self._task_results.get(task_id)
            
            elif status == TaskStatus.FAILED:
                raise self._task_results.get(task_id, Exception("Task failed"))
            
            elif status == TaskStatus.CANCELLED:
                raise Exception("Task was cancelled")
            
            elif status is None:
                raise ValueError(f"Unknown task ID: {task_id}")
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Timeout waiting for task {task_id}")
            
            # Wait a bit
            time.sleep(0.1)
    
    def wait_all(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for multiple tasks to complete.
        
        Args:
            task_ids: List of task IDs
            timeout: Maximum wait time
            
        Returns:
            Dict of task_id -> result
        """
        results = {}
        start_time = time.time()
        
        for task_id in task_ids:
            remaining_timeout = None
            if timeout:
                elapsed = time.time() - start_time
                remaining_timeout = max(0, timeout - elapsed)
            
            try:
                results[task_id] = self.get_result(task_id, remaining_timeout)
            except Exception as e:
                results[task_id] = e
        
        return results
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending_tasks = sum(1 for s in self._task_status.values() 
                          if s == TaskStatus.PENDING)
        running_tasks = sum(1 for s in self._task_status.values() 
                          if s == TaskStatus.RUNNING)
        
        return {
            **self._stats,
            'pending_tasks': pending_tasks,
            'running_tasks': running_tasks,
            'queue_size': self._queue.qsize()
        }
    
    def shutdown(self, wait: bool = True):
        """Shutdown the queue."""
        logger.info("Shutting down computation queue")
        self._shutdown = True
        
        if wait:
            # Wait for pending tasks
            self._worker_thread.join(timeout=30)
        
        # Shutdown executors
        self._io_executor.shutdown(wait=wait)
        self._cpu_executor.shutdown(wait=wait)
    
    def _process_queue(self):
        """Worker thread that processes the queue."""
        while not self._shutdown:
            try:
                # Get task with timeout
                task = self._queue.get(timeout=1)
                
                # Check if cancelled
                if self._task_status.get(task.task_id) == TaskStatus.CANCELLED:
                    continue
                
                # Update status
                self._task_status[task.task_id] = TaskStatus.RUNNING
                
                # Select executor
                executor = self._cpu_executor if task.cpu_bound else self._io_executor
                
                # Submit to executor
                future = executor.submit(self._execute_task, task)
                self._task_futures[task.task_id] = future
                
                # Add done callback
                future.add_done_callback(
                    lambda f: self._task_completed(task, f)
                )
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
    
    def _execute_task(self, task: ComputationTask) -> Any:
        """Execute a single task."""
        start_time = time.time()
        
        try:
            # Execute with timeout if specified
            if task.timeout:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Task exceeded timeout of {task.timeout}s")
                
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(task.timeout))
                
                try:
                    result = task.func(*task.args, **task.kwargs)
                finally:
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            # Update execution time
            execution_time = time.time() - start_time
            self._stats['total_execution_time'] += execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            raise
    
    def _task_completed(self, task: ComputationTask, future: Future):
        """Handle task completion."""
        try:
            if future.cancelled():
                self._task_status[task.task_id] = TaskStatus.CANCELLED
                self._stats['tasks_cancelled'] += 1
                
            elif future.exception():
                self._task_status[task.task_id] = TaskStatus.FAILED
                self._task_results[task.task_id] = future.exception()
                self._stats['tasks_failed'] += 1
                
                # Call error callback
                if task.error_callback:
                    try:
                        task.error_callback(future.exception())
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}")
                
            else:
                self._task_status[task.task_id] = TaskStatus.COMPLETED
                self._task_results[task.task_id] = future.result()
                self._stats['tasks_completed'] += 1
                
                # Call success callback
                if task.callback:
                    try:
                        task.callback(future.result())
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
        
        finally:
            # Clean up future reference
            self._task_futures.pop(task.task_id, None)
    
    def _monitor_resources(self):
        """Monitor system resources and adjust executors."""
        import psutil
        
        while not self._shutdown:
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Log if resources are constrained
                if cpu_percent > 90:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                
                if memory_percent > 85:
                    logger.warning(f"High memory usage: {memory_percent}%")
                
                # Sleep for monitoring interval
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                time.sleep(30)


def with_priority_queue(queue: ComputationQueue):
    """Decorator to automatically submit function to queue."""
    def decorator(priority: TaskPriority = TaskPriority.NORMAL,
                 cpu_bound: bool = False):
        def wrapper(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                return queue.submit(
                    func, *args,
                    priority=priority,
                    cpu_bound=cpu_bound,
                    **kwargs
                )
            return wrapped
        return wrapper
    return decorator