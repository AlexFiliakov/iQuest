"""
Goal models for the health tracking goal management system.
Defines different goal types and their structures.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import json
import pandas as pd


class GoalType(Enum):
    """Types of goals supported by the system."""
    TARGET = "target"  # Reach a specific value
    CONSISTENCY = "consistency"  # Maintain frequency
    IMPROVEMENT = "improvement"  # Improve by percentage
    HABIT = "habit"  # Form habits (21-day challenges etc)


class GoalStatus(Enum):
    """Status of a goal."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalTimeframe(Enum):
    """Timeframe for goal evaluation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class Goal:
    """Base class for all goal types."""
    id: Optional[int] = None
    goal_type: GoalType = GoalType.TARGET
    metric: str = ""
    name: str = ""
    description: str = ""
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    user_id: Optional[int] = None
    
    def is_active(self) -> bool:
        """Check if goal is currently active."""
        if self.status != GoalStatus.ACTIVE:
            return False
        
        today = date.today()
        if self.start_date > today:
            return False
        
        if self.end_date and self.end_date < today:
            return False
            
        return True
    
    def calculate_progress(self, current_value: Union[float, pd.Series]) -> float:
        """Calculate progress percentage. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement calculate_progress")
    
    def is_achieved(self, data: Any) -> bool:
        """Check if goal is achieved. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement is_achieved")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'goal_type': self.goal_type.value,
            'metric': self.metric,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'user_id': self.user_id
        }


@dataclass
class TargetGoal(Goal):
    """Goal to reach a specific target value."""
    target_value: float = 0.0
    timeframe: GoalTimeframe = GoalTimeframe.DAILY
    duration: Optional[int] = None  # Number of periods (days/weeks/months)
    
    def __post_init__(self):
        self.goal_type = GoalType.TARGET
        if not self.name:
            self.name = f"Reach {self.target_value} {self.metric} {self.timeframe.value}"
    
    def calculate_progress(self, current_value: float) -> float:
        """Calculate progress towards target."""
        if self.target_value == 0:
            return 100.0 if current_value >= self.target_value else 0.0
        
        return min(100.0, (current_value / self.target_value) * 100)
    
    def is_achieved(self, current_value: float) -> bool:
        """Check if target is reached."""
        return current_value >= self.target_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = super().to_dict()
        data.update({
            'target_value': self.target_value,
            'timeframe': self.timeframe.value,
            'duration': self.duration
        })
        return data


@dataclass
class ConsistencyGoal(Goal):
    """Goal to maintain consistency (e.g., exercise 5 times per week)."""
    frequency: int = 0  # Times per period
    period: GoalTimeframe = GoalTimeframe.WEEKLY
    threshold: Optional[float] = None  # Minimum value to count
    allow_partial: bool = True  # Allow partial credit
    
    def __post_init__(self):
        self.goal_type = GoalType.CONSISTENCY
        if not self.name:
            self.name = f"{self.metric} {self.frequency} times per {self.period.value}"
    
    def calculate_progress(self, period_data: List[float]) -> float:
        """Calculate consistency progress."""
        if self.threshold:
            valid_days = sum(1 for value in period_data if value >= self.threshold)
        else:
            valid_days = sum(1 for value in period_data if value > 0)
        
        if self.allow_partial:
            return min(100.0, (valid_days / self.frequency) * 100)
        else:
            return 100.0 if valid_days >= self.frequency else 0.0
    
    def is_achieved(self, period_data: List[float]) -> bool:
        """Check if consistency target is met."""
        return self.calculate_progress(period_data) >= 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = super().to_dict()
        data.update({
            'frequency': self.frequency,
            'period': self.period.value,
            'threshold': self.threshold,
            'allow_partial': self.allow_partial
        })
        return data


@dataclass
class ImprovementGoal(Goal):
    """Goal to improve by a certain percentage or amount."""
    improvement_target: float = 0.0  # Percentage or absolute
    improvement_type: str = "percentage"  # "percentage" or "absolute"
    baseline_value: Optional[float] = None
    baseline_period: int = 30  # Days to calculate baseline
    
    def __post_init__(self):
        self.goal_type = GoalType.IMPROVEMENT
        if not self.name:
            symbol = "%" if self.improvement_type == "percentage" else ""
            self.name = f"Improve {self.metric} by {self.improvement_target}{symbol}"
    
    def calculate_progress(self, current_value: float) -> float:
        """Calculate improvement progress."""
        if self.baseline_value is None or self.baseline_value == 0:
            return 0.0
        
        if self.improvement_type == "percentage":
            target_value = self.baseline_value * (1 + self.improvement_target / 100)
            current_improvement = ((current_value - self.baseline_value) / self.baseline_value) * 100
            return min(100.0, (current_improvement / self.improvement_target) * 100)
        else:
            target_value = self.baseline_value + self.improvement_target
            current_improvement = current_value - self.baseline_value
            return min(100.0, (current_improvement / self.improvement_target) * 100)
    
    def is_achieved(self, current_value: float) -> bool:
        """Check if improvement target is met."""
        return self.calculate_progress(current_value) >= 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = super().to_dict()
        data.update({
            'improvement_target': self.improvement_target,
            'improvement_type': self.improvement_type,
            'baseline_value': self.baseline_value,
            'baseline_period': self.baseline_period
        })
        return data


@dataclass
class HabitGoal(Goal):
    """Goal for habit formation (21-day challenges, etc.)."""
    target_days: int = 21  # Total days for habit formation
    current_streak: int = 0
    best_streak: int = 0
    required_daily_value: Optional[float] = None
    allow_skip_days: int = 0  # Grace days allowed
    skips_used: int = 0
    
    def __post_init__(self):
        self.goal_type = GoalType.HABIT
        if not self.name:
            self.name = f"{self.target_days}-day {self.metric} challenge"
    
    def calculate_progress(self, current_streak: int) -> float:
        """Calculate habit formation progress."""
        return min(100.0, (current_streak / self.target_days) * 100)
    
    def is_achieved(self, current_streak: int) -> bool:
        """Check if habit goal is completed."""
        return current_streak >= self.target_days
    
    def update_streak(self, did_today: bool) -> None:
        """Update streak based on today's performance."""
        if did_today:
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            if self.skips_used < self.allow_skip_days:
                self.skips_used += 1
            else:
                self.current_streak = 0
                self.skips_used = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = super().to_dict()
        data.update({
            'target_days': self.target_days,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'required_daily_value': self.required_daily_value,
            'allow_skip_days': self.allow_skip_days,
            'skips_used': self.skips_used
        })
        return data


