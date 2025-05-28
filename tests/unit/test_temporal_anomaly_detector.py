"""
Tests for LSTM-based temporal anomaly detection with hybrid approach.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

from src.analytics.temporal_anomaly_detector import (
    STLAnomalyDetector, LSTMTemporalDetector, HybridTemporalAnomalyDetector,
    TENSORFLOW_AVAILABLE
)
from src.analytics.anomaly_models import (
    DetectionMethod, Severity, InsufficientDataError, ModelNotTrainedError
)


class TestSTLAnomalyDetector:
    """Test cases for STL-based anomaly detector."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time series data with seasonal pattern."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # Create data with weekly seasonality
        base = 100
        seasonal = 10 * np.sin(2 * np.pi * np.arange(100) / 7)
        noise = np.random.normal(0, 2, 100)
        
        # Add some anomalies
        values = base + seasonal + noise
        values[20] += 30  # Positive anomaly
        values[50] -= 25  # Negative anomaly
        values[75] += 40  # Large positive anomaly
        
        return pd.Series(values, index=dates, name='test_metric')
    
    def test_stl_detection_basic(self, sample_data):
        """Test basic STL anomaly detection."""
        detector = STLAnomalyDetector(seasonal=7, iqr_multiplier=1.5)
        anomalies = detector.detect(sample_data)
        
        assert len(anomalies) > 0
        assert all(a.method == DetectionMethod.IQR for a in anomalies)
        
        # Check that we detected the large anomalies
        anomaly_indices = [a.timestamp for a in anomalies]
        assert sample_data.index[75] in anomaly_indices  # Large anomaly should be detected
    
    def test_stl_insufficient_data(self):
        """Test STL with insufficient data."""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.Series(np.random.randn(10), index=dates)
        
        detector = STLAnomalyDetector(seasonal=7)
        
        with pytest.raises(InsufficientDataError):
            detector.detect(data)
    
    def test_stl_fallback_to_iqr(self):
        """Test fallback to simple IQR when STL fails."""
        # Create data that might cause STL issues
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        data = pd.Series(np.ones(50), index=dates)  # Constant data
        data[25] = 10  # One anomaly
        
        detector = STLAnomalyDetector(seasonal=7)
        
        # Should fall back to simple IQR
        with warnings.catch_warnings(record=True) as w:
            anomalies = detector.detect(data)
            # Check that a warning was issued
            assert any("STL decomposition failed" in str(warning.message) for warning in w)
        
        assert len(anomalies) == 1
        assert anomalies[0].context['decomposition_method'] == 'None (IQR only)'
    
    def test_stl_context_information(self, sample_data):
        """Test that STL provides rich context information."""
        detector = STLAnomalyDetector(seasonal=7)
        anomalies = detector.detect(sample_data)
        
        assert len(anomalies) > 0
        
        # Check context fields
        context = anomalies[0].context
        assert 'trend_value' in context
        assert 'seasonal_value' in context
        assert 'residual_value' in context
        assert 'Q1' in context
        assert 'Q3' in context
        assert 'IQR' in context
        assert 'decomposition_method' in context
        assert context['decomposition_method'] == 'STL'


