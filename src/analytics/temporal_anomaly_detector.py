"""
LSTM-based Temporal Anomaly Detection with Hybrid Approach.

This module implements a hybrid anomaly detection system that combines:
1. Statistical foundation (STL + IQR) for immediate deployment
2. Optional LSTM enhancement for complex temporal patterns

The system gracefully degrades when TensorFlow is not available.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import warnings
from statsmodels.tsa.seasonal import STL
from sklearn.preprocessing import StandardScaler

from .anomaly_models import (
    Anomaly, DetectionMethod, Severity, ModelNotTrainedError,
    InsufficientDataError
)
from .anomaly_detectors import BaseDetector

# Try to import TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
    from tensorflow.keras.optimizers import Adam
    import joblib
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    warnings.warn("TensorFlow not available. Using statistical-only mode for temporal anomaly detection.")


class STLAnomalyDetector(BaseDetector):
    """Statistical anomaly detector using STL decomposition + IQR."""
    
    def __init__(self, seasonal: int = 7, trend: Optional[int] = None, 
                 iqr_multiplier: float = 1.5):
        super().__init__("STL Anomaly Detector", DetectionMethod.IQR)
        self.seasonal = seasonal
        self.trend = trend
        self.iqr_multiplier = iqr_multiplier
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Detect anomalies using STL decomposition and IQR on residuals."""
        self._validate_data(data)
        
        if len(data) < 2 * self.seasonal:
            raise InsufficientDataError(f"Need at least {2 * self.seasonal} points for STL")
        
        try:
            # Perform STL decomposition
            stl = STL(data, seasonal=self.seasonal, trend=self.trend)
            result = stl.fit()
            
            # Work with residuals
            residuals = result.resid
            
            # Calculate IQR bounds on residuals
            Q1 = residuals.quantile(0.25)
            Q3 = residuals.quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0:
                return []  # No variation in residuals
            
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            
            # Find anomalies
            anomalies = []
            anomaly_mask = (residuals < lower_bound) | (residuals > upper_bound)
            
            for idx in data[anomaly_mask].index:
                residual_value = residuals[idx]
                
                # Calculate score based on distance from bounds
                if residual_value < lower_bound:
                    score = (lower_bound - residual_value) / IQR
                else:
                    score = (residual_value - upper_bound) / IQR
                
                anomalies.append(Anomaly(
                    timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                    metric=data.name or "temporal_pattern",
                    value=data[idx],
                    score=float(score),
                    method=self.method,
                    severity=self._calculate_severity(score, 1.0),
                    threshold=self.iqr_multiplier,
                    context={
                        'trend_value': float(result.trend[idx]),
                        'seasonal_value': float(result.seasonal[idx]),
                        'residual_value': float(residual_value),
                        'Q1': float(Q1),
                        'Q3': float(Q3),
                        'IQR': float(IQR),
                        'lower_bound': float(lower_bound),
                        'upper_bound': float(upper_bound),
                        'decomposition_method': 'STL'
                    }
                ))
            
            return anomalies
            
        except Exception as e:
            # Fallback to simple IQR if STL fails
            warnings.warn(f"STL decomposition failed, using simple IQR: {e}")
            return self._simple_iqr_detection(data)
    
    def _simple_iqr_detection(self, data: pd.Series) -> List[Anomaly]:
        """Fallback to simple IQR detection without decomposition."""
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR == 0:
            return []
        
        lower_bound = Q1 - self.iqr_multiplier * IQR
        upper_bound = Q3 + self.iqr_multiplier * IQR
        
        anomalies = []
        anomaly_mask = (data < lower_bound) | (data > upper_bound)
        
        for idx in data[anomaly_mask].index:
            value = data[idx]
            if value < lower_bound:
                score = (lower_bound - value) / IQR
            else:
                score = (value - upper_bound) / IQR
            
            anomalies.append(Anomaly(
                timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                metric=data.name or "temporal_pattern",
                value=value,
                score=float(score),
                method=self.method,
                severity=self._calculate_severity(score, 1.0),
                threshold=self.iqr_multiplier,
                context={
                    'Q1': float(Q1),
                    'Q3': float(Q3),
                    'IQR': float(IQR),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'decomposition_method': 'None (IQR only)'
                }
            ))
        
        return anomalies


