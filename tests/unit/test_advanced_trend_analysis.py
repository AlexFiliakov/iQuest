"""Tests for advanced trend analysis engine."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.analytics.advanced_trend_engine import AdvancedTrendAnalysisEngine
from src.analytics.advanced_trend_models import (
    TrendAnalysis, TrendClassification, EvidenceQuality, PredictionQuality,
    ChangePoint, PredictionPoint, SeasonalComponent,
    ValidationResult, EnsembleResult
)


class TestAdvancedTrendAnalysisEngine:
    """Test suite for AdvancedTrendAnalysisEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create test engine instance."""
        return AdvancedTrendAnalysisEngine()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time series data."""
        dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='D')
        # Create trend with some noise
        trend = np.linspace(100, 120, len(dates))
        noise = np.random.normal(0, 2, len(dates))
        values = trend + noise
        return pd.Series(values, index=dates)
    
    @pytest.fixture
    def volatile_data(self):
        """Create volatile time series data."""
        dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='D')
        # High volatility data
        values = 100 + np.random.normal(0, 20, len(dates))
        return pd.Series(values, index=dates)
    
    @pytest.fixture
    def seasonal_data(self):
        """Create data with seasonal pattern."""
        dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='D')
        # Weekly seasonal pattern
        t = np.arange(len(dates))
        trend = 100 + 0.1 * t
        seasonal = 10 * np.sin(2 * np.pi * t / 7)  # Weekly cycle
        noise = np.random.normal(0, 1, len(dates))
        values = trend + seasonal + noise
        return pd.Series(values, index=dates)
    
    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert 'prophet' in engine.ensemble_weights
        assert 'stl' in engine.ensemble_weights
        assert 'linear' in engine.ensemble_weights
        assert sum(engine.ensemble_weights.values()) == pytest.approx(1.0)
    
    def test_clean_data(self, engine, sample_data):
        """Test data cleaning functionality."""
        # Add some NaN values and outliers
        dirty_data = sample_data.copy()
        dirty_data.iloc[5] = np.nan
        dirty_data.iloc[10] = 1000  # Outlier
        
        clean = engine._clean_data(dirty_data)
        
        assert len(clean) == len(dirty_data) - 1  # NaN removed
        assert clean.iloc[9] < 200  # Outlier capped
        assert clean.index.is_monotonic_increasing
    
    def test_assess_data_quality(self, engine, sample_data):
        """Test data quality assessment."""
        quality = engine._assess_data_quality(sample_data)
        
        assert 0 <= quality <= 1
        assert quality > 0.5  # Good quality data
        
        # Test with sparse data
        sparse_data = sample_data.iloc[::5]  # Every 5th point
        sparse_quality = engine._assess_data_quality(sparse_data)
        assert sparse_quality < quality
    
    def test_determine_evidence_quality(self, engine):
        """Test evidence quality determination."""
        # Strong evidence (>30 days)
        dates = pd.date_range(start='2024-01-01', periods=40, freq='D')
        data = pd.Series(range(40), index=dates)
        assert engine._determine_evidence_quality(data) == EvidenceQuality.STRONG
        
        # Moderate evidence (14-30 days)
        data_moderate = data.iloc[:20]
        assert engine._determine_evidence_quality(data_moderate) == EvidenceQuality.MODERATE
        
        # Weak evidence (<14 days)
        data_weak = data.iloc[:10]
        assert engine._determine_evidence_quality(data_weak) == EvidenceQuality.WEAK
    
    def test_mann_kendall_test(self, engine):
        """Test Mann-Kendall trend test."""
        # Increasing trend
        values = np.arange(20) + np.random.normal(0, 0.1, 20)
        result = engine._mann_kendall_test(values)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "Mann-Kendall"
        assert result.trend_detected
        assert result.trend_direction == "increasing"
        assert result.p_value < 0.05
        
        # No trend
        random_values = np.random.normal(100, 1, 20)
        result_random = engine._mann_kendall_test(random_values)
        assert not result_random.trend_detected
    
    def test_sens_slope_estimator(self, engine):
        """Test Sen's slope estimator."""
        # Linear trend
        values = 2 * np.arange(20) + 100
        result = engine._sens_slope_estimator(values)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "Sen's Slope"
        assert abs(result.statistic - 2.0) < 0.1  # Slope should be ~2
        assert result.trend_detected
        assert result.confidence_interval is not None
    
    def test_linear_regression_test(self, engine, sample_data):
        """Test linear regression trend test."""
        result = engine._linear_regression_test(sample_data)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "Linear Regression"
        assert result.trend_detected
        assert result.p_value < 0.05
        assert result.confidence_interval is not None
        assert "R²=" in result.interpretation
    
    def test_classify_trends(self, engine):
        """Test trend classification methods."""
        # Strongly increasing
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        strong_increase = pd.Series(100 * (1.1 ** np.arange(30)), index=dates)
        trend = engine._classify_simple_trend(strong_increase)
        assert trend == TrendClassification.STRONGLY_INCREASING
        
        # Stable
        stable = pd.Series(100 + np.random.normal(0, 0.5, 30), index=dates)
        trend_stable = engine._classify_simple_trend(stable)
        assert trend_stable == TrendClassification.STABLE
        
        # Volatile
        volatile = pd.Series(100 + np.random.normal(0, 50, 30), index=dates)
        trend_volatile = engine._classify_simple_trend(volatile)
        assert trend_volatile == TrendClassification.VOLATILE
    
    def test_detect_change_points(self, engine):
        """Test change point detection."""
        # Create data with clear change point
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        values = np.concatenate([
            np.ones(30) * 100,  # Stable at 100
            np.ones(30) * 120   # Jump to 120
        ])
        data = pd.Series(values + np.random.normal(0, 1, 60), index=dates)
        
        change_points = engine._detect_change_points(data)
        
        assert len(change_points) > 0
        assert isinstance(change_points[0], ChangePoint)
        # Should detect change around day 30
        assert 25 < (change_points[0].timestamp - dates[0]).days < 35
    
    def test_analyze_volatility(self, engine, sample_data, volatile_data):
        """Test volatility analysis."""
        # Low volatility
        vol_low = engine._analyze_volatility(sample_data)
        assert vol_low['level'] == 'low'
        assert vol_low['score'] < 0.1
        
        # High volatility
        vol_high = engine._analyze_volatility(volatile_data)
        assert vol_high['level'] == 'high'
        assert vol_high['score'] > 0.1
    
    def test_generate_predictions(self, engine, sample_data):
        """Test prediction generation."""
        ensemble_result = EnsembleResult(
            primary_trend=TrendClassification.INCREASING,
            confidence=80.0,
            individual_results={},
            weights={},
            agreement_score=0.8
        )
        
        predictions = engine._generate_predictions(
            sample_data, None, ensemble_result, forecast_days=7
        )
        
        assert len(predictions) == 7
        assert all(isinstance(p, PredictionPoint) for p in predictions)
        assert all(p.lower_bound <= p.predicted_value <= p.upper_bound for p in predictions)
        assert predictions[0].timestamp > sample_data.index[-1]
    
    def test_seasonal_detection(self, engine, seasonal_data):
        """Test seasonal pattern detection."""
        decomposition = engine._decompose_time_series(seasonal_data)
        
        assert decomposition is not None
        assert engine._has_significant_seasonality(decomposition)
        
        components = engine._extract_seasonal_components(decomposition, seasonal_data)
        assert len(components) > 0
        assert any(c.period == "weekly" for c in components)
    
    @patch('src.analytics.advanced_trend_engine.Prophet')
    def test_prophet_analysis(self, mock_prophet_class, engine, sample_data):
        """Test Prophet-based analysis when available."""
        # Mock Prophet
        mock_prophet = MagicMock()
        mock_prophet_class.return_value = mock_prophet
        
        # Mock forecast data
        future_dates = pd.date_range(
            start=sample_data.index[-1] + timedelta(days=1),
            periods=7,
            freq='D'
        )
        mock_forecast = pd.DataFrame({
            'ds': pd.concat([pd.Series(sample_data.index), pd.Series(future_dates)]),
            'yhat': np.concatenate([sample_data.values, np.linspace(120, 125, 7)]),
            'yhat_lower': np.concatenate([sample_data.values - 5, np.linspace(115, 120, 7)]),
            'yhat_upper': np.concatenate([sample_data.values + 5, np.linspace(125, 130, 7)]),
            'trend': np.linspace(100, 125, len(sample_data) + 7)
        })
        mock_prophet.predict.return_value = mock_forecast
        mock_prophet.make_future_dataframe.return_value = pd.DataFrame({
            'ds': mock_forecast['ds']
        })
        mock_prophet.changepoints = pd.Series([sample_data.index[15]])
        
        # Enable Prophet
        with patch.object(engine, '__init__', lambda self, style_manager=None: None):
            engine = AdvancedTrendAnalysisEngine()
            engine.style_manager = None
            engine.ensemble_weights = {'prophet': 0.5, 'stl': 0.3, 'linear': 0.2}
            engine.trend_thresholds = {
                'strongly_increasing': 0.05,
                'increasing': 0.01,
                'stable': 0.01,
                'decreasing': -0.01,
                'strongly_decreasing': -0.05
            }
            engine._prophet_cache = {}
            
        result = engine._analyze_with_prophet(sample_data, forecast_days=7)
        
        assert result is not None
        assert 'forecast' in result
        assert 'trend' in result
        assert len(result['trend']) > 0
    
    def test_comprehensive_analysis(self, engine, sample_data):
        """Test full comprehensive analysis."""
        analysis = engine.analyze_trend_comprehensive(
            sample_data,
            metric_name="test_metric",
            health_context={'user_goals': {'test_metric': 110}},
            forecast_days=7
        )
        
        assert analysis is not None
        assert analysis.trend_direction in ["increasing", "decreasing", "stable", "volatile"]
        assert analysis.confidence > 0
        assert len(analysis.predictions) == 7
        assert analysis.summary != ""
        assert analysis.evidence_quality in ["strong", "moderate", "weak"]
        assert analysis.interpretation != ""
        assert len(analysis.methods_used) > 0
        assert 0 <= analysis.data_quality_score <= 1
    
    def test_ensemble_analysis(self, engine, sample_data):
        """Test ensemble voting mechanism."""
        # Create mock results
        statistical_result = {
            'mann_kendall': ValidationResult(
                test_name="Mann-Kendall",
                statistic=2.5,
                p_value=0.01,
                trend_detected=True,
                trend_direction="increasing"
            ),
            'sens_slope': ValidationResult(
                test_name="Sen's Slope",
                statistic=0.02,
                p_value=0.0,
                trend_detected=True,
                trend_direction="increasing"
            ),
            'linear_regression': ValidationResult(
                test_name="Linear Regression",
                statistic=0.015,
                p_value=0.001,
                trend_detected=True,
                trend_direction="increasing"
            ),
            'adf_test': ValidationResult(
                test_name="ADF Test",
                statistic=-2.0,
                p_value=0.3,
                trend_detected=True
            )
        }
        
        ensemble_result = engine._ensemble_analysis(
            sample_data,
            None,  # No Prophet result
            statistical_result,
            None   # No decomposition
        )
        
        assert isinstance(ensemble_result, EnsembleResult)
        assert ensemble_result.primary_trend in [
            TrendClassification.INCREASING,
            TrendClassification.STRONGLY_INCREASING
        ]
        assert ensemble_result.confidence > 50
        assert ensemble_result.agreement_score > 0.5
    
    def test_health_context_interpretation(self, engine):
        """Test health-specific interpretations."""
        ensemble_result = EnsembleResult(
            primary_trend=TrendClassification.INCREASING,
            confidence=85.0,
            individual_results={},
            weights={},
            agreement_score=0.9
        )
        
        # Test steps interpretation
        interp_steps = engine._interpret_health_context(
            ensemble_result,
            "steps",
            {'user_goals': {'steps': 10000}}
        )
        assert "progress" in interp_steps.lower()
        assert "10000" in interp_steps
        
        # Test heart rate interpretation  
        ensemble_result_hr = EnsembleResult(
            primary_trend=TrendClassification.DECREASING,
            confidence=85.0,
            individual_results={},
            weights={},
            agreement_score=0.9
        )
        interp_hr = engine._interpret_health_context(
            ensemble_result_hr,
            "heart_rate_resting",
            {}
        )
        assert "fitness" in interp_hr.lower() or "good" in interp_hr.lower()
    
    def test_wsj_summary_generation(self, engine):
        """Test WSJ-style summary generation."""
        ensemble_result = EnsembleResult(
            primary_trend=TrendClassification.STRONGLY_INCREASING,
            confidence=90.0,
            individual_results={},
            weights={},
            agreement_score=0.95
        )
        
        summary = engine._generate_wsj_summary(
            ensemble_result,
            "Your daily steps are improving significantly.",
            "daily_steps"
        )
        
        assert "Daily Steps" in summary
        assert "clearly" in summary  # High confidence
        assert "sharply" in summary  # Strong trend
    
    def test_recommendations_generation(self, engine):
        """Test recommendation generation."""
        ensemble_result = EnsembleResult(
            primary_trend=TrendClassification.DECREASING,
            confidence=75.0,
            individual_results={},
            weights={},
            agreement_score=0.8
        )
        
        # Test steps recommendations
        recs = engine._generate_recommendations(
            ensemble_result,
            "steps",
            {'user_goals': {'steps': 10000}}
        )
        
        assert len(recs) > 0
        assert len(recs) <= 3
        assert any("walk" in r.lower() for r in recs)
        
        # Test sleep recommendations
        recs_sleep = engine._generate_recommendations(
            ensemble_result,
            "sleep_hours",
            {}
        )
        
        assert len(recs_sleep) > 0
        assert any("bedtime" in r.lower() or "sleep" in r.lower() for r in recs_sleep)
    
    def test_edge_cases(self, engine):
        """Test edge cases and error handling."""
        # Empty data
        empty_data = pd.Series([], dtype=float)
        analysis = engine.analyze_trend_comprehensive(
            empty_data,
            "test_metric"
        )
        assert analysis.trend_direction == "stable"  # Maps INSUFFICIENT_DATA to stable
        
        # Single data point
        single_point = pd.Series([100], index=[datetime.now()])
        analysis_single = engine.analyze_trend_comprehensive(
            single_point,
            "test_metric"
        )
        assert analysis_single.trend_direction == "stable"  # Maps INSUFFICIENT_DATA to stable
        
        # All same values
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        constant_data = pd.Series([100] * 30, index=dates)
        analysis_constant = engine.analyze_trend_comprehensive(
            constant_data,
            "test_metric"
        )
        assert analysis_constant.trend_direction == "stable"