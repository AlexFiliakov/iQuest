"""Advanced trend analysis engine with Prophet integration and statistical validation."""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import logging
from scipy import stats
from scipy.signal import find_peaks
import warnings

from .advanced_trend_models import (
    TrendAnalysis, AdvancedTrendAnalysis, TrendClassification, EvidenceQuality,
    PredictionQuality, ChangePoint, PredictionPoint, SeasonalComponent,
    TrendComponent, TrendDecomposition, ValidationResult, EnsembleResult,
    WSJVisualizationConfig
)

# Try to import optional dependencies
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    warnings.warn("Prophet not available. Using fallback methods.")

try:
    from statsmodels.tsa.seasonal import STL
    STL_AVAILABLE = True
except ImportError:
    STL_AVAILABLE = False
    warnings.warn("STL not available. Using simple decomposition.")

logger = logging.getLogger(__name__)


class AdvancedTrendAnalysisEngine:
    """Advanced trend analysis following WSJ analytics principles."""
    
    def __init__(self, style_manager: Optional[Any] = None):
        self.style_manager = style_manager
        
        # Ensemble weights for different methods
        self.ensemble_weights = {
            'prophet': 0.5 if PROPHET_AVAILABLE else 0.0,
            'stl': 0.3 if STL_AVAILABLE else 0.0,
            'linear': 0.2
        }
        
        # Normalize weights if Prophet/STL not available
        total_weight = sum(self.ensemble_weights.values())
        if total_weight > 0:
            self.ensemble_weights = {
                k: v/total_weight for k, v in self.ensemble_weights.items()
            }
        
        # Trend classification thresholds
        self.trend_thresholds = {
            'strongly_increasing': 0.05,  # 5% daily increase
            'increasing': 0.01,           # 1% daily increase
            'stable': 0.01,              # ±1% daily change
            'decreasing': -0.01,         # -1% daily decrease
            'strongly_decreasing': -0.05  # -5% daily decrease
        }
        
        # Cache for Prophet models
        self._prophet_cache = {}
        
    def analyze_trend_comprehensive(
        self, 
        data: pd.Series, 
        metric_name: str,
        health_context: Optional[Dict[str, Any]] = None,
        forecast_days: int = 7
    ) -> TrendAnalysis:
        """Comprehensive trend analysis with health context."""
        
        # Ensure we have datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # Clean and validate data
        clean_data = self._clean_data(data)
        
        # Check data quality
        data_quality = self._assess_data_quality(clean_data)
        evidence_quality = self._determine_evidence_quality(clean_data)
        
        # Primary analysis with Prophet (if available)
        if PROPHET_AVAILABLE and len(clean_data) >= 14:
            prophet_result = self._analyze_with_prophet(clean_data, forecast_days)
        else:
            prophet_result = None
            
        # Statistical validation
        statistical_result = self._validate_trend_statistically(clean_data)
        
        # Decomposition analysis
        decomposition = self._decompose_time_series(clean_data)
        
        # Ensemble analysis
        ensemble_result = self._ensemble_analysis(
            clean_data, prophet_result, statistical_result, decomposition
        )
        
        # Change point detection
        change_points = self._detect_change_points(clean_data)
        
        # Volatility analysis
        volatility_analysis = self._analyze_volatility(clean_data)
        
        # Generate predictions
        predictions = self._generate_predictions(
            clean_data, prophet_result, ensemble_result, forecast_days
        )
        
        # Health context interpretation
        interpretation = self._interpret_health_context(
            ensemble_result, metric_name, health_context or {}
        )
        
        # Generate WSJ-style summary
        summary = self._generate_wsj_summary(
            ensemble_result, interpretation, metric_name
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            ensemble_result, metric_name, health_context or {}
        )
        
        # Convert TrendClassification enum to string for spec compliance
        trend_direction_str = self._trend_classification_to_string(ensemble_result.primary_trend)
        
        # Convert EvidenceQuality enum to string
        evidence_quality_str = evidence_quality.value
        
        return TrendAnalysis(
            # Required fields per specification
            trend_direction=trend_direction_str,
            trend_strength=self._calculate_trend_strength(statistical_result),
            confidence=ensemble_result.confidence,
            statistical_significance=statistical_result['mann_kendall'].p_value,
            seasonal_component=self._has_significant_seasonality(decomposition),
            seasonal_strength=self._calculate_seasonal_strength(decomposition),
            volatility_level=volatility_analysis['level'],
            volatility_score=volatility_analysis['score'],
            predictions=predictions,
            change_points=change_points,
            summary=summary,
            evidence_quality=evidence_quality_str,
            interpretation=interpretation,
            # Enhanced optional fields
            seasonal_components=self._extract_seasonal_components(decomposition, clean_data),
            volatility_trend=volatility_analysis['trend'],
            methods_used=self._get_methods_used(),
            ensemble_agreement=ensemble_result.agreement_score,
            data_quality_score=data_quality,
            recommendations=recommendations,
            forecast_horizon=forecast_days,
            structural_breaks=self._find_structural_breaks(change_points)
        )
    
    def _clean_data(self, data: pd.Series) -> pd.Series:
        """Clean and prepare data for analysis."""
        # Remove NaN values
        clean_data = data.dropna()
        
        # Sort by index
        clean_data = clean_data.sort_index()
        
        # Remove duplicates
        clean_data = clean_data[~clean_data.index.duplicated(keep='first')]
        
        # Handle outliers (using IQR method)
        Q1 = clean_data.quantile(0.25)
        Q3 = clean_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Cap outliers instead of removing
        clean_data = clean_data.clip(lower=lower_bound, upper=upper_bound)
        
        return clean_data
    
    def _assess_data_quality(self, data: pd.Series) -> float:
        """Assess data quality score (0-1)."""
        if len(data) == 0:
            return 0.0
            
        # Factors for quality assessment
        factors = []
        
        # Data completeness (check for gaps)
        date_range = pd.date_range(data.index.min(), data.index.max(), freq='D')
        completeness = len(data) / len(date_range)
        factors.append(completeness)
        
        # Data consistency (coefficient of variation)
        cv = data.std() / data.mean() if data.mean() != 0 else 1.0
        consistency = 1.0 - min(cv, 1.0)
        factors.append(consistency)
        
        # Data recency
        days_old = (datetime.now() - data.index.max()).days
        recency = max(0, 1.0 - days_old / 30)  # Decay over 30 days
        factors.append(recency)
        
        return np.mean(factors)
    
    def _determine_evidence_quality(self, data: pd.Series) -> EvidenceQuality:
        """Determine quality of evidence based on data."""
        data_points = len(data)
        
        if data_points >= 30:
            return EvidenceQuality.STRONG
        elif data_points >= 14:
            return EvidenceQuality.MODERATE
        else:
            return EvidenceQuality.WEAK
    
    def _analyze_with_prophet(
        self, data: pd.Series, forecast_days: int
    ) -> Dict[str, Any]:
        """Prophet-based trend analysis with uncertainty quantification."""
        try:
            # Prepare data for Prophet
            df = pd.DataFrame({
                'ds': data.index,
                'y': data.values
            })
            
            # Configure Prophet with health data considerations
            model = Prophet(
                daily_seasonality=len(data) >= 30,
                weekly_seasonality=len(data) >= 14,
                yearly_seasonality=len(data) >= 365,
                uncertainty_samples=1000,
                changepoint_prior_scale=0.05,  # Conservative change points
                seasonality_mode='multiplicative' if data.min() > 0 else 'additive'
            )
            
            # Fit model
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(df)
            
            # Generate predictions
            future = model.make_future_dataframe(periods=forecast_days, freq='D')
            forecast = model.predict(future)
            
            # Extract components
            components = model.predict(df)
            
            return {
                'model': model,
                'forecast': forecast,
                'components': components,
                'trend': forecast['trend'].values,
                'changepoints': model.changepoints,
                'changepoint_scores': self._calculate_changepoint_scores(model, forecast)
            }
            
        except Exception as e:
            logger.warning(f"Prophet analysis failed: {e}")
            return None
    
    def _validate_trend_statistically(self, data: pd.Series) -> Dict[str, ValidationResult]:
        """Perform statistical validation of trends."""
        results = {}
        
        # Mann-Kendall test
        results['mann_kendall'] = self._mann_kendall_test(data.values)
        
        # Sen's slope
        results['sens_slope'] = self._sens_slope_estimator(data.values)
        
        # Linear regression
        results['linear_regression'] = self._linear_regression_test(data)
        
        # Augmented Dickey-Fuller test (stationarity)
        results['adf_test'] = self._adf_test(data.values)
        
        return results
    
    def _mann_kendall_test(self, values: np.ndarray) -> ValidationResult:
        """Perform Mann-Kendall trend test."""
        n = len(values)
        if n < 4:
            return ValidationResult(
                test_name="Mann-Kendall",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False
            )
        
        # Calculate S statistic
        s = 0
        for i in range(n-1):
            for j in range(i+1, n):
                s += np.sign(values[j] - values[i])
        
        # Calculate variance
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        # Calculate z-score
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0
            
        # Calculate p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        # Determine trend
        trend_detected = p_value < 0.05
        trend_direction = "increasing" if s > 0 else "decreasing" if s < 0 else "no_trend"
        
        return ValidationResult(
            test_name="Mann-Kendall",
            statistic=z,
            p_value=p_value,
            trend_detected=trend_detected,
            trend_direction=trend_direction,
            interpretation=f"{'Significant' if trend_detected else 'No significant'} {trend_direction} trend"
        )
    
    def _sens_slope_estimator(self, values: np.ndarray) -> ValidationResult:
        """Calculate Sen's slope estimator."""
        n = len(values)
        if n < 2:
            return ValidationResult(
                test_name="Sen's Slope",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False
            )
        
        # Calculate all slopes
        slopes = []
        for i in range(n-1):
            for j in range(i+1, n):
                if j - i > 0:
                    slope = (values[j] - values[i]) / (j - i)
                    slopes.append(slope)
        
        # Median slope
        sen_slope = np.median(slopes)
        
        # Confidence interval (95%)
        alpha = 0.05
        c_alpha = stats.norm.ppf(1 - alpha/2)
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        n_slopes = len(slopes)
        rank_lower = int((n_slopes - c_alpha * np.sqrt(var_s)) / 2)
        rank_upper = int((n_slopes + c_alpha * np.sqrt(var_s)) / 2)
        
        slopes_sorted = sorted(slopes)
        ci_lower = slopes_sorted[max(0, rank_lower)]
        ci_upper = slopes_sorted[min(n_slopes-1, rank_upper)]
        
        # Determine if trend is significant
        trend_detected = ci_lower > 0 or ci_upper < 0
        trend_direction = "increasing" if sen_slope > 0 else "decreasing" if sen_slope < 0 else "no_trend"
        
        return ValidationResult(
            test_name="Sen's Slope",
            statistic=sen_slope,
            p_value=0.0,  # Sen's slope doesn't provide p-value
            trend_detected=trend_detected,
            trend_direction=trend_direction,
            confidence_interval=(ci_lower, ci_upper),
            interpretation=f"Trend slope: {sen_slope:.4f} per time unit"
        )
    
    def _linear_regression_test(self, data: pd.Series) -> ValidationResult:
        """Perform linear regression trend test."""
        if len(data) < 2:
            return ValidationResult(
                test_name="Linear Regression",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False
            )
        
        # Create time variable
        x = np.arange(len(data))
        y = data.values
        
        # Perform regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Calculate confidence interval for slope
        t_val = stats.t.ppf(0.975, len(data) - 2)
        ci_lower = slope - t_val * std_err
        ci_upper = slope + t_val * std_err
        
        trend_detected = p_value < 0.05
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "no_trend"
        
        return ValidationResult(
            test_name="Linear Regression",
            statistic=slope,
            p_value=p_value,
            trend_detected=trend_detected,
            trend_direction=trend_direction,
            confidence_interval=(ci_lower, ci_upper),
            interpretation=f"R²={r_value**2:.3f}, slope={slope:.4f}"
        )
    
    def _adf_test(self, values: np.ndarray) -> ValidationResult:
        """Augmented Dickey-Fuller test for stationarity."""
        if len(values) < 4:
            return ValidationResult(
                test_name="ADF Test",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False
            )
        
        # Check if data is constant
        if np.std(values) == 0:
            return ValidationResult(
                test_name="ADF Test",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False,
                interpretation="Constant series (no variation)"
            )
        
        try:
            from statsmodels.tsa.stattools import adfuller
            result = adfuller(values)
            
            return ValidationResult(
                test_name="ADF Test",
                statistic=result[0],
                p_value=result[1],
                trend_detected=result[1] > 0.05,  # Non-stationary indicates trend
                interpretation=f"{'Non-stationary' if result[1] > 0.05 else 'Stationary'} series"
            )
        except ImportError:
            return ValidationResult(
                test_name="ADF Test",
                statistic=0.0,
                p_value=1.0,
                trend_detected=False,
                interpretation="ADF test not available"
            )
    
    def _decompose_time_series(self, data: pd.Series) -> Optional[TrendDecomposition]:
        """Decompose time series into trend, seasonal, and residual components."""
        if len(data) < 14:
            return None
            
        try:
            if STL_AVAILABLE and len(data) >= 14:
                # Use STL decomposition
                stl = STL(data, seasonal=13 if len(data) < 365 else 365)
                result = stl.fit()
                
                return TrendDecomposition(
                    observed=data.values.tolist(),
                    trend=result.trend.values.tolist(),
                    seasonal=result.seasonal.values.tolist(),
                    residual=result.resid.values.tolist(),
                    timestamps=data.index.tolist(),
                    method="STL"
                )
            else:
                # Fallback to simple moving average decomposition
                window = min(7, len(data) // 3)
                trend = data.rolling(window=window, center=True).mean()
                detrended = data - trend
                seasonal = detrended.groupby(data.index.dayofweek).transform('mean')
                residual = data - trend - seasonal
                
                return TrendDecomposition(
                    observed=data.values.tolist(),
                    trend=trend.bfill().ffill().values.tolist(),
                    seasonal=seasonal.fillna(0).values.tolist(),
                    residual=residual.fillna(0).values.tolist(),
                    timestamps=data.index.tolist(),
                    method="Simple"
                )
        except Exception as e:
            logger.warning(f"Decomposition failed: {e}")
            return None
    
    def _ensemble_analysis(
        self,
        data: pd.Series,
        prophet_result: Optional[Dict[str, Any]],
        statistical_result: Dict[str, ValidationResult],
        decomposition: Optional[TrendDecomposition]
    ) -> EnsembleResult:
        """Combine results from multiple analysis methods."""
        individual_results = {}
        
        # Prophet classification
        if prophet_result:
            prophet_trend = self._classify_prophet_trend(prophet_result)
            individual_results['prophet'] = prophet_trend
            
        # Statistical classification
        stat_trend = self._classify_statistical_trend(statistical_result)
        individual_results['statistical'] = stat_trend
        
        # Decomposition classification
        if decomposition:
            decomp_trend = self._classify_decomposition_trend(decomposition)
            individual_results['decomposition'] = decomp_trend
            
        # Simple trend classification
        simple_trend = self._classify_simple_trend(data)
        individual_results['simple'] = simple_trend
        
        # Weighted voting
        trend_votes = {}
        total_weight = 0
        
        for method, trend in individual_results.items():
            weight = self.ensemble_weights.get(method, 0.1)
            if trend != TrendClassification.INSUFFICIENT_DATA:
                if trend not in trend_votes:
                    trend_votes[trend] = 0
                trend_votes[trend] += weight
                total_weight += weight
        
        # Determine primary trend
        if total_weight > 0:
            primary_trend = max(trend_votes.items(), key=lambda x: x[1])[0]
            confidence = (trend_votes[primary_trend] / total_weight) * 100
        else:
            primary_trend = TrendClassification.INSUFFICIENT_DATA
            confidence = 0.0
            
        # Calculate agreement score
        if len(individual_results) > 1:
            trend_counts = {}
            for trend in individual_results.values():
                if trend != TrendClassification.INSUFFICIENT_DATA:
                    trend_counts[trend] = trend_counts.get(trend, 0) + 1
            
            max_agreement = max(trend_counts.values()) if trend_counts else 0
            agreement_score = max_agreement / len(individual_results)
        else:
            agreement_score = 1.0
            
        return EnsembleResult(
            primary_trend=primary_trend,
            confidence=confidence,
            individual_results=individual_results,
            weights=self.ensemble_weights,
            agreement_score=agreement_score
        )
    
    def _classify_prophet_trend(self, prophet_result: Dict[str, Any]) -> TrendClassification:
        """Classify trend from Prophet results."""
        trend = prophet_result['trend']
        if len(trend) < 2:
            return TrendClassification.INSUFFICIENT_DATA
            
        # Calculate trend slope
        daily_changes = np.diff(trend) / trend[:-1]
        avg_daily_change = np.mean(daily_changes)
        
        # Check volatility
        volatility = np.std(daily_changes)
        
        if volatility > 0.1:  # High volatility threshold
            return TrendClassification.VOLATILE
        elif avg_daily_change > self.trend_thresholds['strongly_increasing']:
            return TrendClassification.STRONGLY_INCREASING
        elif avg_daily_change > self.trend_thresholds['increasing']:
            return TrendClassification.INCREASING
        elif avg_daily_change < self.trend_thresholds['strongly_decreasing']:
            return TrendClassification.STRONGLY_DECREASING
        elif avg_daily_change < self.trend_thresholds['decreasing']:
            return TrendClassification.DECREASING
        else:
            return TrendClassification.STABLE
    
    def _classify_statistical_trend(
        self, statistical_result: Dict[str, ValidationResult]
    ) -> TrendClassification:
        """Classify trend from statistical tests."""
        mk_result = statistical_result['mann_kendall']
        lr_result = statistical_result['linear_regression']
        
        if not mk_result.trend_detected and abs(lr_result.statistic) < 0.001:
            return TrendClassification.STABLE
            
        # Use Sen's slope for magnitude
        sen_slope = statistical_result['sens_slope'].statistic
        
        # Normalize slope to daily change
        daily_change = sen_slope
        
        if mk_result.trend_direction == "increasing":
            if daily_change > self.trend_thresholds['strongly_increasing']:
                return TrendClassification.STRONGLY_INCREASING
            else:
                return TrendClassification.INCREASING
        elif mk_result.trend_direction == "decreasing":
            if daily_change < self.trend_thresholds['strongly_decreasing']:
                return TrendClassification.STRONGLY_DECREASING
            else:
                return TrendClassification.DECREASING
        else:
            return TrendClassification.STABLE
    
    def _classify_decomposition_trend(self, decomposition: TrendDecomposition) -> TrendClassification:
        """Classify trend from decomposition results."""
        trend = np.array(decomposition.trend)
        if len(trend) < 2:
            return TrendClassification.INSUFFICIENT_DATA
            
        # Remove NaN values
        trend_clean = trend[~np.isnan(trend)]
        if len(trend_clean) < 2:
            return TrendClassification.INSUFFICIENT_DATA
            
        # Calculate trend direction
        x = np.arange(len(trend_clean))
        slope, _, r_value, _, _ = stats.linregress(x, trend_clean)
        
        # Normalize to daily change
        daily_change = slope / np.mean(trend_clean) if np.mean(trend_clean) != 0 else 0
        
        if abs(r_value) < 0.3:  # Low correlation
            return TrendClassification.VOLATILE
        elif daily_change > self.trend_thresholds['strongly_increasing']:
            return TrendClassification.STRONGLY_INCREASING
        elif daily_change > self.trend_thresholds['increasing']:
            return TrendClassification.INCREASING
        elif daily_change < self.trend_thresholds['strongly_decreasing']:
            return TrendClassification.STRONGLY_DECREASING
        elif daily_change < self.trend_thresholds['decreasing']:
            return TrendClassification.DECREASING
        else:
            return TrendClassification.STABLE
    
    def _classify_simple_trend(self, data: pd.Series) -> TrendClassification:
        """Simple trend classification as fallback."""
        if len(data) < 2:
            return TrendClassification.INSUFFICIENT_DATA
            
        # Compare first and last quartiles
        q1_data = data.iloc[:len(data)//4]
        q4_data = data.iloc[-len(data)//4:]
        
        q1_mean = q1_data.mean()
        q4_mean = q4_data.mean()
        
        if q1_mean == 0:
            return TrendClassification.STABLE
            
        change_ratio = (q4_mean - q1_mean) / q1_mean
        days = (data.index[-1] - data.index[0]).days
        daily_change = change_ratio / days if days > 0 else 0
        
        # Check volatility
        cv = data.std() / data.mean() if data.mean() != 0 else 0
        if cv > 0.5:  # High coefficient of variation
            return TrendClassification.VOLATILE
        elif daily_change > self.trend_thresholds['strongly_increasing']:
            return TrendClassification.STRONGLY_INCREASING
        elif daily_change > self.trend_thresholds['increasing']:
            return TrendClassification.INCREASING
        elif daily_change < self.trend_thresholds['strongly_decreasing']:
            return TrendClassification.STRONGLY_DECREASING
        elif daily_change < self.trend_thresholds['decreasing']:
            return TrendClassification.DECREASING
        else:
            return TrendClassification.STABLE
    
    def _detect_change_points(self, data: pd.Series) -> List[ChangePoint]:
        """Detect change points using multiple methods."""
        change_points = []
        
        # CUSUM detection
        cusum_changes = self._cusum_change_detection(data)
        change_points.extend(cusum_changes)
        
        # Statistical change detection
        stat_changes = self._statistical_change_detection(data)
        change_points.extend(stat_changes)
        
        # Merge nearby change points
        change_points = self._merge_nearby_changepoints(change_points)
        
        return sorted(change_points, key=lambda x: x.timestamp)
    
    def _cusum_change_detection(self, data: pd.Series) -> List[ChangePoint]:
        """CUSUM (Cumulative Sum) change point detection."""
        if len(data) < 10:
            return []
            
        changes = []
        values = data.values
        
        # Calculate CUSUM
        mean = np.mean(values)
        cusum = np.cumsum(values - mean)
        
        # Find peaks in CUSUM
        peaks, properties = find_peaks(np.abs(cusum), height=np.std(values)*2)
        
        for peak_idx in peaks:
            if peak_idx > 0 and peak_idx < len(data) - 1:
                # Calculate magnitude of change
                before_mean = np.mean(values[max(0, peak_idx-5):peak_idx])
                after_mean = np.mean(values[peak_idx:min(len(values), peak_idx+5)])
                magnitude = after_mean - before_mean
                
                # Determine direction
                direction = "increase" if magnitude > 0 else "decrease"
                
                # Calculate confidence based on consistency
                before_std = np.std(values[max(0, peak_idx-5):peak_idx])
                after_std = np.std(values[peak_idx:min(len(values), peak_idx+5)])
                confidence = min(100, 100 * abs(magnitude) / (before_std + after_std + 1))
                
                changes.append(ChangePoint(
                    timestamp=data.index[peak_idx],
                    confidence=confidence,
                    magnitude=magnitude,
                    direction=direction,
                    method="CUSUM"
                ))
                
        return changes
    
    def _statistical_change_detection(self, data: pd.Series) -> List[ChangePoint]:
        """Statistical change point detection using t-tests."""
        if len(data) < 20:
            return []
            
        changes = []
        window_size = max(5, len(data) // 10)
        
        for i in range(window_size, len(data) - window_size):
            before = data.iloc[i-window_size:i].values
            after = data.iloc[i:i+window_size].values
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(before, after)
            
            if p_value < 0.01:  # Significant change
                magnitude = np.mean(after) - np.mean(before)
                direction = "increase" if magnitude > 0 else "decrease"
                confidence = (1 - p_value) * 100
                
                changes.append(ChangePoint(
                    timestamp=data.index[i],
                    confidence=confidence,
                    magnitude=magnitude,
                    direction=direction,
                    method="T-test"
                ))
                
        return changes
    
    def _merge_nearby_changepoints(
        self, change_points: List[ChangePoint], threshold_days: int = 7
    ) -> List[ChangePoint]:
        """Merge change points that are close in time."""
        if not change_points:
            return []
            
        merged = []
        current_group = [change_points[0]]
        
        for cp in change_points[1:]:
            days_diff = (cp.timestamp - current_group[-1].timestamp).days
            
            if days_diff <= threshold_days:
                current_group.append(cp)
            else:
                # Merge current group
                merged.append(self._merge_changepoint_group(current_group))
                current_group = [cp]
                
        # Don't forget last group
        if current_group:
            merged.append(self._merge_changepoint_group(current_group))
            
        return merged
    
    def _merge_changepoint_group(self, group: List[ChangePoint]) -> ChangePoint:
        """Merge a group of change points into one."""
        if len(group) == 1:
            return group[0]
            
        # Use weighted average based on confidence
        total_confidence = sum(cp.confidence for cp in group)
        
        if total_confidence == 0:
            # Simple average if no confidence
            avg_timestamp = group[len(group)//2].timestamp
            avg_magnitude = np.mean([cp.magnitude for cp in group])
            avg_confidence = np.mean([cp.confidence for cp in group])
        else:
            # Weighted average
            weights = [cp.confidence / total_confidence for cp in group]
            
            # For timestamp, use the one with highest confidence
            max_conf_idx = np.argmax([cp.confidence for cp in group])
            avg_timestamp = group[max_conf_idx].timestamp
            
            avg_magnitude = sum(cp.magnitude * w for cp, w in zip(group, weights))
            avg_confidence = np.mean([cp.confidence for cp in group])
        
        # Most common direction
        directions = [cp.direction for cp in group]
        direction = max(set(directions), key=directions.count)
        
        # Combined methods
        methods = list(set(cp.method for cp in group))
        method = " + ".join(methods)
        
        return ChangePoint(
            timestamp=avg_timestamp,
            confidence=avg_confidence,
            magnitude=avg_magnitude,
            direction=direction,
            method=method
        )
    
    def _analyze_volatility(self, data: pd.Series) -> Dict[str, Any]:
        """Analyze volatility patterns."""
        if len(data) < 7:
            return {
                'level': 'unknown',
                'score': 0.0,
                'trend': 'stable'
            }
        
        # Calculate coefficient of variation
        cv = data.std() / data.mean() if data.mean() != 0 else 0
        
        # Determine volatility level
        if cv < 0.1:
            level = "low"
        elif cv < 0.3:
            level = "medium"
        else:
            level = "high"
            
        # Analyze volatility trend
        window = min(7, len(data) // 4)
        rolling_std = data.rolling(window=window).std()
        
        if len(rolling_std.dropna()) >= 2:
            # Check if volatility is changing
            vol_slope, _, _, vol_p_value, _ = stats.linregress(
                np.arange(len(rolling_std.dropna())),
                rolling_std.dropna().values
            )
            
            if vol_p_value < 0.05:
                vol_trend = "increasing" if vol_slope > 0 else "decreasing"
            else:
                vol_trend = "stable"
        else:
            vol_trend = "stable"
            
        return {
            'level': level,
            'score': cv,
            'trend': vol_trend,
            'rolling_volatility': rolling_std
        }
    
    def _generate_predictions(
        self,
        data: pd.Series,
        prophet_result: Optional[Dict[str, Any]],
        ensemble_result: EnsembleResult,
        forecast_days: int
    ) -> List[PredictionPoint]:
        """Generate predictions with uncertainty bounds."""
        predictions = []
        
        if prophet_result and 'forecast' in prophet_result:
            # Use Prophet predictions
            forecast = prophet_result['forecast']
            future_forecast = forecast[forecast['ds'] > data.index.max()][:forecast_days]
            
            for _, row in future_forecast.iterrows():
                # Calculate prediction quality based on uncertainty
                uncertainty = (row['yhat_upper'] - row['yhat_lower']) / (2 * row['yhat'])
                
                if uncertainty < 0.1:
                    quality = PredictionQuality.HIGH
                elif uncertainty < 0.3:
                    quality = PredictionQuality.MEDIUM
                else:
                    quality = PredictionQuality.LOW
                    
                predictions.append(PredictionPoint(
                    timestamp=row['ds'],
                    predicted_value=row['yhat'],
                    lower_bound=row['yhat_lower'],
                    upper_bound=row['yhat_upper'],
                    prediction_quality=quality,
                    uncertainty_score=uncertainty
                ))
        else:
            # Fallback to simple linear extrapolation
            if len(data) >= 2:
                # Fit linear trend to recent data
                recent_data = data.tail(min(14, len(data)))
                x = np.arange(len(recent_data))
                slope, intercept, _, _, std_err = stats.linregress(x, recent_data.values)
                
                for i in range(1, forecast_days + 1):
                    future_date = data.index[-1] + timedelta(days=i)
                    predicted = intercept + slope * (len(recent_data) + i - 1)
                    
                    # Simple uncertainty bounds
                    uncertainty = std_err * i * 1.96
                    lower = predicted - uncertainty
                    upper = predicted + uncertainty
                    
                    # Quality degrades with distance
                    quality = PredictionQuality.HIGH if i <= 3 else \
                             PredictionQuality.MEDIUM if i <= 7 else \
                             PredictionQuality.LOW
                    
                    predictions.append(PredictionPoint(
                        timestamp=future_date,
                        predicted_value=predicted,
                        lower_bound=lower,
                        upper_bound=upper,
                        prediction_quality=quality,
                        uncertainty_score=uncertainty / predicted if predicted != 0 else 1.0
                    ))
                    
        return predictions
    
    def _calculate_trend_strength(self, statistical_result: Dict[str, ValidationResult]) -> float:
        """Calculate overall trend strength (0-1)."""
        strengths = []
        
        # R-squared from linear regression
        lr_result = statistical_result['linear_regression']
        if lr_result.statistic != 0:
            # Convert slope to R-squared equivalent
            strengths.append(min(abs(lr_result.statistic) / 0.1, 1.0))
            
        # Sen's slope magnitude
        sen_result = statistical_result['sens_slope']
        if sen_result.statistic != 0:
            strengths.append(min(abs(sen_result.statistic) / 0.1, 1.0))
            
        # Mann-Kendall z-score
        mk_result = statistical_result['mann_kendall']
        if mk_result.statistic != 0:
            strengths.append(min(abs(mk_result.statistic) / 3.0, 1.0))
            
        return np.mean(strengths) if strengths else 0.0
    
    def _has_significant_seasonality(self, decomposition: Optional[TrendDecomposition]) -> bool:
        """Check if data has significant seasonal patterns."""
        if not decomposition:
            return False
            
        seasonal = np.array(decomposition.seasonal)
        observed = np.array(decomposition.observed)
        
        # Calculate seasonal strength
        seasonal_var = np.var(seasonal)
        total_var = np.var(observed)
        
        if total_var == 0:
            return False
            
        seasonal_ratio = seasonal_var / total_var
        
        return seasonal_ratio > 0.1  # 10% of variance explained by seasonality
    
    def _extract_seasonal_components(
        self, decomposition: Optional[TrendDecomposition], data: pd.Series
    ) -> List[SeasonalComponent]:
        """Extract seasonal patterns from decomposition."""
        if not decomposition or not self._has_significant_seasonality(decomposition):
            return []
            
        components = []
        seasonal = pd.Series(decomposition.seasonal, index=data.index)
        
        # Weekly pattern
        if len(data) >= 14:
            weekly_pattern = {}
            for dow in range(7):
                dow_data = seasonal[seasonal.index.dayofweek == dow]
                if len(dow_data) > 0:
                    weekly_pattern[str(dow)] = dow_data.mean()
                    
            if len(weekly_pattern) == 7:
                # Test significance with ANOVA
                dow_groups = [seasonal[seasonal.index.dayofweek == dow].values 
                             for dow in range(7)]
                dow_groups = [g for g in dow_groups if len(g) > 0]
                
                if len(dow_groups) >= 2:
                    f_stat, p_value = stats.f_oneway(*dow_groups)
                    
                    components.append(SeasonalComponent(
                        period="weekly",
                        strength=np.std(list(weekly_pattern.values())) / (np.mean(data) + 1e-10),
                        pattern=weekly_pattern,
                        significance=p_value
                    ))
                    
        # Monthly pattern (if enough data)
        if len(data) >= 60:
            monthly_pattern = {}
            for day in range(1, 32):
                day_data = seasonal[seasonal.index.day == day]
                if len(day_data) > 0:
                    monthly_pattern[str(day)] = day_data.mean()
                    
            if len(monthly_pattern) >= 20:
                components.append(SeasonalComponent(
                    period="monthly",
                    strength=np.std(list(monthly_pattern.values())) / (np.mean(data) + 1e-10),
                    pattern=monthly_pattern,
                    significance=0.05  # Placeholder
                ))
                
        return components
    
    def _calculate_seasonal_strength(self, decomposition: Optional[TrendDecomposition]) -> float:
        """Calculate overall seasonal strength (0-1)."""
        if not decomposition:
            return 0.0
            
        seasonal = np.array(decomposition.seasonal)
        observed = np.array(decomposition.observed)
        
        # Remove NaN values
        mask = ~(np.isnan(seasonal) | np.isnan(observed))
        seasonal = seasonal[mask]
        observed = observed[mask]
        
        if len(seasonal) == 0 or np.var(observed) == 0:
            return 0.0
            
        # Seasonal strength as ratio of variances
        strength = np.var(seasonal) / np.var(observed)
        
        return min(strength, 1.0)
    
    def _find_structural_breaks(self, change_points: List[ChangePoint]) -> List[datetime]:
        """Identify major structural breaks from change points."""
        if not change_points:
            return []
            
        # Structural breaks are high-confidence, large magnitude changes
        structural_breaks = []
        
        for cp in change_points:
            if cp.confidence > 80 and abs(cp.magnitude) > 0.2:
                structural_breaks.append(cp.timestamp)
                
        return structural_breaks
    
    def _interpret_health_context(
        self,
        ensemble_result: EnsembleResult,
        metric_name: str,
        health_context: Dict[str, Any]
    ) -> str:
        """Generate health-specific interpretation of trends."""
        trend = ensemble_result.primary_trend
        
        # Metric-specific interpretations
        interpretations = {
            'steps': {
                TrendClassification.STRONGLY_INCREASING: "Excellent progress in daily activity! Your step count is improving significantly.",
                TrendClassification.INCREASING: "Good progress - your daily steps are trending upward.",
                TrendClassification.STABLE: "Your step count is consistent. Consider setting a higher daily goal.",
                TrendClassification.DECREASING: "Your activity level is declining. Try to incorporate more walking into your routine.",
                TrendClassification.STRONGLY_DECREASING: "Significant decline in activity detected. This may impact your overall health.",
                TrendClassification.VOLATILE: "Your step count varies significantly. Try to establish a more consistent routine."
            },
            'heart_rate_resting': {
                TrendClassification.STRONGLY_INCREASING: "Your resting heart rate is increasing significantly, which may indicate stress or declining fitness.",
                TrendClassification.INCREASING: "Slight increase in resting heart rate. Monitor for continued changes.",
                TrendClassification.STABLE: "Your resting heart rate is stable, indicating consistent cardiovascular health.",
                TrendClassification.DECREASING: "Good news - your resting heart rate is decreasing, suggesting improved fitness.",
                TrendClassification.STRONGLY_DECREASING: "Excellent improvement in resting heart rate, indicating better cardiovascular fitness.",
                TrendClassification.VOLATILE: "Your resting heart rate fluctuates significantly. Consider factors like stress and sleep quality."
            },
            'sleep_hours': {
                TrendClassification.STRONGLY_INCREASING: "You're getting much more sleep recently.",
                TrendClassification.INCREASING: "Your sleep duration is improving.",
                TrendClassification.STABLE: "Your sleep pattern is consistent.",
                TrendClassification.DECREASING: "You're getting less sleep lately. Aim for 7-9 hours nightly.",
                TrendClassification.STRONGLY_DECREASING: "Significant sleep reduction detected. This can impact your health and wellbeing.",
                TrendClassification.VOLATILE: "Your sleep schedule is irregular. Try to maintain consistent bed and wake times."
            }
        }
        
        # Get metric-specific interpretation or use generic
        metric_interp = interpretations.get(metric_name, {})
        
        if trend in metric_interp:
            base_interpretation = metric_interp[trend]
        else:
            # Generic interpretation
            if trend == TrendClassification.STRONGLY_INCREASING:
                base_interpretation = f"Your {metric_name} is increasing significantly."
            elif trend == TrendClassification.INCREASING:
                base_interpretation = f"Your {metric_name} is trending upward."
            elif trend == TrendClassification.STABLE:
                base_interpretation = f"Your {metric_name} remains stable."
            elif trend == TrendClassification.DECREASING:
                base_interpretation = f"Your {metric_name} is trending downward."
            elif trend == TrendClassification.STRONGLY_DECREASING:
                base_interpretation = f"Your {metric_name} is decreasing significantly."
            elif trend == TrendClassification.VOLATILE:
                base_interpretation = f"Your {metric_name} shows high variability."
            else:
                base_interpretation = f"Insufficient data to determine {metric_name} trend."
                
        # Add context if available
        if health_context.get('user_goals'):
            goals = health_context['user_goals']
            if metric_name in goals:
                goal_value = goals[metric_name]
                base_interpretation += f" Your goal is {goal_value}."
                
        return base_interpretation
    
    def _generate_wsj_summary(
        self,
        ensemble_result: EnsembleResult,
        interpretation: str,
        metric_name: str
    ) -> str:
        """Generate WSJ-style trend summary: clear, concise, actionable."""
        trend = ensemble_result.primary_trend
        confidence = ensemble_result.confidence
        
        # WSJ-style: Lead with the key finding
        if confidence > 80:
            certainty = "clearly"
        elif confidence > 60:
            certainty = "generally"
        else:
            certainty = "appears to be"
            
        # Format metric name for display
        display_name = metric_name.replace('_', ' ').title()
        
        # Build summary
        if trend == TrendClassification.STRONGLY_INCREASING:
            summary = f"{display_name} is {certainty} rising sharply"
        elif trend == TrendClassification.INCREASING:
            summary = f"{display_name} is {certainty} trending up"
        elif trend == TrendClassification.STABLE:
            summary = f"{display_name} remains stable"
        elif trend == TrendClassification.DECREASING:
            summary = f"{display_name} is {certainty} trending down"
        elif trend == TrendClassification.STRONGLY_DECREASING:
            summary = f"{display_name} is {certainty} falling sharply"
        elif trend == TrendClassification.VOLATILE:
            summary = f"{display_name} shows high volatility"
        else:
            summary = f"Insufficient {display_name} data for trend analysis"
            
        # Add confidence qualifier if moderate
        if 40 < confidence <= 60:
            summary += " (moderate confidence)"
        elif confidence <= 40:
            summary += " (low confidence)"
            
        return summary
    
    def _generate_recommendations(
        self,
        ensemble_result: EnsembleResult,
        metric_name: str,
        health_context: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on trends."""
        recommendations = []
        trend = ensemble_result.primary_trend
        
        # Metric-specific recommendations
        if metric_name == 'steps':
            if trend in [TrendClassification.DECREASING, TrendClassification.STRONGLY_DECREASING]:
                recommendations.extend([
                    "Schedule regular walking breaks throughout your day",
                    "Consider using a step reminder on your phone",
                    "Try parking farther away or taking stairs when possible"
                ])
            elif trend == TrendClassification.VOLATILE:
                recommendations.extend([
                    "Establish a consistent daily walking routine",
                    "Set a minimum daily step goal to maintain on all days"
                ])
            elif trend in [TrendClassification.STABLE]:
                recommendations.extend([
                    "Challenge yourself with a higher daily step goal",
                    "Add variety with different walking routes or hiking"
                ])
                
        elif metric_name == 'heart_rate_resting':
            if trend in [TrendClassification.INCREASING, TrendClassification.STRONGLY_INCREASING]:
                recommendations.extend([
                    "Consider adding cardiovascular exercise to your routine",
                    "Practice stress management techniques like meditation",
                    "Ensure you're getting adequate sleep"
                ])
            elif trend == TrendClassification.VOLATILE:
                recommendations.extend([
                    "Monitor factors that may affect heart rate (caffeine, stress, sleep)",
                    "Try to maintain consistent sleep and exercise schedules"
                ])
                
        elif metric_name == 'sleep_hours':
            if trend in [TrendClassification.DECREASING, TrendClassification.STRONGLY_DECREASING]:
                recommendations.extend([
                    "Set a consistent bedtime and stick to it",
                    "Create a relaxing bedtime routine",
                    "Limit screen time before bed"
                ])
            elif trend == TrendClassification.VOLATILE:
                recommendations.extend([
                    "Maintain consistent sleep and wake times, even on weekends",
                    "Track factors that may affect your sleep quality"
                ])
                
        # Add goal-based recommendations if available
        if health_context.get('user_goals') and metric_name in health_context['user_goals']:
            goal = health_context['user_goals'][metric_name]
            if trend in [TrendClassification.DECREASING, TrendClassification.STRONGLY_DECREASING]:
                recommendations.append(f"Focus on reaching your {metric_name} goal of {goal}")
                
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _calculate_changepoint_scores(
        self, model: Any, forecast: pd.DataFrame
    ) -> Dict[datetime, float]:
        """Calculate change point scores from Prophet model."""
        scores = {}
        
        if hasattr(model, 'changepoints') and model.changepoints is not None:
            for cp in model.changepoints:
                # Find the magnitude of change around this point
                idx = forecast[forecast['ds'] == cp].index
                if len(idx) > 0:
                    idx = idx[0]
                    if idx > 0 and idx < len(forecast) - 1:
                        before = forecast.iloc[idx-1]['trend']
                        after = forecast.iloc[idx+1]['trend']
                        magnitude = abs(after - before)
                        scores[cp] = magnitude
                        
        return scores
    
    def _get_methods_used(self) -> List[str]:
        """Get list of analysis methods used."""
        methods = []
        
        if PROPHET_AVAILABLE:
            methods.append("Prophet")
        if STL_AVAILABLE:
            methods.append("STL Decomposition")
            
        methods.extend([
            "Mann-Kendall Test",
            "Sen's Slope",
            "Linear Regression",
            "CUSUM Change Detection"
        ])
        
        return methods
    
    def _trend_classification_to_string(self, classification: TrendClassification) -> str:
        """Convert TrendClassification enum to string for spec compliance."""
        mapping = {
            TrendClassification.STRONGLY_INCREASING: "increasing",
            TrendClassification.INCREASING: "increasing",
            TrendClassification.STABLE: "stable",
            TrendClassification.DECREASING: "decreasing",
            TrendClassification.STRONGLY_DECREASING: "decreasing",
            TrendClassification.VOLATILE: "volatile",
            TrendClassification.INSUFFICIENT_DATA: "stable"
        }
        return mapping.get(classification, "stable")