"""
Adaptive threshold system for performance benchmarks.

This module manages performance thresholds that adapt to different
environments and hardware capabilities.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
import platform
import psutil
import timeit


class AdaptiveThresholds:
    """Manage adaptive performance thresholds based on environment."""
    
    def __init__(self, baseline_file: str = "benchmarks/baseline.json"):
        """
        Initialize adaptive threshold manager.
        
        Args:
            baseline_file: Path to baseline performance data
        """
        self.baseline_file = Path(baseline_file)
        self.baselines = self._load_baselines()
        self.environment_factor = self._calculate_env_factor()
        self.hardware_profile = self._get_hardware_profile()
        
    def _load_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load baseline performance data from file."""
        if not self.baseline_file.exists():
            return {}
            
        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_baselines(self):
        """Save baseline performance data to file."""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)
    
    def _get_hardware_profile(self) -> Dict[str, Any]:
        """Get current hardware profile for environment detection."""
        return {
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'machine': platform.machine()
        }
    
    def _calculate_env_factor(self) -> float:
        """
        Calculate environment performance factor.
        
        Returns:
            Factor > 1.0 means slower environment, < 1.0 means faster
        """
        # Run a simple CPU benchmark
        benchmark_code = """
import math
result = 0
for i in range(1000000):
    result += math.sqrt(i)
"""
        
        # Time the benchmark
        benchmark_time = timeit.timeit(
            benchmark_code, 
            number=3
        ) / 3  # Average of 3 runs
        
        # Baseline from a reference machine (adjust as needed)
        # This represents a modern development machine
        baseline_time = 0.5  # seconds
        
        # Calculate factor
        factor = benchmark_time / baseline_time
        
        # Apply bounds to prevent extreme values
        return max(0.5, min(3.0, factor))
    
    def get_threshold(
        self, 
        test_name: str, 
        metric: str,
        margin: float = 1.2,
        environment_adjust: bool = True
    ) -> float:
        """
        Get adjusted threshold for a specific test and metric.
        
        Args:
            test_name: Name of the test
            metric: Metric name (e.g., 'duration', 'memory_mb')
            margin: Safety margin multiplier (1.2 = 20% margin)
            environment_adjust: Whether to adjust for environment
            
        Returns:
            Adjusted threshold value
        """
        # Get baseline value
        baseline = self.baselines.get(test_name, {}).get(metric)
        
        if baseline is None:
            # No baseline exists, use defaults based on metric type
            defaults = {
                'duration': 1.0,  # 1 second default
                'memory_mb': 100.0,  # 100MB default
                'memory_growth_mb': 50.0,  # 50MB growth default
                'cpu_percent': 80.0  # 80% CPU default
            }
            baseline = defaults.get(metric, 1.0)
        
        # Apply environment factor if requested
        if environment_adjust and metric == 'duration':
            baseline *= self.environment_factor
        
        # Apply safety margin
        return baseline * margin
    
    def update_baseline(
        self, 
        test_name: str, 
        results: Dict[str, float],
        strategy: str = 'percentile'
    ):
        """
        Update baseline with new results.
        
        Args:
            test_name: Name of the test
            results: New performance results
            strategy: Update strategy ('percentile', 'average', 'best')
        """
        if test_name not in self.baselines:
            self.baselines[test_name] = {
                '_history': {},
                '_metadata': {
                    'hardware': self.hardware_profile,
                    'env_factor': self.environment_factor
                }
            }
        
        baseline = self.baselines[test_name]
        
        # Update history for each metric
        for metric, value in results.items():
            if metric.startswith('_'):
                continue  # Skip metadata fields
                
            # Initialize history if needed
            if metric not in baseline['_history']:
                baseline['_history'][metric] = []
            
            # Add to history
            history = baseline['_history'][metric]
            history.append(value)
            
            # Keep only recent history (last 20 runs)
            if len(history) > 20:
                history = history[-20:]
                baseline['_history'][metric] = history
            
            # Update baseline value based on strategy
            if strategy == 'percentile':
                # Use 90th percentile for stability
                sorted_history = sorted(history)
                idx = int(len(sorted_history) * 0.9)
                baseline[metric] = sorted_history[min(idx, len(sorted_history) - 1)]
            elif strategy == 'average':
                # Use average of recent runs
                baseline[metric] = sum(history) / len(history)
            elif strategy == 'best':
                # Use best (minimum) value
                baseline[metric] = min(history)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        # Save updated baselines
        self._save_baselines()
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get detailed environment information."""
        return {
            'hardware': self.hardware_profile,
            'env_factor': self.environment_factor,
            'baseline_file': str(self.baseline_file),
            'baselines_loaded': len(self.baselines) > 0
        }
    
    def suggest_thresholds(
        self, 
        test_name: str,
        sample_results: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Suggest appropriate thresholds based on sample results.
        
        Args:
            test_name: Name of the test
            sample_results: Sample performance results
            
        Returns:
            Suggested thresholds for each metric
        """
        suggestions = {}
        
        for metric, value in sample_results.items():
            # Base suggestion on value with appropriate margins
            if 'duration' in metric:
                # Time-based metrics: 50% margin
                suggestions[f"max_{metric}"] = value * 1.5
            elif 'memory' in metric:
                # Memory metrics: 100% margin
                suggestions[f"max_{metric}"] = value * 2.0
            elif 'cpu' in metric:
                # CPU metrics: fixed threshold
                suggestions[f"max_{metric}"] = 90.0  # 90% CPU max
            else:
                # Default: 50% margin
                suggestions[f"max_{metric}"] = value * 1.5
        
        return suggestions
    
    def is_ci_environment(self) -> bool:
        """Detect if running in CI environment."""
        ci_env_vars = [
            'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS',
            'JENKINS', 'TRAVIS', 'CIRCLECI', 'GITLAB_CI'
        ]
        
        return any(os.getenv(var) for var in ci_env_vars)
    
    def get_ci_adjustment_factor(self) -> float:
        """Get adjustment factor for CI environments."""
        if self.is_ci_environment():
            # CI environments are typically slower
            return 2.0
        return 1.0


