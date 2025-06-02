"""
Background worker thread for Activity Timeline analytics calculations.

This module provides asynchronous processing of heavy ML operations
(clustering, anomaly detection, correlations) to prevent UI freezing
and enable progressive updates.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal, QMutex

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN

from ..utils.logging_config import get_logger
from ..analytics.cache_manager import AnalyticsCacheManager

logger = get_logger(__name__)


class TimelineAnalyticsWorker(QThread):
    """Background worker for timeline analytics calculations."""
    
    # Signals for progressive updates
    progress_updated = pyqtSignal(int, str)  # percentage, message
    insights_ready = pyqtSignal(str, object)  # insight_type, data
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the analytics worker."""
        super().__init__()
        self._is_cancelled = False
        self._mutex = QMutex()
        self.scaler = StandardScaler()
        self.cache_manager = AnalyticsCacheManager()
        
        # Data to process
        self.grouped_data = None
        self.selected_metrics = []
        self.date = None
        
        # Results
        self.active_periods = []
        self.rest_periods = []
        self.clusters = None
        self.anomalies = None
        self.correlations = None
        self.lagged_correlations = {}
        
    def set_data(self, grouped_data: pd.DataFrame, selected_metrics: List[str], date: str):
        """Set the data to be processed.
        
        Args:
            grouped_data: Aggregated timeline data
            selected_metrics: List of metric names to analyze
            date: Date string for cache key generation
        """
        self.grouped_data = grouped_data
        self.selected_metrics = selected_metrics
        self.date = date
        
    def cancel(self):
        """Cancel the current processing."""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()
        
    def is_cancelled(self) -> bool:
        """Check if processing has been cancelled."""
        self._mutex.lock()
        result = self._is_cancelled
        self._mutex.unlock()
        return result
        
    def run(self):
        """Execute analytics calculations in background."""
        try:
            # Reset cancellation flag
            self._mutex.lock()
            self._is_cancelled = False
            self._mutex.unlock()
            
            if self.grouped_data is None or self.grouped_data.empty:
                self.error_occurred.emit("No data to process")
                return
                
            # Check cache first
            cache_key = self._generate_cache_key()
            cached_results = self.cache_manager.get(
                cache_key,
                lambda: None,  # No compute function needed for simple lookup
                cache_tiers=['l1', 'l2'],  # Check memory and SQLite caches
                ttl=3600
            )
            if cached_results:
                logger.info("Using cached analytics results")
                self._emit_cached_results(cached_results)
                return
                
            # Step 1: Pattern Detection (20%)
            if not self.is_cancelled():
                self.progress_updated.emit(10, "Detecting activity patterns...")
                self._detect_activity_patterns()
                self.progress_updated.emit(20, "Activity patterns detected")
                self.insights_ready.emit("patterns", {
                    "active_periods": self.active_periods,
                    "rest_periods": self.rest_periods
                })
                
            # Step 2: Clustering (50%)
            if not self.is_cancelled():
                self.progress_updated.emit(30, "Performing clustering analysis...")
                self._perform_clustering()
                self.progress_updated.emit(50, "Clustering complete")
                self.insights_ready.emit("clustering", {
                    "clusters": self.clusters,
                    "anomalies": self.anomalies
                })
                
            # Step 3: Correlations (80%)
            if not self.is_cancelled():
                self.progress_updated.emit(60, "Calculating correlations...")
                self._calculate_correlations()
                self.progress_updated.emit(80, "Correlations calculated")
                self.insights_ready.emit("correlations", {
                    "correlations": self.correlations,
                    "lagged_correlations": self.lagged_correlations
                })
                
            # Step 4: Cache results (100%)
            if not self.is_cancelled():
                self.progress_updated.emit(90, "Caching results...")
                self._cache_results(cache_key)
                self.progress_updated.emit(100, "Analysis complete")
                
        except Exception as e:
            logger.error(f"Analytics processing error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            
    def _generate_cache_key(self) -> str:
        """Generate cache key for current analysis."""
        metrics_hash = hash(tuple(sorted(self.selected_metrics)))
        return f"timeline_analytics_{self.date}_{metrics_hash}_{len(self.grouped_data)}"
        
    def _emit_cached_results(self, cached_results: Dict[str, Any]):
        """Emit all cached results immediately."""
        self.progress_updated.emit(50, "Loading cached results...")
        
        # Emit patterns
        if "patterns" in cached_results:
            self.active_periods = cached_results["patterns"]["active_periods"]
            self.rest_periods = cached_results["patterns"]["rest_periods"]
            self.insights_ready.emit("patterns", cached_results["patterns"])
            
        # Emit clustering
        if "clustering" in cached_results:
            self.clusters = cached_results["clustering"]["clusters"]
            self.anomalies = cached_results["clustering"]["anomalies"]
            self.insights_ready.emit("clustering", cached_results["clustering"])
            
        # Emit correlations
        if "correlations" in cached_results:
            self.correlations = cached_results["correlations"]["correlations"]
            self.lagged_correlations = cached_results["correlations"]["lagged_correlations"]
            self.insights_ready.emit("correlations", cached_results["correlations"])
            
        self.progress_updated.emit(100, "Cached results loaded")
        
    def _detect_activity_patterns(self):
        """Detect active vs rest periods using statistical methods."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Calculate activity scores using vectorized operations
        activity_scores = pd.Series(0, index=self.grouped_data.index, dtype='float64')
        
        # Sum up mean values for each metric
        for metric in self.selected_metrics:
            if (metric, 'mean') in self.grouped_data.columns:
                metric_values = self.grouped_data[(metric, 'mean')].fillna(0)
                activity_scores = activity_scores + metric_values
                
        # Determine thresholds
        scores_array = np.array(activity_scores)
        if len(scores_array) > 0:
            threshold = np.percentile(scores_array, 25)
            
            # Classify periods using boolean indexing
            active_mask = activity_scores > threshold
            
            # Extract periods
            active_indices = self.grouped_data.index[active_mask]
            active_scores = activity_scores[active_mask]
            self.active_periods = list(zip(active_indices, active_scores))
            
            rest_indices = self.grouped_data.index[~active_mask]
            rest_scores = activity_scores[~active_mask]
            self.rest_periods = list(zip(rest_indices, rest_scores))
            
    def _perform_clustering(self):
        """Perform ML clustering on activity patterns."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Prepare features for clustering
        features = []
        for idx, row in self.grouped_data.iterrows():
            feature_vec = []
            for metric in self.selected_metrics:
                if (metric, 'mean') in row.index:
                    value = row[(metric, 'mean')]
                    feature_vec.append(value if pd.notna(value) else 0)
                    
            # Add temporal features
            hour = idx.hour
            feature_vec.extend([
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24)
            ])
            features.append(feature_vec)
            
        if not features:
            return
            
        # Scale features
        X = np.array(features)
        try:
            X_scaled = self.scaler.fit_transform(X)
            
            # K-means clustering
            n_clusters = min(4, len(X))  # Adaptive cluster count
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.clusters = kmeans.fit_predict(X_scaled)
            
            # DBSCAN for anomaly detection
            dbscan = DBSCAN(eps=0.5, min_samples=3)
            anomaly_labels = dbscan.fit_predict(X_scaled)
            self.anomalies = anomaly_labels == -1
            
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            self.clusters = None
            self.anomalies = None
            
    def _calculate_correlations(self):
        """Calculate correlations between metrics."""
        if self.grouped_data is None or self.grouped_data.empty:
            return
            
        # Extract metric values
        metric_data = {}
        for metric in self.selected_metrics:
            if (metric, 'mean') in self.grouped_data.columns:
                metric_data[metric] = self.grouped_data[(metric, 'mean')].fillna(0)
                
        if len(metric_data) < 2:
            self.correlations = None
            return
            
        # Convert to DataFrame and calculate correlations
        metrics_df = pd.DataFrame(metric_data)
        self.correlations = metrics_df.corr()
        
        # Calculate time-lagged correlations
        self.lagged_correlations = {}
        for lag in [1, 2, 3]:  # Check correlations with 1-3 time period lags
            lagged_corr = {}
            for m1 in self.selected_metrics:
                for m2 in self.selected_metrics:
                    if m1 != m2 and m1 in metrics_df and m2 in metrics_df:
                        # Calculate correlation with lag
                        corr = metrics_df[m1].corr(metrics_df[m2].shift(lag))
                        if not np.isnan(corr):
                            lagged_corr[f"{m1}_vs_{m2}_lag{lag}"] = corr
            self.lagged_correlations[lag] = lagged_corr
            
    def _cache_results(self, cache_key: str):
        """Cache the analytics results."""
        results = {
            "patterns": {
                "active_periods": self.active_periods,
                "rest_periods": self.rest_periods
            },
            "clustering": {
                "clusters": self.clusters.tolist() if self.clusters is not None else None,
                "anomalies": self.anomalies.tolist() if self.anomalies is not None else None
            },
            "correlations": {
                "correlations": self.correlations.to_dict() if self.correlations is not None else None,
                "lagged_correlations": self.lagged_correlations
            }
        }
        
        # Cache for 1 hour
        self.cache_manager.set(cache_key, results, ttl=3600)