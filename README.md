# Apple Health Monitor Dashboard

A Windows desktop application for analyzing and visualizing Apple Health data from CSV exports. Features a warm, inviting UI with comprehensive health metrics dashboards and journaling functionality.

## Features

- **Multi-view Dashboards**: Daily, weekly, and monthly health metrics visualization
- **Journal Integration**: Add personal notes and observations to your health data
- **Beautiful Charts**: Interactive visualizations with warm color themes
- **Windows Native**: Packaged as a standalone Windows executable
- **Fast Performance**: Efficient handling of large CSV files (100MB+ in under 30 seconds)

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
├── tests/              # Test suites
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── ui/            # UI tests
├── docs/              # Documentation
├── data/              # Data files (CSV exports)
├── assets/            # Icons, fonts, themes
└── venv/              # Python virtual environment
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Windows 10/11
- Apple Health CSV export file

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

## Design Philosophy

The application emphasizes:
- **Warm, inviting aesthetics**: Using colors like tan (#F5E6D3), orange (#FF8C42), and yellow (#FFD166)
- **User-friendly interface**: Clear navigation and progressive disclosure
- **Performance**: Fast loading and responsive interactions
- **Privacy**: All data stays local on your machine

## Contributing

This project follows conventional commit standards. Please ensure all tests pass before submitting pull requests.

## License

[License information to be added]