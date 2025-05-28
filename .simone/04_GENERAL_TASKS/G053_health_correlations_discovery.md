---
task_id: G053
status: open
created: 2025-05-28
complexity: medium
sprint_ref: S04_M01_Core_Analytics
---

# Task G053: Health Correlations Discovery Engine

## Description
Build intelligent correlation discovery system that identifies meaningful relationships between health metrics, provides statistical validation, and generates actionable insights about health patterns and behaviors.

## Goals
- [ ] Implement layered correlation analysis: traditional → mutual information → Granger causality
- [ ] Create comprehensive correlation framework (Pearson, Spearman, Kendall, mutual information)
- [ ] Build lag correlation analysis for delayed health effects (0-7 days)
- [ ] Implement conditional correlation analysis (weekday/weekend, seasonal, activity context)
- [ ] Add robust statistical significance testing with Bonferroni correction
- [ ] Create correlation clustering and network analysis for metric ecosystems
- [ ] Implement Granger causality testing for key health relationships
- [ ] Build automated insight generation following WSJ analytics principles
- [ ] Create interactive correlation matrix with progressive disclosure
- [ ] Implement WSJ-style correlation visualization with clear hierarchy and minimal decoration

## Acceptance Criteria
- [ ] Calculates correlations between all metric pairs with significance testing
- [ ] Identifies time-lagged relationships (0-7 day delays)
- [ ] Provides context-aware correlations (weekday vs weekend, seasons)
- [ ] Filters spurious correlations using statistical rigor
- [ ] Generates human-readable correlation insights
- [ ] Interactive matrix visualization with drill-down capability
- [ ] Handles missing data and different sampling frequencies
- [ ] Performance: < 300ms for correlation matrix with 20+ metrics

## Technical Details

### Layered Correlation Analysis Framework
**Layer 1: Traditional Correlations (Always Available)**
- Pearson (linear relationships), Spearman (monotonic), Kendall (rank-based)
- Fast computation, immediate insights, interpretable results
- Statistical significance with proper multiple comparison correction

**Layer 2: Advanced Analysis (Progressive Enhancement)**
- Mutual Information for non-linear relationships
- Partial correlations controlling for confounders
- Rolling correlations for time-varying relationships

**Layer 3: Causal Analysis (For Key Relationships)**
- Granger causality testing for temporal precedence
- Structural equation modeling for complex relationships
- Mediation analysis for understanding pathways

### WSJ-Style Correlation Presentation
- **Visual Hierarchy**: Strong correlations prominently displayed
- **Progressive Disclosure**: Summary → correlation matrix → detailed analysis
- **Clear Significance Indicators**: Visual cues for statistical confidence
- **Contextual Interpretation**: Health-relevant explanations, not just statistics
- **Minimal Decoration**: Focus on correlation patterns, reduce chart junk

### Statistical Validation
- **Significance Testing**: p-values with Bonferroni correction
- **Effect Size**: Cohen's conventions for correlation strength
- **Confidence Intervals**: Bootstrap confidence intervals
- **Robustness**: Outlier-resistant correlation measures

### Insight Generation
```python
@dataclass
class CorrelationInsight:
    metric_pair: Tuple[str, str]
    correlation_value: float
    correlation_type: str  # "pearson", "spearman", "mutual_info", "granger"
    significance: float  # p-value
    effect_size: str  # "small", "medium", "large" (Cohen's conventions)
    confidence_interval: Tuple[float, float]  # Bootstrap CI
    lag_days: int  # 0 for instantaneous
    context: str  # "weekdays", "weekends", "seasonal", "all"
    health_interpretation: str  # Clinical/behavioral meaning
    actionable_insight: str  # What user can do with this information
    evidence_quality: str  # "strong", "moderate", "weak" based on data quality
    sample_size: int  # Number of observations
    strength: str  # "weak", "moderate", "strong"
    direction: str  # "positive", "negative"
    wsj_summary: str  # Clear, concise summary following WSJ principles
    
@dataclass
class CorrelationNetwork:
    nodes: List[str]  # Metric names
    edges: List[CorrelationInsight]  # Significant correlations
    clusters: List[List[str]]  # Groups of highly correlated metrics
    key_hubs: List[str]  # Metrics with many significant correlations
    network_summary: str  # WSJ-style network interpretation
```

