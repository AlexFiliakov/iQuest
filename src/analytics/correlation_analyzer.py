"""
Correlation Analysis Engine for Apple Health Monitor
Implements comprehensive correlation analysis including Pearson/Spearman correlations,
lag correlation analysis, partial correlations, and causality detection.
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy.stats.contingency import chi2_contingency
from statsmodels.tsa.stattools import grangercausalitytests
# from statsmodels.stats.correlation_tools import corr_pearson  # Not available in newer versions
import networkx as nx
from typing import Dict, List, Tuple, Optional, Any
import warnings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Core correlation analysis engine supporting multiple correlation types,
    causality detection, and significance testing.
    """
    
    def __init__(self, data: pd.DataFrame, significance_threshold: float = 0.05):
        """
        Initialize the correlation analyzer.
        
        Args:
            data: DataFrame with datetime index and numeric columns for metrics
            significance_threshold: P-value threshold for statistical significance
        """
        self.data = data.copy()
        self.significance_threshold = significance_threshold
        self.correlation_cache = {}
        self.p_value_cache = {}
        
        # Ensure data has datetime index
        if not isinstance(self.data.index, pd.DatetimeIndex):
            if 'date' in self.data.columns:
                self.data['date'] = pd.to_datetime(self.data['date'])
                self.data.set_index('date', inplace=True)
            else:
                logger.warning("Data should have datetime index for time-based analysis")
        
        # Store numeric columns only
        self.numeric_columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        if len(self.numeric_columns) < 2:
            raise ValueError("Need at least 2 numeric columns for correlation analysis")
    
    def calculate_correlations(self, method: str = 'pearson', 
                             min_periods: int = 30) -> pd.DataFrame:
        """
        Calculate correlation matrix using specified method.
        
        Args:
            method: 'pearson' or 'spearman'
            min_periods: Minimum number of observations required per pair
            
        Returns:
            Correlation matrix with significance markers
        """
        cache_key = f"{method}_{min_periods}"
        
        if cache_key in self.correlation_cache:
            return self.correlation_cache[cache_key]
        
        # Get numeric data only
        numeric_data = self.data[self.numeric_columns]
        
        if method == 'pearson':
            corr_matrix = numeric_data.corr(method='pearson', min_periods=min_periods)
            p_values = self._calculate_pearson_pvalues(numeric_data, min_periods)
        elif method == 'spearman':
            corr_matrix = numeric_data.corr(method='spearman', min_periods=min_periods)
            p_values = self._calculate_spearman_pvalues(numeric_data, min_periods)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        # Store p-values for later use
        self.p_value_cache[cache_key] = p_values
        
        # Add significance markers to correlation matrix
        corr_matrix_with_significance = self._add_significance_markers(
            corr_matrix, p_values
        )
        
        self.correlation_cache[cache_key] = corr_matrix_with_significance
        return corr_matrix_with_significance
    
    def _calculate_pearson_pvalues(self, data: pd.DataFrame, 
                                 min_periods: int) -> pd.DataFrame:
        """Calculate p-values for Pearson correlations."""
        columns = data.columns
        p_values = np.ones((len(columns), len(columns)))
        
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i != j:
                    # Get valid pairs
                    valid_mask = ~(data[col1].isna() | data[col2].isna())
                    valid_data1 = data[col1][valid_mask]
                    valid_data2 = data[col2][valid_mask]
                    
                    if len(valid_data1) >= min_periods:
                        try:
                            _, p_value = pearsonr(valid_data1, valid_data2)
                            p_values[i, j] = p_value
                        except Exception as e:
                            logger.warning(f"Failed to calculate Pearson p-value for {col1}-{col2}: {e}")
                            p_values[i, j] = 1.0
                    else:
                        p_values[i, j] = 1.0
        
        return pd.DataFrame(p_values, index=columns, columns=columns)
    
    def _calculate_spearman_pvalues(self, data: pd.DataFrame, 
                                  min_periods: int) -> pd.DataFrame:
        """Calculate p-values for Spearman correlations."""
        columns = data.columns
        p_values = np.ones((len(columns), len(columns)))
        
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i != j:
                    # Get valid pairs
                    valid_mask = ~(data[col1].isna() | data[col2].isna())
                    valid_data1 = data[col1][valid_mask]
                    valid_data2 = data[col2][valid_mask]
                    
                    if len(valid_data1) >= min_periods:
                        try:
                            _, p_value = spearmanr(valid_data1, valid_data2)
                            p_values[i, j] = p_value
                        except Exception as e:
                            logger.warning(f"Failed to calculate Spearman p-value for {col1}-{col2}: {e}")
                            p_values[i, j] = 1.0
                    else:
                        p_values[i, j] = 1.0
        
        return pd.DataFrame(p_values, index=columns, columns=columns)
    
    def _add_significance_markers(self, corr_matrix: pd.DataFrame, 
                                p_values: pd.DataFrame) -> pd.DataFrame:
        """Add significance level markers to correlation matrix."""
        result = corr_matrix.copy()
        
        # Create significance markers
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix.columns)):
                if i != j:
                    p_val = p_values.iloc[i, j]
                    corr_val = corr_matrix.iloc[i, j]
                    
                    if pd.isna(p_val) or pd.isna(corr_val):
                        continue
                    
                    # Mark significance level
                    if p_val < 0.001:
                        result.iloc[i, j] = f"{corr_val:.3f}***"
                    elif p_val < 0.01:
                        result.iloc[i, j] = f"{corr_val:.3f}**"
                    elif p_val < self.significance_threshold:
                        result.iloc[i, j] = f"{corr_val:.3f}*"
        
        return result
    
    def calculate_lag_correlation(self, metric1: str, metric2: str, 
                                max_lag: int = 30) -> Dict[str, Any]:
        """
        Calculate correlation at different time lags to identify lead/lag relationships.
        
        Args:
            metric1: First metric name
            metric2: Second metric name
            max_lag: Maximum lag to test (in both directions)
            
        Returns:
            Dictionary with lag analysis results
        """
        if metric1 not in self.numeric_columns or metric2 not in self.numeric_columns:
            raise ValueError(f"Metrics must be numeric columns: {self.numeric_columns}")
        
        results = {
            'lags': [],
            'correlations': [],
            'p_values': [],
            'confidence_intervals': [],
            'sample_sizes': []
        }
        
        series1 = self.data[metric1]
        series2 = self.data[metric2]
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # metric1 leads metric2 (metric1 shifted forward)
                shifted_series1 = series1.shift(-lag)
                aligned_series2 = series2
            else:
                # metric2 leads metric1 (metric2 shifted forward)
                shifted_series1 = series1
                aligned_series2 = series2.shift(lag)
            
            # Remove NaN values from shifting
            mask = ~(shifted_series1.isna() | aligned_series2.isna())
            valid_count = mask.sum()
            
            if valid_count >= 10:  # Minimum data points for reliable correlation
                try:
                    corr, p_value = pearsonr(
                        shifted_series1[mask],
                        aligned_series2[mask]
                    )
                    
                    # Calculate confidence interval
                    ci_low, ci_high = self._calculate_confidence_interval(corr, valid_count)
                    
                    results['lags'].append(lag)
                    results['correlations'].append(corr)
                    results['p_values'].append(p_value)
                    results['confidence_intervals'].append((ci_low, ci_high))
                    results['sample_sizes'].append(valid_count)
                    
                except Exception as e:
                    logger.warning(f"Failed lag correlation at lag {lag}: {e}")
                    continue
        
        # Find optimal lag
        if results['correlations']:
            results['optimal_lag'] = self._find_optimal_lag(results)
            results['max_correlation'] = max(results['correlations'], key=abs)
            results['max_correlation_lag'] = results['lags'][
                np.argmax([abs(c) for c in results['correlations']])
            ]
        
        return results
    
    def _calculate_confidence_interval(self, correlation: float, n: int, 
                                     confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for correlation coefficient."""
        if n < 4:
            return -1.0, 1.0
        
        # Fisher's z-transformation
        z = 0.5 * np.log((1 + correlation) / (1 - correlation))
        se = 1.0 / np.sqrt(n - 3)
        
        # Critical value for confidence interval
        alpha = 1 - confidence
        z_critical = 1.96  # For 95% confidence
        
        z_lower = z - z_critical * se
        z_upper = z + z_critical * se
        
        # Transform back to correlation scale
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        
        return float(r_lower), float(r_upper)
    
    def _find_optimal_lag(self, lag_results: Dict[str, List]) -> int:
        """Find optimal lag based on strongest significant correlation."""
        correlations = np.array(lag_results['correlations'])
        p_values = np.array(lag_results['p_values'])
        lags = np.array(lag_results['lags'])
        
        # Only consider significant correlations
        significant_mask = p_values < self.significance_threshold
        
        if not significant_mask.any():
            # If no significant correlations, return lag with highest absolute correlation
            return lags[np.argmax(np.abs(correlations))]
        
        # Among significant correlations, find strongest
        significant_correlations = correlations[significant_mask]
        significant_lags = lags[significant_mask]
        
        strongest_idx = np.argmax(np.abs(significant_correlations))
        return significant_lags[strongest_idx]
    
    def calculate_partial_correlation(self, metric1: str, metric2: str, 
                                    controlling_for: List[str], 
                                    min_periods: int = 50) -> Tuple[float, float]:
        """
        Calculate partial correlation controlling for other variables.
        
        Args:
            metric1: First metric name
            metric2: Second metric name  
            controlling_for: List of metric names to control for
            min_periods: Minimum observations required
            
        Returns:
            Tuple of (partial_correlation, p_value)
        """
        # Validate inputs
        all_metrics = [metric1, metric2] + controlling_for
        missing_metrics = set(all_metrics) - set(self.numeric_columns)
        if missing_metrics:
            raise ValueError(f"Metrics not found: {missing_metrics}")
        
        # Create data matrix with all variables
        data_subset = self.data[all_metrics].dropna()
        
        if len(data_subset) < min_periods:
            logger.warning(f"Insufficient data for partial correlation: {len(data_subset)} < {min_periods}")
            return np.nan, 1.0
        
        try:
            # Calculate partial correlation using multiple regression approach
            # Regress metric1 on controlling variables
            X_control = data_subset[controlling_for]
            X_control = np.column_stack([np.ones(len(X_control)), X_control])  # Add intercept
            
            y1 = data_subset[metric1].values
            y2 = data_subset[metric2].values
            
            # Calculate residuals
            beta1 = np.linalg.lstsq(X_control, y1, rcond=None)[0]
            beta2 = np.linalg.lstsq(X_control, y2, rcond=None)[0]
            
            residuals1 = y1 - X_control @ beta1
            residuals2 = y2 - X_control @ beta2
            
            # Correlation of residuals is partial correlation
            partial_corr, p_value = pearsonr(residuals1, residuals2)
            
            return float(partial_corr), float(p_value)
            
        except Exception as e:
            logger.error(f"Failed to calculate partial correlation: {e}")
            return np.nan, 1.0
    
    def get_correlation_strength_category(self, correlation: float) -> str:
        """Categorize correlation strength."""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.8:
            return "Very Strong"
        elif abs_corr >= 0.6:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def get_significant_correlations(self, method: str = 'pearson', 
                                   min_strength: float = 0.3) -> List[Dict[str, Any]]:
        """
        Get list of significant correlations above minimum strength threshold.
        
        Args:
            method: Correlation method to use
            min_strength: Minimum absolute correlation strength
            
        Returns:
            List of correlation results with metadata
        """
        # Calculate correlations and get p-values
        corr_matrix = self.calculate_correlations(method)
        cache_key = f"{method}_30"  # Default min_periods
        p_values = self.p_value_cache.get(cache_key)
        
        if p_values is None:
            logger.warning("P-values not found, recalculating correlations")
            corr_matrix = self.calculate_correlations(method)
            p_values = self.p_value_cache[cache_key]
        
        significant_correlations = []
        
        for i, metric1 in enumerate(corr_matrix.index):
            for j, metric2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates and self-correlations
                    # Extract numeric value from potentially marked correlation
                    corr_val = corr_matrix.iloc[i, j]
                    if isinstance(corr_val, str):
                        # Extract numeric part from marked correlation
                        corr_val = float(corr_val.split('*')[0])
                    
                    p_val = p_values.iloc[i, j]
                    
                    if (abs(corr_val) >= min_strength and 
                        p_val < self.significance_threshold and
                        not pd.isna(corr_val)):
                        
                        significant_correlations.append({
                            'metric1': metric1,
                            'metric2': metric2,
                            'correlation': corr_val,
                            'p_value': p_val,
                            'strength_category': self.get_correlation_strength_category(corr_val),
                            'method': method,
                            'direction': 'positive' if corr_val > 0 else 'negative'
                        })
        
        # Sort by absolute correlation strength
        significant_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return significant_correlations
    
    def get_correlation_summary(self) -> Dict[str, Any]:
        """Get summary statistics of correlation analysis."""
        pearson_corr = self.calculate_correlations('pearson')
        spearman_corr = self.calculate_correlations('spearman')
        
        # Extract numeric values from correlation matrices
        pearson_values = []
        spearman_values = []
        
        for i in range(len(pearson_corr)):
            for j in range(i + 1, len(pearson_corr.columns)):
                p_val = pearson_corr.iloc[i, j]
                s_val = spearman_corr.iloc[i, j]
                
                # Extract numeric parts
                if isinstance(p_val, str):
                    p_val = float(p_val.split('*')[0])
                if isinstance(s_val, str):
                    s_val = float(s_val.split('*')[0])
                
                if not pd.isna(p_val):
                    pearson_values.append(p_val)
                if not pd.isna(s_val):
                    spearman_values.append(s_val)
        
        pearson_values = np.array(pearson_values)
        spearman_values = np.array(spearman_values)
        
        significant_pearson = self.get_significant_correlations('pearson')
        significant_spearman = self.get_significant_correlations('spearman')
        
        return {
            'total_metric_pairs': len(pearson_values),
            'pearson_summary': {
                'mean_correlation': float(np.mean(np.abs(pearson_values))) if len(pearson_values) > 0 else 0,
                'max_correlation': float(np.max(np.abs(pearson_values))) if len(pearson_values) > 0 else 0,
                'significant_correlations': len(significant_pearson),
                'strong_correlations': len([c for c in significant_pearson if abs(c['correlation']) >= 0.6])
            },
            'spearman_summary': {
                'mean_correlation': float(np.mean(np.abs(spearman_values))) if len(spearman_values) > 0 else 0,
                'max_correlation': float(np.max(np.abs(spearman_values))) if len(spearman_values) > 0 else 0,
                'significant_correlations': len(significant_spearman),
                'strong_correlations': len([c for c in significant_spearman if abs(c['correlation']) >= 0.6])
            },
            'data_quality': {
                'metrics_count': len(self.numeric_columns),
                'date_range': {
                    'start': self.data.index.min().isoformat() if hasattr(self.data.index, 'min') else None,
                    'end': self.data.index.max().isoformat() if hasattr(self.data.index, 'max') else None
                },
                'total_observations': len(self.data)
            }
        }