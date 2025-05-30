# Insights Tab Specification

## Overview
The Insights tab is the 6th tab in the Apple Health Monitor application, located between the Compare tab and Records tab. It provides personalized, evidence-based health insights and recommendations derived from the user's health data patterns. The tab is labeled "💡 Insights" with the tooltip "View personalized health insights and recommendations".

## Architecture
- **Primary Widget**: `HealthInsightsWidget` (src/ui/health_insights_widget.py)
- **Engine**: `EnhancedHealthInsightsEngine` (src/analytics/health_insights_engine.py)
- **Data Models**: `HealthInsight` objects defined in `src/analytics/health_insights_models.py`
- **Evidence Database**: `EvidenceDatabase` for medical validation
- **Style Management**: `WSJStyleManager` for Wall Street Journal-style presentation

## Core Components

### 1. Header Section
- **Title**: "Health Insights & Recommendations" (20px bold, #333 color)
- **Time Period Selector**: ComboBox with options:
  - Weekly
  - Monthly (default)
  - Quarterly
- **Insights Count Selector**: SpinBox (3-10 insights, default 5)
- **Refresh Button**: Triggers new insight generation

### 2. Progress Indicator
- Progress bar that appears during insight generation
- Shows percentage and descriptive messages
- Hidden when not in use

### 3. Tabbed Content Area
The main content is organized into tabs:

#### All Insights Tab
- Displays all generated insights in a scrollable area
- Insights are shown as expandable cards
- Cards include:
  - Category icon (24x24px)
  - Title (14px bold)
  - Evidence badge indicating quality level
  - Summary text
  - Expandable content with:
    - Detailed description
    - Recommendations
    - Evidence sources
    - "Show more/less" toggle

#### Category-Specific Tabs
Individual tabs for each insight category:
- **Sleep**: Sleep patterns and recommendations
- **Activity**: Physical activity insights
- **Recovery**: Recovery and rest patterns
- **Nutrition**: Nutritional insights (if data available)
- **Body Metrics**: Weight, BMI, body composition trends
- **Heart Health**: Heart rate, blood pressure insights

### 4. Summary Section
- **Insights Summary**: Text area showing overview of findings
- Maximum height of 150px
- Read-only text display

## Insight Card Behavior

### Visual Design
- **Background**: White (#FFFFFF)
- **Border**: 2px solid light gray (#E0E0E0)
- **Hover State**: Orange border (#FF8C42) with 3px width
- **Border Radius**: 8px
- **Padding**: 12px

### Interactive Features
- **Click to Expand**: Cards can be clicked to show additional details
- **Evidence Indicators**: Color-coded badges showing evidence quality:
  - Strong: High-quality medical evidence
  - Moderate: Clinical studies and professional recommendations
  - Weak: Observational studies
  - Pattern-based: User-specific patterns

### Content Structure
Each insight card contains:
- **Category Icon**: Visual indicator of insight type
- **Title**: Clear, actionable headline
- **Summary**: Brief overview of the insight
- **Evidence Badge**: Quality indicator
- **Expandable Content**:
  - Detailed description
  - Specific recommendations
  - Evidence sources and citations
  - Implementation timeframes
  - Achievability ratings

## Data Processing

### Background Generation
- Insights are generated in a separate thread (`InsightGenerationThread`)
- Progress updates are provided during generation
- Maximum of 10 insights can be requested
- Generation uses the selected time period for analysis

### Evidence-Based Analysis
- All insights are backed by medical evidence or user pattern analysis
- Evidence sources include:
  - WHO/CDC guidelines (strong evidence)
  - Clinical studies (moderate evidence)
  - Professional organization recommendations (moderate evidence)
  - User-specific pattern analysis (pattern-based evidence)

### Insight Categories
Six main categories are supported:
1. **Sleep**: Sleep duration, quality, timing patterns
2. **Activity**: Step count, exercise patterns, movement trends
3. **Recovery**: Rest periods, recovery metrics
4. **Nutrition**: Dietary patterns (if nutritional data available)
5. **Body Metrics**: Weight trends, BMI changes, body composition
6. **Heart Health**: Heart rate patterns, blood pressure trends

## Progressive Loading Support
The widget supports progressive loading with callbacks for:
- Loading started
- Skeleton UI ready
- First data available
- Progress updates
- Loading complete
- Error handling

## Error Handling
- Import errors fall back to placeholder content
- Generation errors are logged and progress bar is hidden
- Missing data scenarios are handled gracefully
- Empty categories show "No insights available for this category"

## Integration Points
- **Main Window**: Tab is created in `_create_health_insights_tab()` method
- **Data Manager**: Insights engine receives data manager reference when data is loaded
- **Signal Connections**:
  - `refresh_requested`: Connected to main window refresh handler
  - `insight_selected`: Connected to main window insight selection handler

## Fallback Behavior
If the `HealthInsightsWidget` cannot be imported:
- A placeholder widget is created
- Shows "Health Insights & Recommendations" title (24px, #5D4E37)
- Displays explanatory text: "Personalized health insights based on your data patterns will appear here" (16px, #8B7355)
- Tab still appears with the same icon and tooltip

## Performance Considerations
- Insight generation runs in background thread to prevent UI blocking
- Progressive loading callbacks allow for responsive user experience
- Cards are created dynamically and cleaned up when refreshed
- Scroll areas are optimized for large numbers of insights