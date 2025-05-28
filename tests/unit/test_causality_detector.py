"""
Unit tests for CausalityDetector class.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.analytics.correlation_analyzer import CorrelationAnalyzer
from src.analytics.causality_detector import CausalityDetector


class TestCausalityDetector:
    """Test suite for CausalityDetector class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data with known causal relationships."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=200, freq='D')
        
        # Create time series with lagged relationships
        base_series = np.random.normal(0, 1, 200)
        
        # Exercise causes weight loss (with 3-day lag)
        exercise = np.random.normal(50, 15, 200)
        weight = 70 + np.cumsum(np.random.normal(0, 0.05, 200))
        
        # Add causal effect: more exercise -> weight decrease (lagged)
        for i in range(3, 200):
            weight[i] -= exercise[i-3] * 0.001
        
        # Sleep affects heart rate next day
        sleep_hours = np.random.normal(7.5, 1, 200)
        heart_rate = np.random.normal(70, 8, 200)
        
        for i in range(1, 200):
            heart_rate[i] += (7.5 - sleep_hours[i-1]) * 2  # Poor sleep -> higher HR
        
        # Steps and calories (immediate relationship)
        steps = np.random.normal(8000, 2000, 200)
        calories = 1800 + steps * 0.05 + np.random.normal(0, 100, 200)
        
        data = pd.DataFrame({
            'exercise_minutes': exercise,
            'weight': weight,
            'sleep_hours': sleep_hours,
            'heart_rate': heart_rate,
            'steps': steps,
            'calories': calories
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def analyzer(self, sample_data):
        """Create CorrelationAnalyzer instance."""
        return CorrelationAnalyzer(sample_data)
    
    @pytest.fixture
    def detector(self, analyzer):
        """Create CausalityDetector instance."""
        return CausalityDetector(analyzer)
    
    def test_initialization(self, analyzer):
        """Test causality detector initialization."""
        detector = CausalityDetector(analyzer)
        
        assert detector.analyzer == analyzer
        assert detector.causality_threshold == 0.05
        assert detector.correlation_threshold == 0.3
        assert detector.causality_cache == {}
        assert detector.network_cache == {}
    
    def test_initialization_custom_thresholds(self, analyzer):
        """Test initialization with custom thresholds."""
        detector = CausalityDetector(
            analyzer, 
            causality_threshold=0.01,
            correlation_threshold=0.5
        )
        
        assert detector.causality_threshold == 0.01
        assert detector.correlation_threshold == 0.5
    
    @patch('src.analytics.causality_detector.grangercausalitytests')
    def test_granger_causality_test_success(self, mock_granger, detector):
        """Test successful Granger causality test."""
        # Mock statsmodels response
        mock_result = {
            1: [
                {'ssr_ftest': (5.2, 0.02)},  # F-stat, p-value
                [Mock(aic=100.0, bic=105.0)]
            ],
            2: [
                {'ssr_ftest': (3.8, 0.05)},
                [Mock(aic=102.0, bic=108.0)]
            ]
        }
        mock_granger.return_value = mock_result
        
        result = detector.granger_causality_test('steps', 'calories', max_lag=2)
        
        assert result['cause'] == 'steps'
        assert result['effect'] == 'calories'
        assert len(result['lags']) == 2
        assert len(result['p_values']) == 2
        assert result['optimal_lag'] == 1  # Better AIC
        assert result['is_causal'] == True  # p < 0.05
        
        # Check caching
        assert 'steps_calories_2' in detector.causality_cache
    
    def test_granger_causality_invalid_metrics(self, detector):
        """Test Granger causality with invalid metric names."""
        with pytest.raises(ValueError, match="Metrics must be numeric"):
            detector.granger_causality_test('invalid_metric', 'calories')
    
    def test_granger_causality_insufficient_data(self, detector):
        """Test Granger causality with insufficient data."""
        # Create small dataset
        small_data = detector.analyzer.data.head(10)
        detector.analyzer.data = small_data
        
        result = detector.granger_causality_test('steps', 'calories', min_periods=50)
        
        assert result['is_causal'] == False
        assert result['sample_size'] == 0
        assert len(result['lags']) == 0
    
    @patch('src.analytics.causality_detector.grangercausalitytests')
    def test_granger_causality_test_failure(self, mock_granger, detector):
        """Test Granger causality test failure handling."""
        mock_granger.side_effect = Exception("Statsmodels error")
        
        result = detector.granger_causality_test('steps', 'calories')
        
        assert result['is_causal'] == False
        assert result['cause'] == ''
        assert result['effect'] == ''
    
    def test_bidirectional_causality_test(self, detector):
        """Test bidirectional causality analysis."""
        # Mock the Granger causality results
        with patch.object(detector, 'granger_causality_test') as mock_granger:
            mock_granger.side_effect = [
                {'is_causal': True, 'optimal_p_value': 0.01},   # steps -> calories
                {'is_causal': False, 'optimal_p_value': 0.8}    # calories -> steps
            ]
            
            result = detector.bidirectional_causality_test('steps', 'calories')
            
            assert result['relationship_type'] == 'unidirectional_1_to_2'
            assert result['bidirectional'] == False
            assert result['strongest_direction'] == 'steps'
    
    def test_bidirectional_causality_feedback_loop(self, detector):
        """Test detection of bidirectional causality (feedback loop)."""
        with patch.object(detector, 'granger_causality_test') as mock_granger:
            mock_granger.side_effect = [
                {'is_causal': True, 'optimal_p_value': 0.01},   # metric1 -> metric2
                {'is_causal': True, 'optimal_p_value': 0.02}    # metric2 -> metric1
            ]
            
            result = detector.bidirectional_causality_test('metric1', 'metric2')
            
            assert result['relationship_type'] == 'feedback_loop'
            assert result['bidirectional'] == True
    
    def test_bidirectional_causality_no_causality(self, detector):
        """Test no causality detected."""
        with patch.object(detector, 'granger_causality_test') as mock_granger:
            mock_granger.side_effect = [
                {'is_causal': False, 'optimal_p_value': 0.8},
                {'is_causal': False, 'optimal_p_value': 0.9}
            ]
            
            result = detector.bidirectional_causality_test('metric1', 'metric2')
            
            assert result['relationship_type'] == 'no_causality'
            assert result['bidirectional'] == False
    
    def test_feedback_loops_detection_empty(self, detector):
        """Test feedback loop detection with no relationships."""
        with patch.object(detector, 'granger_causality_test') as mock_granger:
            mock_granger.return_value = {'is_causal': False}
            
            feedback_loops = detector.detect_feedback_loops(min_correlation=0.1)
            
            assert isinstance(feedback_loops, list)
            assert len(feedback_loops) == 0
    
    def test_feedback_loops_detection_with_cycles(self, detector):
        """Test feedback loop detection with actual cycles."""
        # Mock significant correlations and causality
        with patch.object(detector.analyzer.data, 'corr') as mock_corr:
            with patch.object(detector, 'granger_causality_test') as mock_granger:
                # Mock correlations above threshold
                mock_corr.return_value = 0.5
                
                # Mock causality results
                mock_granger.return_value = {
                    'is_causal': True,
                    'optimal_p_value': 0.01,
                    'optimal_lag': 1
                }
                
                feedback_loops = detector.detect_feedback_loops(min_correlation=0.3)
                
                assert isinstance(feedback_loops, list)
                # Should be sorted by strength
                if feedback_loops:
                    assert all('metrics' in loop for loop in feedback_loops)
                    assert all('strength' in loop for loop in feedback_loops)
                    assert all('edges' in loop for loop in feedback_loops)
    
    def test_calculate_loop_strength(self, detector):
        """Test loop strength calculation."""
        import networkx as nx
        
        # Create test graph
        G = nx.DiGraph()
        G.add_edge('A', 'B', correlation=0.6)
        G.add_edge('B', 'C', correlation=0.8)
        G.add_edge('C', 'A', correlation=0.5)
        
        cycle = ['A', 'B', 'C']
        strength = detector._calculate_loop_strength(G, cycle)
        
        # Should be geometric mean of absolute correlations
        expected = (0.6 * 0.8 * 0.5) ** (1/3)
        assert abs(strength - expected) < 0.001
    
    def test_calculate_loop_strength_empty(self, detector):
        """Test loop strength with empty cycle."""
        import networkx as nx
        
        G = nx.DiGraph()
        strength = detector._calculate_loop_strength(G, [])
        
        assert strength == 0.0
    
    def test_calculate_loop_significance(self, detector):
        """Test loop significance calculation."""
        import networkx as nx
        
        # Create test graph with p-values
        G = nx.DiGraph()
        G.add_edge('A', 'B', p_value=0.01)
        G.add_edge('B', 'C', p_value=0.03)
        G.add_edge('C', 'A', p_value=0.02)
        
        cycle = ['A', 'B', 'C']
        significance = detector._calculate_loop_significance(G, cycle)
        
        # Should be mean of p-values
        expected = (0.01 + 0.03 + 0.02) / 3
        assert abs(significance - expected) < 0.001
    
    def test_identify_intervention_points(self, detector):
        """Test intervention point identification."""
        import networkx as nx
        
        # Create test graph
        G = nx.DiGraph()
        G.add_edge('A', 'B')
        G.add_edge('B', 'C')
        G.add_edge('C', 'A')
        G.add_edge('D', 'B')  # B has higher connectivity
        
        cycle = ['A', 'B', 'C']
        intervention_points = detector._identify_intervention_points(G, cycle)
        
        assert len(intervention_points) == 3
        assert all('metric' in point for point in intervention_points)
        assert all('intervention_score' in point for point in intervention_points)
        
        # Should be sorted by intervention score (B should be highest)
        assert intervention_points[0]['metric'] == 'B'
    
    def test_analyze_causal_network(self, detector):
        """Test comprehensive causal network analysis."""
        with patch.object(detector, 'bidirectional_causality_test') as mock_bidirectional:
            with patch.object(detector, 'detect_feedback_loops') as mock_feedback:
                # Mock bidirectional test results
                mock_bidirectional.return_value = {
                    'causality_1_to_2': {'is_causal': True, 'optimal_p_value': 0.01, 'optimal_lag': 1},
                    'causality_2_to_1': {'is_causal': False, 'optimal_p_value': 0.8, 'optimal_lag': 1}
                }
                
                # Mock correlation
                with patch.object(detector.analyzer.data, 'corr') as mock_corr:
                    mock_corr.return_value = 0.5
                    
                    mock_feedback.return_value = []
                    
                    network_analysis = detector.analyze_causal_network(min_correlation=0.3)
                    
                    assert 'nodes' in network_analysis
                    assert 'edges' in network_analysis
                    assert 'density' in network_analysis
                    assert 'causal_relationships' in network_analysis
                    assert 'feedback_loops' in network_analysis
                    assert 'centrality_measures' in network_analysis
    
    def test_get_causality_summary(self, detector):
        """Test causality summary generation."""
        with patch.object(detector, 'detect_feedback_loops') as mock_feedback:
            with patch.object(detector, 'analyze_causal_network') as mock_network:
                # Mock feedback loops
                mock_feedback.return_value = [
                    {
                        'metrics': ['A', 'B'],
                        'strength': 0.8,
                        'intervention_points': [
                            {'metric': 'A', 'reasoning': 'High connectivity'}
                        ]
                    }
                ]
                
                # Mock network analysis
                mock_network.return_value = {
                    'causal_relationships': [
                        {'cause': 'A', 'effect': 'B'},
                        {'cause': 'B', 'effect': 'A'}
                    ],
                    'density': 0.5,
                    'centrality_measures': {
                        'out_degree': {'A': 2, 'B': 1},
                        'in_degree': {'A': 1, 'B': 2},
                        'pagerank': {'A': 0.6, 'B': 0.4}
                    }
                }
                
                summary = detector.get_causality_summary()
                
                assert 'total_metrics' in summary
                assert 'causal_relationships' in summary
                assert 'relationship_breakdown' in summary
                assert 'most_influential_metrics' in summary
                assert 'strongest_feedback_loops' in summary
                assert 'intervention_recommendations' in summary
    
    def test_most_influential_metrics(self, detector):
        """Test identification of most influential metrics."""
        network_analysis = {
            'centrality_measures': {
                'out_degree': {'A': 2, 'B': 1, 'C': 0},
                'in_degree': {'A': 0, 'B': 1, 'C': 2},
                'pagerank': {'A': 0.5, 'B': 0.3, 'C': 0.2}
            }
        }
        
        # Mock numeric columns
        detector.analyzer.numeric_columns = ['A', 'B', 'C']
        
        influential = detector._get_most_influential_metrics(network_analysis)
        
        assert len(influential) <= 5
        assert all('metric' in m for m in influential)
        assert all('influence_score' in m for m in influential)
        
        # Should be sorted by influence score
        if len(influential) > 1:
            scores = [m['influence_score'] for m in influential]
            assert scores == sorted(scores, reverse=True)
    
    def test_intervention_recommendations(self, detector):
        """Test intervention recommendations generation."""
        feedback_loops = [
            {
                'metrics': ['A', 'B', 'C'],
                'strength': 0.8,
                'intervention_points': [
                    {
                        'metric': 'B',
                        'reasoning': 'High connectivity node'
                    }
                ]
            }
        ]
        
        recommendations = detector._get_intervention_recommendations(feedback_loops)
        
        assert len(recommendations) <= 3
        if recommendations:
            assert all('loop_metrics' in r for r in recommendations)
            assert all('recommended_intervention_metric' in r for r in recommendations)
            assert all('intervention_reasoning' in r for r in recommendations)
    
    def test_empty_causality_result(self, detector):
        """Test empty causality result structure."""
        empty_result = detector._empty_causality_result()
        
        required_keys = [
            'cause', 'effect', 'lags', 'p_values', 'f_statistics',
            'aic_scores', 'bic_scores', 'significant', 'optimal_lag',
            'optimal_p_value', 'is_causal', 'sample_size', 'data_span_days'
        ]
        
        for key in required_keys:
            assert key in empty_result
        
        assert empty_result['is_causal'] == False
        assert empty_result['sample_size'] == 0


class TestCausalityDetectorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_with_minimal_data(self):
        """Test with minimal data that might cause issues."""
        # Create very small dataset
        data = pd.DataFrame({
            'metric1': [1, 2, 3],
            'metric2': [2, 4, 6]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        analyzer = CorrelationAnalyzer(data)
        detector = CausalityDetector(analyzer)
        
        # Should handle gracefully
        result = detector.granger_causality_test('metric1', 'metric2')
        assert not result['is_causal']  # Insufficient data
    
    def test_with_identical_metrics(self):
        """Test causality detection with identical metrics."""
        data = pd.DataFrame({
            'metric1': np.random.normal(0, 1, 100),
            'metric2': np.random.normal(0, 1, 100)
        }, index=pd.date_range('2023-01-01', periods=100))
        
        # Make metric2 identical to metric1
        data['metric2'] = data['metric1']
        
        analyzer = CorrelationAnalyzer(data)
        detector = CausalityDetector(analyzer)
        
        # Test should handle perfect correlation
        with patch('src.analytics.causality_detector.grangercausalitytests') as mock_granger:
            mock_granger.side_effect = Exception("Perfect correlation issue")
            
            result = detector.granger_causality_test('metric1', 'metric2')
            assert not result['is_causal']


if __name__ == "__main__":
    pytest.main([__file__])