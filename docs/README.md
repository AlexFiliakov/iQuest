# Apple Health Monitor Documentation

This directory contains the Sphinx documentation for Apple Health Monitor.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
pip install -r requirements.txt
```

### Building HTML Documentation

```bash
# Quick build
make html

# Clean and rebuild
make rebuild

# Live development server
make livehtml
```

### Building on Windows

```batch
# Quick build
make.bat html

# Clean and rebuild
make.bat rebuild

# Live development server
make.bat livehtml
```

## Documentation Structure

- **`index.rst`** - Main documentation index
- **`api/`** - API reference documentation
  - `core.rst` - Core modules (database, data loading, etc.)
  - `analytics.rst` - Analytics engine and calculators
  - `ui.rst` - User interface components
  - `utils.rst` - Utility modules
  - `models.rst` - Data models
- **`user/`** - User guides and tutorials
  - `data-import.rst` - Data import guide
  - `analytics-overview.rst` - Analytics features overview
- **`development/`** - Developer documentation
  - `architecture.rst` - System architecture
- **`examples/`** - Code examples and tutorials
  - `basic-usage.rst` - Basic usage examples
- **`_static/`** - Static assets (CSS, images)
- **`_templates/`** - Sphinx templates

## Configuration

The documentation is configured in `conf.py` with:

- **Sphinx Extensions**: autodoc, napoleon, viewcode, intersphinx
- **Theme**: Read the Docs theme with custom styling
- **Google Docstring Style**: All docstrings use Google format
- **API Documentation**: Auto-generated from source code

## Writing Documentation

### Docstring Style

Use Google-style docstrings for all Python code:

```python
def calculate_health_score(metrics: List[HealthMetric]) -> HealthScore:
    """Calculate health score from metrics.
    
    Args:
        metrics (List[HealthMetric]): List of health metrics to analyze.
        
    Returns:
        HealthScore: Calculated health score with component breakdown.
        
    Raises:
        ValueError: If metrics list is empty.
        
    Example:
        >>> metrics = [step_metric, heart_rate_metric]
        >>> score = calculate_health_score(metrics)
        >>> print(f"Score: {score.overall_score}")
    """
```

### reStructuredText Format

Documentation files use reStructuredText format:

```rst
Section Title
=============

Subsection
----------

Code Example
~~~~~~~~~~~~

.. code-block:: python

   # Python code example
   from analytics import DailyMetricsCalculator
   
   calculator = DailyMetricsCalculator(database)
   metrics = calculator.calculate_metrics("steps", start_date, end_date)

Cross-references
~~~~~~~~~~~~~~~~

Reference other sections: :doc:`user/data-import`
Reference Python objects: :class:`analytics.DailyMetricsCalculator`
```

## Troubleshooting

### Common Issues

**Import Warnings During Build**
- Expected when building without installing the package
- Warnings don't affect documentation generation
- API documentation still generates from source code analysis

**Missing Extensions**
- Install missing Sphinx extensions with pip
- Optional extensions gracefully degrade if not available

**Theme Issues**
- Ensure sphinx-rtd-theme is installed
- Custom CSS is in `_static/custom.css`

### Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Test configuration
sphinx-build -T -E -b html . _build/html

# Build with warnings as errors (for CI)
sphinx-build -W -b html . _build/html

# Check for broken links
sphinx-build -b linkcheck . _build/linkcheck
```

## Deployment

The documentation can be deployed to:

- **Read the Docs**: Connect your repository for automatic builds
- **GitHub Pages**: Use the `html` output directory
- **Static Hosting**: Any web server can serve the `_build/html` directory

For Read the Docs deployment, ensure:
1. `requirements.txt` is in the docs directory
2. `.readthedocs.yaml` configuration file exists
3. Repository has appropriate permissions

## Contributing

When adding new features:

1. **Update Docstrings**: Follow Google style format
2. **Add Documentation**: Create or update relevant `.rst` files
3. **Test Build**: Run `make html` to verify documentation builds
4. **Review Output**: Check generated HTML for formatting and links

See `contributing.rst` for detailed contribution guidelines.