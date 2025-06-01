# Apple Health Monitor Dashboard - Claude Development Reference

This document provides comprehensive information about the Apple Health Monitor Dashboard codebase for Claude AI assistant development and maintenance.

## 🏗️ Project Overview

The Apple Health Monitor Dashboard is a sophisticated PyQt6-based desktop application for analyzing and visualizing Apple Health data. The application features a modular architecture with comprehensive Google-style docstrings throughout the codebase.

### Key Technologies
- **Python 3.10+**: Core programming language
- **PyQt6**: Modern desktop UI framework
- **SQLite**: Local database for health data and app state
- **Pandas**: Data processing and analysis
- **Matplotlib**: Chart generation and visualization
- **Sphinx**: Documentation generation with Google docstring support

## 📊 Current Codebase Statistics

- **Total Python Files**: ~183 modules across all packages
- **Core Modules**: 16 files in `/src/`
- **Analytics Package**: 38+ specialized analysis modules
- **UI Package**: 85+ interface and visualization components
- **Utils Package**: 3 utility modules with comprehensive error handling
- **Test Suite**: Comprehensive testing with unit, integration, and performance tests

## 🎯 Architecture Overview

The application follows a clean architecture pattern with clear separation of concerns:

```
src/
├── 🎯 Core Layer (16 modules)
│   ├── main.py                    # Application entry point
│   ├── config.py                  # Configuration constants
│   ├── models.py                  # Data models (7 dataclasses)
│   ├── database.py                # Database management
│   ├── data_loader.py             # Data import/export
│   └── ...
├── 📊 Analytics Layer (38+ modules)
│   ├── daily_metrics_calculator.py
│   ├── monthly_metrics_calculator.py
│   ├── cache_manager.py
│   ├── anomaly_detection.py
│   ├── health_score/             # Health scoring subsystem
│   └── ...
├── 🎨 UI Layer (85+ modules)
│   ├── main_window.py
│   ├── configuration_tab.py
│   ├── charts/                   # Visualization components
│   ├── dashboards/               # Dashboard management
│   ├── accessibility/            # Accessibility features
│   └── ...
└── 🛠️ Utils Layer (3 modules)
    ├── error_handler.py           # Comprehensive error handling
    ├── logging_config.py          # Centralized logging
    └── xml_validator.py           # XML validation
```

## 📝 Documentation Standards

### Google-Style Docstrings Implementation

**ALL modules in this codebase now feature comprehensive Google-style docstrings** with:

- **Module-level docstrings**: Comprehensive descriptions with examples and feature lists
- **Class docstrings**: Detailed Attributes sections and usage examples
- **Method/Function docstrings**: Complete Args, Returns, Raises, and Examples sections
- **Consistent formatting**: Following Google docstring conventions exactly

### Example Documentation Pattern

```python
def calculate_daily_statistics(self, 
                             metric: str, 
                             date: date,
                             aggregation_method: str = 'mean') -> Optional[MetricStatistics]:
    """Calculate comprehensive daily statistics for a specific health metric.
    
    Computes statistical measures for a single day's health data including
    central tendencies, variability measures, and distribution characteristics.
    
    Args:
        metric (str): The health metric to analyze (e.g., 'steps', 'heart_rate').
        date (date): The specific date to calculate statistics for.
        aggregation_method (str): Statistical method to use ('mean', 'median', 'sum').
            Defaults to 'mean'.
    
    Returns:
        Optional[MetricStatistics]: Statistical results object containing mean,
            median, standard deviation, min/max values, and record count.
            Returns None if no data exists for the specified date.
    
    Raises:
        ValueError: If metric name is invalid or date is in the future.
        DatabaseError: If database query fails.
    
    Example:
        >>> calculator = DailyMetricsCalculator(data_access)
        >>> stats = calculator.calculate_daily_statistics('steps', date(2024, 1, 15))
        >>> print(f"Average steps: {stats.mean:.0f}")
        Average steps: 8542
    """
```

## 🗂️ Key Module Categories

### Core Infrastructure
- **database.py**: Thread-safe SQLite operations with singleton pattern
- **data_loader.py**: XML/CSV import with validation and streaming processing
- **models.py**: 7 dataclasses for database entities (JournalEntry, UserPreference, etc.)
- **data_access.py**: DAO pattern implementation for data persistence

