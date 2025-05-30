"""
Anomaly Detection Module - Main API Interface

This module provides a comprehensive anomaly detection system for health data analysis.
It integrates multiple detection algorithms, user feedback processing, and notifications.
"""

from .anomaly_models import (
    Anomaly, DetectionMethod, Severity, DetectionConfig, DetectionResult,
    UserFeedback, PersonalThreshold, Notification, Action,
    AnomalyDetectionError, InsufficientDataError, ModelNotTrainedError
)

from .anomaly_detectors import (
    BaseDetector, ZScoreDetector, ModifiedZScoreDetector, IQRDetector,
    IsolationForestDetector, LocalOutlierFactorDetector, LSTMDetector,
    EnsembleDetector  # Import the simple ensemble detector
)

# Comment out the complex ensemble detector for now
# from .ensemble_detector import EnsembleDetector
from .notification_manager import NotificationManager
from .feedback_processor import FeedbackProcessor, FeedbackDatabase
from .anomaly_detection_system import AnomalyDetectionSystem

# Convenience imports for easy access
__all__ = [
    # Main system
    'AnomalyDetectionSystem',
    
    # Core models
    'Anomaly',
    'DetectionMethod', 
    'Severity',
    'DetectionConfig',
    'DetectionResult',
    
    # User interaction
    'UserFeedback',
    'PersonalThreshold',
    'Notification',
    'Action',
    
    # Detection components
    'BaseDetector',
    'ZScoreDetector',
    'ModifiedZScoreDetector', 
    'IQRDetector',
    'IsolationForestDetector',
    'LocalOutlierFactorDetector',
    'LSTMDetector',
    'EnsembleDetector',
    
    # Management components
    'NotificationManager',
    'FeedbackProcessor',
    'FeedbackDatabase',
    
    # Exceptions
    'AnomalyDetectionError',
    'InsufficientDataError',
    'ModelNotTrainedError',
    
    # Factory functions
    'create_default_system',
    'create_statistical_system',
    'create_ml_system',
    'create_ensemble_system'
]


def create_default_system(enable_notifications: bool = True,
                         enable_feedback: bool = True,
                         real_time: bool = False) -> AnomalyDetectionSystem:
    """
    Create a default anomaly detection system with balanced settings.
    
    Args:
        enable_notifications: Whether to enable user notifications
        enable_feedback: Whether to enable adaptive feedback learning
        real_time: Whether to enable real-time detection capabilities
    
    Returns:
        Configured AnomalyDetectionSystem
    """
    config = DetectionConfig(
        enabled_methods=[
            DetectionMethod.MODIFIED_ZSCORE,
            DetectionMethod.ISOLATION_FOREST,
            DetectionMethod.LOF
        ],
        notification_enabled=enable_notifications,
        adaptive_thresholds=enable_feedback,
        real_time_enabled=real_time,
        ensemble_min_votes=2
    )
    
    return AnomalyDetectionSystem(config)


def create_statistical_system(sensitivity: str = 'medium') -> AnomalyDetectionSystem:
    """
    Create an anomaly detection system using only statistical methods.
    
    Args:
        sensitivity: Detection sensitivity ('low', 'medium', 'high')
    
    Returns:
        Configured AnomalyDetectionSystem
    """
    # Adjust thresholds based on sensitivity
    thresholds = {
        'low': {'zscore': 4.0, 'modified_zscore': 4.5, 'iqr': 2.0},
        'medium': {'zscore': 3.0, 'modified_zscore': 3.5, 'iqr': 1.5},
        'high': {'zscore': 2.5, 'modified_zscore': 3.0, 'iqr': 1.2}
    }
    
    threshold_set = thresholds.get(sensitivity, thresholds['medium'])
    
    config = DetectionConfig(
        enabled_methods=[
            DetectionMethod.ZSCORE,
            DetectionMethod.MODIFIED_ZSCORE,
            DetectionMethod.IQR
        ],
        zscore_threshold=threshold_set['zscore'],
        modified_zscore_threshold=threshold_set['modified_zscore'],
        iqr_multiplier=threshold_set['iqr'],
        ensemble_min_votes=2
    )
    
    return AnomalyDetectionSystem(config)


def create_ml_system(contamination: float = 0.01) -> AnomalyDetectionSystem:
    """
    Create an anomaly detection system using only machine learning methods.
    
    Args:
        contamination: Expected proportion of anomalies in data
    
    Returns:
        Configured AnomalyDetectionSystem
    """
    config = DetectionConfig(
        enabled_methods=[
            DetectionMethod.ISOLATION_FOREST,
            DetectionMethod.LOF
        ],
        isolation_forest_contamination=contamination,
        lof_contamination=contamination,
        ensemble_min_votes=1  # Either method can trigger
    )
    
    return AnomalyDetectionSystem(config)


def create_ensemble_system(include_lstm: bool = False,
                          strict_consensus: bool = False) -> AnomalyDetectionSystem:
    """
    Create a comprehensive ensemble anomaly detection system.
    
    Args:
        include_lstm: Whether to include LSTM detector (requires TensorFlow)
        strict_consensus: Whether to require consensus from multiple methods
    
    Returns:
        Configured AnomalyDetectionSystem
    """
    methods = [
        DetectionMethod.MODIFIED_ZSCORE,
        DetectionMethod.IQR,
        DetectionMethod.ISOLATION_FOREST,
        DetectionMethod.LOF
    ]
    
    if include_lstm:
        methods.append(DetectionMethod.LSTM)
    
    config = DetectionConfig(
        enabled_methods=methods,
        ensemble_min_votes=3 if strict_consensus else 2,
        ensemble_weight_by_confidence=True,
        notification_enabled=True,
        adaptive_thresholds=True,
        real_time_enabled=False  # Can be enabled later
    )
    
    return AnomalyDetectionSystem(config)


