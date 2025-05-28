"""
Predictive Analytics module for health data forecasting.

Provides forecasting models for health metrics including next-day predictions,
weekly trend forecasts, goal achievement probability, and health risk indicators.
Implements multiple ML models (ARIMA, Random Forest, linear regression) with
confidence intervals and plain language explanations.
"""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

# Optional pmdarima import with fallback
try:
    import pmdarima as pm
    PMDARIMA_AVAILABLE = True
except (ImportError, ValueError) as e:
    PMDARIMA_AVAILABLE = False
    logging.warning(f"pmdarima not available ({e}), using fallback ARIMA parameter selection")

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)


class RiskLevel(Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Prediction:
    """Container for prediction results."""
    value: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    explanation: str
    model_contributions: Dict[str, Dict]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class WeeklyForecast:
    """Container for weekly forecast results."""
    daily_predictions: List[float]
    scenarios: Dict[str, List[float]]
    trend_direction: str
    trend_confidence: float
    key_insights: List[str]


@dataclass
class GoalPrediction:
    """Container for goal achievement predictions."""
    success_probability: float
    confidence_interval: Tuple[float, float]
    estimated_time_days: Optional[int]
    daily_targets: Dict[str, float]
    milestones: List[Dict]
    factors: List[str]


@dataclass
class HealthRisk:
    """Container for health risk assessment."""
    metric: str
    severity: RiskLevel
    probability: float
    description: str
    recommendations: List[str]
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()


@dataclass
class RiskAssessment:
    """Container for comprehensive risk assessment."""
    risks: List[HealthRisk]
    overall_risk_level: RiskLevel
    recommendations: List[str]
    next_check_date: datetime


@dataclass
class AccuracyReport:
    """Container for prediction accuracy metrics."""
    overall_mae: float
    overall_rmse: float
    interval_coverage: float
    model_accuracy: Dict[str, Dict]
    trend_accuracy: float
    recommendations: List[str]


class FeatureBuilder:
    """Builds features for machine learning models."""
    
    def build_features(self, data: pd.Series, context: Dict = None) -> pd.DataFrame:
        """Build engineered features from time series data."""
        df = pd.DataFrame()
        df['value'] = data.values
        
        # Lag features
        for lag in [1, 3, 7, 14]:
            df[f'lag_{lag}'] = data.shift(lag).values
            
        # Rolling statistics
        for window in [3, 7, 14]:
            df[f'rolling_mean_{window}'] = data.rolling(window=window).mean().values
            df[f'rolling_std_{window}'] = data.rolling(window=window).std().values
            
        # Time-based features
        if isinstance(data.index, pd.DatetimeIndex):
            df['day_of_week'] = data.index.dayofweek
            df['day_of_month'] = data.index.day
            df['month'] = data.index.month
            df['is_weekend'] = (data.index.dayofweek >= 5).astype(int)
        else:
            # If no datetime index, create dummy time features
            df['day_of_week'] = np.arange(len(data)) % 7
            df['day_of_month'] = (np.arange(len(data)) % 30) + 1
            df['month'] = ((np.arange(len(data)) // 30) % 12) + 1
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
        # Trend features
        df['linear_trend'] = np.arange(len(data))
        
        # Context features
        if context:
            for key, value in context.items():
                if isinstance(value, (int, float)):
                    df[f'context_{key}'] = value
                    
        # Drop rows with NaN values
        df = df.dropna()
        
        return df
    
    def build_next_features(self, data: pd.Series, context: Dict = None) -> np.ndarray:
        """Build features for predicting the next value."""
        features = {}
        
        # Lag features
        for lag in [1, 3, 7, 14]:
            if len(data) >= lag:
                features[f'lag_{lag}'] = data.iloc[-lag]
            else:
                features[f'lag_{lag}'] = data.iloc[0]  # Use first value if not enough data
                
        # Rolling statistics
        for window in [3, 7, 14]:
            if len(data) >= window:
                features[f'rolling_mean_{window}'] = data.iloc[-window:].mean()
                features[f'rolling_std_{window}'] = data.iloc[-window:].std()
            else:
                features[f'rolling_mean_{window}'] = data.mean()
                features[f'rolling_std_{window}'] = data.std()
                
        # Time-based features for next day
        if isinstance(data.index, pd.DatetimeIndex):
            next_date = data.index[-1] + timedelta(days=1)
            features['day_of_week'] = next_date.dayofweek
            features['day_of_month'] = next_date.day
            features['month'] = next_date.month
            features['is_weekend'] = int(next_date.dayofweek >= 5)
        else:
            features['day_of_week'] = len(data) % 7
            features['day_of_month'] = ((len(data) % 30) + 1)
            features['month'] = ((len(data) // 30) % 12) + 1
            features['is_weekend'] = int(features['day_of_week'] >= 5)
            
        # Trend feature
        features['linear_trend'] = len(data)
        
        # Context features
        if context:
            for key, value in context.items():
                if isinstance(value, (int, float)):
                    features[f'context_{key}'] = value
                    
        # Convert to numpy array in consistent order
        feature_names = [
            'lag_1', 'lag_3', 'lag_7', 'lag_14',
            'rolling_mean_3', 'rolling_mean_7', 'rolling_mean_14',
            'rolling_std_3', 'rolling_std_7', 'rolling_std_14',
            'day_of_week', 'day_of_month', 'month', 'is_weekend', 'linear_trend'
        ]
        
        # Add context features
        if context:
            for key in sorted(context.keys()):
                if isinstance(context[key], (int, float)):
                    feature_names.append(f'context_{key}')
                    
        # Fill missing features with 0
        feature_values = []
        for name in feature_names:
            feature_values.append(features.get(name, 0))
            
        return np.array(feature_values)


class ARIMAForecaster:
    """ARIMA-based forecasting model."""
    
    def __init__(self):
        self.model_params = {}
        self.seasonal_period = 7  # Weekly seasonality
        
    def predict_next_day(self, data: pd.Series, context: Dict = None) -> Dict:
        """ARIMA prediction for next day."""
        try:
            # Determine best parameters if not cached
            cache_key = f"{data.name}_{len(data)}"
            if cache_key not in self.model_params:
                self.model_params[cache_key] = self._auto_arima(data)
                
            params = self.model_params[cache_key]
            
            # Fit ARIMA model
            model = ARIMA(data, order=params['order'], 
                         seasonal_order=params['seasonal_order'])
            fitted = model.fit(method_kwargs={'warn_convergence': False})
            
            # Generate forecast
            forecast = fitted.forecast(steps=1)
            
            # Get prediction intervals
            forecast_df = fitted.get_forecast(steps=1).summary_frame()
            
            return {
                'value': float(forecast.iloc[0]),
                'interval': (float(forecast_df['mean_ci_lower'].iloc[0]), 
                            float(forecast_df['mean_ci_upper'].iloc[0])),
                'model': 'ARIMA',
                'params': params
            }
            
        except Exception as e:
            logging.warning(f"ARIMA prediction failed: {e}")
            # Fallback to simple moving average
            return self._fallback_prediction(data)
    
    def forecast(self, data: pd.Series, periods: int = 7) -> List[float]:
        """Generate multi-step forecast."""
        try:
            cache_key = f"{data.name}_{len(data)}"
            if cache_key not in self.model_params:
                self.model_params[cache_key] = self._auto_arima(data)
                
            params = self.model_params[cache_key]
            
            model = ARIMA(data, order=params['order'], 
                         seasonal_order=params['seasonal_order'])
            fitted = model.fit(method_kwargs={'warn_convergence': False})
            
            forecast = fitted.forecast(steps=periods)
            return forecast.tolist()
            
        except Exception as e:
            logging.warning(f"ARIMA forecast failed: {e}")
            # Fallback to trend-based forecast
            return self._fallback_forecast(data, periods)
    
    def _auto_arima(self, data: pd.Series) -> Dict:
        """Automatically determine best ARIMA parameters."""
        if PMDARIMA_AVAILABLE:
            try:
                model = pm.auto_arima(
                    data,
                    seasonal=True,
                    m=self.seasonal_period,
                    suppress_warnings=True,
                    stepwise=True,
                    max_p=3,
                    max_q=3,
                    max_d=2,
                    max_P=2,
                    max_Q=2,
                    max_D=1,
                    information_criterion='aic',
                    error_action='ignore'
                )
                
                return {
                    'order': model.order,
                    'seasonal_order': model.seasonal_order
                }
                
            except Exception as e:
                logging.warning(f"Auto-ARIMA failed: {e}, using default parameters")
        else:
            logging.info("pmdarima not available, using default ARIMA parameters")
            
        return {
            'order': (1, 1, 1),
            'seasonal_order': (1, 1, 1, self.seasonal_period)
        }
    
    def _fallback_prediction(self, data: pd.Series) -> Dict:
        """Fallback prediction using simple moving average."""
        window = min(7, len(data))
        prediction = data.iloc[-window:].mean()
        std = data.iloc[-window:].std()
        
        return {
            'value': float(prediction),
            'interval': (float(prediction - 2*std), float(prediction + 2*std)),
            'model': 'ARIMA_Fallback',
            'params': {'window': window}
        }
    
    def _fallback_forecast(self, data: pd.Series, periods: int) -> List[float]:
        """Fallback forecast using trend and seasonality."""
        # Simple trend calculation
        if len(data) >= 14:
            recent_trend = (data.iloc[-7:].mean() - data.iloc[-14:-7].mean()) / 7
        else:
            recent_trend = 0
            
        last_value = data.iloc[-1]
        forecast = []
        
        for i in range(periods):
            # Add trend component
            next_value = last_value + recent_trend * (i + 1)
            
            # Add seasonal component (weekly)
            if len(data) >= 7:
                seasonal_idx = (len(data) + i) % 7
                seasonal_base_idx = len(data) - 7 + seasonal_idx
                if seasonal_base_idx >= 0:
                    seasonal_factor = data.iloc[seasonal_base_idx] / data.iloc[-7:].mean()
                    next_value *= seasonal_factor
                    
            forecast.append(float(next_value))
            
        return forecast


class RandomForestForecaster:
    """Random Forest-based forecasting model."""
    
    def __init__(self):
        self.models = {}
        self.feature_builder = FeatureBuilder()
        
    def predict_next_day(self, data: pd.Series, context: Dict = None) -> Dict:
        """Random Forest prediction using engineered features."""
        try:
            # Build features
            features_df = self.feature_builder.build_features(data, context)
            
            if len(features_df) < 2:
                return self._fallback_prediction(data)
                
            X = features_df.drop('value', axis=1).values
            y = features_df['value'].values
            
            # Train model
            cache_key = f"{data.name}_{len(data)}"
            if cache_key not in self.models:
                self.models[cache_key] = RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1
                )
                
            model = self.models[cache_key]
            model.fit(X, y)
            
            # Predict next value
            next_features = self.feature_builder.build_next_features(data, context)
            # Ensure feature alignment
            next_features = next_features[:X.shape[1]]  # Trim to match training features
            if len(next_features) < X.shape[1]:
                # Pad with zeros if needed
                next_features = np.pad(next_features, (0, X.shape[1] - len(next_features)))
                
            prediction = model.predict(next_features.reshape(1, -1))[0]
            
            # Calculate prediction interval using quantile regression approach
            lower, upper = self._calculate_prediction_interval(model, X, y, next_features)
            
            return {
                'value': float(prediction),
                'interval': (float(lower), float(upper)),
                'model': 'RandomForest',
                'feature_importance': dict(zip(features_df.drop('value', axis=1).columns, 
                                             model.feature_importances_))
            }
            
        except Exception as e:
            logging.warning(f"Random Forest prediction failed: {e}")
            return self._fallback_prediction(data)
    
    def _calculate_prediction_interval(self, model, X, y, next_features, alpha=0.05):
        """Calculate prediction interval using bootstrap approach."""
        try:
            # Bootstrap predictions
            n_bootstrap = 100
            predictions = []
            
            for _ in range(n_bootstrap):
                # Bootstrap sample
                indices = np.random.choice(len(X), size=len(X), replace=True)
                X_boot = X[indices]
                y_boot = y[indices]
                
                # Train on bootstrap sample
                boot_model = RandomForestRegressor(
                    n_estimators=50,  # Fewer trees for speed
                    random_state=np.random.randint(10000),
                    n_jobs=1
                )
                boot_model.fit(X_boot, y_boot)
                
                # Predict
                pred = boot_model.predict(next_features.reshape(1, -1))[0]
                predictions.append(pred)
                
            # Calculate confidence interval
            lower = np.percentile(predictions, alpha/2 * 100)
            upper = np.percentile(predictions, (1 - alpha/2) * 100)
            
            return lower, upper
            
        except Exception:
            # Fallback to simple std-based interval
            prediction = model.predict(next_features.reshape(1, -1))[0]
            residuals = y - model.predict(X)
            std = np.std(residuals)
            return prediction - 2*std, prediction + 2*std
    
    def _fallback_prediction(self, data: pd.Series) -> Dict:
        """Fallback prediction using simple approach."""
        window = min(7, len(data))
        prediction = data.iloc[-window:].mean()
        std = data.iloc[-window:].std()
        
        return {
            'value': float(prediction),
            'interval': (float(prediction - 2*std), float(prediction + 2*std)),
            'model': 'RandomForest_Fallback',
            'feature_importance': {}
        }


class LinearForecaster:
    """Simple linear regression forecaster."""
    
    def __init__(self):
        self.models = {}
        
    def predict_next_day(self, data: pd.Series, context: Dict = None) -> Dict:
        """Linear regression prediction for next day."""
        try:
            if len(data) < 3:
                return self._fallback_prediction(data)
                
            # Prepare data for linear regression
            X = np.arange(len(data)).reshape(-1, 1)
            y = data.values
            
            # Train model
            cache_key = f"{data.name}_{len(data)}"
            if cache_key not in self.models:
                self.models[cache_key] = LinearRegression()
                
            model = self.models[cache_key]
            model.fit(X, y)
            
            # Predict next value
            next_X = np.array([[len(data)]])
            prediction = model.predict(next_X)[0]
            
            # Calculate prediction interval
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            
            return {
                'value': float(prediction),
                'interval': (float(prediction - 2*std_error), 
                            float(prediction + 2*std_error)),
                'model': 'LinearRegression',
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_)
            }
            
        except Exception as e:
            logging.warning(f"Linear regression prediction failed: {e}")
            return self._fallback_prediction(data)
    
    def _fallback_prediction(self, data: pd.Series) -> Dict:
        """Fallback prediction using last value."""
        last_value = data.iloc[-1]
        std = data.std()
        
        return {
            'value': float(last_value),
            'interval': (float(last_value - std), float(last_value + std)),
            'model': 'Linear_Fallback',
            'slope': 0.0,
            'intercept': float(last_value)
        }


class EnsembleForecaster:
    """Ensemble forecaster combining multiple models."""
    
    def ensemble_predictions(self, predictions: Dict[str, Dict]) -> Dict:
        """Combine predictions from multiple models using weighted average."""
        if not predictions:
            return {'value': 0.0, 'interval': (0.0, 0.0)}
            
        # Model weights (can be adjusted based on historical performance)
        weights = {
            'arima': 0.4,
            'random_forest': 0.4,
            'linear': 0.2
        }
        
        # Calculate weighted average
        total_weight = 0
        weighted_value = 0
        intervals = []
        
        for model_name, pred in predictions.items():
            weight = weights.get(model_name, 0.2)
            total_weight += weight
            weighted_value += pred['value'] * weight
            intervals.append(pred['interval'])
            
        if total_weight > 0:
            ensemble_value = weighted_value / total_weight
        else:
            ensemble_value = np.mean([p['value'] for p in predictions.values()])
            
        # Combine intervals using conservative approach
        if intervals:
            lower_bounds = [interval[0] for interval in intervals]
            upper_bounds = [interval[1] for interval in intervals]
            ensemble_interval = (min(lower_bounds), max(upper_bounds))
        else:
            ensemble_interval = (ensemble_value, ensemble_value)
            
        return {
            'value': ensemble_value,
            'interval': ensemble_interval
        }


class PredictiveAnalytics:
    """Main predictive analytics engine."""
    
    def __init__(self):
        self.models = {
            'arima': ARIMAForecaster(),
            'random_forest': RandomForestForecaster(),
            'linear': LinearForecaster(),
            'ensemble': EnsembleForecaster()
        }
        self.explainer = None  # Will be initialized when needed
        self.accuracy_tracker = None  # Will be initialized when needed
        
    def predict_next_day(self, metric: str, historical_data: pd.Series, 
                        context: Dict = None) -> Prediction:
        """Generate next-day prediction with confidence."""
        try:
            predictions = {}
            
            # Get predictions from each model
            for name, model in self.models.items():
                if name == 'ensemble':
                    continue  # Skip ensemble in this loop
                    
                try:
                    pred = model.predict_next_day(historical_data, context)
                    predictions[name] = pred
                except Exception as e:
                    logging.warning(f"Model {name} failed: {e}")
                    
            # Ensemble prediction
            ensemble_pred = self.models['ensemble'].ensemble_predictions(predictions)
            
            # Calculate confidence
            confidence = self._calculate_confidence(predictions, historical_data)
            
            # Generate explanation
            explanation = self._generate_explanation(
                ensemble_pred, predictions, historical_data, context
            )
            
            return Prediction(
                value=ensemble_pred['value'],
                confidence_interval=ensemble_pred['interval'],
                confidence_level=confidence,
                explanation=explanation,
                model_contributions=predictions
            )
            
        except Exception as e:
            logging.error(f"Prediction failed for {metric}: {e}")
            # Return fallback prediction
            last_value = historical_data.iloc[-1]
            return Prediction(
                value=last_value,
                confidence_interval=(last_value * 0.9, last_value * 1.1),
                confidence_level=0.3,
                explanation="Using fallback prediction due to modeling error.",
                model_contributions={}
            )
    
    def forecast_weekly_trend(self, metric: str, historical_data: pd.Series) -> WeeklyForecast:
        """Generate 7-day forecast with scenarios."""
        try:
            # Base forecast using ARIMA
            base_forecast = self.models['arima'].forecast(historical_data, periods=7)
            
            # Scenario analysis
            scenarios = {
                'optimistic': [x * 1.1 for x in base_forecast],  # 10% increase
                'realistic': base_forecast,
                'pessimistic': [x * 0.9 for x in base_forecast]  # 10% decrease
            }
            
            # Trend analysis
            trend_direction = self._analyze_trend_direction(base_forecast)
            trend_confidence = self._calculate_trend_confidence(base_forecast)
            
            # Generate insights
            key_insights = self._generate_weekly_insights(base_forecast, historical_data)
            
            return WeeklyForecast(
                daily_predictions=base_forecast,
                scenarios=scenarios,
                trend_direction=trend_direction,
                trend_confidence=trend_confidence,
                key_insights=key_insights
            )
            
        except Exception as e:
            logging.error(f"Weekly forecast failed for {metric}: {e}")
            # Return fallback forecast
            last_value = historical_data.iloc[-1]
            return WeeklyForecast(
                daily_predictions=[last_value] * 7,
                scenarios={
                    'optimistic': [last_value * 1.1] * 7,
                    'realistic': [last_value] * 7,
                    'pessimistic': [last_value * 0.9] * 7
                },
                trend_direction='stable',
                trend_confidence=0.3,
                key_insights=['Limited data available for detailed forecast']
            )
    
    def _calculate_confidence(self, predictions: Dict, historical_data: pd.Series) -> float:
        """Calculate confidence based on model agreement and data quality."""
        if not predictions:
            return 0.0
            
        # Model agreement
        values = [p['value'] for p in predictions.values()]
        if len(values) > 1:
            std_ratio = np.std(values) / (np.mean(values) + 1e-8)
            agreement_score = max(0, 1 - std_ratio)
        else:
            agreement_score = 0.5
            
        # Data quality score
        data_length_score = min(1.0, len(historical_data) / 30)  # Full score at 30+ days
        data_variance = historical_data.std() / (historical_data.mean() + 1e-8)
        stability_score = max(0, 1 - data_variance)
        
        # Combine scores
        confidence = (agreement_score * 0.4 + 
                     data_length_score * 0.3 + 
                     stability_score * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_explanation(self, prediction: Dict, model_predictions: Dict, 
                            historical_data: pd.Series, context: Dict) -> str:
        """Generate plain language explanation."""
        explanation_parts = []
        
        # Main prediction
        explanation_parts.append(
            f"Based on your recent patterns, we expect your {historical_data.name} "
            f"to be around {prediction['value']:.1f} tomorrow."
        )
        
        # Key factors
        factors = self._identify_key_factors(model_predictions, historical_data)
        if factors:
            factor_text = "Key factors: " + ", ".join(factors)
            explanation_parts.append(factor_text)
            
        return " ".join(explanation_parts)
    
    def _identify_key_factors(self, model_predictions: Dict, data: pd.Series) -> List[str]:
        """Identify main factors affecting prediction."""
        factors = []
        
        # Recent trend
        if len(data) >= 7:
            recent_avg = data.iloc[-3:].mean()
            older_avg = data.iloc[-7:-3].mean()
            if recent_avg > older_avg * 1.05:
                factors.append("recent increasing trend")
            elif recent_avg < older_avg * 0.95:
                factors.append("recent decreasing trend")
                
        # Feature importance from RF
        if 'random_forest' in model_predictions:
            rf_pred = model_predictions['random_forest']
            if 'feature_importance' in rf_pred and rf_pred['feature_importance']:
                top_feature = max(rf_pred['feature_importance'], 
                                key=rf_pred['feature_importance'].get)
                factors.append(f"{self._humanize_feature(top_feature)}")
                
        return factors[:3]  # Top 3 factors
    
    def _humanize_feature(self, feature_name: str) -> str:
        """Convert feature names to human-readable text."""
        mappings = {
            'lag_1': 'yesterday\'s value',
            'lag_7': 'last week\'s pattern',
            'rolling_mean_7': '7-day average',
            'day_of_week': 'day of week pattern',
            'is_weekend': 'weekend effect',
            'linear_trend': 'overall trend'
        }
        return mappings.get(feature_name, feature_name.replace('_', ' '))
    
    def _analyze_trend_direction(self, forecast: List[float]) -> str:
        """Analyze trend direction from forecast."""
        if len(forecast) < 2:
            return 'stable'
            
        start_avg = np.mean(forecast[:2])
        end_avg = np.mean(forecast[-2:])
        
        if end_avg > start_avg * 1.05:
            return 'increasing'
        elif end_avg < start_avg * 0.95:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_trend_confidence(self, forecast: List[float]) -> float:
        """Calculate confidence in trend direction."""
        if len(forecast) < 3:
            return 0.5
            
        # Calculate trend consistency
        diffs = np.diff(forecast)
        if len(diffs) == 0:
            return 0.5
            
        # Check if trend is consistent
        positive_changes = sum(1 for d in diffs if d > 0)
        negative_changes = sum(1 for d in diffs if d < 0)
        
        consistency = max(positive_changes, negative_changes) / len(diffs)
        return consistency
    
    def _generate_weekly_insights(self, forecast: List[float], historical_data: pd.Series) -> List[str]:
        """Generate insights from weekly forecast."""
        insights = []
        
        # Compare to historical average
        if len(historical_data) >= 7:
            historical_avg = historical_data.iloc[-7:].mean()
            forecast_avg = np.mean(forecast)
            
            if forecast_avg > historical_avg * 1.1:
                insights.append("Forecast shows above-average values expected")
            elif forecast_avg < historical_avg * 0.9:
                insights.append("Forecast shows below-average values expected")
            else:
                insights.append("Forecast shows values similar to recent patterns")
                
        # Identify peak day
        if forecast:
            peak_day = np.argmax(forecast)
            peak_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                           'Friday', 'Saturday', 'Sunday'][peak_day]
            insights.append(f"Highest value expected on {peak_day_name}")
            
        return insights


@dataclass
class Goal:
    """Container for user health goals."""
    metric: str
    target_value: float
    current_value: float
    target_date: datetime
    goal_type: str  # 'increase', 'decrease', 'maintain'


class MonteCarloSimulator:
    """Monte Carlo simulation for goal achievement."""
    
    def simulate_to_goal(self, goal: Goal, current_data: pd.Series, n_simulations: int = 1000) -> Dict:
        """Simulate paths to goal achievement."""
        try:
            success_count = 0
            times_to_goal = []
            
            # Calculate daily change statistics
            if len(current_data) >= 7:
                daily_changes = current_data.diff().dropna()
                mean_change = daily_changes.mean()
                std_change = daily_changes.std()
            else:
                mean_change = 0
                std_change = current_data.std() / 10
                
            days_available = (goal.target_date - datetime.now()).days
            
            for _ in range(n_simulations):
                current_value = goal.current_value
                days_elapsed = 0
                
                for day in range(days_available):
                    # Simulate daily change
                    daily_change = np.random.normal(mean_change, std_change)
                    current_value += daily_change
                    days_elapsed += 1
                    
                    # Check if goal reached
                    if goal.goal_type == 'increase' and current_value >= goal.target_value:
                        success_count += 1
                        times_to_goal.append(days_elapsed)
                        break
                    elif goal.goal_type == 'decrease' and current_value <= goal.target_value:
                        success_count += 1
                        times_to_goal.append(days_elapsed)
                        break
                        
                # Check final achievement for 'maintain' goals
                if goal.goal_type == 'maintain':
                    tolerance = abs(goal.target_value * 0.05)  # 5% tolerance
                    if abs(current_value - goal.target_value) <= tolerance:
                        success_count += 1
                        times_to_goal.append(days_available)
                        
            success_rate = success_count / n_simulations
            avg_time_to_goal = np.mean(times_to_goal) if times_to_goal else None
            
            return {
                'success_rate': success_rate,
                'avg_time_to_goal': avg_time_to_goal,
                'simulation_count': n_simulations
            }
            
        except Exception as e:
            logging.error(f"Monte Carlo simulation failed: {e}")
            return {
                'success_rate': 0.5,
                'avg_time_to_goal': None,
                'simulation_count': 0
            }


class HistoricalSimulator:
    """Historical pattern-based simulation."""
    
    def simulate_to_goal(self, goal: Goal, current_data: pd.Series, n_simulations: int = 1000) -> Dict:
        """Simulate using historical patterns."""
        try:
            if len(current_data) < 14:
                return {'success_rate': 0.5, 'avg_time_to_goal': None, 'simulation_count': 0}
                
            # Extract historical patterns
            weekly_patterns = []
            for i in range(0, len(current_data) - 7, 7):
                week_data = current_data.iloc[i:i+7]
                if len(week_data) == 7:
                    weekly_patterns.append(week_data.values)
                    
            if not weekly_patterns:
                return {'success_rate': 0.5, 'avg_time_to_goal': None, 'simulation_count': 0}
                
            success_count = 0
            times_to_goal = []
            days_available = (goal.target_date - datetime.now()).days
            
            for _ in range(n_simulations):
                current_value = goal.current_value
                days_elapsed = 0
                
                # Simulate using random historical weeks
                while days_elapsed < days_available:
                    # Pick a random historical week
                    week_pattern = weekly_patterns[np.random.randint(len(weekly_patterns))]
                    
                    for daily_value in week_pattern:
                        if days_elapsed >= days_available:
                            break
                            
                        current_value = daily_value
                        days_elapsed += 1
                        
                        # Check goal achievement
                        if goal.goal_type == 'increase' and current_value >= goal.target_value:
                            success_count += 1
                            times_to_goal.append(days_elapsed)
                            break
                        elif goal.goal_type == 'decrease' and current_value <= goal.target_value:
                            success_count += 1
                            times_to_goal.append(days_elapsed)
                            break
                    else:
                        continue
                    break
                    
            success_rate = success_count / n_simulations
            avg_time_to_goal = np.mean(times_to_goal) if times_to_goal else None
            
            return {
                'success_rate': success_rate,
                'avg_time_to_goal': avg_time_to_goal,
                'simulation_count': n_simulations
            }
            
        except Exception as e:
            logging.error(f"Historical simulation failed: {e}")
            return {'success_rate': 0.5, 'avg_time_to_goal': None, 'simulation_count': 0}


class GoalAchievementPredictor:
    """Predicts goal achievement probability using multiple simulation methods."""
    
    def __init__(self):
        self.simulators = {
            'monte_carlo': MonteCarloSimulator(),
            'historical': HistoricalSimulator()
        }
        
    def predict_goal_achievement(self, goal: Goal, current_data: pd.Series) -> GoalPrediction:
        """Predict probability of achieving goal."""
        try:
            # Run simulations
            simulation_results = {}
            
            for name, simulator in self.simulators.items():
                results = simulator.simulate_to_goal(goal, current_data, n_simulations=1000)
                simulation_results[name] = results
                
            # Aggregate results
            probabilities = [r['success_rate'] for r in simulation_results.values()]
            mean_probability = np.mean(probabilities)
            
            # Time estimates
            time_estimates = [r['avg_time_to_goal'] for r in simulation_results.values() 
                            if r['avg_time_to_goal'] is not None]
            estimated_time = int(np.median(time_estimates)) if time_estimates else None
            
            # Required daily targets
            daily_targets = self._calculate_required_daily_targets(goal, current_data)
            
            # Milestone predictions
            milestones = self._predict_milestones(goal, current_data, mean_probability)
            
            # Success factors
            factors = self._identify_success_factors(simulation_results, current_data)
            
            return GoalPrediction(
                success_probability=mean_probability,
                confidence_interval=(np.percentile(probabilities, 25), 
                                   np.percentile(probabilities, 75)),
                estimated_time_days=estimated_time,
                daily_targets=daily_targets,
                milestones=milestones,
                factors=factors
            )
            
        except Exception as e:
            logging.error(f"Goal achievement prediction failed: {e}")
            # Return fallback prediction
            return GoalPrediction(
                success_probability=0.5,
                confidence_interval=(0.3, 0.7),
                estimated_time_days=None,
                daily_targets={},
                milestones=[],
                factors=['Insufficient data for detailed analysis']
            )
    
    def _calculate_required_daily_targets(self, goal: Goal, current_data: pd.Series) -> Dict[str, float]:
        """Calculate required daily targets to achieve goal."""
        try:
            days_remaining = (goal.target_date - datetime.now()).days
            if days_remaining <= 0:
                return {}
                
            value_gap = goal.target_value - goal.current_value
            daily_change_needed = value_gap / days_remaining
            
            # Calculate different pacing strategies
            current_avg = current_data.iloc[-7:].mean() if len(current_data) >= 7 else goal.current_value
            
            return {
                'linear_daily_change': daily_change_needed,
                'current_pace': (current_avg - current_data.iloc[0]) / len(current_data) if len(current_data) > 1 else 0,
                'recommended_daily_value': goal.current_value + daily_change_needed,
                'days_remaining': days_remaining
            }
            
        except Exception:
            return {}
    
    def _predict_milestones(self, goal: Goal, current_data: pd.Series, probability: float) -> List[Dict]:
        """Predict milestone achievements."""
        try:
            milestones = []
            days_remaining = (goal.target_date - datetime.now()).days
            
            if days_remaining <= 0:
                return milestones
                
            value_gap = goal.target_value - goal.current_value
            
            # Create milestones at 25%, 50%, 75% progress
            for pct in [0.25, 0.5, 0.75]:
                milestone_value = goal.current_value + (value_gap * pct)
                milestone_date = datetime.now() + timedelta(days=int(days_remaining * pct))
                milestone_probability = probability * (1 - pct * 0.2)  # Decrease probability over time
                
                milestones.append({
                    'percentage': int(pct * 100),
                    'target_value': milestone_value,
                    'target_date': milestone_date,
                    'probability': milestone_probability
                })
                
            return milestones
            
        except Exception:
            return []
    
    def _identify_success_factors(self, simulation_results: Dict, current_data: pd.Series) -> List[str]:
        """Identify factors that contribute to goal success."""
        factors = []
        
        try:
            # Data consistency factor
            if len(current_data) >= 7:
                cv = current_data.std() / current_data.mean()
                if cv < 0.2:
                    factors.append("Consistent daily patterns")
                elif cv > 0.5:
                    factors.append("High variability in measurements")
                    
            # Trend factor
            if len(current_data) >= 14:
                recent_trend = current_data.iloc[-7:].mean() - current_data.iloc[-14:-7].mean()
                if abs(recent_trend) > current_data.std() * 0.5:
                    direction = "positive" if recent_trend > 0 else "negative"
                    factors.append(f"Strong {direction} recent trend")
                    
            # Data completeness
            if len(current_data) >= 30:
                factors.append("Sufficient historical data")
            else:
                factors.append("Limited historical data")
                
        except Exception:
            factors.append("Basic analysis only")
            
        return factors


class AnomalyRiskModel:
    """Detects anomalous patterns in health data."""
    
    def assess_risk(self, metric: str, data: pd.Series) -> HealthRisk:
        """Assess anomaly risk for a metric."""
        try:
            if len(data) < 7:
                return HealthRisk(
                    metric=metric,
                    severity=RiskLevel.LOW,
                    probability=0.1,
                    description="Insufficient data for anomaly detection",
                    recommendations=["Continue monitoring to build baseline"]
                )
                
            # Calculate statistical bounds
            mean = data.mean()
            std = data.std()
            recent_values = data.iloc[-3:]
            
            # Check for outliers
            z_scores = np.abs((recent_values - mean) / std)
            max_z_score = z_scores.max()
            
            if max_z_score > 3:
                severity = RiskLevel.HIGH
                probability = 0.8
                description = f"Recent {metric} values show significant deviation from normal patterns"
                recommendations = [
                    "Review recent activities and factors",
                    "Consider consulting healthcare provider",
                    "Monitor closely for next few days"
                ]
            elif max_z_score > 2:
                severity = RiskLevel.MEDIUM
                probability = 0.6
                description = f"Moderate deviation detected in {metric}"
                recommendations = [
                    "Monitor for continued deviation",
                    "Review recent lifestyle changes"
                ]
            else:
                severity = RiskLevel.LOW
                probability = 0.1
                description = f"{metric} values within normal range"
                recommendations = ["Continue regular monitoring"]
                
            return HealthRisk(
                metric=metric,
                severity=severity,
                probability=probability,
                description=description,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Anomaly risk assessment failed: {e}")
            return HealthRisk(
                metric=metric,
                severity=RiskLevel.LOW,
                probability=0.0,
                description="Risk assessment unavailable",
                recommendations=["Continue monitoring"]
            )


class TrendRiskModel:
    """Assesses risk based on concerning trends."""
    
    def assess_risk(self, metric: str, data: pd.Series) -> HealthRisk:
        """Assess trend-based risk for a metric."""
        try:
            if len(data) < 14:
                return HealthRisk(
                    metric=metric,
                    severity=RiskLevel.LOW,
                    probability=0.1,
                    description="Insufficient data for trend analysis",
                    recommendations=["Continue monitoring to establish trends"]
                )
                
            # Calculate trend over different periods
            recent_trend = self._calculate_trend(data.iloc[-7:])
            medium_trend = self._calculate_trend(data.iloc[-14:])
            
            # Assess trend severity based on metric type
            risk_thresholds = self._get_risk_thresholds(metric)
            
            # Determine risk level
            if abs(recent_trend) > risk_thresholds['high']:
                severity = RiskLevel.HIGH
                probability = 0.7
                direction = "increasing" if recent_trend > 0 else "decreasing"
                description = f"Concerning {direction} trend in {metric}"
                recommendations = [
                    "Consider lifestyle modifications",
                    "Consult healthcare provider if trend continues",
                    "Monitor daily"
                ]
            elif abs(recent_trend) > risk_thresholds['medium']:
                severity = RiskLevel.MEDIUM
                probability = 0.5
                direction = "increasing" if recent_trend > 0 else "decreasing"
                description = f"Moderate {direction} trend in {metric}"
                recommendations = [
                    "Monitor trend development",
                    "Consider preventive measures"
                ]
            else:
                severity = RiskLevel.LOW
                probability = 0.2
                description = f"{metric} trend within normal range"
                recommendations = ["Continue regular monitoring"]
                
            return HealthRisk(
                metric=metric,
                severity=severity,
                probability=probability,
                description=description,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Trend risk assessment failed: {e}")
            return HealthRisk(
                metric=metric,
                severity=RiskLevel.LOW,
                probability=0.0,
                description="Risk assessment unavailable",
                recommendations=["Continue monitoring"]
            )
    
    def _calculate_trend(self, data: pd.Series) -> float:
        """Calculate trend slope as percentage change per day."""
        if len(data) < 2:
            return 0.0
            
        x = np.arange(len(data))
        slope, _ = np.polyfit(x, data.values, 1)
        
        # Convert to percentage change per day
        mean_value = data.mean()
        return (slope / mean_value) * 100 if mean_value != 0 else 0.0
    
    def _get_risk_thresholds(self, metric: str) -> Dict[str, float]:
        """Get risk thresholds for different metrics."""
        # Default thresholds (percentage change per day)
        default_thresholds = {'medium': 2.0, 'high': 5.0}
        
        # Metric-specific thresholds
        metric_thresholds = {
            'HeartRate': {'medium': 1.0, 'high': 3.0},
            'BloodPressure': {'medium': 1.5, 'high': 4.0},
            'Weight': {'medium': 0.5, 'high': 1.5},
            'Steps': {'medium': 10.0, 'high': 25.0}
        }
        
        return metric_thresholds.get(metric, default_thresholds)


class HealthRiskPredictor:
    """Comprehensive health risk assessment system."""
    
    def __init__(self):
        self.risk_models = {
            'anomaly': AnomalyRiskModel(),
            'trend': TrendRiskModel()
        }
        
    def assess_health_risks(self, health_data: Dict[str, pd.Series]) -> RiskAssessment:
        """Comprehensive health risk assessment."""
        try:
            all_risks = []
            
            # Assess risks for each metric
            for metric, data in health_data.items():
                for model_name, model in self.risk_models.items():
                    try:
                        risk = model.assess_risk(metric, data)
                        if risk.severity != RiskLevel.LOW or risk.probability > 0.3:
                            all_risks.append(risk)
                    except Exception as e:
                        logging.warning(f"Risk assessment failed for {metric} with {model_name}: {e}")
                        
            # Prioritize risks
            prioritized_risks = self._prioritize_risks(all_risks)
            
            # Calculate overall risk level
            overall_risk = self._calculate_overall_risk(prioritized_risks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(prioritized_risks)
            
            # Determine next check date
            next_check = self._determine_next_check(overall_risk)
            
            return RiskAssessment(
                risks=prioritized_risks,
                overall_risk_level=overall_risk,
                recommendations=recommendations,
                next_check_date=next_check
            )
            
        except Exception as e:
            logging.error(f"Health risk assessment failed: {e}")
            return RiskAssessment(
                risks=[],
                overall_risk_level=RiskLevel.LOW,
                recommendations=["Regular monitoring recommended"],
                next_check_date=datetime.now() + timedelta(days=7)
            )
    
    def _prioritize_risks(self, risks: List[HealthRisk]) -> List[HealthRisk]:
        """Prioritize risks by severity and probability."""
        severity_order = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, 
                         RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        
        return sorted(risks, 
                     key=lambda r: (severity_order[r.severity], r.probability), 
                     reverse=True)
    
    def _calculate_overall_risk(self, risks: List[HealthRisk]) -> RiskLevel:
        """Calculate overall risk level from individual risks."""
        if not risks:
            return RiskLevel.LOW
            
        # Check for critical or high risks
        high_severity_risks = [r for r in risks if r.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        if high_severity_risks:
            return RiskLevel.HIGH
            
        # Check for multiple medium risks
        medium_risks = [r for r in risks if r.severity == RiskLevel.MEDIUM]
        if len(medium_risks) >= 2:
            return RiskLevel.MEDIUM
        elif len(medium_risks) == 1:
            return RiskLevel.MEDIUM
            
        return RiskLevel.LOW
    
    def _generate_recommendations(self, risks: List[HealthRisk]) -> List[str]:
        """Generate consolidated recommendations."""
        all_recommendations = []
        
        for risk in risks[:3]:  # Top 3 risks
            all_recommendations.extend(risk.recommendations)
            
        # Remove duplicates while preserving order
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)
                
        return unique_recommendations[:5]  # Top 5 recommendations
    
    def _determine_next_check(self, overall_risk: RiskLevel) -> datetime:
        """Determine next check date based on risk level."""
        days_map = {
            RiskLevel.CRITICAL: 1,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 7,
            RiskLevel.LOW: 14
        }
        
        days = days_map.get(overall_risk, 7)
        return datetime.now() + timedelta(days=days)


class PredictionsDatabase:
    """Simple in-memory database for storing predictions (could be extended to persistent storage)."""
    
    def __init__(self):
        self.predictions = []
        
    def store(self, metric: str, date: datetime, predicted_value: float, 
              confidence_interval: Tuple[float, float], model_contributions: Dict):
        """Store a prediction for later accuracy calculation."""
        self.predictions.append({
            'metric': metric,
            'date': date,
            'predicted_value': predicted_value,
            'confidence_interval': confidence_interval,
            'model_contributions': model_contributions,
            'stored_at': datetime.now()
        })
        
    def get_predictions(self, metric: str, lookback_days: int) -> List[Dict]:
        """Get predictions for a metric within lookback period."""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        return [p for p in self.predictions 
                if p['metric'] == metric and p['date'] >= cutoff_date]
    
    def clear_old_predictions(self, days_to_keep: int = 90):
        """Clear predictions older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        self.predictions = [p for p in self.predictions if p['stored_at'] >= cutoff_date]


class AccuracyTracker:
    """Tracks prediction accuracy over time."""
    
    def __init__(self):
        self.predictions_db = PredictionsDatabase()
        
    def track_prediction(self, prediction: Prediction, metric: str, date: datetime):
        """Store prediction for later accuracy calculation."""
        self.predictions_db.store(
            metric=metric,
            date=date,
            predicted_value=prediction.value,
            confidence_interval=prediction.confidence_interval,
            model_contributions=prediction.model_contributions
        )
        
    def calculate_accuracy(self, metric: str, actual_data: pd.Series, 
                          lookback_days: int = 30) -> AccuracyReport:
        """Calculate prediction accuracy over time."""
        try:
            predictions = self.predictions_db.get_predictions(metric, lookback_days)
            
            if not predictions:
                return AccuracyReport(
                    overall_mae=0.0,
                    overall_rmse=0.0,
                    interval_coverage=0.0,
                    model_accuracy={},
                    trend_accuracy=0.0,
                    recommendations=["No predictions available for accuracy assessment"]
                )
            
            # Match predictions with actual values
            matched_pairs = []
            for pred in predictions:
                pred_date = pred['date']
                
                # Find actual value for this date
                if pred_date in actual_data.index:
                    actual_value = actual_data[pred_date]
                    matched_pairs.append({
                        'predicted': pred['predicted_value'],
                        'actual': actual_value,
                        'confidence_interval': pred['confidence_interval'],
                        'model_contributions': pred['model_contributions']
                    })
                    
            if not matched_pairs:
                return AccuracyReport(
                    overall_mae=0.0,
                    overall_rmse=0.0,
                    interval_coverage=0.0,
                    model_accuracy={},
                    trend_accuracy=0.0,
                    recommendations=["No matching actual values found for predictions"]
                )
            
            # Calculate overall accuracy metrics
            predicted_values = [p['predicted'] for p in matched_pairs]
            actual_values = [p['actual'] for p in matched_pairs]
            
            mae = mean_absolute_error(actual_values, predicted_values)
            rmse = np.sqrt(mean_squared_error(actual_values, predicted_values))
            
            # Calculate confidence interval coverage
            coverage = self._calculate_interval_coverage(matched_pairs)
            
            # Calculate model-specific accuracy
            model_accuracy = self._calculate_model_accuracy(matched_pairs)
            
            # Calculate trend accuracy
            trend_accuracy = self._calculate_trend_accuracy(predicted_values, actual_values)
            
            # Generate recommendations
            recommendations = self._generate_accuracy_recommendations(mae, rmse, coverage, model_accuracy)
            
            return AccuracyReport(
                overall_mae=mae,
                overall_rmse=rmse,
                interval_coverage=coverage,
                model_accuracy=model_accuracy,
                trend_accuracy=trend_accuracy,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Accuracy calculation failed: {e}")
            return AccuracyReport(
                overall_mae=0.0,
                overall_rmse=0.0,
                interval_coverage=0.0,
                model_accuracy={},
                trend_accuracy=0.0,
                recommendations=["Accuracy calculation failed"]
            )
    
    def _calculate_interval_coverage(self, matched_pairs: List[Dict]) -> float:
        """Calculate percentage of actual values within confidence intervals."""
        if not matched_pairs:
            return 0.0
            
        within_interval = 0
        for pair in matched_pairs:
            actual = pair['actual']
            lower, upper = pair['confidence_interval']
            if lower <= actual <= upper:
                within_interval += 1
                
        return within_interval / len(matched_pairs)
    
    def _calculate_model_accuracy(self, matched_pairs: List[Dict]) -> Dict[str, Dict]:
        """Calculate accuracy for individual models."""
        model_accuracy = {}
        
        # Group by model contributions
        model_predictions = defaultdict(list)
        
        for pair in matched_pairs:
            actual = pair['actual']
            for model_name, model_pred in pair['model_contributions'].items():
                if 'value' in model_pred:
                    model_predictions[model_name].append({
                        'predicted': model_pred['value'],
                        'actual': actual
                    })
                    
        # Calculate accuracy for each model
        for model_name, predictions in model_predictions.items():
            if predictions:
                predicted_vals = [p['predicted'] for p in predictions]
                actual_vals = [p['actual'] for p in predictions]
                
                model_mae = mean_absolute_error(actual_vals, predicted_vals)
                model_rmse = np.sqrt(mean_squared_error(actual_vals, predicted_vals))
                
                model_accuracy[model_name] = {
                    'mae': model_mae,
                    'rmse': model_rmse,
                    'sample_size': len(predictions)
                }
                
        return model_accuracy
    
    def _calculate_trend_accuracy(self, predicted_values: List[float], 
                                actual_values: List[float]) -> float:
        """Calculate accuracy of trend predictions."""
        if len(predicted_values) < 3:
            return 0.5
            
        # Calculate trend directions
        pred_trend = np.mean(np.diff(predicted_values))
        actual_trend = np.mean(np.diff(actual_values))
        
        # Check if trends are in same direction
        if pred_trend * actual_trend > 0:
            return 1.0  # Same direction
        elif pred_trend == 0 and actual_trend == 0:
            return 1.0  # Both flat
        else:
            return 0.0  # Opposite directions
    
    def _generate_accuracy_recommendations(self, mae: float, rmse: float, 
                                         coverage: float, model_accuracy: Dict) -> List[str]:
        """Generate recommendations based on accuracy metrics."""
        recommendations = []
        
        # Overall accuracy assessment
        if mae > rmse * 1.5:  # High variability in errors
            recommendations.append("Consider improving model stability")
            
        # Confidence interval coverage
        if coverage < 0.8:
            recommendations.append("Confidence intervals may be too narrow")
        elif coverage > 0.95:
            recommendations.append("Confidence intervals may be too wide")
            
        # Model performance comparison
        if model_accuracy:
            best_model = min(model_accuracy.items(), key=lambda x: x[1]['mae'])
            worst_model = max(model_accuracy.items(), key=lambda x: x[1]['mae'])
            
            if best_model[1]['mae'] < worst_model[1]['mae'] * 0.8:
                recommendations.append(f"Consider weighting {best_model[0]} model higher")
                
        # General recommendations
        if not recommendations:
            recommendations.append("Prediction accuracy is acceptable")
            
        return recommendations


@dataclass
class PredictionVariant:
    """Container for A/B test prediction variants."""
    name: str
    description: str
    model_config: Dict
    weight_config: Dict


@dataclass
class Experiment:
    """Container for A/B test experiments."""
    name: str
    variants: List[PredictionVariant]
    metrics: List[str]
    min_sample_size: int
    outcomes: Dict = None
    
    def __post_init__(self):
        if self.outcomes is None:
            self.outcomes = {variant.name: [] for variant in self.variants}
    
    def record_outcome(self, variant: PredictionVariant, outcome: Dict):
        """Record an outcome for a variant."""
        self.outcomes[variant.name].append(outcome)
        
    def has_sufficient_data(self) -> bool:
        """Check if experiment has sufficient data for analysis."""
        for variant_outcomes in self.outcomes.values():
            if len(variant_outcomes) < self.min_sample_size:
                return False
        return True


class RandomAssignment:
    """Random assignment strategy for A/B tests."""
    
    def assign(self, user_id: str, experiment: Experiment) -> PredictionVariant:
        """Assign user to experiment variant."""
        # Use hash of user_id for consistent assignment
        import hashlib
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        variant_index = hash_value % len(experiment.variants)
        return experiment.variants[variant_index]


class PredictionABTester:
    """A/B testing framework for prediction models."""
    
    def __init__(self):
        self.experiments = {}
        self.assignment_strategy = RandomAssignment()
        
    def create_experiment(self, name: str, variants: List[PredictionVariant]) -> Experiment:
        """Create new A/B test for predictions."""
        experiment = Experiment(
            name=name,
            variants=variants,
            metrics=['mae', 'user_trust', 'action_taken'],
            min_sample_size=self._calculate_sample_size(len(variants))
        )
        
        self.experiments[name] = experiment
        return experiment
        
    def assign_variant(self, user_id: str, experiment_name: str) -> PredictionVariant:
        """Assign user to experiment variant."""
        if experiment_name not in self.experiments:
            raise ValueError(f"Experiment {experiment_name} not found")
            
        experiment = self.experiments[experiment_name]
        return self.assignment_strategy.assign(user_id, experiment)
        
    def record_outcome(self, user_id: str, experiment_name: str, outcomes: Dict):
        """Record experiment outcomes."""
        if experiment_name not in self.experiments:
            return
            
        experiment = self.experiments[experiment_name]
        variant = self.get_user_variant(user_id, experiment_name)
        
        experiment.record_outcome(variant, outcomes)
        
        # Check if we can conclude experiment
        if experiment.has_sufficient_data():
            self.analyze_experiment(experiment)
            
    def get_user_variant(self, user_id: str, experiment_name: str) -> PredictionVariant:
        """Get the variant assigned to a user."""
        experiment = self.experiments[experiment_name]
        return self.assignment_strategy.assign(user_id, experiment)
        
    def analyze_experiment(self, experiment: Experiment) -> Dict:
        """Analyze experiment results."""
        try:
            results = {}
            
            for variant in experiment.variants:
                variant_outcomes = experiment.outcomes[variant.name]
                
                if not variant_outcomes:
                    results[variant.name] = {
                        'mae': float('inf'),
                        'user_trust': 0.0,
                        'action_taken': 0.0,
                        'sample_size': 0
                    }
                    continue
                    
                # Calculate metrics
                mae_values = [o.get('mae', 0) for o in variant_outcomes]
                trust_values = [o.get('user_trust', 0) for o in variant_outcomes]
                action_values = [o.get('action_taken', 0) for o in variant_outcomes]
                
                results[variant.name] = {
                    'mae': np.mean(mae_values),
                    'user_trust': np.mean(trust_values),
                    'action_taken': np.mean(action_values),
                    'sample_size': len(variant_outcomes)
                }
                
            # Determine winner
            winner = self._determine_winner(results)
            results['winner'] = winner
            results['statistical_significance'] = self._check_significance(experiment)
            
            logging.info(f"Experiment {experiment.name} results: {results}")
            return results
            
        except Exception as e:
            logging.error(f"Experiment analysis failed: {e}")
            return {}
    
    def _calculate_sample_size(self, num_variants: int) -> int:
        """Calculate minimum sample size for experiment."""
        # Simple heuristic: more variants need more samples
        base_size = 50
        return base_size * num_variants
    
    def _determine_winner(self, results: Dict) -> str:
        """Determine winning variant based on composite score."""
        best_variant = None
        best_score = -float('inf')
        
        for variant_name, metrics in results.items():
            if isinstance(metrics, dict) and 'mae' in metrics:
                # Composite score: lower MAE is better, higher trust and action are better
                score = (
                    -metrics['mae'] +  # Lower MAE is better
                    metrics['user_trust'] * 2 +  # Weight trust highly
                    metrics['action_taken']
                )
                
                if score > best_score:
                    best_score = score
                    best_variant = variant_name
                    
        return best_variant
    
    def _check_significance(self, experiment: Experiment) -> bool:
        """Check if results are statistically significant (simplified)."""
        # Simplified significance check
        min_effect_size = 0.1  # 10% improvement
        
        variants = list(experiment.variants)
        if len(variants) < 2:
            return False
            
        # Compare first two variants as example
        outcomes_a = experiment.outcomes[variants[0].name]
        outcomes_b = experiment.outcomes[variants[1].name]
        
        if len(outcomes_a) < 30 or len(outcomes_b) < 30:
            return False  # Need sufficient sample size
            
        # Simple effect size check
        mae_a = np.mean([o.get('mae', 0) for o in outcomes_a])
        mae_b = np.mean([o.get('mae', 0) for o in outcomes_b])
        
        effect_size = abs(mae_a - mae_b) / max(mae_a, mae_b, 1e-8)
        return effect_size >= min_effect_size