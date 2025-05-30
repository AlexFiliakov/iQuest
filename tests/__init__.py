"""Comprehensive test suite for Apple Health Monitor Dashboard.

This package provides extensive testing infrastructure for the Apple Health Monitor
Dashboard application, ensuring code quality, performance, and reliability across
all components.

The test suite includes:

- **Unit Tests**: Comprehensive testing of individual modules and functions
- **Integration Tests**: End-to-end testing of component interactions
- **Performance Tests**: Benchmarking and performance regression detection
- **Visual Regression Tests**: Automated UI testing with baseline comparison
- **Accessibility Tests**: WCAG compliance validation and screen reader testing
- **Mock Infrastructure**: Comprehensive mocking for external dependencies
- **Test Data Generation**: Health data factories and edge case generators

The testing framework follows pytest conventions and includes extensive fixtures,
generators, and utilities for creating realistic test scenarios. All tests are
designed to run quickly and reliably in CI/CD environments.

Example:
    Running the complete test suite:
    
    >>> pytest tests/
    
    Running specific test categories:
    
    >>> pytest tests/unit/
    >>> pytest tests/integration/
    >>> pytest tests/performance/

Note:
    Test data is generated synthetically and does not contain any real health
    information. All test fixtures are designed to respect privacy principles.
"""