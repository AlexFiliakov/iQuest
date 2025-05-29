"""
Performance monitor for chart interactions.

Tracks frame times and validates performance requirements.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QElapsedTimer
from typing import List, Optional
import time


class InteractionPerformanceMonitor(QObject):
    """Monitor and validate interaction performance"""
    
    # Signals
    performance_report = pyqtSignal(dict)  # Performance metrics
    performance_warning = pyqtSignal(float)  # When frame time exceeds target
    
    def __init__(self, target_frame_time: float = 16.0):
        """
        Initialize performance monitor.
        
        Args:
            target_frame_time: Target frame time in milliseconds (default: 16ms for 60fps)
        """
        super().__init__()
        
        # Performance targets
        self.target_frame_time = target_frame_time
        self.warning_threshold = target_frame_time * 1.5  # Warn at 150% of target
        
        # Metrics storage
        self.frame_times: List[float] = []
        self.max_samples = 100
        
        # Timing
        self.frame_timer = QElapsedTimer()
        self.last_frame_time = time.perf_counter()
        
        # Reporting
        self.report_timer = QTimer()
        self.report_timer.timeout.connect(self._generate_report)
        self.report_timer.start(1000)  # Report every second
        
        # Performance state
        self.is_monitoring = False
        
    def start_frame(self):
        """Mark the start of a frame"""
        self.frame_timer.restart()
        self.is_monitoring = True
        
    def end_frame(self):
        """Mark the end of a frame and record timing"""
        if not self.is_monitoring:
            return
            
        # Calculate frame time
        frame_time = self.frame_timer.elapsed()  # milliseconds
        
        # Store frame time
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)
            
        # Check performance
        if frame_time > self.warning_threshold:
            self.performance_warning.emit(frame_time)
            
        self.is_monitoring = False
        
    def measure_operation(self, operation_name: str) -> 'PerformanceContext':
        """
        Context manager for measuring specific operations.
        
        Usage:
            with monitor.measure_operation("zoom"):
                # Perform zoom operation
        """
        return PerformanceContext(self, operation_name)
        
    def get_average_frame_time(self) -> float:
        """Get average frame time in milliseconds"""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)
        
    def get_max_frame_time(self) -> float:
        """Get maximum frame time in milliseconds"""
        if not self.frame_times:
            return 0.0
        return max(self.frame_times)
        
    def get_fps(self) -> float:
        """Get current frames per second"""
        avg_time = self.get_average_frame_time()
        if avg_time > 0:
            return 1000.0 / avg_time
        return 0.0
        
    def is_meeting_target(self) -> bool:
        """Check if performance meets target frame time"""
        return self.get_average_frame_time() <= self.target_frame_time
        
    def get_performance_score(self) -> float:
        """
        Get performance score (0-100).
        100 = all frames under target
        0 = all frames over 2x target
        """
        if not self.frame_times:
            return 100.0
            
        good_frames = sum(1 for t in self.frame_times if t <= self.target_frame_time)
        return (good_frames / len(self.frame_times)) * 100
        
    def _generate_report(self):
        """Generate performance report"""
        if not self.frame_times:
            return
            
        report = {
            'average_frame_time': self.get_average_frame_time(),
            'max_frame_time': self.get_max_frame_time(),
            'min_frame_time': min(self.frame_times),
            'fps': self.get_fps(),
            'target_frame_time': self.target_frame_time,
            'meeting_target': self.is_meeting_target(),
            'performance_score': self.get_performance_score(),
            'sample_count': len(self.frame_times),
            'percentiles': self._calculate_percentiles()
        }
        
        self.performance_report.emit(report)
        
    def _calculate_percentiles(self) -> dict:
        """Calculate frame time percentiles"""
        if not self.frame_times:
            return {}
            
        sorted_times = sorted(self.frame_times)
        n = len(sorted_times)
        
        return {
            'p50': sorted_times[n // 2],
            'p90': sorted_times[int(n * 0.9)],
            'p95': sorted_times[int(n * 0.95)],
            'p99': sorted_times[int(n * 0.99)] if n > 100 else sorted_times[-1]
        }
        
    def reset(self):
        """Reset performance metrics"""
        self.frame_times.clear()
        
    def cleanup(self):
        """Clean up resources"""
        self.report_timer.stop()


class PerformanceContext:
    """Context manager for measuring operation performance"""
    
    def __init__(self, monitor: InteractionPerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = 0
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
        
        # Log if operation is slow
        if duration > self.monitor.target_frame_time:
            print(f"Performance warning: {self.operation_name} took {duration:.1f}ms")
            
        # Record as frame time if monitor is active
        if self.monitor.is_monitoring:
            self.monitor.frame_times.append(duration)