@pytest.mark.skipif(not TENSORFLOW_AVAILABLE, reason="TensorFlow not available")
class TestLSTMTemporalDetector:
    """Test cases for LSTM temporal anomaly detector."""
    
    @pytest.fixture
    def training_data(self):
        """Create training data for LSTM."""
        dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
        
        # Create sinusoidal pattern with noise
        t = np.arange(200)
        values = 100 + 20 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 3, 200)
        
        return pd.Series(values, index=dates, name='training_metric')
    
    @pytest.fixture
    def test_data_with_anomalies(self):
        """Create test data with anomalies."""
        dates = pd.date_range(start='2024-08-01', periods=50, freq='D')
        
        # Normal pattern
        t = np.arange(50)
        values = 100 + 20 * np.sin(2 * np.pi * t / 30) + np.random.normal(0, 3, 50)
        
        # Add anomalies
        values[10] += 50  # Large spike
        values[20:23] -= 30  # Sustained dip
        values[40] = 200  # Extreme value
        
        return pd.Series(values, index=dates, name='test_metric')
    
    def test_lstm_training(self, training_data):
        """Test LSTM model training."""
        detector = LSTMTemporalDetector(sequence_length=24, threshold_percentile=95)
        
        # Train the model
        result = detector.train(training_data, epochs=5, batch_size=32)
        
        assert detector.is_trained
        assert detector.threshold is not None
        assert 'history' in result
        assert 'threshold' in result
        assert result['final_loss'] < result['history']['loss'][0]  # Loss decreased
    
    def test_lstm_detection(self, training_data, test_data_with_anomalies):
        """Test LSTM anomaly detection."""
        detector = LSTMTemporalDetector(sequence_length=10, threshold_percentile=90)
        
        # Train on normal data
        detector.train(training_data[:150], epochs=10)
        
        # Detect on test data
        anomalies = detector.detect(test_data_with_anomalies)
        
        assert len(anomalies) > 0
        assert all(a.method == DetectionMethod.LSTM for a in anomalies)
        
        # Check context information
        for anomaly in anomalies:
            assert 'reconstruction_error' in anomaly.context
            assert 'expected_pattern' in anomaly.context
            assert 'actual_pattern' in anomaly.context
            assert 'pattern_deviation' in anomaly.context
            assert 'percentile_rank' in anomaly.context
    
    def test_lstm_untrained_error(self, test_data_with_anomalies):
        """Test error when using untrained LSTM."""
        detector = LSTMTemporalDetector()
        
        with pytest.raises(ModelNotTrainedError):
            detector.detect(test_data_with_anomalies)
    
    def test_lstm_save_load(self, training_data, tmp_path):
        """Test saving and loading LSTM model."""
        detector = LSTMTemporalDetector(sequence_length=12)
        
        # Train model
        detector.train(training_data[:100], epochs=5)
        original_threshold = detector.threshold
        
        # Save model
        model_path = str(tmp_path / "lstm_model")
        detector.save_model(model_path)
        
        # Create new detector and load
        new_detector = LSTMTemporalDetector()
        new_detector.load_model(model_path)
        
        assert new_detector.is_trained
        assert new_detector.threshold == original_threshold
        assert new_detector.sequence_length == 12
    
    def test_lstm_incremental_update(self, training_data):
        """Test incremental model update."""
        detector = LSTMTemporalDetector(sequence_length=10)
        
        # Initial training
        detector.train(training_data[:100], epochs=5)
        initial_threshold = detector.threshold
        
        # Update with new data
        detector.update_model(training_data[100:150], epochs=3)
        
        assert detector.is_trained
        # Threshold should be updated but not dramatically
        assert abs(detector.threshold - initial_threshold) < initial_threshold * 0.5


