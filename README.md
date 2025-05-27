# Apple Health Monitor Dashboard

A Windows desktop application for analyzing and visualizing Apple Health data from various formats. Features a warm, inviting UI with comprehensive health metrics dashboards, journaling functionality, and robust error handling.

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

## Project Structure

```
Apple Health Exports/
├── src/                # Source code
│   ├── utils/         # Utility modules
│   │   ├── error_handler.py    # Error handling decorators and utilities
│   │   └── logging_config.py   # Centralized logging configuration
│   ├── data_loader.py # Data import and processing
│   └── main.py        # Application entry point
├── tests/              # Test suites
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── ui/            # UI tests
├── logs/              # Application logs
│   ├── apple_health_monitor.log        # General application logs
│   └── apple_health_monitor_errors.log # Error-specific logs
├── docs/              # Documentation
├── data/              # Data files (CSV exports, SQLite databases)
├── raw data/          # Raw Apple Health exports (XML, ZIP)
├── processed data/    # Processed data files
├── assets/            # Icons, fonts, themes
└── venv/              # Python virtual environment
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

## License

[License information to be added]