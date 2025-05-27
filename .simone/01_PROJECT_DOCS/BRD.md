# Business Requirements Document (BRD)
## Apple Health Monitor Dashboard

### 1. Executive Summary
The Apple Health Monitor Dashboard project aims to create a Windows executable application that provides non-technical users with an intuitive, visually appealing interface to analyze their Apple Health data. The application will process pre-exported CSV data and present insights through interactive dashboards with customizable date ranges and metrics.

### 2. Business Objectives
- **Primary Goal:** Enable users to gain meaningful insights from their Apple Health data without technical expertise
- **Secondary Goals:**
  - Provide trend analysis across different time periods (daily, weekly, monthly)
  - Allow users to document personal context through journal entries
  - Create an inviting, warm user experience that encourages regular engagement

### 3. Stakeholders
- **Primary Users:** Health-conscious individuals with Apple devices who want to understand their health trends
- **Technical Requirements:** Windows OS users with access to Apple Health CSV exports
- **Skill Level:** Non-technical users with basic computer literacy

### 4. Functional Requirements

#### 4.1 Data Processing
- Import and process CSV files containing Apple Health data
- Handle large datasets efficiently
- Support data validation and error handling

#### 4.2 Configuration Tab
- Date range selection using "creationDate" field
- Multi-criteria filtering by:
  - sourceName (device/app that recorded the data)
  - type (health metric category)
- Save and load filter configurations

#### 4.3 Dashboard Tabs
- **Daily Metrics Dashboard**
  - Display average, min, max for each metric
  - Compare to weekly and monthly averages
  - Visual timeline representation
  
- **Weekly Metrics Dashboard**  
  - Display weekly aggregated statistics
  - Compare to monthly trends
  - Week-over-week comparisons
  
- **Monthly Metrics Dashboard**
  - Display monthly aggregated statistics
  - Month-over-month trend analysis
  - Year-to-date summaries

#### 4.4 Adaptive Display Logic
- If data range < 1 week: Show daily statistics only
- If data range < 1 month: Show daily and weekly statistics
- If data range ≥ 1 month: Show all three dashboard types

#### 4.5 Journal Feature
- Add text notes to specific dates, weeks, or months
- Save journal entries persistently
- Display journal entries alongside relevant metrics
- Search and filter journal entries

### 5. Non-Functional Requirements

#### 5.1 User Interface
- **Visual Theme:** Warm, inviting color scheme
  - Tan/beige background
  - Orange and yellow accent colors
  - Brown text for readability
- **Design Principles:**
  - Clear, intuitive navigation
  - Large, readable fonts
  - Simple, uncluttered layouts
  - Helpful tooltips and guides

#### 5.2 Performance
- Load CSV files up to 500MB within 30 seconds
- Responsive UI with <200ms interaction feedback
- Smooth chart animations and transitions

#### 5.3 Usability
- Single executable file, no installation required
- Automatic data persistence between sessions
- Export capabilities for charts and reports
- Built-in help documentation

### 6. Technical Constraints
- **Platform:** Windows 10/11 compatible executable
- **Development:** Python-based solution
- **Distribution:** Single portable executable
- **Dependencies:** All dependencies bundled within executable

### 7. Success Criteria
- Users can load and visualize their health data within 5 minutes of first use
- 90% of users can navigate all features without external help
- Application maintains performance with 2+ years of health data
- Positive user feedback on visual design and ease of use

### 8. Future Considerations
- Cross-platform support (macOS, Linux)
- Direct Apple Health API integration
- Advanced analytics and predictions
- Social sharing capabilities
- Mobile companion app