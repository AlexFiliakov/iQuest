"""
Anomaly detection algorithms implementation.
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from .anomaly_models import (
    Anomaly, DetectionMethod, Severity, DetectionResult,
    AnomalyDetectionError, InsufficientDataError
)


class BaseDetector(ABC):
    """Base class for anomaly detectors."""
    
    def __init__(self, name: str, method: DetectionMethod):
        self.name = name
        self.method = method
        self.is_trained = False
        self.last_training_time = None
        
    @abstractmethod
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Detect anomalies in the given data."""
        pass
    
    def detect_batch(self, data: pd.DataFrame) -> List[Anomaly]:
        """Detect anomalies in batch mode."""
        anomalies = []
        for column in data.columns:
            if pd.api.types.is_numeric_dtype(data[column]):
                column_anomalies = self.detect(data[column])
                anomalies.extend(column_anomalies)
        return anomalies
    
    def _calculate_severity(self, score: float, threshold: float) -> Severity:
        """Calculate severity based on score and threshold."""
        abs_score = abs(score)
        
        if abs_score > threshold * 2:
            return Severity.CRITICAL
        elif abs_score > threshold * 1.5:
            return Severity.HIGH
        elif abs_score > threshold:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _validate_data(self, data: Union[pd.Series, np.ndarray]) -> pd.Series:
        """Validate and convert input data to pandas Series."""
        # Convert numpy array to pandas Series if needed
        if isinstance(data, np.ndarray):
            data = pd.Series(data)
        
        if data.empty:
            raise InsufficientDataError("Input data is empty")
        
        if len(data.dropna()) < 3:
            raise InsufficientDataError("Insufficient non-null data points")
        
        return data


class ZScoreDetector(BaseDetector):
    """Z-score based anomaly detection."""
    
    def __init__(self, threshold: float = 3.0):
        super().__init__("Z-Score Detector", DetectionMethod.ZSCORE)
        self.threshold = threshold
    
    def detect(self, data: Union[pd.Series, np.ndarray], metric: str = None) -> Union[List[Anomaly], 'DetectionResult']:
        """Detect anomalies using z-score."""
        import time
        start_time = time.time()
        
        data = self._validate_data(data)
        
        # Calculate z-scores
        mean = data.mean()
        std = data.std()
        
        if std == 0:
            anomalies = []  # No variation in data
        else:
            z_scores = (data - mean) / std
            
            # Find anomalies
            anomalies = []
            anomaly_mask = np.abs(z_scores) > self.threshold
            
            for idx in data[anomaly_mask].index:
                anomalies.append(Anomaly(
                    timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                    metric=metric or data.name or "unknown",
                    value=data[idx],
                    score=float(z_scores[idx]),
                    method=self.method,
                    severity=self._calculate_severity(z_scores[idx], self.threshold),
                    threshold=self.threshold,
                    context={
                        'mean': mean,
                        'std': std,
                        'z_score': float(z_scores[idx])
                    }
                ))
        
        # If metric is provided, return DetectionResult
        if metric is not None:
            return DetectionResult(
                anomalies=anomalies,
                total_points=len(data),
                detection_time=time.time() - start_time,
                method=self.method,
                parameters={'threshold': self.threshold}
            )
        
        return anomalies


