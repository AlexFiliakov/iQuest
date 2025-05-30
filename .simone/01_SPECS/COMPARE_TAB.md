# Compare Tab Specification

## Overview
The Compare Tab provides comprehensive comparative analytics for health metrics, enabling users to understand their health patterns in context. It offers privacy-first comparisons including personal historical trends and seasonal pattern analysis, designed with encouraging and respectful messaging.

## Core Features

### 1. Tab Navigation
- **Tab Name**: "Compare" 
- **Tooltip**: "Compare your metrics with personal history and seasonal trends"
- **Tab Index**: 4 (fifth tab in the sequence)
- **Keyboard Shortcuts**: Ctrl+5 (Compare tab has no Alt+ shortcut defined)

### 2. Main Navigation
- **Button-based Navigation**: Two primary view options
  - **Personal Progress** (default selected)
  - **Seasonal Trends**
- **Navigation Style**: Checkable buttons with single selection
- **Removed Feature**: Group Comparison (peer group comparisons removed for privacy)

### 3. Personal Progress View
**Default active view showing historical personal comparisons**

#### Metric Selection
- **Metric Selector**: Dropdown with 7 supported metrics:
  - Steps
  - Active Energy 
  - Heart Rate
  - Sleep
  - Exercise Minutes
  - Stand Hours
  - Walking Speed
- **Metric Mapping**: Maps display names to Apple Health identifiers
- **Default Selection**: Steps

#### Comparison Cards (2x2 Grid)
- **7-Day Average**: Rolling 7-day average with trend indicator
- **30-Day Average**: Rolling 30-day average with trend indicator  
- **90-Day Average**: Rolling 90-day average with trend indicator
- **365-Day Average**: Rolling 365-day average with trend indicator

#### Trend Indicators
- **Trend Frame**: Visual container with progress indicator
- **Trend Icon**: Visual indicator for trend direction
- **Trend Label**: Text description of current trend
- **Progress Bar**: 4px height progress indicator for data loading

### 4. Seasonal Trends View
**Shows seasonal patterns and weather-related correlations**

#### Loading State
- **Loading Label**: "Seasonal Trends (caching...)"
- **Progress Bar**: Indeterminate progress during data loading
- **Async Loading**: 2-second simulated loading time

#### Content Display
- **Seasonal Pattern Analysis**: Historical patterns by season
- **Weather Correlations**: Activity correlations with weather data
- **Year-over-Year Comparisons**: Same periods across different years

## Technical Implementation

### Data Flow
1. **Engine**: Uses `ComparativeAnalyticsEngine` for core analytics
2. **Calculators**: Integrates daily, weekly, and monthly calculators
3. **Background Processing**: Leverages background trend processor for calculations
4. **Caching**: Uses cached trend data when available

### UI Components
- **Main Widget**: `ComparativeAnalyticsWidget` 
- **Personal View**: `HistoricalComparisonWidget`
- **Seasonal View**: `SeasonalTrendsWidget`  
- **Comparison Cards**: `ComparisonCard` components
- **Gauges**: `PercentileGauge` for animated visualizations

### Data Processing
- **Historical Analysis**: Rolling averages for 7, 30, 90, and 365 days
- **Trend Detection**: Statistical analysis for improvement/decline/stable trends
- **Privacy Protection**: Local-only comparisons, no external data sharing
- **Metric Validation**: Validates against supported health metric types

### Privacy Features
- **Local Only**: All comparisons use local data only
- **No External Sharing**: No data transmitted to external services
- **Anonymous Processing**: Any future group features use anonymous aggregation
- **Opt-in Design**: All comparison features require explicit user selection

## User Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    Comparative Analytics                    │
├─────────────────────────────────────────────────────────────┤
│  [Personal Progress] [Seasonal Trends]                     │
├─────────────────────────────────────────────────────────────┤
│  Personal Progress                      Metric: [Steps ▼]  │
│                                                             │
│  ┌─────────────────┐ ┌─────────────────┐                  │
│  │   7-Day Average │ │  30-Day Average │                  │
│  │      8,234      │ │      7,856      │                  │
│  │       ↗ 5%      │ │       ↗ 12%     │                  │
│  └─────────────────┘ └─────────────────┘                  │
│                                                             │
│  ┌─────────────────┐ ┌─────────────────┐                  │
│  │  90-Day Average │ │ 365-Day Average │                  │
│  │      7,421      │ │      6,945      │                  │
│  │       → 0%      │ │       ↗ 18%     │                  │
│  └─────────────────┘ └─────────────────┘                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┤
│  │ 📈 Improving trend: +12% over the last 30 days        │
│  │ ▓▓▓▓▓▓▓▓░░░░░░░░░░░░                                    │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

## State Management

