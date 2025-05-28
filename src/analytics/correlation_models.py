"""
Data models for the Health Correlations Discovery Engine.
Provides structured representations of correlation insights, networks, and analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class CorrelationType(Enum):
    """Types of correlation analysis methods."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    MUTUAL_INFO = "mutual_info"
    GRANGER = "granger"
    PARTIAL = "partial"


class EffectSize(Enum):
    """Cohen's conventions for correlation effect sizes."""
    NEGLIGIBLE = "negligible"  # < 0.1
    SMALL = "small"            # 0.1 - 0.3
    MEDIUM = "medium"          # 0.3 - 0.5
    LARGE = "large"            # > 0.5


class EvidenceQuality(Enum):
    """Quality of evidence based on data characteristics."""
    STRONG = "strong"      # Large sample, low variance, consistent
    MODERATE = "moderate"  # Medium sample, moderate variance
    WEAK = "weak"         # Small sample, high variance, inconsistent


class CorrelationStrength(Enum):
    """Strength categories for correlations."""
    VERY_WEAK = "very_weak"      # < 0.2
    WEAK = "weak"                # 0.2 - 0.4
    MODERATE = "moderate"        # 0.4 - 0.6
    STRONG = "strong"            # 0.6 - 0.8
    VERY_STRONG = "very_strong"  # > 0.8


@dataclass
class CorrelationInsight:
    """
    Represents a discovered correlation with full context and interpretation.
    Follows WSJ analytics principles for clear, actionable insights.
    """
    metric_pair: Tuple[str, str]
    correlation_value: float
    correlation_type: CorrelationType
    significance: float  # p-value
    effect_size: EffectSize
    confidence_interval: Tuple[float, float]
    lag_days: int = 0  # 0 for instantaneous
    context: str = "all"  # "weekdays", "weekends", "seasonal", "all"
    health_interpretation: str = ""
    actionable_insight: str = ""
    evidence_quality: EvidenceQuality = EvidenceQuality.MODERATE
    sample_size: int = 0
    strength: CorrelationStrength = CorrelationStrength.WEAK
    direction: str = "positive"  # "positive" or "negative"
    wsj_summary: str = ""  # Clear, concise WSJ-style summary
    
    # Additional context
    controlling_variables: List[str] = field(default_factory=list)
    interaction_effects: List[str] = field(default_factory=list)
    temporal_stability: float = 0.0  # How stable the correlation is over time
    
    def __post_init__(self):
        """Validate and compute derived fields."""
        # Compute effect size if not set
        if not isinstance(self.effect_size, EffectSize):
            self.effect_size = self._compute_effect_size()
        
        # Compute strength if not set
        if not isinstance(self.strength, CorrelationStrength):
            self.strength = self._compute_strength()
        
        # Set direction based on correlation value
        self.direction = "positive" if self.correlation_value > 0 else "negative"
    
    def _compute_effect_size(self) -> EffectSize:
        """Compute effect size based on Cohen's conventions."""
        abs_corr = abs(self.correlation_value)
        if abs_corr < 0.1:
            return EffectSize.NEGLIGIBLE
        elif abs_corr < 0.3:
            return EffectSize.SMALL
        elif abs_corr < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE
    
    def _compute_strength(self) -> CorrelationStrength:
        """Compute correlation strength category."""
        abs_corr = abs(self.correlation_value)
        if abs_corr < 0.2:
            return CorrelationStrength.VERY_WEAK
        elif abs_corr < 0.4:
            return CorrelationStrength.WEAK
        elif abs_corr < 0.6:
            return CorrelationStrength.MODERATE
        elif abs_corr < 0.8:
            return CorrelationStrength.STRONG
        else:
            return CorrelationStrength.VERY_STRONG
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if correlation is statistically significant."""
        return self.significance < alpha
    
    def is_actionable(self) -> bool:
        """Check if the insight suggests actionable behavior changes."""
        return bool(self.actionable_insight) and self.effect_size != EffectSize.NEGLIGIBLE


@dataclass
class CorrelationCluster:
    """Represents a group of highly intercorrelated metrics."""
    cluster_id: str
    metrics: List[str]
    central_metric: str  # Most connected metric in cluster
    average_correlation: float
    cluster_interpretation: str
    behavioral_theme: str  # e.g., "exercise cluster", "sleep quality cluster"


@dataclass
class CorrelationNetwork:
    """
    Represents the full network of correlations between health metrics.
    Provides network-level insights and patterns.
    """
    nodes: List[str]  # Metric names
    edges: List[CorrelationInsight]  # Significant correlations
    clusters: List[CorrelationCluster]  # Groups of related metrics
    key_hubs: List[str]  # Metrics with many significant correlations
    network_summary: str  # WSJ-style network interpretation
    
    # Network statistics
    density: float = 0.0  # Proportion of possible edges that exist
    average_clustering: float = 0.0  # How tightly connected neighborhoods are
    modularity: float = 0.0  # How well-separated clusters are
    
    def get_metric_connections(self, metric: str) -> List[CorrelationInsight]:
        """Get all correlations involving a specific metric."""
        connections = []
        for edge in self.edges:
            if metric in edge.metric_pair:
                connections.append(edge)
        return connections
    
    def get_strongest_correlations(self, n: int = 10) -> List[CorrelationInsight]:
        """Get the n strongest correlations in the network."""
        sorted_edges = sorted(self.edges, 
                            key=lambda x: abs(x.correlation_value), 
                            reverse=True)
        return sorted_edges[:n]
    
    def get_cluster_for_metric(self, metric: str) -> Optional[CorrelationCluster]:
        """Find which cluster a metric belongs to."""
        for cluster in self.clusters:
            if metric in cluster.metrics:
                return cluster
        return None


@dataclass
class LagCorrelationResult:
    """Results from lag correlation analysis between two metrics."""
    metric1: str
    metric2: str
    lag_correlations: Dict[int, float]  # lag -> correlation value
    lag_p_values: Dict[int, float]  # lag -> p-value
    optimal_lag: int
    optimal_correlation: float
    interpretation: str  # e.g., "Exercise today predicts better sleep tomorrow"
    
    def get_significant_lags(self, alpha: float = 0.05) -> List[int]:
        """Get all lags with significant correlations."""
        return [lag for lag, p_val in self.lag_p_values.items() if p_val < alpha]


@dataclass
class ConditionalCorrelation:
    """Correlation that varies based on conditions."""
    metric_pair: Tuple[str, str]
    base_correlation: float
    conditional_correlations: Dict[str, float]  # condition -> correlation
    condition_type: str  # "temporal", "activity", "threshold"
    interpretation: str
    
    def get_strongest_condition(self) -> Tuple[str, float]:
        """Get the condition with strongest correlation."""
        return max(self.conditional_correlations.items(), 
                  key=lambda x: abs(x[1]))


@dataclass
class CausalRelationship:
    """Represents a potential causal relationship discovered through analysis."""
    cause_metric: str
    effect_metric: str
    lag_days: int
    granger_statistic: float
    granger_p_value: float
    effect_size: float
    mechanism_hypothesis: str  # Proposed biological/behavioral mechanism
    confidence_level: str  # "high", "medium", "low"
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if Granger causality is significant."""
        return self.granger_p_value < alpha


