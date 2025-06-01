#!/usr/bin/env python3
"""Test script to verify cached_metrics table population and retrieval."""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager
from src.analytics.cached_metrics_access import get_cached_metrics_access


def check_cached_metrics_table():
    """Check the contents of the cached_metrics table."""
    print("Checking cached_metrics table...")
    print("-" * 80)
    
    db = DatabaseManager()
    
    # Get total count
    count_query = "SELECT COUNT(*) as count FROM cached_metrics"
    result = db.execute_query(count_query)
    total_count = result[0]['count'] if result else 0
    print(f"Total cached entries: {total_count}")
    
    if total_count == 0:
        print("\nNo entries found in cached_metrics table!")
        print("Please run a data import first to populate the cache.")
        return
    
    # Get summary by metric type
    summary_query = """
        SELECT 
            metric_type,
            aggregation_type,
            COUNT(*) as count,
            MIN(date_range_start) as earliest,
            MAX(date_range_end) as latest
        FROM cached_metrics
        GROUP BY metric_type, aggregation_type
        ORDER BY metric_type, aggregation_type
    """
    
    results = db.execute_query(summary_query)
    print("\nCache Summary by Type:")
    print(f"{'Metric Type':<20} {'Aggregation':<15} {'Count':<10} {'Date Range':<30}")
    print("-" * 75)
    
    for row in results:
        date_range = f"{row['earliest']} to {row['latest']}"
        print(f"{row['metric_type']:<20} {row['aggregation_type']:<15} {row['count']:<10} {date_range:<30}")
    
    # Get unique health types
    health_types_query = """
        SELECT DISTINCT health_type 
        FROM cached_metrics 
        WHERE health_type IS NOT NULL
        ORDER BY health_type
    """
    
    health_types = db.execute_query(health_types_query)
    print(f"\nUnique health types cached: {len(health_types)}")
    if len(health_types) > 0:
        print("Health types:", ", ".join([row['health_type'] for row in health_types[:10]]))
        if len(health_types) > 10:
            print(f"... and {len(health_types) - 10} more")
    
    # Test retrieval using CachedMetricsAccess
    print("\n" + "-" * 80)
    print("Testing CachedMetricsAccess retrieval...")
    
    cached_access = get_cached_metrics_access()
    
    # Get available metrics
    available_metrics = cached_access.get_available_metrics()
    print(f"\nAvailable metrics: {len(available_metrics)}")
    
    if available_metrics:
        # Test with first available metric
        test_metric = available_metrics[0]
        print(f"\nTesting with metric: {test_metric}")
        
        # Try to get today's summary
        today = date.today()
        summary = cached_access.get_daily_summary(test_metric, today)
        if summary:
            print(f"Today's summary found: {summary}")
        else:
            print("No summary found for today")
            
            # Try yesterday
            yesterday = today - timedelta(days=1)
            summary = cached_access.get_daily_summary(test_metric, yesterday)
            if summary:
                print(f"Yesterday's summary found: {summary}")
            else:
                print("No summary found for yesterday")
                
                # Get any recent date with data
                recent_query = """
                    SELECT date_range_start 
                    FROM cached_metrics 
                    WHERE health_type = ? 
                    AND metric_type = 'daily_summary'
                    ORDER BY date_range_start DESC 
                    LIMIT 1
                """
                recent_results = db.execute_query(recent_query, (test_metric,))
                if recent_results:
                    recent_date_str = recent_results[0]['date_range_start']
                    recent_date = datetime.strptime(recent_date_str, '%Y-%m-%d').date()
                    summary = cached_access.get_daily_summary(test_metric, recent_date)
                    if summary:
                        print(f"Summary for {recent_date}: {summary}")
                        
                        # Test conversion to MetricStatistics
                        stats = cached_access.convert_to_metric_statistics(summary)
                        if stats:
                            print(f"\nConverted to MetricStatistics:")
                            print(f"  Mean: {stats.mean}")
                            print(f"  Count: {stats.count}")
                            print(f"  Min: {stats.min}")
                            print(f"  Max: {stats.max}")
    
    # Get cache statistics
    print("\n" + "-" * 80)
    print("Cache Statistics:")
    cache_stats = cached_access.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        check_cached_metrics_table()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()