# Example usage and integration helpers
class HealthDataAnomalyDetector:
    """
    Specialized anomaly detector for health data with domain-specific logic.
    """
    
    def __init__(self, system: AnomalyDetectionSystem = None):
        """Initialize with custom or default system."""
        self.system = system or create_default_system()
        self.health_metrics_config = self._setup_health_metrics()
    
    def _setup_health_metrics(self) -> dict:
        """Setup health-specific metric configurations."""
        return {
            'heart_rate': {
                'normal_range': (60, 100),
                'context_factors': ['activity', 'sleep', 'stress'],
                'severity_multiplier': 1.2  # Heart rate anomalies are more critical
            },
            'steps': {
                'normal_range': (5000, 15000),
                'context_factors': ['day_of_week', 'weather', 'location'],
                'severity_multiplier': 0.8  # Steps anomalies are less critical
            },
            'sleep_hours': {
                'normal_range': (6, 9),
                'context_factors': ['bedtime', 'stress', 'caffeine'],
                'severity_multiplier': 1.1
            },
            'weight': {
                'normal_range': None,  # Highly individual
                'context_factors': ['diet', 'exercise', 'medication'],
                'severity_multiplier': 1.3  # Weight changes can be significant
            }
        }
    
    def detect_health_anomalies(self, data, metric_type: str = None):
        """
        Detect anomalies with health-specific context.
        
        Args:
            data: Health data (Series or DataFrame)
            metric_type: Type of health metric for specialized handling
        
        Returns:
            List of anomalies with health-specific context
        """
        # Run standard detection
        anomalies = self.system.detect_anomalies(data)
        
        # Add health-specific context
        if metric_type and metric_type in self.health_metrics_config:
            anomalies = self._enhance_health_context(anomalies, metric_type)
        
        return anomalies
    
    def _enhance_health_context(self, anomalies, metric_type):
        """Enhance anomalies with health-specific context."""
        config = self.health_metrics_config[metric_type]
        
        for anomaly in anomalies:
            # Adjust severity based on health metric importance
            severity_multiplier = config['severity_multiplier']
            if severity_multiplier != 1.0:
                anomaly.score *= severity_multiplier
                
                # Update severity if needed
                if severity_multiplier > 1.2 and anomaly.severity == Severity.MEDIUM:
                    anomaly.severity = Severity.HIGH
                elif severity_multiplier < 0.8 and anomaly.severity == Severity.HIGH:
                    anomaly.severity = Severity.MEDIUM
            
            # Add health-specific context
            anomaly.context['health_metric_type'] = metric_type
            anomaly.context['normal_range'] = config['normal_range']
            anomaly.context['context_factors'] = config['context_factors']
            
            # Add range-based context if available
            if config['normal_range'] and isinstance(anomaly.value, (int, float)):
                min_val, max_val = config['normal_range']
                if anomaly.value < min_val:
                    anomaly.context['range_deviation'] = 'below_normal'
                elif anomaly.value > max_val:
                    anomaly.context['range_deviation'] = 'above_normal'
                else:
                    anomaly.context['range_deviation'] = 'within_normal'
        
        return anomalies


def demo_usage():
    """Demonstrate usage of the anomaly detection system."""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    print("Anomaly Detection System Demo")
    print("=" * 40)
    
    # Create sample health data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Simulate heart rate data with some anomalies
    heart_rate = np.random.normal(75, 10, 100)
    heart_rate[20] = 130  # Anomaly: high heart rate
    heart_rate[55] = 45   # Anomaly: low heart rate
    heart_rate[80] = 140  # Another high anomaly
    
    data = pd.Series(heart_rate, index=dates, name='heart_rate')
    
    # Create and use the system
    print("1. Creating default anomaly detection system...")
    system = create_default_system()
    
    print("2. Detecting anomalies in heart rate data...")
    anomalies = system.detect_anomalies(data)
    
    print(f"3. Found {len(anomalies)} anomalies:")
    for i, anomaly in enumerate(anomalies[:3], 1):  # Show first 3
        print(f"   {i}. {anomaly.timestamp.date()}: {anomaly.value:.1f} BPM "
              f"(severity: {anomaly.severity.value}, method: {anomaly.method.value})")
    
    # Demonstrate health-specific detection
    print("\n4. Using health-specific detector...")
    health_detector = HealthDataAnomalyDetector(system)
    health_anomalies = health_detector.detect_health_anomalies(data, 'heart_rate')
    
    print(f"5. Health-enhanced detection found {len(health_anomalies)} anomalies")
    
    # Demonstrate feedback
    if anomalies:
        print("\n6. Demonstrating user feedback...")
        system.mark_false_positive(anomalies[0], "This was after exercise")
        print("   Marked first anomaly as false positive")
    
    # Show system status
    print("\n7. System Status:")
    status = system.get_system_status()
    print(f"   - Detection runs: {status['performance']['detection_runs']}")
    print(f"   - Total anomalies: {status['performance']['total_anomalies_detected']}")
    print(f"   - Feedback entries: {status['feedback'].get('total_feedback', 0)}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    demo_usage()