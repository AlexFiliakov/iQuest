"""
Data models for anomaly detection system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class Severity(Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionMethod(Enum):
    """Anomaly detection methods."""
    ZSCORE = "zscore"
    MODIFIED_ZSCORE = "modified_zscore"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    LOF = "lof"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"
    HYBRID = "hybrid"  # Statistical + ML hybrid approach


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    timestamp: datetime
    metric: str
    value: Any
    score: float
    method: DetectionMethod
    severity: Severity
    threshold: float = 0.0
    explanation: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    contributing_features: Optional[Dict[str, float]] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        """Convert string enums to proper enums if needed."""
        if isinstance(self.method, str):
            self.method = DetectionMethod(self.method)
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)


@dataclass
class Action:
    """Represents an action that can be taken on an anomaly."""
    label: str
    callback: Callable[[], None]
    icon: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Notification:
    """Represents a user notification for an anomaly."""
    title: str
    message: str
    explanation: str
    severity: Severity
    actions: List[Action] = field(default_factory=list)
    dismissible: bool = True
    groupable: bool = True
    timestamp: datetime = field(default_factory=datetime.now)
    anomaly: Optional[Anomaly] = None


@dataclass
class DetectionResult:
    """Results from anomaly detection."""
    anomalies: List[Anomaly]
    total_points: int
    detection_time: float
    method: DetectionMethod
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def anomaly_rate(self) -> float:
        """Calculate the anomaly rate."""
        if self.total_points == 0:
            return 0.0
        return len(self.anomalies) / self.total_points


@dataclass
class UserFeedback:
    """User feedback on anomaly detection."""
    anomaly_id: str
    feedback_type: str  # 'false_positive', 'true_positive', 'adjust_sensitivity'
    timestamp: datetime
    user_comment: Optional[str] = None
    suggested_threshold: Optional[float] = None


@dataclass
class PersonalThreshold:
    """Personal threshold settings for a metric/method combination."""
    metric: str
    method: DetectionMethod
    multiplier: float = 1.0
    false_positives: int = 0
    true_positives: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy based on feedback."""
        total = self.false_positives + self.true_positives
        if total == 0:
            return 0.0
        return self.true_positives / total


@dataclass
class DetectionConfig:
    """Configuration for anomaly detection."""
    enabled_methods: List[DetectionMethod] = field(default_factory=lambda: [
        DetectionMethod.MODIFIED_ZSCORE,
        DetectionMethod.ISOLATION_FOREST,
        DetectionMethod.LOF
    ])
    
    # Statistical method parameters
    zscore_threshold: float = 3.0
    modified_zscore_threshold: float = 3.5
    iqr_multiplier: float = 1.5
    
    # ML method parameters
    isolation_forest_contamination: float = 0.01
    lof_neighbors: int = 20
    lof_contamination: float = 0.01
    
    # LSTM parameters (when available)
    lstm_sequence_length: int = 24
    lstm_threshold_percentile: float = 95
    
    # Ensemble parameters
    ensemble_min_votes: int = 2
    ensemble_weight_by_confidence: bool = True
    
    # Real-time parameters
    real_time_enabled: bool = False
    real_time_latency_ms: int = 100
    
    # Notification parameters
    notification_enabled: bool = True
    notification_severity_threshold: Severity = Severity.MEDIUM
    group_notifications: bool = True
    
    # Feedback parameters
    adaptive_thresholds: bool = True
    feedback_learning_rate: float = 0.1
    min_feedback_for_adjustment: int = 3


class AnomalyDetectionError(Exception):
    """Base exception for anomaly detection errors."""
    pass


class InsufficientDataError(AnomalyDetectionError):
    """Raised when there's insufficient data for detection."""
    pass


class ModelNotTrainedError(AnomalyDetectionError):
    """Raised when trying to use an untrained model."""
    pass


class InvalidConfigurationError(AnomalyDetectionError):
    """Raised when configuration is invalid."""
    pass