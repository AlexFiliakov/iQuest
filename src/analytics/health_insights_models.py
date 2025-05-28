"""
Data models for the Health Insights & Recommendations Engine.

This module defines the data structures used for representing health insights,
evidence, personalized goals, and related entities following evidence-based
medical guidelines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class InsightCategory(str, Enum):
    """Categories of health insights."""
    SLEEP = "sleep"
    ACTIVITY = "activity"
    RECOVERY = "recovery"
    NUTRITION = "nutrition"
    BODY_METRICS = "body_metrics"
    HEART_HEALTH = "heart_health"


class InsightType(str, Enum):
    """Types of insights based on analysis method."""
    PATTERN = "pattern"
    CORRELATION = "correlation"
    TREND = "trend"
    OPPORTUNITY = "opportunity"
    CONCERN = "concern"
    ACHIEVEMENT = "achievement"


class EvidenceLevel(str, Enum):
    """Evidence quality levels following medical standards."""
    STRONG = "strong"  # WHO/CDC guidelines, peer-reviewed meta-analyses
    MODERATE = "moderate"  # Clinical studies, professional organization recommendations
    WEAK = "weak"  # Observational studies, expert opinion
    PATTERN_BASED = "pattern_based"  # User-specific patterns without general medical backing


class Priority(str, Enum):
    """Priority levels for insights."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactPotential(str, Enum):
    """Potential impact of implementing the recommendation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Achievability(str, Enum):
    """How easy it is to achieve the recommendation."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"


class Timeframe(str, Enum):
    """Timeframe for implementing recommendations."""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"  # 1-4 weeks
    LONG_TERM = "long_term"  # 1+ months


@dataclass
class InsightEvidence:
    """Evidence supporting a health insight."""
    source_type: str  # "guideline", "study", "pattern_analysis"
    source_name: str  # "CDC Sleep Guidelines", "User Pattern Analysis"
    evidence_quality: str  # "high", "medium", "low"
    relevance_score: float  # 0-1 relevance to user's situation
    citation: Optional[str] = None  # Full citation if applicable
    url: Optional[str] = None  # Link to source if available
    key_findings: Optional[List[str]] = None  # Key relevant findings from source
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'source_type': self.source_type,
            'source_name': self.source_name,
            'evidence_quality': self.evidence_quality,
            'relevance_score': self.relevance_score,
            'citation': self.citation,
            'url': self.url,
            'key_findings': self.key_findings
        }


@dataclass
class WSJPresentation:
    """WSJ-style presentation configuration for insights."""
    headline_style: str = "prominent"
    evidence_indicator: Dict[str, Any] = field(default_factory=dict)
    confidence_display: str = ""
    color_coding: Dict[str, str] = field(default_factory=dict)
    layout_priority: int = 1
    accessibility: Dict[str, str] = field(default_factory=dict)
    visual_elements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'headline_style': self.headline_style,
            'evidence_indicator': self.evidence_indicator,
            'confidence_display': self.confidence_display,
            'color_coding': self.color_coding,
            'layout_priority': self.layout_priority,
            'accessibility': self.accessibility,
            'visual_elements': self.visual_elements
        }


