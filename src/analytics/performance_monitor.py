"""Performance monitoring and profiling for analytics operations."""

from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import threading
import logging
import json
import os
from collections import deque, defaultdict
from contextlib import contextmanager
import psutil
import tracemalloc

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass 
class OperationProfile:
    """Profile of a single operation."""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_start_mb: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    memory_delta_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    metrics: List[PerformanceMetric] = field(default_factory=list)
    phases: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    
    def finalize(self):
        """Finalize the profile with end metrics."""
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'memory_start_mb': self.memory_start_mb,
            'memory_peak_mb': self.memory_peak_mb,
            'memory_delta_mb': self.memory_delta_mb,
            'cpu_percent': self.cpu_percent,
            'metrics': [m.to_dict() for m in self.metrics],
            'phases': self.phases,
            'error': self.error
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for analytics operations.
    
    Features:
    - Operation profiling with timing and memory tracking
    - Performance metric collection and aggregation
    - Threshold monitoring and alerts
    - Historical performance tracking
    - Performance regression detection
    """
    
    def __init__(self,
                 enable_memory_profiling: bool = True,
                 history_size: int = 1000,
                 alert_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize performance monitor.
        
        Args:
            enable_memory_profiling: Enable memory tracking
            history_size: Number of operations to keep in history
            alert_thresholds: Performance thresholds for alerts
        """
        self.enable_memory_profiling = enable_memory_profiling
        self.history_size = history_size
        
        # Operation tracking
        self._active_operations: Dict[str, OperationProfile] = {}
        self._operation_history = deque(maxlen=history_size)
        self._lock = threading.RLock()
        
        # Metric aggregation
        self._metric_aggregates: Dict[str, List[float]] = defaultdict(list)
        self._metric_percentiles: Dict[str, Dict[str, float]] = {}
        
        # Performance thresholds
        self.alert_thresholds = alert_thresholds or {
            'operation_duration_ms': 5000,  # 5 seconds
            'memory_usage_mb': 500,         # 500 MB
            'cpu_percent': 80,              # 80% CPU
            'cache_hit_ratio': 0.7          # 70% cache hits
        }
        
        # System resource tracking
        self._system_monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            daemon=True
        )
        self._stop_monitoring = threading.Event()
        self._system_metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_available_mb': 0
        }
        
        # Performance reports
        self._report_dir = "performance_reports"
        os.makedirs(self._report_dir, exist_ok=True)
        
        # Start monitoring
        if enable_memory_profiling:
            tracemalloc.start()
        
        self._system_monitor_thread.start()
    
    @contextmanager
    def profile_operation(self, operation_type: str, operation_id: Optional[str] = None):
        """
        Context manager for profiling an operation.
        
        Args:
            operation_type: Type of operation (e.g., 'calculate_daily_metrics')
            operation_id: Optional unique identifier
            
        Yields:
            OperationProfile instance
        """
        if not operation_id:
            operation_id = f"{operation_type}_{int(time.time() * 1000)}"
        
        profile = OperationProfile(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.now()
        )
        
        # Capture starting metrics
        if self.enable_memory_profiling:
            profile.memory_start_mb = self._get_memory_usage_mb()
        
        # Track active operation
        with self._lock:
            self._active_operations[operation_id] = profile
        
        try:
            yield profile
            
            # Success - capture final metrics
            profile.end_time = datetime.now()
            profile.finalize()
            
            if self.enable_memory_profiling:
                profile.memory_peak_mb = self._get_peak_memory_mb()
                profile.memory_delta_mb = profile.memory_peak_mb - profile.memory_start_mb
            
            profile.cpu_percent = self._system_metrics['cpu_percent']
            
            # Check thresholds
            self._check_thresholds(profile)
            
        except Exception as e:
            # Capture error
            profile.error = str(e)
            profile.end_time = datetime.now()
            profile.finalize()
            raise
            
        finally:
            # Move to history
            with self._lock:
                self._active_operations.pop(operation_id, None)
                self._operation_history.append(profile)
            
            # Update aggregates
            self._update_aggregates(profile)
    
    def record_metric(self, name: str, value: float, unit: str = "ms",
                     tags: Optional[Dict[str, Any]] = None):
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            tags: Optional tags
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        # Add to active operation if exists
        current_op = self._get_current_operation()
        if current_op:
            current_op.metrics.append(metric)
        
        # Add to aggregates
        with self._lock:
            self._metric_aggregates[name].append(value)
            
            # Keep only recent values
            if len(self._metric_aggregates[name]) > self.history_size:
                self._metric_aggregates[name] = self._metric_aggregates[name][-self.history_size:]
    
    def start_phase(self, phase_name: str):
        """Start timing a phase within current operation."""
        current_op = self._get_current_operation()
        if current_op:
            current_op.phases[f"{phase_name}_start"] = time.time()
    
    def end_phase(self, phase_name: str):
        """End timing a phase within current operation."""
        current_op = self._get_current_operation()
        if current_op and f"{phase_name}_start" in current_op.phases:
            start_time = current_op.phases.pop(f"{phase_name}_start")
            duration_ms = (time.time() - start_time) * 1000
            current_op.phases[phase_name] = duration_ms
            
            # Also record as metric
            self.record_metric(f"phase_{phase_name}_duration", duration_ms, "ms")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        with self._lock:
            # Calculate percentiles for each metric
            self._calculate_percentiles()
            
            # Recent operations summary
            recent_ops = list(self._operation_history)[-100:]
            
            if recent_ops:
                avg_duration = sum(op.duration_ms for op in recent_ops if op.duration_ms) / len(recent_ops)
                avg_memory = sum(op.memory_delta_mb for op in recent_ops if op.memory_delta_mb) / len([op for op in recent_ops if op.memory_delta_mb])
                error_rate = sum(1 for op in recent_ops if op.error) / len(recent_ops)
            else:
                avg_duration = avg_memory = error_rate = 0
            
            return {
                'summary': {
                    'total_operations': len(self._operation_history),
                    'active_operations': len(self._active_operations),
                    'average_duration_ms': avg_duration,
                    'average_memory_delta_mb': avg_memory,
                    'error_rate': error_rate
                },
                'system_resources': self._system_metrics.copy(),
                'metric_percentiles': self._metric_percentiles.copy(),
                'recent_operations': [op.to_dict() for op in recent_ops[-10:]]
            }
    
    def get_operation_stats(self, operation_type: str) -> Dict[str, Any]:
        """Get statistics for a specific operation type."""
        with self._lock:
            ops = [op for op in self._operation_history if op.operation_type == operation_type]
            
            if not ops:
                return {}
            
            durations = [op.duration_ms for op in ops if op.duration_ms]
            memory_deltas = [op.memory_delta_mb for op in ops if op.memory_delta_mb]
            
            return {
                'count': len(ops),
                'duration': {
                    'min': min(durations) if durations else 0,
                    'max': max(durations) if durations else 0,
                    'avg': sum(durations) / len(durations) if durations else 0,
                    'p50': self._percentile(durations, 50) if durations else 0,
                    'p95': self._percentile(durations, 95) if durations else 0,
                    'p99': self._percentile(durations, 99) if durations else 0
                },
                'memory': {
                    'avg_delta_mb': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                    'max_delta_mb': max(memory_deltas) if memory_deltas else 0
                },
                'error_count': sum(1 for op in ops if op.error),
                'phases': self._aggregate_phases(ops)
            }
    
    def detect_performance_regression(self, operation_type: str,
                                    recent_window: int = 10,
                                    baseline_window: int = 100) -> Optional[Dict[str, Any]]:
        """
        Detect performance regression for an operation type.
        
        Args:
            operation_type: Operation type to check
            recent_window: Number of recent operations
            baseline_window: Number of baseline operations
            
        Returns:
            Regression details if detected, None otherwise
        """
        with self._lock:
            ops = [op for op in self._operation_history 
                  if op.operation_type == operation_type and op.duration_ms]
            
            if len(ops) < recent_window + 10:
                return None
            
            # Get recent and baseline operations
            recent_ops = ops[-recent_window:]
            baseline_ops = ops[-baseline_window:-recent_window] if len(ops) > baseline_window else ops[:-recent_window]
            
            if not baseline_ops:
                return None
            
            # Calculate statistics
            recent_avg = sum(op.duration_ms for op in recent_ops) / len(recent_ops)
            baseline_avg = sum(op.duration_ms for op in baseline_ops) / len(baseline_ops)
            
            # Check for regression (20% threshold)
            if recent_avg > baseline_avg * 1.2:
                return {
                    'operation_type': operation_type,
                    'recent_avg_ms': recent_avg,
                    'baseline_avg_ms': baseline_avg,
                    'regression_percent': ((recent_avg - baseline_avg) / baseline_avg) * 100,
                    'recent_window': recent_window,
                    'baseline_window': baseline_window
                }
        
        return None
    
    def generate_performance_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed performance report."""
        if not output_file:
            output_file = os.path.join(
                self._report_dir,
                f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'operation_types': {},
            'regressions': []
        }
        
        # Get stats for each operation type
        operation_types = set(op.operation_type for op in self._operation_history)
        for op_type in operation_types:
            report['operation_types'][op_type] = self.get_operation_stats(op_type)
            
            # Check for regressions
            regression = self.detect_performance_regression(op_type)
            if regression:
                report['regressions'].append(regression)
        
        # Write report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report generated: {output_file}")
        
        return output_file
    
    def shutdown(self):
        """Shutdown the performance monitor."""
        self._stop_monitoring.set()
        self._system_monitor_thread.join(timeout=5)
        
        if self.enable_memory_profiling:
            tracemalloc.stop()
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        if self.enable_memory_profiling:
            return tracemalloc.get_traced_memory()[0] / (1024 * 1024)
        else:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
    
    def _get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        if self.enable_memory_profiling:
            return tracemalloc.get_traced_memory()[1] / (1024 * 1024)
        else:
            # Fallback to current memory
            return self._get_memory_usage_mb()
    
    def _get_current_operation(self) -> Optional[OperationProfile]:
        """Get current operation for this thread."""
        # Simple implementation - in practice, would use thread-local storage
        with self._lock:
            if self._active_operations:
                return list(self._active_operations.values())[-1]
        return None
    
    def _monitor_system_resources(self):
        """Background thread to monitor system resources."""
        while not self._stop_monitoring.is_set():
            try:
                # Update system metrics
                self._system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                self._system_metrics['memory_percent'] = memory.percent
                self._system_metrics['memory_available_mb'] = memory.available / (1024 * 1024)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                time.sleep(10)
    
    def _check_thresholds(self, profile: OperationProfile):
        """Check if operation exceeded any thresholds."""
        alerts = []
        
        if profile.duration_ms and profile.duration_ms > self.alert_thresholds['operation_duration_ms']:
            alerts.append(f"Duration {profile.duration_ms:.0f}ms exceeds threshold")
        
        if profile.memory_delta_mb and profile.memory_delta_mb > self.alert_thresholds['memory_usage_mb']:
            alerts.append(f"Memory usage {profile.memory_delta_mb:.0f}MB exceeds threshold")
        
        if profile.cpu_percent and profile.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"CPU usage {profile.cpu_percent:.0f}% exceeds threshold")
        
        if alerts:
            logger.warning(f"Performance alerts for {profile.operation_type}: {', '.join(alerts)}")
    
    def _update_aggregates(self, profile: OperationProfile):
        """Update metric aggregates from completed operation."""
        if profile.duration_ms:
            self.record_metric(f"{profile.operation_type}_duration", profile.duration_ms, "ms")
        
        if profile.memory_delta_mb:
            self.record_metric(f"{profile.operation_type}_memory", profile.memory_delta_mb, "MB")
    
    def _calculate_percentiles(self):
        """Calculate percentiles for all metrics."""
        with self._lock:
            self._metric_percentiles = {}
            
            for metric_name, values in self._metric_aggregates.items():
                if values:
                    self._metric_percentiles[metric_name] = {
                        'p50': self._percentile(values, 50),
                        'p75': self._percentile(values, 75),
                        'p90': self._percentile(values, 90),
                        'p95': self._percentile(values, 95),
                        'p99': self._percentile(values, 99)
                    }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _aggregate_phases(self, operations: List[OperationProfile]) -> Dict[str, Dict[str, float]]:
        """Aggregate phase timings across operations."""
        phase_times = defaultdict(list)
        
        for op in operations:
            for phase, duration in op.phases.items():
                if not phase.endswith('_start'):
                    phase_times[phase].append(duration)
        
        result = {}
        for phase, times in phase_times.items():
            if times:
                result[phase] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        
        return result