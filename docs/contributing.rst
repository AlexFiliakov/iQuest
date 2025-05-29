Contributing to Apple Health Monitor
====================================

We welcome contributions to Apple Health Monitor! This guide will help you get started
with contributing to the project.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~

1. **Fork and Clone**

   .. code-block:: bash

      git clone https://github.com/yourusername/apple-health-monitor.git
      cd apple-health-monitor

2. **Set Up Development Environment**

   .. code-block:: bash

      # Create virtual environment
      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      
      # Install development dependencies
      pip install -r requirements-test.txt
      pip install -r docs/requirements.txt

3. **Install Pre-commit Hooks**

   .. code-block:: bash

      pre-commit install

4. **Run Tests**

   .. code-block:: bash

      python -m pytest

Development Workflow
-------------------

Code Standards
~~~~~~~~~~~~~

**Python Style**
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable and function names

**Docstring Requirements**
- All public functions, classes, and modules must have docstrings
- Use Google-style docstrings consistently
- Include examples for complex functions

**Example:**

.. code-block:: python

   def calculate_health_score(
       metrics: List[HealthMetric], 
       user_profile: UserProfile
   ) -> HealthScore:
       """Calculate personalized health score from metrics.
       
       Args:
           metrics (List[HealthMetric]): List of health metrics to analyze.
           user_profile (UserProfile): User's demographic and health profile.
           
       Returns:
           HealthScore: Calculated health score with component breakdown.
           
       Raises:
           ValueError: If metrics list is empty or invalid.
           
       Example:
           >>> metrics = [step_metric, sleep_metric, heart_rate_metric]
           >>> profile = UserProfile(age=30, gender="M")
           >>> score = calculate_health_score(metrics, profile)
           >>> print(f"Health score: {score.overall_score}")
       """

**Testing Requirements**
- Write unit tests for all new functions and classes
- Aim for >90% code coverage
- Include integration tests for new features
- Add performance tests for analytics functions

**Git Workflow**
- Create feature branches from `main`
- Use descriptive commit messages
- Squash commits before merging
- Include issue numbers in commit messages

Commit Message Format
~~~~~~~~~~~~~~~~~~~

Use the conventional commit format:

.. code-block::

   type(scope): description
   
   [optional body]
   
   [optional footer]

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no functional changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `perf`: Performance improvements

**Examples:**

.. code-block::

   feat(analytics): add correlation analysis engine
   
   - Implement Pearson and Spearman correlation methods
   - Add statistical significance testing
   - Include correlation discovery algorithms
   
   Closes #123

   fix(ui): resolve chart rendering memory leak
   
   Fixed memory leak in chart component cleanup that was causing
   performance degradation with large datasets.
   
   Fixes #456

Code Review Process
------------------

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~

1. **Before Submitting**
   - Ensure all tests pass
   - Run linting and formatting tools
   - Update documentation if needed
   - Add or update tests for your changes

2. **PR Title and Description**
   - Use clear, descriptive titles
   - Include detailed description of changes
   - Reference related issues
   - Include testing instructions

3. **Review Process**
   - All PRs require at least one review
   - Address reviewer feedback promptly
   - Update tests and documentation as requested
   - Maintain clean commit history

**PR Template:**

.. code-block:: markdown

   ## Description
   Brief description of changes and motivation.
   
   ## Changes Made
   - List of specific changes
   - Include new features, bug fixes, etc.
   
   ## Testing
   - How to test the changes
   - Any new test cases added
   
   ## Documentation
   - Documentation updates made
   - API changes that affect users
   
   ## Checklist
   - [ ] Tests pass
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] Breaking changes documented

Contributing Areas
-----------------

Analytics Engine
~~~~~~~~~~~~~~~

**Opportunities:**
- New health metric calculators
- Advanced statistical analysis methods
- Machine learning algorithms for health insights
- Performance optimizations

**Getting Started:**
- Look at existing calculators in `src/analytics/`
- Follow the calculator interface pattern
- Add comprehensive tests and documentation

**Example Contribution:**

.. code-block:: python

   class BloodPressureCalculator(BaseCalculator):
       """Calculator for blood pressure analysis and trends."""
       
       def calculate_metrics(
           self, 
           start_date: date, 
           end_date: date
       ) -> List[BloodPressureMetric]:
           """Calculate blood pressure metrics and trends."""
           # Implementation here

Visualization Components
~~~~~~~~~~~~~~~~~~~~~~~

