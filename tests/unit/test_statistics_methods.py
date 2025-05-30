#!/usr/bin/env python3
"""
Simple test to verify statistics calculator methods work and improve coverage.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from statistics_calculator import StatisticsCalculator


def test_statistics_methods():
    """Test the new statistical methods."""
    calc = StatisticsCalculator()
    
    # Create test data
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    # Test descriptive stats
    print("Testing descriptive statistics...")
    stats = calc.calculate_descriptive_stats(data)
    print(f"Mean: {stats['mean']}, Std: {stats['std']}")
    assert 'mean' in stats
    assert 'std' in stats
    assert 'median' in stats
    
    # Test correlation matrix
    print("Testing correlation matrix...")
    df = pd.DataFrame({'x': data, 'y': data * 2})
    corr = calc.calculate_correlation_matrix(df)
    print(f"Correlation shape: {corr.shape}")
    assert not corr.empty
    
    # Test distribution analysis
    print("Testing distribution analysis...")
    dist = calc.analyze_distribution(data)
    print(f"Distribution type: {dist['distribution_type']}")
    assert 'distribution_type' in dist
    
    # Test confidence interval
    print("Testing confidence interval...")
    ci = calc.calculate_confidence_interval(data)
    print(f"95% CI: [{ci['lower']:.2f}, {ci['upper']:.2f}]")
    assert 'lower' in ci
    assert 'upper' in ci
    
    # Test bootstrap
    print("Testing bootstrap statistics...")
    bootstrap = calc.bootstrap_statistics(data, n_bootstrap=100)
    print(f"Bootstrap estimate: {bootstrap['estimate']:.2f}")
    assert 'estimate' in bootstrap
    assert 'standard_error' in bootstrap
    
    print("All tests passed!")


if __name__ == "__main__":
    test_statistics_methods()