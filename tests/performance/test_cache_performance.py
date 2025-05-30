"""
Performance testing and benchmarking for analytics caching layer.
Validates cache hit rates, performance targets, and load testing scenarios.
"""

import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np

from src.analytics.cache_manager import get_cache_manager, CacheMetrics
from src.analytics.cache_background_refresh import get_refresh_monitor, get_warmup_manager
from src.analytics.cached_calculators import (
    create_cached_daily_calculator, 
    create_cached_weekly_calculator,
    create_cached_monthly_calculator
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceTestResult:
    """Results from cache performance testing."""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Cache metrics
    total_requests: int
    cache_hit_rate: float
    l1_hit_rate: float
    l2_hit_rate: float  
    l3_hit_rate: float
    
    # Performance metrics
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    
    # Load testing metrics
    concurrent_users: int = 0
    requests_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Success criteria
    hit_rate_target_met: bool = False
    performance_target_met: bool = False
    memory_target_met: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        return result


class CachePerformanceTester:
    """Performance testing suite for cache system."""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.daily_calc = create_cached_daily_calculator()
        self.weekly_calc = create_cached_weekly_calculator()
        self.monthly_calc = create_cached_monthly_calculator()
        
        # Performance targets
        self.hit_rate_target = 0.80  # 80% hit rate
        self.l1_response_target_ms = 1.0    # <1ms for L1
        self.l2_response_target_ms = 10.0   # <10ms for L2
        self.l3_response_target_ms = 100.0  # <100ms for L3
        self.memory_limit_mb = 500.0        # 500MB memory limit
        
        # Test data
        self.test_metrics = ['steps', 'heart_rate', 'calories', 'distance', 'sleep_hours']
        self.test_date_ranges = self._generate_test_date_ranges()
        
    def _generate_test_date_ranges(self) -> List[Tuple[date, date]]:
        """Generate test date ranges."""
        base_date = date.today()
        ranges = []
        
        # Various date range sizes
        for days in [1, 7, 30, 90, 365]:
            start_date = base_date - timedelta(days=days)
            ranges.append((start_date, base_date))
        
        # Historical ranges
        for months_back in [1, 3, 6, 12]:
            end_date = base_date - timedelta(days=30 * months_back)
            start_date = end_date - timedelta(days=30)
            ranges.append((start_date, end_date))
        
        return ranges
    
    def run_basic_cache_test(self) -> PerformanceTestResult:
        """Test basic cache functionality and hit rates."""
        test_name = "basic_cache_functionality"
        start_time = datetime.now()
        
        response_times = []
        requests = []
        
        # Generate test requests
        for metric in self.test_metrics:
            for start_date, end_date in self.test_date_ranges[:5]:  # Limited for basic test
                requests.append(('daily_stats', metric, start_date, end_date))
                requests.append(('weekly_rolling', metric, 7, start_date, end_date))
                requests.append(('monthly_stats', metric, start_date.year, start_date.month))
        
        # First pass - populate cache
        logger.info("First pass: populating cache")
        for req_type, *args in requests:
            start_req = time.time()
            self._execute_request(req_type, *args)
            response_times.append((time.time() - start_req) * 1000)
        
        # Reset metrics for second pass
        initial_metrics = self.cache_manager.get_metrics()
        self.cache_manager.metrics = CacheMetrics()
        
        # Second pass - test cache hits
        logger.info("Second pass: testing cache hits")
        cache_test_times = []
        for req_type, *args in requests:
            start_req = time.time()
            self._execute_request(req_type, *args)
            cache_test_times.append((time.time() - start_req) * 1000)
        
        end_time = datetime.now()
        final_metrics = self.cache_manager.get_metrics()
        
        # Calculate results
        result = PerformanceTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            total_requests=final_metrics.total_requests,
            cache_hit_rate=final_metrics.overall_hit_rate,
            l1_hit_rate=final_metrics.l1_hit_rate,
            l2_hit_rate=final_metrics.l2_hit_rate,
            l3_hit_rate=final_metrics.l3_hit_rate,
            avg_response_time_ms=statistics.mean(cache_test_times),
            p95_response_time_ms=np.percentile(cache_test_times, 95),
            p99_response_time_ms=np.percentile(cache_test_times, 99),
            min_response_time_ms=min(cache_test_times),
            max_response_time_ms=max(cache_test_times),
            memory_usage_mb=final_metrics.memory_usage_mb,
            hit_rate_target_met=final_metrics.overall_hit_rate >= self.hit_rate_target,
            performance_target_met=statistics.mean(cache_test_times) <= self.l1_response_target_ms,
            memory_target_met=final_metrics.memory_usage_mb <= self.memory_limit_mb
        )
        
        logger.info(f"Basic cache test completed: {result.cache_hit_rate:.2%} hit rate")
        return result
    
    def run_load_test(self, concurrent_users: int = 10, duration_seconds: int = 60) -> PerformanceTestResult:
        """Run load testing with concurrent users."""
        test_name = f"load_test_{concurrent_users}_users"
        start_time = datetime.now()
        
        # Reset metrics
        self.cache_manager.metrics = CacheMetrics()
        
        all_response_times = []
        total_requests = 0
        
        def user_session() -> List[float]:
            """Simulate user session with multiple requests."""
            session_times = []
            session_start = time.time()
            
            while time.time() - session_start < duration_seconds:
                # Random request
                metric = random.choice(self.test_metrics)
                start_date, end_date = random.choice(self.test_date_ranges)
                req_type = random.choice(['daily_stats', 'weekly_rolling', 'monthly_stats'])
                
                start_req = time.time()
                try:
                    if req_type == 'daily_stats':
                        self.daily_calc.calculate_statistics(metric, start_date, end_date)
                    elif req_type == 'weekly_rolling':
                        self.weekly_calc.calculate_rolling_stats(metric, 7, start_date, end_date)
                    elif req_type == 'monthly_stats':
                        self.monthly_calc.calculate_monthly_stats(metric, start_date.year, start_date.month)
                    
                    session_times.append((time.time() - start_req) * 1000)
                    
                except Exception as e:
                    logger.warning(f"Request failed in load test: {e}")
                
                # Small delay between requests
                time.sleep(random.uniform(0.1, 0.5))
            
            return session_times
        
        # Run concurrent users
        logger.info(f"Starting load test with {concurrent_users} users for {duration_seconds} seconds")
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_session) for _ in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    session_times = future.result()
                    all_response_times.extend(session_times)
                    total_requests += len(session_times)
                except Exception as e:
                    logger.error(f"User session failed: {e}")
        
        end_time = datetime.now()
        final_metrics = self.cache_manager.get_metrics()
        
        # Calculate results
        duration = (end_time - start_time).total_seconds()
        
        result = PerformanceTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=final_metrics.total_requests,
            cache_hit_rate=final_metrics.overall_hit_rate,
            l1_hit_rate=final_metrics.l1_hit_rate,
            l2_hit_rate=final_metrics.l2_hit_rate,
            l3_hit_rate=final_metrics.l3_hit_rate,
            avg_response_time_ms=statistics.mean(all_response_times) if all_response_times else 0,
            p95_response_time_ms=np.percentile(all_response_times, 95) if all_response_times else 0,
            p99_response_time_ms=np.percentile(all_response_times, 99) if all_response_times else 0,
            min_response_time_ms=min(all_response_times) if all_response_times else 0,
            max_response_time_ms=max(all_response_times) if all_response_times else 0,
            concurrent_users=concurrent_users,
            requests_per_second=total_requests / duration if duration > 0 else 0,
            memory_usage_mb=final_metrics.memory_usage_mb,
            hit_rate_target_met=final_metrics.overall_hit_rate >= self.hit_rate_target,
            performance_target_met=statistics.mean(all_response_times) <= 50.0 if all_response_times else False,  # 50ms under load
            memory_target_met=final_metrics.memory_usage_mb <= self.memory_limit_mb
        )
        
        logger.info(f"Load test completed: {result.requests_per_second:.1f} RPS, {result.cache_hit_rate:.2%} hit rate")
        return result
    
    def run_cache_warmup_test(self) -> PerformanceTestResult:
        """Test cache warmup performance."""
        test_name = "cache_warmup"
        start_time = datetime.now()
        
        # Clear cache
        self.cache_manager.clear_all()
        self.cache_manager.metrics = CacheMetrics()
        
        # Register warmup tasks
        warmup_manager = get_warmup_manager()
        
        for metric in self.test_metrics[:3]:  # Limited for warmup test
            for start_date, end_date in self.test_date_ranges[:3]:
                # Daily stats warmup
                key = f"warmup_daily_{metric}_{start_date}_{end_date}"
                warmup_manager.register_warmup_task(
                    key=key,
                    compute_fn=lambda m=metric, s=start_date, e=end_date: self.daily_calc.calculator.calculate_statistics(m, s, e),
                    cache_config={'cache_tiers': ['l1', 'l2'], 'ttl': 3600}
                )
        
        # Execute warmup
        warmup_results = warmup_manager.warmup_cache(max_workers=4, timeout=30)
        
        end_time = datetime.now()
        final_metrics = self.cache_manager.get_metrics()
        
        # Test warmup effectiveness with sample requests
        test_times = []
        for metric in self.test_metrics[:2]:
            for start_date, end_date in self.test_date_ranges[:2]:
                start_req = time.time()
                self.daily_calc.calculate_statistics(metric, start_date, end_date)
                test_times.append((time.time() - start_req) * 1000)
        
        success_rate = sum(warmup_results.values()) / len(warmup_results) if warmup_results else 0
        
        result = PerformanceTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
            total_requests=len(warmup_results),
            cache_hit_rate=final_metrics.overall_hit_rate,
            l1_hit_rate=final_metrics.l1_hit_rate,
            l2_hit_rate=final_metrics.l2_hit_rate,
            l3_hit_rate=final_metrics.l3_hit_rate,
            avg_response_time_ms=statistics.mean(test_times) if test_times else 0,
            p95_response_time_ms=np.percentile(test_times, 95) if test_times else 0,
            p99_response_time_ms=np.percentile(test_times, 99) if test_times else 0,
            min_response_time_ms=min(test_times) if test_times else 0,
            max_response_time_ms=max(test_times) if test_times else 0,
            memory_usage_mb=final_metrics.memory_usage_mb,
            hit_rate_target_met=success_rate >= 0.8,  # 80% warmup success
            performance_target_met=(end_time - start_time).total_seconds() <= 30,  # <30s warmup
            memory_target_met=final_metrics.memory_usage_mb <= self.memory_limit_mb
        )
        
        logger.info(f"Cache warmup test completed: {success_rate:.2%} success rate in {result.duration_seconds:.1f}s")
        return result
    
    def run_tier_performance_test(self) -> Dict[str, PerformanceTestResult]:
        """Test performance of individual cache tiers."""
        results = {}
        
        # Test each tier individually
        for tier in ['l1', 'l2', 'l3']:
            test_name = f"tier_{tier}_performance"
            start_time = datetime.now()
            
            # Clear all caches
            self.cache_manager.clear_all()
            self.cache_manager.metrics = CacheMetrics()
            
            response_times = []
            
            # Pre-populate the specific tier
            metric = self.test_metrics[0]
            start_date, end_date = self.test_date_ranges[0]
            
            # First request to populate
            self.daily_calc.calculate_statistics(metric, start_date, end_date)
            
            # Multiple requests to test tier performance
            for _ in range(10):
                start_req = time.time()
                result = self.cache_manager.get(
                    key=f"daily_stats|{metric}|{start_date}|{end_date}|none",
                    compute_fn=lambda: self.daily_calc.calculator.calculate_statistics(metric, start_date, end_date),
                    cache_tiers=[tier]
                )
                response_times.append((time.time() - start_req) * 1000)
            
            end_time = datetime.now()
            final_metrics = self.cache_manager.get_metrics()
            
            # Determine performance target based on tier
            if tier == 'l1':
                target_ms = self.l1_response_target_ms
            elif tier == 'l2':
                target_ms = self.l2_response_target_ms
            else:
                target_ms = self.l3_response_target_ms
            
            result = PerformanceTestResult(
                test_name=test_name,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                total_requests=len(response_times),
                cache_hit_rate=final_metrics.overall_hit_rate,
                l1_hit_rate=final_metrics.l1_hit_rate,
                l2_hit_rate=final_metrics.l2_hit_rate,
                l3_hit_rate=final_metrics.l3_hit_rate,
                avg_response_time_ms=statistics.mean(response_times),
                p95_response_time_ms=np.percentile(response_times, 95),
                p99_response_time_ms=np.percentile(response_times, 99),
                min_response_time_ms=min(response_times),
                max_response_time_ms=max(response_times),
                memory_usage_mb=final_metrics.memory_usage_mb,
                hit_rate_target_met=final_metrics.overall_hit_rate >= 0.8,
                performance_target_met=statistics.mean(response_times) <= target_ms,
                memory_target_met=final_metrics.memory_usage_mb <= self.memory_limit_mb
            )
            
            results[tier] = result
            logger.info(f"Tier {tier} test: {result.avg_response_time_ms:.2f}ms avg response time")
        
        return results
    
    def _execute_request(self, req_type: str, *args) -> Any:
        """Execute a test request."""
        try:
            if req_type == 'daily_stats':
                return self.daily_calc.calculate_statistics(*args)
            elif req_type == 'weekly_rolling':
                return self.weekly_calc.calculate_rolling_stats(*args)
            elif req_type == 'monthly_stats':
                return self.monthly_calc.calculate_monthly_stats(*args)
            else:
                raise ValueError(f"Unknown request type: {req_type}")
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            return None
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite and generate report."""
        logger.info("Starting comprehensive cache performance test suite")
        
        suite_start = datetime.now()
        results = {}
        
        try:
            # Basic functionality test
            results['basic_cache'] = self.run_basic_cache_test()
            
            # Tier performance tests
            results['tier_performance'] = self.run_tier_performance_test()
            
            # Cache warmup test
            results['cache_warmup'] = self.run_cache_warmup_test()
            
            # Load tests with different user counts
            for users in [5, 10, 20]:
                results[f'load_test_{users}_users'] = self.run_load_test(concurrent_users=users, duration_seconds=30)
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            results['error'] = str(e)
        
        suite_end = datetime.now()
        
        # Generate summary
        summary = self._generate_test_summary(results, suite_start, suite_end)
        results['summary'] = summary
        
        logger.info(f"Test suite completed in {(suite_end - suite_start).total_seconds():.1f}s")
        return results
    
    def _generate_test_summary(self, results: Dict[str, Any], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate test summary report."""
        summary = {
            'test_start': start_time.isoformat(),
            'test_end': end_time.isoformat(),
            'total_duration_seconds': (end_time - start_time).total_seconds(),
            'tests_run': len([k for k in results.keys() if k != 'summary']),
            'overall_success': True,
            'criteria_met': {
                'hit_rate_target': False,
                'performance_target': False,
                'memory_target': False
            },
            'recommendations': []
        }
        
        # Analyze results
        hit_rates = []
        performance_met = []
        memory_met = []
        
        for test_name, result in results.items():
            if isinstance(result, PerformanceTestResult):
                hit_rates.append(result.cache_hit_rate)
                performance_met.append(result.performance_target_met)
                memory_met.append(result.memory_target_met)
            elif isinstance(result, dict) and 'tier_performance' in test_name:
                for tier_result in result.values():
                    if isinstance(tier_result, PerformanceTestResult):
                        hit_rates.append(tier_result.cache_hit_rate)
                        performance_met.append(tier_result.performance_target_met)
                        memory_met.append(tier_result.memory_target_met)
        
        # Overall criteria
        if hit_rates:
            avg_hit_rate = statistics.mean(hit_rates)
            summary['average_hit_rate'] = avg_hit_rate
            summary['criteria_met']['hit_rate_target'] = avg_hit_rate >= self.hit_rate_target
        
        if performance_met:
            summary['criteria_met']['performance_target'] = all(performance_met)
        
        if memory_met:
            summary['criteria_met']['memory_target'] = all(memory_met)
        
        summary['overall_success'] = all(summary['criteria_met'].values())
        
        # Generate recommendations
        if not summary['criteria_met']['hit_rate_target']:
            summary['recommendations'].append("Consider increasing cache TTL values or implementing more aggressive preloading")
        
        if not summary['criteria_met']['performance_target']:
            summary['recommendations'].append("Optimize cache key generation and consider reducing cache tier lookup overhead")
        
        if not summary['criteria_met']['memory_target']:
            summary['recommendations'].append("Reduce L1 cache size limits or implement more aggressive eviction policies")
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save test results to JSON file."""
        try:
            # Convert results to serializable format
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, PerformanceTestResult):
                    serializable_results[key] = value.to_dict()
                elif isinstance(value, dict):
                    nested_results = {}
                    for nested_key, nested_value in value.items():
                        if isinstance(nested_value, PerformanceTestResult):
                            nested_results[nested_key] = nested_value.to_dict()
                        else:
                            nested_results[nested_key] = nested_value
                    serializable_results[key] = nested_results
                else:
                    serializable_results[key] = value
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            logger.info(f"Test results saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")


# Convenience function for running tests
def run_cache_performance_tests(output_dir: str = "./test_results/") -> Dict[str, Any]:
    """Run comprehensive cache performance tests."""
    tester = CachePerformanceTester()
    results = tester.run_comprehensive_test_suite()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"cache_performance_{timestamp}.json"
    tester.save_results(results, str(output_path))
    
    return results