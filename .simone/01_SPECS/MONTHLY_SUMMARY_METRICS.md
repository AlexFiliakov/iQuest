# Monthly Summary Metrics - Specification and Caching Strategy

## Overview

This document outlines the current monthly metrics that are cached in the database, identifies potential additional metrics for caching, and provides SQL queries for metric aggregation.

## Current Database Schema

### Health Records Table
```sql
CREATE TABLE IF NOT EXISTS health_records (
    type TEXT,                  -- Health metric type (e.g., "StepCount", "HeartRate")
    sourceName TEXT,           -- Data source (e.g., "iPhone", "Apple Watch")
    sourceVersion TEXT,        -- Source version info
    device TEXT,               -- Device identifier
    unit TEXT,                 -- Unit of measurement (e.g., "count", "bpm")
    creationDate TEXT,         -- When the record was created
    startDate TEXT,            -- Start datetime of the measurement
    endDate TEXT,              -- End datetime of the measurement
    value REAL,                -- Actual measurement value
    UNIQUE(type, sourceName, startDate, endDate, value)
);
```

### Cached Metrics Table
```sql
CREATE TABLE IF NOT EXISTS cached_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,     -- Unique cache identifier
    metric_type VARCHAR(50) NOT NULL,           -- Health metric type
    date_range_start DATE NOT NULL,             -- Start date of aggregation
    date_range_end DATE NOT NULL,               -- End date of aggregation
    source_name VARCHAR(100),                   -- Optional source filter
    health_type VARCHAR(100),                   -- Health record type
    aggregation_type VARCHAR(20) NOT NULL,      -- "daily", "weekly", "monthly"
    metric_data TEXT NOT NULL,                  -- Serialized metric data (JSON)
    unit VARCHAR(20),                           -- Unit of measurement
    record_count INTEGER,                       -- Number of records aggregated
    min_value REAL,                             -- Minimum value in period
    max_value REAL,                             -- Maximum value in period
    avg_value REAL,                             -- Average value in period
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL              -- Cache expiration time
);
```

## Current Monthly Metrics Being Cached

### 1. Core Monthly Statistics (`CachedMonthlyMetricsCalculator.calculate_monthly_stats`)
- **Cache Key Pattern**: `monthly_stats|{metric}|{year}|{month}`
- **Cache Tiers**: L1 (memory), L2 (SQLite), L3 (disk)
- **TTL**: 7200 seconds (2 hours)
- **Computed Data**:
  - Average value for the month
  - Median value for the month
  - Standard deviation
  - Minimum and maximum values
  - Record count
  - Month boundaries (start/end dates)
  - Growth rate (optional)
  - Distribution statistics (optional)

### 2. Year-over-Year Comparisons (`CachedMonthlyMetricsCalculator.compare_year_over_year`)
- **Cache Key Pattern**: `monthly_yoy|{metric}|{month}|{target_year}|{years_back}`
- **Cache Tiers**: L2 (SQLite), L3 (disk)
- **TTL**: 14400 seconds (4 hours)
- **Computed Data**:
  - Current month average
  - Previous year average
  - Percent change
  - Absolute change
  - Number of days compared
  - Statistical significance indicator

### 3. Growth Rate Analysis (`CachedMonthlyMetricsCalculator.calculate_growth_rate`)
- **Cache Key Pattern**: `monthly_growth|{metric}|{periods}|{end_year}|{end_month}`
- **Cache Tiers**: L2 (SQLite), L3 (disk)
- **TTL**: 21600 seconds (6 hours)
- **Computed Data**:
  - Monthly growth rate
  - Annualized growth rate
  - Number of periods analyzed
  - Confidence intervals
  - R-squared value
  - Statistical significance

### 4. Distribution Analysis (`CachedMonthlyMetricsCalculator.analyze_distribution`)
- **Cache Key Pattern**: `monthly_distribution|{metric}|{year}|{month}`
- **Cache Tiers**: L1 (memory), L2 (SQLite)
- **TTL**: 7200 seconds (2 hours)
- **Computed Data**:
  - Skewness
  - Kurtosis
  - Normality p-value
  - Normal distribution indicator
  - Jarque-Bera statistics

### 5. Monthly Summary (`CachedMonthlyMetricsCalculator.get_monthly_summary`)
- **Cache Key Pattern**: `monthly_summary|{metrics}|{year}|{month}`
- **Cache Tiers**: L1 (memory), L2 (SQLite), L3 (disk)
- **TTL**: 7200 seconds (2 hours)
- **Computed Data**:
  - Multi-metric summary statistics
  - Aggregated health score indicators
  - Goal progress metrics

