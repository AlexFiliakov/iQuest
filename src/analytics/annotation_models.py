"""Models for health insight annotations"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd
from PyQt6.QtCore import QPointF


class AnnotationType(Enum):
    """Types of health annotations"""
    ANOMALY = "anomaly"
    ACHIEVEMENT = "achievement"
    TREND = "trend"
    INSIGHT = "insight"
    MILESTONE = "milestone"
    COMPARISON = "comparison"
    WARNING = "warning"
    GOAL = "goal"


class AnnotationPriority(Enum):
    """Priority levels for annotations"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TrendDirection(Enum):
    """Direction of trend annotations"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


@dataclass
class HealthAnnotation:
    """Base class for all health annotations"""
    id: str
    type: AnnotationType
    data_point: datetime
    value: float
    priority: AnnotationPriority = AnnotationPriority.MEDIUM
    position: Optional[QPointF] = None
    title: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    visible: bool = True
    interactive: bool = True
    
    def __post_init__(self):
        """Initialize position if not provided"""
        if self.position is None:
            self.position = QPointF(0, 0)


@dataclass
class AnomalyAnnotation(HealthAnnotation):
    """Annotation for anomalous health data"""
    severity: float = 0.5  # 0-1 scale
    anomaly_type: str = ""
    expected_range: tuple = (0, 0)
    deviation_percent: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.ANOMALY
        if not self.title:
            self.title = "Unusual Pattern Detected"


@dataclass
class AchievementAnnotation(HealthAnnotation):
    """Annotation for health achievements and milestones"""
    achievement_type: str = ""
    previous_best: Optional[float] = None
    improvement_percent: float = 0.0
    streak_days: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.ACHIEVEMENT
        if not self.title:
            self.title = "New Achievement!"


@dataclass
class TrendAnnotation(HealthAnnotation):
    """Annotation for health trends"""
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_start: datetime = field(default_factory=datetime.now)
    trend_end: datetime = field(default_factory=datetime.now)
    confidence: float = 0.8  # 0-1 scale
    slope: float = 0.0
    change_percent: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.TREND
        if not self.title:
            direction_text = self.trend_direction.value.capitalize()
            self.title = f"{direction_text} Trend"


@dataclass
class InsightAnnotation(HealthAnnotation):
    """Annotation for contextual health insights"""
    insight_category: str = ""
    confidence: float = 0.8
    related_metrics: List[str] = field(default_factory=list)
    recommendation: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.INSIGHT
        if not self.title:
            self.title = "Health Insight"


@dataclass
class MilestoneAnnotation(HealthAnnotation):
    """Annotation for health milestones"""
    milestone_type: str = ""
    days_to_achieve: int = 0
    target_value: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.MILESTONE
        if not self.title:
            self.title = "Milestone Reached!"


@dataclass
class ComparisonAnnotation(HealthAnnotation):
    """Annotation for comparative insights"""
    comparison_type: str = ""  # e.g., "peer_group", "personal_average", "goal"
    comparison_value: float = 0.0
    difference_percent: float = 0.0
    better_than_percent: float = 50.0  # percentile
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.COMPARISON
        if not self.title:
            self.title = "Comparison"


@dataclass
class GoalAnnotation(HealthAnnotation):
    """Annotation for goal-related information"""
    goal_name: str = ""
    target_value: float = 0.0
    progress_percent: float = 0.0
    days_remaining: int = 0
    on_track: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        self.type = AnnotationType.GOAL
        if not self.title:
            self.title = f"Goal: {self.goal_name}"


@dataclass
class AnnotationStyle:
    """Visual style configuration for annotations"""
    marker_symbol: str = "circle"
    marker_size: int = 8
    marker_color: str = "#6B4226"
    text_color: str = "#6B4226"
    background_color: str = "#FFFFFF"
    border_color: str = "#D4B5A0"
    font_size: int = 10
    font_weight: str = "normal"
    opacity: float = 1.0
    shadow: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary for serialization"""
        return {
            'marker_symbol': self.marker_symbol,
            'marker_size': self.marker_size,
            'marker_color': self.marker_color,
            'text_color': self.text_color,
            'background_color': self.background_color,
            'border_color': self.border_color,
            'font_size': self.font_size,
            'font_weight': self.font_weight,
            'opacity': self.opacity,
            'shadow': self.shadow
        }


@dataclass
class AnnotationPosition:
    """Position information for annotation placement"""
    data_position: QPointF  # Position in data coordinates
    screen_position: QPointF  # Position in screen coordinates
    anchor_point: str = "center"  # center, top, bottom, left, right
    offset: QPointF = field(default_factory=lambda: QPointF(0, 0))
    leader_line: bool = False
    
    def calculate_final_position(self) -> QPointF:
        """Calculate final position with offset"""
        return self.screen_position + self.offset