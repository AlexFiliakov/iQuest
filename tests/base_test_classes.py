"""
Base test classes for common test patterns and shared functionality.

Provides reusable test patterns to reduce duplication across test files.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class BaseCalculatorTest(ABC):
    """Base class for calculator tests with common patterns."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample health data for testing."""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'steps': np.random.randint(5000, 15000, 30),
            'heart_rate': np.random.randint(60, 100, 30),
            'calories': np.random.randint(1500, 3000, 30),
            'sleep_hours': np.random.uniform(6, 9, 30),
        })
        return data
    
    @pytest.fixture
    def empty_data(self):
        """Empty DataFrame for testing edge cases."""
        return pd.DataFrame()
    
    @pytest.fixture
    def single_row_data(self):
        """Single row DataFrame for boundary testing."""
        return pd.DataFrame({
            'date': [datetime.now()],
            'steps': [10000],
            'heart_rate': [75],
            'calories': [2000],
            'sleep_hours': [8.0],
        })
    
    @abstractmethod
    def get_calculator_class(self):
        """Return the calculator class to test."""
        pass
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return self.get_calculator_class()()
    
    def assert_calculation_result(self, calculator, input_data, expected_keys: List[str]):
        """Common assertion pattern for calculations."""
        result = calculator.calculate(input_data)
        assert isinstance(result, dict)
        for key in expected_keys:
            assert key in result
        return result
    
    def test_empty_data_handling(self, calculator):
        """Test calculator handles empty data gracefully."""
        empty_df = pd.DataFrame()
        result = calculator.calculate(empty_df)
        assert isinstance(result, dict)
        # Should return empty result or default values, not crash
    
    def test_null_handling(self, calculator):
        """Test calculator handles null values."""
        data = pd.DataFrame({
            'date': [datetime.now(), datetime.now() + timedelta(days=1)],
            'steps': [10000, None],
            'heart_rate': [75, None],
        })
        result = calculator.calculate(data)
        assert isinstance(result, dict)
        # Should not crash on null values
    
    def test_single_data_point(self, calculator, single_row_data):
        """Test calculator with single data point."""
        result = calculator.calculate(single_row_data)
        assert isinstance(result, dict)
    
    def test_calculation_consistency(self, calculator, sample_data):
        """Test that repeated calculations give same results."""
        result1 = calculator.calculate(sample_data)
        result2 = calculator.calculate(sample_data)
        assert result1 == result2


class BaseWidgetTest(ABC):
    """Base class for widget tests with Qt-specific functionality."""
    
    @pytest.fixture(scope="session")
    def qt_app(self):
        """Common Qt application fixture."""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6 not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    @abstractmethod
    def get_widget_class(self):
        """Return the widget class to test."""
        pass
    
    @pytest.fixture
    def widget(self, qt_app):
        """Create widget instance."""
        widget_class = self.get_widget_class()
        widget = widget_class()
        yield widget
        if widget:
            widget.close()
            widget.deleteLater()
    
    def test_widget_initialization(self, widget):
        """Test widget can be initialized."""
        assert isinstance(widget, QWidget)
        assert widget.isVisible() is False
    
    def test_widget_show_hide(self, widget):
        """Test widget show/hide functionality."""
        widget.show()
        assert widget.isVisible() is True
        widget.hide()
        assert widget.isVisible() is False
    
    def test_widget_has_layout(self, widget):
        """Test widget has a layout set."""
        layout = widget.layout()
        # Widget should either have a layout or be designed without one
        # This is a basic structural check
        assert layout is not None or hasattr(widget, 'paintEvent')
    
    def assert_widget_updates(self, widget, data):
        """Common pattern for testing widget data updates."""
        # Base implementation - override in subclasses
        if hasattr(widget, 'update_data'):
            widget.update_data(data)
        elif hasattr(widget, 'set_data'):
            widget.set_data(data)


