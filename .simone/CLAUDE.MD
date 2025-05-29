# Apple Health Monitor Dashboard - Claude Guide

## Project Overview
Building a Windows desktop application to analyze Apple Health data from XML exports. The app features a warm, inviting UI with dashboards for daily, weekly, and monthly health metrics plus journaling functionality.

### Git Configuration
Commit with the following author info:
```bash
git config user.name "Alex Filiakov"
git config user.email "alexfiliakov@gmail.com"
```

## Key Technical Decisions
- **UI Framework:** PyQt6 for rich desktop experience
- **Data Processing:** Pandas with hybrid memory/streaming approach
- **Database:** SQLite for journal entries and cached metrics
- **Packaging:** PyInstaller → Windows executable with NSIS installer
- **Charts:** Matplotlib with custom warm color themes

## Current Sprint: S01_M01_Project_Setup
Focus on establishing project foundation, PyQt6 skeleton app, and development environment.

## Project Structure
```
Apple Health Exports/
├── src/                           # Application source code
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # Entry point (PyQt6 app)
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Data models
│   ├── data_access.py            # Data access layer
│   ├── data_loader.py            # Data import and processing
│   ├── database.py               # Database operations
│   ├── health_database.py        # Health-specific database operations
│   ├── xml_streaming_processor.py # XML processing with streaming
│   ├── filter_config_manager.py  # Filter configuration management
│   ├── data_filter_engine.py     # Data filtering engine
│   ├── data_availability_service.py # Data availability tracking
│   ├── statistics_calculator.py  # Statistical calculations
│   ├── predictive_analytics.py   # Predictive analytics engine
│   ├── version.py                # Version information
│   ├── analytics/                # Analytics modules
│   │   ├── __init__.py
│   │   ├── advanced_trend_engine.py      # Advanced trend analysis
│   │   ├── anomaly_detection_system.py   # Anomaly detection system
│   │   ├── cache_manager.py              # Cache management
│   │   ├── comparative_analytics.py      # Comparative analytics
│   │   ├── computation_queue.py          # Computation queue management
│   │   ├── connection_pool.py            # Database connection pool
│   │   ├── correlation_analyzer.py       # Correlation analysis
│   │   ├── daily_metrics_calculator.py   # Daily metrics calculations
│   │   ├── data_story_generator.py       # Data story generation
│   │   ├── goal_management_system.py     # Goal management
│   │   ├── health_insights_engine.py     # Health insights engine
│   │   ├── monthly_metrics_calculator.py # Monthly metrics
│   │   ├── optimized_analytics_engine.py # Optimized analytics
│   │   ├── performance_monitor.py        # Performance monitoring
│   │   ├── progressive_loader.py         # Progressive data loading
│   │   ├── streaming_data_loader.py      # Streaming data loader
│   │   ├── week_over_week_trends.py      # Weekly trend analysis
│   │   ├── weekly_metrics_calculator.py  # Weekly metrics
│   │   └── health_score/                 # Health scoring system
│   │       ├── __init__.py
│   │       ├── health_score_calculator.py
│   │       ├── health_score_models.py
│   │       └── personalization_engine.py
│   ├── ui/                        # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py                # Main application window
│   │   ├── component_factory.py          # Component factory
│   │   ├── configuration_tab.py          # Configuration interface
│   │   ├── adaptive_configuration_tab.py # Adaptive configuration
│   │   ├── statistics_widget.py          # Statistics display
│   │   ├── bar_chart_component.py        # Bar chart component
│   │   ├── comparative_visualization.py  # Comparative visualizations
│   │   ├── data_story_widget.py          # Data story display
│   │   ├── goal_progress_widget.py       # Goal progress display
│   │   ├── health_insights_widget.py     # Health insights display
│   │   ├── import_progress_dialog.py     # Import progress dialog
│   │   ├── monthly_dashboard_widget.py   # Monthly dashboard
│   │   ├── preference_tracker.py         # User preference tracking
│   │   ├── progressive_ui_integration.py # Progressive UI loading
│   │   ├── settings_manager.py           # Settings management
│   │   ├── summary_cards.py              # Summary card display
│   │   ├── table_components.py           # Table components
│   │   └── charts/                       # Chart components
│   │       ├── __init__.py
│   │       ├── base_chart.py             # Base chart class
│   │       ├── line_chart.py             # Line chart component
│   │       ├── enhanced_line_chart.py    # Enhanced line charts
│   │       ├── calendar_heatmap.py       # Calendar heatmap
│   │       ├── matplotlib_chart_factory.py # Matplotlib charts
│   │       ├── pyqtgraph_chart_factory.py # PyQtGraph charts
│   │       ├── shareable_dashboard.py    # Shareable dashboards
│   │       ├── wsj_health_visualization_suite.py # WSJ-style visualizations
│   │       └── wsj_style_manager.py      # WSJ style management
│   └── utils/                     # Utility modules
│       ├── __init__.py
│       ├── error_handler.py              # Error handling decorators and utilities
│       ├── logging_config.py             # Centralized logging configuration
│       └── xml_validator.py              # XML validation utilities
├── tests/                         # Test suites
│   ├── __init__.py
│   ├── conftest.py                       # Test configuration
│   ├── unit/                             # Unit tests
│   │   ├── __init__.py
│   │   └── test_*.py                     # Individual unit test files
│   ├── integration/                      # Integration tests
│   │   └── test_*.py                     # Integration test files
│   ├── ui/                               # UI tests
│   │   └── test_*.py                     # UI test files
│   ├── performance/                      # Performance tests
│   │   ├── __init__.py
│   │   ├── benchmark_base.py
│   │   └── test_*.py                     # Performance test files
│   ├── visual/                           # Visual regression tests
│   │   ├── baseline_manager.py
│   │   └── visual_test_base.py
│   ├── fixtures/                         # Test fixtures
│   │   ├── __init__.py
│   │   └── health_fixtures.py
│   └── generators/                       # Test data generators
│       ├── __init__.py
│       └── health_data.py
├── docs/                          # Documentation
│   ├── api/                              # API documentation
│   ├── architecture/                     # Architecture documentation
│   ├── development/                      # Development documentation
│   ├── user/                             # User documentation
│   └── *.md                              # Various documentation files
├── coverage_analysis/             # Test coverage analysis
│   └── *.py                              # Coverage analysis tools
├── tools/                         # Development tools
│   └── *.py                              # Development utilities
├── examples/                      # Usage examples
│   └── *.py                              # Example scripts
├── assets/                        # Icons, themes, fonts
│   ├── README.md
│   └── characters/                       # Character assets
├── logs/                          # Application logs (gitignored)
├── data/                          # User data (gitignored)
├── specs/                         # Project specifications
├── pyproject.toml                 # Project configuration
├── pytest.ini                    # Pytest configuration
├── requirements*.txt              # Python dependencies
└── venv/                          # Virtual environment (gitignored)
```

## Development Setup
```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application (during development)
python src/main.py

# Run tests
pytest

# Build executable (future)
pyinstaller build_config.spec

# Create installer (future)
makensis installer.nsi
```

## Design Guidelines
- **Colors:** Warm palette - tan (#F5E6D3), orange (#FF8C42), yellow (#FFD166)
- **Typography:** Clear, readable fonts for non-technical users
- **UX:** Progressive disclosure, clear feedback, keyboard navigation

## Sprint Sequence (M01)
1. **S01**: Project setup & architecture
2. **S02**: CSV data processing pipeline
3. **S03**: UI framework with tabs
4. **S04**: Analytics engine (daily/weekly/monthly)
5. **S05**: Data visualization & charts
6. **S06**: Journal feature
7. **S07**: Windows packaging & distribution

## Key Files to Reference
- Requirements: `.simone/02_REQUIREMENTS/M01/`
- UI Specs: `.simone/02_REQUIREMENTS/M01/SPECS_UI.md`
- Architecture Decisions: `.simone/05_ARCHITECTURAL_DECISIONS/`

## Testing Approach
- Unit tests for data processing logic
- Integration tests for CSV → UI pipeline
- UI tests with pytest-qt
- Manual testing on Windows 10/11 before release