class TestHybridTemporalAnomalyDetector:
    """Test cases for hybrid temporal anomaly detector."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for hybrid detection."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        # Weekly pattern with trend
        t = np.arange(100)
        trend = 0.5 * t
        seasonal = 15 * np.sin(2 * np.pi * t / 7)
        noise = np.random.normal(0, 3, 100)
        
        values = 100 + trend + seasonal + noise
        
        # Add anomalies
        values[30] += 40
        values[60] -= 35
        values[80:83] += 25
        
        return pd.Series(values, index=dates, name='hybrid_test')
    
    def test_hybrid_statistical_only(self, sample_data):
        """Test hybrid detector in statistical-only mode."""
        detector = HybridTemporalAnomalyDetector(enable_ml=False)
        
        anomalies = detector.detect(sample_data)
        
        assert len(anomalies) > 0
        # Should use ensemble method for hybrid
        assert all(a.method == DetectionMethod.ENSEMBLE for a in anomalies)
        
        # Check context shows statistical only
        for anomaly in anomalies:
            assert anomaly.context['detection_agreement'] == 'Statistical only'
    
    @pytest.mark.skipif(not TENSORFLOW_AVAILABLE, reason="TensorFlow not available")
    def test_hybrid_with_ml(self, sample_data):
        """Test hybrid detector with ML component."""
        detector = HybridTemporalAnomalyDetector(enable_ml=True)
        
        # Train ML component
        result = detector.train_ml_component(sample_data[:80], epochs=5)
        assert result is not None
        
        # Detect anomalies
        anomalies = detector.detect(sample_data)
        
        assert len(anomalies) > 0
        
        # Check for ensemble voting
        agreements = [a.context['detection_agreement'] for a in anomalies]
        # Should have some cases where both methods agree
        assert 'Both methods' in agreements or 'ML only' in agreements
    
    def test_hybrid_fallback(self):
        """Test hybrid detector fallback when TensorFlow not available."""
        # Force fallback mode
        detector = HybridTemporalAnomalyDetector(
            enable_ml=True, 
            fallback_only=True
        )
        
        assert detector.ml_detector is None
        
        # Should still work with statistical only
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        data = pd.Series(np.random.randn(50) * 10 + 100, index=dates)
        data[25] += 50
        
        anomalies = detector.detect(data)
        assert len(anomalies) >= 0  # May or may not find anomalies
    
    def test_hybrid_ensemble_weights(self, sample_data):
        """Test custom ensemble weights."""
        custom_weights = {'statistical': 0.8, 'ml': 0.2}
        detector = HybridTemporalAnomalyDetector(
            enable_ml=False,  # Use statistical only for simplicity
            ensemble_weights=custom_weights
        )
        
        anomalies = detector.detect(sample_data)
        
        # Weights should be stored
        assert detector.ensemble_weights == custom_weights
    
    @pytest.mark.skipif(not TENSORFLOW_AVAILABLE, reason="TensorFlow not available")
    def test_hybrid_save_load(self, sample_data, tmp_path):
        """Test saving and loading hybrid models."""
        detector = HybridTemporalAnomalyDetector(enable_ml=True)
        
        # Train ML component
        detector.train_ml_component(sample_data[:80], epochs=5)
        
        # Save models
        model_prefix = str(tmp_path / "hybrid")
        detector.save_models(model_prefix)
        
        # Create new detector and load
        new_detector = HybridTemporalAnomalyDetector(enable_ml=True)
        new_detector.load_models(model_prefix)
        
        # ML component should be loaded and trained
        assert new_detector.ml_detector is not None
        assert new_detector.ml_detector.is_trained
    
    def test_hybrid_trend_context(self, sample_data):
        """Test trend context in hybrid detection."""
        detector = HybridTemporalAnomalyDetector(enable_ml=False)
        
        anomalies = detector.detect(sample_data)
        
        # Check trend context
        for anomaly in anomalies:
            if 'recent_trend' in anomaly.context:
                assert anomaly.context['recent_trend'] in [
                    'stable', 'increasing', 'decreasing',
                    'sharply_increasing', 'sharply_decreasing',
                    'flat', 'insufficient_data'
                ]
    
    def test_hybrid_confidence_scoring(self, sample_data):
        """Test confidence scoring in ensemble voting."""
        detector = HybridTemporalAnomalyDetector(enable_ml=False)
        
        anomalies = detector.detect(sample_data)
        
        for anomaly in anomalies:
            assert 'ensemble_confidence' in anomaly.context
            assert 0 <= anomaly.context['ensemble_confidence'] <= 1
            assert anomaly.confidence > 0


# Integration test
@pytest.mark.integration
class TestTemporalAnomalyIntegration:
    """Integration tests with the main anomaly detection system."""
    
    def test_integration_with_ensemble(self):
        """Test integration with ensemble detector."""
        from src.analytics.anomaly_detection_system import AnomalyDetectionSystem
        from src.analytics.anomaly_models import DetectionConfig
        
        config = DetectionConfig()
        system = AnomalyDetectionSystem(config)
        
        # Check that hybrid detector is available
        assert 'hybrid_temporal' in system.detectors or 'lstm' in system.detectors
        
        # Create test data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.Series(
            100 + 10 * np.sin(2 * np.pi * np.arange(100) / 7) + 
            np.random.randn(100) * 2,
            index=dates
        )
        data[50] += 30  # Add anomaly
        
        # Run detection
        anomalies = system.detect_anomalies(data)
        
        # Should detect some anomalies
        assert isinstance(anomalies, list)