# Apple Health Monitor Dashboard Architecture

This document outlines the high-level architecture of the Apple Health Monitor Dashboard application.

## System Overview

A Windows desktop application built with Python that analyzes Apple Health CSV exports and presents health metrics through an intuitive, warm-themed dashboard interface. The application processes health data using Pandas and displays it via PyQt6 with multiple visualization tabs.

## Technical Architecture

### Core Technology Stack

- **Language**: Python 3.10+
- **UI Framework**: PyQt6 for rich desktop interface
- **Data Processing**: Pandas 2.0+ for efficient CSV handling
- **Visualization**: Matplotlib with custom warm color themes
- **Database**: SQLite for journal entries and preferences
- **Packaging**: PyInstaller for Windows executable creation

### Project Structure

```
Apple Health Exports/
├── src/                    # Application source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Application entry point
│   ├── ui/                # UI components and layouts
│   ├── data/              # Data processing modules
│   ├── analytics/         # Analytics and calculations
│   └── utils/             # Utility functions
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── ui/                # UI tests with pytest-qt
├── assets/                 # Static resources
│   ├── icons/             # Application icons
│   ├── themes/            # Color themes and styles
│   └── fonts/             # Custom fonts
├── data/                   # User data directory
├── docs/                   # Documentation
└── venv/                   # Python virtual environment
```

### Backend Architecture

- **Data Layer**: 
  - CSV parser for Apple Health exports
  - Pandas DataFrames for in-memory processing
  - SQLite for persistent journal storage
  - Hybrid approach: streaming for large files, memory for performance

- **Business Logic**:
  - Analytics engine for daily/weekly/monthly calculations
  - Metric aggregation and statistical analysis
  - Date range filtering and data validation

- **Testing**: 
  - pytest for unit and integration testing
  - pytest-qt for UI component testing
  - Coverage targets: >80% for core logic

### Frontend Architecture

- **UI Framework**: PyQt6 with custom styling
- **Design System**:
  - Warm color palette: tan (#F5E6D3), orange (#FF8C42), yellow (#FFD166)
  - Tab-based navigation (Daily, Weekly, Monthly views)
  - Responsive layouts with proper spacing
  
- **Components**:
  - Main window with tab container
  - Dashboard views for different time periods
  - Chart widgets using Matplotlib
  - Journal entry forms
  - Settings dialog

## System Components

1. **CSV Processor**: Handles Apple Health export parsing and validation
2. **Data Analyzer**: Calculates metrics and aggregations for different time periods
3. **Visualization Engine**: Generates interactive charts and graphs
4. **Journal Manager**: CRUD operations for markdown-based journal entries
5. **Settings Manager**: User preferences and application configuration
6. **Export Module**: Data export functionality to various formats

## Data Flow

1. **Application Launch**: User opens the Windows executable
2. **Data Import**: User imports Apple Health CSV export file
   - CSV is parsed and validated
   - Data is loaded into Pandas DataFrames
   - Duplicate entries are handled (newer data overwrites older)
3. **Data Processing**: 
   - Metrics are calculated for different time periods
   - Aggregations are performed for dashboard views
   - Results are cached for performance
4. **Visualization**: User navigates between Daily/Weekly/Monthly tabs
   - Charts are generated on-demand
   - Interactive features allow drilling into specific metrics
5. **Journaling**: User adds notes and observations
   - Entries are saved to SQLite database
   - Associated with specific dates/periods
6. **Data Persistence**: 
   - All data stored locally (no cloud/remote storage)
   - CSV data can be re-imported to update
   - Journal entries persist between sessions
7. **Export**: User can export analyzed data and reports

## Performance Considerations

- **Load Time**: <30 seconds for 100MB CSV files
- **Memory Usage**: Efficient streaming for large files
- **UI Responsiveness**: <200ms for all user interactions
- **Caching**: Calculated metrics cached to improve performance

## Security & Privacy

- **Local Only**: All data remains on user's machine
- **No Network**: No internet connectivity required or used
- **No Authentication**: Simple local user profiles without passwords
- **Data Isolation**: Each user profile has separate data storage
