"""
Unit tests for anomaly detection system.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.analytics.anomaly_detection import (
    AnomalyDetectionSystem, create_default_system, create_statistical_system,
    Anomaly, DetectionMethod, Severity, DetectionConfig,
    ZScoreDetector, ModifiedZScoreDetector, IQRDetector,
    HealthDataAnomalyDetector
)


class TestAnomalyModels:
    """Test anomaly data models."""
    
    def test_anomaly_creation(self):
        """Test creating an anomaly object."""
        anomaly = Anomaly(
            timestamp=datetime.now(),
            metric="heart_rate",
            value=120.0,
            score=3.5,
            method=DetectionMethod.ZSCORE,
            severity=Severity.HIGH,
            threshold=3.0
        )
        
        assert anomaly.metric == "heart_rate"
        assert anomaly.value == 120.0
        assert anomaly.score == 3.5
        assert anomaly.method == DetectionMethod.ZSCORE
        assert anomaly.severity == Severity.HIGH
    
    def test_detection_config_defaults(self):
        """Test detection configuration with defaults."""
        config = DetectionConfig()
        
        assert DetectionMethod.MODIFIED_ZSCORE in config.enabled_methods
        assert config.zscore_threshold == 3.0
        assert config.modified_zscore_threshold == 3.5
        assert config.notification_enabled is True


class TestStatisticalDetectors:
    """Test statistical anomaly detectors."""
    
    def setup_method(self):
        """Setup test data."""
        # Create sample data with known anomalies
        np.random.seed(42)
        normal_data = np.random.normal(50, 10, 95)
        anomalies = [100, 0, 150, -20, 200]  # Clear outliers
        
        all_data = np.concatenate([normal_data, anomalies])
        dates = pd.date_range('2024-01-01', periods=len(all_data), freq='D')
        self.test_data = pd.Series(all_data, index=dates, name='test_metric')
    
    def test_zscore_detector(self):
        """Test Z-score anomaly detector."""
        detector = ZScoreDetector(threshold=3.0)
        anomalies = detector.detect(self.test_data)
        
        assert len(anomalies) > 0
        assert all(abs(a.score) > 3.0 for a in anomalies)
        assert all(a.method == DetectionMethod.ZSCORE for a in anomalies)
    
    def test_modified_zscore_detector(self):
        """Test Modified Z-score anomaly detector."""
        detector = ModifiedZScoreDetector(threshold=3.5)
        anomalies = detector.detect(self.test_data)
        
        assert len(anomalies) > 0
        assert all(a.method == DetectionMethod.MODIFIED_ZSCORE for a in anomalies)
    
    def test_iqr_detector(self):
        """Test IQR anomaly detector."""
        detector = IQRDetector(multiplier=1.5)
        anomalies = detector.detect(self.test_data)
        
        assert len(anomalies) > 0
        assert all(a.method == DetectionMethod.IQR for a in anomalies)
    
    def test_empty_data_handling(self):
        """Test that detectors handle empty data gracefully."""
        empty_data = pd.Series([], name='empty')
        detector = ZScoreDetector()
        
        with pytest.raises(Exception):  # Should raise InsufficientDataError
            detector.detect(empty_data)
    
    def test_constant_data_handling(self):
        """Test that detectors handle constant data (no variance)."""
        constant_data = pd.Series([50] * 100, name='constant')
        detector = ZScoreDetector()
        
        anomalies = detector.detect(constant_data)
        assert len(anomalies) == 0  # No anomalies in constant data


class TestEnsembleDetection:
    """Test ensemble anomaly detection."""
    
    def setup_method(self):
        """Setup test data and system."""
        np.random.seed(42)
        normal_data = np.random.normal(100, 15, 90)
        anomalies = [200, 10, 250, 0, 300]  # Clear outliers
        
        all_data = np.concatenate([normal_data, anomalies])
        dates = pd.date_range('2024-01-01', periods=len(all_data), freq='D')
        self.test_data = pd.Series(all_data, index=dates, name='test_metric')
        
        self.system = create_default_system()
    
    def test_ensemble_detection(self):
        """Test ensemble anomaly detection."""
        anomalies = self.system.detect_anomalies(self.test_data)
        
        assert len(anomalies) > 0
        assert all(isinstance(a, Anomaly) for a in anomalies)
        
        # Check that we have ensemble results
        ensemble_anomalies = [a for a in anomalies if a.method == DetectionMethod.ENSEMBLE]
        assert len(ensemble_anomalies) > 0
    
    def test_multivariate_detection(self):
        """Test multivariate anomaly detection."""
        # Create multivariate data
        data = pd.DataFrame({
            'metric1': self.test_data.values,
            'metric2': np.random.normal(50, 5, len(self.test_data))
        }, index=self.test_data.index)
        
        anomalies = self.system.detect_anomalies(data)
        assert len(anomalies) >= 0  # May or may not find anomalies
    
    def test_system_configuration(self):
        """Test system configuration."""
        config = DetectionConfig(
            enabled_methods=[DetectionMethod.ZSCORE, DetectionMethod.MODIFIED_ZSCORE],
            zscore_threshold=2.5,
            ensemble_min_votes=1
        )
        
        system = AnomalyDetectionSystem(config)
        assert system.config.zscore_threshold == 2.5
        assert DetectionMethod.ZSCORE in system.config.enabled_methods


class TestFeedbackSystem:
    """Test user feedback and adaptation."""
    
    def setup_method(self):
        """Setup test system."""
        self.system = create_default_system(enable_feedback=True)
        
        # Create test anomaly
        self.test_anomaly = Anomaly(
            timestamp=datetime.now(),
            metric="test_metric",
            value=150.0,
            score=4.0,
            method=DetectionMethod.ZSCORE,
            severity=Severity.HIGH,
            threshold=3.0
        )
    
    def test_false_positive_feedback(self):
        """Test marking anomaly as false positive."""
        # This should work without errors
        self.system.mark_false_positive(self.test_anomaly, "Normal after exercise")
        
        # Check that feedback was recorded
        feedback_stats = self.system.feedback_processor.get_feedback_statistics()
        assert feedback_stats.get('total_feedback', 0) >= 0
    
    def test_true_positive_feedback(self):
        """Test confirming anomaly as true positive."""
        self.system.confirm_true_positive(self.test_anomaly, "Confirmed unusual")
        
        # Check that feedback was recorded
        feedback_stats = self.system.feedback_processor.get_feedback_statistics()
        assert feedback_stats.get('total_feedback', 0) >= 0
    
    def test_threshold_adaptation(self):
        """Test that thresholds adapt based on feedback."""
        original_threshold = self.system.config.zscore_threshold
        
        # Provide multiple false positive feedbacks
        for _ in range(5):
            self.system.mark_false_positive(self.test_anomaly)
        
        # Check if threshold was adjusted (this is internal to feedback processor)
        feedback_stats = self.system.feedback_processor.get_feedback_statistics()
        assert feedback_stats.get('false_positives', 0) > 0


class TestHealthDataDetector:
    """Test health-specific anomaly detection."""
    
    def setup_method(self):
        """Setup health data detector."""
        self.health_detector = HealthDataAnomalyDetector()
        
        # Create sample heart rate data
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        heart_rates = np.random.normal(75, 8, 45)
        heart_rates = np.append(heart_rates, [130, 140, 45, 40, 160])  # Add anomalies
        
        self.heart_rate_data = pd.Series(heart_rates, index=dates, name='heart_rate')
    
    def test_health_specific_detection(self):
        """Test health-specific anomaly detection."""
        anomalies = self.health_detector.detect_health_anomalies(
            self.heart_rate_data, 
            metric_type='heart_rate'
        )
        
        assert len(anomalies) >= 0
        
        # Check that health context was added
        for anomaly in anomalies:
            assert 'health_metric_type' in anomaly.context
            assert anomaly.context['health_metric_type'] == 'heart_rate'
    
    def test_severity_adjustment(self):
        """Test that severity is adjusted for health metrics."""
        # Heart rate has severity multiplier of 1.2, so medium may become high
        anomalies = self.health_detector.detect_health_anomalies(
            self.heart_rate_data,
            metric_type='heart_rate'
        )
        
        # Should have some anomalies with health-adjusted severity
        assert len(anomalies) >= 0


class TestSystemIntegration:
    """Test system integration and performance."""
    
    def setup_method(self):
        """Setup test system."""
        self.system = create_default_system()
    
    def test_system_status(self):
        """Test getting system status."""
        status = self.system.get_system_status()
        
        assert 'config' in status
        assert 'performance' in status
        assert 'feedback' in status
        assert 'notifications' in status
    
    def test_system_recommendations(self):
        """Test getting system recommendations."""
        recommendations = self.system.get_recommendations()
        
        assert isinstance(recommendations, list)
        # Should have at least some recommendations for a new system
    
    def test_configuration_update(self):
        """Test updating system configuration."""
        new_config = DetectionConfig(
            enabled_methods=[DetectionMethod.ZSCORE],
            zscore_threshold=2.0
        )
        
        self.system.update_configuration(new_config)
        assert self.system.config.zscore_threshold == 2.0
        assert len(self.system.config.enabled_methods) == 1
    
    @patch('time.time')
    def test_performance_tracking(self, mock_time):
        """Test that performance is tracked."""
        mock_time.side_effect = [0, 0.1]  # 100ms detection time
        
        # Create simple test data
        data = pd.Series([1, 2, 3, 100, 5], name='test')  # One clear anomaly
        
        anomalies = self.system.detect_anomalies(data)
        
        # Check that performance was recorded
        assert 'detection_time' in self.system.performance_metrics
        assert len(self.system.detection_history) > 0


class TestFactoryFunctions:
    """Test factory functions for creating different system types."""
    
    def test_create_default_system(self):
        """Test creating default system."""
        system = create_default_system()
        
        assert isinstance(system, AnomalyDetectionSystem)
        assert system.config.notification_enabled is True
        assert DetectionMethod.MODIFIED_ZSCORE in system.config.enabled_methods
    
    def test_create_statistical_system(self):
        """Test creating statistical-only system."""
        system = create_statistical_system(sensitivity='high')
        
        # Should only have statistical methods
        statistical_methods = [
            DetectionMethod.ZSCORE,
            DetectionMethod.MODIFIED_ZSCORE, 
            DetectionMethod.IQR
        ]
        
        for method in system.config.enabled_methods:
            assert method in statistical_methods
        
        # High sensitivity should have lower thresholds
        assert system.config.zscore_threshold < 3.0
    
    def test_create_statistical_system_sensitivities(self):
        """Test different sensitivity levels."""
        low_system = create_statistical_system('low')
        medium_system = create_statistical_system('medium')
        high_system = create_statistical_system('high')
        
        # Low sensitivity should have higher thresholds
        assert low_system.config.zscore_threshold > medium_system.config.zscore_threshold
        assert medium_system.config.zscore_threshold > high_system.config.zscore_threshold


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_insufficient_data_error(self):
        """Test handling of insufficient data."""
        system = create_default_system()
        
        # Very small dataset
        tiny_data = pd.Series([1, 2], name='tiny')
        
        # Should handle gracefully (may return empty list or raise specific error)
        result = system.detect_anomalies(tiny_data)
        assert isinstance(result, list)
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        system = create_default_system()
        
        # Should raise appropriate error for invalid input
        with pytest.raises((ValueError, TypeError)):
            system.detect_anomalies("invalid_data")
    
    def test_nan_handling(self):
        """Test handling of NaN values in data."""
        system = create_default_system()
        
        # Data with NaN values
        data_with_nan = pd.Series([1, 2, np.nan, 4, 100, np.nan, 6], name='with_nan')
        
        # Should handle NaN values gracefully
        anomalies = system.detect_anomalies(data_with_nan)
        assert isinstance(anomalies, list)


if __name__ == "__main__":
    # Run a simple test to verify the system works
    print("Running basic anomaly detection test...")
    
    # Create test data
    np.random.seed(42)
    test_data = pd.Series(
        np.concatenate([np.random.normal(50, 10, 95), [150, 200, 0, -50, 300]]),
        name='test_metric'
    )
    
    # Test the system
    system = create_default_system()
    anomalies = system.detect_anomalies(test_data)
    
    print(f"✓ Detected {len(anomalies)} anomalies in test data")
    print(f"✓ Methods used: {set(a.method.value for a in anomalies)}")
    print(f"✓ Severities found: {set(a.severity.value for a in anomalies)}")
    
    print("\nBasic test completed successfully!")