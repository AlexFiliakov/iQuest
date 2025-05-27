# PROJECT MANIFEST

## Project Overview
- **Project Name**: Apple Health Analytics Dashboard
- **Description**: Windows executable dashboard with Python to analyze Apple Health Data
- **Status**: Active
- **Start Date**: 2025-01-27
- **Last Updated**: 2025-05-27 (Logging and error handling framework completed)

## Current State
- **Current Milestone**: M01_MVP
- **Current Sprint**: S01_M01_Initial_EXE
- **Highest Sprint in Milestone**: S04
- **Last General Task ID**: G007
- **Completed General Tasks**: GX001 (Python project structure), GX002 (SQLite data loader), GX003 (Basic UI framework), GX005 (Logging and error handling framework)

## Sprint Summary

### Milestone M01: MVP
- [x] S01_M01_data_processing - Data import and processing pipeline ✓ COMPLETE
  - CSV import with large file support
  - Data model and schema definition
  - Filtering and aggregation engine
  - SQLite storage layer
- [ ] S02_M01_core_ui - Core dashboard UI framework
  - Tab-based navigation structure
  - Configuration tab with filters
  - Warm visual design implementation
  - Reusable UI component library
- [ ] S03_M01_basic_analytics - Basic daily/weekly/monthly summaries
  - Daily analytics with min/max/average
  - Weekly rollups and patterns
  - Monthly aggregations and heatmaps
  - Time-based comparisons
- [ ] S04_M01_health_analytics - Comprehensive health analytics features
  - Core health metrics dashboard (activity, heart, sleep, body)
  - Advanced trend analysis and predictions
  - Health correlations engine
  - Interactive visualizations
  - Health insights and recommendations
  - Export and reporting capabilities

## Recent Updates
- 2025-05-27: Completed GX003 - Created basic UI framework with PyQt6, tab navigation, and warm color theme
- 2025-05-27: Completed GX005 - Implemented logging and error handling framework with exception hooks
- 2025-05-27: Completed GX002 - Implemented SQLite data loader with XML/CSV import and query methods
- 2025-05-27: Completed GX001 - Setup Python project structure with PyQt6 foundation
- 2025-01-27: Created comprehensive sprint plan for M01_MVP milestone
- 2025-01-27: Planned Sprint S04 with detailed Apple Health analytics based on user research

## Technical Stack
- **Language**: Python 3.10+
- **UI Framework**: PyQt6
- **Data Processing**: Pandas 2.0+
- **Packaging**: PyInstaller for Windows executable
- **Charts**: Matplotlib with custom themes
- **Database**: SQLite for journal entries

## Key Features
- CSV data import from Apple Health export
- Date range and source filtering
- Daily/Weekly/Monthly metric summaries
- Journal feature for notes
- Warm, inviting UI design with tan/orange/yellow color scheme