@dataclass
class GoalSuggestion:
    """Suggested goal based on user's historical data."""
    goal_type: GoalType
    metric: str
    suggested_value: float
    timeframe: GoalTimeframe
    achievability_score: float = 0.0  # 0-1 score
    impact_score: float = 0.0  # 0-1 score
    reasoning: str = ""
    based_on: str = ""  # What data the suggestion is based on
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'goal_type': self.goal_type.value,
            'metric': self.metric,
            'suggested_value': self.suggested_value,
            'timeframe': self.timeframe.value,
            'achievability_score': self.achievability_score,
            'impact_score': self.impact_score,
            'reasoning': self.reasoning,
            'based_on': self.based_on
        }


@dataclass
class GoalProgress:
    """Progress tracking for a goal."""
    goal_id: int
    date: date
    value: float
    progress_percentage: float
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'goal_id': self.goal_id,
            'date': self.date.isoformat(),
            'value': self.value,
            'progress_percentage': self.progress_percentage,
            'notes': self.notes
        }


@dataclass
class GoalAdjustment:
    """Suggested adjustment for an adaptive goal."""
    adjustment_type: str  # 'increase_difficulty', 'decrease_difficulty', 'modify_approach'
    reason: str
    new_target: Optional[float] = None
    suggestion: Optional[str] = None
    confidence: float = 0.0  # 0-1 confidence in the adjustment
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'adjustment_type': self.adjustment_type,
            'reason': self.reason,
            'new_target': self.new_target,
            'suggestion': self.suggestion,
            'confidence': self.confidence
        }


@dataclass  
class GoalRelationship:
    """Relationship between two goals."""
    goal1_id: int
    goal2_id: int
    relationship_type: str  # 'synergistic', 'conflicting', 'independent'
    strength: float  # 0-1 strength of relationship
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'goal1_id': self.goal1_id,
            'goal2_id': self.goal2_id,
            'relationship_type': self.relationship_type,
            'strength': self.strength,
            'description': self.description
        }