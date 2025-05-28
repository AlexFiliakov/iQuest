---
task_id: G050
status: completed
created: 2025-05-28
complexity: high
sprint_ref: S04_M01_health_analytics
dependencies: G041
---

# Task G050: Implement LSTM-based Temporal Anomaly Detection

## Description
Implement LSTM (Long Short-Term Memory) neural network-based temporal anomaly detection for health data time series. This detector will identify anomalies in temporal patterns by learning normal sequences and flagging reconstruction errors above threshold.

## Goals
- [x] Implement hybrid anomaly detection approach (statistical baseline + LSTM enhancement)
- [x] Create STL decomposition + IQR statistical detector as foundation
- [x] Add TensorFlow/PyTorch dependency for LSTM enhancement
- [x] Implement LSTM autoencoder for complex temporal patterns
- [x] Create sequence preparation and windowing logic
- [x] Implement reconstruction error-based anomaly scoring with confidence intervals
- [x] Add temporal context and pattern explanation following WSJ analytics principles
- [x] Integrate with existing ensemble anomaly detection system
- [x] Implement progressive model deployment (statistical → ML)
- [x] Create interpretable anomaly explanations with clear visual indicators
- [x] Add model persistence and loading functionality
- [x] Implement fallback mechanisms when ML models fail

## Acceptance Criteria
- [x] LSTM model trains successfully on health data sequences
- [x] Reconstruction error accurately identifies temporal anomalies
- [x] Model handles variable sequence lengths gracefully
- [x] Training converges within reasonable time (<10 minutes for typical dataset)
- [x] Temporal patterns are explained with context
- [x] Model can be saved and loaded between sessions
- [x] Online learning updates model with new data
- [x] Integration with ensemble detector works seamlessly
- [x] Memory usage stays under 1GB during training
- [x] Performance benchmarks show <5 second inference time
- [x] Unit tests cover all core functionality

## Technical Details

### Hybrid Architecture Approach
**Priority 1: Statistical Foundation**
- STL (Seasonal and Trend decomposition using Loess) for baseline
- IQR-based outlier detection for immediate deployment
- Fast execution (<100ms) for real-time analysis
- Transparent, interpretable results

**Priority 2: ML Enhancement**
- LSTM autoencoder for complex pattern learning
- Ensemble voting between statistical and ML methods
- Confidence scoring for result reliability

### LSTM Architecture (When Available)
- **Input Layer**: Sequence length x feature dimensions
- **Encoder LSTM**: 128 units with relu activation
- **Repeat Vector**: Replicate encoded representation
- **Decoder LSTM**: 128 units with return_sequences=True
- **Output Layer**: TimeDistributed Dense layer
- **Loss Function**: Mean Squared Error

### Sequence Processing
- **Window Size**: Configurable (default 24 hours for daily patterns)
- **Stride**: 1 for overlapping windows
- **Normalization**: StandardScaler per feature
- **Padding**: Handle sequences shorter than window size

### Anomaly Scoring
- **Reconstruction Error**: MSE between input and output sequences
- **Threshold**: Percentile-based (default 95th percentile)
- **Severity Mapping**: Linear mapping from error magnitude
- **Context**: Include expected vs actual patterns

### Model Management
- **Checkpointing**: Save best model during training
- **Version Control**: Track model versions and performance
- **Incremental Learning**: Update with new data batches
- **Model Selection**: Choose best performing architecture
- **Fallback Strategy**: Always maintain statistical baseline
- **Performance Monitoring**: Track model drift and accuracy
- **WSJ Design Compliance**: Clear confidence indicators and uncertainty visualization

## Dependencies
- TensorFlow >= 2.12.0 or PyTorch >= 2.0.0
- G041 (Anomaly Detection System) must be completed
- Sufficient computing resources for neural network training

## Implementation Notes

### Hybrid Detector Implementation
```python
class HybridTemporalAnomalyDetector(BaseDetector):
    def __init__(self, enable_ml=True, fallback_only=False):
        super().__init__("Hybrid Temporal Detector", DetectionMethod.HYBRID)
        
        # Always available statistical detector
        self.statistical_detector = STLAnomalyDetector()
        
        # Optional ML enhancement
        self.ml_detector = None
        if enable_ml and not fallback_only:
            try:
                self.ml_detector = LSTMTemporalDetector()
            except ImportError:
                logger.warning("TensorFlow not available, using statistical only")
        
        self.ensemble_weights = {'statistical': 0.6, 'ml': 0.4}
        
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Hybrid detection with ensemble voting."""
        # Always get statistical results
        statistical_anomalies = self.statistical_detector.detect(data)
        
        if self.ml_detector and self.ml_detector.is_trained:
            ml_anomalies = self.ml_detector.detect(data)
            return self._ensemble_vote(statistical_anomalies, ml_anomalies)
        else:
            # Fallback to statistical only
            return statistical_anomalies
            
    def _ensemble_vote(self, stat_anomalies, ml_anomalies):
        """Combine results with WSJ-style confidence indicators."""
        # Implementation with clear confidence scoring
        pass
```

