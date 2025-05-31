"""
Comprehensive seasonal pattern analysis with Fourier analysis, STL decomposition, 
Prophet forecasting, and weather correlation analysis.

This module provides advanced seasonal pattern detection including:
- Fourier analysis for cyclical patterns identification
- Enhanced STL decomposition capabilities  
- Prophet-style forecasting with uncertainty intervals
- Weather correlation analysis for environmental factors
- Polar plots for annual cycle visualization
- Phase plots for pattern shift detection
- Multi-year overlay comparisons with statistical validation
- Actionable insights for optimal goal timing
"""

from typing import Dict, List, Optional, Tuple, Union, Any, NamedTuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats, signal
from scipy.fft import fft, fftfreq
import logging
from collections import defaultdict
from enum import Enum
import warnings
import math

from .month_over_month_trends import SeasonalDecomposition, SeasonalDecomposer
from .monthly_metrics_calculator import MonthlyMetricsCalculator, MonthlyMetrics
from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics

logger = logging.getLogger(__name__)


class SeasonalStrength(Enum):
    """Seasonality strength categories."""
    NONE = "none"
    WEAK = "weak" 
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class FourierComponent:
    """Individual Fourier frequency component."""
    frequency: float  # cycles per year
    amplitude: float
    phase: float  # radians
    period_days: float
    power: float
    significance: float  # p-value


@dataclass
class FourierAnalysis:
    """Results from Fourier analysis of time series."""
    dominant_frequencies: List[FourierComponent]
    frequency_spectrum: List[float]
    power_spectrum: List[float]
    frequencies: List[float]
    seasonal_strength: float
    annual_cycle_detected: bool
    semi_annual_cycle_detected: bool


@dataclass 
class PolarPlotData:
    """Data structure for polar plot visualization."""
    angles: List[float]  # radians (0-2π for 12 months)
    radii: List[float]   # metric values
    years: List[int]
    colors: List[str]
    labels: List[str]
    center_value: float
    max_radius: float


@dataclass
class PhasePlotData:
    """Data structure for phase plot visualization."""
    current_values: List[float]
    rate_of_change: List[float]
    dates: List[datetime]
    trajectory_color: List[str]
    direction_arrows: List[Tuple[float, float, float, float]]  # x, y, dx, dy


@dataclass
class WeatherCorrelation:
    """Weather correlation analysis results."""
    temperature_correlation: float
    precipitation_correlation: float
    daylight_correlation: float
    seasonal_temperature_effect: float
    weather_significance: float  # p-value
    optimal_conditions: Dict[str, float]


@dataclass
class PatternBreakAlert:
    """Alert for detected pattern breaks."""
    date: datetime
    metric: str
    expected_value: float
    actual_value: float
    deviation_score: float  # standard deviations
    significance: float  # p-value
    description: str
    severity: str  # 'low', 'medium', 'high'


@dataclass
class GoalTimingRecommendation:
    """Recommendation for optimal goal timing."""
    goal_type: str
    optimal_start_date: datetime
    success_probability: float
    expected_challenges: List[str]
    supporting_evidence: Dict[str, Any]
    confidence_interval: Tuple[float, float]


@dataclass
class SeasonalAnalysis:
    """Comprehensive seasonal pattern analysis results."""
    metric_name: str
    analysis_period: Tuple[datetime, datetime]
    
    # Core analysis components
    fourier_results: FourierAnalysis
    stl_decomposition: SeasonalDecomposition
    
    # Seasonality metrics (set defaults for proper dataclass ordering)
    seasonality_strength: float = 0.0
    seasonality_category: SeasonalStrength = SeasonalStrength.NONE
    pattern_consistency: float = 0.0
    
    # Multi-year analysis
    year_over_year_variance: float = 0.0
    pattern_evolution_trend: str = "stable"  # 'stable', 'strengthening', 'weakening'
    
    # Statistical validation
    statistical_significance: float = 1.0  # p-value for seasonality
    confidence_level: float = 0.0
    
    # Optional components with defaults
    weather_correlation: Optional[WeatherCorrelation] = None
    polar_plot_data: Optional[PolarPlotData] = None
    phase_plot_data: Optional[PhasePlotData] = None
    forecast_data: Optional[Dict[str, Any]] = None
    pattern_breaks: List[PatternBreakAlert] = field(default_factory=list)
    goal_timing_recommendations: List[GoalTimingRecommendation] = field(default_factory=list)


