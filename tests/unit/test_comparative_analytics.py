"""
Unit tests for comparative analytics functionality.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from src.analytics.comparative_analytics import (
    ComparativeAnalyticsEngine, PrivacyManager, InsightsGenerator,
    ComparisonType, PrivacyLevel, ComparisonResult, HistoricalComparison,
    DemographicCohort, SeasonalNorm
)
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator


class TestPrivacyManager:
    """Test privacy management functionality."""
    
    def test_privacy_manager_initialization(self):
        """Test privacy manager initialization."""
        manager = PrivacyManager()
        assert manager.minimum_cohort_size == 50
        assert manager.differential_privacy_epsilon == 1.0
        assert len(manager.permissions) == 0
        
    def test_permission_checking(self):
        """Test permission checking."""
        manager = PrivacyManager()
        
        # No permissions granted initially
        assert not manager.has_permission('demographic_comparison')
        assert not manager.has_permission('peer_group_sharing')
        
        # Grant permission
        manager.permissions['demographic_comparison'] = {
            'granted': True,
            'timestamp': datetime.now()
        }
        
        assert manager.has_permission('demographic_comparison')
        assert not manager.has_permission('peer_group_sharing')
        
    def test_value_anonymization(self):
        """Test value anonymization methods."""
        manager = PrivacyManager()
        
        # Test rounding anonymization (rounds to nearest 10)
        assert manager.anonymize_value(12345, 'rounding') == 12340
        assert manager.anonymize_value(678, 'rounding') == 680
        
        # Test differential privacy adds noise
        original = 1000
        anonymized = manager.anonymize_value(original, 'differential_privacy')
        assert anonymized != original  # Should add noise
        
        # Multiple runs should give different results
        results = [manager.anonymize_value(1000, 'differential_privacy') 
                  for _ in range(10)]
        assert len(set(results)) > 1  # Should have variation


class TestComparativeAnalyticsEngine:
    """Test comparative analytics engine."""
    
    @pytest.fixture
    def mock_calculators(self, mocker):
        """Create mock calculator instances."""
        daily = mocker.Mock(spec=DailyMetricsCalculator)
        weekly = mocker.Mock(spec=WeeklyMetricsCalculator)
        monthly = mocker.Mock(spec=MonthlyMetricsCalculator)
        return daily, weekly, monthly
        
    @pytest.fixture
    def engine(self, mock_calculators):
        """Create engine with mock calculators."""
        daily, weekly, monthly = mock_calculators
        return ComparativeAnalyticsEngine(daily, weekly, monthly)
        
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.daily_calc is not None
        assert engine.weekly_calc is not None
        assert engine.monthly_calc is not None
        assert isinstance(engine.privacy_manager, PrivacyManager)
        assert isinstance(engine.insights_generator, InsightsGenerator)
        
    def test_historical_comparison(self, engine, mock_calculators):
        """Test historical comparison generation."""
        daily_calc, _, _ = mock_calculators
        
        # Mock return values
        mock_stats = MetricStatistics(
            metric_name='steps',
            count=30,
            mean=8000,
            median=7900,
            std=1500,
            min=5000,
            max=12000,
            percentile_25=6500,
            percentile_75=9500,
            percentile_95=11000,
            missing_data_count=0,
            outlier_count=1,
            insufficient_data=False
        )
        
        daily_calc.calculate_statistics.return_value = mock_stats
        
        # Generate comparison
        current_date = datetime.now()
        historical = engine.compare_to_historical('steps', current_date)
        
        # Verify structure
        assert isinstance(historical, HistoricalComparison)
        assert historical.rolling_7_day is not None
        assert historical.rolling_30_day is not None
        assert historical.rolling_90_day is not None
        assert historical.rolling_365_day is not None
        
        # Verify calls
        assert daily_calc.calculate_statistics.call_count >= 4
        
    def test_historical_comparison_trend_detection(self, engine, mock_calculators):
        """Test trend detection in historical comparison."""
        daily_calc, _, _ = mock_calculators
        
        # Mock improving trend
        mock_30_day = MetricStatistics(
            metric_name='steps',
            count=30, mean=9000, median=9000, std=1000,
            min=7000, max=11000, percentile_25=8000,
            percentile_75=10000, percentile_95=10500,
            missing_data_count=0, outlier_count=0,
            insufficient_data=False
        )
        
        mock_90_day = MetricStatistics(
            metric_name='steps',
            count=90, mean=8000, median=8000, std=1000,
            min=6000, max=10000, percentile_25=7000,
            percentile_75=9000, percentile_95=9500,
            missing_data_count=0, outlier_count=0,
            insufficient_data=False
        )
        
        # Set up mock returns
        daily_calc.calculate_statistics.side_effect = [
            mock_30_day,  # Current
            mock_30_day,  # 7-day
            mock_30_day,  # 30-day
            mock_90_day,  # 90-day
            mock_90_day,  # 365-day
            mock_90_day   # Last year
        ]
        
        historical = engine.compare_to_historical('steps', datetime.now())
        
        # Should detect improving trend (9000 > 8000 * 1.05)
        assert historical.trend_direction == "improving"
        
    def test_demographic_comparison_no_permission(self, engine):
        """Test demographic comparison without permission."""
        result = engine.compare_to_demographic('steps', 35, 'male', 'moderately_active')
        assert result is None
        
    def test_demographic_comparison_with_permission(self, engine):
        """Test demographic comparison with permission."""
        # Grant permission
        engine.privacy_manager.permissions['demographic_comparison'] = {
            'granted': True
        }
        
        result = engine.compare_to_demographic('steps', 35, 'male', 'moderately_active')
        
        assert result is not None
        assert result.comparison_type == ComparisonType.DEMOGRAPHIC
        assert result.privacy_level == PrivacyLevel.ANONYMOUS_AGGREGATE
        assert result.percentile is not None
        assert len(result.insights) > 0
        
    def test_seasonal_comparison(self, engine, mock_calculators):
        """Test seasonal comparison."""
        daily_calc, _, _ = mock_calculators
        
        # Mock current stats
        mock_stats = MetricStatistics(
            metric_name='steps',
            count=30, mean=8500, median=8400, std=1200,
            min=6000, max=11000, percentile_25=7500,
            percentile_75=9500, percentile_95=10500,
            missing_data_count=0, outlier_count=0,
            insufficient_data=False
        )
        
        daily_calc.calculate_statistics.return_value = mock_stats
        
        # Test summer comparison
        summer_date = datetime(2024, 7, 15)
        result = engine.compare_to_seasonal('steps', summer_date)
        
        assert result is not None
        assert result.comparison_type == ComparisonType.SEASONAL
        assert result.context == "Typical for July"
        assert len(result.insights) > 0


class TestInsightsGenerator:
    """Test insights generation."""
    
    def test_demographic_insights_generation(self):
        """Test demographic insight messages."""
        generator = InsightsGenerator()
        
        # Test top percentile
        insights = generator.generate_demographic_insights(80)
        assert any("inspiring" in insight for insight in insights)
        assert any("top quarter" in insight for insight in insights)
        
        # Test middle percentile
        insights = generator.generate_demographic_insights(55)
        assert any("great path" in insight for insight in insights)
        
        # Test lower percentile
        insights = generator.generate_demographic_insights(20)
        assert any("journey" in insight or "unique" in insight 
                  for insight in insights)
        assert all("shame" not in insight.lower() for insight in insights)
        
    def test_seasonal_insights(self):
        """Test seasonal insight generation."""
        generator = InsightsGenerator()
        
        seasonal_norm = SeasonalNorm(
            month=7,
            average=9000,
            std_dev=1500,
            percentile_25=7500,
            percentile_75=10500,
            typical_range=(6000, 12000)
        )
        
        # Above average
        insights = generator.generate_seasonal_insights(10000, seasonal_norm)
        assert any("above" in insight for insight in insights)
        
        # Below average
        insights = generator.generate_seasonal_insights(7000, seasonal_norm)
        assert any("seasonal" in insight.lower() for insight in insights)
        
    def test_historical_insights(self):
        """Test historical insight generation."""
        generator = InsightsGenerator()
        
        # Improving trend
        historical = HistoricalComparison(trend_direction="improving")
        insights = generator.generate_historical_insights(historical)
        assert any("improvement" in insight or "trend" in insight 
                  for insight in insights)
        
        # Stable trend
        historical = HistoricalComparison(trend_direction="stable")
        insights = generator.generate_historical_insights(historical)
        assert any("consistency" in insight or "stable" in insight 
                  for insight in insights)
        
        # With personal best
        historical = HistoricalComparison(
            trend_direction="stable",
            personal_best=(datetime.now(), 12500)
        )
        insights = generator.generate_historical_insights(historical)
        assert any("12,500" in insight for insight in insights)


class TestDemographicCohort:
    """Test demographic cohort functionality."""
    
    def test_cohort_validation(self):
        """Test cohort size validation."""
        # Valid cohort
        cohort = DemographicCohort(
            age_range=(30, 34),
            gender="female",
            activity_level="high",
            cohort_size=75,
            stats=MetricStatistics(
                metric_name='steps',
                count=75, mean=9000, median=8800, std=1800,
                min=5000, max=15000, percentile_25=7500,
                percentile_75=10500, percentile_95=13000,
                missing_data_count=0, outlier_count=3,
                insufficient_data=False
            ),
            last_updated=datetime.now()
        )
        
        assert cohort.is_valid_for_comparison
        
        # Invalid cohort (too small)
        small_cohort = DemographicCohort(
            age_range=(30, 34),
            gender="female", 
            activity_level="high",
            cohort_size=25,
            stats=MetricStatistics(
                metric_name='steps',
                count=25, mean=9000, median=8800, std=1800,
                min=5000, max=15000, percentile_25=7500,
                percentile_75=10500, percentile_95=13000,
                missing_data_count=0, outlier_count=1,
                insufficient_data=False
            ),
            last_updated=datetime.now()
        )
        
        assert not small_cohort.is_valid_for_comparison


class TestComparisonResult:
    """Test comparison result structure."""
    
    def test_comparison_result_initialization(self):
        """Test comparison result initialization."""
        result = ComparisonResult(
            comparison_type=ComparisonType.PERSONAL_HISTORICAL,
            current_value=8500,
            comparison_value=8000,
            percentile=65,
            context="30-day average",
            insights=["You're improving!", "Keep it up!"],
            privacy_level=PrivacyLevel.LOCAL_ONLY
        )
        
        assert result.comparison_type == ComparisonType.PERSONAL_HISTORICAL
        assert result.current_value == 8500
        assert result.comparison_value == 8000
        assert result.percentile == 65
        assert result.context == "30-day average"
        assert len(result.insights) == 2
        assert result.privacy_level == PrivacyLevel.LOCAL_ONLY
        
    def test_comparison_result_defaults(self):
        """Test comparison result with defaults."""
        result = ComparisonResult(
            comparison_type=ComparisonType.DEMOGRAPHIC,
            current_value=7000,
            comparison_value=8000
        )
        
        assert result.percentile is None
        assert result.context is None
        assert result.insights == []
        assert result.privacy_level == PrivacyLevel.LOCAL_ONLY

    def test_input_validation(self):
        """Test input validation for comparative analytics engine."""
        # Create mock calculators with proper DataFrame
        test_df = pd.DataFrame({
            'creationDate': pd.date_range('2024-01-01', periods=10),
            'type': ['steps'] * 10,
            'value': range(1000, 1100, 10)
        })
        daily_calc = DailyMetricsCalculator(test_df)
        weekly_calc = WeeklyMetricsCalculator(daily_calc)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        engine = ComparativeAnalyticsEngine(
            daily_calculator=daily_calc,
            weekly_calculator=weekly_calc,
            monthly_calculator=monthly_calc
        )
        
        # Test invalid metric name - should return empty result
        result = engine.compare_to_historical("invalid@metric!", datetime.now())
        assert result is not None  # Returns empty HistoricalComparison
        assert result.rolling_7_day is None
        assert result.rolling_30_day is None
        
        # Test invalid lookback days - should return empty result
        result = engine.compare_to_historical("steps", datetime.now(), lookback_days=5000)
        assert result is not None
        assert result.rolling_7_day is None
        
        # Test invalid age - should return None
        result = engine.compare_to_demographic("steps", age=200)
        assert result is None
        
        # Test invalid gender - should return None
        result = engine.compare_to_demographic("steps", age=30, gender="invalid")
        assert result is None

    def test_secure_random_generation(self):
        """Test that secure random generation is working properly."""
        privacy_manager = PrivacyManager()
        
        # Generate multiple anonymized values
        values = []
        for _ in range(10):
            anonymized = privacy_manager.anonymize_value(100.0, method='differential_privacy')
            values.append(anonymized)
        
        # Check that values are different (randomness working)
        assert len(set(values)) > 1, "Secure random should generate different values"
        
        # Check that values are within reasonable range (differential privacy)
        assert all(50 < v < 150 for v in values), "Values should be within reasonable range"

    def test_error_handling_in_historical_comparison(self):
        """Test error handling when calculators raise exceptions."""
        # Create mock calculator that raises an error
        class ErrorCalculator:
            def calculate_statistics(self, metric, start_date, end_date):
                if metric == "error_metric":
                    raise Exception("Simulated error")
                return None
        
        error_calc = ErrorCalculator()
        engine = ComparativeAnalyticsEngine(
            daily_calculator=error_calc,
            weekly_calculator=error_calc,
            monthly_calculator=error_calc
        )
        
        # Should return empty HistoricalComparison without raising exception
        result = engine.compare_to_historical("error_metric", datetime.now())
        assert isinstance(result, HistoricalComparison)
        assert result.rolling_7_day is None
        assert result.rolling_30_day is None
        assert result.rolling_90_day is None