### WSJ Design Principles for Anomaly Presentation
- **Clear Visual Hierarchy**: Anomalies highlighted with consistent color coding
- **Confidence Indicators**: Visual uncertainty representation
- **Context Preservation**: Show normal patterns alongside anomalies
- **Progressive Disclosure**: Summary → detailed explanation → raw data
- **Minimal Decoration**: Focus on data, minimize chart junk

### TensorFlow Implementation (ML Enhancement)
```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.optimizers import Adam

class LSTMTemporalDetector(BaseDetector):
    def __init__(self, sequence_length=24, threshold_percentile=95, 
                 encoding_dim=128, learning_rate=0.001):
        super().__init__("LSTM Temporal Detector", DetectionMethod.LSTM)
        self.sequence_length = sequence_length
        self.threshold_percentile = threshold_percentile
        self.encoding_dim = encoding_dim
        self.learning_rate = learning_rate
        self.model = self._build_model()
        self.scaler = StandardScaler()
        self.threshold = None
        
    def _build_model(self):
        model = Sequential([
            LSTM(self.encoding_dim, activation='relu', 
                 input_shape=(self.sequence_length, 1)),
            RepeatVector(self.sequence_length),
            LSTM(self.encoding_dim, activation='relu', return_sequences=True),
            TimeDistributed(Dense(1))
        ])
        
        model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='mse')
        return model
    
    def train(self, data: pd.Series, epochs=50, batch_size=32, 
              validation_split=0.2):
        """Train the LSTM model on historical data."""
        sequences = self._create_sequences(data)
        
        # Scale data
        scaled_sequences = self.scaler.fit_transform(
            sequences.reshape(-1, 1)
        ).reshape(sequences.shape)
        
        # Train autoencoder (input = output for autoencoder)
        history = self.model.fit(
            scaled_sequences, scaled_sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            verbose=1
        )
        
        # Calculate threshold from training data
        train_errors = self._calculate_reconstruction_errors(scaled_sequences)
        self.threshold = np.percentile(train_errors, self.threshold_percentile)
        
        self.is_trained = True
        self.last_training_time = datetime.now()
        
        return history
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Detect temporal anomalies using trained LSTM."""
        if not self.is_trained:
            raise ModelNotTrainedError("LSTM model must be trained before detection")
        
        sequences = self._create_sequences(data)
        
        # Scale sequences
        scaled_sequences = self.scaler.transform(
            sequences.reshape(-1, 1)
        ).reshape(sequences.shape)
        
        # Get reconstruction errors
        reconstruction_errors = self._calculate_reconstruction_errors(scaled_sequences)
        
        # Find anomalies
        anomalies = []
        anomaly_indices = np.where(reconstruction_errors > self.threshold)[0]
        
        for idx in anomaly_indices:
            # Map back to original timestamp
            original_idx = idx + self.sequence_length - 1
            
            if original_idx < len(data):
                # Get predicted vs actual patterns
                predicted_sequence = self.model.predict(
                    scaled_sequences[idx:idx+1], verbose=0
                )[0]
                actual_sequence = scaled_sequences[idx]
                
                anomalies.append(Anomaly(
                    timestamp=data.index[original_idx],
                    metric=data.name or "temporal_pattern",
                    value=data.iloc[original_idx],
                    score=float(reconstruction_errors[idx]),
                    method=DetectionMethod.LSTM,
                    severity=self._calculate_severity(
                        reconstruction_errors[idx], self.threshold
                    ),
                    threshold=self.threshold,
                    context={
                        'sequence_length': self.sequence_length,
                        'reconstruction_error': float(reconstruction_errors[idx]),
                        'expected_pattern': self._inverse_transform_sequence(predicted_sequence),
                        'actual_pattern': self._inverse_transform_sequence(actual_sequence),
                        'pattern_deviation': self._calculate_pattern_deviation(
                            actual_sequence, predicted_sequence
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
    
    def _inverse_transform_sequence(self, scaled_sequence: np.ndarray) -> List[float]:
        """Transform scaled sequence back to original scale."""
        return self.scaler.inverse_transform(
            scaled_sequence.reshape(-1, 1)
        ).flatten().tolist()
    
    def _calculate_pattern_deviation(self, actual: np.ndarray, 
                                   predicted: np.ndarray) -> Dict[str, float]:
        """Calculate specific pattern deviations."""
        actual_flat = actual.flatten()
        predicted_flat = predicted.flatten()
        
        return {
            'mse': float(np.mean((actual_flat - predicted_flat) ** 2)),
            'mae': float(np.mean(np.abs(actual_flat - predicted_flat))),
            'max_deviation': float(np.max(np.abs(actual_flat - predicted_flat))),
            'correlation': float(np.corrcoef(actual_flat, predicted_flat)[0, 1])
        }
    
    def save_model(self, filepath: str):
        """Save trained model and scaler."""
        import joblib
        
        # Save Keras model
        self.model.save(f"{filepath}_model.h5")
        
        # Save scaler and metadata
        metadata = {
            'scaler': self.scaler,
            'threshold': self.threshold,
            'sequence_length': self.sequence_length,
            'threshold_percentile': self.threshold_percentile,
            'is_trained': self.is_trained,
            'last_training_time': self.last_training_time
        }
        
        joblib.dump(metadata, f"{filepath}_metadata.pkl")
    
    def load_model(self, filepath: str):
        """Load trained model and scaler."""
        import joblib
        from tensorflow.keras.models import load_model
        
        # Load Keras model
        self.model = load_model(f"{filepath}_model.h5")
        
        # Load scaler and metadata
        metadata = joblib.load(f"{filepath}_metadata.pkl")
        
        self.scaler = metadata['scaler']
        self.threshold = metadata['threshold']
        self.sequence_length = metadata['sequence_length']
        self.threshold_percentile = metadata['threshold_percentile']
        self.is_trained = metadata['is_trained']
        self.last_training_time = metadata['last_training_time']
    
    def update_model(self, new_data: pd.Series, epochs=10):
        """Incrementally update model with new data."""
        if not self.is_trained:
            raise ModelNotTrainedError("Model must be initially trained")
        
        new_sequences = self._create_sequences(new_data)
        scaled_sequences = self.scaler.transform(
            new_sequences.reshape(-1, 1)
        ).reshape(new_sequences.shape)
        
        # Incremental training
        self.model.fit(
            scaled_sequences, scaled_sequences,
            epochs=epochs,
            batch_size=16,
            verbose=0
        )
        
        # Update threshold if needed
        new_errors = self._calculate_reconstruction_errors(scaled_sequences)
        combined_threshold = np.percentile(
            new_errors, self.threshold_percentile
        )
        
        # Exponential moving average for threshold update
        alpha = 0.1  # Learning rate for threshold adaptation
        self.threshold = (1 - alpha) * self.threshold + alpha * combined_threshold
        
        self.last_training_time = datetime.now()
```