@dataclass
class CorrelationAnalysisReport:
    """
    Comprehensive report of correlation analysis results.
    Organized for progressive disclosure and WSJ-style presentation.
    """
    analysis_timestamp: datetime
    metrics_analyzed: List[str]
    total_observations: int
    date_range: Tuple[datetime, datetime]
    
    # Layer 1: Traditional correlations
    pearson_insights: List[CorrelationInsight]
    spearman_insights: List[CorrelationInsight]
    
    # Layer 2: Advanced analysis
    lag_correlations: List[LagCorrelationResult]
    conditional_correlations: List[ConditionalCorrelation]
    partial_correlations: List[CorrelationInsight]
    
    # Layer 3: Causal analysis
    causal_relationships: List[CausalRelationship]
    
    # Network analysis
    correlation_network: CorrelationNetwork
    
    # Key findings
    top_insights: List[CorrelationInsight]
    behavioral_recommendations: List[str]
    data_quality_warnings: List[str]
    
    def get_executive_summary(self) -> str:
        """Generate WSJ-style executive summary of findings."""
        summary_parts = []
        
        # Lead with most important finding
        if self.top_insights:
            top = self.top_insights[0]
            summary_parts.append(top.wsj_summary)
        
        # Add network-level insight
        if self.correlation_network.network_summary:
            summary_parts.append(self.correlation_network.network_summary)
        
        # Add actionable recommendation
        if self.behavioral_recommendations:
            summary_parts.append(f"Key recommendation: {self.behavioral_recommendations[0]}")
        
        return " ".join(summary_parts)


@dataclass
class CorrelationMatrixStyle:
    """WSJ-style configuration for correlation matrix visualization."""
    color_palette: str = "RdBu_r"  # Diverging palette
    significance_markers: Dict[float, str] = field(default_factory=lambda: {
        0.001: "***",
        0.01: "**", 
        0.05: "*"
    })
    cell_format: str = ".2f"  # Format for correlation values
    highlight_threshold: float = 0.5  # Highlight strong correlations
    show_only_significant: bool = False
    annotation_style: Dict[str, Any] = field(default_factory=lambda: {
        "fontsize": 10,
        "ha": "center",
        "va": "center"
    })