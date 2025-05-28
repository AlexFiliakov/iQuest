# Development Setup Guide

This guide provides detailed instructions for setting up the Apple Health Monitor Dashboard development environment.

## Table of Contents

- [System Requirements](#system-requirements)
- [Initial Setup](#initial-setup)
- [IDE Configuration](#ide-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Development Tools](#development-tools)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Required Software

- **Python**: 3.10 or higher
- **Git**: Latest version
- **Operating System**: Windows 10/11 (primary), Linux/macOS (development only)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space for development environment

### Recommended Software

- **IDE**: Visual Studio Code or PyCharm
- **Database Browser**: DB Browser for SQLite
- **Git GUI**: GitHub Desktop or SourceTree

## Initial Setup

### 1. Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/YOUR_USERNAME/apple-health-monitor.git

# Or clone via SSH
git clone git@github.com:YOUR_USERNAME/apple-health-monitor.git

cd apple-health-monitor
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
# Check Python version
python --version

# Check PyQt6 installation
python -c "from PyQt6 import QtCore; print(f'PyQt6 version: {QtCore.QT_VERSION_STR}')"

# Check pandas installation
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
```

## IDE Configuration

### Visual Studio Code

1. **Install Python Extension**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Python" by Microsoft
   - Install the extension

2. **Configure Python Interpreter**
   - Open Command Palette (Ctrl+Shift+P)
   - Type "Python: Select Interpreter"
   - Choose the virtual environment: `./venv/Scripts/python.exe`

3. **Recommended Extensions**
   - Python Docstring Generator
   - GitLens
   - Pylance
   - Python Test Explorer

4. **Workspace Settings** (.vscode/settings.json)
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black",
     "python.testing.pytestEnabled": true,
     "python.testing.unittestEnabled": false,
     "editor.formatOnSave": true,
     "editor.rulers": [100]
   }
   ```

### PyCharm

1. **Open Project**
   - File → Open → Select project directory

2. **Configure Interpreter**
   - File → Settings → Project → Python Interpreter
   - Click gear icon → Add
   - Select "Existing environment"
   - Browse to: `venv/Scripts/python.exe`

3. **Enable pytest**
   - File → Settings → Tools → Python Integrated Tools
   - Set Default test runner to "pytest"

## Database Setup

### SQLite Configuration

The application uses SQLite for data storage. No additional setup required, but you can configure the database location:

```python
# In src/config.py
DATABASE_PATH = "data/health_data.db"  # Default location
```

### Sample Data

For development, you can use sample data:

```bash
# Create sample database
python scripts/create_sample_data.py

# Or import test XML file
python -c "from src.data_loader import HealthDataLoader; loader = HealthDataLoader(); loader.convert_xml_to_sqlite('tests/data/sample_export.xml', 'data/test.db')"
```

## Running the Application

### Development Mode

```bash
# Run the main application
python src/main.py

# Run with debug logging
python src/main.py --debug

# Run with specific config
python src/main.py --config dev_config.json
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test module
pytest tests/unit/test_data_loader.py

# Run tests in verbose mode
pytest -v

# Run tests matching pattern
pytest -k "test_import"
```

### Linting and Formatting

```bash
# Run pylint
pylint src/

# Run black formatter
black src/ tests/

# Check code style
flake8 src/ tests/
```

## Development Tools

### Debugging

1. **VS Code Debugging**
   - Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Current File",
         "type": "python",
         "request": "launch",
         "program": "${file}",
         "console": "integratedTerminal"
       },
       {
         "name": "Python: Main Application",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/src/main.py",
         "console": "integratedTerminal"
       }
     ]
   }
   ```

2. **PyCharm Debugging**
   - Right-click `src/main.py` → Debug
   - Set breakpoints by clicking line numbers

### Performance Profiling

```python
# Profile specific functions
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats()
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory_profiler

# Run with memory profiling
python -m memory_profiler src/main.py
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'PyQt6'**
   ```bash
   # Ensure virtual environment is activated
   # Reinstall PyQt6
   pip install --force-reinstall PyQt6
   ```

2. **Qt platform plugin error on Windows**
   ```bash
   # Install required Windows components
   pip install pyqt6-tools
   ```

3. **Database locked error**
   - Close any database browser applications
   - Ensure only one instance of the app is running
   - Check file permissions

4. **Virtual environment not recognized**
   ```bash
   # Windows: Use full path
   C:\path\to\project\venv\Scripts\activate
   
   # Or recreate virtual environment
   rm -rf venv  # or manually delete venv folder
   python -m venv venv
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```python
# In src/utils/logging_config.py
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Getting Help

1. Check the [project wiki](https://github.com/project/wiki)
2. Search existing [issues](https://github.com/project/issues)
3. Join the development discussion
4. Contact the maintainers

## Next Steps

After setting up your development environment:

1. Read the [Architecture Overview](../architecture/overview.md)
2. Review [Coding Standards](../../CONTRIBUTING.md)
3. Explore the [API Documentation](../api/)
4. Start with a simple bug fix or documentation improvement

Happy coding!