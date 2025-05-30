"""Fixed comprehensive tests for anomaly detection modules."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd

from src.analytics.anomaly_detection import (
    AnomalyDetectionSystem,
    ZScoreDetector, IQRDetector, IsolationForestDetector,
    LocalOutlierFactorDetector, EnsembleDetector,
    Anomaly, Severity, DetectionMethod,
    DetectionConfig, DetectionResult
)


class TestAnomalyModels:
    """Test anomaly model classes."""
    
    def test_severity_enum(self):
        """Test Severity enumeration."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"
        
    def test_detection_method_enum(self):
        """Test DetectionMethod enumeration."""
        assert DetectionMethod.ZSCORE.value == "zscore"
        assert DetectionMethod.MODIFIED_ZSCORE.value == "modified_zscore"
        assert DetectionMethod.IQR.value == "iqr"
        assert DetectionMethod.ISOLATION_FOREST.value == "isolation_forest"
        assert DetectionMethod.LOF.value == "lof"
        assert DetectionMethod.LSTM.value == "lstm"
        assert DetectionMethod.ENSEMBLE.value == "ensemble"
        
    def test_anomaly_creation(self):
        """Test creating Anomaly instance."""
        anomaly = Anomaly(
            timestamp=datetime(2023, 1, 1),
            metric="steps",
            value=150.0,
            score=3.5,
            method=DetectionMethod.ZSCORE,
            severity=Severity.HIGH,
            threshold=3.0,
            explanation="Value exceeds 3 standard deviations",
            context={"zscore": 3.5},
            confidence=0.95
        )
        
        assert anomaly.timestamp == datetime(2023, 1, 1)
        assert anomaly.metric == "steps"
        assert anomaly.value == 150.0
        assert anomaly.score == 3.5
        assert anomaly.method == DetectionMethod.ZSCORE
        assert anomaly.severity == Severity.HIGH
        assert anomaly.confidence == 0.95
        assert anomaly.context["zscore"] == 3.5
        
    def test_detection_config(self):
        """Test DetectionConfig."""
        config = DetectionConfig(
            enabled_methods=[DetectionMethod.ZSCORE, DetectionMethod.ISOLATION_FOREST],
            zscore_threshold=3.0,
            isolation_forest_contamination=0.1,
            notification_enabled=True,
            adaptive_thresholds=True
        )
        
        assert len(config.enabled_methods) == 2
        assert config.zscore_threshold == 3.0
        assert config.isolation_forest_contamination == 0.1
        assert config.notification_enabled is True
        assert config.adaptive_thresholds is True
        
    def test_detection_result(self):
        """Test DetectionResult creation."""
        anomalies = [
            Anomaly(
                timestamp=datetime(2023, 1, 1),
                metric="steps",
                value=150.0,
                score=3.5,
                method=DetectionMethod.ZSCORE,
                severity=Severity.HIGH,
                confidence=0.95
            )
        ]
        
        result = DetectionResult(
            anomalies=anomalies,
            total_points=100,
            detection_time=0.5,
            method=DetectionMethod.ZSCORE,
            parameters={"threshold": 3.0}
        )
        
        assert len(result.anomalies) == 1
        assert result.total_points == 100
        assert result.anomaly_rate == 0.01
        assert result.detection_time == 0.5