### Analytics Engine
- **daily_metrics_calculator.py**: Daily health metric analysis with outlier detection
- **monthly_metrics_calculator.py**: Monthly aggregations with YoY comparisons
- **cache_manager.py**: High-performance caching with LRU and SQLite backends
- **anomaly_detection.py**: Statistical anomaly detection algorithms
- **health_score/**: Comprehensive health scoring system (5 modules)

### User Interface
- **main_window.py**: Main application window with tab-based navigation
- **configuration_tab.py**: Data import and filtering interface
- **charts/**: Chart components with WSJ-inspired styling (20+ modules)
- **dashboards/**: Responsive dashboard layouts and customization
- **accessibility/**: WCAG-compliant accessibility features

### Utilities
- **error_handler.py**: Custom exception hierarchy and error decorators
- **logging_config.py**: Structured logging with rotation and multiple handlers
- **xml_validator.py**: Apple Health XML validation with detailed reporting

## 🧪 Testing Infrastructure

Comprehensive test suite with:
- **Unit Tests**: 60+ test modules in `tests/unit/`
- **Integration Tests**: 8 integration test modules
- **Performance Tests**: Benchmarking and memory profiling
- **Visual Regression Tests**: Automated UI testing with baseline comparison
- **Coverage Analysis**: Automated coverage monitoring and gap analysis

## 📊 Database Schema

The application uses SQLite with the following key tables:
- **health_records**: Primary health data storage
- **journal_entries**: Daily/weekly/monthly journal entries
- **user_preferences**: Application settings and user preferences
- **cached_metrics**: Performance optimization cache
- **import_history**: Data import tracking

## 🔧 Development Commands

### Running the Application
```bash
python src/main.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

### Documentation Generation
```bash
# Generate Sphinx documentation
cd docs/
make html

# The documentation will be available in docs/_build/html/
```

### Code Quality
```bash
# Run linting (if configured)
ruff check src/

# Run type checking (if configured)
mypy src/
```

## Taking Screenshots

The project includes a `take_screenshot.py` utility for capturing screenshots in Windows via WSL. This script provides two main functions:

### Primary Monitor Screenshot
To capture only the primary monitor:
```bash
cd "/mnt/c/Users/alexf/OneDrive/Documents/Projects/Apple Health Exports" && python take_screenshot.py
```
This calls the `take_screenshot()` function which captures the primary monitor and saves it to `ad hoc/screenshot_YYYYMMDD_HHMMSS.png`.

### Specific Monitor Screenshot
To capture a specific monitor:
```bash
cd "/mnt/c/Users/alexf/OneDrive/Documents/Projects/Apple Health Exports" && python take_screenshot.py --monitor X
```
This calls the `take_screenshot()` function which captures monitor X and saves it to `ad hoc/screenshot_YYYYMMDD_HHMMSS.png`.

### All Monitors Screenshot
To capture all monitors in a single image:
```bash
cd "/mnt/c/Users/alexf/OneDrive/Documents/Projects/Apple Health Exports" && python take_screenshot.py --all
```
This calls the `take_screenshot_all_monitors()` function which captures the entire virtual screen (all monitors combined) and saves it to `ad hoc/screenshot_all_monitors_YYYYMMDD_HHMMSS.png`.

### Usage Notes
- Screenshots are automatically saved to the `ad hoc/` directory with timestamps
- The script uses PowerShell to capture screenshots in WSL environments
- If a specific path is requested, you can modify the script or copy the file after capture
- The script will display monitor information when capturing all monitors

## 📁 Key Configuration Files

- **pyproject.toml**: Project configuration and dependencies
- **pytest.ini**: Test configuration and coverage settings
- **requirements.txt**: Production dependencies
- **requirements-test.txt**: Testing dependencies
- **docs/conf.py**: Sphinx documentation configuration with Google docstring support

## 🚀 Performance Considerations

- **Caching Strategy**: Multi-level caching with LRU and SQLite backends
- **Database Optimization**: Indexed queries and bulk operations
- **UI Responsiveness**: Background workers for data processing
- **Memory Management**: Lazy loading and data streaming for large datasets

## 🔐 Security Features

- **Local Data Only**: All health data stays on user's machine
- **Input Validation**: Comprehensive XML and data validation
- **Error Handling**: Secure error messages without data leakage
- **Access Control**: File system permissions and validation

## 📈 Analytics Capabilities

The application provides sophisticated health analytics:
- **Temporal Analysis**: Daily, weekly, monthly trend analysis
- **Anomaly Detection**: Statistical outlier identification
- **Correlation Analysis**: Multi-metric relationship discovery
- **Health Scoring**: Comprehensive health assessment system
- **Predictive Analytics**: Trend forecasting and pattern recognition

## 🎨 UI/UX Design

- **WSJ-Inspired Styling**: Professional, clean design with warm color palette
- **Accessibility**: WCAG 2.1 AA compliance with keyboard navigation
- **Responsive Design**: Adaptive layouts for different screen sizes
- **Interactive Charts**: Rich visualizations with drill-down capabilities

## 📝 Maintenance Notes

When working on this codebase:

1. **Maintain Google-style docstrings** for all new code
2. **Follow existing patterns** for error handling and logging
3. **Add tests** for new functionality with appropriate coverage
4. **Update documentation** when adding new features or modules
5. **Use the existing analytics infrastructure** rather than duplicating functionality
6. **Follow the established architecture patterns** and module organization

## 🔗 Important File Locations

- **Main Entry Point**: `src/main.py`
- **Configuration**: `src/config.py`
- **Database Setup**: `src/database.py`
- **Core Models**: `src/models.py`
- **Analytics Hub**: `src/analytics/`
- **UI Components**: `src/ui/`
- **Documentation**: `docs/`
- **Test Suite**: `tests/`

## 📋 Common Development Tasks

### Adding a New Analytics Module
1. Create module in `src/analytics/`
2. Add comprehensive Google-style docstrings
3. Implement caching if performance-critical
4. Add unit tests in `tests/unit/`
5. Update `docs/api/analytics.rst`

### Adding a New UI Component
1. Create component in appropriate `src/ui/` subdirectory
2. Follow existing styling patterns
3. Implement accessibility features
4. Add to component factory if reusable
5. Add visual regression tests

### Database Schema Changes
1. Update models in `src/models.py`
2. Add migration logic in `src/database.py`
3. Update DAO methods in `src/data_access.py`
4. Add tests for new functionality

This document serves as a comprehensive reference for understanding and working with the Apple Health Monitor Dashboard codebase. All modules feature extensive Google-style documentation for detailed implementation guidance.