### 6. Multi-Month Parallel Processing (`CachedMonthlyMetricsCalculator.calculate_multiple_months_parallel`)
- **Cache Key Pattern**: `monthly_multi|{metrics}|{year_month_pairs}`
- **Cache Tiers**: L3 (disk) - Large datasets
- **TTL**: 7200 seconds (2 hours)
- **Computed Data**:
  - Batch-processed monthly statistics
  - Optimized for dashboard loading

## Potential Additional Metrics for Caching

### 1. Daily Aggregations within Months
```sql
-- Cache Key Pattern: monthly_daily_agg|{metric}|{year}|{month}|{aggregation_method}
```
- **Purpose**: Store daily averages, sums, min/max for each day in a month
- **Benefits**: Faster calendar heatmap rendering
- **Data**: Daily values for calendar visualization

### 2. Weekly Summaries within Months
```sql
-- Cache Key Pattern: monthly_weekly_summary|{metric}|{year}|{month}
```
- **Purpose**: Week-over-week trends within monthly context
- **Benefits**: Improved weekly trend analysis
- **Data**: Weekly averages and week-over-week changes

### 3. Monthly Percentiles and Quantiles
```sql
-- Cache Key Pattern: monthly_percentiles|{metric}|{year}|{month}|{percentiles}
```
- **Purpose**: Store percentile distributions for monthly data
- **Benefits**: Faster outlier detection and ranking
- **Data**: 10th, 25th, 50th, 75th, 90th percentiles

### 4. Monthly Streak and Consistency Metrics
```sql
-- Cache Key Pattern: monthly_consistency|{metric}|{year}|{month}
```
- **Purpose**: Track measurement consistency and streaks
- **Benefits**: Better user engagement metrics
- **Data**: Days with data, longest streak, consistency score

### 5. Monthly Goal Progress
```sql
-- Cache Key Pattern: monthly_goals|{metric}|{year}|{month}|{goal_value}
```
- **Purpose**: Track progress towards monthly goals
- **Benefits**: Real-time goal tracking
- **Data**: Goal completion percentage, days to goal, trajectory

### 6. Monthly Correlation Matrix
```sql
-- Cache Key Pattern: monthly_correlations|{metrics}|{year}|{month}
```
- **Purpose**: Inter-metric correlations for the month
- **Benefits**: Faster health insights and pattern detection
- **Data**: Correlation coefficients between metrics

### 7. Monthly Data Quality Metrics
```sql
-- Cache Key Pattern: monthly_quality|{metric}|{year}|{month}
```
- **Purpose**: Data completeness and quality indicators
- **Benefits**: Better data reliability insights
- **Data**: Missing days, data gaps, source reliability

## SQL Queries for Metric Aggregation

### 1. Basic Monthly Statistics
```sql
-- Calculate basic monthly statistics for a specific metric
SELECT 
    type,
    sourceName,
    COUNT(*) as record_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    ROUND(
        (SELECT value FROM (
            SELECT value, ROW_NUMBER() OVER (ORDER BY value) as rn,
                   COUNT(*) OVER () as cnt
            FROM health_records 
            WHERE type = :metric_type 
              AND DATE(startDate) >= :month_start 
              AND DATE(startDate) <= :month_end
        ) WHERE rn = (cnt + 1) / 2), 2
    ) as median_value,
    unit,
    MIN(DATE(startDate)) as first_record_date,
    MAX(DATE(startDate)) as last_record_date
FROM health_records 
WHERE type = :metric_type 
  AND DATE(startDate) >= :month_start 
  AND DATE(startDate) <= :month_end
GROUP BY type, sourceName, unit
ORDER BY record_count DESC;
```

### 2. Daily Aggregations within Month
```sql
-- Get daily aggregated values for calendar heatmap
SELECT 
    DATE(startDate) as record_date,
    type,
    sourceName,
    COUNT(*) as daily_count,
    AVG(value) as daily_avg,
    SUM(value) as daily_sum,
    MIN(value) as daily_min,
    MAX(value) as daily_max,
    unit
FROM health_records 
WHERE type = :metric_type 
  AND DATE(startDate) >= :month_start 
  AND DATE(startDate) <= :month_end
  AND (:source_name IS NULL OR sourceName = :source_name)
GROUP BY DATE(startDate), type, sourceName, unit
ORDER BY record_date;
```

