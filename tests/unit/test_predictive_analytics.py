"""
Unit tests for predictive analytics module.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.predictive_analytics import (
    PredictiveAnalytics, ARIMAForecaster, RandomForestForecaster, LinearForecaster,
    GoalAchievementPredictor, Goal, HealthRiskPredictor, RiskLevel, AccuracyTracker,
    PredictionABTester, PredictionVariant, Prediction, FeatureBuilder
)


@pytest.fixture
def sample_time_series():
    """Create sample time series data for testing."""
    dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
    # Create trend with noise
    trend = np.linspace(100, 120, 30)
    noise = np.random.normal(0, 2, 30)
    values = trend + noise
    
    return pd.Series(values, index=dates, name='TestMetric')


@pytest.fixture
def sample_health_data():
    """Create sample health data for testing."""
    dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
    
    # Heart rate data with weekly pattern
    heart_rate = 70 + np.sin(np.arange(30) * 2 * np.pi / 7) * 5 + np.random.normal(0, 2, 30)
    
    # Steps data with weekend pattern
    steps = 8000 + np.random.normal(0, 1000, 30)
    # Lower on weekends
    weekend_mask = pd.Series(dates).dt.dayofweek >= 5
    steps[weekend_mask] *= 0.7
    
    return {
        'HeartRate': pd.Series(heart_rate, index=dates, name='HeartRate'),
        'Steps': pd.Series(steps, index=dates, name='Steps')
    }


class TestFeatureBuilder:
    """Test feature engineering functionality."""
    
    def test_build_features(self, sample_time_series):
        """Test feature building from time series."""
        builder = FeatureBuilder()
        features = builder.build_features(sample_time_series)
        
        assert not features.empty
        assert 'value' in features.columns
        assert 'lag_1' in features.columns
        assert 'rolling_mean_7' in features.columns
        assert 'day_of_week' in features.columns
        
    def test_build_next_features(self, sample_time_series):
        """Test building features for next prediction."""
        builder = FeatureBuilder()
        next_features = builder.build_next_features(sample_time_series)
        
        assert isinstance(next_features, np.ndarray)
        assert len(next_features) >= 10  # Should have multiple features
        
    def test_build_features_with_context(self, sample_time_series):
        """Test feature building with context data."""
        builder = FeatureBuilder()
        context = {'weather_temp': 25.0, 'is_holiday': 0}
        
        features = builder.build_features(sample_time_series, context)
        
        assert 'context_weather_temp' in features.columns
        assert 'context_is_holiday' in features.columns


class TestForecasters:
    """Test individual forecasting models."""
    
    def test_arima_forecaster(self, sample_time_series):
        """Test ARIMA forecasting."""
        forecaster = ARIMAForecaster()
        prediction = forecaster.predict_next_day(sample_time_series)
        
        assert 'value' in prediction
        assert 'interval' in prediction
        assert 'model' in prediction
        assert isinstance(prediction['value'], float)
        assert len(prediction['interval']) == 2
        
    def test_random_forest_forecaster(self, sample_time_series):
        """Test Random Forest forecasting."""
        forecaster = RandomForestForecaster()
        prediction = forecaster.predict_next_day(sample_time_series)
        
        assert 'value' in prediction
        assert 'interval' in prediction
        assert 'model' in prediction
        assert 'feature_importance' in prediction
        assert isinstance(prediction['value'], float)
        
    def test_linear_forecaster(self, sample_time_series):
        """Test Linear regression forecasting."""
        forecaster = LinearForecaster()
        prediction = forecaster.predict_next_day(sample_time_series)
        
        assert 'value' in prediction
        assert 'interval' in prediction
        assert 'model' in prediction
        assert 'slope' in prediction
        assert isinstance(prediction['value'], float)
        
    def test_arima_forecast_multiple_periods(self, sample_time_series):
        """Test multi-period ARIMA forecasting."""
        forecaster = ARIMAForecaster()
        forecast = forecaster.forecast(sample_time_series, periods=7)
        
        assert len(forecast) == 7
        assert all(isinstance(val, float) for val in forecast)


class TestPredictiveAnalytics:
    """Test main predictive analytics engine."""
    
    def test_predict_next_day(self, sample_time_series):
        """Test next day prediction."""
        analytics = PredictiveAnalytics()
        prediction = analytics.predict_next_day('TestMetric', sample_time_series)
        
        assert isinstance(prediction, Prediction)
        assert isinstance(prediction.value, float)
        assert len(prediction.confidence_interval) == 2
        assert 0 <= prediction.confidence_level <= 1
        assert isinstance(prediction.explanation, str)
        assert isinstance(prediction.model_contributions, dict)
        
    def test_forecast_weekly_trend(self, sample_time_series):
        """Test weekly trend forecasting."""
        analytics = PredictiveAnalytics()
        forecast = analytics.forecast_weekly_trend('TestMetric', sample_time_series)
        
        assert len(forecast.daily_predictions) == 7
        assert 'optimistic' in forecast.scenarios
        assert 'realistic' in forecast.scenarios
        assert 'pessimistic' in forecast.scenarios
        assert forecast.trend_direction in ['increasing', 'decreasing', 'stable']
        assert 0 <= forecast.trend_confidence <= 1
        assert isinstance(forecast.key_insights, list)
        
    def test_predict_with_context(self, sample_time_series):
        """Test prediction with context data."""
        analytics = PredictiveAnalytics()
        context = {'weather_temp': 22.0}
        
        prediction = analytics.predict_next_day('TestMetric', sample_time_series, context)
        
        assert isinstance(prediction, Prediction)
        assert prediction.value is not None


class TestGoalAchievementPredictor:
    """Test goal achievement prediction."""
    
    def test_predict_goal_achievement(self, sample_time_series):
        """Test goal achievement prediction."""
        predictor = GoalAchievementPredictor()
        
        goal = Goal(
            metric='TestMetric',
            target_value=130.0,
            current_value=sample_time_series.iloc[-1],
            target_date=datetime.now() + timedelta(days=30),
            goal_type='increase'
        )
        
        prediction = predictor.predict_goal_achievement(goal, sample_time_series)
        
        assert 0 <= prediction.success_probability <= 1
        assert len(prediction.confidence_interval) == 2
        assert isinstance(prediction.daily_targets, dict)
        assert isinstance(prediction.milestones, list)
        assert isinstance(prediction.factors, list)
        
    def test_goal_types(self, sample_time_series):
        """Test different goal types."""
        predictor = GoalAchievementPredictor()
        current_value = sample_time_series.iloc[-1]
        
        # Test increase goal
        increase_goal = Goal(
            metric='TestMetric',
            target_value=current_value + 10,
            current_value=current_value,
            target_date=datetime.now() + timedelta(days=30),
            goal_type='increase'
        )
        
        # Test decrease goal
        decrease_goal = Goal(
            metric='TestMetric',
            target_value=current_value - 10,
            current_value=current_value,
            target_date=datetime.now() + timedelta(days=30),
            goal_type='decrease'
        )
        
        # Test maintain goal
        maintain_goal = Goal(
            metric='TestMetric',
            target_value=current_value,
            current_value=current_value,
            target_date=datetime.now() + timedelta(days=30),
            goal_type='maintain'
        )
        
        for goal in [increase_goal, decrease_goal, maintain_goal]:
            prediction = predictor.predict_goal_achievement(goal, sample_time_series)
            assert isinstance(prediction.success_probability, float)


class TestHealthRiskPredictor:
    """Test health risk assessment."""
    
    def test_assess_health_risks(self, sample_health_data):
        """Test comprehensive health risk assessment."""
        predictor = HealthRiskPredictor()
        assessment = predictor.assess_health_risks(sample_health_data)
        
        assert hasattr(assessment, 'risks')
        assert hasattr(assessment, 'overall_risk_level')
        assert hasattr(assessment, 'recommendations')
        assert hasattr(assessment, 'next_check_date')
        assert isinstance(assessment.recommendations, list)
        
    def test_anomaly_detection(self, sample_health_data):
        """Test anomaly-based risk detection."""
        predictor = HealthRiskPredictor()
        
        # Add an outlier to test anomaly detection
        heart_rate_data = sample_health_data['HeartRate'].copy()
        heart_rate_data.iloc[-1] = heart_rate_data.mean() + 5 * heart_rate_data.std()
        
        risk = predictor.risk_models['anomaly'].assess_risk('HeartRate', heart_rate_data)
        
        assert risk.severity in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert 0 <= risk.probability <= 1
        assert isinstance(risk.description, str)
        assert isinstance(risk.recommendations, list)
        
    def test_trend_risk_detection(self, sample_health_data):
        """Test trend-based risk detection."""
        predictor = HealthRiskPredictor()
        
        # Create a strong trend to test trend detection
        trending_data = sample_health_data['HeartRate'].copy()
        trending_data.iloc[-7:] += np.linspace(0, 20, 7)  # Strong upward trend
        
        risk = predictor.risk_models['trend'].assess_risk('HeartRate', trending_data)
        
        assert risk.severity in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert isinstance(risk.description, str)


class TestAccuracyTracker:
    """Test prediction accuracy tracking."""
    
    def test_track_and_calculate_accuracy(self, sample_time_series):
        """Test prediction tracking and accuracy calculation."""
        tracker = AccuracyTracker()
        analytics = PredictiveAnalytics()
        
        # Make some predictions and track them
        for i in range(5):
            historical_data = sample_time_series.iloc[:20+i]
            prediction = analytics.predict_next_day('TestMetric', historical_data)
            
            prediction_date = historical_data.index[-1] + timedelta(days=1)
            tracker.track_prediction(prediction, 'TestMetric', prediction_date)
            
        # Calculate accuracy (this will have empty matched pairs since we don't have actual future data)
        accuracy_report = tracker.calculate_accuracy('TestMetric', sample_time_series)
        
        assert isinstance(accuracy_report.overall_mae, float)
        assert isinstance(accuracy_report.overall_rmse, float)
        assert isinstance(accuracy_report.interval_coverage, float)
        assert isinstance(accuracy_report.model_accuracy, dict)
        assert isinstance(accuracy_report.recommendations, list)


class TestABTesting:
    """Test A/B testing framework."""
    
    def test_create_experiment(self):
        """Test experiment creation."""
        tester = PredictionABTester()
        
        variants = [
            PredictionVariant(
                name='baseline',
                description='Baseline model',
                model_config={'type': 'ensemble'},
                weight_config={'arima': 0.5, 'rf': 0.3, 'linear': 0.2}
            ),
            PredictionVariant(
                name='improved',
                description='Improved model weights',
                model_config={'type': 'ensemble'},
                weight_config={'arima': 0.3, 'rf': 0.5, 'linear': 0.2}
            )
        ]
        
        experiment = tester.create_experiment('test_weights', variants)
        
        assert experiment.name == 'test_weights'
        assert len(experiment.variants) == 2
        assert experiment.min_sample_size > 0
        
    def test_variant_assignment(self):
        """Test consistent variant assignment."""
        tester = PredictionABTester()
        
        variants = [
            PredictionVariant('A', 'Variant A', {}, {}),
            PredictionVariant('B', 'Variant B', {}, {})
        ]
        
        experiment = tester.create_experiment('test_assignment', variants)
        
        # Same user should get same variant
        user_id = 'test_user_123'
        variant1 = tester.assign_variant(user_id, 'test_assignment')
        variant2 = tester.assign_variant(user_id, 'test_assignment')
        
        assert variant1.name == variant2.name
        
    def test_outcome_recording(self):
        """Test recording experiment outcomes."""
        tester = PredictionABTester()
        
        variants = [
            PredictionVariant('A', 'Variant A', {}, {}),
            PredictionVariant('B', 'Variant B', {}, {})
        ]
        
        experiment = tester.create_experiment('test_outcomes', variants)
        
        # Record some outcomes
        for i in range(10):
            user_id = f'user_{i}'
            outcomes = {
                'mae': np.random.uniform(1, 5),
                'user_trust': np.random.uniform(0, 1),
                'action_taken': np.random.choice([0, 1])
            }
            tester.record_outcome(user_id, 'test_outcomes', outcomes)
            
        # Check that outcomes were recorded
        experiment = tester.experiments['test_outcomes']
        total_outcomes = sum(len(outcomes) for outcomes in experiment.outcomes.values())
        assert total_outcomes == 10


class TestIntegration:
    """Integration tests for the full system."""
    
    def test_full_prediction_pipeline(self, sample_time_series):
        """Test complete prediction pipeline."""
        analytics = PredictiveAnalytics()
        
        # Make prediction
        prediction = analytics.predict_next_day('TestMetric', sample_time_series)
        assert isinstance(prediction, Prediction)
        
        # Track accuracy
        tracker = AccuracyTracker()
        prediction_date = sample_time_series.index[-1] + timedelta(days=1)
        tracker.track_prediction(prediction, 'TestMetric', prediction_date)
        
        # Generate weekly forecast
        weekly_forecast = analytics.forecast_weekly_trend('TestMetric', sample_time_series)
        assert len(weekly_forecast.daily_predictions) == 7
        
    def test_goal_and_risk_integration(self, sample_health_data):
        """Test goal prediction and risk assessment integration."""
        goal_predictor = GoalAchievementPredictor()
        risk_predictor = HealthRiskPredictor()
        
        # Create a health goal
        current_hr = sample_health_data['HeartRate'].iloc[-1]
        goal = Goal(
            metric='HeartRate',
            target_value=current_hr - 5,  # Reduce heart rate
            current_value=current_hr,
            target_date=datetime.now() + timedelta(days=30),
            goal_type='decrease'
        )
        
        # Predict goal achievement
        goal_prediction = goal_predictor.predict_goal_achievement(goal, sample_health_data['HeartRate'])
        assert isinstance(goal_prediction.success_probability, float)
        
        # Assess health risks
        risk_assessment = risk_predictor.assess_health_risks(sample_health_data)
        assert hasattr(risk_assessment, 'overall_risk_level')


# Test error handling
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_data(self):
        """Test handling of empty data."""
        analytics = PredictiveAnalytics()
        empty_series = pd.Series([], dtype=float, name='Empty')
        
        # Should not raise exception
        prediction = analytics.predict_next_day('Empty', empty_series)
        assert isinstance(prediction, Prediction)
        
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        analytics = PredictiveAnalytics()
        short_series = pd.Series([1.0, 2.0], name='Short')
        
        prediction = analytics.predict_next_day('Short', short_series)
        assert isinstance(prediction, Prediction)
        
    def test_invalid_goal_dates(self):
        """Test handling of invalid goal dates."""
        predictor = GoalAchievementPredictor()
        
        # Goal with past target date
        past_goal = Goal(
            metric='Test',
            target_value=100,
            current_value=90,
            target_date=datetime.now() - timedelta(days=10),  # Past date
            goal_type='increase'
        )
        
        data = pd.Series([90, 91, 92], name='Test')
        prediction = predictor.predict_goal_achievement(past_goal, data)
        
        # Should handle gracefully
        assert isinstance(prediction.success_probability, float)


if __name__ == '__main__':
    pytest.main([__file__])