### Widget States
- **Loading**: Shows progress indicators during data processing
- **Personal View**: Default active state showing historical comparisons
- **Seasonal View**: Shows seasonal patterns and correlations
- **No Data**: Graceful handling when insufficient data available
- **Placeholder**: Fallback state when ComparativeAnalyticsWidget import fails

### Data Refresh Triggers
- **Tab Activation**: Refreshes when Compare tab becomes active
- **Data Import**: Updates when new health data is imported
- **Metric Selection**: Refreshes when user selects different metrics
- **Engine Updates**: Responds to comparative engine data updates

### Navigation State
- **Single Selection**: Only one navigation button active at a time
- **View Persistence**: Maintains selected view during session
- **Metric Persistence**: Remembers selected metric across view switches

## Error Handling

### Graceful Degradation
- **Missing Data**: Shows appropriate messages for insufficient data
- **Calculation Errors**: Handles edge cases in trend calculations
- **Engine Failures**: Maintains UI functionality with error states
- **Loading Timeouts**: Provides fallback states for long calculations

### User Feedback
- **Loading States**: Clear progress indicators during processing
- **Trend Messages**: Encouraging and informative trend descriptions
- **Error Messages**: Helpful guidance for data issues
- **Cache Status**: Indicators showing when data is being cached

## Performance Considerations

### Optimization Features
- **Background Processing**: Heavy calculations run asynchronously
- **Caching Strategy**: Intelligent caching of trend calculations
- **Lazy Loading**: Components load on demand
- **Progress Indicators**: Non-blocking operations with visual feedback

### Memory Management
- **LRU Caching**: Limited cache size with automatic cleanup
- **Data Cleanup**: Proper disposal of temporary calculations
- **Component Lifecycle**: Efficient widget creation and destruction

## Integration Points

### Comparative Analytics Engine
- **Engine Interface**: `ComparativeAnalyticsEngine` provides core functionality
- **Calculator Integration**: Uses daily, weekly, and monthly calculators
- **Background Processor**: Integrates with background trend processing
- **Cache Management**: Leverages trend caching for performance

### Main Application
- **Tab System**: Integrates with main application tab widget
- **Data Pipeline**: Connects to configuration tab data source
- **Settings**: Respects user privacy and preference settings

### Other Tabs
- **Historical Context**: Provides comparative context for other tab data
- **Cross-tab Navigation**: Enables drill-down to specific time periods
- **Metric Consistency**: Uses same metric definitions across tabs

## Privacy and Security

### Privacy-First Design
- **Local Processing**: All analytics performed locally
- **No External APIs**: No data sent to external comparison services
- **User Control**: Explicit opt-in for any future sharing features
- **Data Minimization**: Only processes necessary data for comparisons

### Security Measures
- **Input Validation**: Validates all metric inputs and calculations
- **Error Boundaries**: Prevents calculation errors from breaking UI
- **Safe Defaults**: Conservative defaults for all privacy settings

## Future Enhancements

### Planned Features
- **Goal Integration**: Comparison with personal health goals
- **Seasonal Intelligence**: Weather-aware seasonal adjustments
- **Export Capabilities**: Export comparison reports and charts
- **Custom Timeframes**: User-defined comparison periods

### Technical Improvements
- **Advanced Visualizations**: Enhanced charts and graphs
- **Machine Learning**: Predictive trend analysis
- **Real-time Updates**: Live updating of trend calculations
- **Performance Optimization**: Further caching and calculation improvements

## Accessibility Features

### Visual Accessibility
- **High Contrast**: Support for high contrast themes
- **Font Scaling**: Respects system font size preferences
- **Color Independence**: Trend information available through multiple channels

### Interaction Accessibility
- **Keyboard Navigation**: Full keyboard accessibility for all controls
- **Screen Reader Support**: Proper ARIA labels for comparison data
- **Focus Management**: Clear focus indicators and logical tab order

## Fallback Behavior

### Placeholder State
When the `ComparativeAnalyticsWidget` import fails, a placeholder widget is shown with:
- **Title**: "Comparative Analytics"
- **Description**: "Compare your health metrics with personal history and seasonal trends"
- **Feature List**: 
  - Personal progress tracking
  - Anonymous demographic comparisons
  - Seasonal trend analysis
- **Styling**: Matches application warm color theme

## Known Limitations

### Current Constraints
- **Metric Support**: Limited to 7 predefined health metrics
- **Timeframe Limits**: Fixed comparison periods (7, 30, 90, 365 days)
- **Visualization Types**: Basic card-based comparison display
- **Real-time Data**: No live streaming data updates

### Removed Features
- **Peer Group Comparisons**: Removed for privacy compliance
- **External Benchmarks**: No external health benchmark comparisons
- **Social Features**: No social sharing or community features