class LSTMTemporalDetector(BaseDetector):
    """LSTM-based temporal anomaly detector with reconstruction error."""
    
    def __init__(self, sequence_length: int = 24, threshold_percentile: float = 95,
                 encoding_dim: int = 128, learning_rate: float = 0.001):
        # Add HYBRID method to DetectionMethod if needed
        super().__init__("LSTM Temporal Detector", DetectionMethod.LSTM)
        self.sequence_length = sequence_length
        self.threshold_percentile = threshold_percentile
        self.encoding_dim = encoding_dim
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM detector")
    
    def _build_model(self, input_shape: Tuple[int, int]) -> Any:
        """Build LSTM autoencoder model."""
        model = Sequential([
            LSTM(self.encoding_dim, activation='relu',
                 input_shape=input_shape, return_sequences=False),
            RepeatVector(input_shape[0]),
            LSTM(self.encoding_dim, activation='relu', return_sequences=True),
            TimeDistributed(Dense(input_shape[1]))
        ])
        
        model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='mse')
        return model
    
    def train(self, data: pd.Series, epochs: int = 50, batch_size: int = 32,
              validation_split: float = 0.2) -> Dict[str, Any]:
        """Train the LSTM model on historical data."""
        if len(data) < self.sequence_length + 1:
            raise InsufficientDataError(f"Need at least {self.sequence_length + 1} points")
        
        # Create sequences
        sequences = self._create_sequences(data)
        
        # Scale data
        sequences_reshaped = sequences.reshape(-1, 1)
        scaled_sequences = self.scaler.fit_transform(sequences_reshaped)
        scaled_sequences = scaled_sequences.reshape(sequences.shape)
        
        # Reshape for LSTM [samples, timesteps, features]
        X = scaled_sequences.reshape((scaled_sequences.shape[0], 
                                    scaled_sequences.shape[1], 1))
        
        # Build model
        self.model = self._build_model((self.sequence_length, 1))
        
        # Train autoencoder
        history = self.model.fit(
            X, X,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=0
        )
        
        # Calculate threshold from training data
        train_errors = self._calculate_reconstruction_errors(X)
        self.threshold = np.percentile(train_errors, self.threshold_percentile)
        
        self.is_trained = True
        self.last_training_time = datetime.now()
        
        return {
            'history': history.history,
            'threshold': self.threshold,
            'final_loss': history.history['loss'][-1],
            'final_val_loss': history.history.get('val_loss', [None])[-1]
        }
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Detect temporal anomalies using trained LSTM."""
        if not self.is_trained:
            raise ModelNotTrainedError("LSTM model must be trained before detection")
        
        self._validate_data(data)
        
        if len(data) < self.sequence_length:
            raise InsufficientDataError(f"Need at least {self.sequence_length} points")
        
        sequences = self._create_sequences(data)
        
        # Scale sequences
        sequences_reshaped = sequences.reshape(-1, 1)
        scaled_sequences = self.scaler.transform(sequences_reshaped)
        scaled_sequences = scaled_sequences.reshape(sequences.shape)
        
        # Reshape for LSTM
        X = scaled_sequences.reshape((scaled_sequences.shape[0],
                                    scaled_sequences.shape[1], 1))
        
        # Get reconstruction errors
        reconstruction_errors = self._calculate_reconstruction_errors(X)
        
        # Find anomalies
        anomalies = []
        anomaly_indices = np.where(reconstruction_errors > self.threshold)[0]
        
        for idx in anomaly_indices:
            # Map back to original timestamp
            original_idx = idx + self.sequence_length - 1
            
            if original_idx < len(data):
                # Get predicted vs actual patterns
                predicted_sequence = self.model.predict(X[idx:idx+1], verbose=0)[0]
                actual_sequence = X[idx]
                
                # Transform back to original scale for explanation
                actual_orig = self.scaler.inverse_transform(
                    actual_sequence.reshape(-1, 1)
                ).flatten()
                predicted_orig = self.scaler.inverse_transform(
                    predicted_sequence.reshape(-1, 1)
                ).flatten()
                
                anomalies.append(Anomaly(
                    timestamp=data.index[original_idx],
                    metric=data.name or "temporal_pattern",
                    value=data.iloc[original_idx],
                    score=float(reconstruction_errors[idx]),
                    method=self.method,
                    severity=self._calculate_severity(
                        reconstruction_errors[idx], self.threshold
                    ),
                    threshold=self.threshold,
                    confidence=self._calculate_confidence(reconstruction_errors[idx]),
                    context={
                        'sequence_length': self.sequence_length,
                        'reconstruction_error': float(reconstruction_errors[idx]),
                        'expected_pattern': predicted_orig.tolist(),
                        'actual_pattern': actual_orig.tolist(),
                        'pattern_deviation': self._calculate_pattern_deviation(
                            actual_sequence, predicted_sequence
                        ),
                        'percentile_rank': float(
                            (reconstruction_errors < reconstruction_errors[idx]).sum() / 
                            len(reconstruction_errors) * 100
                        )
                    }
                ))
        
        return anomalies
    
    def _create_sequences(self, data: pd.Series) -> np.ndarray:
        """Create sliding window sequences for LSTM input."""
        sequences = []
        
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data.iloc[i:i + self.sequence_length].values)
        
        return np.array(sequences)
    
    def _calculate_reconstruction_errors(self, sequences: np.ndarray) -> np.ndarray:
        """Calculate reconstruction errors for sequences."""
        reconstructed = self.model.predict(sequences, verbose=0)
        errors = np.mean((sequences - reconstructed) ** 2, axis=(1, 2))
        return errors
    
    def _calculate_pattern_deviation(self, actual: np.ndarray,
                                   predicted: np.ndarray) -> Dict[str, float]:
        """Calculate specific pattern deviations."""
        actual_flat = actual.flatten()
        predicted_flat = predicted.flatten()
        
        # Avoid division by zero
        correlation = 0.0
        if np.std(actual_flat) > 0 and np.std(predicted_flat) > 0:
            correlation = np.corrcoef(actual_flat, predicted_flat)[0, 1]
        
        return {
            'mse': float(np.mean((actual_flat - predicted_flat) ** 2)),
            'mae': float(np.mean(np.abs(actual_flat - predicted_flat))),
            'max_deviation': float(np.max(np.abs(actual_flat - predicted_flat))),
            'correlation': float(correlation)
        }
    
    def _calculate_confidence(self, reconstruction_error: float) -> float:
        """Calculate confidence score based on reconstruction error."""
        if self.threshold > 0:
            # Higher error relative to threshold = higher confidence it's an anomaly
            confidence = min(1.0, reconstruction_error / (2 * self.threshold))
        else:
            confidence = 1.0
        return confidence
    
    def save_model(self, filepath: str):
        """Save trained model and scaler."""
        if not self.is_trained:
            raise ModelNotTrainedError("Cannot save untrained model")
        
        # Save Keras model
        self.model.save(f"{filepath}_model.h5")
        
        # Save scaler and metadata
        metadata = {
            'scaler': self.scaler,
            'threshold': self.threshold,
            'sequence_length': self.sequence_length,
            'threshold_percentile': self.threshold_percentile,
            'encoding_dim': self.encoding_dim,
            'is_trained': self.is_trained,
            'last_training_time': self.last_training_time
        }
        
        joblib.dump(metadata, f"{filepath}_metadata.pkl")
    
    def load_model(self, filepath: str):
        """Load trained model and scaler."""
        # Load Keras model
        self.model = load_model(f"{filepath}_model.h5")
        
        # Load scaler and metadata
        metadata = joblib.load(f"{filepath}_metadata.pkl")
        
        self.scaler = metadata['scaler']
        self.threshold = metadata['threshold']
        self.sequence_length = metadata['sequence_length']
        self.threshold_percentile = metadata['threshold_percentile']
        self.encoding_dim = metadata['encoding_dim']
        self.is_trained = metadata['is_trained']
        self.last_training_time = metadata['last_training_time']
    
    def update_model(self, new_data: pd.Series, epochs: int = 10):
        """Incrementally update model with new data."""
        if not self.is_trained:
            raise ModelNotTrainedError("Model must be initially trained")
        
        new_sequences = self._create_sequences(new_data)
        sequences_reshaped = new_sequences.reshape(-1, 1)
        scaled_sequences = self.scaler.transform(sequences_reshaped)
        scaled_sequences = scaled_sequences.reshape(new_sequences.shape)
        
        X = scaled_sequences.reshape((scaled_sequences.shape[0],
                                    scaled_sequences.shape[1], 1))
        
        # Incremental training
        self.model.fit(
            X, X,
            epochs=epochs,
            batch_size=16,
            verbose=0
        )
        
        # Update threshold
        new_errors = self._calculate_reconstruction_errors(X)
        combined_threshold = np.percentile(new_errors, self.threshold_percentile)
        
        # Exponential moving average for threshold update
        alpha = 0.1  # Learning rate for threshold adaptation
        self.threshold = (1 - alpha) * self.threshold + alpha * combined_threshold
        
        self.last_training_time = datetime.now()


class HybridTemporalAnomalyDetector(BaseDetector):
    """Hybrid detector combining STL+IQR with optional LSTM enhancement."""
    
    def __init__(self, enable_ml: bool = True, fallback_only: bool = False,
                 seasonal: int = 7, sequence_length: int = 24,
                 ensemble_weights: Optional[Dict[str, float]] = None):
        # Create a new detection method for hybrid
        super().__init__("Hybrid Temporal Detector", DetectionMethod.ENSEMBLE)
        
        # Always available statistical detector
        self.statistical_detector = STLAnomalyDetector(seasonal=seasonal)
        
        # Optional ML enhancement
        self.ml_detector = None
        self.enable_ml = enable_ml
        if enable_ml and not fallback_only and TENSORFLOW_AVAILABLE:
            try:
                self.ml_detector = LSTMTemporalDetector(sequence_length=sequence_length)
            except ImportError:
                warnings.warn("TensorFlow not available, using statistical only")
        
        # Ensemble weights
        if ensemble_weights is None:
            self.ensemble_weights = {'statistical': 0.6, 'ml': 0.4}
        else:
            self.ensemble_weights = ensemble_weights
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Hybrid detection with ensemble voting."""
        # Always get statistical results
        statistical_anomalies = self.statistical_detector.detect(data)
        
        if self.ml_detector and self.ml_detector.is_trained:
            try:
                ml_anomalies = self.ml_detector.detect(data)
                return self._ensemble_vote(statistical_anomalies, ml_anomalies, data)
            except Exception as e:
                warnings.warn(f"ML detection failed, using statistical only: {e}")
                return statistical_anomalies
        else:
            # Fallback to statistical only
            return statistical_anomalies
    
    def train_ml_component(self, data: pd.Series, **kwargs) -> Optional[Dict[str, Any]]:
        """Train the ML component if available."""
        if self.ml_detector:
            return self.ml_detector.train(data, **kwargs)
        else:
            warnings.warn("ML detector not available for training")
            return None
    
    def _ensemble_vote(self, stat_anomalies: List[Anomaly], 
                      ml_anomalies: List[Anomaly], 
                      data: pd.Series) -> List[Anomaly]:
        """Combine results with WSJ-style confidence indicators."""
        # Create lookup dictionaries by timestamp
        stat_dict = {a.timestamp: a for a in stat_anomalies}
        ml_dict = {a.timestamp: a for a in ml_anomalies}
        
        # Get all unique timestamps
        all_timestamps = set(stat_dict.keys()) | set(ml_dict.keys())
        
        ensemble_anomalies = []
        
        for timestamp in all_timestamps:
            stat_anomaly = stat_dict.get(timestamp)
            ml_anomaly = ml_dict.get(timestamp)
            
            # Calculate weighted score
            if stat_anomaly and ml_anomaly:
                # Both methods agree
                weighted_score = (
                    self.ensemble_weights['statistical'] * stat_anomaly.score +
                    self.ensemble_weights['ml'] * ml_anomaly.score
                )
                confidence = 0.9  # High confidence when both agree
                agreement = "Both methods"
            elif stat_anomaly:
                # Only statistical
                weighted_score = stat_anomaly.score
                confidence = 0.6  # Medium confidence
                agreement = "Statistical only"
            else:
                # Only ML
                weighted_score = ml_anomaly.score
                confidence = 0.7  # ML alone has decent confidence
                agreement = "ML only"
            
            # Create ensemble anomaly
            base_anomaly = stat_anomaly or ml_anomaly
            
            # Determine severity based on weighted score and agreement
            if stat_anomaly and ml_anomaly:
                # Take higher severity when both agree
                severity = max(stat_anomaly.severity, ml_anomaly.severity,
                             key=lambda s: ['low', 'medium', 'high', 'critical'].index(s.value))
            else:
                severity = base_anomaly.severity
            
            # Build comprehensive context
            context = {
                'detection_agreement': agreement,
                'ensemble_confidence': confidence,
                'statistical_score': stat_anomaly.score if stat_anomaly else None,
                'ml_score': ml_anomaly.score if ml_anomaly else None,
                'weighted_score': weighted_score
            }
            
            # Add method-specific contexts
            if stat_anomaly:
                context['statistical_context'] = stat_anomaly.context
            if ml_anomaly:
                context['ml_context'] = ml_anomaly.context
            
            # Add data context for WSJ-style presentation
            if timestamp in data.index:
                idx_pos = data.index.get_loc(timestamp)
                context['recent_trend'] = self._get_recent_trend(data, idx_pos)
                context['percentile_in_data'] = (data < data.iloc[idx_pos]).sum() / len(data) * 100
            
            ensemble_anomalies.append(Anomaly(
                timestamp=timestamp,
                metric=base_anomaly.metric,
                value=base_anomaly.value,
                score=weighted_score,
                method=DetectionMethod.ENSEMBLE,
                severity=severity,
                threshold=base_anomaly.threshold,
                confidence=confidence,
                context=context
            ))
        
        # Sort by score and timestamp
        ensemble_anomalies.sort(key=lambda a: (abs(a.score), a.timestamp), reverse=True)
        
        return ensemble_anomalies
    
    def _get_recent_trend(self, data: pd.Series, idx: int, window: int = 7) -> str:
        """Get recent trend description for context."""
        start_idx = max(0, idx - window)
        end_idx = min(len(data), idx + 1)
        
        if end_idx - start_idx < 3:
            return "insufficient_data"
        
        window_data = data.iloc[start_idx:end_idx]
        
        # Simple linear regression for trend
        x = np.arange(len(window_data))
        slope = np.polyfit(x, window_data.values, 1)[0]
        
        # Normalize slope by data scale
        data_range = window_data.max() - window_data.min()
        if data_range > 0:
            normalized_slope = slope / data_range
            
            if abs(normalized_slope) < 0.05:
                return "stable"
            elif normalized_slope > 0.1:
                return "sharply_increasing"
            elif normalized_slope > 0:
                return "increasing"
            elif normalized_slope < -0.1:
                return "sharply_decreasing"
            else:
                return "decreasing"
        else:
            return "flat"
    
    def save_models(self, filepath_prefix: str):
        """Save both statistical and ML models."""
        # Statistical detector doesn't need saving (no state)
        
        # Save ML model if available and trained
        if self.ml_detector and self.ml_detector.is_trained:
            self.ml_detector.save_model(f"{filepath_prefix}_lstm")
    
    def load_models(self, filepath_prefix: str):
        """Load saved models."""
        # Try to load ML model
        if self.ml_detector:
            try:
                self.ml_detector.load_model(f"{filepath_prefix}_lstm")
            except Exception as e:
                warnings.warn(f"Could not load ML model: {e}")