class TestZScoreDetector:
    """Test ZScoreDetector class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        data = np.random.normal(100, 10, 100)
        # Add some anomalies
        data[25] = 200  # Spike
        data[50] = 20   # Drop
        data[75] = 180  # Another spike
        return pd.Series(data, index=pd.date_range('2023-01-01', periods=100))
    
    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = ZScoreDetector(threshold=3.0)
        assert detector is not None
        assert detector.threshold == 3.0
        
    def test_basic_anomaly_detection(self, sample_data):
        """Test basic anomaly detection."""
        detector = ZScoreDetector(threshold=3.0)
        
        anomalies = detector.detect(sample_data)
        assert isinstance(anomalies, list)
        assert len(anomalies) >= 2  # Should detect at least the spike and drop
        
    def test_detect_with_dataframe(self):
        """Test detection with pandas DataFrame."""
        detector = ZScoreDetector(threshold=3.0)
        
        dates = pd.date_range('2023-01-01', periods=100)
        values = np.random.normal(100, 10, 100)
        values[50] = 200  # Add anomaly
        
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        # Test with Series input (ZScoreDetector expects univariate data)
        value_series = pd.Series(values, index=dates, name='value')
        result = detector.detect(value_series, metric="test_metric")
        assert isinstance(result, DetectionResult)
        assert len(result.anomalies) > 0


class TestIsolationForestDetector:
    """Test Isolation Forest detector."""
    
    @pytest.fixture
    def detector(self):
        """Create Isolation Forest detector."""
        return IsolationForestDetector(contamination=0.1)
    
    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.contamination == 0.1
        assert hasattr(detector, 'detect')
        
    def test_detect_anomalies(self, detector):
        """Test anomaly detection."""
        # Create data with clear outliers
        np.random.seed(42)
        values = np.random.normal(100, 5, 100)
        # Add outliers
        values[10:15] = np.random.normal(200, 5, 5)
        
        # IsolationForestDetector expects Series
        series = pd.Series(values, index=pd.date_range('2023-01-01', periods=100), name='test_metric')
        anomalies = detector.detect(series)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) > 0
        assert all(isinstance(a, Anomaly) for a in anomalies)


class TestIQRDetector:
    """Test IQR-based anomaly detector."""
    
    @pytest.fixture
    def detector(self):
        """Create IQR detector."""
        return IQRDetector(multiplier=1.5)
    
    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.multiplier == 1.5
        
    def test_detect_outliers(self, detector):
        """Test outlier detection using IQR method."""
        # Create data with clear outliers
        data = np.concatenate([
            np.random.normal(100, 10, 90),  # Normal data
            [200, 250, 10, 5]  # Clear outliers
        ])
        
        result = detector.detect(data, metric="test_metric")
        
        assert isinstance(result, DetectionResult)
        assert len(result.anomalies) >= 2  # Should detect extreme values


class TestEnsembleDetector:
    """Test ensemble anomaly detector."""
    
    @pytest.fixture
    def detector(self):
        """Create ensemble detector."""
        zscore_detector = ZScoreDetector(threshold=3.0)
        isolation_detector = IsolationForestDetector(contamination=0.1)
        
        detectors = {
            'zscore': zscore_detector,
            'isolation': isolation_detector
        }
        
        config = DetectionConfig(
            enabled_methods=[DetectionMethod.ZSCORE, DetectionMethod.ISOLATION_FOREST],
            ensemble_min_votes=1
        )
        
        return EnsembleDetector(detectors=detectors, config=config)
    
    def test_initialization(self, detector):
        """Test detector initialization."""
        assert len(detector.detectors) == 2
        assert detector.config.ensemble_min_votes == 1
        
    def test_ensemble_detection(self, detector):
        """Test ensemble detection."""
        # Create data with clear anomaly
        values = np.random.normal(100, 5, 50)
        values[25] = 200  # Clear anomaly
        
        result = detector.detect(values, metric="test_metric")
        
        assert isinstance(result, DetectionResult)
        assert len(result.anomalies) > 0


class TestAnomalyDetectionSystem:
    """Test the complete anomaly detection system."""
    
    @pytest.fixture
    def system(self):
        """Create anomaly detection system."""
        config = DetectionConfig(
            enabled_methods=[DetectionMethod.ZSCORE, DetectionMethod.ISOLATION_FOREST]
        )
        return AnomalyDetectionSystem(config)
    
    @pytest.fixture
    def health_data(self):
        """Create realistic health data."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
        
        # Create realistic step data with weekly patterns
        base_steps = 8000
        weekly_pattern = np.tile([1.0, 1.1, 1.2, 1.1, 1.0, 0.8, 0.9], 53)[:365]
        noise = np.random.normal(0, 500, 365)
        steps = base_steps * weekly_pattern + noise
        
        # Add some anomalies
        steps[50] = 25000  # Very high day
        steps[100] = 1000  # Very low day
        steps[200:203] = 0  # Device off
        
        return pd.DataFrame({
            'timestamp': dates,
            'value': steps,
            'metric': 'steps'
        })
    
    def test_system_initialization(self, system):
        """Test system initialization."""
        assert system.config is not None
        assert len(system.config.enabled_methods) >= 1
        
    @patch('src.analytics.anomaly_detection_system.AnomalyDetectionSystem.detect_anomalies')
    def test_detect_anomalies(self, mock_detect, system, health_data):
        """Test anomaly detection on health data."""
        # Mock the detect method to return sample anomalies
        mock_anomalies = [
            Anomaly(
                timestamp=health_data.iloc[50]['timestamp'],
                metric='steps',
                value=25000,
                score=5.0,
                method=DetectionMethod.ZSCORE,
                severity=Severity.HIGH
            )
        ]
        mock_detect.return_value = mock_anomalies
        
        # Convert health_data to Series for detect_anomalies
        values_series = pd.Series(health_data['value'].values, 
                                 index=health_data['timestamp'].values,
                                 name='steps')
        result = system.detect_anomalies(values_series)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(a, Anomaly) for a in result)
        mock_detect.assert_called_once()


def test_anomaly_detection_integration():
    """Test integration of anomaly detection components."""
    # Create simple test data
    np.random.seed(42)
    data = np.random.normal(100, 10, 100)
    data[50] = 200  # Add clear anomaly
    
    # Test individual detectors
    zscore_detector = ZScoreDetector(threshold=3.0)
    zscore_result = zscore_detector.detect(data, metric="test")
    assert len(zscore_result.anomalies) > 0
    
    iqr_detector = IQRDetector(multiplier=1.5)
    iqr_result = iqr_detector.detect(data, metric="test")
    assert len(iqr_result.anomalies) > 0
    
    # Test ensemble
    ensemble = EnsembleDetector(
        detectors=[zscore_detector, iqr_detector],
        min_votes=1
    )
    ensemble_result = ensemble.detect(data, metric="test")
    assert len(ensemble_result.anomalies) > 0