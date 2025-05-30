# Apple Health Monitor Dashboard

[![CI](https://github.com/alexf/Apple-Health-Exports/actions/workflows/ci.yml/badge.svg)](https://github.com/alexf/Apple-Health-Exports/actions/workflows/ci.yml)
[![Security](https://github.com/alexf/Apple-Health-Exports/actions/workflows/security.yml/badge.svg)](https://github.com/alexf/Apple-Health-Exports/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/alexf/Apple-Health-Exports/branch/main/graph/badge.svg)](https://codecov.io/gh/alexf/Apple-Health-Exports)
[![CodeQL](https://github.com/alexf/Apple-Health-Exports/workflows/CodeQL/badge.svg)](https://github.com/alexf/Apple-Health-Exports/security/code-scanning)
[![Docker](https://github.com/alexf/Apple-Health-Exports/actions/workflows/docker.yml/badge.svg)](https://github.com/alexf/Apple-Health-Exports/actions/workflows/docker.yml)

![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-025E8C?logo=dependabot)](https://github.com/dependabot)

A powerful Windows desktop application for analyzing and visualizing Apple Health data. Transform your health exports into beautiful, actionable insights with our warm, intuitive interface.

![Dashboard Preview](docs/assets/dashboard-preview.png)

## 🌟 Why Apple Health Monitor?

- **📊 Comprehensive Analytics** - Daily, weekly, and monthly health insights at your fingertips
- **🎨 Beautiful Visualizations** - Modern Wall Street Journal-inspired UI with interactive charts and heatmaps (see [UI Specifications](.simone/01_SPECS/UI_SPECS.md))
- **📝 Personal Journal** - Add context to your health data with integrated journaling
- **🔒 Privacy First** - All data stays local on your machine
- **⚡ Lightning Fast** - Optimized SQLite backend handles millions of data points
- **🪟 Windows Native** - Packaged as a standalone executable, no dependencies needed

## Features

- **Multi-format Support**: Import from CSV files, SQLite databases, or XML exports
- **Multi-view Dashboards**: Daily, weekly, and monthly health metrics visualization
- **Journal Integration**: Add personal notes and observations to your health data
- **Beautiful Charts**: Interactive visualizations with warm color themes
- **Advanced Data Processing**:
  - XML to SQLite conversion for efficient storage
  - CSV to SQLite migration capabilities
  - Date range queries with metric filtering
  - Automated daily, weekly, and monthly aggregations
- **Comprehensive Error Logging**:
  - Centralized logging with rotating file handlers
  - Separate error log files for issue tracking
  - Configurable log levels and structured format
  - Automatic log rotation to manage disk space
- **Robust Error Handling**:
  - Custom exception hierarchy for different error types
  - Detailed error context tracking
  - User-friendly error messages
- **Windows Native**: Packaged as a standalone Windows executable
- **Fast Performance**: Efficient database queries with indexing and bulk imports

## Technology Stack

- **Python 3.10+**: Core programming language
- **PyQt6**: Desktop UI framework
- **Pandas**: Data processing and analysis
- **Matplotlib**: Chart generation
- **SQLite**: Local database for journal entries
- **PyInstaller**: Windows executable packaging

## 📁 Project Structure

The Apple Health Monitor Dashboard is organized into a modular architecture with clear separation of concerns. **All modules feature comprehensive Google-style docstrings** with detailed examples, parameter documentation, and usage guidelines:

```
Apple Health Exports/
├── src/                           # 🎯 Source code
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # 🚀 Application entry point with Google-style docstrings
│   ├── config.py                 # ⚙️ Configuration constants and settings
│   ├── models.py                 # 📊 Data models for database entities
│   ├── data_access.py            # 💾 Data access layer (DAO pattern)
│   ├── data_loader.py            # 📥 Data import and XML/CSV processing
│   ├── database.py               # 🗄️ Database operations and management
│   ├── health_database.py        # 🏥 Health-specific database operations
│   ├── xml_streaming_processor.py # 🔄 XML processing with streaming
│   ├── filter_config_manager.py  # 🔧 Filter configuration management
│   ├── data_filter_engine.py     # 🔍 Data filtering and query engine
│   ├── data_availability_service.py # 📅 Data availability tracking
│   ├── statistics_calculator.py  # 📈 Statistical calculations and analysis
│   ├── predictive_analytics.py   # 🔮 Predictive analytics engine
│   ├── version.py                # 📋 Version information
│   ├── analytics/                # 📊 Advanced Analytics Package (38+ modules)
│   │   ├── __init__.py
│   │   ├── daily_metrics_calculator.py   # 📅 Daily metrics with Google docstrings
│   │   ├── monthly_metrics_calculator.py # 📆 Monthly metrics with comprehensive docs
│   │   ├── weekly_metrics_calculator.py  # 📅 Weekly aggregations and trends
│   │   ├── cache_manager.py              # ⚡ High-performance caching system
│   │   ├── comparative_analytics.py      # 📈 Multi-metric comparison analysis
│   │   ├── anomaly_detection.py          # 🚨 Statistical anomaly detection
│   │   ├── correlation_analyzer.py       # 🔗 Health metric correlation analysis
│   │   ├── advanced_trend_engine.py      # 📈 Machine learning trend analysis
│   │   ├── advanced_trend_models.py      # 🤖 Trend analysis models
│   │   ├── anomaly_detection_system.py   # 🎯 Comprehensive anomaly system
│   │   ├── anomaly_detectors.py          # 🔍 Multiple detection algorithms
│   │   ├── anomaly_models.py             # 📊 Anomaly detection models
│   │   ├── cache_background_refresh.py   # 🔄 Background cache refresh
│   │   ├── cached_calculators.py         # ⚡ Cached calculation engines
│   │   ├── causality_detector.py         # 🔗 Causal relationship detection
│   │   ├── comparison_overlay_calculator.py # 📊 Overlay comparison calculations
│   │   ├── computation_queue.py          # ⚙️ Async computation management
│   │   ├── connection_pool.py            # 🔗 Database connection pool
│   │   ├── correlation_discovery.py      # 🔍 Automated correlation discovery
│   │   ├── correlation_models.py         # 📊 Correlation analysis models
│   │   ├── data_source_protocol.py       # 🔌 Data source abstraction
│   │   ├── data_story_generator.py       # 📖 Narrative health insights
│   │   ├── dataframe_adapter.py          # 🔄 DataFrame integration adapters
│   │   ├── day_of_week_analyzer.py       # 📅 Weekly pattern analysis
│   │   ├── ensemble_detector.py          # 🎯 Ensemble anomaly detection
│   │   ├── evidence_database.py          # 📚 Medical evidence database
│   │   ├── feedback_processor.py         # 💬 User feedback processing
│   │   ├── goal_management_system.py     # 🎯 Health goal tracking
│   │   ├── goal_models.py                # 📊 Goal data models
│   │   ├── goal_notification_integration.py # 🔔 Goal-based notifications
│   │   ├── health_insights_engine.py     # 🧠 AI-powered health insights
│   │   ├── health_insights_models.py     # 🤖 Health insight models
│   │   ├── medical_evidence_validator.py # ⚕️ Medical evidence validation
│   │   ├── month_over_month_trends.py    # 📊 MoM trend analysis
│   │   ├── monthly_context_provider.py   # 📅 Monthly data context
│   │   ├── notification_manager.py       # 🔔 Notification management
│   │   ├── optimized_analytics_engine.py # ⚡ Performance-optimized analytics
│   │   ├── optimized_calculator_integration.py # 🔧 Calculator integration
│   │   ├── peer_group_comparison.py      # 👥 Peer group comparisons
│   │   ├── performance_monitor.py        # 📊 System performance monitoring
│   │   ├── personal_records_tracker.py   # 🏆 Personal achievement tracking
│   │   ├── progressive_loader.py         # 📥 Progressive data loading
│   │   ├── seasonal_pattern_analyzer.py  # 🌱 Seasonal health patterns
│   │   ├── story_delivery_manager.py     # 📖 Health story delivery
│   │   ├── story_templates.py            # 📝 Narrative templates
│   │   ├── streaming_data_loader.py      # 🔄 Real-time data streaming
│   │   ├── temporal_anomaly_detector.py  # ⏰ Time-based anomaly detection
│   │   ├── week_over_week_trends.py      # 📊 WoW trend analysis
│   │   └── health_score/                 # 🏥 Health Scoring System
│   │       ├── __init__.py
│   │       ├── health_score_calculator.py # 🧮 Core health scoring
│   │       ├── health_score_models.py    # 📊 Health score data models
│   │       ├── component_calculators.py  # 🔧 Score component calculators
│   │       ├── personalization_engine.py # 🎯 Personalized health scoring
│   │       └── trend_analyzer.py         # 📈 Health score trend analysis
│   ├── ui/                        # 🎨 User Interface Package (85+ modules)
│   │   ├── __init__.py
│   │   ├── main_window.py                # 🏠 Main application window with Google docs
│   │   ├── configuration_tab.py          # ⚙️ Configuration interface with docs
│   │   ├── component_factory.py          # 🏭 UI component factory
│   │   ├── statistics_widget.py          # 📊 Statistics display widgets
│   │   ├── settings_manager.py           # ⚙️ Settings persistence with docs
│   │   ├── style_manager.py              # 🎨 Design system with docs  
│   │   ├── adaptive_configuration_tab.py # 🔧 Adaptive configuration UI
│   │   ├── bar_chart_component.py        # 📊 Interactive bar charts
│   │   ├── activity_timeline_component.py # ⏰ Activity timeline visualization
│   │   ├── celebration_manager.py        # 🎉 Achievement celebrations
│   │   ├── comparative_visualization.py  # 📈 Multi-metric comparisons
│   │   ├── comparison_overlay_widget.py  # 📊 Comparison overlay displays
│   │   ├── correlation_matrix_widget.py  # 🔗 Correlation matrix visualization
│   │   ├── daily_trend_indicator.py      # 📅 Daily trend indicators
│   │   ├── data_availability_indicator.py # 📅 Data availability displays
│   │   ├── data_story_widget.py          # 📖 Health narrative display
│   │   ├── enhanced_date_edit.py         # 📅 Enhanced date editing
│   │   ├── adaptive_date_edit.py         # 🔧 Adaptive date controls
│   │   ├── goal_progress_widget.py       # 🎯 Goal tracking displays
│   │   ├── health_insights_widget.py     # 🧠 AI insights display
│   │   ├── health_score_visualizations.py # 🏥 Health score visualizations
│   │   ├── import_progress_dialog.py     # 📥 Import progress dialogs
│   │   ├── import_worker.py              # ⚙️ Background import workers
│   │   ├── month_over_month_widget.py    # 📊 MoM comparison widgets
│   │   ├── monthly_context_widget.py     # 📅 Monthly context displays
│   │   ├── monthly_dashboard_widget.py   # 📆 Monthly dashboard
│   │   ├── multi_select_combo.py         # 📋 Multi-selection controls
│   │   ├── adaptive_multi_select_combo.py # 🔧 Adaptive multi-select
│   │   ├── adaptive_time_range_selector.py # ⏰ Smart time range selection
│   │   ├── preference_tracker.py         # 👤 User preference tracking
│   │   ├── summary_cards.py              # 📋 Dashboard summary cards
│   │   ├── table_components.py           # 📊 Data table components
│   │   ├── time_comparison_utils.py      # ⏰ Time comparison utilities
│   │   ├── trend_calculator.py           # 📈 Trend calculation widgets
│   │   ├── trophy_case_widget.py         # 🏆 Achievement displays
│   │   ├── view_transitions.py           # 🔄 Smooth view transitions
│   │   ├── week_over_week_widget.py      # 📊 WoW comparison widgets
│   │   ├── charts/                       # 📊 Chart Components (20+ modules)
│   │   │   ├── __init__.py
│   │   │   ├── base_chart.py             # 📊 Base chart framework with docs
│   │   │   ├── line_chart.py             # 📈 Interactive line charts with docs
│   │   │   ├── enhanced_line_chart.py    # 📈 Advanced line chart features
│   │   │   ├── bump_chart.py             # 📊 Bump chart visualizations
│   │   │   ├── calendar_heatmap.py       # 📅 Calendar heatmap displays
│   │   │   ├── chart_config.py           # ⚙️ Chart configuration system
│   │   │   ├── waterfall_chart.py        # 📊 Waterfall chart component
│   │   │   ├── small_multiples.py        # 📊 Small multiples visualization
│   │   │   ├── stream_graph.py           # 🌊 Stream graph component
│   │   │   ├── wsj_health_visualization_suite.py # 📰 WSJ-style charts
│   │   │   └── wsj_style_manager.py      # 🎨 WSJ design system
│   │   ├── dashboards/                   # 📊 Dashboard Components
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_customization.py # 🎨 Dashboard customization
│   │   │   ├── dashboard_models.py       # 📊 Dashboard data models
│   │   │   ├── responsive_grid_manager.py # 📱 Responsive grid layouts
│   │   │   └── wsj_dashboard_layout.py   # 📰 WSJ-style dashboard layout
│   │   └── accessibility/                # ♿ Accessibility Features
│   │       ├── __init__.py
│   │       ├── accessibility_manager.py  # ♿ Accessibility management
│   │       ├── color_accessibility.py    # 🎨 Color accessibility features
│   │       ├── keyboard_navigation.py    # ⌨️ Keyboard navigation support
│   │       └── screen_reader_support.py  # 🔊 Screen reader integration
│   └── utils/                     # 🛠️ Utility Modules (Comprehensive docs)
│       ├── __init__.py
│       ├── error_handler.py              # 🚨 Error handling with Google docstrings
│       ├── logging_config.py             # 📝 Logging configuration with docs
│       └── xml_validator.py              # ✅ XML validation with comprehensive docs
├── tests/                         # Test suites
│   ├── __init__.py
│   ├── conftest.py                       # Test configuration
│   ├── base_test_classes.py              # Base test classes
│   ├── unit/                             # Unit tests
│   │   ├── __init__.py
│   │   ├── test_*.py                     # Individual unit test files
│   │   └── monthly_metrics_optimization_summary.md
│   ├── integration/                      # Integration tests
│   │   ├── test_comparative_analytics_integration.py
│   │   ├── test_database_integration.py
│   │   ├── test_smart_selection_integration.py
│   │   ├── test_visualization_integration.py
│   │   ├── test_week_over_week_integration.py
│   │   └── test_xml_streaming_integration.py
│   ├── ui/                               # UI tests
│   │   ├── test_bar_chart_component.py
│   │   ├── test_component_factory.py
│   │   ├── test_consolidated_widgets.py
│   │   └── test_summary_cards.py
│   ├── performance/                      # Performance tests
│   │   ├── __init__.py
│   │   ├── adaptive_thresholds.py
│   │   ├── benchmark_base.py
│   │   ├── memory_profiler.py
│   │   ├── performance_dashboard.py
│   │   ├── regression_detector.py
│   │   └── test_*.py                     # Performance test files
│   ├── visual/                           # Visual regression tests
│   │   ├── baseline_manager.py
│   │   ├── image_comparison.py
│   │   ├── qt_config.py
│   │   ├── visual_test_base.py
│   │   ├── baselines/                    # Visual test baselines
│   │   └── failures/                     # Failed visual tests
│   ├── fixtures/                         # Test fixtures
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── factories.py
│   │   └── health_fixtures.py
│   ├── generators/                       # Test data generators
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── edge_cases.py
│   │   ├── health_data.py
│   │   └── time_series.py
│   ├── helpers/                          # Test helpers
│   │   ├── time_helpers.py
│   │   └── transaction_helpers.py
│   └── mocks/                            # Test mocks
│       ├── __init__.py
│       └── data_sources.py
├── docs/                          # Documentation
│   ├── api/                              # API documentation
│   ├── architecture/                     # Architecture documentation
│   │   ├── README.md
│   │   ├── class_diagrams/
│   │   ├── context_diagram.md
│   │   ├── module_overview.md
│   │   └── overview.md
│   ├── development/                      # Development documentation
│   │   └── setup.md
│   ├── user/                             # User documentation
│   │   └── getting-started.md
│   ├── development_workflow.md
│   ├── keyboard_shortcuts_guide.md
│   ├── performance_testing_guide.md
│   ├── test_consolidation_results.md
│   ├── test_data_guide.md
│   ├── testing_guide.md
│   └── tooltip_guidelines.md
├── coverage_analysis/             # Test coverage analysis
│   ├── consolidated_coverage_report/     # HTML coverage reports
│   ├── automated_coverage_monitor.py
│   ├── coverage_gap_analyzer.py
│   └── *.json                            # Coverage data files
├── tools/                         # Development tools
│   ├── analyze_test_coverage.py
│   ├── distribute_comprehensive_tests.py
│   └── migrate_test_data.py
├── examples/                      # Usage examples
│   ├── bar_chart_demo.py
│   ├── journal_example.py
│   ├── table_usage_example.py
│   └── temporal_anomaly_example.py
├── assets/                        # Icons, fonts, themes
│   ├── README.md
│   ├── characters/                       # Character assets
│   └── iQuest Image Descriptions.txt
├── logs/                          # Application logs
│   ├── apple_health_monitor.log          # General application logs
│   └── apple_health_monitor_errors.log   # Error-specific logs
├── data/                          # Data files (CSV exports, SQLite databases)
├── specs/                         # Project specifications
│   └── Apple Health Monitor Project Spec.txt
├── pyproject.toml                 # Project configuration
├── pytest.ini                    # Pytest configuration
├── requirements.txt               # Python dependencies
├── requirements-test.txt          # Test dependencies
├── requirements-ml.txt            # Machine learning dependencies
└── venv/                          # Python virtual environment
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Windows 10/11
- Apple Health data export (CSV, XML, or SQLite format)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd "Apple Health Exports"
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
python src/main.py
```

### Running Tests

```bash
pytest
```

### Building Windows Executable

```bash
pyinstaller build_config.spec
```

## Data Import Options

The application supports multiple data import methods:

1. **CSV Import**: Direct import from Apple Health CSV exports
2. **XML Import**: Convert Apple Health XML exports to SQLite database
3. **SQLite Database**: Load existing SQLite databases for faster access

### Converting XML to SQLite

```python
from src.data_loader import HealthDataLoader

loader = HealthDataLoader()
loader.convert_xml_to_sqlite('export.xml', 'health_data.db')
```

## Error Logging

The application includes comprehensive error logging:

- **Log Files Location**: `logs/` directory in project root
- **General Logs**: `apple_health_monitor.log` - All application events
- **Error Logs**: `apple_health_monitor_errors.log` - Error-specific tracking
- **Log Rotation**: Automatic rotation at 10MB with 5 backup files
- **Log Levels**: Configurable (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Design Philosophy

The application emphasizes:
- **Warm, inviting aesthetics**: Using colors like tan (#F5E6D3), orange (#FF8C42), and yellow (#FFD166)
- **User-friendly interface**: Clear navigation and progressive disclosure
- **Performance**: Fast loading and responsive interactions with database indexing
- **Privacy**: All data stays local on your machine
- **Reliability**: Comprehensive error handling and logging for troubleshooting

## Contributing

This project follows conventional commit standards. Please ensure all tests pass before submitting pull requests.

## 📈 Screenshots

<details>
<summary>View Screenshots</summary>

### Daily View
![Daily Dashboard](docs/assets/daily-view.png)
*Track your daily health metrics with detailed breakdowns*

### Weekly Patterns
![Weekly Analysis](docs/assets/weekly-view.png)
*Discover patterns and trends in your weekly activity*

### Monthly Overview
![Monthly Heatmap](docs/assets/monthly-view.png)
*See the big picture with monthly aggregations and heatmaps*

</details>

## 🚀 Quick Start

### For Users

1. **Download** the latest release from the [Releases](https://github.com/project/releases) page
2. **Export** your Apple Health data from your iPhone
3. **Import** the data into the dashboard
4. **Explore** your health insights!

See the [User Guide](docs/user/getting-started.md) for detailed instructions.

### For Developers

```bash
# Clone the repository
git clone https://github.com/project/apple-health-monitor.git
cd apple-health-monitor

# Set up virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

See the [Development Guide](docs/development/setup.md) for complete setup instructions.

## 📚 Documentation

- [User Guide](docs/user/getting-started.md) - Getting started for end users
- [Development Setup](docs/development/setup.md) - Set up your development environment
- [Architecture Overview](docs/architecture/overview.md) - System design and components
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [API Documentation](docs/api/) - Technical API reference

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code style and standards
- Development workflow
- Testing requirements
- Pull request process

## 🛠️ Built With

- **[Python 3.10+](https://www.python.org/)** - Core programming language
- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** - Modern UI framework
- **[Pandas](https://pandas.pydata.org/)** - Data analysis powerhouse
- **[Matplotlib](https://matplotlib.org/)** - Beautiful visualizations
- **[SQLite](https://www.sqlite.org/)** - Fast, reliable local storage

## 📋 Roadmap

- [x] Core data import and processing
- [x] Daily, weekly, monthly analytics
- [x] Interactive visualizations
- [x] Personal journal integration
- [ ] Export reports (PDF, Excel)
- [ ] Custom analytics plugins
- [ ] Cloud backup support
- [ ] Mobile companion app

See our [Project Board](https://github.com/project/projects/1) for detailed progress.

## 🐛 Known Issues

- Large XML files (>500MB) may take extended time to import
- Some third-party app data may not be fully supported
- See [Issues](https://github.com/project/issues) for complete list

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apple Health team for the comprehensive export format
- PyQt community for excellent documentation
- Our contributors and beta testers

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/project/issues)
- **Discussions**: [GitHub Discussions](https://github.com/project/discussions)
- **Email**: support@example.com

---

<p align="center">
  Made with ❤️ for the health-conscious community
</p>