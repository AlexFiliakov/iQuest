"""Test fixtures and data generators for Apple Health Monitor Dashboard.

This module provides comprehensive test fixtures, data factories, and utilities
for creating realistic test scenarios across the application. All fixtures
generate synthetic health data that maintains statistical realism while
ensuring complete privacy protection.

The fixtures package includes:

- **Health Data Fixtures**: Comprehensive health metric data generators
- **Database Fixtures**: Pre-configured test databases and transaction helpers
- **Factory Pattern**: Data factories for creating complex test scenarios
- **Time Series Generators**: Realistic temporal health data patterns
- **Edge Case Fixtures**: Boundary conditions and error scenario generators

All fixtures are designed to be:
- **Deterministic**: Reproducible results for consistent testing
- **Realistic**: Statistically accurate health data patterns
- **Comprehensive**: Coverage of all major health metrics and scenarios
- **Privacy-Safe**: No real health data, purely synthetic generation

Example:
    Using health data fixtures in tests:
    
    >>> from tests.fixtures import HealthDataFixtures
    >>> fixtures = HealthDataFixtures()
    >>> steps_data = fixtures.generate_steps_data(days=30)
    >>> heart_rate_data = fixtures.generate_heart_rate_data(days=7)
    
    Using in pytest fixtures:
    
    >>> @pytest.fixture
    ... def sample_health_data():
    ...     return HealthDataFixtures().generate_comprehensive_data()

Note:
    All generated data follows Apple Health Export XML schema conventions
    and includes appropriate metadata, timestamps, and data relationships.
"""

from .health_fixtures import HealthDataFixtures

__all__ = ['HealthDataFixtures']