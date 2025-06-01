#!/usr/bin/env python3
"""
Demo script to test cache monitoring functionality.
This script shows cache health diagnostics.
"""

import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

from analytics.cache_manager import get_cache_diagnostics, get_cache_manager

def main():
    """Demo cache monitoring."""
    print("=== Cache Health Diagnostics Demo ===\n")
    
    # Initialize cache manager
    cache_manager = get_cache_manager()
    print("✓ Cache manager initialized\n")
    
    # Get cache diagnostics
    diagnostics = get_cache_diagnostics()
    
    if not diagnostics:
        print("❌ No cache diagnostics available")
        return
    
    # Print cache health status
    status = diagnostics.get('health_status', 'unknown')
    status_icon = {
        'excellent': '🟢',
        'good': '🟡', 
        'fair': '🟠',
        'poor': '🔴'
    }.get(status, '❓')
    
    print(f"{status_icon} Cache Health: {status.upper()}\n")
    
    # Print hit rates
    hit_rates = diagnostics.get('hit_rates', {})
    print("📊 Cache Hit Rates:")
    for tier, rate in hit_rates.items():
        percentage = rate * 100
        print(f"  {tier.upper()}: {percentage:.1f}%")
    print()
    
    # Print cache sizes
    sizes = diagnostics.get('cache_sizes', {})
    print("💾 Cache Sizes:")
    for key, value in sizes.items():
        if 'memory' in key:
            print(f"  {key}: {value} MB")
        else:
            print(f"  {key}: {value} entries")
    print()
    
    # Print request counts
    requests = diagnostics.get('request_counts', {})
    print("📈 Request Statistics:")
    total = requests.get('total_requests', 0)
    print(f"  Total requests: {total}")
    
    if total > 0:
        for tier in ['l1', 'l2', 'l3']:
            hits = requests.get(f'{tier}_hits', 0)
            misses = requests.get(f'{tier}_misses', 0)
            if hits + misses > 0:
                print(f"  {tier.upper()}: {hits} hits, {misses} misses")
    
    print("\n✅ Cache monitoring demo complete!")

if __name__ == "__main__":
    main()