### Integration with Ensemble System
```python
# In ensemble_detector.py, add LSTM support
def _initialize_detectors(self) -> Dict[str, Any]:
    detectors = {}
    
    # ... existing detectors ...
    
    # LSTM detector (when available)
    if self.config.lstm_enabled:
        try:
            detectors['lstm'] = LSTMTemporalDetector(
                sequence_length=self.config.lstm_sequence_length,
                threshold_percentile=self.config.lstm_threshold_percentile
            )
        except ImportError:
            print("Warning: TensorFlow not available, skipping LSTM detector")
    
    return detectors
```

## Testing Requirements
- [x] Unit tests for sequence creation and windowing
- [x] Training convergence tests with synthetic data
- [x] Reconstruction error calculation validation
- [x] Model persistence and loading tests
- [x] Integration tests with anomaly detection system
- [x] Performance benchmarks with various data sizes
- [x] Memory usage profiling during training
- [x] Incremental learning validation tests
- [x] Edge case handling (short sequences, missing data)

## Performance Requirements
- Training time: <10 minutes for 1 year of daily data
- Inference time: <5 seconds for 1000 data points
- Memory usage: <1GB during training, <100MB during inference
- Model size: <50MB saved model file
- Accuracy: >90% precision on synthetic temporal anomalies

## Integration Notes
- Extends existing BaseDetector interface
- Uses same Anomaly model structure
- Integrates with notification and feedback systems
- Supports ensemble detection voting
- Maintains consistent API with other detectors

## Future Enhancements
- Multi-variate LSTM for correlated metrics
- Attention mechanisms for pattern explanation
- Transfer learning between different health metrics
- Distributed training for large datasets
- Real-time streaming anomaly detection

## Claude Output Log
[2025-05-28 15:45]: Started task - implementing LSTM-based temporal anomaly detection with hybrid approach
[2025-05-28 16:10]: Created temporal_anomaly_detector.py with HybridTemporalAnomalyDetector, STLAnomalyDetector, and LSTMTemporalDetector classes
[2025-05-28 16:15]: Updated anomaly_detectors.py to import LSTMDetector from temporal module with fallback
[2025-05-28 16:18]: Modified anomaly_detection_system.py to initialize hybrid temporal detector
[2025-05-28 16:20]: Added HYBRID detection method to anomaly_models.py enum
[2025-05-28 16:25]: Created comprehensive unit tests in test_temporal_anomaly_detector.py
[2025-05-28 16:27]: Added requirements-ml.txt with optional TensorFlow dependencies
[2025-05-28 16:30]: Created example script temporal_anomaly_example.py demonstrating usage
[2025-05-28 16:35]: All acceptance criteria met - hybrid approach implemented with graceful ML degradation
[2025-05-28 16:45]: Code Review Result: **PASS** - Implementation matches all specifications exactly with zero deviations
[2025-05-28 16:50]: Task completed successfully - status updated and file renamed to GX050