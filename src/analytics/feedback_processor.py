"""
Feedback processing and adaptive threshold management.
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from .anomaly_models import (
    Anomaly, UserFeedback, PersonalThreshold, DetectionMethod, 
    Severity, DetectionConfig
)


class FeedbackDatabase:
    """Database handler for user feedback storage."""
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize feedback database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anomaly_id TEXT,
                    metric TEXT,
                    method TEXT,
                    feedback_type TEXT,
                    timestamp TEXT,
                    user_comment TEXT,
                    suggested_threshold REAL,
                    anomaly_score REAL,
                    anomaly_value TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Personal thresholds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_thresholds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric TEXT,
                    method TEXT,
                    multiplier REAL DEFAULT 1.0,
                    false_positives INTEGER DEFAULT 0,
                    true_positives INTEGER DEFAULT 0,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric, method)
                )
            """)
            
            # Feedback statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_feedback INTEGER,
                    false_positives INTEGER,
                    true_positives INTEGER,
                    accuracy REAL,
                    avg_adjustment REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_feedback(self, feedback: UserFeedback, anomaly: Anomaly):
        """Add user feedback to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_feedback 
                (anomaly_id, metric, method, feedback_type, timestamp, 
                 user_comment, suggested_threshold, anomaly_score, anomaly_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.anomaly_id,
                anomaly.metric,
                anomaly.method.value,
                feedback.feedback_type,
                feedback.timestamp.isoformat(),
                feedback.user_comment,
                feedback.suggested_threshold,
                anomaly.score,
                json.dumps(anomaly.value) if isinstance(anomaly.value, dict) else str(anomaly.value)
            ))
            conn.commit()
    
    def get_feedback_history(self, metric: str = None, method: str = None, 
                           days: int = 30) -> List[Dict[str, Any]]:
        """Get feedback history with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM user_feedback 
                WHERE created_at > date('now', '-{} days')
            """.format(days)
            
            params = []
            if metric:
                query += " AND metric = ?"
                params.append(metric)
            if method:
                query += " AND method = ?"
                params.append(method)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_personal_threshold(self, threshold: PersonalThreshold):
        """Update or insert personal threshold."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO personal_thresholds 
                (metric, method, multiplier, false_positives, true_positives, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                threshold.metric,
                threshold.method.value,
                threshold.multiplier,
                threshold.false_positives,
                threshold.true_positives,
                threshold.last_updated.isoformat()
            ))
            conn.commit()
    
    def get_personal_threshold(self, metric: str, method: DetectionMethod) -> Optional[PersonalThreshold]:
        """Get personal threshold for metric/method combination."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM personal_thresholds 
                WHERE metric = ? AND method = ?
            """, (metric, method.value))
            
            row = cursor.fetchone()
            if row:
                return PersonalThreshold(
                    metric=row[1],
                    method=DetectionMethod(row[2]),
                    multiplier=row[3],
                    false_positives=row[4],
                    true_positives=row[5],
                    last_updated=datetime.fromisoformat(row[6])
                )
            return None


