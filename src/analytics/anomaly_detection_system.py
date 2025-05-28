"""
Main anomaly detection system that orchestrates all components.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import time
import threading
from queue import Queue

from .anomaly_models import (
    Anomaly, DetectionMethod, Severity, DetectionConfig, DetectionResult,
    AnomalyDetectionError, InsufficientDataError
)
from .anomaly_detectors import (
    ZScoreDetector, ModifiedZScoreDetector, IQRDetector,
    IsolationForestDetector, LocalOutlierFactorDetector, LSTMDetector
)
from .ensemble_detector import EnsembleDetector
from .notification_manager import NotificationManager
from .feedback_processor import FeedbackProcessor


class AnomalyDetectionSystem:
    """Main anomaly detection system."""
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        """Initialize the anomaly detection system."""
        self.config = config or DetectionConfig()
        
        # Initialize detectors
        self.detectors = self._initialize_detectors()
        
        # Initialize main components
        self.ensemble = EnsembleDetector(self.detectors, self.config)
        self.notification_manager = NotificationManager()
        self.feedback_processor = FeedbackProcessor(self.config)
        
        # Real-time detection components
        self.real_time_queue = Queue()
        self.real_time_thread = None
        self.real_time_running = False
        
        # Detection history and statistics
        self.detection_history = []
        self.performance_metrics = {}
        
        # Integration with existing calculators
        self.calculator_integration = {}
    
    def _initialize_detectors(self) -> Dict[str, Any]:
        """Initialize all available detectors."""
        detectors = {}
        
        # Statistical detectors
        detectors['zscore'] = ZScoreDetector(
            threshold=self.config.zscore_threshold
        )
        detectors['modified_zscore'] = ModifiedZScoreDetector(
            threshold=self.config.modified_zscore_threshold
        )
        detectors['iqr'] = IQRDetector(
            multiplier=self.config.iqr_multiplier
        )
        
        # Machine learning detectors
        detectors['isolation_forest'] = IsolationForestDetector(
            contamination=self.config.isolation_forest_contamination
        )
        detectors['lof'] = LocalOutlierFactorDetector(
            n_neighbors=self.config.lof_neighbors,
            contamination=self.config.lof_contamination
        )
        
        # LSTM detector (when available)
        try:
            detectors['lstm'] = LSTMDetector(
                sequence_length=self.config.lstm_sequence_length,
                threshold_percentile=self.config.lstm_threshold_percentile
            )
        except NotImplementedError:
            # LSTM not available, skip
            pass
        
        return detectors
    
    def detect_anomalies(self, data: Union[pd.Series, pd.DataFrame], 
                        real_time: bool = False) -> List[Anomaly]:
        """Main entry point for anomaly detection."""
        if isinstance(data, pd.Series):
            return self._detect_univariate(data, real_time)
        elif isinstance(data, pd.DataFrame):
            return self._detect_multivariate(data, real_time)
        else:
            raise ValueError("Data must be pandas Series or DataFrame")
    
    def _detect_univariate(self, data: pd.Series, real_time: bool = False) -> List[Anomaly]:
        """Detect anomalies in univariate time series."""
        start_time = time.time()
        
        try:
            # Validate data
            if data.empty:
                return []
            
            if real_time and self.config.real_time_enabled:
                return self._detect_real_time_univariate(data)
            else:
                return self._detect_batch_univariate(data)
                
        except InsufficientDataError as e:
            print(f"Insufficient data for anomaly detection: {e}")
            return []
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return []
        finally:
            detection_time = time.time() - start_time
            self._record_performance_metric('detection_time', detection_time)
    
    def _detect_multivariate(self, data: pd.DataFrame, real_time: bool = False) -> List[Anomaly]:
        """Detect anomalies in multivariate data."""
        start_time = time.time()
        
        try:
            if data.empty:
                return []
            
            if real_time and self.config.real_time_enabled:
                return self._detect_real_time_multivariate(data)
            else:
                return self._detect_batch_multivariate(data)
                
        except InsufficientDataError as e:
            print(f"Insufficient data for multivariate anomaly detection: {e}")
            return []
        except Exception as e:
            print(f"Error in multivariate anomaly detection: {e}")
            return []
        finally:
            detection_time = time.time() - start_time
            self._record_performance_metric('multivariate_detection_time', detection_time)
    
    def _detect_batch_univariate(self, data: pd.Series) -> List[Anomaly]:
        """Run batch anomaly detection on univariate data."""
        # Use ensemble detector
        anomalies = self.ensemble.detect(data)
        
        # Apply feedback-based filtering
        filtered_anomalies = self.feedback_processor.filter_anomalies(anomalies)
        
        # Add explanations
        for anomaly in filtered_anomalies:
            self._enhance_anomaly_explanation(anomaly, data)
        
        # Create notifications
        if self.config.notification_enabled:
            for anomaly in filtered_anomalies:
                notification = self.notification_manager.create_notification(anomaly)
                if notification:
                    print(f"Notification: {notification.title}")
        
        # Record detection result
        self._record_detection_result(filtered_anomalies, len(data), DetectionMethod.ENSEMBLE)
        
        return filtered_anomalies
    
    def _detect_batch_multivariate(self, data: pd.DataFrame) -> List[Anomaly]:
        """Run batch anomaly detection on multivariate data."""
        # Use ensemble detector for multivariate data
        anomalies = self.ensemble.detect_multivariate(data)
        
        # Apply feedback-based filtering
        filtered_anomalies = self.feedback_processor.filter_anomalies(anomalies)
        
        # Add explanations
        for anomaly in filtered_anomalies:
            self._enhance_anomaly_explanation(anomaly, data)
        
        # Create notifications
        if self.config.notification_enabled:
            for anomaly in filtered_anomalies:
                notification = self.notification_manager.create_notification(anomaly)
                if notification:
                    print(f"Notification: {notification.title}")
        
        # Record detection result
        self._record_detection_result(filtered_anomalies, len(data), DetectionMethod.ENSEMBLE)
        
        return filtered_anomalies
    
    def _detect_real_time_univariate(self, data: pd.Series) -> List[Anomaly]:
        """Real-time anomaly detection for univariate data."""
        # For real-time, we typically process the latest point(s)
        # Use a sliding window approach
        window_size = min(100, len(data))  # Use last 100 points for context
        
        if len(data) < window_size:
            window_data = data
        else:
            window_data = data.iloc[-window_size:]
        
        # Run detection on window
        anomalies = self._detect_batch_univariate(window_data)
        
        # Filter to only recent anomalies
        if anomalies:
            # Only return anomalies from the last few points
            recent_threshold = window_data.index[-min(5, len(window_data))]
            recent_anomalies = [
                a for a in anomalies 
                if a.timestamp >= recent_threshold
            ]
            return recent_anomalies
        
        return []
    
    def _detect_real_time_multivariate(self, data: pd.DataFrame) -> List[Anomaly]:
        """Real-time anomaly detection for multivariate data."""
        # Similar to univariate but for DataFrame
        window_size = min(100, len(data))
        
        if len(data) < window_size:
            window_data = data
        else:
            window_data = data.iloc[-window_size:]
        
        anomalies = self._detect_batch_multivariate(window_data)
        
        if anomalies:
            recent_threshold = window_data.index[-min(5, len(window_data))]
            recent_anomalies = [
                a for a in anomalies 
                if a.timestamp >= recent_threshold
            ]
            return recent_anomalies
        
        return []
    
    def _enhance_anomaly_explanation(self, anomaly: Anomaly, data: Union[pd.Series, pd.DataFrame]):
        """Enhance anomaly with additional context and explanation."""
        # Add historical context
        if isinstance(data, pd.Series) and len(data) > 10:
            # Calculate percentile rank
            percentile = (data < anomaly.value).sum() / len(data) * 100
            anomaly.context['percentile_rank'] = percentile
            
            # Add recent trend context
            if len(data) >= 7:
                recent_trend = self._calculate_trend(data.iloc[-7:])
                anomaly.context['recent_trend'] = recent_trend
        
        # Add time-based context
        if isinstance(anomaly.timestamp, datetime):
            anomaly.context['hour_of_day'] = anomaly.timestamp.hour
            anomaly.context['day_of_week'] = anomaly.timestamp.weekday()
            anomaly.context['day_name'] = anomaly.timestamp.strftime('%A')
    
    def _calculate_trend(self, data: pd.Series) -> str:
        """Calculate trend direction for recent data."""
        if len(data) < 3:
            return "insufficient_data"
        
        # Simple linear trend
        x = np.arange(len(data))
        slope = np.polyfit(x, data.values, 1)[0]
        
        if abs(slope) < data.std() * 0.1:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _record_detection_result(self, anomalies: List[Anomaly], total_points: int, method: DetectionMethod):
        """Record detection result for performance tracking."""
        result = DetectionResult(
            anomalies=anomalies,
            total_points=total_points,
            detection_time=self.performance_metrics.get('detection_time', 0),
            method=method
        )
        self.detection_history.append(result)
        
        # Keep only recent history
        if len(self.detection_history) > 100:
            self.detection_history = self.detection_history[-100:]
    
    def _record_performance_metric(self, metric_name: str, value: float):
        """Record performance metric."""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        
        self.performance_metrics[metric_name].append(value)
        
        # Keep only recent metrics
        if len(self.performance_metrics[metric_name]) > 100:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-100:]
    
    # Integration with existing calculator classes
    def integrate_with_calculator(self, calculator_type: str, calculator_instance):
        """Integrate with existing calculator classes (G019, G020, G021)."""
        self.calculator_integration[calculator_type] = calculator_instance
    
    def detect_from_daily_metrics(self, start_date: datetime, end_date: datetime, 
                                 metrics: List[str] = None) -> List[Anomaly]:
        """Detect anomalies using daily metrics calculator."""
        if 'daily' not in self.calculator_integration:
            raise ValueError("Daily metrics calculator not integrated")
        
        calculator = self.calculator_integration['daily']
        
        # Get daily metrics data
        daily_data = calculator.get_daily_metrics(start_date, end_date, metrics)
        
        if daily_data.empty:
            return []
        
        return self.detect_anomalies(daily_data)
    
    def detect_from_weekly_metrics(self, start_date: datetime, end_date: datetime,
                                  metrics: List[str] = None) -> List[Anomaly]:
        """Detect anomalies using weekly metrics calculator."""
        if 'weekly' not in self.calculator_integration:
            raise ValueError("Weekly metrics calculator not integrated")
        
        calculator = self.calculator_integration['weekly']
        
        # Get weekly metrics data
        weekly_data = calculator.get_weekly_metrics(start_date, end_date, metrics)
        
        if weekly_data.empty:
            return []
        
        return self.detect_anomalies(weekly_data)
    
    def detect_from_monthly_metrics(self, start_date: datetime, end_date: datetime,
                                   metrics: List[str] = None) -> List[Anomaly]:
        """Detect anomalies using monthly metrics calculator."""
        if 'monthly' not in self.calculator_integration:
            raise ValueError("Monthly metrics calculator not integrated")
        
        calculator = self.calculator_integration['monthly']
        
        # Get monthly metrics data
        monthly_data = calculator.get_monthly_metrics(start_date, end_date, metrics)
        
        if monthly_data.empty:
            return []
        
        return self.detect_anomalies(monthly_data)
    
    # User feedback interface
    def provide_feedback(self, anomaly: Anomaly, feedback_type: str, 
                        comment: str = None, suggested_threshold: float = None):
        """Allow user to provide feedback on an anomaly."""
        self.feedback_processor.process_feedback(
            anomaly, feedback_type, comment, suggested_threshold
        )
    
    def mark_false_positive(self, anomaly: Anomaly, comment: str = None):
        """Mark an anomaly as false positive."""
        self.provide_feedback(anomaly, 'false_positive', comment)
    
    def confirm_true_positive(self, anomaly: Anomaly, comment: str = None):
        """Confirm an anomaly as true positive."""
        self.provide_feedback(anomaly, 'true_positive', comment)
    
    # Real-time detection control
    def start_real_time_detection(self, data_stream_callback: callable):
        """Start real-time anomaly detection."""
        if self.real_time_running:
            return
        
        self.real_time_running = True
        self.real_time_thread = threading.Thread(
            target=self._real_time_detection_loop,
            args=(data_stream_callback,)
        )
        self.real_time_thread.start()
    
    def stop_real_time_detection(self):
        """Stop real-time anomaly detection."""
        self.real_time_running = False
        if self.real_time_thread:
            self.real_time_thread.join()
    
    def _real_time_detection_loop(self, data_stream_callback: callable):
        """Real-time detection loop (runs in separate thread)."""
        while self.real_time_running:
            try:
                # Get new data from stream
                new_data = data_stream_callback()
                
                if new_data is not None and not new_data.empty:
                    # Run real-time detection
                    anomalies = self.detect_anomalies(new_data, real_time=True)
                    
                    # Process any detected anomalies
                    for anomaly in anomalies:
                        self.real_time_queue.put(anomaly)
                
                # Sleep to maintain latency target
                time.sleep(self.config.real_time_latency_ms / 1000.0)
                
            except Exception as e:
                print(f"Error in real-time detection: {e}")
                time.sleep(1)  # Prevent rapid error loops
    
    def get_real_time_anomalies(self) -> List[Anomaly]:
        """Get anomalies from real-time detection queue."""
        anomalies = []
        while not self.real_time_queue.empty():
            anomalies.append(self.real_time_queue.get())
        return anomalies
    
    # System information and statistics
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics."""
        feedback_stats = self.feedback_processor.get_feedback_statistics()
        ensemble_stats = self.ensemble.get_detection_summary()
        
        return {
            'config': {
                'enabled_methods': [m.value for m in self.config.enabled_methods],
                'real_time_enabled': self.config.real_time_enabled,
                'notification_enabled': self.config.notification_enabled,
                'adaptive_thresholds': self.config.adaptive_thresholds
            },
            'performance': {
                'avg_detection_time': np.mean(self.performance_metrics.get('detection_time', [0])),
                'detection_runs': len(self.detection_history),
                'total_anomalies_detected': sum(len(r.anomalies) for r in self.detection_history)
            },
            'feedback': feedback_stats,
            'ensemble': ensemble_stats,
            'notifications': {
                'pending': len(self.notification_manager.get_pending_notifications()),
                'total_sent': len(self.notification_manager.notification_history)
            },
            'real_time': {
                'running': self.real_time_running,
                'queue_size': self.real_time_queue.qsize() if hasattr(self.real_time_queue, 'qsize') else 0
            }
        }
    
    def get_recommendations(self) -> List[str]:
        """Get system recommendations for improving performance."""
        recommendations = []
        
        # Get feedback recommendations
        feedback_recs = self.feedback_processor.get_learning_recommendations()
        recommendations.extend(feedback_recs)
        
        # Performance recommendations
        if self.performance_metrics.get('detection_time'):
            avg_time = np.mean(self.performance_metrics['detection_time'])
            if avg_time > 1.0:  # More than 1 second
                recommendations.append("Consider reducing enabled detection methods to improve speed")
        
        # Data recommendations
        if len(self.detection_history) > 0:
            recent_results = self.detection_history[-10:]
            avg_anomaly_rate = np.mean([r.anomaly_rate for r in recent_results])
            
            if avg_anomaly_rate > 0.1:  # More than 10% anomalies
                recommendations.append("High anomaly rate detected - consider adjusting thresholds")
            elif avg_anomaly_rate < 0.001:  # Less than 0.1% anomalies
                recommendations.append("Very low anomaly rate - consider more sensitive detection")
        
        return recommendations
    
    def export_system_report(self, filepath: str):
        """Export comprehensive system report."""
        report = {
            'export_timestamp': datetime.now().isoformat(),
            'system_status': self.get_system_status(),
            'recommendations': self.get_recommendations(),
            'detection_history': [
                {
                    'timestamp': r.detection_time,
                    'anomaly_count': len(r.anomalies),
                    'total_points': r.total_points,
                    'method': r.method.value
                }
                for r in self.detection_history[-50:]  # Last 50 runs
            ],
            'configuration': {
                'detection_methods': {m.value: True for m in self.config.enabled_methods},
                'thresholds': {
                    'zscore': self.config.zscore_threshold,
                    'modified_zscore': self.config.modified_zscore_threshold,
                    'iqr_multiplier': self.config.iqr_multiplier,
                    'isolation_forest_contamination': self.config.isolation_forest_contamination,
                    'lof_neighbors': self.config.lof_neighbors
                }
            }
        }
        
        import json
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def update_configuration(self, new_config: DetectionConfig):
        """Update system configuration."""
        self.config = new_config
        
        # Reinitialize detectors with new configuration
        self.detectors = self._initialize_detectors()
        self.ensemble = EnsembleDetector(self.detectors, self.config)
        
        # Update feedback processor
        self.feedback_processor.config = new_config