### 3. Weekly Summaries within Month
```sql
-- Calculate weekly summaries within a month
WITH weekly_data AS (
    SELECT 
        type,
        sourceName,
        strftime('%W', startDate) as week_number,
        DATE(startDate, 'weekday 0', '-6 days') as week_start,
        COUNT(*) as weekly_count,
        AVG(value) as weekly_avg,
        SUM(value) as weekly_sum,
        MIN(value) as weekly_min,
        MAX(value) as weekly_max,
        unit
    FROM health_records 
    WHERE type = :metric_type 
      AND DATE(startDate) >= :month_start 
      AND DATE(startDate) <= :month_end
    GROUP BY type, sourceName, strftime('%W', startDate), unit
)
SELECT 
    *,
    LAG(weekly_avg) OVER (PARTITION BY type, sourceName ORDER BY week_start) as prev_week_avg,
    CASE 
        WHEN LAG(weekly_avg) OVER (PARTITION BY type, sourceName ORDER BY week_start) IS NOT NULL 
        THEN ROUND(
            ((weekly_avg - LAG(weekly_avg) OVER (PARTITION BY type, sourceName ORDER BY week_start)) 
             / LAG(weekly_avg) OVER (PARTITION BY type, sourceName ORDER BY week_start)) * 100, 2
        )
        ELSE NULL 
    END as week_over_week_change_pct
FROM weekly_data
ORDER BY week_start;
```

### 4. Monthly Percentiles
```sql
-- Calculate percentiles for monthly data
WITH ordered_values AS (
    SELECT 
        type,
        sourceName,
        value,
        unit,
        ROW_NUMBER() OVER (PARTITION BY type, sourceName ORDER BY value) as rn,
        COUNT(*) OVER (PARTITION BY type, sourceName) as total_count
    FROM health_records 
    WHERE type = :metric_type 
      AND DATE(startDate) >= :month_start 
      AND DATE(startDate) <= :month_end
)
SELECT 
    type,
    sourceName,
    unit,
    total_count,
    MAX(CASE WHEN rn <= total_count * 0.1 THEN value END) as p10,
    MAX(CASE WHEN rn <= total_count * 0.25 THEN value END) as p25,
    MAX(CASE WHEN rn <= total_count * 0.5 THEN value END) as p50_median,
    MAX(CASE WHEN rn <= total_count * 0.75 THEN value END) as p75,
    MAX(CASE WHEN rn <= total_count * 0.9 THEN value END) as p90
FROM ordered_values
GROUP BY type, sourceName, unit, total_count;
```

### 5. Monthly Data Quality Assessment
```sql
-- Assess data quality and completeness for the month
WITH date_series AS (
    SELECT DATE(:month_start, '+' || (seq - 1) || ' days') as date
    FROM (
        SELECT ROW_NUMBER() OVER () as seq 
        FROM health_records 
        LIMIT (julianday(:month_end) - julianday(:month_start) + 1)
    )
    WHERE date <= :month_end
),
daily_data AS (
    SELECT 
        DATE(startDate) as record_date,
        type,
        sourceName,
        COUNT(*) as record_count,
        COUNT(DISTINCT device) as device_count,
        MIN(value) as min_val,
        MAX(value) as max_val,
        AVG(value) as avg_val
    FROM health_records 
    WHERE type = :metric_type 
      AND DATE(startDate) >= :month_start 
      AND DATE(startDate) <= :month_end
    GROUP BY DATE(startDate), type, sourceName
)
SELECT 
    :metric_type as metric_type,
    COUNT(DISTINCT ds.date) as total_days_in_month,
    COUNT(DISTINCT dd.record_date) as days_with_data,
    ROUND(
        (COUNT(DISTINCT dd.record_date) * 100.0 / COUNT(DISTINCT ds.date)), 2
    ) as data_completeness_pct,
    COALESCE(SUM(dd.record_count), 0) as total_records,
    COUNT(DISTINCT dd.sourceName) as unique_sources,
    AVG(dd.device_count) as avg_devices_per_day,
    MIN(dd.record_date) as first_data_date,
    MAX(dd.record_date) as last_data_date
FROM date_series ds
LEFT JOIN daily_data dd ON ds.date = dd.record_date;
```

