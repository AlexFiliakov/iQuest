"""
pytest configuration file for test suite
"""

import sys
import os
from pathlib import Path
import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import test data generators and fixtures
from tests.generators import HealthMetricGenerator, TimeSeriesGenerator, EdgeCaseGenerator
from tests.fixtures import HealthDataFixtures
from tests.fixtures.database import TestDatabaseFactory
from tests.helpers.time_helpers import TimeMocker

# Import new centralized fixtures
from tests.fixtures.factories import (
    health_data, mock_data_source, daily_calculator, weekly_calculator, monthly_calculator,
    empty_data_source, large_data_source, weekly_health_data, monthly_health_data, yearly_health_data
)

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )


# Test Data Generator Fixtures
@pytest.fixture(scope='session')
def health_data_generator():
    """Session-scoped health data generator."""
    return HealthMetricGenerator(seed=42)


@pytest.fixture(scope='function')
def sample_health_data():
    """Function-scoped sample health data."""
    return HealthDataFixtures.create_health_dataframe()


@pytest.fixture(scope='function')
def user_profiles():
    """Various user profiles for testing."""
    return {
        'sedentary': HealthDataFixtures.create_user_profile(
            age=45, fitness_level='sedentary'
        ),
        'athlete': HealthDataFixtures.create_user_profile(
            age=25, fitness_level='athlete'
        ),
        'elderly': HealthDataFixtures.create_user_profile(
            age=75, fitness_level='sedentary'
        )
    }


@pytest.fixture(
    params=['small', 'medium', 'large'],
    scope='function'
)
def dataset_size(request):
    """Parameterized dataset sizes."""
    sizes = {
        'small': 7,    # 1 week
        'medium': 30,  # 1 month
        'large': 365   # 1 year
    }
    return sizes[request.param]


@pytest.fixture(scope='function')
def time_series_generator():
    """Time series data generator."""
    return TimeSeriesGenerator(seed=42)


@pytest.fixture(scope='function')
def edge_case_generator():
    """Edge case data generator."""
    return EdgeCaseGenerator(seed=42)


@pytest.fixture(scope='function')
def edge_case_datasets(edge_case_generator):
    """Collection of edge case datasets."""
    return edge_case_generator.generate_edge_case_datasets()


# Database fixtures for cache and database testing
@pytest.fixture
def memory_db():
    """In-memory database for fast unit tests."""
    with TestDatabaseFactory.in_memory_db() as conn:
        yield conn


@pytest.fixture
def file_db():
    """File-based database for integration tests."""
    with TestDatabaseFactory.temp_file_db() as (conn, path):
        yield conn, path


@pytest.fixture(autouse=True)
def isolate_tests(monkeypatch):
    """Ensure each test gets fresh database."""
    # Prevent tests from using production database
    monkeypatch.setenv('HEALTH_DB_PATH', ':memory:')
    # Ensure cache directories are temporary
    import tempfile
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv('CACHE_DIR', temp_dir)


@pytest.fixture
def time_mocker():
    """Time mocker for testing time-dependent functionality."""
    return TimeMocker()