class ModifiedZScoreDetector(BaseDetector):
    """Modified Z-score based anomaly detection using median absolute deviation."""
    
    def __init__(self, threshold: float = 3.5):
        super().__init__("Modified Z-Score Detector", DetectionMethod.MODIFIED_ZSCORE)
        self.threshold = threshold
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Detect anomalies using modified z-score."""
        self._validate_data(data)
        
        # Calculate median absolute deviation
        median = data.median()
        mad = np.median(np.abs(data - median))
        
        if mad == 0:
            return []  # No variation in data
        
        # Modified z-scores
        modified_z_scores = 0.6745 * (data - median) / mad
        
        # Find anomalies
        anomalies = []
        anomaly_mask = np.abs(modified_z_scores) > self.threshold
        
        for idx in data[anomaly_mask].index:
            anomalies.append(Anomaly(
                timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                metric=data.name or "unknown",
                value=data[idx],
                score=float(modified_z_scores[idx]),
                method=self.method,
                severity=self._calculate_severity(modified_z_scores[idx], self.threshold),
                threshold=self.threshold,
                context={
                    'median': median,
                    'mad': mad,
                    'modified_z_score': float(modified_z_scores[idx])
                }
            ))
        
        return anomalies


class IQRDetector(BaseDetector):
    """Interquartile Range based anomaly detection."""
    
    def __init__(self, multiplier: float = 1.5):
        super().__init__("IQR Detector", DetectionMethod.IQR)
        self.multiplier = multiplier
    
    def detect(self, data: Union[pd.Series, np.ndarray], metric: str = None) -> Union[List[Anomaly], 'DetectionResult']:
        """Detect anomalies using IQR method."""
        import time
        start_time = time.time()
        
        data = self._validate_data(data)
        
        # Calculate quartiles
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR == 0:
            return []  # No variation in data
        
        # Calculate bounds
        lower_bound = Q1 - self.multiplier * IQR
        upper_bound = Q3 + self.multiplier * IQR
        
        # Find anomalies
        anomalies = []
        anomaly_mask = (data < lower_bound) | (data > upper_bound)
        
        for idx in data[anomaly_mask].index:
            value = data[idx]
            # Calculate score as distance from nearest bound
            if value < lower_bound:
                score = (lower_bound - value) / IQR
            else:
                score = (value - upper_bound) / IQR
            
            anomalies.append(Anomaly(
                timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                metric=metric or data.name or "unknown",
                value=value,
                score=float(score),
                method=self.method,
                severity=self._calculate_severity(score, 1.0),
                threshold=self.multiplier,
                context={
                    'Q1': Q1,
                    'Q3': Q3,
                    'IQR': IQR,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
            ))
        
        # If metric is provided, return DetectionResult
        if metric is not None:
            return DetectionResult(
                anomalies=anomalies,
                total_points=len(data),
                detection_time=time.time() - start_time,
                method=self.method,
                parameters={'multiplier': self.multiplier}
            )
        
        return anomalies


class IsolationForestDetector(BaseDetector):
    """Isolation Forest based anomaly detection for multivariate data."""
    
    def __init__(self, contamination: float = 0.01, n_estimators: int = 100):
        super().__init__("Isolation Forest Detector", DetectionMethod.ISOLATION_FOREST)
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """For single series, convert to DataFrame and detect."""
        df = pd.DataFrame({data.name or 'value': data})
        return self.detect_multivariate(df)
    
    def detect_multivariate(self, data: pd.DataFrame) -> List[Anomaly]:
        """Detect multivariate anomalies using Isolation Forest."""
        if data.empty:
            raise InsufficientDataError("Input data is empty")
        
        # Prepare features
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            return []
        
        features = data[numeric_columns].dropna()
        if len(features) < 5:
            raise InsufficientDataError("Insufficient data for Isolation Forest")
        
        self.feature_names = list(features.columns)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Fit and predict
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=self.n_estimators
        )
        
        predictions = self.model.fit_predict(scaled_features)
        scores = self.model.score_samples(scaled_features)
        
        # Extract anomalies
        anomalies = []
        anomaly_indices = np.where(predictions == -1)[0]
        
        for idx in anomaly_indices:
            original_idx = features.index[idx]
            
            # Calculate feature contributions
            feature_contributions = self._explain_isolation(features.iloc[idx])
            
            anomalies.append(Anomaly(
                timestamp=original_idx if isinstance(original_idx, datetime) else datetime.now(),
                metric='multivariate',
                value=features.iloc[idx].to_dict(),
                score=float(scores[idx]),
                method=self.method,
                severity=self._score_to_severity(scores[idx]),
                threshold=self.contamination,
                contributing_features=feature_contributions,
                context={
                    'n_features': len(self.feature_names),
                    'contamination': self.contamination
                }
            ))
        
        self.is_trained = True
        self.last_training_time = datetime.now()
        
        return anomalies
    
    def _explain_isolation(self, sample: pd.Series) -> Dict[str, float]:
        """Explain which features contributed to isolation."""
        contributions = {}
        
        # Calculate simple feature deviations
        for feature in sample.index:
            if feature in self.feature_names:
                # Get feature statistics from training data
                feature_mean = self.scaler.mean_[self.feature_names.index(feature)]
                feature_std = self.scaler.scale_[self.feature_names.index(feature)]
                
                # Calculate normalized deviation
                deviation = abs(sample[feature] - feature_mean) / feature_std
                contributions[feature] = float(deviation)
        
        return contributions
    
    def _score_to_severity(self, score: float) -> Severity:
        """Convert isolation score to severity."""
        # Isolation Forest scores are typically between -1 and 1
        # More negative scores indicate stronger anomalies
        abs_score = abs(score)
        
        if abs_score > 0.8:
            return Severity.CRITICAL
        elif abs_score > 0.6:
            return Severity.HIGH
        elif abs_score > 0.4:
            return Severity.MEDIUM
        else:
            return Severity.LOW


class LocalOutlierFactorDetector(BaseDetector):
    """Local Outlier Factor based anomaly detection."""
    
    def __init__(self, n_neighbors: int = 20, contamination: float = 0.01):
        super().__init__("Local Outlier Factor Detector", DetectionMethod.LOF)
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """For single series, convert to DataFrame and detect."""
        df = pd.DataFrame({data.name or 'value': data})
        return self.detect_multivariate(df)
    
    def detect_multivariate(self, data: pd.DataFrame) -> List[Anomaly]:
        """Detect anomalies using Local Outlier Factor."""
        if data.empty:
            raise InsufficientDataError("Input data is empty")
        
        # Prepare features
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            return []
        
        features = data[numeric_columns].dropna()
        if len(features) < max(5, self.n_neighbors + 1):
            raise InsufficientDataError(f"Insufficient data for LOF (need at least {self.n_neighbors + 1} points)")
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Fit and predict
        self.model = LocalOutlierFactor(
            n_neighbors=min(self.n_neighbors, len(features) - 1),
            contamination=self.contamination
        )
        
        predictions = self.model.fit_predict(scaled_features)
        scores = self.model.negative_outlier_factor_
        
        # Extract anomalies
        anomalies = []
        anomaly_indices = np.where(predictions == -1)[0]
        
        for idx in anomaly_indices:
            original_idx = features.index[idx]
            
            anomalies.append(Anomaly(
                timestamp=original_idx if isinstance(original_idx, datetime) else datetime.now(),
                metric='local_density',
                value=features.iloc[idx].to_dict(),
                score=float(abs(scores[idx])),
                method=self.method,
                severity=self._lof_score_to_severity(scores[idx]),
                threshold=self.contamination,
                context={
                    'n_neighbors': self.n_neighbors,
                    'lof_score': float(scores[idx]),
                    'local_density_factor': float(abs(scores[idx]))
                }
            ))
        
        self.is_trained = True
        self.last_training_time = datetime.now()
        
        return anomalies
    
    def _lof_score_to_severity(self, score: float) -> Severity:
        """Convert LOF score to severity."""
        # LOF scores are negative, with more negative indicating stronger outliers
        abs_score = abs(score)
        
        if abs_score > 2.0:
            return Severity.CRITICAL
        elif abs_score > 1.5:
            return Severity.HIGH
        elif abs_score > 1.2:
            return Severity.MEDIUM
        else:
            return Severity.LOW


class SimpleEnsembleDetector(BaseDetector):
    """Simple ensemble detector that combines results from multiple detectors."""
    
    def __init__(self, detectors: Union[List[BaseDetector], Dict[str, BaseDetector]], 
                 min_votes: int = None, config: Optional['DetectionConfig'] = None):
        super().__init__("Simple Ensemble Detector", DetectionMethod.ENSEMBLE)
        
        # Handle both list and dict formats
        if isinstance(detectors, dict):
            self.detectors = list(detectors.values())
        else:
            self.detectors = detectors
        
        # Handle config or min_votes
        if config is not None:
            self.config = config
            self.min_votes = getattr(config, 'ensemble_min_votes', 1)
        else:
            self.config = None
            self.min_votes = min_votes if min_votes is not None else 1
    
    def detect(self, data: Union[pd.Series, np.ndarray], metric: str = None) -> Union[List[Anomaly], 'DetectionResult']:
        """Detect anomalies using ensemble of detectors."""
        import time
        from collections import defaultdict
        
        start_time = time.time()
        
        # Collect anomalies from all detectors
        timestamp_votes = defaultdict(list)
        all_anomalies = []
        
        for detector in self.detectors:
            try:
                # Get anomalies (not DetectionResult) from each detector
                detector_anomalies = detector.detect(data)
                if isinstance(detector_anomalies, DetectionResult):
                    detector_anomalies = detector_anomalies.anomalies
                
                for anomaly in detector_anomalies:
                    timestamp_votes[anomaly.timestamp].append(anomaly)
                    all_anomalies.append(anomaly)
            except Exception as e:
                # Skip failed detectors
                continue
        
        # Filter based on minimum votes
        ensemble_anomalies = []
        for timestamp, anomaly_list in timestamp_votes.items():
            if len(anomaly_list) >= self.min_votes:
                # Use the anomaly with highest score
                best_anomaly = max(anomaly_list, key=lambda a: abs(a.score))
                # Update method to ensemble
                best_anomaly.method = DetectionMethod.ENSEMBLE
                # Add voting info to context
                best_anomaly.context['votes'] = len(anomaly_list)
                best_anomaly.context['detectors'] = [a.method.value for a in anomaly_list]
                ensemble_anomalies.append(best_anomaly)
        
        # If metric is provided, return DetectionResult
        if metric is not None:
            return DetectionResult(
                anomalies=ensemble_anomalies,
                total_points=len(data) if hasattr(data, '__len__') else 0,
                detection_time=time.time() - start_time,
                method=self.method,
                parameters={
                    'min_votes': self.min_votes,
                    'n_detectors': len(self.detectors)
                }
            )
        
        return ensemble_anomalies


# Alias for backward compatibility in tests
EnsembleDetector = SimpleEnsembleDetector


# Import LSTM detector from temporal module
try:
    from .temporal_anomaly_detector import LSTMTemporalDetector as LSTMDetector
except ImportError:
    # Fallback if TensorFlow not available
    class LSTMDetector(BaseDetector):
        """LSTM-based temporal anomaly detection (requires TensorFlow/PyTorch)."""
        
        def __init__(self, sequence_length: int = 24, threshold_percentile: float = 95):
            super().__init__("LSTM Detector", DetectionMethod.LSTM)
            self.sequence_length = sequence_length
            self.threshold_percentile = threshold_percentile
            self.model = None
            self.scaler = StandardScaler()
        
        def detect(self, data: pd.Series) -> List[Anomaly]:
            """Detect temporal anomalies using LSTM."""
            raise NotImplementedError(
                "LSTM detector requires TensorFlow or PyTorch. "
                "Please install with: pip install tensorflow>=2.0"
            )