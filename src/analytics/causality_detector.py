"""
Causality Detection Engine for Apple Health Monitor
Implements Granger causality tests, feedback loop detection, and causal network analysis.
"""

import pandas as pd
import numpy as np
import networkx as nx
from scipy.stats import pearsonr
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from typing import Dict, List, Tuple, Optional, Any
import warnings
import logging
from .correlation_analyzer import CorrelationAnalyzer

logger = logging.getLogger(__name__)


class CausalityDetector:
    """
    Advanced causality detection engine for identifying causal relationships,
    feedback loops, and intervention points in health metrics.
    """
    
    def __init__(self, analyzer: CorrelationAnalyzer, 
                 causality_threshold: float = 0.05,
                 correlation_threshold: float = 0.3):
        """
        Initialize causality detector.
        
        Args:
            analyzer: CorrelationAnalyzer instance with loaded data
            causality_threshold: P-value threshold for Granger causality
            correlation_threshold: Minimum correlation for network edges
        """
        self.analyzer = analyzer
        self.causality_threshold = causality_threshold
        self.correlation_threshold = correlation_threshold
        self.causality_cache = {}
        self.network_cache = {}
        
        # Suppress statsmodels warnings for cleaner output
        warnings.filterwarnings('ignore', category=UserWarning, module='statsmodels')
    
    def granger_causality_test(self, cause: str, effect: str, 
                             max_lag: int = 10, 
                             min_periods: int = 50) -> Dict[str, Any]:
        """
        Perform Granger causality test to determine if one metric causes another.
        
        Args:
            cause: Name of the potential causal metric
            effect: Name of the effect metric
            max_lag: Maximum lag to test
            min_periods: Minimum observations required
            
        Returns:
            Dictionary with causality test results
        """
        cache_key = f"{cause}_{effect}_{max_lag}"
        if cache_key in self.causality_cache:
            return self.causality_cache[cache_key]
        
        # Validate inputs
        if cause not in self.analyzer.numeric_columns or effect not in self.analyzer.numeric_columns:
            raise ValueError(f"Metrics must be numeric: {self.analyzer.numeric_columns}")
        
        # Prepare data
        data = pd.DataFrame({
            'effect': self.analyzer.data[effect],
            'cause': self.analyzer.data[cause]
        }).dropna()
        
        if len(data) < min_periods:
            logger.warning(f"Insufficient data for Granger causality test: {len(data)} < {min_periods}")
            return self._empty_causality_result()
        
        try:
            # Run Granger causality tests for different lags
            results = grangercausalitytests(
                data[['effect', 'cause']], 
                maxlag=max_lag, 
                verbose=False
            )
            
            # Extract results for each lag
            causality_results = {
                'cause': cause,
                'effect': effect,
                'lags': [],
                'p_values': [],
                'f_statistics': [],
                'aic_scores': [],
                'bic_scores': [],
                'significant': [],
                'test_name': 'granger_causality'
            }
            
            for lag, result in results.items():
                # Extract F-test results
                f_test = result[0]['ssr_ftest']
                p_value = f_test[1]
                f_stat = f_test[0]
                
                # Extract information criteria
                aic = result[1][0].aic
                bic = result[1][0].bic
                
                causality_results['lags'].append(lag)
                causality_results['p_values'].append(p_value)
                causality_results['f_statistics'].append(f_stat)
                causality_results['aic_scores'].append(aic)
                causality_results['bic_scores'].append(bic)
                causality_results['significant'].append(p_value < self.causality_threshold)
            
            # Find optimal lag (best AIC)
            if causality_results['aic_scores']:
                optimal_lag_idx = np.argmin(causality_results['aic_scores'])
                causality_results['optimal_lag'] = causality_results['lags'][optimal_lag_idx]
                causality_results['optimal_p_value'] = causality_results['p_values'][optimal_lag_idx]
                causality_results['is_causal'] = causality_results['significant'][optimal_lag_idx]
            else:
                causality_results['optimal_lag'] = 1
                causality_results['optimal_p_value'] = 1.0
                causality_results['is_causal'] = False
            
            # Add metadata
            causality_results['sample_size'] = len(data)
            causality_results['data_span_days'] = (data.index.max() - data.index.min()).days
            
            self.causality_cache[cache_key] = causality_results
            return causality_results
            
        except Exception as e:
            logger.error(f"Granger causality test failed for {cause}->{effect}: {e}")
            return self._empty_causality_result()
    
    def _empty_causality_result(self) -> Dict[str, Any]:
        """Return empty causality result structure."""
        return {
            'cause': '',
            'effect': '',
            'lags': [],
            'p_values': [],
            'f_statistics': [],
            'aic_scores': [],
            'bic_scores': [],
            'significant': [],
            'optimal_lag': 1,
            'optimal_p_value': 1.0,
            'is_causal': False,
            'sample_size': 0,
            'data_span_days': 0,
            'test_name': 'granger_causality'
        }
    
    def bidirectional_causality_test(self, metric1: str, metric2: str, 
                                   max_lag: int = 10) -> Dict[str, Any]:
        """
        Test for bidirectional causality between two metrics.
        
        Args:
            metric1: First metric name
            metric2: Second metric name
            max_lag: Maximum lag to test
            
        Returns:
            Dictionary with bidirectional causality results
        """
        # Test both directions
        causality_1_to_2 = self.granger_causality_test(metric1, metric2, max_lag)
        causality_2_to_1 = self.granger_causality_test(metric2, metric1, max_lag)
        
        # Determine relationship type
        causal_1_to_2 = causality_1_to_2['is_causal']
        causal_2_to_1 = causality_2_to_1['is_causal']
        
        if causal_1_to_2 and causal_2_to_1:
            relationship_type = "feedback_loop"
        elif causal_1_to_2:
            relationship_type = "unidirectional_1_to_2"
        elif causal_2_to_1:
            relationship_type = "unidirectional_2_to_1"
        else:
            relationship_type = "no_causality"
        
        return {
            'metric1': metric1,
            'metric2': metric2,
            'relationship_type': relationship_type,
            'causality_1_to_2': causality_1_to_2,
            'causality_2_to_1': causality_2_to_1,
            'bidirectional': causal_1_to_2 and causal_2_to_1,
            'strongest_direction': metric1 if (causal_1_to_2 and 
                                            causality_1_to_2['optimal_p_value'] < 
                                            causality_2_to_1['optimal_p_value']) else metric2
        }
    
    def detect_feedback_loops(self, min_correlation: float = None, 
                            max_lag: int = 5) -> List[Dict[str, Any]]:
        """
        Detect circular dependencies (feedback loops) between metrics.
        
        Args:
            min_correlation: Minimum correlation threshold (uses class default if None)
            max_lag: Maximum lag for causality tests
            
        Returns:
            List of detected feedback loops with metadata
        """
        if min_correlation is None:
            min_correlation = self.correlation_threshold
        
        cache_key = f"feedback_loops_{min_correlation}_{max_lag}"
        if cache_key in self.network_cache:
            return self.network_cache[cache_key]
        
        # Build directed graph based on significant correlations and causality
        G = nx.DiGraph()
        
        # Add all metrics as nodes
        for metric in self.analyzer.numeric_columns:
            G.add_node(metric)
        
        # Add edges based on causality tests
        logger.info(f"Testing causality for {len(self.analyzer.numeric_columns)} metrics...")
        
        for i, metric1 in enumerate(self.analyzer.numeric_columns):
            for j, metric2 in enumerate(self.analyzer.numeric_columns):
                if i != j:
                    # Check correlation first (faster)
                    try:
                        corr = self.analyzer.data[metric1].corr(self.analyzer.data[metric2])
                        if abs(corr) >= min_correlation:
                            # Test causality
                            causality = self.granger_causality_test(metric1, metric2, max_lag)
                            
                            if causality['is_causal']:
                                G.add_edge(
                                    metric1, 
                                    metric2, 
                                    correlation=corr,
                                    p_value=causality['optimal_p_value'],
                                    lag=causality['optimal_lag']
                                )
                    except Exception as e:
                        logger.warning(f"Failed causality test {metric1}->{metric2}: {e}")
                        continue
        
        # Find cycles (feedback loops)
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception as e:
            logger.error(f"Failed to find cycles in causality graph: {e}")
            cycles = []
        
        # Analyze feedback loops
        feedback_loops = []
        for cycle in cycles:
            if len(cycle) >= 2:  # At least a 2-node cycle
                loop_strength = self._calculate_loop_strength(G, cycle)
                loop_significance = self._calculate_loop_significance(G, cycle)
                
                feedback_loops.append({
                    'metrics': cycle,
                    'length': len(cycle),
                    'strength': loop_strength,
                    'significance': loop_significance,
                    'edges': [(cycle[i], cycle[(i+1) % len(cycle)]) for i in range(len(cycle))],
                    'edge_data': [G.get_edge_data(cycle[i], cycle[(i+1) % len(cycle)]) 
                                for i in range(len(cycle))],
                    'intervention_points': self._identify_intervention_points(G, cycle)
                })
        
        # Sort by loop strength
        feedback_loops.sort(key=lambda x: x['strength'], reverse=True)
        
        self.network_cache[cache_key] = feedback_loops
        return feedback_loops
    
    def _calculate_loop_strength(self, graph: nx.DiGraph, cycle: List[str]) -> float:
        """Calculate the strength of a feedback loop."""
        if len(cycle) < 2:
            return 0.0
        
        correlations = []
        for i in range(len(cycle)):
            source = cycle[i]
            target = cycle[(i + 1) % len(cycle)]
            
            edge_data = graph.get_edge_data(source, target)
            if edge_data and 'correlation' in edge_data:
                correlations.append(abs(edge_data['correlation']))
        
        if not correlations:
            return 0.0
        
        # Use geometric mean of absolute correlations
        return float(np.prod(correlations) ** (1.0 / len(correlations)))
    
    def _calculate_loop_significance(self, graph: nx.DiGraph, cycle: List[str]) -> float:
        """Calculate statistical significance of feedback loop."""
        if len(cycle) < 2:
            return 1.0
        
        p_values = []
        for i in range(len(cycle)):
            source = cycle[i]
            target = cycle[(i + 1) % len(cycle)]
            
            edge_data = graph.get_edge_data(source, target)
            if edge_data and 'p_value' in edge_data:
                p_values.append(edge_data['p_value'])
        
        if not p_values:
            return 1.0
        
        # Use Fisher's method to combine p-values
        return float(np.mean(p_values))  # Simplified - could use proper Fisher combination
    
    def _identify_intervention_points(self, graph: nx.DiGraph, cycle: List[str]) -> List[Dict[str, Any]]:
        """Identify optimal intervention points in feedback loop."""
        intervention_points = []
        
        for i, node in enumerate(cycle):
            # Calculate intervention score based on centrality measures
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            
            # Node with highest connectivity is often best intervention point
            intervention_score = in_degree + out_degree
            
            intervention_points.append({
                'metric': node,
                'position_in_cycle': i,
                'intervention_score': intervention_score,
                'in_degree': in_degree,
                'out_degree': out_degree,
                'reasoning': f"High connectivity node (in:{in_degree}, out:{out_degree})"
            })
        
        # Sort by intervention score
        intervention_points.sort(key=lambda x: x['intervention_score'], reverse=True)
        
        return intervention_points
    
    def analyze_causal_network(self, min_correlation: float = None) -> Dict[str, Any]:
        """
        Perform comprehensive causal network analysis.
        
        Args:
            min_correlation: Minimum correlation threshold for edges
            
        Returns:
            Network analysis results with centrality measures and clusters
        """
        if min_correlation is None:
            min_correlation = self.correlation_threshold
        
        # Build causal network
        G = nx.DiGraph()
        
        # Add nodes
        for metric in self.analyzer.numeric_columns:
            G.add_node(metric)
        
        # Add edges based on causality
        causal_relationships = []
        
        for i, metric1 in enumerate(self.analyzer.numeric_columns):
            for j, metric2 in enumerate(self.analyzer.numeric_columns):
                if i < j:  # Test both directions once
                    bidirectional = self.bidirectional_causality_test(metric1, metric2)
                    
                    if bidirectional['causality_1_to_2']['is_causal']:
                        causality = bidirectional['causality_1_to_2']
                        corr = self.analyzer.data[metric1].corr(self.analyzer.data[metric2])
                        
                        if abs(corr) >= min_correlation:
                            G.add_edge(metric1, metric2, 
                                     correlation=corr,
                                     p_value=causality['optimal_p_value'],
                                     lag=causality['optimal_lag'])
                            
                            causal_relationships.append({
                                'cause': metric1,
                                'effect': metric2,
                                'correlation': corr,
                                'p_value': causality['optimal_p_value'],
                                'lag': causality['optimal_lag']
                            })
                    
                    if bidirectional['causality_2_to_1']['is_causal']:
                        causality = bidirectional['causality_2_to_1']
                        corr = self.analyzer.data[metric2].corr(self.analyzer.data[metric1])
                        
                        if abs(corr) >= min_correlation:
                            G.add_edge(metric2, metric1,
                                     correlation=corr,
                                     p_value=causality['optimal_p_value'],
                                     lag=causality['optimal_lag'])
                            
                            causal_relationships.append({
                                'cause': metric2,
                                'effect': metric1,
                                'correlation': corr,
                                'p_value': causality['optimal_p_value'],
                                'lag': causality['optimal_lag']
                            })
        
        # Calculate network metrics
        network_analysis = {
            'nodes': len(G.nodes()),
            'edges': len(G.edges()),
            'density': nx.density(G),
            'is_connected': nx.is_weakly_connected(G),
            'causal_relationships': causal_relationships,
            'feedback_loops': self.detect_feedback_loops(min_correlation),
            'centrality_measures': {},
            'clusters': []
        }
        
        # Calculate centrality measures
        if G.nodes():
            try:
                network_analysis['centrality_measures'] = {
                    'in_degree': dict(G.in_degree()),
                    'out_degree': dict(G.out_degree()),
                    'betweenness': nx.betweenness_centrality(G),
                    'closeness': nx.closeness_centrality(G),
                    'pagerank': nx.pagerank(G)
                }
            except Exception as e:
                logger.warning(f"Failed to calculate centrality measures: {e}")
        
        # Find strongly connected components (clusters)
        try:
            sccs = list(nx.strongly_connected_components(G))
            network_analysis['clusters'] = [
                {'metrics': list(scc), 'size': len(scc)} 
                for scc in sccs if len(scc) > 1
            ]
        except Exception as e:
            logger.warning(f"Failed to find strongly connected components: {e}")
        
        return network_analysis
    
    def get_causality_summary(self) -> Dict[str, Any]:
        """Get summary of all causality analysis results."""
        feedback_loops = self.detect_feedback_loops()
        network_analysis = self.analyze_causal_network()
        
        # Count different types of relationships
        relationship_counts = {
            'unidirectional': 0,
            'bidirectional': 0,
            'feedback_loops': len(feedback_loops),
            'isolated_metrics': 0
        }
        
        for relationship in network_analysis['causal_relationships']:
            # Check if bidirectional relationship exists
            reverse_exists = any(
                r['cause'] == relationship['effect'] and r['effect'] == relationship['cause']
                for r in network_analysis['causal_relationships']
            )
            
            if reverse_exists:
                relationship_counts['bidirectional'] += 1
            else:
                relationship_counts['unidirectional'] += 1
        
        # Count isolated metrics (no causal relationships)
        metrics_with_relationships = set()
        for rel in network_analysis['causal_relationships']:
            metrics_with_relationships.add(rel['cause'])
            metrics_with_relationships.add(rel['effect'])
        
        relationship_counts['isolated_metrics'] = (
            len(self.analyzer.numeric_columns) - len(metrics_with_relationships)
        )
        
        return {
            'total_metrics': len(self.analyzer.numeric_columns),
            'causal_relationships': len(network_analysis['causal_relationships']),
            'relationship_breakdown': relationship_counts,
            'network_density': network_analysis['density'],
            'most_influential_metrics': self._get_most_influential_metrics(network_analysis),
            'strongest_feedback_loops': feedback_loops[:3],  # Top 3
            'intervention_recommendations': self._get_intervention_recommendations(feedback_loops)
        }
    
    def _get_most_influential_metrics(self, network_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify most influential metrics based on centrality measures."""
        if not network_analysis['centrality_measures']:
            return []
        
        centrality = network_analysis['centrality_measures']
        metrics_influence = []
        
        for metric in self.analyzer.numeric_columns:
            influence_score = (
                centrality['out_degree'].get(metric, 0) * 2 +  # Outgoing influence
                centrality['in_degree'].get(metric, 0) +      # Incoming influence
                centrality['pagerank'].get(metric, 0) * 10    # Overall importance
            )
            
            metrics_influence.append({
                'metric': metric,
                'influence_score': influence_score,
                'out_degree': centrality['out_degree'].get(metric, 0),
                'in_degree': centrality['in_degree'].get(metric, 0),
                'pagerank': centrality['pagerank'].get(metric, 0)
            })
        
        # Sort by influence score
        metrics_influence.sort(key=lambda x: x['influence_score'], reverse=True)
        
        return metrics_influence[:5]  # Top 5 most influential
    
    def _get_intervention_recommendations(self, feedback_loops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate intervention recommendations based on feedback loop analysis."""
        recommendations = []
        
        for loop in feedback_loops[:3]:  # Top 3 strongest loops
            if loop['intervention_points']:
                best_intervention = loop['intervention_points'][0]
                
                recommendations.append({
                    'loop_metrics': loop['metrics'],
                    'recommended_intervention_metric': best_intervention['metric'],
                    'intervention_reasoning': best_intervention['reasoning'],
                    'loop_strength': loop['strength'],
                    'expected_impact': "Breaking this feedback loop could disrupt the cycle and allow for targeted improvements."
                })
        
        return recommendations