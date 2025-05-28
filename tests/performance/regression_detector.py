"""
Performance regression detection for CI/CD pipelines.

This module provides tools to detect performance regressions by comparing
current test execution metrics against established baselines and alerting
when performance degrades beyond acceptable thresholds.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import subprocess


@dataclass
class RegressionResult:
    """Result of regression detection."""
    test_category: str
    metric: str
    current_value: float
    baseline_value: float
    change_percent: float
    threshold_percent: float
    is_regression: bool
    severity: str  # 'minor', 'major', 'critical'


class PerformanceRegressionDetector:
    """Detects performance regressions in test suite execution."""
    
    def __init__(
        self, 
        baseline_file: str = "tests/performance/baseline_metrics.json",
        thresholds: Dict[str, float] = None
    ):
        """
        Initialize regression detector.
        
        Args:
            baseline_file: Path to baseline metrics file
            thresholds: Custom regression thresholds for different metrics
        """
        self.baseline_file = Path(baseline_file)
        self.thresholds = thresholds or {
            'execution_time': 10.0,     # 10% slower = minor regression
            'collection_time': 15.0,    # 15% slower = minor regression
            'memory_peak_mb': 20.0,     # 20% more memory = minor regression
            'total_time': 10.0          # 10% slower total = minor regression
        }
        
        self.severity_thresholds = {
            'minor': (5.0, 20.0),    # 5-20% degradation
            'major': (20.0, 50.0),   # 20-50% degradation
            'critical': (50.0, float('inf'))  # >50% degradation
        }
    
    def load_baseline(self) -> Dict:
        """Load baseline performance metrics."""
        if not self.baseline_file.exists():
            raise FileNotFoundError(f"Baseline file not found: {self.baseline_file}")
        
        with open(self.baseline_file, 'r') as f:
            return json.load(f)
    
    def run_performance_tests(self) -> Dict:
        """Run performance tests and collect current metrics."""
        # This would normally run the actual benchmark tool
        # For now, simulate with dummy data showing slight regression
        return {
            "unit": {
                "category": "unit",
                "test_count": 743,
                "collection_time": 2.8,  # 12% slower
                "execution_time": 14.0,  # 12% slower
                "total_time": 16.8,      # 12% slower
                "memory_peak_mb": 95.0,  # 12% more memory
                "memory_delta_mb": 28.0,
                "cpu_avg_percent": 48.0,
                "passed": 740,
                "failed": 3,
                "skipped": 0,
                "errors": 0,
                "timestamp": datetime.now().isoformat()
            },
            "integration": {
                "category": "integration",
                "test_count": 5,
                "collection_time": 0.5,
                "execution_time": 8.2,
                "total_time": 8.7,
                "memory_peak_mb": 125.0,
                "memory_delta_mb": 42.0,
                "cpu_avg_percent": 57.0,
                "passed": 5,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def detect_regressions(
        self, 
        current_metrics: Dict, 
        baseline_metrics: Dict
    ) -> List[RegressionResult]:
        """
        Detect performance regressions by comparing current vs baseline.
        
        Args:
            current_metrics: Current test execution metrics
            baseline_metrics: Baseline metrics to compare against
            
        Returns:
            List of regression results
        """
        regressions = []
        
        for category in current_metrics:
            if category not in baseline_metrics:
                continue
                
            current = current_metrics[category]
            baseline = baseline_metrics[category]
            
            # Check each metric for regression
            metrics_to_check = [
                ('execution_time', 'execution_time'),
                ('collection_time', 'collection_time'), 
                ('total_time', 'total_time'),
                ('memory_peak_mb', 'memory_peak_mb')
            ]
            
            for metric_name, threshold_key in metrics_to_check:
                if metric_name not in current or metric_name not in baseline:
                    continue
                    
                current_value = current[metric_name]
                baseline_value = baseline[metric_name]
                
                if baseline_value == 0:
                    continue  # Avoid division by zero
                    
                change_percent = (
                    (current_value - baseline_value) / baseline_value * 100
                )
                
                threshold = self.thresholds.get(threshold_key, 10.0)
                is_regression = change_percent > threshold
                
                # Determine severity
                severity = 'none'
                if is_regression:
                    abs_change = abs(change_percent)
                    for sev, (min_thresh, max_thresh) in self.severity_thresholds.items():
                        if min_thresh <= abs_change < max_thresh:
                            severity = sev
                            break
                
                regression = RegressionResult(
                    test_category=category,
                    metric=metric_name,
                    current_value=current_value,
                    baseline_value=baseline_value,
                    change_percent=change_percent,
                    threshold_percent=threshold,
                    is_regression=is_regression,
                    severity=severity
                )
                
                regressions.append(regression)
        
        return regressions
    
    def generate_regression_report(self, regressions: List[RegressionResult]) -> str:
        """Generate a human-readable regression report."""
        lines = [
            "# Performance Regression Detection Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Count regressions by severity
        regression_count = len([r for r in regressions if r.is_regression])
        critical_count = len([r for r in regressions if r.severity == 'critical'])
        major_count = len([r for r in regressions if r.severity == 'major'])
        minor_count = len([r for r in regressions if r.severity == 'minor'])
        
        lines.extend([
            "## Summary",
            f"Total regressions detected: {regression_count}",
            f"- Critical: {critical_count}",
            f"- Major: {major_count}",
            f"- Minor: {minor_count}",
            ""
        ])
        
        # Overall status
        if critical_count > 0:
            status = "🚨 CRITICAL - Performance severely degraded"
        elif major_count > 0:
            status = "⚠️ MAJOR - Significant performance degradation"
        elif minor_count > 0:
            status = "⚡ MINOR - Some performance degradation detected"
        else:
            status = "✅ PASS - No significant regressions detected"
            
        lines.extend([
            f"## Status: {status}",
            ""
        ])
        
        # Detailed regression breakdown
        if regression_count > 0:
            lines.extend([
                "## Regressions Detected",
                "",
                "| Category | Metric | Current | Baseline | Change | Severity |",
                "|----------|--------|---------|----------|--------|----------|"
            ])
            
            for regression in regressions:
                if regression.is_regression:
                    severity_icon = {
                        'critical': '🚨',
                        'major': '⚠️',
                        'minor': '⚡'
                    }.get(regression.severity, '')
                    
                    lines.append(
                        f"| {regression.test_category} | {regression.metric} | "
                        f"{regression.current_value:.2f} | {regression.baseline_value:.2f} | "
                        f"{regression.change_percent:+.1f}% | {severity_icon} {regression.severity} |"
                    )
            
            lines.append("")
        
        # All metrics for reference
        lines.extend([
            "## All Metrics",
            "",
            "| Category | Metric | Current | Baseline | Change |",
            "|----------|--------|---------|----------|--------|"
        ])
        
        for regression in regressions:
            lines.append(
                f"| {regression.test_category} | {regression.metric} | "
                f"{regression.current_value:.2f} | {regression.baseline_value:.2f} | "
                f"{regression.change_percent:+.1f}% |"
            )
        
        return "\n".join(lines)
    
    def should_fail_ci(self, regressions: List[RegressionResult]) -> bool:
        """Determine if CI should fail based on regression severity."""
        critical_regressions = [r for r in regressions if r.severity == 'critical']
        major_regressions = [r for r in regressions if r.severity == 'major']
        
        # Fail CI for critical regressions or too many major regressions
        return len(critical_regressions) > 0 or len(major_regressions) > 2
    
    def save_current_as_baseline(self, current_metrics: Dict):
        """Save current metrics as new baseline."""
        with open(self.baseline_file, 'w') as f:
            json.dump(current_metrics, f, indent=2)
    
    def run_regression_check(self) -> int:
        """
        Run complete regression check.
        
        Returns:
            Exit code (0 = pass, 1 = fail)
        """
        try:
            # Load baseline
            baseline = self.load_baseline()
            
            # Run current performance tests
            current = self.run_performance_tests()
            
            # Detect regressions
            regressions = self.detect_regressions(current, baseline)
            
            # Generate report
            report = self.generate_regression_report(regressions)
            print(report)
            
            # Save report to file
            report_file = Path("tests/performance/regression_report.md")
            with open(report_file, 'w') as f:
                f.write(report)
            
            # Determine if CI should fail
            should_fail = self.should_fail_ci(regressions)
            
            if should_fail:
                print("\n❌ Performance regression check FAILED")
                return 1
            else:
                print("\n✅ Performance regression check PASSED")
                return 0
                
        except Exception as e:
            print(f"❌ Error during regression check: {e}")
            return 1


def main():
    """CLI interface for regression detection."""
    parser = argparse.ArgumentParser(
        description="Detect performance regressions in test suite"
    )
    parser.add_argument(
        "--baseline",
        default="tests/performance/baseline_metrics.json",
        help="Path to baseline metrics file"
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current metrics"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Regression threshold percentage (default: 10%)"
    )
    parser.add_argument(
        "--output",
        help="Output file for regression report"
    )
    
    args = parser.parse_args()
    
    # Set custom thresholds if provided
    thresholds = {
        'execution_time': args.threshold,
        'collection_time': args.threshold,
        'memory_peak_mb': args.threshold * 2,  # More lenient for memory
        'total_time': args.threshold
    }
    
    detector = PerformanceRegressionDetector(
        baseline_file=args.baseline,
        thresholds=thresholds
    )
    
    if args.update_baseline:
        current = detector.run_performance_tests()
        detector.save_current_as_baseline(current)
        print(f"✅ Updated baseline: {args.baseline}")
        return 0
    
    return detector.run_regression_check()


if __name__ == "__main__":
    sys.exit(main())