Apple Health Monitor Documentation
=====================================

Apple Health Monitor is a comprehensive health data analytics platform that provides 
powerful tools for analyzing, visualizing, and gaining insights from Apple Health data exports.

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://python.org
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/docs-latest-brightgreen.svg
   :target: https://apple-health-monitor.readthedocs.io/
   :alt: Documentation

Overview
--------

Apple Health Monitor transforms raw Apple Health export data into meaningful insights 
through advanced analytics, interactive visualizations, and intelligent health scoring.

Key Features
~~~~~~~~~~~~

🏥 **Comprehensive Health Analytics**
   - Daily, weekly, and monthly health metrics calculation
   - Advanced trend analysis and anomaly detection
   - Predictive analytics and health forecasting
   - Personal health score computation

📊 **Professional Visualizations**
   - Wall Street Journal-inspired chart styling
   - Interactive dashboards with drill-down capabilities
   - Accessibility-compliant visualizations (WCAG 2.1 AA)
   - Export-ready charts for presentations

⚡ **High Performance**
   - Optimized analytics engine with streaming data processing
   - Multi-level caching system for fast responses
   - Progressive loading for large datasets
   - Memory-efficient data handling

🔧 **Developer Friendly**
   - Comprehensive Python API
   - Extensible plugin architecture
   - Well-documented codebase with examples
   - Unit and integration test coverage

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install apple-health-monitor

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from src.main import HealthMonitorApp
   from src.data_loader import DataLoader
   
   # Load Apple Health data
   loader = DataLoader()
   data = loader.load_from_xml("export.xml")
   
   # Launch the application
   app = HealthMonitorApp()
   app.load_data(data)
   app.run()

API Quick Reference
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import DailyMetricsCalculator, HealthScoreCalculator
   from ui.charts import WSJHealthVisualizationSuite
   
   # Calculate metrics
   calculator = DailyMetricsCalculator(database)
   metrics = calculator.calculate_metrics("HKQuantityTypeIdentifierStepCount", 
                                         start_date, end_date)
   
   # Generate health score
   scorer = HealthScoreCalculator(database)
   score = scorer.calculate_score(user_id, start_date, end_date)
   
   # Create visualizations
   viz_suite = WSJHealthVisualizationSuite()
   chart = viz_suite.create_trend_chart(metrics, "Steps")

Architecture Overview
--------------------

Apple Health Monitor is built with a modular architecture:

.. mermaid::

   graph TB
       UI[User Interface Layer]
       API[Analytics API Layer]
       CORE[Core Processing Engine]
       DATA[Data Access Layer]
       STORE[Data Storage]
       
       UI --> API
       API --> CORE
       CORE --> DATA
       DATA --> STORE
       
       UI -.-> |Charts & Dashboards| VIZ[Visualization Engine]
       API -.-> |Caching| CACHE[Cache Manager]
       CORE -.-> |Performance| OPT[Optimization Engine]

User Documentation
------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user/getting-started
   user/data-import
   user/analytics-overview
   user/visualizations
   user/health-scoring
   user/export-reporting
   user/troubleshooting

Developer Documentation
-----------------------

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   development/setup
   development/architecture
   development/contributing
   development/testing
   development/performance
   development/deployment

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   api/core
   api/analytics
   api/ui
   api/utils
   api/models

Examples and Tutorials
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic-usage
   examples/custom-analytics
   examples/chart-customization
   examples/plugin-development
   examples/performance-optimization

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 1
   :caption: Project Info
   :hidden:

   changelog
   license
   contributing