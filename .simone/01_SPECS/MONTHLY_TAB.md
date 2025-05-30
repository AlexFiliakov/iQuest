# Monthly Tab Specification

## Overview
The Monthly tab provides a comprehensive calendar-based view of health metrics with advanced statistical analysis, trend detection, and multi-format visualizations. It serves as the primary interface for understanding monthly patterns, seasonal variations, and long-term health trends.

## Current Implementation

### Core Components

#### 1. Monthly Dashboard Widget (`src/ui/monthly_dashboard_widget.py`)
- **Primary Interface**: Orchestrates the Monthly tab experience
- **State Management**: Tracks current month/year for navigation
- **Data Integration**: Connects with MonthlyMetricsCalculator for analytics

#### 2. Calendar Heatmap (`src/ui/charts/calendar_heatmap.py`)
- **Primary Visualization**: Color-coded calendar grid showing daily values
- **Style Options**: Classic calendar vs GitHub-style contribution graph
- **Color Schemes**: Customizable palettes with accessibility support
- **Interactive Features**: Hover tooltips with detailed daily information

#### 3. Navigation Controls
- **Month Navigation**: Previous/Next buttons with keyboard shortcuts
- **Today Button**: Quick return to current month
- **Future Prevention**: Blocks navigation beyond current date
- **Date Display**: Shows current month/year in header

#### 4. Metric Selection System
- **Comprehensive Coverage**: 60+ Apple Health metrics supported
- **Source Filtering**: Option to view data from specific devices
- **Aggregation Options**: "All Sources" or device-specific views
- **Smart Defaults**: Automatically selects StepCount on first load

### Data Analysis Features

#### 1. Monthly Metrics Calculator (`src/analytics/monthly_metrics_calculator.py`)
- **Statistical Analysis**:
  - Basic statistics (mean, median, std dev, min, max)
  - Distribution analysis (skewness, kurtosis, normality)
  - Year-over-year comparisons
  - Compound growth rate calculations
- **Performance Features**:
  - LRU caching for repeated queries
  - Parallel processing for batch operations
  - Lazy loading for large datasets
- **Advanced Analytics**:
  - Seasonal decomposition (trend, seasonal, residual)
  - Statistical significance testing
  - Confidence interval calculation

#### 2. Summary Statistics Cards
- **Average**: Mean value for the month with smart formatting
- **Total**: Sum of all daily values (when applicable)
- **Best Day**: Maximum daily value with date
- **Trend**: Direction indicator with percentage change

#### 3. Month-over-Month Analysis (`src/analytics/month_over_month_trends.py`)
- **Trend Detection**:
  - Change point identification
  - Momentum scoring
  - Seasonal pattern recognition
- **Forecasting**: Future projections with confidence intervals
- **Milestone Tracking**: Records, streaks, improvements
- **Natural Language Insights**: Generated narratives about trends

### Visualization Options

#### 1. Calendar Heatmap (Primary View)
- **Grid Layout**: 7 columns (days) × 4-6 rows (weeks)
- **Color Intensity**: Values mapped to color gradient
- **Day Labels**: Abbreviated weekday names
- **Week Numbers**: Optional week-of-year display

#### 2. Month-over-Month Widget (`src/ui/month_over_month_widget.py`)
- **Multiple Chart Types**:
  - Waterfall chart: Cumulative monthly changes
  - Bump chart: Performance rankings over time
  - Stream graph: Composition analysis
  - Small multiples: Multiple analytical views
- **Time Period Selection**: 6-36 month analysis windows
- **Background Processing**: Non-blocking analysis with progress tracking

### User Interactions

#### 1. Navigation Flow
- Click Previous/Next to change months
- Click Today to return to current month
- Use keyboard shortcuts (← → Space)
- Month changes trigger automatic data refresh

#### 2. Metric Selection Flow
- Open dropdown to see available metrics
- Optional: Filter by data source
- Selection triggers immediate visualization update
- Summary cards refresh with new data

#### 3. Style Toggle
- Switch between Classic and GitHub styles
- Preference saved for future sessions
- Immediate visual update on toggle

### Data Flow

1. **Initial Load**:
   ```
   MonthlyDashboardWidget → MonthlyMetricsCalculator → Database
                          ↓
                    Calendar Heatmap ← Processed Data
   ```

2. **Metric Change**:
   ```
   Metric Dropdown → Update Request → Calculator
                                    ↓
   Summary Cards ← Statistics ← Calendar Update
   ```

3. **Month Navigation**:
   ```
   Navigation Button → Date Change → Data Query
                                   ↓
   UI Update ← New Month Data ← Validation
   ```

## Key Features

### 1. Multi-Source Support
- Aggregates data from multiple Apple devices
- Device-specific filtering (e.g., "Steps - Apple Watch")
- Intelligent source detection and labeling

### 2. Statistical Rigor
- Significance testing for comparisons
- Confidence intervals for estimates
- Distribution normality assessment
- Outlier detection and handling

### 3. Performance Optimization
- Caching at multiple levels
- Lazy loading for large datasets
- Background processing for complex analyses
- Efficient database queries with indexing

### 4. Accessibility
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode options
- Clear visual indicators

## Planned Enhancements

### 1. Journal Integration
- Monthly reflection prompts
- Goal setting and tracking
- Achievement celebrations
- Progress narratives

### 2. Advanced Analytics
- Machine learning predictions
- Anomaly explanations
- Correlation discovery
- Personalized insights

### 3. Export Capabilities
- Monthly reports (PDF/HTML)
- Data export (CSV/JSON)
- Chart image export
- Shareable summaries

### 4. Customization
- Custom date ranges
- Metric combinations
- Threshold settings
- Alert configurations

## Technical Specifications

### Dependencies
- PyQt6 for UI framework
- Pandas for data processing
- NumPy for numerical operations
- SciPy for statistical analysis
- Matplotlib for chart rendering

### Performance Targets
- Initial load: < 500ms
- Month navigation: < 200ms
- Metric switch: < 300ms
- Chart render: < 100ms

### Data Limits
- Maximum 5 years historical data
- Up to 100,000 data points per metric
- 60+ metric types supported
- Multiple source aggregation

## User Experience Goals

1. **Intuitive Navigation**: Clear month-based browsing
2. **Visual Impact**: Immediate pattern recognition
3. **Statistical Depth**: Professional-grade analysis
4. **Performance**: Responsive interactions
5. **Flexibility**: Multiple view and analysis options

## Integration Points

- **Database Layer**: Direct queries through DataAccess
- **Cache System**: Shared cache with other tabs
- **Settings Manager**: User preferences persistence
- **Analytics Engine**: Reusable calculation components
- **Export System**: Unified export functionality

## File Structure
```
src/
├── ui/
│   ├── monthly_dashboard_widget.py      # Main tab widget
│   ├── monthly_dashboard_widget_modern.py # Modern variant
│   ├── monthly_context_widget.py        # Context insights
│   └── month_over_month_widget.py       # Trend analysis
├── analytics/
│   ├── monthly_metrics_calculator.py    # Core calculations
│   ├── monthly_context_provider.py      # Contextual analysis
│   └── month_over_month_trends.py       # Trend detection
└── ui/charts/
    └── calendar_heatmap.py              # Calendar visualization
```