"""
Basic tests for the health data generator.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from tests.test_data_generator import HealthDataGenerator, HealthDataPatterns


class TestHealthDataPatterns:
    """Test the health data patterns generator."""
    
    @pytest.fixture
    def patterns(self):
        return HealthDataPatterns(seed=42)
    
    def test_steps_pattern_generation(self, patterns):
        """Test steps pattern generation."""
        steps = patterns.generate_steps_pattern(30)
        
        assert len(steps) == 30
        assert all(isinstance(x, (int, np.integer)) for x in steps)
        assert all(x >= 0 for x in steps)
        assert all(x <= 50000 for x in steps)
    
    def test_heart_rate_pattern_generation(self, patterns):
        """Test heart rate pattern generation."""
        hr = patterns.generate_heart_rate_pattern(30)
        
        assert len(hr) == 30
        assert all(isinstance(x, (int, np.integer)) for x in hr)
        assert all(x >= 40 for x in hr)
        assert all(x <= 200 for x in hr)
    
    def test_sleep_pattern_generation(self, patterns):
        """Test sleep pattern generation."""
        sleep = patterns.generate_sleep_pattern(30)
        
        assert len(sleep) == 30
        assert all(isinstance(x, (float, np.floating)) for x in sleep)
        assert all(x >= 2 for x in sleep)
        assert all(x <= 12 for x in sleep)
    
    def test_exercise_pattern_generation(self, patterns):
        """Test exercise pattern generation."""
        exercise = patterns.generate_exercise_pattern(30)
        
        assert len(exercise) == 30
        assert all(isinstance(x, (int, np.integer)) for x in exercise)
        assert all(x >= 0 for x in exercise)
        assert all(x <= 180 for x in exercise)


class TestHealthDataGeneratorBasic:
    """Test the main health data generator."""
    
    @pytest.fixture
    def generator(self):
        return HealthDataGenerator(seed=42)
    
    def test_synthetic_data_generation(self, generator):
        """Test synthetic data generation."""
        data = generator.generate(30)
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 30
        
        # Check required columns
        required_columns = ['date', 'steps', 'heart_rate_avg', 'sleep_hours', 'exercise_minutes']
        for col in required_columns:
            assert col in data.columns
        
        # Check data types
        assert pd.api.types.is_datetime64_any_dtype(data['date'])
        assert pd.api.types.is_numeric_dtype(data['steps'])
        assert pd.api.types.is_numeric_dtype(data['heart_rate_avg'])
        assert pd.api.types.is_numeric_dtype(data['sleep_hours'])
        assert pd.api.types.is_numeric_dtype(data['exercise_minutes'])
    
    def test_edge_cases_generation(self, generator):
        """Test edge cases generation."""
        edge_cases = generator.generate_edge_cases()
        
        assert isinstance(edge_cases, dict)
        assert 'all_zeros' in edge_cases
        assert 'all_nulls' in edge_cases
        assert 'single_point' in edge_cases
        assert 'extreme_values' in edge_cases
        
        # Test all_zeros
        zeros_data = edge_cases['all_zeros']
        assert all(zeros_data['steps'] == 0)
        
        # Test single_point
        single_data = edge_cases['single_point']
        assert len(single_data) == 1
    
    def test_performance_data_generation(self, generator):
        """Test performance data generation."""
        small_data = generator.generate_performance_data('small')
        medium_data = generator.generate_performance_data('medium')
        large_data = generator.generate_performance_data('large')
        
        assert len(small_data) == 1000
        assert len(medium_data) == 10000
        assert len(large_data) == 100000
        
        # All should have same structure
        for data in [small_data, medium_data, large_data]:
            assert isinstance(data, pd.DataFrame)
            assert 'date' in data.columns
            assert 'steps' in data.columns
    
    def test_anonymized_sample_generation(self, generator):
        """Test anonymized sample generation."""
        patterns = {'steps_mean': 8500, 'days': 30}
        data = generator.generate_anonymized_sample(patterns)
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 30
        
        # Should roughly match the target mean
        assert abs(data['steps'].mean() - 8500) < 1000  # Allow some variance
    
    def test_database_data_generation(self, generator):
        """Test database test data generation."""
        db_data = generator.create_sample_datasets()
        
        assert isinstance(db_data, dict)
        assert 'normal_year' in db_data
        assert 'leap_year' in db_data
        assert 'partial_year' in db_data
        
        # Check year lengths
        assert len(db_data['normal_year']) == 365
        assert len(db_data['leap_year']) == 366
        assert len(db_data['partial_year']) == 90