class FeedbackProcessor:
    """Processes user feedback and adapts detection thresholds."""
    
    def __init__(self, config: DetectionConfig, db_path: str = "feedback.db"):
        self.config = config
        self.feedback_db = FeedbackDatabase(db_path)
        self.personal_thresholds = {}
        self.feedback_history = []
        self._load_personal_thresholds()
    
    def _load_personal_thresholds(self):
        """Load personal thresholds from database."""
        # This would load from database in real implementation
        pass
    
    def process_feedback(self, anomaly: Anomaly, feedback_type: str, 
                        user_comment: str = None, suggested_threshold: float = None) -> UserFeedback:
        """Process user feedback on an anomaly."""
        # Create feedback record
        feedback = UserFeedback(
            anomaly_id=f"{anomaly.timestamp}_{anomaly.metric}_{anomaly.method.value}",
            feedback_type=feedback_type,
            timestamp=datetime.now(),
            user_comment=user_comment,
            suggested_threshold=suggested_threshold
        )
        
        # Store in database
        self.feedback_db.add_feedback(feedback, anomaly)
        
        # Update personal thresholds
        if feedback_type in ['false_positive', 'true_positive']:
            self._update_personal_threshold(anomaly, feedback_type)
        
        # Learn from feedback if adaptive thresholds are enabled
        if self.config.adaptive_thresholds:
            self._adapt_thresholds(anomaly, feedback)
        
        self.feedback_history.append(feedback)
        return feedback
    
    def _update_personal_threshold(self, anomaly: Anomaly, feedback_type: str):
        """Update personal threshold based on feedback."""
        key = f"{anomaly.metric}_{anomaly.method.value}"
        
        # Get or create personal threshold
        threshold = self.personal_thresholds.get(key)
        if not threshold:
            threshold = PersonalThreshold(
                metric=anomaly.metric,
                method=anomaly.method
            )
            self.personal_thresholds[key] = threshold
        
        # Update based on feedback type
        if feedback_type == 'false_positive':
            threshold.false_positives += 1
            # Increase threshold to reduce false positives
            adjustment = self.config.feedback_learning_rate * (1 + threshold.false_positives / 10)
            threshold.multiplier *= (1 + adjustment)
        elif feedback_type == 'true_positive':
            threshold.true_positives += 1
            # Slightly decrease threshold to catch more similar anomalies
            adjustment = self.config.feedback_learning_rate * 0.5
            threshold.multiplier *= (1 - adjustment)
        
        threshold.last_updated = datetime.now()
        
        # Store in database
        self.feedback_db.update_personal_threshold(threshold)
    
    def _adapt_thresholds(self, anomaly: Anomaly, feedback: UserFeedback):
        """Adapt detection thresholds based on feedback."""
        if feedback.feedback_type == 'false_positive':
            # Make detection less sensitive for this type of anomaly
            self._adjust_detector_sensitivity(anomaly, increase=True)
        elif feedback.feedback_type == 'true_positive':
            # Potentially make detection more sensitive
            self._adjust_detector_sensitivity(anomaly, increase=False)
        elif feedback.suggested_threshold is not None:
            # Use user-suggested threshold
            self._apply_suggested_threshold(anomaly, feedback.suggested_threshold)
    
    def _adjust_detector_sensitivity(self, anomaly: Anomaly, increase: bool):
        """Adjust detector sensitivity based on feedback."""
        adjustment_factor = 1.1 if increase else 0.95
        
        # Adjust method-specific thresholds in config
        if anomaly.method == DetectionMethod.ZSCORE:
            self.config.zscore_threshold *= adjustment_factor
        elif anomaly.method == DetectionMethod.MODIFIED_ZSCORE:
            self.config.modified_zscore_threshold *= adjustment_factor
        elif anomaly.method == DetectionMethod.IQR:
            self.config.iqr_multiplier *= adjustment_factor
        elif anomaly.method == DetectionMethod.ISOLATION_FOREST:
            # Adjust contamination parameter
            new_contamination = self.config.isolation_forest_contamination
            if increase:
                new_contamination *= 0.9  # Less contamination = higher threshold
            else:
                new_contamination *= 1.1  # More contamination = lower threshold
            self.config.isolation_forest_contamination = min(0.5, max(0.001, new_contamination))
    
    def _apply_suggested_threshold(self, anomaly: Anomaly, suggested_threshold: float):
        """Apply user-suggested threshold."""
        # Update the appropriate threshold based on detection method
        if anomaly.method == DetectionMethod.ZSCORE:
            self.config.zscore_threshold = suggested_threshold
        elif anomaly.method == DetectionMethod.MODIFIED_ZSCORE:
            self.config.modified_zscore_threshold = suggested_threshold
        # Add other methods as needed
    
    def filter_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Filter anomalies based on personal thresholds and feedback history."""
        if not self.config.adaptive_thresholds:
            return anomalies
        
        filtered = []
        
        for anomaly in anomalies:
            if self._should_include_anomaly(anomaly):
                filtered.append(anomaly)
        
        return filtered
    
    def _should_include_anomaly(self, anomaly: Anomaly) -> bool:
        """Determine if anomaly should be included based on personal thresholds."""
        key = f"{anomaly.metric}_{anomaly.method.value}"
        threshold = self.personal_thresholds.get(key)
        
        if not threshold:
            return True  # No personal threshold, include by default
        
        # Apply personal threshold multiplier
        adjusted_threshold = anomaly.threshold * threshold.multiplier
        
        # Check if anomaly score exceeds adjusted threshold
        return abs(anomaly.score) > adjusted_threshold
    
    def get_feedback_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback statistics for the specified period."""
        history = self.feedback_db.get_feedback_history(days=days)
        
        if not history:
            return {'no_data': True}
        
        false_positives = len([f for f in history if f['feedback_type'] == 'false_positive'])
        true_positives = len([f for f in history if f['feedback_type'] == 'true_positive'])
        total_feedback = len(history)
        
        accuracy = true_positives / max(total_feedback, 1)
        
        # Method breakdown
        method_stats = defaultdict(lambda: {'fp': 0, 'tp': 0})
        for feedback in history:
            method = feedback['method']
            if feedback['feedback_type'] == 'false_positive':
                method_stats[method]['fp'] += 1
            elif feedback['feedback_type'] == 'true_positive':
                method_stats[method]['tp'] += 1
        
        # Metric breakdown
        metric_stats = defaultdict(lambda: {'fp': 0, 'tp': 0})
        for feedback in history:
            metric = feedback['metric']
            if feedback['feedback_type'] == 'false_positive':
                metric_stats[metric]['fp'] += 1
            elif feedback['feedback_type'] == 'true_positive':
                metric_stats[metric]['tp'] += 1
        
        return {
            'total_feedback': total_feedback,
            'false_positives': false_positives,
            'true_positives': true_positives,
            'accuracy': accuracy,
            'false_positive_rate': false_positives / max(total_feedback, 1),
            'method_breakdown': dict(method_stats),
            'metric_breakdown': dict(metric_stats),
            'personal_thresholds_count': len(self.personal_thresholds),
            'avg_threshold_adjustment': self._calculate_avg_threshold_adjustment()
        }
    
    def _calculate_avg_threshold_adjustment(self) -> float:
        """Calculate average threshold adjustment across all personal thresholds."""
        if not self.personal_thresholds:
            return 1.0
        
        adjustments = [t.multiplier for t in self.personal_thresholds.values()]
        return np.mean(adjustments)
    
    def get_learning_recommendations(self) -> List[str]:
        """Get recommendations for improving detection accuracy."""
        stats = self.get_feedback_statistics()
        recommendations = []
        
        if stats.get('no_data'):
            recommendations.append("Start providing feedback on anomalies to improve accuracy")
            return recommendations
        
        fp_rate = stats['false_positive_rate']
        if fp_rate > 0.3:
            recommendations.append("Consider increasing detection thresholds to reduce false positives")
        elif fp_rate < 0.05:
            recommendations.append("Detection seems well-tuned. Consider enabling more sensitive methods")
        
        # Method-specific recommendations
        method_breakdown = stats['method_breakdown']
        for method, counts in method_breakdown.items():
            total = counts['fp'] + counts['tp']
            if total > 0:
                method_fp_rate = counts['fp'] / total
                if method_fp_rate > 0.5:
                    recommendations.append(f"Consider tuning {method} detector - high false positive rate")
        
        # Data quantity recommendations
        if stats['total_feedback'] < 10:
            recommendations.append("More feedback needed for reliable threshold adaptation")
        
        return recommendations
    
    def export_feedback_data(self, filepath: str, days: int = 90):
        """Export feedback data for analysis."""
        history = self.feedback_db.get_feedback_history(days=days)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'period_days': days,
            'feedback_history': history,
            'personal_thresholds': {
                key: {
                    'metric': threshold.metric,
                    'method': threshold.method.value,
                    'multiplier': threshold.multiplier,
                    'false_positives': threshold.false_positives,
                    'true_positives': threshold.true_positives,
                    'accuracy': threshold.accuracy
                }
                for key, threshold in self.personal_thresholds.items()
            },
            'statistics': self.get_feedback_statistics(days)
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def reset_learning(self, confirm: bool = False):
        """Reset all learning data and personal thresholds."""
        if not confirm:
            raise ValueError("Must confirm reset by passing confirm=True")
        
        self.personal_thresholds.clear()
        self.feedback_history.clear()
        
        # Reset database tables
        with sqlite3.connect(self.feedback_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_feedback")
            cursor.execute("DELETE FROM personal_thresholds")
            cursor.execute("DELETE FROM feedback_stats")
            conn.commit()