## Dependencies
- Correlation analysis engine (G040) - enhance existing implementation
- Data filtering engine (G016)
- Statistical libraries (scipy, numpy)

## Implementation Notes
```python
class LayeredCorrelationsEngine:
    """Multi-layered correlation analysis following WSJ analytics principles."""
    
    def __init__(self, data_manager, style_manager: WSJStyleManager):
        self.data_manager = data_manager
        self.style_manager = style_manager
        self.correlation_cache = {}
        
        # Layer 1: Traditional correlations (always available)
        self.traditional_analyzer = TraditionalCorrelationAnalyzer()
        
        # Layer 2: Advanced analysis (when computational resources available)
        self.advanced_analyzer = AdvancedCorrelationAnalyzer()
        
        # Layer 3: Causal analysis (for key relationships)
        self.causal_analyzer = CausalAnalysisEngine()
        
        # WSJ-style insight generator
        self.insight_generator = WSJInsightGenerator()
        
    def discover_correlations_progressive(self, metrics: List[str], 
                                        analysis_depth: str = "standard") -> List[CorrelationInsight]:
        """Progressive correlation discovery with WSJ-style presentation."""
        
        insights = []
        
        # Layer 1: Always compute traditional correlations
        traditional_insights = self._analyze_traditional_correlations(metrics)
        insights.extend(traditional_insights)
        
        if analysis_depth in ["advanced", "comprehensive"]:
            # Layer 2: Non-linear and conditional analysis
            advanced_insights = self._analyze_advanced_correlations(metrics)
            insights.extend(advanced_insights)
            
        if analysis_depth == "comprehensive":
            # Layer 3: Causal analysis for top correlations
            key_pairs = self._identify_key_correlation_pairs(insights)
            causal_insights = self._analyze_causal_relationships(key_pairs)
            insights.extend(causal_insights)
            
        # Generate WSJ-style summaries
        for insight in insights:
            insight.wsj_summary = self._generate_wsj_summary(insight)
            insight.health_interpretation = self._interpret_health_context(insight)
            
        return self._prioritize_insights(insights)
        
    def _analyze_traditional_correlations(self, metrics: List[str]) -> List[CorrelationInsight]:
        """Fast traditional correlation analysis."""
        insights = []
        
        # Get data for all metrics
        data_dict = {}
        for metric in metrics:
            data_dict[metric] = self.data_manager.get_metric_data(metric)
            
        # Pairwise correlation analysis
        for i, metric1 in enumerate(metrics):
            for metric2 in metrics[i+1:]:
                
                # Calculate multiple correlation types
                correlations = {
                    'pearson': self._calculate_pearson(data_dict[metric1], data_dict[metric2]),
                    'spearman': self._calculate_spearman(data_dict[metric1], data_dict[metric2]),
                    'kendall': self._calculate_kendall(data_dict[metric1], data_dict[metric2])
                }
                
                # Lag analysis (0-7 days)
                lag_correlations = self._calculate_lag_correlations(data_dict[metric1], data_dict[metric2])
                
                # Create insights for significant correlations
                for corr_type, (corr_val, p_val) in correlations.items():
                    if p_val < 0.05:  # Significant correlation
                        insight = CorrelationInsight(
                            metric_pair=(metric1, metric2),
                            correlation_value=corr_val,
                            correlation_type=corr_type,
                            significance=p_val,
                            effect_size=self._classify_effect_size(abs(corr_val)),
                            lag_days=0,
                            context="all",
                            sample_size=len(data_dict[metric1]),
                            strength=self._classify_strength(abs(corr_val)),
                            direction="positive" if corr_val > 0 else "negative"
                        )
                        insights.append(insight)
                        
        return insights
        
    def _generate_wsj_summary(self, insight: CorrelationInsight) -> str:
        """Generate WSJ-style correlation summary: clear, actionable, context-aware."""
        
        metric1, metric2 = insight.metric_pair
        
        # Clear language for correlation strength
        if insight.strength == "strong":
            strength_desc = "strongly related to"
        elif insight.strength == "moderate":
            strength_desc = "moderately related to"
        else:
            strength_desc = "weakly related to"
            
        # Direction with health context
        if insight.direction == "positive":
            direction_desc = "increases with"
        else:
            direction_desc = "decreases as"
            
        # Lead with the key finding (WSJ style)
        summary = f"Your {metric1} {direction_desc} {metric2}"
        
        # Add context if significant
        if insight.lag_days > 0:
            summary += f" (with a {insight.lag_days}-day delay)"
            
        if insight.context != "all":
            summary += f" on {insight.context}"
            
        # Add confidence indicator
        if insight.effect_size == "large" and insight.significance < 0.01:
            summary += ". This is a strong, reliable pattern in your data."
        elif insight.significance < 0.05:
            summary += ". This pattern appears consistent in your data."
            
        return summary
        
    def create_wsj_correlation_matrix(self, insights: List[CorrelationInsight]) -> Dict[str, Any]:
        """Create WSJ-style correlation matrix visualization data."""
        
        # Extract unique metrics
        metrics = set()
        for insight in insights:
            metrics.update(insight.metric_pair)
        metrics = sorted(list(metrics))
        
        # Create correlation matrix
        matrix = np.eye(len(metrics))  # Identity matrix
        significance_matrix = np.ones((len(metrics), len(metrics)))
        
        metric_index = {metric: i for i, metric in enumerate(metrics)}
        
        for insight in insights:
            i = metric_index[insight.metric_pair[0]]
            j = metric_index[insight.metric_pair[1]]
            
            matrix[i, j] = insight.correlation_value
            matrix[j, i] = insight.correlation_value
            significance_matrix[i, j] = insight.significance
            significance_matrix[j, i] = insight.significance
            
        return {
            'matrix': matrix,
            'significance': significance_matrix,
            'metrics': metrics,
            'style': self.style_manager.get_correlation_matrix_style(),
            'wsj_annotations': self._generate_matrix_annotations(insights)
        }
```