### 6. Year-over-Year Monthly Comparison
```sql
-- Compare current month with same month in previous year(s)
WITH current_month AS (
    SELECT 
        type,
        sourceName,
        COUNT(*) as current_count,
        AVG(value) as current_avg,
        MIN(value) as current_min,
        MAX(value) as current_max,
        unit
    FROM health_records 
    WHERE type = :metric_type 
      AND DATE(startDate) >= :current_month_start 
      AND DATE(startDate) <= :current_month_end
    GROUP BY type, sourceName, unit
),
previous_year AS (
    SELECT 
        type,
        sourceName,
        COUNT(*) as prev_count,
        AVG(value) as prev_avg,
        MIN(value) as prev_min,
        MAX(value) as prev_max,
        unit
    FROM health_records 
    WHERE type = :metric_type 
      AND DATE(startDate) >= :prev_year_month_start 
      AND DATE(startDate) <= :prev_year_month_end
    GROUP BY type, sourceName, unit
)
SELECT 
    COALESCE(cm.type, py.type) as type,
    COALESCE(cm.sourceName, py.sourceName) as sourceName,
    COALESCE(cm.unit, py.unit) as unit,
    COALESCE(cm.current_count, 0) as current_count,
    COALESCE(cm.current_avg, 0) as current_avg,
    COALESCE(py.prev_count, 0) as prev_count,
    COALESCE(py.prev_avg, 0) as prev_avg,
    CASE 
        WHEN py.prev_avg > 0 THEN 
            ROUND(((cm.current_avg - py.prev_avg) / py.prev_avg) * 100, 2)
        ELSE NULL 
    END as yoy_change_pct,
    ROUND(cm.current_avg - py.prev_avg, 2) as yoy_change_absolute
FROM current_month cm
FULL OUTER JOIN previous_year py ON cm.type = py.type 
    AND cm.sourceName = py.sourceName 
    AND cm.unit = py.unit;
```

### 7. Multi-Metric Monthly Summary
```sql
-- Get summary statistics for multiple metrics in one query
SELECT 
    type,
    sourceName,
    unit,
    COUNT(*) as record_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(DISTINCT DATE(startDate)) as days_with_data,
    MIN(DATE(startDate)) as first_record_date,
    MAX(DATE(startDate)) as last_record_date,
    -- Calculate coefficient of variation (CV)
    CASE 
        WHEN AVG(value) > 0 THEN 
            ROUND((
                SQRT(SUM((value - (SELECT AVG(value) FROM health_records hr2 
                    WHERE hr2.type = hr1.type 
                      AND hr2.sourceName = hr1.sourceName
                      AND DATE(hr2.startDate) >= :month_start 
                      AND DATE(hr2.startDate) <= :month_end)) * 
                (value - (SELECT AVG(value) FROM health_records hr3 
                    WHERE hr3.type = hr1.type 
                      AND hr3.sourceName = hr1.sourceName
                      AND DATE(hr3.startDate) >= :month_start 
                      AND DATE(hr3.startDate) <= :month_end))) / COUNT(*))
                / AVG(value)
            ) * 100, 2)
        ELSE NULL 
    END as coefficient_of_variation
FROM health_records hr1
WHERE type IN (:metric_types)  -- List of metrics: 'StepCount', 'HeartRate', etc.
  AND DATE(startDate) >= :month_start 
  AND DATE(startDate) <= :month_end
GROUP BY type, sourceName, unit
ORDER BY type, record_count DESC;
```

## Cache Implementation Strategy

### Cache Key Patterns
```
monthly_stats|{metric}|{year}|{month}
monthly_daily_agg|{metric}|{year}|{month}|{aggregation}
monthly_weekly_summary|{metric}|{year}|{month}
monthly_percentiles|{metric}|{year}|{month}
monthly_consistency|{metric}|{year}|{month}
monthly_goals|{metric}|{year}|{month}|{goal}
monthly_correlations|{metrics_hash}|{year}|{month}
monthly_quality|{metric}|{year}|{month}
monthly_yoy|{metric}|{month}|{target_year}|{years_back}
monthly_growth|{metric}|{periods}|{end_year}|{end_month}
```

### Cache Tier Strategy
- **L1 (Memory)**: Frequently accessed monthly stats, recent months
- **L2 (SQLite)**: All monthly summaries, percentiles, quality metrics
- **L3 (Disk)**: Historical data, large multi-metric datasets, growth analysis

### Cache TTL Configuration
- **Monthly Stats**: 2 hours (7200 seconds)
- **YoY Comparisons**: 4 hours (14400 seconds)
- **Growth Rates**: 6 hours (21600 seconds)
- **Data Quality**: 1 hour (3600 seconds)
- **Daily Aggregations**: 30 minutes (1800 seconds)

### Cache Dependencies
```
metric:{metric_name}
month:{year}:{month}
date_range:{start_date}:{end_date}
source:{source_name}
goal:{goal_value}
```

### Cache Warming Query
```sql
-- Identify months that need cache population
SELECT DISTINCT 
    type,
    strftime('%Y', startDate) as year,
    strftime('%m', startDate) as month,
    COUNT(*) as record_count
FROM health_records 
WHERE DATE(startDate) >= DATE('now', '-12 months')
GROUP BY type, strftime('%Y', startDate), strftime('%m', startDate)
HAVING record_count > 0
ORDER BY year DESC, month DESC, type;
```

This specification provides a comprehensive foundation for implementing robust monthly metrics caching that will eliminate the warning and improve dashboard performance.