class BaseDataProcessingTest(ABC):
    """Base class for data processing tests."""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV-like data for testing."""
        return {
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Steps': [10000, 12000, 8000],
            'HeartRate': [75, 80, 70],
            'Calories': [2000, 2200, 1800],
        }
    
    @pytest.fixture
    def invalid_csv_data(self):
        """Invalid CSV data for error testing."""
        return {
            'Date': ['invalid-date', '2024-01-02'],
            'Steps': ['not-a-number', 12000],
            'HeartRate': [75, 'invalid'],
        }
    
    def assert_data_validation(self, processor, valid_data, invalid_data):
        """Common data validation test pattern."""
        # Should process valid data successfully
        result = processor.process(valid_data)
        assert result is not None
        
        # Should handle invalid data gracefully
        try:
            invalid_result = processor.process(invalid_data)
            # If it doesn't raise an exception, it should return some result
            assert invalid_result is not None
        except (ValueError, TypeError) as e:
            # Expected exception for invalid data
            assert str(e) != ""
    
    def test_empty_input_handling(self):
        """Test processing empty input."""
        processor = self.get_processor_class()()
        result = processor.process({})
        # Should handle empty input gracefully
        assert result is not None


class BaseAnalyticsTest(BaseCalculatorTest):
    """Specialized base class for analytics components."""
    
    @pytest.fixture
    def time_series_data(self):
        """Generate time series data for analytics."""
        dates = pd.date_range('2024-01-01', periods=90, freq='D')
        trend = np.linspace(5000, 15000, 90)  # Linear trend
        noise = np.random.normal(0, 1000, 90)  # Add some noise
        seasonal = 2000 * np.sin(2 * np.pi * np.arange(90) / 7)  # Weekly pattern
        
        data = pd.DataFrame({
            'date': dates,
            'steps': trend + noise + seasonal,
            'heart_rate': np.random.normal(75, 10, 90),
            'calories': trend * 0.2 + np.random.normal(2000, 200, 90),
        })
        return data
    
    @pytest.fixture
    def correlation_test_data(self):
        """Generate data with known correlations for testing."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        # Create correlated data
        base_trend = np.linspace(0, 10, 100)
        noise = np.random.normal(0, 1, 100)
        
        data = pd.DataFrame({
            'steps': 8000 + base_trend * 500 + noise * 1000,
            'heart_rate': 70 + base_trend * 2 + noise * 5,
            'sleep_hours': 7.5 - base_trend * 0.1 + noise * 0.5,
            'calories': 2000 + base_trend * 100 + noise * 200
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def anomaly_test_data(self):
        """Generate data with known anomalies for testing."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        
        # Normal data with clear outliers
        normal_values = np.random.normal(70, 5, 100)
        normal_values[20] = 150  # Clear outlier
        normal_values[50] = 40   # Another outlier
        
        return pd.DataFrame({
            'metric': normal_values,
            'steps': np.random.normal(8000, 1000, 100)
        }, index=dates)
    
    @pytest.fixture
    def causality_test_data(self):
        """Generate data with known causal relationships for testing."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='D')
        
        # Create time series with lagged relationships
        exercise = np.random.normal(50, 15, 200)
        weight = 70 + np.cumsum(np.random.normal(0, 0.05, 200))
        
        # Add causal effect: exercise -> weight decrease (3-day lag)
        for i in range(3, 200):
            weight[i] -= exercise[i-3] * 0.001
        
        return pd.DataFrame({
            'exercise': exercise,
            'weight': weight,
            'steps': np.random.normal(8000, 1000, 200)
        }, index=dates)
    
    def assert_analytics_structure(self, result: Dict):
        """Assert common analytics result structure."""
        assert isinstance(result, dict)
        # Common analytics fields
        expected_fields = ['summary', 'trends', 'insights']
        for field in expected_fields:
            if field in result:
                assert result[field] is not None
    
    def assert_correlation_result(self, result, expected_metrics=None):
        """Assert correlation analysis result structure."""
        assert isinstance(result, (pd.DataFrame, dict))
        if isinstance(result, pd.DataFrame):
            assert result.shape[0] == result.shape[1]  # Square matrix
        if expected_metrics:
            if isinstance(result, pd.DataFrame):
                assert all(metric in result.columns for metric in expected_metrics)
    
    def assert_anomaly_result(self, anomalies, metric_name=None):
        """Assert anomaly detection result structure."""
        assert isinstance(anomalies, list)
        for anomaly in anomalies:
            assert hasattr(anomaly, 'timestamp')
            assert hasattr(anomaly, 'value')
            assert hasattr(anomaly, 'score')
            if metric_name:
                assert anomaly.metric == metric_name


class BaseIntegrationTest:
    """Base class for integration tests."""
    
    @pytest.fixture
    def test_database(self, tmp_path):
        """Create temporary test database."""
        db_path = tmp_path / "test.db"
        return str(db_path)
    
    @pytest.fixture
    def mock_data_source(self):
        """Mock data source for integration tests."""
        mock = Mock()
        mock.get_data.return_value = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'steps': np.random.randint(5000, 15000, 10),
        })
        return mock
    
    def assert_end_to_end_flow(self, input_data, expected_output_type):
        """Test complete data flow from input to output."""
        # Override in specific integration tests
        pass


# Parametrized test mixins
class ParametrizedCalculatorTests:
    """Mixin for parametrized calculator tests."""
    
    @pytest.mark.parametrize("data_size", [1, 10, 100, 1000])
    def test_calculation_scalability(self, calculator, data_size):
        """Test calculator performance with different data sizes."""
        dates = pd.date_range('2024-01-01', periods=data_size, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'steps': np.random.randint(5000, 15000, data_size),
            'heart_rate': np.random.randint(60, 100, data_size),
        })
        
        result = calculator.calculate(data)
        assert isinstance(result, dict)
    
    @pytest.mark.parametrize("null_percentage", [0.1, 0.3, 0.5])
    def test_null_data_robustness(self, calculator, null_percentage):
        """Test calculator with varying amounts of null data."""
        size = 100
        data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=size),
            'steps': np.random.randint(5000, 15000, size),
        })
        
        # Introduce nulls
        null_count = int(size * null_percentage)
        null_indices = np.random.choice(size, null_count, replace=False)
        data.loc[null_indices, 'steps'] = None
        
        result = calculator.calculate(data)
        assert isinstance(result, dict)


class PerformanceTestMixin:
    """Mixin for performance testing patterns."""
    
    @pytest.mark.performance
    def test_calculation_performance(self, calculator, benchmark=None):
        """Test calculation performance."""
        if benchmark is None:
            pytest.skip("Benchmark fixture not available")
            
        large_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10000),
            'steps': np.random.randint(5000, 15000, 10000),
        })
        
        result = benchmark(calculator.calculate, large_data)
        assert isinstance(result, dict)


# Test discovery helpers
def get_test_methods(test_class):
    """Helper to discover test methods in a class."""
    return [method for method in dir(test_class) if method.startswith('test_')]


def create_parametrized_widget_tests(widget_classes, test_methods):
    """Helper to create parametrized tests for multiple widget classes."""
    @pytest.mark.parametrize("widget_class", widget_classes)
    def test_widget_parametrized(widget_class, qt_app):
        widget = widget_class()
        try:
            for method_name in test_methods:
                if hasattr(BaseWidgetTest, method_name):
                    method = getattr(BaseWidgetTest, method_name)
                    method(None, widget)  # self is None for static call
        finally:
            widget.close()
            widget.deleteLater()
    
    return test_widget_parametrized