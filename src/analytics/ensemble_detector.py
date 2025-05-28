"""
Ensemble anomaly detection that combines multiple detectors.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime

from .anomaly_models import (
    Anomaly, DetectionMethod, Severity, DetectionResult, DetectionConfig
)
from .anomaly_detectors import BaseDetector


class EnsembleDetector:
    """Combines multiple anomaly detectors for improved accuracy."""
    
    def __init__(self, detectors: Dict[str, BaseDetector], config: DetectionConfig):
        self.detectors = detectors
        self.config = config
        self.detection_history = []
    
    def detect(self, data: pd.Series) -> List[Anomaly]:
        """Run ensemble detection on single series."""
        if data.empty:
            return []
        
        start_time = datetime.now()
        all_anomalies = []
        detector_results = {}
        
        # Run each enabled detector
        for name, detector in self.detectors.items():
            if detector.method in self.config.enabled_methods:
                try:
                    anomalies = detector.detect(data)
                    detector_results[name] = anomalies
                    all_anomalies.extend(anomalies)
                except Exception as e:
                    print(f"Detector {name} failed: {e}")
                    detector_results[name] = []
        
        # Combine results using ensemble logic
        combined_anomalies = self._combine_anomalies(all_anomalies, detector_results)
        
        # Record detection history
        detection_time = (datetime.now() - start_time).total_seconds()
        result = DetectionResult(
            anomalies=combined_anomalies,
            total_points=len(data),
            detection_time=detection_time,
            method=DetectionMethod.ENSEMBLE,
            parameters={
                'detectors_used': list(detector_results.keys()),
                'min_votes': self.config.ensemble_min_votes,
                'weight_by_confidence': self.config.ensemble_weight_by_confidence
            }
        )
        self.detection_history.append(result)
        
        return combined_anomalies
    
    def detect_multivariate(self, data: pd.DataFrame) -> List[Anomaly]:
        """Run ensemble detection on multivariate data."""
        if data.empty:
            return []
        
        start_time = datetime.now()
        all_anomalies = []
        detector_results = {}
        
        # Run multivariate detectors
        multivariate_detectors = ['isolation_forest', 'lof']
        for name, detector in self.detectors.items():
            if (detector.method in self.config.enabled_methods and 
                name in multivariate_detectors):
                try:
                    if hasattr(detector, 'detect_multivariate'):
                        anomalies = detector.detect_multivariate(data)
                    else:
                        # Run on each column separately
                        anomalies = detector.detect_batch(data)
                    
                    detector_results[name] = anomalies
                    all_anomalies.extend(anomalies)
                except Exception as e:
                    print(f"Multivariate detector {name} failed: {e}")
                    detector_results[name] = []
        
        # Run univariate detectors on each column
        univariate_detectors = ['zscore', 'modified_zscore', 'iqr']
        for column in data.select_dtypes(include=[np.number]).columns:
            series = data[column].dropna()
            if len(series) > 3:
                for name, detector in self.detectors.items():
                    if (detector.method in self.config.enabled_methods and 
                        name in univariate_detectors):
                        try:
                            anomalies = detector.detect(series)
                            if name not in detector_results:
                                detector_results[name] = []
                            detector_results[name].extend(anomalies)
                            all_anomalies.extend(anomalies)
                        except Exception as e:
                            print(f"Univariate detector {name} failed on {column}: {e}")
        
        # Combine results
        combined_anomalies = self._combine_anomalies(all_anomalies, detector_results)
        
        # Record detection history
        detection_time = (datetime.now() - start_time).total_seconds()
        result = DetectionResult(
            anomalies=combined_anomalies,
            total_points=len(data),
            detection_time=detection_time,
            method=DetectionMethod.ENSEMBLE,
            parameters={
                'detectors_used': list(detector_results.keys()),
                'columns_processed': list(data.columns)
            }
        )
        self.detection_history.append(result)
        
        return combined_anomalies
    
    def _combine_anomalies(self, all_anomalies: List[Anomaly], 
                          detector_results: Dict[str, List[Anomaly]]) -> List[Anomaly]:
        """Combine anomalies from multiple detectors."""
        if not all_anomalies:
            return []
        
        # Group anomalies by timestamp and metric
        anomaly_groups = defaultdict(list)
        for anomaly in all_anomalies:
            key = (anomaly.timestamp, anomaly.metric)
            anomaly_groups[key].append(anomaly)
        
        combined_anomalies = []
        
        for (timestamp, metric), group in anomaly_groups.items():
            if len(group) >= self.config.ensemble_min_votes:
                # Create ensemble anomaly
                ensemble_anomaly = self._create_ensemble_anomaly(group)
                combined_anomalies.append(ensemble_anomaly)
        
        # Sort by severity and score
        combined_anomalies.sort(
            key=lambda a: (a.severity.value, abs(a.score)), 
            reverse=True
        )
        
        return combined_anomalies
    
    def _create_ensemble_anomaly(self, anomalies: List[Anomaly]) -> Anomaly:
        """Create a single anomaly from multiple detections."""
        # Use the first anomaly as base
        base = anomalies[0]
        
        # Calculate ensemble score
        if self.config.ensemble_weight_by_confidence:
            # Weight by confidence
            weighted_scores = [a.score * a.confidence for a in anomalies]
            total_confidence = sum(a.confidence for a in anomalies)
            ensemble_score = sum(weighted_scores) / max(total_confidence, 1)
        else:
            # Simple average
            ensemble_score = np.mean([a.score for a in anomalies])
        
        # Determine ensemble severity (take the maximum)
        severities = [a.severity for a in anomalies]
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        ensemble_severity = max(severities, key=lambda s: severity_order.index(s))
        
        # Combine methods and contexts
        methods = [a.method.value for a in anomalies]
        method_counts = Counter(methods)
        
        # Combine contexts
        ensemble_context = {
            'contributing_methods': list(method_counts.keys()),
            'method_votes': dict(method_counts),
            'individual_scores': [a.score for a in anomalies],
            'agreement_level': len(anomalies) / len(self.detectors)
        }
        
        # Add individual contexts
        for i, anomaly in enumerate(anomalies):
            ensemble_context[f'{anomaly.method.value}_context'] = anomaly.context
        
        return Anomaly(
            timestamp=base.timestamp,
            metric=base.metric,
            value=base.value,
            score=ensemble_score,
            method=DetectionMethod.ENSEMBLE,
            severity=ensemble_severity,
            threshold=base.threshold,
            context=ensemble_context,
            confidence=min(1.0, len(anomalies) / len(self.detectors))
        )
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of recent detection performance."""
        if not self.detection_history:
            return {}
        
        recent_results = self.detection_history[-10:]  # Last 10 runs
        
        return {
            'total_runs': len(self.detection_history),
            'recent_runs': len(recent_results),
            'avg_detection_time': np.mean([r.detection_time for r in recent_results]),
            'avg_anomaly_rate': np.mean([r.anomaly_rate for r in recent_results]),
            'total_anomalies': sum(len(r.anomalies) for r in recent_results),
            'detector_usage': self._get_detector_usage_stats(),
            'performance_trends': self._get_performance_trends()
        }
    
    def _get_detector_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on detector usage and performance."""
        stats = defaultdict(lambda: {'runs': 0, 'anomalies': 0, 'avg_time': 0})
        
        for result in self.detection_history:
            detectors_used = result.parameters.get('detectors_used', [])
            for detector in detectors_used:
                stats[detector]['runs'] += 1
                stats[detector]['anomalies'] += len(result.anomalies)
        
        return dict(stats)
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(self.detection_history) < 5:
            return {'insufficient_data': True}
        
        recent_times = [r.detection_time for r in self.detection_history[-10:]]
        older_times = [r.detection_time for r in self.detection_history[-20:-10]]
        
        if older_times:
            time_trend = (np.mean(recent_times) - np.mean(older_times)) / np.mean(older_times)
        else:
            time_trend = 0
        
        recent_rates = [r.anomaly_rate for r in self.detection_history[-10:]]
        older_rates = [r.anomaly_rate for r in self.detection_history[-20:-10]]
        
        if older_rates:
            rate_trend = (np.mean(recent_rates) - np.mean(older_rates)) / max(np.mean(older_rates), 0.001)
        else:
            rate_trend = 0
        
        return {
            'detection_time_trend': time_trend,  # Positive means getting slower
            'anomaly_rate_trend': rate_trend,    # Positive means more anomalies
            'consistency': 1 - (np.std(recent_times) / max(np.mean(recent_times), 0.001))
        }