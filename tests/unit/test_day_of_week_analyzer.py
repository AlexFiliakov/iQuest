"""Unit tests for DayOfWeekAnalyzer."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.analytics.day_of_week_analyzer import (
    DayOfWeekAnalyzer, PatternResult, ChiSquareResult, DayMetrics
)


class TestDayOfWeekAnalyzer:
    """Test suite for DayOfWeekAnalyzer."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        # Create data with clear patterns
        dates = []
        values = []
        metric_types = []
        
        # Generate 12 weeks of data
        start_date = datetime(2024, 1, 1)  # Monday
        
        for week in range(12):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                dates.append(current_date)
                
                # Weekend warrior pattern: higher values on weekends
                if day in [5, 6]:  # Saturday, Sunday
                    base_value = 100
                else:
                    base_value = 50
                
                # Add some random variation
                value = base_value + np.random.normal(0, 10)
                values.append(max(0, value))
                metric_types.append('StepCount')
        
        df = pd.DataFrame({
            'date': dates,
            'metric_type': metric_types,
            'value': values,
            'unit': 'count'
        })
        
        return df
    
    @pytest.fixture
    def monday_blues_data(self):
        """Create data with Monday blues pattern."""
        dates = []
        values = []
        metric_types = []
        
        start_date = datetime(2024, 1, 1)  # Monday
        
        for week in range(12):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                dates.append(current_date)
                
                # Monday blues: lower on Monday, gradual improvement
                if day == 0:  # Monday
                    base_value = 30
                elif day < 5:  # Tuesday-Friday
                    base_value = 50 + (day * 5)
                else:  # Weekend
                    base_value = 60
                
                value = base_value + np.random.normal(0, 5)
                values.append(max(0, value))
                metric_types.append('ActiveEnergyBurned')
        
        df = pd.DataFrame({
            'date': dates,
            'metric_type': metric_types,
            'value': values,
            'unit': 'kcal'
        })
        
        return df
    
    @pytest.fixture
    def uniform_data(self):
        """Create data with no day-of-week patterns."""
        dates = []
        values = []
        metric_types = []
        
        start_date = datetime(2024, 1, 1)
        
        for week in range(12):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                dates.append(current_date)
                
                # Uniform distribution across all days
                value = 50 + np.random.normal(0, 5)
                values.append(max(0, value))
                metric_types.append('HeartRate')
        
        df = pd.DataFrame({
            'date': dates,
            'metric_type': metric_types,
            'value': values,
            'unit': 'bpm'
        })
        
        return df
    
    def test_initialization(self, sample_data):
        """Test analyzer initialization."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        assert analyzer.data is not None
        assert 'day_of_week' in analyzer.data.columns
        assert 'day_name' in analyzer.data.columns
        assert 'hour' in analyzer.data.columns
    
    def test_calculate_day_metrics(self, sample_data):
        """Test day metrics calculation."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        metric_data = sample_data[sample_data['metric_type'] == 'StepCount']
        
        day_metrics = analyzer.calculate_day_metrics(metric_data)
        
        # Should have metrics for all 7 days
        assert len(day_metrics) == 7
        
        # Check structure of metrics
        for day, metrics in day_metrics.items():
            assert isinstance(metrics, DayMetrics)
            assert metrics.day_number == day
            assert metrics.day_name in analyzer.DAY_NAMES
            assert metrics.mean > 0
            assert metrics.std >= 0
            assert len(metrics.confidence_interval) == 2
            assert metrics.sample_size > 0
            assert 0 <= metrics.consistency_score <= 1
        
        # Weekend values should be higher
        assert day_metrics[5].mean > day_metrics[0].mean  # Saturday > Monday
        assert day_metrics[6].mean > day_metrics[0].mean  # Sunday > Monday
    
    def test_detect_weekend_warrior(self, sample_data):
        """Test weekend warrior pattern detection."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        metric_data = sample_data[sample_data['metric_type'] == 'StepCount']
        
        pattern = analyzer.detect_weekend_warrior(metric_data)
        
        assert pattern is not None
        assert pattern.pattern_type == 'weekend_warrior'
        assert pattern.confidence > 0.8
        assert 'ratio' in pattern.details
        assert pattern.details['ratio'] > 1.5
    
    def test_detect_monday_blues(self, monday_blues_data):
        """Test Monday blues pattern detection."""
        analyzer = DayOfWeekAnalyzer(monday_blues_data)
        metric_data = monday_blues_data[monday_blues_data['metric_type'] == 'ActiveEnergyBurned']
        
        pattern = analyzer.detect_monday_blues(metric_data)
        
        assert pattern is not None
        assert pattern.pattern_type == 'monday_blues'
        assert pattern.confidence > 0.8
        assert 'ratio' in pattern.details
        assert pattern.details['ratio'] < 0.8
        assert pattern.details['gradual_improvement'] is True
    
    def test_no_patterns_detected(self, uniform_data):
        """Test when no patterns should be detected."""
        analyzer = DayOfWeekAnalyzer(uniform_data)
        metric_data = uniform_data[uniform_data['metric_type'] == 'HeartRate']
        
        patterns = analyzer.detect_all_patterns(metric_data)
        
        # Should detect no or weak patterns
        strong_patterns = [p for p in patterns if p.confidence > 0.5]
        assert len(strong_patterns) == 0
    
    def test_calculate_consistency_scores(self, sample_data):
        """Test consistency score calculation."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        metric_data = sample_data[sample_data['metric_type'] == 'StepCount']
        
        scores = analyzer.calculate_consistency_scores(metric_data)
        
        assert len(scores) == 7
        for day_name, score in scores.items():
            assert day_name in analyzer.DAY_NAMES
            assert 0 <= score <= 1
    
    def test_calculate_habit_strength(self, sample_data):
        """Test habit strength calculation."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        metric_data = sample_data[sample_data['metric_type'] == 'StepCount']
        
        habit_strength = analyzer.calculate_habit_strength(metric_data)
        
        assert 'regularity_score' in habit_strength
        assert 'time_consistency' in habit_strength
        assert 'completion_rate' in habit_strength
        assert 'overall_strength' in habit_strength
        
        # All scores should be between 0 and 100
        for key, value in habit_strength.items():
            assert 0 <= value <= 100
    
    def test_chi_square_test(self, sample_data):
        """Test chi-square test for independence."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        metric_data = sample_data[sample_data['metric_type'] == 'StepCount']
        
        chi_result = analyzer.perform_chi_square_test(metric_data)
        
        assert isinstance(chi_result, ChiSquareResult)
        assert chi_result.statistic >= 0  # Can be 0 if perfectly uniform
        assert 0 <= chi_result.p_value <= 1
        assert chi_result.degrees_of_freedom == 6
        assert isinstance(chi_result.is_significant, bool)
        assert chi_result.interpretation != ""
    
    def test_analyze_metric(self, sample_data):
        """Test complete metric analysis."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        results = analyzer.analyze_metric('StepCount')
        
        assert results['metric_type'] == 'StepCount'
        assert 'day_metrics' in results
        assert 'patterns' in results
        assert 'chi_square' in results
        assert 'consistency_scores' in results
        assert 'habit_strength' in results
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_df = pd.DataFrame(columns=['date', 'metric_type', 'value', 'unit'])
        analyzer = DayOfWeekAnalyzer(empty_df)
        
        results = analyzer.analyze_metric('StepCount')
        assert results == {}
    
    def test_missing_metric_type(self, sample_data):
        """Test handling of missing metric type."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        results = analyzer.analyze_metric('NonExistentMetric')
        assert results == {}
    
    def test_edge_cases(self):
        """Test various edge cases."""
        # Test with single day of data
        single_day_df = pd.DataFrame({
            'date': [datetime(2024, 1, 1)],
            'metric_type': ['StepCount'],
            'value': [1000],
            'unit': ['count']
        })
        
        analyzer = DayOfWeekAnalyzer(single_day_df)
        results = analyzer.analyze_metric('StepCount')
        
        # Should handle gracefully
        assert 'day_metrics' in results
        assert len(results['day_metrics']) <= 1
    
    def test_visualization_methods(self, sample_data):
        """Test that visualization methods don't crash."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        # Test radar chart
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_ax.figure = mock_fig
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            fig = analyzer.create_radar_chart('StepCount')
            assert fig is not None
        
        # Test heatmap
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_ax.figure = mock_fig
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            fig = analyzer.create_heatmap('StepCount')
            assert fig is not None
        
        # Test pattern summary
        patterns = analyzer.detect_all_patterns(
            sample_data[sample_data['metric_type'] == 'StepCount']
        )
        
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_ax.figure = mock_fig
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            fig = analyzer.create_pattern_summary_chart(patterns)
            assert fig is not None
    
    def test_workday_warrior_pattern(self):
        """Test workday warrior pattern detection."""
        # Create data with workday warrior pattern
        dates = []
        values = []
        metric_types = []
        
        start_date = datetime(2024, 1, 1)
        
        for week in range(12):
            for day in range(7):
                current_date = start_date + timedelta(weeks=week, days=day)
                dates.append(current_date)
                
                # Higher values on weekdays
                if day < 5:  # Monday-Friday
                    base_value = 100
                else:  # Weekend
                    base_value = 60
                
                value = base_value + np.random.normal(0, 5)
                values.append(max(0, value))
                metric_types.append('WorkHours')
        
        df = pd.DataFrame({
            'date': dates,
            'metric_type': metric_types,
            'value': values,
            'unit': 'hours'
        })
        
        analyzer = DayOfWeekAnalyzer(df)
        pattern = analyzer.detect_workday_warrior(df)
        
        assert pattern is not None
        assert pattern.pattern_type == 'workday_warrior'
        assert pattern.confidence > 0.8
    
    def test_anomaly_detection(self, sample_data):
        """Test weekday anomaly detection."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        anomalies = analyzer.detect_weekday_anomalies(sample_data, 'StepCount')
        
        # Should have anomaly data for each day
        assert len(anomalies) == 7
        
        # Each day should have a list (even if empty)
        for day, day_anomalies in anomalies.items():
            assert isinstance(day_anomalies, list)
            assert 0 <= day <= 6
    
    def test_custom_patterns(self, sample_data):
        """Test custom pattern functionality."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        # Test adding custom pattern
        def custom_pattern(data):
            # Simple custom pattern: high activity on Tuesday
            tuesday_data = data[data['day_of_week'] == 1]['value']
            other_data = data[data['day_of_week'] != 1]['value']
            
            if tuesday_data.empty or other_data.empty:
                return None
                
            ratio = tuesday_data.mean() / other_data.mean()
            
            if ratio > 1.2:
                return PatternResult(
                    pattern_type='tuesday_boost',
                    confidence=0.8,
                    description='Higher activity on Tuesdays',
                    details={'ratio': ratio}
                )
            return None
        
        analyzer.add_custom_pattern('tuesday_boost', custom_pattern)
        
        # Test detection
        custom_results = analyzer.detect_custom_patterns(sample_data)
        assert isinstance(custom_results, list)
    
    def test_pattern_config_template(self, sample_data):
        """Test pattern configuration template."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        config = analyzer.get_pattern_config_template()
        
        assert 'weekend_warrior_threshold' in config
        assert 'monday_blues_threshold' in config
        assert 'custom_patterns' in config
        assert isinstance(config['custom_patterns'], dict)
    
    def test_animation_support(self, sample_data):
        """Test animation support in radar chart."""
        analyzer = DayOfWeekAnalyzer(sample_data)
        
        # Test that animation parameter doesn't crash
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_ax.figure = mock_fig
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            fig = analyzer.create_radar_chart('StepCount', animate=True)
            assert fig is not None