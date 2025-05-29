#!/usr/bin/env python3
"""Estimate coverage improvement from new tests."""

import os
import json

def count_test_lines():
    """Count lines in test files."""
    test_dir = "tests/unit"
    new_tests = [
        "test_calendar_heatmap.py",
        "test_optimized_analytics_engine.py", 
        "test_summary_cards_improved.py",
        "test_error_handler_comprehensive.py",
        "test_data_loading_comprehensive.py",
        "test_anomaly_detection_comprehensive.py",
        "test_goal_management_comprehensive.py",
        "test_data_story_generator_comprehensive.py",
        "test_health_score_comprehensive.py",
        "test_comparative_analytics_comprehensive.py",
        "test_correlation_analyzer_comprehensive.py",
        "test_causality_detector_comprehensive.py",
        "test_ensemble_and_feedback_comprehensive.py"
    ]
    
    total_lines = 0
    for test_file in new_tests:
        path = os.path.join(test_dir, test_file)
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = len(f.readlines())
                total_lines += lines
                print(f"{test_file}: {lines} lines")
    
    print(f"\nTotal new test lines: {total_lines}")
    return total_lines

def estimate_coverage_improvement():
    """Estimate coverage improvement."""
    # Load current coverage data
    coverage_file = "coverage_analysis/current_coverage.json"
    
    with open(coverage_file, 'r') as f:
        data = json.load(f)
    
    # Modules we created tests for
    tested_modules = [
        "src/ui/charts/calendar_heatmap.py",
        "src/analytics/optimized_analytics_engine.py",
        "src/ui/summary_cards.py",
        "src/utils/error_handler.py",
        "src/data_loader.py",
        "src/analytics/anomaly_detection.py",
        "src/analytics/anomaly_detection_system.py",
        "src/analytics/anomaly_detectors.py",
        "src/analytics/goal_management_system.py",
        "src/analytics/goal_models.py",
        "src/analytics/data_story_generator.py",
        "src/analytics/health_score/health_score_calculator.py",
        "src/analytics/health_score/component_calculators.py",
        "src/analytics/comparative_analytics.py",
        "src/analytics/comparison_overlay_calculator.py",
        "src/analytics/correlation_analyzer.py",
        "src/analytics/causality_detector.py",
        "src/analytics/ensemble_detector.py",
        "src/analytics/feedback_processor.py"
    ]
    
    # Calculate potential coverage improvement
    files = data.get('files', {})
    
    improvement_lines = 0
    for module in tested_modules:
        if module in files:
            file_data = files[module]
            summary = file_data.get('summary', {})
            missing_lines = summary.get('missing_lines', 0)
            percent_covered = summary.get('percent_covered', 0)
            
            # Estimate 80% of missing lines will be covered by new tests
            estimated_covered = int(missing_lines * 0.8)
            improvement_lines += estimated_covered
            
            print(f"{module}: ~{estimated_covered} lines covered (was {percent_covered:.1f}%)")
    
    # Calculate new overall coverage
    total_lines = sum(f.get('summary', {}).get('num_statements', 0) 
                     for f in files.values() if f.get('summary'))
    current_covered = sum(f.get('summary', {}).get('num_statements', 0) - 
                         f.get('summary', {}).get('missing_lines', 0)
                         for f in files.values() if f.get('summary'))
    
    new_covered = current_covered + improvement_lines
    old_coverage = (current_covered / total_lines * 100) if total_lines > 0 else 0
    new_coverage = (new_covered / total_lines * 100) if total_lines > 0 else 0
    
    print(f"\n=== Coverage Estimate ===")
    print(f"Current coverage: {old_coverage:.1f}%")
    print(f"Estimated new coverage: {new_coverage:.1f}%")
    print(f"Improvement: +{new_coverage - old_coverage:.1f}%")
    print(f"Lines covered: +{improvement_lines}")
    
    if new_coverage >= 90:
        print("\n✅ Estimated to achieve 90% coverage goal!")
    else:
        print(f"\n❌ Still need ~{int((total_lines * 0.9) - new_covered)} more lines covered")

if __name__ == "__main__":
    print("=== New Test Files ===")
    count_test_lines()
    print("\n=== Coverage Improvement Estimate ===")
    estimate_coverage_improvement()