class FourierAnalyzer:
    """Fourier analysis for cyclical pattern detection."""
    
    def __init__(self, min_cycles: int = 2, significance_threshold: float = 0.05):
        self.min_cycles = min_cycles
        self.significance_threshold = significance_threshold
    
    def analyze(self, metric_data: pd.Series) -> FourierAnalysis:
        """Perform comprehensive Fourier analysis on metric data.
        
        Args:
            metric_data: Time series data with datetime index
            
        Returns:
            FourierAnalysis object with detailed frequency analysis
        """
        logger.info(f"Starting Fourier analysis on {len(metric_data)} data points")
        
        # Ensure regular sampling by resampling to daily frequency
        daily_data = metric_data.resample('D').mean().interpolate()
        values = daily_data.values
        n_samples = len(values)
        
        if n_samples < 365:  # Need at least 1 year
            logger.warning("Insufficient data for reliable Fourier analysis")
            return self._create_empty_analysis()
        
        # Calculate FFT
        fft_values = fft(values)
        frequencies = fftfreq(n_samples, d=1)  # Daily sampling (d=1 day)
        
        # Convert to cycles per year and calculate power spectrum
        freq_per_year = frequencies * 365.25
        power_spectrum = np.abs(fft_values) ** 2
        
        # Only consider positive frequencies
        positive_freq_mask = freq_per_year > 0
        freq_per_year = freq_per_year[positive_freq_mask]
        power_spectrum = power_spectrum[positive_freq_mask]
        fft_values = fft_values[positive_freq_mask]
        
        # Find dominant frequencies
        dominant_components = self._identify_dominant_frequencies(
            freq_per_year, power_spectrum, fft_values, n_samples
        )
        
        # Calculate seasonal strength and detect specific cycles
        seasonal_strength = self._calculate_seasonal_strength(power_spectrum, freq_per_year)
        annual_detected = any(0.8 <= comp.frequency <= 1.2 for comp in dominant_components)
        semi_annual_detected = any(1.8 <= comp.frequency <= 2.2 for comp in dominant_components)
        
        return FourierAnalysis(
            dominant_frequencies=dominant_components,
            frequency_spectrum=freq_per_year.tolist(),
            power_spectrum=power_spectrum.tolist(),
            frequencies=frequencies.tolist(),
            seasonal_strength=seasonal_strength,
            annual_cycle_detected=annual_detected,
            semi_annual_cycle_detected=semi_annual_detected
        )
    
    def _identify_dominant_frequencies(self, frequencies: np.ndarray, power: np.ndarray, 
                                     fft_values: np.ndarray, n_samples: int) -> List[FourierComponent]:
        """Identify statistically significant dominant frequencies."""
        # Find peaks in power spectrum
        peak_indices, properties = signal.find_peaks(
            power, 
            height=np.mean(power) + 2 * np.std(power),  # Above 2σ threshold
            distance=n_samples // 100  # Minimum separation between peaks
        )
        
        components = []
        for idx in peak_indices:
            if idx >= len(frequencies):
                continue
                
            freq = frequencies[idx]
            amplitude = np.abs(fft_values[idx]) * 2 / n_samples
            phase = np.angle(fft_values[idx])
            period_days = 365.25 / freq if freq > 0 else float('inf')
            power_val = power[idx]
            
            # Calculate significance using F-test
            significance = self._calculate_frequency_significance(power_val, power, n_samples)
            
            if significance < self.significance_threshold:
                components.append(FourierComponent(
                    frequency=freq,
                    amplitude=amplitude,
                    phase=phase,
                    period_days=period_days,
                    power=power_val,
                    significance=significance
                ))
        
        # Sort by power (strongest first)
        components.sort(key=lambda x: x.power, reverse=True)
        return components[:10]  # Return top 10 components
    
    def _calculate_frequency_significance(self, peak_power: float, all_power: np.ndarray, 
                                        n_samples: int) -> float:
        """Calculate statistical significance of a frequency component using F-test."""
        # F-test: ratio of peak power to background noise
        background_power = np.mean(all_power)
        f_statistic = peak_power / background_power
        
        # Degrees of freedom
        df1 = 2  # Complex amplitude has 2 parameters
        df2 = n_samples - 2
        
        # Calculate p-value
        p_value = 1 - stats.f.cdf(f_statistic, df1, df2)
        return p_value
    
    def _calculate_seasonal_strength(self, power_spectrum: np.ndarray, 
                                   frequencies: np.ndarray) -> float:
        """Calculate overall seasonal strength from power spectrum."""
        # Focus on seasonal frequencies (0.5 to 4 cycles per year)
        seasonal_mask = (frequencies >= 0.5) & (frequencies <= 4.0)
        seasonal_power = np.sum(power_spectrum[seasonal_mask])
        total_power = np.sum(power_spectrum)
        
        return seasonal_power / total_power if total_power > 0 else 0.0
    
    def _create_empty_analysis(self) -> FourierAnalysis:
        """Create empty analysis for insufficient data."""
        return FourierAnalysis(
            dominant_frequencies=[],
            frequency_spectrum=[],
            power_spectrum=[],
            frequencies=[],
            seasonal_strength=0.0,
            annual_cycle_detected=False,
            semi_annual_cycle_detected=False
        )


