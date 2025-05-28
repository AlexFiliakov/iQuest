# Apple Health Monitor Dashboard

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-Active-success.svg)

A powerful Windows desktop application for analyzing and visualizing Apple Health data. Transform your health exports into beautiful, actionable insights with our warm, intuitive interface.

![Dashboard Preview](docs/assets/dashboard-preview.png)

## 🌟 Why Apple Health Monitor?

- **📊 Comprehensive Analytics** - Daily, weekly, and monthly health insights at your fingertips
- **🎨 Beautiful Visualizations** - Warm, inviting UI with interactive charts and heatmaps
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