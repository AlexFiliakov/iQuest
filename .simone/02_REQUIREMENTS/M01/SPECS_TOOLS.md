# Tool Specifications
## Apple Health Monitor Dashboard - M01

### 1. Development Tools

#### 1.1 Core Technologies
- **Python Version:** 3.10+ (for modern type hints and features)
- **Package Manager:** pip with virtual environment
- **Version Control:** Git with conventional commits

#### 1.2 Primary Libraries
```toml
# pyproject.toml dependencies
[project]
dependencies = [
    "pandas>=2.0.0",        # Data processing
    "numpy>=1.24.0",        # Numerical computations
    "PyQt6>=6.5.0",         # GUI framework
    "matplotlib>=3.7.0",    # Charting library
    "sqlite3",              # Built-in database
    "python-dateutil",      # Date handling
    "pyqtgraph",           # Fast real-time plotting
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",        # Testing framework
    "pytest-qt",            # Qt testing
    "black",                # Code formatting
    "flake8",              # Linting
    "mypy",                # Type checking
    "coverage",            # Code coverage
]

test = [
    "pytest-benchmark>=4.0.0",    # Performance benchmarking
    "pytest-timeout>=2.1.0",      # Timeout protection
    "pytest-mock>=3.10.0",        # Advanced mocking
    "pytest-xdist>=3.0.0",        # Parallel test execution
    "pytest-html>=3.1.0",         # HTML test reports
    "pytest-mpl>=0.16.0",         # Visual regression testing
    "pillow>=9.0.0",              # Image processing for visual tests
    "memory-profiler>=0.60.0",    # Memory usage profiling
    "faker>=18.0.0",              # Synthetic data generation
]

build = [
    "pyinstaller>=5.0",    # Executable creation
    "setuptools>=65.0",    # Package management
]
```

### 2. Build Tools

#### 2.1 PyInstaller Configuration
```python
# build_config.spec
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icons', 'assets/icons'),
        ('assets/fonts', 'assets/fonts'),
        ('assets/themes', 'assets/themes'),
    ],
    hiddenimports=[
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'matplotlib.backends.backend_qt5agg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HealthMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app_icon.ico',
    version='version_info.txt'
)
```

#### 2.2 Build Scripts
```bash
# scripts/build_windows.sh
#!/bin/bash
# Build Windows executable

echo "Building Health Monitor for Windows..."

# Clean previous builds
rm -rf build dist

# Run tests
pytest tests/ || exit 1

# Type checking
mypy src/ || exit 1

# Build executable
pyinstaller build_config.spec --clean

# Compress executable
upx --best dist/HealthMonitor.exe

# Create installer
makensis installer.nsi

echo "Build complete!"
```

### 3. Development Environment

#### 3.1 IDE Configuration
```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "build/": true,
        "dist/": true
    }
}
```

#### 3.2 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 4. Testing Tools

#### 4.1 Testing Framework
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --qt-api=pyqt6
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    ui: marks tests that require Qt
```

#### 4.2 Test Structure
```
tests/
├── unit/
│   ├── test_data_import.py
│   ├── test_metrics.py
│   ├── test_filters.py
│   └── test_journal.py
├── integration/
│   ├── test_csv_processing.py
│   ├── test_database.py
│   └── test_chart_generation.py
├── ui/
│   ├── test_main_window.py
│   ├── test_dashboards.py
│   └── test_configuration.py
└── fixtures/
    ├── sample_data.csv
    └── test_config.json
```

### 5. Documentation Tools

#### 5.1 Code Documentation
```python
# Example docstring format (Google style)
def calculate_metrics(data: pd.DataFrame, metric_type: str) -> MetricsResult:
    """Calculate statistical metrics for health data.
    
    Args:
        data: Filtered dataframe containing health records
        metric_type: Type of health metric to analyze
        
    Returns:
        MetricsResult object containing avg, min, max values
        
    Raises:
        ValueError: If metric_type not found in data
        DataError: If insufficient data for calculation
        
    Example:
        >>> result = calculate_metrics(df, "HeartRate")
        >>> print(f"Average: {result.average}")
    """
```

#### 5.2 User Documentation
- **Tool:** MkDocs with Material theme
- **Structure:**
  ```
  docs/
  ├── index.md           # Overview
  ├── installation.md    # Setup guide
  ├── user-guide/
  │   ├── importing.md   # Data import
  │   ├── filtering.md   # Using filters
  │   ├── dashboards.md  # Dashboard guide
  │   └── journaling.md  # Journal feature
  └── troubleshooting.md # Common issues
  ```

### 6. Performance Tools

#### 6.1 Profiling
```python
# Performance profiling decorator
import cProfile
import pstats
from functools import wraps

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper
```

#### 6.2 Memory Profiling
```python
# requirements-dev.txt
memory-profiler==0.60.0
pympler==1.0.1

# Usage
@profile
def process_large_csv(file_path):
    # Memory-intensive operation
    pass
```

### 7. UI Design Tools

#### 7.1 Qt Designer
- **Purpose:** Visual UI design
- **Integration:** Convert .ui files to Python
- **Workflow:**
  ```bash
  # Convert UI files
  pyuic6 -x design.ui -o ui_design.py
  
  # Convert resources
  pyrcc6 resources.qrc -o resources_rc.py
  ```

#### 7.2 Color Palette Generator
```python
# tools/generate_theme.py
class ThemeGenerator:
    """Generate consistent color themes"""
    
    BASE_COLORS = {
        'primary_bg': '#F5E6D3',     # Warm tan
        'secondary_bg': '#FFFFFF',    # White
        'primary_accent': '#FF8C42',  # Warm orange
        'secondary_accent': '#FFD166', # Soft yellow
        'text_primary': '#5D4E37',    # Dark brown
        'text_secondary': '#8B7355',  # Medium brown
    }
    
    def generate_stylesheet(self) -> str:
        """Generate Qt stylesheet from color palette"""
        pass
```

### 8. Debugging Tools

#### 8.1 Qt Debug Configuration
```python
# Enable Qt debugging
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'
os.environ['QT_LOGGING_RULES'] = '*.debug=true'

# Debug widget inspector
from PyQt6.QtWidgets import QApplication
app = QApplication.instance()
app.setAttribute(Qt.AA_EnableHighDpiScaling)
```

#### 8.2 Logging Configuration
```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': 'health_monitor.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

### 9. Deployment Tools

#### 9.1 Windows Installer (NSIS)
```nsis
; installer.nsi
!define APP_NAME "Health Monitor"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Health Monitor Team"
!define APP_ICON "assets\icons\app_icon.ico"

!include "MUI2.nsh"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "HealthMonitor-${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

Section "Main"
    SetOutPath "$INSTDIR"
    File /r "dist\*.*"
    
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\HealthMonitor.exe"
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\HealthMonitor.exe"
SectionEnd
```

#### 9.2 Update Mechanism
```python
# Auto-update configuration
class UpdateChecker:
    UPDATE_URL = "https://api.healthmonitor.app/updates"
    
    def check_for_updates(self, current_version: str) -> Optional[UpdateInfo]:
        """Check if newer version available"""
        pass
        
    def download_update(self, update_info: UpdateInfo) -> bool:
        """Download and prepare update"""
        pass
```

### 10. Continuous Integration

#### 10.1 GitHub Actions
```yaml
# .github/workflows/build.yml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,build]
    
    - name: Run tests
      run: pytest
    
    - name: Build executable
      run: pyinstaller build_config.spec
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: HealthMonitor-${{ matrix.python-version }}
        path: dist/HealthMonitor.exe
```