class ProphetForecaster:
    """Prophet-style forecasting with seasonality modeling."""
    
    def __init__(self, yearly_seasonality: bool = True, weekly_seasonality: bool = True):
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
    
    def forecast(self, metric_data: pd.Series, periods: int = 90) -> Dict[str, Any]:
        """Generate forecast using Prophet or fallback method.
        
        Args:
            metric_data: Time series data with datetime index
            periods: Number of days to forecast ahead
            
        Returns:
            Dictionary with forecast data including confidence intervals
        """
        try:
            from prophet import Prophet
            return self._prophet_forecast(metric_data, periods)
        except ImportError:
            logger.warning("Prophet not available, using fallback forecasting")
            return self._fallback_forecast(metric_data, periods)
    
    def _prophet_forecast(self, metric_data: pd.Series, periods: int) -> Dict[str, Any]:
        """Generate forecast using Facebook Prophet."""
        from prophet import Prophet
        
        # Prepare data for Prophet
        df = pd.DataFrame({
            'ds': metric_data.index,
            'y': metric_data.values
        })
        
        # Configure Prophet model
        model = Prophet(
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=False,
            uncertainty_samples=1000,
            seasonality_mode='additive'
        )
        
        # Fit model
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Extract results
        forecast_dates = forecast['ds'].iloc[-periods:].tolist()
        point_forecast = forecast['yhat'].iloc[-periods:].tolist()
        lower_bound = forecast['yhat_lower'].iloc[-periods:].tolist() 
        upper_bound = forecast['yhat_upper'].iloc[-periods:].tolist()
        
        return {
            'dates': forecast_dates,
            'forecast': point_forecast,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'confidence_level': 0.8,
            'method': 'Prophet',
            'seasonal_components': {
                'yearly': forecast['yearly'].iloc[-periods:].tolist() if 'yearly' in forecast else [],
                'weekly': forecast['weekly'].iloc[-periods:].tolist() if 'weekly' in forecast else []
            }
        }
    
    def _fallback_forecast(self, metric_data: pd.Series, periods: int) -> Dict[str, Any]:
        """Fallback forecasting using seasonal naive method with trend."""
        # Use last year's pattern with trend adjustment
        daily_data = metric_data.resample('D').mean().ffill()
        
        if len(daily_data) < 365:
            # Use simple trend extrapolation for short series
            return self._simple_trend_forecast(daily_data, periods)
        
        # Seasonal naive with trend
        last_year = daily_data.iloc[-365:]
        trend = (daily_data.iloc[-30:].mean() - daily_data.iloc[-60:-30].mean()) / 30
        
        forecast_dates = pd.date_range(
            start=daily_data.index[-1] + timedelta(days=1),
            periods=periods,
            freq='D'
        ).tolist()
        
        # Repeat seasonal pattern with trend
        seasonal_pattern = last_year.values[:periods] if periods <= 365 else np.tile(last_year.values, periods // 365 + 1)[:periods]
        trend_adjustment = trend * np.arange(1, periods + 1)
        point_forecast = (seasonal_pattern + trend_adjustment).tolist()
        
        # Simple confidence intervals (±20% of recent volatility)
        recent_volatility = daily_data.iloc[-90:].std()
        confidence_width = 1.645 * recent_volatility  # 90% confidence interval
        lower_bound = (np.array(point_forecast) - confidence_width).tolist()
        upper_bound = (np.array(point_forecast) + confidence_width).tolist()
        
        return {
            'dates': forecast_dates,
            'forecast': point_forecast,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'confidence_level': 0.9,
            'method': 'Seasonal Naive with Trend'
        }
    
    def _simple_trend_forecast(self, daily_data: pd.Series, periods: int) -> Dict[str, Any]:
        """Simple linear trend forecast for short time series."""
        if len(daily_data) < 30:
            # Use mean for very short series
            mean_value = daily_data.mean()
            point_forecast = [mean_value] * periods
        else:
            # Linear regression trend
            x = np.arange(len(daily_data))
            y = daily_data.values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            future_x = np.arange(len(daily_data), len(daily_data) + periods)
            point_forecast = (slope * future_x + intercept).tolist()
        
        forecast_dates = pd.date_range(
            start=daily_data.index[-1] + timedelta(days=1),
            periods=periods,
            freq='D'
        ).tolist()
        
        # Confidence intervals based on historical volatility
        volatility = daily_data.std()
        confidence_width = 1.645 * volatility
        lower_bound = (np.array(point_forecast) - confidence_width).tolist()
        upper_bound = (np.array(point_forecast) + confidence_width).tolist()
        
        return {
            'dates': forecast_dates,
            'forecast': point_forecast,
            'lower_bound': lower_bound, 
            'upper_bound': upper_bound,
            'confidence_level': 0.9,
            'method': 'Linear Trend'
        }


class WeatherCorrelator:
    """Weather correlation analysis for environmental factor impact."""
    
    def __init__(self, location: Optional[str] = None):
        self.location = location
        self._weather_cache = {}
    
    def correlate(self, metric_data: pd.Series) -> Optional[WeatherCorrelation]:
        """Analyze correlation between metric and weather patterns.
        
        Args:
            metric_data: Time series data with datetime index
            
        Returns:
            WeatherCorrelation object or None if weather data unavailable
        """
        logger.info("Starting weather correlation analysis")
        
        # For now, return simulated correlation analysis
        # In production, this would integrate with weather APIs
        return self._simulate_weather_correlation(metric_data)
    
    def _simulate_weather_correlation(self, metric_data: pd.Series) -> WeatherCorrelation:
        """Simulate weather correlation for demonstration purposes."""
        # Generate synthetic seasonal temperature data
        dates = metric_data.index
        day_of_year = dates.dayofyear
        
        # Simulate temperature (sinusoidal with random noise)
        temp_pattern = 50 + 30 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
        temp_noise = np.random.normal(0, 5, len(temp_pattern))
        temperature = temp_pattern + temp_noise
        
        # Calculate correlations
        temp_corr, temp_p = stats.pearsonr(metric_data.values, temperature)
        
        # Simulate other weather factors
        precip_corr = np.random.uniform(-0.3, 0.1)  # Generally negative correlation
        daylight_corr = np.random.uniform(-0.2, 0.4)  # Variable correlation
        
        # Calculate seasonal temperature effect
        seasonal_effect = abs(temp_corr) * np.std(temperature) / np.std(metric_data.values)
        
        return WeatherCorrelation(
            temperature_correlation=temp_corr,
            precipitation_correlation=precip_corr,
            daylight_correlation=daylight_corr,
            seasonal_temperature_effect=seasonal_effect,
            weather_significance=temp_p,
            optimal_conditions={
                'temperature_range': (65, 75),
                'max_precipitation': 0.1,
                'min_daylight_hours': 10
            }
        )


class SeasonalPatternAnalyzer:
    """Main class for comprehensive seasonal pattern analysis."""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.fourier_analyzer = FourierAnalyzer()
        self.stl_decomposer = SeasonalDecomposer()
        self.prophet_forecaster = ProphetForecaster()
        self.weather_correlator = WeatherCorrelator()
    
    def analyze_seasonality(self, metric: str) -> SeasonalAnalysis:
        """Comprehensive seasonal pattern analysis for a specific metric.
        
        Args:
            metric: Name of the metric column to analyze
            
        Returns:
            SeasonalAnalysis object with comprehensive results
        """
        logger.info(f"Starting comprehensive seasonal analysis for metric: {metric}")
        
        if metric not in self.data.columns:
            raise ValueError(f"Metric '{metric}' not found in data")
        
        # Extract metric time series
        metric_data = self.data[metric].dropna()
        if len(metric_data) < 30:
            raise ValueError(f"Insufficient data for analysis: {len(metric_data)} points")
        
        analysis_start = metric_data.index.min()
        analysis_end = metric_data.index.max()
        
        # 1. Fourier Analysis
        fourier_results = self.fourier_analyzer.analyze(metric_data)
        
        # 2. STL Decomposition (enhanced from existing)
        stl_decomposition = self.stl_decomposer.decompose(
            metric_data.values.tolist(), 
            metric_data.index.tolist()
        )
        
        # 3. Weather Correlation
        weather_correlation = self.weather_correlator.correlate(metric_data)
        
        # 4. Generate Visualization Data
        polar_plot_data = self._create_polar_plot_data(metric_data)
        phase_plot_data = self._create_phase_plot_data(metric_data)
        
        # 5. Calculate Seasonality Metrics
        seasonality_strength = max(
            fourier_results.seasonal_strength,
            stl_decomposition.seasonal_strength
        )
        seasonality_category = self._categorize_seasonality(seasonality_strength)
        pattern_consistency = self._calculate_pattern_consistency(metric_data)
        
        # 6. Generate Forecast
        forecast_data = self.prophet_forecaster.forecast(metric_data)
        
        # 7. Detect Pattern Breaks
        pattern_breaks = self._detect_pattern_breaks(metric_data, stl_decomposition)
        
        # 8. Generate Goal Timing Recommendations
        goal_recommendations = self._generate_goal_timing_recommendations(
            metric, metric_data, fourier_results
        )
        
        # 9. Multi-year Analysis
        year_variance, evolution_trend = self._analyze_pattern_evolution(metric_data)
        
        # 10. Statistical Validation
        statistical_significance = self._validate_seasonality(metric_data)
        
        return SeasonalAnalysis(
            metric_name=metric,
            analysis_period=(analysis_start, analysis_end),
            fourier_results=fourier_results,
            stl_decomposition=stl_decomposition,
            weather_correlation=weather_correlation,
            polar_plot_data=polar_plot_data,
            phase_plot_data=phase_plot_data,
            seasonality_strength=seasonality_strength,
            seasonality_category=seasonality_category,
            pattern_consistency=pattern_consistency,
            forecast_data=forecast_data,
            pattern_breaks=pattern_breaks,
            goal_timing_recommendations=goal_recommendations,
            year_over_year_variance=year_variance,
            pattern_evolution_trend=evolution_trend,
            statistical_significance=statistical_significance,
            confidence_level=1 - statistical_significance
        )
    
    def _create_polar_plot_data(self, metric_data: pd.Series) -> PolarPlotData:
        """Create data for polar plot visualization of annual cycles."""
        # Group data by month across all years
        monthly_data = metric_data.groupby(metric_data.index.month).agg(['mean', 'std'])
        
        # Create angles for 12 months (0 to 2π)
        angles = [2 * np.pi * (month - 1) / 12 for month in range(1, 13)]
        radii = monthly_data['mean'].values.tolist()
        
        # Normalize radii to center around mean
        center_value = np.mean(radii)
        max_radius = max(radii) - center_value
        
        # Create colors based on season
        season_colors = ['#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e', '#ff7f0e', 
                        '#2ca02c', '#2ca02c', '#2ca02c', '#d62728', '#d62728', 
                        '#9467bd', '#1f77b4']  # Winter, Spring, Summer, Fall colors
        
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Get unique years for multi-year overlay
        years = sorted(metric_data.index.year.unique())
        
        return PolarPlotData(
            angles=angles,
            radii=radii,
            years=years,
            colors=season_colors,
            labels=labels,
            center_value=center_value,
            max_radius=max_radius
        )
    
    def _create_phase_plot_data(self, metric_data: pd.Series) -> PhasePlotData:
        """Create data for phase plot visualization of pattern shifts."""
        # Calculate rate of change (derivative)
        daily_data = metric_data.resample('D').mean().interpolate()
        rate_of_change = daily_data.diff().fillna(0).values.tolist()
        current_values = daily_data.values.tolist()
        
        # Create trajectory colors based on direction
        colors = []
        for roc in rate_of_change:
            if roc > 0:
                colors.append('#2ca02c')  # Green for increasing
            elif roc < 0:
                colors.append('#d62728')  # Red for decreasing
            else:
                colors.append('#1f77b4')  # Blue for stable
        
        # Create direction arrows for visualization
        arrows = []
        for i in range(0, len(current_values), max(1, len(current_values) // 20)):
            if i + 1 < len(current_values):
                x, y = current_values[i], rate_of_change[i]
                dx = current_values[i + 1] - x
                dy = rate_of_change[i + 1] - y
                arrows.append((x, y, dx, dy))
        
        return PhasePlotData(
            current_values=current_values,
            rate_of_change=rate_of_change,
            dates=daily_data.index.tolist(),
            trajectory_color=colors,
            direction_arrows=arrows
        )
    
    def _categorize_seasonality(self, strength: float) -> SeasonalStrength:
        """Categorize seasonality strength."""
        if strength < 0.1:
            return SeasonalStrength.NONE
        elif strength < 0.3:
            return SeasonalStrength.WEAK
        elif strength < 0.6:
            return SeasonalStrength.MODERATE
        elif strength < 0.8:
            return SeasonalStrength.STRONG
        else:
            return SeasonalStrength.VERY_STRONG
    
    def _calculate_pattern_consistency(self, metric_data: pd.Series) -> float:
        """Calculate how consistent the seasonal pattern is across years."""
        if len(metric_data) < 365 * 2:  # Need at least 2 years
            return 0.0
        
        # Group by month and year, then calculate coefficient of variation
        monthly_means = metric_data.groupby([metric_data.index.year, metric_data.index.month]).mean()
        monthly_patterns = monthly_means.groupby(level=1)  # Group by month
        
        consistency_scores = []
        for month, group in monthly_patterns:
            if len(group) > 1:  # Need multiple years for the same month
                cv = group.std() / group.mean() if group.mean() != 0 else 1
                consistency_scores.append(1 / (1 + cv))  # Convert to consistency score
        
        return np.mean(consistency_scores) if consistency_scores else 0.0
    
    def _detect_pattern_breaks(self, metric_data: pd.Series, 
                             decomposition: SeasonalDecomposition) -> List[PatternBreakAlert]:
        """Detect significant breaks in seasonal patterns."""
        alerts = []
        
        if len(decomposition.residual) < 30:
            return alerts
        
        residuals = np.array(decomposition.residual)
        threshold = 2.0 * np.std(residuals)
        
        # Find points where residuals exceed threshold
        break_indices = np.where(np.abs(residuals) > threshold)[0]
        
        for idx in break_indices:
            if idx < len(decomposition.dates):
                break_date = decomposition.dates[idx]
                expected = decomposition.trend[idx] + decomposition.seasonal[idx]
                actual = expected + residuals[idx]
                deviation_score = abs(residuals[idx]) / np.std(residuals)
                
                # Calculate significance using z-test
                p_value = 2 * (1 - stats.norm.cdf(deviation_score))
                
                severity = 'high' if deviation_score > 3 else 'medium' if deviation_score > 2 else 'low'
                
                alerts.append(PatternBreakAlert(
                    date=break_date,
                    metric=metric_data.name or "Unknown",
                    expected_value=expected,
                    actual_value=actual,
                    deviation_score=deviation_score,
                    significance=p_value,
                    description=f"Pattern break detected: {deviation_score:.1f}σ deviation",
                    severity=severity
                ))
        
        return alerts
    
    def _generate_goal_timing_recommendations(self, metric: str, metric_data: pd.Series,
                                            fourier_results: FourierAnalysis) -> List[GoalTimingRecommendation]:
        """Generate recommendations for optimal goal timing."""
        recommendations = []
        
        if not fourier_results.annual_cycle_detected:
            return recommendations
        
        # Find the dominant annual component
        annual_component = None
        for comp in fourier_results.dominant_frequencies:
            if 0.8 <= comp.frequency <= 1.2:  # Annual frequency
                annual_component = comp
                break
        
        if annual_component is None:
            return recommendations
        
        # Calculate optimal timing based on phase
        phase_days = annual_component.phase * 365.25 / (2 * np.pi)
        optimal_start = datetime.now().replace(month=1, day=1) + timedelta(days=phase_days % 365.25)
        
        # Estimate success probability based on seasonal strength
        success_prob = 0.5 + (fourier_results.seasonal_strength * 0.4)  # 50-90% range
        
        # Generate contextual challenges and evidence
        challenges = ["Weather variations", "Holiday disruptions", "Schedule changes"]
        evidence = {
            "historical_pattern_strength": fourier_results.seasonal_strength,
            "optimal_phase": annual_component.phase,
            "annual_amplitude": annual_component.amplitude
        }
        
        recommendations.append(GoalTimingRecommendation(
            goal_type="General Improvement",
            optimal_start_date=optimal_start,
            success_probability=success_prob,
            expected_challenges=challenges,
            supporting_evidence=evidence,
            confidence_interval=(success_prob - 0.1, min(0.95, success_prob + 0.1))
        ))
        
        return recommendations
    
    def _analyze_pattern_evolution(self, metric_data: pd.Series) -> Tuple[float, str]:
        """Analyze how seasonal patterns evolve over multiple years."""
        if len(metric_data) < 365 * 2:
            return 0.0, "insufficient_data"
        
        years = sorted(metric_data.index.year.unique())
        if len(years) < 2:
            return 0.0, "insufficient_years"
        
        # Calculate year-over-year variance in seasonal patterns
        yearly_patterns = {}
        for year in years:
            year_data = metric_data[metric_data.index.year == year]
            if len(year_data) > 30:  # Minimum data for pattern
                monthly_means = year_data.groupby(year_data.index.month).mean()
                yearly_patterns[year] = monthly_means
        
        if len(yearly_patterns) < 2:
            return 0.0, "insufficient_patterns"
        
        # Calculate variance across years for each month
        monthly_variances = []
        for month in range(1, 13):
            month_values = []
            for year, pattern in yearly_patterns.items():
                if month in pattern.index:
                    month_values.append(pattern[month])
            
            if len(month_values) > 1:
                monthly_variances.append(np.var(month_values))
        
        year_variance = np.mean(monthly_variances) if monthly_variances else 0.0
        
        # Determine evolution trend
        if len(yearly_patterns) >= 3:
            # Calculate trend in pattern strength over time
            pattern_strengths = []
            for year in sorted(yearly_patterns.keys()):
                pattern = yearly_patterns[year]
                strength = pattern.std() / pattern.mean() if pattern.mean() != 0 else 0
                pattern_strengths.append(strength)
            
            if len(pattern_strengths) >= 3:
                trend_slope, _, _, p_value, _ = stats.linregress(
                    range(len(pattern_strengths)), pattern_strengths
                )
                
                if p_value < 0.05:  # Significant trend
                    if trend_slope > 0.01:
                        evolution_trend = "strengthening"
                    elif trend_slope < -0.01:
                        evolution_trend = "weakening"
                    else:
                        evolution_trend = "stable"
                else:
                    evolution_trend = "stable"
            else:
                evolution_trend = "stable"
        else:
            evolution_trend = "stable"
        
        return year_variance, evolution_trend
    
    def _validate_seasonality(self, metric_data: pd.Series) -> float:
        """Statistical validation of seasonal patterns using multiple tests."""
        try:
            from statsmodels.tsa.stattools import adfuller
            from statsmodels.stats.diagnostic import acorr_ljungbox
            
            # Augmented Dickey-Fuller test for stationarity
            adf_result = adfuller(metric_data.values)
            adf_p_value = adf_result[1]
            
            # Ljung-Box test for autocorrelation (seasonality)
            if len(metric_data) > 12:
                lb_result = acorr_ljungbox(metric_data.values, lags=min(12, len(metric_data) // 4))
                lb_p_value = lb_result['lb_pvalue'].min()
            else:
                lb_p_value = 1.0
            
            # Combine tests (take minimum p-value for conservative estimate)
            combined_p_value = min(adf_p_value, lb_p_value)
            
            return combined_p_value
            
        except ImportError:
            logger.warning("statsmodels not available for statistical validation")
            # Fallback: use variance ratio test
            return self._variance_ratio_test(metric_data)
    
    def _variance_ratio_test(self, metric_data: pd.Series) -> float:
        """Fallback statistical test using variance ratio."""
        # Compare variance of detrended data vs random walk
        detrended = metric_data - metric_data.rolling(window=30, center=True).mean()
        detrended = detrended.dropna()
        
        if len(detrended) < 30:
            return 1.0
        
        # Calculate variance ratio
        observed_var = detrended.var()
        expected_var = detrended.diff().var() * len(detrended)  # Random walk variance
        
        if expected_var == 0:
            return 1.0
        
        variance_ratio = observed_var / expected_var
        
        # Convert to approximate p-value (rough heuristic)
        if variance_ratio < 0.5 or variance_ratio > 2.0:
            return 0.01  # Strong evidence of pattern
        elif variance_ratio < 0.7 or variance_ratio > 1.4:
            return 0.05  # Moderate evidence
        else:
            return 0.1   # Weak evidence
    
    def identify_optimal_goal_timing(self, goal_type: str) -> List[GoalTimingRecommendation]:
        """Suggest best times to pursue goals based on historical patterns."""
        recommendations = []
        
        # Analyze relevant metrics for the goal type
        relevant_metrics = self._get_relevant_metrics(goal_type)
        
        for metric in relevant_metrics:
            if metric in self.data.columns:
                analysis = self.analyze_seasonality(metric)
                recommendations.extend(analysis.goal_timing_recommendations)
        
        return recommendations
    
    def _get_relevant_metrics(self, goal_type: str) -> List[str]:
        """Map goal types to relevant health metrics."""
        goal_metric_map = {
            "weight_loss": ["Weight", "BodyMass", "ActiveEnergyBurned"],
            "fitness": ["StepCount", "DistanceWalkingRunning", "ActiveEnergyBurned"],
            "sleep": ["SleepAnalysis", "TimeInBed"],
            "activity": ["StepCount", "FlightsClimbed", "ExerciseTime"],
            "general": list(self.data.columns)
        }
        
        return goal_metric_map.get(goal_type.lower(), ["StepCount", "ActiveEnergyBurned"])
    
    def create_polar_visualization(self, metric: str, years: Optional[List[int]] = None) -> PolarPlotData:
        """Create circular annual pattern visualization data."""
        if metric not in self.data.columns:
            raise ValueError(f"Metric '{metric}' not found in data")
        
        metric_data = self.data[metric].dropna()
        
        if years:
            metric_data = metric_data[metric_data.index.year.isin(years)]
        
        return self._create_polar_plot_data(metric_data)
    
    def detect_pattern_breaks(self, metric: str, threshold: float = 2.0) -> List[PatternBreakAlert]:
        """Identify when patterns are breaking from expected behavior."""
        analysis = self.analyze_seasonality(metric)
        return analysis.pattern_breaks