### WSJ Design Principles for Correlation Visualization
- **Clear Matrix Layout**: Easy-to-read correlation matrix with proper labeling
- **Significance Indicators**: Visual cues for statistical confidence (**, *, NS)
- **Color Coding**: Consistent warm palette for correlation strength
- **Progressive Disclosure**: Matrix overview → individual correlation details → raw data
- **Smart Annotations**: Key correlations highlighted with context
- **Accessibility**: High contrast, screen reader compatible, keyboard navigation
        
    def discover_correlations(self, metrics: List[str], 
                            max_lag_days: int = 7) -> List[CorrelationInsight]:
        """Find all significant correlations between metrics"""
        pass
        
    def calculate_lag_correlations(self, metric1: str, metric2: str,
                                 max_lag: int = 7) -> Dict[int, float]:
        """Calculate correlations at different time lags"""
        pass
        
    def conditional_correlations(self, metric1: str, metric2: str,
                               conditions: Dict[str, Any]) -> float:
        """Calculate correlations under specific conditions"""
        pass
        
    def generate_insights(self, correlations: pd.DataFrame) -> List[CorrelationInsight]:
        """Generate human-readable insights from correlation matrix"""
        pass
        
    def create_correlation_network(self, threshold: float = 0.3) -> nx.Graph:
        """Build network graph of significant correlations"""
        pass
```

## Notes
- Focus on clinically and behaviorally meaningful correlations
- Provide clear explanations of correlation vs causation
- Consider seasonal and cyclical patterns in correlation analysis
- Handle multicollinearity and confounding variables appropriately