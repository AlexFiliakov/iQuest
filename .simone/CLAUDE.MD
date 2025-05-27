# Apple Health Monitor Dashboard - Claude Guide

## Project Overview
Building a Windows desktop application to analyze Apple Health data from CSV exports. The app features a warm, inviting UI with dashboards for daily, weekly, and monthly health metrics plus journaling functionality.

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
├── src/                    # Application source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Entry point (PyQt6 app)
│   ├── ui/                # UI components
│   ├── data/              # Data processing
│   ├── analytics/         # Analytics engine
│   └── utils/             # Utilities
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── ui/                # UI tests
├── assets/                 # Icons, themes, fonts
├── data/                   # User data (gitignored)
├── docs/                   # Documentation
├── venv/                   # Virtual environment
├── requirements.txt        # Python dependencies
├── README.md              # Project overview
└── .gitignore             # Git ignore rules
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