@dataclass
class HealthInsight:
    """Comprehensive health insight with evidence and recommendations."""
    category: InsightCategory
    insight_type: InsightType
    title: str  # WSJ-style clear, engaging headline
    summary: str  # One-sentence key finding
    description: str  # Detailed explanation with context
    recommendation: str  # Specific, actionable advice
    evidence_level: EvidenceLevel
    evidence_sources: List[str]  # References to guidelines, studies
    confidence: float  # 0-100% statistical confidence in pattern
    priority: Priority
    impact_potential: ImpactPotential
    achievability: Achievability
    timeframe: Timeframe
    supporting_data: Dict[str, Any] = field(default_factory=dict)  # Charts, statistics, trends
    medical_disclaimer: str = "This analysis is for informational purposes only and does not constitute medical advice."
    wsj_presentation: Optional[WSJPresentation] = None
    created_at: datetime = field(default_factory=datetime.now)
    evidence_details: List[InsightEvidence] = field(default_factory=list)
    related_metrics: List[str] = field(default_factory=list)  # Metrics involved in this insight
    
    def __post_init__(self):
        """Initialize WSJ presentation if not provided."""
        if self.wsj_presentation is None:
            self.wsj_presentation = WSJPresentation()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'category': self.category.value,
            'insight_type': self.insight_type.value,
            'title': self.title,
            'summary': self.summary,
            'description': self.description,
            'recommendation': self.recommendation,
            'evidence_level': self.evidence_level.value,
            'evidence_sources': self.evidence_sources,
            'confidence': self.confidence,
            'priority': self.priority.value,
            'impact_potential': self.impact_potential.value,
            'achievability': self.achievability.value,
            'timeframe': self.timeframe.value,
            'supporting_data': self.supporting_data,
            'medical_disclaimer': self.medical_disclaimer,
            'wsj_presentation': self.wsj_presentation.to_dict() if self.wsj_presentation else None,
            'created_at': self.created_at.isoformat(),
            'evidence_details': [e.to_dict() for e in self.evidence_details],
            'related_metrics': self.related_metrics
        }


@dataclass
class PersonalizedGoal:
    """Evidence-based personalized health goal."""
    goal_type: str  # "sleep_duration", "daily_steps", "weight_target"
    current_baseline: float  # User's current average
    recommended_target: float  # Evidence-based target
    rationale: str  # Why this target is appropriate
    timeline: str  # Suggested timeframe for achievement
    milestones: List[Dict[str, Any]] = field(default_factory=list)  # Intermediate goals
    evidence_basis: Optional[InsightEvidence] = None  # Supporting evidence
    confidence_score: float = 0.0  # Confidence in achievability
    personalization_factors: Dict[str, Any] = field(default_factory=dict)  # User-specific adjustments
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'goal_type': self.goal_type,
            'current_baseline': self.current_baseline,
            'recommended_target': self.recommended_target,
            'rationale': self.rationale,
            'timeline': self.timeline,
            'milestones': self.milestones,
            'evidence_basis': self.evidence_basis.to_dict() if self.evidence_basis else None,
            'confidence_score': self.confidence_score,
            'personalization_factors': self.personalization_factors
        }


@dataclass
class InsightBatch:
    """Collection of insights for a specific time period."""
    time_period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    insights: List[HealthInsight] = field(default_factory=list)
    summary: str = ""
    total_insights: int = 0
    high_priority_count: int = 0
    evidence_summary: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate summary statistics."""
        self.total_insights = len(self.insights)
        self.high_priority_count = sum(1 for i in self.insights if i.priority == Priority.HIGH)
        
        # Count evidence levels
        self.evidence_summary = {
            'strong': sum(1 for i in self.insights if i.evidence_level == EvidenceLevel.STRONG),
            'moderate': sum(1 for i in self.insights if i.evidence_level == EvidenceLevel.MODERATE),
            'weak': sum(1 for i in self.insights if i.evidence_level == EvidenceLevel.WEAK),
            'pattern_based': sum(1 for i in self.insights if i.evidence_level == EvidenceLevel.PATTERN_BASED)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'time_period': self.time_period,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'insights': [i.to_dict() for i in self.insights],
            'summary': self.summary,
            'total_insights': self.total_insights,
            'high_priority_count': self.high_priority_count,
            'evidence_summary': self.evidence_summary
        }


@dataclass
class MedicalGuideline:
    """Medical guideline from authoritative sources."""
    category: InsightCategory
    metric_type: str  # "sleep_duration", "steps_daily", etc.
    source: str  # "CDC", "WHO", "NSF", etc.
    guideline_name: str
    recommendations: Dict[str, Any]  # Age/condition-specific recommendations
    evidence_strength: EvidenceLevel
    last_updated: datetime
    url: Optional[str] = None
    notes: Optional[str] = None
    
    def applies_to_user(self, user_demographics: Dict[str, Any]) -> bool:
        """Check if guideline applies to specific user demographics."""
        # Implementation would check age, gender, conditions, etc.
        return True
    
    def get_recommendation_for_user(self, user_demographics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get specific recommendation for user based on demographics."""
        # Implementation would return age/condition-specific recommendation
        return self.recommendations.get('general', None)