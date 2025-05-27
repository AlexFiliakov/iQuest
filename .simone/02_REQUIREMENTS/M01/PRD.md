# Product Requirements Document (PRD)
## Apple Health Monitor Dashboard - M01

### 1. Product Overview

#### 1.1 Product Vision
Create an intuitive, visually appealing Windows desktop application that transforms complex Apple Health data into actionable insights for everyday users.

#### 1.2 Product Goals
- Simplify health data analysis for non-technical users
- Provide meaningful time-based comparisons and trends
- Enable personal context through journaling
- Deliver a warm, engaging user experience

### 2. User Stories

#### 2.1 Data Import & Configuration
- **As a user**, I want to import my Apple Health CSV file so that I can analyze my health data
- **As a user**, I want to filter data by date range so that I can focus on specific time periods
- **As a user**, I want to filter by device and metric type so that I can analyze specific data sources

#### 2.2 Dashboard Navigation
- **As a user**, I want to switch between daily, weekly, and monthly views so that I can see different perspectives of my data
- **As a user**, I want the app to automatically show relevant timeframes based on my data range
- **As a user**, I want to see comparisons between different time periods to understand trends

#### 2.3 Data Visualization
- **As a user**, I want to see average, minimum, and maximum values for each metric
- **As a user**, I want charts that are easy to understand without statistical knowledge
- **As a user**, I want a warm, inviting interface that makes data exploration enjoyable

#### 2.4 Journaling
- **As a user**, I want to add notes to specific dates to provide context for my health data
- **As a user**, I want to add notes to weekly and monthly summaries for broader reflections
- **As a user**, I want my notes to persist between sessions

### 3. Feature Specifications

#### 3.1 Configuration Tab
**Purpose:** Allow users to customize their data view

**Components:**
- File selector for CSV import
- Date range picker with calendar widgets
- Multi-select dropdown for sourceName (devices/apps)
- Multi-select dropdown for type (health metrics)
- Apply/Reset buttons
- Import progress indicator

**Behavior:**
- Filters apply to all dashboard tabs
- Settings persist between sessions
- Real-time validation of date ranges
- Clear feedback on data loading status

#### 3.2 Daily Metrics Dashboard
**Purpose:** Provide detailed day-by-day health insights

**Components:**
- Date navigation (previous/next day, date picker)
- Metric cards showing:
  - Current day's avg/min/max
  - Weekly average (with up/down indicator)
  - Monthly average (with up/down indicator)
- Time-series chart for selected metric
- Journal entry section for the day

**Visual Design:**
- Card-based layout with soft shadows
- Color-coded indicators (green=improvement, red=decline)
- Smooth animations on data updates

#### 3.3 Weekly Metrics Dashboard
**Purpose:** Show weekly trends and patterns

**Components:**
- Week navigation (previous/next week, week picker)
- Weekly summary cards with:
  - Week's avg/min/max
  - Comparison to previous week
  - Comparison to monthly average
- Bar chart showing daily values within the week
- Weekly journal entry section

**Visual Design:**
- Horizontal bar charts with gradient fills
- Week-over-week trend arrows
- Highlighted current week

#### 3.4 Monthly Metrics Dashboard
**Purpose:** Display long-term trends and patterns

**Components:**
- Month navigation (previous/next month, month/year picker)
- Monthly summary cards with:
  - Month's avg/min/max
  - Comparison to previous month
  - Year-to-date statistics
- Calendar heatmap visualization
- Monthly journal entry section

**Visual Design:**
- Calendar grid with color intensity representing values
- Trend line overlays
- Seasonal pattern indicators

### 4. User Interface Specifications

#### 4.1 Color Palette
- **Primary Background:** #F5E6D3 (Warm tan)
- **Secondary Background:** #FFFFFF (White for cards)
- **Primary Accent:** #FF8C42 (Warm orange)
- **Secondary Accent:** #FFD166 (Soft yellow)
- **Text Primary:** #5D4E37 (Dark brown)
- **Text Secondary:** #8B7355 (Medium brown)

#### 4.2 Typography
- **Headers:** Sans-serif, bold, 18-24px
- **Body Text:** Sans-serif, regular, 14-16px
- **Data Values:** Monospace, 16-20px
- **Captions:** Sans-serif, light, 12px

#### 4.3 Layout Principles
- Consistent 16px grid system
- Generous whitespace (minimum 24px between sections)
- Maximum content width of 1200px
- Responsive scaling for different screen sizes

#### 4.4 Interactive Elements
- Hover effects on all clickable elements
- Smooth transitions (200-300ms)
- Loading skeletons during data fetches
- Tooltips for additional information
- Keyboard navigation support

### 5. Technical Specifications

#### 5.1 Data Structure
```python
# Expected CSV columns
{
    'creationDate': 'datetime',
    'sourceName': 'string',
    'type': 'string',
    'unit': 'string',
    'value': 'float'
}
```

#### 5.2 Performance Requirements
- Initial load time: <5 seconds for UI
- CSV processing: <30 seconds for 100MB file
- Chart rendering: <500ms
- Filter application: <200ms
- Memory usage: <500MB for typical datasets

#### 5.3 Data Persistence
- User preferences stored in local config file
- Journal entries saved in SQLite database
- Recent files list maintained
- Window size and position remembered

### 6. Accessibility Requirements
- High contrast mode support
- Keyboard navigation for all features
- Screen reader compatible labels
- Scalable UI elements
- Color-blind friendly visualizations

### 7. Error Handling
- Clear error messages for invalid CSV format
- Graceful handling of missing data
- Recovery options for corrupted journal entries
- Helpful suggestions for common issues
- Debug log generation for support

### 8. Future Enhancements (Post-M01)
- Export functionality (PDF, PNG, Excel)
- Additional metric types support
- Custom metric calculations
- Data sharing capabilities
- Cloud backup for journal entries
- Multi-language support