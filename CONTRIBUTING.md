# Contributing to Apple Health Monitor Dashboard

Thank you for your interest in contributing to the Apple Health Monitor Dashboard project! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see Development Setup)
4. Create a new branch for your feature or bug fix
5. Make your changes following our coding standards
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Windows 10/11 (for full testing)
- Git

### Environment Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/apple-health-monitor.git
cd apple-health-monitor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Application

```bash
python src/main.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_data_loader.py

# Run tests with verbose output
pytest -v
```

## Development Workflow

1. **Create a branch**: Use descriptive branch names
   - Feature: `feature/add-export-functionality`
   - Bug fix: `fix/csv-import-error`
   - Documentation: `docs/update-api-guide`

2. **Make changes**: Follow coding standards and add tests

3. **Test locally**: Ensure all tests pass
   ```bash
   pytest
   python src/main.py  # Manual testing
   ```

4. **Commit changes**: Use conventional commit messages

5. **Push to your fork**: `git push origin your-branch-name`

6. **Create pull request**: Provide clear description of changes

## Coding Standards

### UI/UX Development

When developing UI components, please refer to our comprehensive [UI Specifications](.simone/01_SPECS/UI_SPECS.md) which covers:
- Design philosophy and principles
- Visual design system (colors, typography, spacing)
- Component architecture and specifications
- Layout principles and responsive design
- Interaction patterns and animations
- Accessibility guidelines
- Performance considerations

All UI components should follow the modern Wall Street Journal-inspired design aesthetic outlined in the specifications.

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: Maximum 100 characters (PyQt6 code can be verbose)
- **Imports**: Group in order: standard library, third-party, local
- **Docstrings**: Use Google style docstrings
- **Type hints**: Required for all public functions

### Code Organization

```python
# Import grouping
import os
import sys
from datetime import datetime

import pandas as pd
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from src.utils import logger
from src.models import HealthData
```

### Function Documentation

```python
def process_health_data(file_path: str, date_range: tuple[datetime, datetime]) -> pd.DataFrame:
    """Process health data from CSV file within specified date range.
    
    Args:
        file_path: Path to the CSV file containing health data
        date_range: Tuple of (start_date, end_date) for filtering
        
    Returns:
        DataFrame containing processed health metrics
        
    Raises:
        FileNotFoundError: If the specified file doesn't exist
        ValueError: If date_range is invalid
    """
    pass
```

### PyQt6 Conventions

- Use Qt Designer for complex UIs when appropriate
- Separate UI logic from business logic
- Follow Qt naming conventions (e.g., `on_buttonName_clicked`)
- Use signals and slots for communication between components

### Error Handling

```python
from src.utils.error_handler import handle_errors

@handle_errors
def risky_operation():
    """Operation that might fail."""
    # Use the error handling decorator for consistent error management
    pass
```

### Logging

```python
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def some_function():
    logger.info("Starting operation")
    try:
        # operation
        logger.debug("Operation details")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
```

## Testing Guidelines

### Test Structure

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- UI tests: `tests/ui/`

### Writing Tests

```python
import pytest
from src.data_loader import HealthDataLoader

class TestHealthDataLoader:
    """Test cases for HealthDataLoader class."""
    
    @pytest.fixture
    def loader(self):
        """Create a HealthDataLoader instance for testing."""
        return HealthDataLoader()
    
    def test_load_csv_valid_file(self, loader, tmp_path):
        """Test loading a valid CSV file."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("date,metric,value\n2024-01-01,steps,5000")
        
        # Test loading
        result = loader.load_csv(str(test_file))
        assert len(result) == 1
        assert result.iloc[0]['metric'] == 'steps'
```

### Test Coverage

- Aim for >80% code coverage
- Test edge cases and error conditions
- Include integration tests for critical paths
- Add UI tests for user-facing features

## Commit Messages

We use conventional commits format:

```
type(scope): subject

body

footer
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(analytics): add weekly trend analysis

Implement weekly metrics calculator with:
- 7-day rolling averages
- Week-over-week comparisons
- Trend detection algorithms

Closes #123
```

```
fix(import): handle large XML files efficiently

Use iterative parsing to prevent memory issues
when importing files >100MB
```

## Pull Request Process

1. **Update documentation**: Include any necessary documentation changes

2. **Add tests**: Include tests for new functionality

3. **Pass CI checks**: Ensure all automated checks pass

4. **Fill PR template**: Provide clear description of changes

5. **Request review**: Tag appropriate reviewers

6. **Address feedback**: Respond to review comments promptly

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Code follows style guidelines
- [ ] Commit messages follow conventions
- [ ] PR description is clear and complete

## Documentation

### Code Documentation

- All public modules, classes, and functions must have docstrings
- Use type hints for function parameters and return values
- Include usage examples in docstrings for complex functions

### User Documentation

- Update user guides in `docs/user/` for user-facing changes
- Include screenshots for UI changes
- Keep getting started guide current

### API Documentation

- Document all public APIs in `docs/api/`
- Include request/response examples
- Update when API changes are made

## Questions?

If you have questions about contributing, please:

1. Check existing issues and discussions
2. Review the documentation
3. Open a new issue with the question label

Thank you for contributing to Apple Health Monitor Dashboard!