**Opportunities:**
- New chart types and visualizations
- Interactive features and animations
- Accessibility improvements
- Mobile-responsive designs

**Getting Started:**
- Examine existing charts in `src/ui/charts/`
- Follow the WSJ style guidelines
- Ensure accessibility compliance

User Interface
~~~~~~~~~~~~~

**Opportunities:**
- New dashboard layouts
- Improved user experience
- Accessibility enhancements
- Internationalization support

**Getting Started:**
- Review existing UI components in `src/ui/`
- Follow Qt5 best practices
- Test across different platforms

Data Processing
~~~~~~~~~~~~~~

**Opportunities:**
- Support for new data sources
- Improved data validation
- Performance optimizations
- Data export formats

**Getting Started:**
- Look at data processing in `src/data_loader.py`
- Add support for new Apple Health data types
- Ensure robust error handling

Testing and Quality
------------------

Test Categories
~~~~~~~~~~~~~~

**Unit Tests**
- Test individual functions and classes
- Mock external dependencies
- Cover edge cases and error conditions

**Integration Tests**
- Test component interactions
- Database integration
- End-to-end workflows

**Performance Tests**
- Benchmark analytics calculations
- Memory usage validation
- Large dataset processing

**Visual Regression Tests**
- Chart rendering consistency
- UI component appearance
- Cross-platform compatibility

Running Tests
~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   python -m pytest
   
   # Run specific test category
   python -m pytest tests/unit/
   python -m pytest tests/integration/
   python -m pytest tests/performance/
   
   # Run with coverage
   python -m pytest --cov=src --cov-report=html
   
   # Run specific test file
   python -m pytest tests/unit/test_analytics.py

Code Quality Tools
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Linting
   flake8 src/
   pylint src/
   
   # Type checking
   mypy src/
   
   # Security scanning
   bandit -r src/
   
   # Import sorting
   isort src/
   
   # Code formatting
   black src/

Documentation
------------

Documentation Types
~~~~~~~~~~~~~~~~~~

**API Documentation**
- Automatically generated from docstrings
- Comprehensive parameter descriptions
- Usage examples and best practices

**User Guides**
- Step-by-step tutorials
- Feature explanations
- Troubleshooting guides

**Developer Documentation**
- Architecture explanations
- Contributing guidelines
- Testing procedures

Building Documentation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs/
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Build HTML documentation
   make html
   
   # Build with live reload for development
   make livehtml
   
   # Clean and rebuild
   make rebuild

Writing Documentation
~~~~~~~~~~~~~~~~~~~~

**Guidelines:**
- Use clear, concise language
- Include practical examples
- Update documentation with code changes
- Follow reStructuredText format

**Example:**

.. code-block:: rst

   Health Score Calculation
   ========================
   
   The health score system provides a comprehensive assessment of your
   overall health based on multiple metrics.
   
   Basic Usage
   -----------
   
   .. code-block:: python
   
      from analytics.health_score import HealthScoreCalculator
      
      calculator = HealthScoreCalculator(database)
      score = calculator.calculate_score(user_id, start_date, end_date)
      print(f"Health Score: {score.overall_score}/100")

Community Guidelines
-------------------

Communication
~~~~~~~~~~~~

**Be Respectful**
- Treat all contributors with respect
- Provide constructive feedback
- Be patient with newcomers

**Be Helpful**
- Answer questions when you can
- Share knowledge and resources
- Mentor new contributors

**Stay Focused**
- Keep discussions on-topic
- Use appropriate channels for different topics
- Search before asking questions

Issue Reporting
~~~~~~~~~~~~~~

**Bug Reports**
- Use the bug report template
- Include steps to reproduce
- Provide system information
- Include relevant logs and screenshots

**Feature Requests**
- Describe the problem you're trying to solve
- Explain why the feature would be valuable
- Consider implementation approaches
- Discuss with maintainers before starting work

**Questions and Support**
- Check existing documentation first
- Search existing issues
- Use clear, descriptive titles
- Provide context and examples

Recognition
----------

We recognize contributors in several ways:

**Contributors List**
- All contributors are listed in the repository
- Contributions are tracked and acknowledged

**Release Notes**
- Significant contributions are highlighted in release notes
- Feature additions and improvements are credited

**Community Roles**
- Active contributors may be invited to join the core team
- Experienced contributors can become maintainers

Getting Help
-----------

If you need help with contributing:

- **Documentation**: Check the developer docs
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Request specific feedback on your PR

Thank you for contributing to Apple Health Monitor!