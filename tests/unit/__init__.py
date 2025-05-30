"""Unit tests for Apple Health Monitor Dashboard components.

This module contains comprehensive unit tests for individual components, functions,
and classes within the Apple Health Monitor Dashboard. Each test focuses on testing
isolated functionality with minimal dependencies.

The unit tests cover:

- **Core Infrastructure**: Database operations, data models, and configuration
- **Analytics Engine**: Calculators, caching systems, and optimization algorithms
- **UI Components**: Individual widgets, charts, and interface elements
- **Utilities**: Error handling, logging, and validation functions
- **Data Processing**: Import/export functionality and streaming processors

All unit tests use mocking extensively to isolate the component under test and
ensure fast, reliable execution. The tests follow AAA (Arrange-Act-Assert)
patterns and include comprehensive edge case coverage.

Example:
    Running all unit tests:
    
    >>> pytest tests/unit/
    
    Running specific module tests:
    
    >>> pytest tests/unit/test_daily_metrics_calculator.py
    >>> pytest tests/unit/test_database.py

Note:
    Unit tests are designed to run independently and should complete in under
    5 minutes for the entire suite. Mock data is used exclusively.
"""