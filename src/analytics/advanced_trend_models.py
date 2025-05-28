"""Advanced trend analysis models and data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TrendClassification(Enum):
    """Detailed trend classifications."""
    STRONGLY_INCREASING = "strongly_increasing"
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    STRONGLY_DECREASING = "strongly_decreasing"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class EvidenceQuality(Enum):
    """Quality of trend evidence."""
    STRONG = "strong"       # > 30 days of data, high confidence
    MODERATE = "moderate"   # 14-30 days of data, moderate confidence
    WEAK = "weak"          # < 14 days of data, low confidence


class PredictionQuality(Enum):
    """Quality of predictions."""
    HIGH = "high"       # Low uncertainty, stable patterns
    MEDIUM = "medium"   # Moderate uncertainty
    LOW = "low"        # High uncertainty or volatile data


@dataclass
class ChangePoint:
    """Detected change point in trend."""
    timestamp: datetime
    confidence: float  # 0-100% confidence in change point
    magnitude: float   # Size of change
    direction: str     # "increase", "decrease", "volatility_change"
    method: str       # Detection method used (CUSUM, Bayesian, etc.)
    context: Optional[str] = None  # Additional context


@dataclass
class PredictionPoint:
    """Prediction with uncertainty bounds."""
    timestamp: datetime
    predicted_value: float
    lower_bound: float  # 95% confidence interval
    upper_bound: float
    prediction_quality: PredictionQuality
    uncertainty_score: float  # 0-1, higher = more uncertain


@dataclass
class SeasonalComponent:
    """Seasonal pattern information."""
    period: str  # "daily", "weekly", "monthly", "yearly"
    strength: float  # 0-1 strength score
    pattern: Dict[str, float]  # Pattern values (e.g., day_of_week -> value)
    significance: float  # Statistical significance (p-value)


@dataclass
class TrendComponent:
    """Trend component with statistical validation."""
    direction: TrendClassification
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    p_value: float  # Statistical significance
    confidence_interval: Tuple[float, float]  # CI for slope


@dataclass
class TrendAnalysis:
    """Standard trend analysis results as per specification."""
    # Core fields as per specification
    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    trend_strength: float  # 0-1 strength score (effect size)
    confidence: float  # 0-100% confidence in classification
    statistical_significance: float  # p-value from Mann-Kendall test
    seasonal_component: bool  # Has seasonal patterns
    seasonal_strength: float  # 0-1 seasonal component strength
    volatility_level: str  # "low", "medium", "high"
    volatility_score: float  # Coefficient of variation
    predictions: List[PredictionPoint]  # Future predictions with uncertainty
    change_points: List[ChangePoint]  # Detected trend changes with confidence
    summary: str  # Human-readable description (WSJ-style)
    evidence_quality: str  # "strong", "moderate", "weak" based on data quality
    interpretation: str  # Health context and actionable insights
    
    # Enhanced features (optional, for advanced analysis)
    seasonal_components: Optional[List[SeasonalComponent]] = None  # Detailed seasonal patterns
    volatility_trend: Optional[str] = None  # "increasing", "stable", "decreasing"
    methods_used: Optional[List[str]] = None  # Analysis methods employed
    ensemble_agreement: Optional[float] = None  # 0-1, agreement between methods
    data_quality_score: Optional[float] = None  # 0-1, data quality assessment
    recommendations: Optional[List[str]] = None  # Actionable recommendations
    comparison_to_baseline: Optional[Dict[str, float]] = None  # Comparison metrics
    peer_comparison: Optional[Dict[str, float]] = None  # Peer group comparison
    historical_context: Optional[str] = None  # Historical perspective
    
    # Additional advanced fields (not in original spec)
    forecast_horizon: Optional[int] = None  # Days ahead
    structural_breaks: Optional[List[datetime]] = None  # Major pattern changes


@dataclass
class AdvancedTrendAnalysis(TrendAnalysis):
    """Extended trend analysis with all advanced features.
    
    This class exists for backward compatibility and advanced use cases.
    For standard compliance, use TrendAnalysis directly.
    """
    pass


@dataclass
class TrendDecomposition:
    """Decomposed time series components."""
    observed: List[float]
    trend: List[float]
    seasonal: List[float]
    residual: List[float]
    timestamps: List[datetime]
    method: str  # "STL", "Prophet", "Classical"
    
    
@dataclass
class ValidationResult:
    """Statistical validation results."""
    test_name: str  # "Mann-Kendall", "Sen's Slope", etc.
    statistic: float
    p_value: float
    trend_detected: bool
    trend_direction: Optional[str] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    interpretation: Optional[str] = None


@dataclass
class EnsembleResult:
    """Results from ensemble analysis."""
    primary_trend: TrendClassification
    confidence: float  # Weighted confidence
    individual_results: Dict[str, TrendClassification]
    weights: Dict[str, float]
    agreement_score: float  # 0-1, how much methods agree
    
    
@dataclass
class WSJVisualizationConfig:
    """Configuration for WSJ-style visualization."""
    title: str
    subtitle: Optional[str] = None
    show_confidence_bands: bool = True
    highlight_change_points: bool = True
    annotation_style: str = "minimal"  # "minimal", "detailed"
    color_scheme: str = "warm"  # "warm", "cool", "monochrome"
    progressive_disclosure: bool = True
    summary_position: str = "top"  # "top", "bottom", "side"