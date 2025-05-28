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