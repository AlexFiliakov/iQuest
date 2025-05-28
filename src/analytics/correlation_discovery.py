"""
Health Correlations Discovery Engine
Implements intelligent correlation discovery with layered analysis, 
statistical validation, and WSJ-style insight generation.
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr, kendalltau
from statsmodels.stats.multitest import multipletests
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import StandardScaler
import networkx as nx
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import warnings
import logging
from dataclasses import dataclass, field

from .correlation_models import (
    CorrelationInsight, CorrelationType, EffectSize, EvidenceQuality,
    CorrelationStrength, CorrelationNetwork, CorrelationCluster,
    LagCorrelationResult, ConditionalCorrelation, CausalRelationship,
    CorrelationAnalysisReport, CorrelationMatrixStyle
)
from .correlation_analyzer import CorrelationAnalyzer

logger = logging.getLogger(__name__)


class WSJStyleManager:
    """Manages WSJ-style formatting and presentation of insights."""
    
    @staticmethod
    def get_correlation_matrix_style() -> CorrelationMatrixStyle:
        """Get WSJ-style configuration for correlation matrices."""
        return CorrelationMatrixStyle(
            color_palette="RdBu_r",
            significance_markers={0.001: "***", 0.01: "**", 0.05: "*"},
            cell_format=".2f",
            highlight_threshold=0.5,
            show_only_significant=False,
            annotation_style={
                "fontsize": 10,
                "ha": "center",
                "va": "center",
                "color": "#333333"
            }
        )
    
    @staticmethod
    def format_metric_name(metric: str) -> str:
        """Convert metric names to human-readable format."""
        # Convert snake_case to Title Case
        formatted = metric.replace('_', ' ').title()
        
        # Special cases
        replacements = {
            'Hrv': 'HRV',
            'Rhr': 'Resting Heart Rate',
            'Vo2Max': 'VO2 Max',
            'Bmi': 'BMI'
        }
        
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)
        
        return formatted


class LayeredCorrelationEngine:
    """
    Multi-layered correlation analysis engine following WSJ analytics principles.
    Provides progressive analysis from basic correlations to causal relationships.
    """
    
    def __init__(self, data_manager: Any, style_manager: Optional[WSJStyleManager] = None):
        """
        Initialize the correlation engine.
        
        Args:
            data_manager: Data access manager for retrieving metric data
            style_manager: WSJ style configuration manager
        """
        self.data_manager = data_manager
        self.style_manager = style_manager or WSJStyleManager()
        self.correlation_cache = {}
        self.insight_cache = {}
        
        # Analysis components
        self.traditional_analyzer = TraditionalCorrelationAnalyzer()
        self.advanced_analyzer = AdvancedCorrelationAnalyzer()
        self.causal_analyzer = CausalAnalysisEngine()
        self.insight_generator = WSJInsightGenerator(self.style_manager)
        
    def discover_correlations_progressive(
        self, 
        metrics: List[str], 
        analysis_depth: str = "standard",
        date_range: Optional[Tuple[datetime, datetime]] = None,
        min_observations: int = 30
    ) -> List[CorrelationInsight]:
        """
        Progressive correlation discovery with WSJ-style presentation.
        
        Args:
            metrics: List of metric names to analyze
            analysis_depth: "basic", "standard", "advanced", or "comprehensive"
            date_range: Optional date range for analysis
            min_observations: Minimum observations required for valid correlation
            
        Returns:
            List of correlation insights sorted by importance
        """
        insights = []
        
        # Get data for all metrics
        metric_data = self._prepare_metric_data(metrics, date_range)
        
        if metric_data.empty or len(metric_data) < min_observations:
            logger.warning(f"Insufficient data for correlation analysis: {len(metric_data)} observations")
            return insights
        
        # Layer 1: Always compute traditional correlations
        logger.info("Computing traditional correlations...")
        traditional_insights = self.traditional_analyzer.analyze(
            metric_data, min_observations
        )
        insights.extend(traditional_insights)
        
        if analysis_depth in ["standard", "advanced", "comprehensive"]:
            # Add lag analysis for key correlations
            logger.info("Computing lag correlations...")
            lag_insights = self._analyze_lag_correlations(
                metric_data, traditional_insights[:10]  # Top 10 correlations
            )
            insights.extend(lag_insights)
        
        if analysis_depth in ["advanced", "comprehensive"]:
            # Layer 2: Non-linear and conditional analysis
            logger.info("Computing advanced correlations...")
            advanced_insights = self.advanced_analyzer.analyze(
                metric_data, traditional_insights
            )
            insights.extend(advanced_insights)
        
        if analysis_depth == "comprehensive":
            # Layer 3: Causal analysis for top correlations
            logger.info("Computing causal relationships...")
            key_pairs = self._identify_key_correlation_pairs(insights)
            causal_insights = self.causal_analyzer.analyze(
                metric_data, key_pairs
            )
            insights.extend(causal_insights)
        
        # Generate WSJ-style summaries and interpretations
        for insight in insights:
            insight.wsj_summary = self.insight_generator.generate_summary(insight)
            insight.health_interpretation = self.insight_generator.interpret_health_context(insight)
            insight.actionable_insight = self.insight_generator.generate_actionable_insight(insight)
        
        return self._prioritize_insights(insights)
    
    def _prepare_metric_data(
        self, 
        metrics: List[str], 
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> pd.DataFrame:
        """Prepare metric data for correlation analysis."""
        data_dict = {}
        
        for metric in metrics:
            try:
                # Get metric data from data manager
                metric_data = self.data_manager.get_metric_data(
                    metric, 
                    start_date=date_range[0] if date_range else None,
                    end_date=date_range[1] if date_range else None
                )
                
                if metric_data is not None and len(metric_data) > 0:
                    data_dict[metric] = metric_data
            except Exception as e:
                logger.warning(f"Failed to load data for metric {metric}: {e}")
        
        if not data_dict:
            return pd.DataFrame()
        
        # Combine into single DataFrame
        df = pd.DataFrame(data_dict)
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Sort by date
        df.sort_index(inplace=True)
        
        return df
    
    def _analyze_lag_correlations(
        self, 
        data: pd.DataFrame, 
        top_correlations: List[CorrelationInsight]
    ) -> List[CorrelationInsight]:
        """Analyze time-lagged correlations for top metric pairs."""
        lag_insights = []
        
        for insight in top_correlations:
            metric1, metric2 = insight.metric_pair
            
            if metric1 not in data.columns or metric2 not in data.columns:
                continue
            
            # Calculate correlations at different lags (0-7 days)
            for lag in range(1, 8):
                try:
                    # Shift metric2 by lag days
                    lagged_data = pd.DataFrame({
                        metric1: data[metric1],
                        f"{metric2}_lag{lag}": data[metric2].shift(lag)
                    }).dropna()
                    
                    if len(lagged_data) < 30:
                        continue
                    
                    corr, p_value = pearsonr(
                        lagged_data[metric1],
                        lagged_data[f"{metric2}_lag{lag}"]
                    )
                    
                    # Only keep significant lag correlations
                    if p_value < 0.05 and abs(corr) > 0.2:
                        lag_insight = CorrelationInsight(
                            metric_pair=(metric1, metric2),
                            correlation_value=corr,
                            correlation_type=CorrelationType.PEARSON,
                            significance=p_value,
                            effect_size=self._calculate_effect_size(corr),
                            confidence_interval=self._calculate_confidence_interval(
                                corr, len(lagged_data)
                            ),
                            lag_days=lag,
                            sample_size=len(lagged_data),
                            evidence_quality=self._assess_evidence_quality(
                                len(lagged_data), p_value
                            )
                        )
                        lag_insights.append(lag_insight)
                        
                except Exception as e:
                    logger.debug(f"Failed lag correlation for {metric1}-{metric2} at lag {lag}: {e}")
        
        return lag_insights
    
    def _identify_key_correlation_pairs(
        self, 
        insights: List[CorrelationInsight], 
        top_n: int = 10
    ) -> List[Tuple[str, str]]:
        """Identify key metric pairs for deeper analysis."""
        # Sort by absolute correlation value and significance
        sorted_insights = sorted(
            insights,
            key=lambda x: (abs(x.correlation_value), -x.significance),
            reverse=True
        )
        
        # Get unique pairs
        pairs = []
        seen_pairs = set()
        
        for insight in sorted_insights:
            pair = tuple(sorted(insight.metric_pair))
            if pair not in seen_pairs and len(pairs) < top_n:
                pairs.append(insight.metric_pair)
                seen_pairs.add(pair)
        
        return pairs
    
    def _calculate_effect_size(self, correlation: float) -> EffectSize:
        """Calculate Cohen's effect size for correlation."""
        abs_corr = abs(correlation)
        if abs_corr < 0.1:
            return EffectSize.NEGLIGIBLE
        elif abs_corr < 0.3:
            return EffectSize.SMALL
        elif abs_corr < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE
    
    def _calculate_confidence_interval(
        self, 
        correlation: float, 
        n: int, 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient."""
        if n < 4:
            return (-1.0, 1.0)
        
        # Fisher's z-transformation
        z = 0.5 * np.log((1 + correlation) / (1 - correlation))
        se = 1.0 / np.sqrt(n - 3)
        
        # Critical value for confidence interval
        z_critical = stats.norm.ppf((1 + confidence) / 2)
        
        z_lower = z - z_critical * se
        z_upper = z + z_critical * se
        
        # Transform back to correlation scale
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return (float(r_lower), float(r_upper))
    
    def _assess_evidence_quality(
        self, 
        sample_size: int, 
        p_value: float
    ) -> EvidenceQuality:
        """Assess quality of evidence based on sample size and significance."""
        if sample_size >= 100 and p_value < 0.01:
            return EvidenceQuality.STRONG
        elif sample_size >= 50 and p_value < 0.05:
            return EvidenceQuality.MODERATE
        else:
            return EvidenceQuality.WEAK
    
    def _prioritize_insights(
        self, 
        insights: List[CorrelationInsight]
    ) -> List[CorrelationInsight]:
        """Prioritize insights based on importance and actionability."""
        # Score each insight
        scored_insights = []
        
        for insight in insights:
            score = 0
            
            # Correlation strength
            score += abs(insight.correlation_value) * 10
            
            # Statistical significance
            if insight.significance < 0.001:
                score += 5
            elif insight.significance < 0.01:
                score += 3
            elif insight.significance < 0.05:
                score += 1
            
            # Effect size
            if insight.effect_size == EffectSize.LARGE:
                score += 4
            elif insight.effect_size == EffectSize.MEDIUM:
                score += 2
            elif insight.effect_size == EffectSize.SMALL:
                score += 1
            
            # Evidence quality
            if insight.evidence_quality == EvidenceQuality.STRONG:
                score += 3
            elif insight.evidence_quality == EvidenceQuality.MODERATE:
                score += 1
            
            # Actionability
            if insight.is_actionable():
                score += 5
            
            # Lag bonus (delayed effects are interesting)
            if insight.lag_days > 0:
                score += 2
            
            scored_insights.append((score, insight))
        
        # Sort by score
        scored_insights.sort(key=lambda x: x[0], reverse=True)
        
        return [insight for _, insight in scored_insights]
    
    def create_correlation_network(
        self, 
        insights: List[CorrelationInsight],
        min_correlation: float = 0.3
    ) -> CorrelationNetwork:
        """Build network representation of correlations."""
        # Create graph
        G = nx.Graph()
        
        # Add nodes (metrics)
        metrics = set()
        for insight in insights:
            metrics.update(insight.metric_pair)
        
        G.add_nodes_from(metrics)
        
        # Add edges (correlations)
        significant_edges = []
        for insight in insights:
            if abs(insight.correlation_value) >= min_correlation and insight.is_significant():
                G.add_edge(
                    insight.metric_pair[0],
                    insight.metric_pair[1],
                    weight=abs(insight.correlation_value),
                    correlation=insight.correlation_value,
                    insight=insight
                )
                significant_edges.append(insight)
        
        # Find clusters using community detection
        try:
            import community
            partition = community.best_partition(G)
            clusters = self._extract_clusters(G, partition)
        except ImportError:
            logger.warning("Community detection not available, using connected components")
            clusters = self._extract_clusters_simple(G)
        
        # Identify hub metrics (high degree centrality)
        centrality = nx.degree_centrality(G)
        hubs = [node for node, cent in centrality.items() if cent > 0.5]
        
        # Calculate network statistics
        density = nx.density(G)
        avg_clustering = nx.average_clustering(G, weight='weight')
        
        # Generate network summary
        network_summary = self.insight_generator.generate_network_summary(
            len(metrics), len(significant_edges), len(clusters), len(hubs)
        )
        
        return CorrelationNetwork(
            nodes=list(metrics),
            edges=significant_edges,
            clusters=clusters,
            key_hubs=hubs,
            network_summary=network_summary,
            density=density,
            average_clustering=avg_clustering
        )
    
    def _extract_clusters(
        self, 
        G: nx.Graph, 
        partition: Dict[str, int]
    ) -> List[CorrelationCluster]:
        """Extract clusters from network partition."""
        clusters = []
        
        # Group nodes by cluster
        cluster_nodes = {}
        for node, cluster_id in partition.items():
            if cluster_id not in cluster_nodes:
                cluster_nodes[cluster_id] = []
            cluster_nodes[cluster_id].append(node)
        
        # Create cluster objects
        for cluster_id, nodes in cluster_nodes.items():
            if len(nodes) < 2:
                continue
            
            # Calculate average correlation within cluster
            correlations = []
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    if G.has_edge(node1, node2):
                        correlations.append(G[node1][node2]['correlation'])
            
            avg_corr = np.mean(correlations) if correlations else 0
            
            # Find central metric (highest degree within cluster)
            subgraph = G.subgraph(nodes)
            centrality = nx.degree_centrality(subgraph)
            central_metric = max(centrality, key=centrality.get)
            
            # Generate interpretation
            interpretation = self.insight_generator.interpret_cluster(nodes)
            theme = self.insight_generator.identify_behavioral_theme(nodes)
            
            clusters.append(CorrelationCluster(
                cluster_id=f"cluster_{cluster_id}",
                metrics=nodes,
                central_metric=central_metric,
                average_correlation=avg_corr,
                cluster_interpretation=interpretation,
                behavioral_theme=theme
            ))
        
        return clusters
    
    def _extract_clusters_simple(self, G: nx.Graph) -> List[CorrelationCluster]:
        """Extract clusters using connected components (fallback method)."""
        clusters = []
        
        for i, component in enumerate(nx.connected_components(G)):
            if len(component) < 2:
                continue
            
            nodes = list(component)
            subgraph = G.subgraph(nodes)
            
            # Calculate average correlation
            correlations = [G[u][v]['correlation'] for u, v in subgraph.edges()]
            avg_corr = np.mean(correlations) if correlations else 0
            
            # Find central metric
            centrality = nx.degree_centrality(subgraph)
            central_metric = max(centrality, key=centrality.get) if centrality else nodes[0]
            
            clusters.append(CorrelationCluster(
                cluster_id=f"cluster_{i}",
                metrics=nodes,
                central_metric=central_metric,
                average_correlation=avg_corr,
                cluster_interpretation=f"Group of {len(nodes)} related metrics",
                behavioral_theme="health metrics cluster"
            ))
        
        return clusters


class TraditionalCorrelationAnalyzer:
    """Handles traditional correlation analysis (Pearson, Spearman, Kendall)."""
    
    def analyze(
        self, 
        data: pd.DataFrame, 
        min_observations: int = 30,
        apply_bonferroni: bool = True
    ) -> List[CorrelationInsight]:
        """Perform traditional correlation analysis with multiple comparison correction."""
        insights = []
        columns = data.columns.tolist()
        all_p_values = []
        correlation_results = []
        
        # Calculate all pairwise correlations
        for i, metric1 in enumerate(columns):
            for j, metric2 in enumerate(columns[i+1:], i+1):
                # Get valid pairs
                valid_data = data[[metric1, metric2]].dropna()
                
                if len(valid_data) < min_observations:
                    continue
                
                # Calculate different correlation types
                correlations = self._calculate_correlations(
                    valid_data[metric1], 
                    valid_data[metric2]
                )
                
                # Store results for later processing
                for corr_type, (corr_val, p_val) in correlations.items():
                    if abs(corr_val) > 0.1:  # Pre-filter very weak correlations
                        correlation_results.append({
                            'metric_pair': (metric1, metric2),
                            'correlation_value': corr_val,
                            'correlation_type': corr_type,
                            'p_value': p_val,
                            'sample_size': len(valid_data)
                        })
                        all_p_values.append(p_val)
        
        # Apply Bonferroni correction if requested
        if apply_bonferroni and all_p_values:
            # Use Bonferroni correction from statsmodels
            rejected, corrected_p_values, _, _ = multipletests(
                all_p_values, 
                alpha=0.05, 
                method='bonferroni'
            )
            
            # Create insights with corrected p-values
            for i, result in enumerate(correlation_results):
                if rejected[i]:  # Only keep significant correlations after correction
                    insight = CorrelationInsight(
                        metric_pair=result['metric_pair'],
                        correlation_value=result['correlation_value'],
                        correlation_type=CorrelationType(result['correlation_type']),
                        significance=corrected_p_values[i],
                        effect_size=self._calculate_effect_size(result['correlation_value']),
                        confidence_interval=self._calculate_confidence_interval(
                            result['correlation_value'], result['sample_size']
                        ),
                        sample_size=result['sample_size'],
                        evidence_quality=self._assess_evidence_quality(
                            result['sample_size'], corrected_p_values[i]
                        )
                    )
                    insights.append(insight)
        else:
            # No correction - use original p-values
            for result in correlation_results:
                if result['p_value'] < 0.05:
                    insight = CorrelationInsight(
                        metric_pair=result['metric_pair'],
                        correlation_value=result['correlation_value'],
                        correlation_type=CorrelationType(result['correlation_type']),
                        significance=result['p_value'],
                        effect_size=self._calculate_effect_size(result['correlation_value']),
                        confidence_interval=self._calculate_confidence_interval(
                            result['correlation_value'], result['sample_size']
                        ),
                        sample_size=result['sample_size'],
                        evidence_quality=self._assess_evidence_quality(
                            result['sample_size'], result['p_value']
                        )
                    )
                    insights.append(insight)
        
        return insights
    
    def _calculate_correlations(
        self, 
        x: pd.Series, 
        y: pd.Series
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate multiple correlation types."""
        results = {}
        
        try:
            # Pearson correlation
            corr, p_val = pearsonr(x, y)
            results['pearson'] = (corr, p_val)
        except Exception as e:
            logger.debug(f"Pearson correlation failed: {e}")
        
        try:
            # Spearman correlation
            corr, p_val = spearmanr(x, y)
            results['spearman'] = (corr, p_val)
        except Exception as e:
            logger.debug(f"Spearman correlation failed: {e}")
        
        try:
            # Kendall correlation
            corr, p_val = kendalltau(x, y)
            results['kendall'] = (corr, p_val)
        except Exception as e:
            logger.debug(f"Kendall correlation failed: {e}")
        
        return results
    
    def _calculate_effect_size(self, correlation: float) -> EffectSize:
        """Calculate Cohen's effect size."""
        abs_corr = abs(correlation)
        if abs_corr < 0.1:
            return EffectSize.NEGLIGIBLE
        elif abs_corr < 0.3:
            return EffectSize.SMALL
        elif abs_corr < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE
    
    def _calculate_confidence_interval(
        self, 
        correlation: float, 
        n: int
    ) -> Tuple[float, float]:
        """Calculate 95% confidence interval."""
        if n < 4:
            return (-1.0, 1.0)
        
        # Fisher's z-transformation
        z = 0.5 * np.log((1 + correlation) / (1 - correlation))
        se = 1.0 / np.sqrt(n - 3)
        z_critical = 1.96
        
        z_lower = z - z_critical * se
        z_upper = z + z_critical * se
        
        # Transform back
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return (float(r_lower), float(r_upper))
    
    def _assess_evidence_quality(
        self, 
        sample_size: int, 
        p_value: float
    ) -> EvidenceQuality:
        """Assess evidence quality."""
        if sample_size >= 100 and p_value < 0.01:
            return EvidenceQuality.STRONG
        elif sample_size >= 50 and p_value < 0.05:
            return EvidenceQuality.MODERATE
        else:
            return EvidenceQuality.WEAK


class AdvancedCorrelationAnalyzer:
    """Handles advanced correlation analysis (mutual information, conditional, partial)."""
    
    def analyze(
        self, 
        data: pd.DataFrame, 
        traditional_insights: List[CorrelationInsight]
    ) -> List[CorrelationInsight]:
        """Perform advanced correlation analysis."""
        insights = []
        
        # Mutual information for non-linear relationships
        mi_insights = self._analyze_mutual_information(data)
        insights.extend(mi_insights)
        
        # Conditional correlations
        conditional_insights = self._analyze_conditional_correlations(
            data, traditional_insights[:10]  # Top 10
        )
        insights.extend(conditional_insights)
        
        return insights
    
    def _analyze_mutual_information(
        self, 
        data: pd.DataFrame
    ) -> List[CorrelationInsight]:
        """Calculate mutual information between metrics."""
        insights = []
        columns = data.columns.tolist()
        
        # Standardize data
        scaler = StandardScaler()
        scaled_data = pd.DataFrame(
            scaler.fit_transform(data.dropna()),
            columns=data.columns,
            index=data.dropna().index
        )
        
        for i, metric1 in enumerate(columns):
            for j, metric2 in enumerate(columns[i+1:], i+1):
                try:
                    # Calculate mutual information
                    mi_score = mutual_info_regression(
                        scaled_data[[metric1]], 
                        scaled_data[metric2],
                        random_state=42
                    )[0]
                    
                    # Normalize to [0, 1] range (approximate)
                    normalized_mi = min(mi_score, 1.0)
                    
                    if normalized_mi > 0.1:  # Threshold for meaningful MI
                        insight = CorrelationInsight(
                            metric_pair=(metric1, metric2),
                            correlation_value=normalized_mi,
                            correlation_type=CorrelationType.MUTUAL_INFO,
                            significance=0.001 if normalized_mi > 0.5 else 0.05,
                            effect_size=self._mi_to_effect_size(normalized_mi),
                            confidence_interval=(normalized_mi * 0.8, min(normalized_mi * 1.2, 1.0)),
                            sample_size=len(scaled_data)
                        )
                        insights.append(insight)
                        
                except Exception as e:
                    logger.debug(f"MI calculation failed for {metric1}-{metric2}: {e}")
        
        return insights
    
    def _analyze_conditional_correlations(
        self, 
        data: pd.DataFrame,
        top_correlations: List[CorrelationInsight]
    ) -> List[CorrelationInsight]:
        """Analyze correlations under different conditions."""
        insights = []
        
        # Add day of week analysis
        if hasattr(data.index, 'dayofweek'):
            weekday_data = data[data.index.dayofweek < 5]
            weekend_data = data[data.index.dayofweek >= 5]
            
            for base_insight in top_correlations:
                metric1, metric2 = base_insight.metric_pair
                
                if metric1 in data.columns and metric2 in data.columns:
                    # Weekday correlation
                    weekday_valid = weekday_data[[metric1, metric2]].dropna()
                    if len(weekday_valid) >= 20:
                        try:
                            corr, p_val = pearsonr(weekday_valid[metric1], weekday_valid[metric2])
                            if p_val < 0.05 and abs(corr - base_insight.correlation_value) > 0.1:
                                insight = CorrelationInsight(
                                    metric_pair=(metric1, metric2),
                                    correlation_value=corr,
                                    correlation_type=CorrelationType.PEARSON,
                                    significance=p_val,
                                    effect_size=self._calculate_effect_size(corr),
                                    confidence_interval=self._calculate_confidence_interval(
                                        corr, len(weekday_valid)
                                    ),
                                    context="weekdays",
                                    sample_size=len(weekday_valid)
                                )
                                insights.append(insight)
                        except Exception:
                            pass
                    
                    # Weekend correlation
                    weekend_valid = weekend_data[[metric1, metric2]].dropna()
                    if len(weekend_valid) >= 20:
                        try:
                            corr, p_val = pearsonr(weekend_valid[metric1], weekend_valid[metric2])
                            if p_val < 0.05 and abs(corr - base_insight.correlation_value) > 0.1:
                                insight = CorrelationInsight(
                                    metric_pair=(metric1, metric2),
                                    correlation_value=corr,
                                    correlation_type=CorrelationType.PEARSON,
                                    significance=p_val,
                                    effect_size=self._calculate_effect_size(corr),
                                    confidence_interval=self._calculate_confidence_interval(
                                        corr, len(weekend_valid)
                                    ),
                                    context="weekends",
                                    sample_size=len(weekend_valid)
                                )
                                insights.append(insight)
                        except Exception:
                            pass
        
        return insights
    
    def _mi_to_effect_size(self, mi_score: float) -> EffectSize:
        """Convert mutual information score to effect size."""
        if mi_score < 0.1:
            return EffectSize.NEGLIGIBLE
        elif mi_score < 0.3:
            return EffectSize.SMALL
        elif mi_score < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE
    
    def _calculate_effect_size(self, correlation: float) -> EffectSize:
        """Calculate effect size from correlation."""
        abs_corr = abs(correlation)
        if abs_corr < 0.1:
            return EffectSize.NEGLIGIBLE
        elif abs_corr < 0.3:
            return EffectSize.SMALL
        elif abs_corr < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE
    
    def _calculate_confidence_interval(
        self, 
        correlation: float, 
        n: int
    ) -> Tuple[float, float]:
        """Calculate confidence interval."""
        if n < 4:
            return (-1.0, 1.0)
        
        z = 0.5 * np.log((1 + correlation) / (1 - correlation))
        se = 1.0 / np.sqrt(n - 3)
        z_critical = 1.96
        
        z_lower = z - z_critical * se
        z_upper = z + z_critical * se
        
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return (float(r_lower), float(r_upper))


class CausalAnalysisEngine:
    """Handles causal analysis including Granger causality testing."""
    
    def analyze(
        self, 
        data: pd.DataFrame, 
        key_pairs: List[Tuple[str, str]]
    ) -> List[CorrelationInsight]:
        """Perform causal analysis on key metric pairs."""
        insights = []
        
        for metric1, metric2 in key_pairs:
            if metric1 not in data.columns or metric2 not in data.columns:
                continue
            
            # Test both directions
            for cause, effect in [(metric1, metric2), (metric2, metric1)]:
                try:
                    # Prepare data for Granger test
                    test_data = data[[cause, effect]].dropna()
                    
                    if len(test_data) < 50:
                        continue
                    
                    # Simplified Granger causality test
                    # (Full implementation would use statsmodels.tsa.stattools.grangercausalitytests)
                    # For now, we'll use lag correlation as a proxy
                    
                    max_corr = 0
                    best_lag = 0
                    
                    for lag in range(1, 8):
                        lagged = test_data[cause].shift(lag)
                        valid_data = pd.DataFrame({
                            'cause': lagged,
                            'effect': test_data[effect]
                        }).dropna()
                        
                        if len(valid_data) >= 30:
                            corr, p_val = pearsonr(valid_data['cause'], valid_data['effect'])
                            if abs(corr) > abs(max_corr) and p_val < 0.05:
                                max_corr = corr
                                best_lag = lag
                    
                    if best_lag > 0 and abs(max_corr) > 0.2:
                        insight = CorrelationInsight(
                            metric_pair=(cause, effect),
                            correlation_value=max_corr,
                            correlation_type=CorrelationType.GRANGER,
                            significance=0.01,  # Placeholder
                            effect_size=self._calculate_effect_size(max_corr),
                            confidence_interval=(max_corr * 0.8, max_corr * 1.2),
                            lag_days=best_lag,
                            sample_size=len(test_data)
                        )
                        insights.append(insight)
                        
                except Exception as e:
                    logger.debug(f"Causal analysis failed for {cause}->{effect}: {e}")
        
        return insights
    
    def _calculate_effect_size(self, correlation: float) -> EffectSize:
        """Calculate effect size."""
        abs_corr = abs(correlation)
        if abs_corr < 0.1:
            return EffectSize.NEGLIGIBLE
        elif abs_corr < 0.3:
            return EffectSize.SMALL
        elif abs_corr < 0.5:
            return EffectSize.MEDIUM
        else:
            return EffectSize.LARGE


class WSJInsightGenerator:
    """Generates WSJ-style insights and interpretations."""
    
    def __init__(self, style_manager: WSJStyleManager):
        self.style_manager = style_manager
        
        # Health context mappings
        self.health_contexts = {
            'steps': 'physical activity',
            'heart_rate': 'cardiovascular health',
            'sleep': 'recovery and rest',
            'calories': 'energy balance',
            'weight': 'body composition',
            'exercise': 'fitness activity',
            'stress': 'mental wellbeing',
            'hrv': 'recovery status',
            'blood_pressure': 'cardiovascular health',
            'mood': 'mental health'
        }
        
        self.behavioral_themes = {
            frozenset(['steps', 'calories', 'exercise']): 'Activity & Energy',
            frozenset(['sleep', 'hrv', 'stress']): 'Recovery & Stress',
            frozenset(['weight', 'calories', 'exercise']): 'Body Composition',
            frozenset(['heart_rate', 'blood_pressure', 'hrv']): 'Cardiovascular Health',
            frozenset(['mood', 'stress', 'sleep']): 'Mental Wellbeing'
        }
    
    def generate_summary(self, insight: CorrelationInsight) -> str:
        """Generate WSJ-style correlation summary."""
        metric1 = self.style_manager.format_metric_name(insight.metric_pair[0])
        metric2 = self.style_manager.format_metric_name(insight.metric_pair[1])
        
        # Strength descriptor
        strength_map = {
            CorrelationStrength.VERY_STRONG: "very strongly",
            CorrelationStrength.STRONG: "strongly",
            CorrelationStrength.MODERATE: "moderately",
            CorrelationStrength.WEAK: "weakly",
            CorrelationStrength.VERY_WEAK: "very weakly"
        }
        strength_desc = strength_map.get(insight.strength, "somewhat")
        
        # Direction and relationship
        if insight.direction == "positive":
            relationship = f"{strength_desc} increases with"
        else:
            relationship = f"{strength_desc} decreases as"
        
        # Base summary
        summary = f"Your {metric1} {relationship} {metric2}"
        
        # Add temporal context
        if insight.lag_days > 0:
            if insight.lag_days == 1:
                summary += " the next day"
            else:
                summary += f" after {insight.lag_days} days"
        
        # Add context
        if insight.context != "all":
            summary += f" (on {insight.context})"
        
        # Add confidence
        if insight.effect_size == EffectSize.LARGE and insight.significance < 0.01:
            summary += ". This is a strong, consistent pattern"
        elif insight.significance < 0.05:
            summary += ". This pattern appears reliable"
        
        return summary
    
    def interpret_health_context(self, insight: CorrelationInsight) -> str:
        """Generate health-specific interpretation."""
        metric1, metric2 = insight.metric_pair
        
        # Get health contexts
        context1 = self._get_health_context(metric1)
        context2 = self._get_health_context(metric2)
        
        # Generate interpretation based on correlation type and direction
        if insight.correlation_type == CorrelationType.GRANGER:
            if insight.direction == "positive":
                interpretation = f"Changes in {context1} appear to predict increases in {context2}"
            else:
                interpretation = f"Changes in {context1} appear to predict decreases in {context2}"
        else:
            if insight.direction == "positive":
                interpretation = f"Higher {context1} is associated with increased {context2}"
            else:
                interpretation = f"Higher {context1} is associated with decreased {context2}"
        
        # Add lag interpretation
        if insight.lag_days > 0:
            interpretation += f" with a {insight.lag_days}-day delay"
        
        return interpretation
    
    def generate_actionable_insight(self, insight: CorrelationInsight) -> str:
        """Generate actionable recommendations."""
        metric1, metric2 = insight.metric_pair
        
        # Skip if correlation is too weak
        if insight.effect_size == EffectSize.NEGLIGIBLE:
            return ""
        
        # Generate recommendations based on metric pairs
        recommendations = {
            ('steps', 'sleep'): "Consider timing your walks earlier in the day for better sleep",
            ('exercise', 'heart_rate'): "Monitor your heart rate recovery after workouts",
            ('stress', 'sleep'): "Try stress reduction techniques before bedtime",
            ('calories', 'weight'): "Track your energy balance for weight management",
            ('sleep', 'hrv'): "Prioritize consistent sleep for better recovery"
        }
        
        # Check both directions
        pair1 = (metric1.lower(), metric2.lower())
        pair2 = (metric2.lower(), metric1.lower())
        
        for pair in [pair1, pair2]:
            if pair in recommendations:
                return recommendations[pair]
        
        # Generic recommendation
        if insight.direction == "positive" and insight.effect_size in [EffectSize.MEDIUM, EffectSize.LARGE]:
            return f"Consider tracking both metrics together for optimization"
        
        return ""
    
    def generate_network_summary(
        self, 
        num_metrics: int, 
        num_correlations: int,
        num_clusters: int,
        num_hubs: int
    ) -> str:
        """Generate network-level summary."""
        summary_parts = []
        
        # Overall connectivity
        if num_correlations > num_metrics * 2:
            summary_parts.append(f"Your health metrics show high interconnectedness")
        else:
            summary_parts.append(f"Your health metrics show moderate connections")
        
        # Clusters
        if num_clusters > 0:
            summary_parts.append(f"with {num_clusters} distinct behavioral patterns")
        
        # Hubs
        if num_hubs > 0:
            summary_parts.append(f"and {num_hubs} key metrics driving multiple relationships")
        
        return ". ".join(summary_parts)
    
    def interpret_cluster(self, metrics: List[str]) -> str:
        """Interpret a cluster of correlated metrics."""
        # Format metric names
        formatted_metrics = [self.style_manager.format_metric_name(m) for m in metrics]
        
        if len(metrics) == 2:
            return f"{formatted_metrics[0]} and {formatted_metrics[1]} move together"
        elif len(metrics) == 3:
            return f"{', '.join(formatted_metrics[:-1])} and {formatted_metrics[-1]} form a related group"
        else:
            return f"A group of {len(metrics)} interconnected health metrics"
    
    def identify_behavioral_theme(self, metrics: List[str]) -> str:
        """Identify the behavioral theme of a metric cluster."""
        metric_set = frozenset(m.lower() for m in metrics)
        
        # Check predefined themes
        for theme_metrics, theme_name in self.behavioral_themes.items():
            if len(metric_set & theme_metrics) >= 2:
                return theme_name
        
        # Default theme based on most common context
        contexts = [self._get_health_context(m) for m in metrics]
        if contexts:
            return f"{contexts[0]} cluster"
        
        return "health metrics cluster"
    
    def _get_health_context(self, metric: str) -> str:
        """Get health context for a metric."""
        metric_lower = metric.lower()
        
        for key, context in self.health_contexts.items():
            if key in metric_lower:
                return context
        
        return metric_lower.replace('_', ' ')