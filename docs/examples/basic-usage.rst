Basic Usage Examples
===================

This guide provides practical examples of how to use Apple Health Monitor's core features
for common health data analysis tasks.

Getting Started
---------------

Basic Application Setup
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sys
   from PyQt5.QtWidgets import QApplication
   from src.main import HealthMonitorApp
   from src.data_loader import DataLoader
   
   # Initialize the application
   app = QApplication(sys.argv)
   
   # Create and configure the main application
   health_app = HealthMonitorApp()
   
   # Load health data
   loader = DataLoader()
   health_data = loader.load_from_xml("path/to/export.xml")
   health_app.load_data(health_data)
   
   # Show the application
   health_app.show()
   
   # Run the application
   sys.exit(app.exec_())

Database Setup and Data Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.database import DatabaseManager
   from src.data_loader import DataLoader
   from src.health_database import HealthDatabase
   
   # Initialize database
   db_manager = DatabaseManager()
   health_db = HealthDatabase()
   
   # Load and import health data
   loader = DataLoader()
   
   # Option 1: Load from XML file
   health_data = loader.load_from_xml("export.xml")
   
   # Option 2: Load from CSV file
   health_data = loader.load_from_csv("health_data.csv")
   
   # Import data to database
   import_stats = loader.import_to_database(health_data, db_manager)
   print(f"Imported {import_stats['records']} health records")
   
   # Verify import
   available_types = health_db.get_available_types()
   print(f"Available health metrics: {available_types}")

Basic Analytics
---------------

Daily Metrics Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import DailyMetricsCalculator
   from datetime import datetime, date
   
   # Initialize calculator
   calculator = DailyMetricsCalculator(health_db)
   
   # Define date range
   start_date = date(2024, 1, 1)
   end_date = date(2024, 1, 31)
   
   # Calculate daily step counts
   step_metrics = calculator.calculate_metrics(
       metric_type="HKQuantityTypeIdentifierStepCount",
       start_date=start_date,
       end_date=end_date
   )
   
   # Display results
   for daily_metric in step_metrics:
       print(f"{daily_metric.date}: {daily_metric.total_value} steps")
   
   # Get summary statistics
   summary = calculator.get_summary_stats(step_metrics)
   print(f"Average daily steps: {summary.mean:.0f}")
   print(f"Max daily steps: {summary.max:.0f}")
   print(f"Days with data: {summary.count}")

Weekly Trend Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import WeeklyMetricsCalculator, WeekOverWeekTrends
   
   # Calculate weekly metrics
   weekly_calc = WeeklyMetricsCalculator(health_db)
   weekly_steps = weekly_calc.calculate_metrics(
       metric_type="HKQuantityTypeIdentifierStepCount",
       start_date=start_date,
       end_date=end_date
   )
   
   # Analyze week-over-week trends
   trend_analyzer = WeekOverWeekTrends(health_db)
   trends = trend_analyzer.analyze_trends(
       metric_type="HKQuantityTypeIdentifierStepCount",
       weeks=12
   )
   
   # Display trend information
   print(f"Current trend: {trends.current_trend.direction}")
   print(f"Trend strength: {trends.current_trend.strength}")
   print(f"Momentum: {trends.momentum.type}")
   
   if trends.prediction:
       print(f"Next week prediction: {trends.prediction.value:.0f} steps")
       print(f"Confidence: {trends.prediction.confidence:.2f}")

Health Score Calculation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics.health_score import HealthScoreCalculator
   
   # Initialize health score calculator
   score_calculator = HealthScoreCalculator(health_db)
   
   # Calculate health score for a time period
   health_score = score_calculator.calculate_score(
       user_id="default_user",
       start_date=start_date,
       end_date=end_date
   )
   
   # Display overall score
   print(f"Overall Health Score: {health_score.overall_score}/100")
   print(f"Score Date: {health_score.calculation_date}")
   
   # Display component scores
   for component in health_score.components:
       print(f"{component.name}: {component.score}/100")
       if component.insights:
           for insight in component.insights:
               print(f"  - {insight}")

Basic Visualizations
--------------------

Creating Simple Charts
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ui.charts import LineChart, ChartConfig
   from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
   
   # Create application window
   app = QApplication(sys.argv)
   window = QMainWindow()
   central_widget = QWidget()
   layout = QVBoxLayout(central_widget)
   
   # Configure chart
   config = ChartConfig(
       title="Daily Steps",
       x_label="Date",
       y_label="Steps",
       show_grid=True
   )
   
   # Create line chart
   chart = LineChart(config)
   
   # Prepare data (convert metrics to chart format)
   dates = [metric.date for metric in step_metrics]
   values = [metric.total_value for metric in step_metrics]
   
   # Set chart data
   chart.set_data(dates, values)
   
   # Add chart to layout
   layout.addWidget(chart)
   window.setCentralWidget(central_widget)
   
   # Show window
   window.show()
   sys.exit(app.exec_())

WSJ-Style Visualization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ui.charts import WSJHealthVisualizationSuite
   from ui.component_factory import ComponentFactory
   
   # Create WSJ-style visualization suite
   viz_suite = WSJHealthVisualizationSuite()
   
   # Create component factory for consistent styling
   factory = ComponentFactory()
   
   # Create a trend chart with WSJ styling
   trend_chart = viz_suite.create_trend_chart(
       data=step_metrics,
       metric_name="Daily Steps",
       title="Step Count Trends"
   )
   
   # Create summary cards
   step_card = factory.create_metric_card(
       title="Average Steps",
       value=f"{summary.mean:.0f}",
       card_type="simple",
       wsj_style=True
   )
   
   # Create comparison chart
   comparison_chart = viz_suite.create_comparison_chart(
       current_data=step_metrics,
       comparison_data=previous_month_steps,
       title="Month-over-Month Comparison"
   )

Dashboard Creation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ui.dashboards import WSJDashboardLayout, HealthDashboardTemplates
   from ui.component_factory import ComponentFactory
   
   # Create dashboard with template
   dashboard = WSJDashboardLayout()
   template = HealthDashboardTemplates.get_template_by_name("daily_overview")
   dashboard.apply_layout_template(template)
   
   # Create components using factory
   factory = ComponentFactory()
   
   # Add summary cards
   steps_card = factory.create_metric_card(
       title="Steps Today",
       value="8,547",
       trend="+12% vs yesterday"
   )
   
   heart_rate_card = factory.create_metric_card(
       title="Avg Heart Rate",
       value="72 bpm",
       trend="Normal range"
   )
   
   # Add charts
   steps_chart = factory.create_line_chart(wsj_style=True)
   steps_chart.set_data(dates, values)
   
   # Add components to dashboard
   dashboard.add_component(steps_card, row=0, col=0)
   dashboard.add_component(heart_rate_card, row=0, col=1)
   dashboard.add_component(steps_chart, row=1, col=0, colspan=2)

Data Analysis Workflows
-----------------------

Complete Analysis Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import (
       DailyMetricsCalculator,
       WeekOverWeekTrends,
       AnomalyDetectionSystem,
       CorrelationAnalyzer
   )
   
   def comprehensive_health_analysis(metric_type, start_date, end_date):
       \"\"\"Perform comprehensive analysis of a health metric.\"\"\"
       
       # 1. Calculate basic metrics
       daily_calc = DailyMetricsCalculator(health_db)
       metrics = daily_calc.calculate_metrics(metric_type, start_date, end_date)
       
       # 2. Analyze trends
       trend_analyzer = WeekOverWeekTrends(health_db)
       trends = trend_analyzer.analyze_trends(metric_type, weeks=12)
       
       # 3. Detect anomalies
       anomaly_detector = AnomalyDetectionSystem(health_db)
       anomalies = anomaly_detector.detect_anomalies(
           metric_type=metric_type,
           start_date=start_date,
           end_date=end_date
       )
       
       # 4. Find correlations with other metrics
       correlation_analyzer = CorrelationAnalyzer(health_db)
       correlations = correlation_analyzer.find_correlations(
           primary_metric=metric_type,
           secondary_metrics=["sleep", "heart_rate"],
           time_period="3_months"
       )
       
       # 5. Generate summary report
       report = {
           'metric_type': metric_type,
           'date_range': (start_date, end_date),
           'basic_stats': {
               'count': len(metrics),
               'mean': sum(m.total_value for m in metrics) / len(metrics),
               'max': max(m.total_value for m in metrics),
               'min': min(m.total_value for m in metrics)
           },
           'trends': trends,
           'anomalies': anomalies,
           'correlations': correlations
       }
       
       return report
   
   # Run comprehensive analysis
   analysis = comprehensive_health_analysis(
       "HKQuantityTypeIdentifierStepCount",
       start_date,
       end_date
   )
   
   # Display results
   print(f"Analysis for {analysis['metric_type']}")
   print(f"Basic Stats: {analysis['basic_stats']}")
   print(f"Trend Direction: {analysis['trends'].current_trend.direction}")
   print(f"Anomalies Found: {len(analysis['anomalies'])}")

Multi-Metric Comparison
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import ComparativeAnalytics
   
   def compare_health_metrics(metrics, start_date, end_date):
       \"\"\"Compare multiple health metrics over the same period.\"\"\"
       
       comparative_analyzer = ComparativeAnalytics(health_db)
       results = {}
       
       for metric in metrics:
           # Calculate daily values
           daily_calc = DailyMetricsCalculator(health_db)
           daily_data = daily_calc.calculate_metrics(metric, start_date, end_date)
           
           # Compare weekdays vs weekends
           weekday_comparison = comparative_analyzer.compare_contexts(
               metric_type=metric,
               context_a="weekdays",
               context_b="weekends",
               start_date=start_date,
               end_date=end_date
           )
           
           results[metric] = {
               'daily_data': daily_data,
               'weekday_vs_weekend': weekday_comparison
           }
       
       return results
   
   # Compare multiple metrics
   metrics_to_compare = [
       "HKQuantityTypeIdentifierStepCount",
       "HKQuantityTypeIdentifierActiveEnergyBurned",
       "HKCategoryTypeIdentifierSleepAnalysis"
   ]
   
   comparison_results = compare_health_metrics(
       metrics_to_compare,
       start_date,
       end_date
   )
   
   # Display comparison results
   for metric, data in comparison_results.items():
       print(f"\\n{metric}:")
       comparison = data['weekday_vs_weekend']
       print(f"  Weekday average: {comparison.context_a_stats.mean:.2f}")
       print(f"  Weekend average: {comparison.context_b_stats.mean:.2f}")
       print(f"  Difference: {comparison.difference_percentage:.1f}%")

Goal Tracking Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import GoalManagementSystem
   from datetime import datetime, timedelta
   
   def setup_and_track_goals():
       \"\"\"Set up health goals and track progress.\"\"\"
       
       goal_system = GoalManagementSystem(health_db)
       
       # Create daily step goal
       step_goal = goal_system.create_goal(
           metric_type="HKQuantityTypeIdentifierStepCount",
           target_value=10000,
           target_period="daily",
           start_date=datetime.now().date(),
           end_date=datetime.now().date() + timedelta(days=30)
       )
       
       # Create weekly active energy goal
       energy_goal = goal_system.create_goal(
           metric_type="HKQuantityTypeIdentifierActiveEnergyBurned",
           target_value=2000,  # 2000 calories per week
           target_period="weekly",
           start_date=datetime.now().date(),
           end_date=datetime.now().date() + timedelta(weeks=12)
       )
       
       # Track progress for both goals
       goals = [step_goal, energy_goal]
       
       for goal in goals:
           progress = goal_system.calculate_progress(goal.id)
           print(f"Goal: {goal.metric_type}")
           print(f"Target: {goal.target_value} per {goal.target_period}")
           print(f"Progress: {progress.completion_percentage:.1f}%")
           print(f"Current streak: {progress.current_streak} days")
           
           if progress.is_on_track:
               print("✅ On track to meet goal")
           else:
               print("⚠️ Behind target - need improvement")
           print()
   
   # Set up and track goals
   setup_and_track_goals()

Error Handling and Best Practices
---------------------------------

Robust Data Loading
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.data_loader import DataLoader
   from src.utils.error_handler import handle_data_loading_error
   from src.utils.xml_validator import XMLValidator
   
   def safe_data_loading(file_path):
       \"\"\"Safely load health data with proper error handling.\"\"\"
       
       try:
           # Validate XML file first
           validator = XMLValidator()
           validation_result = validator.validate_health_export(file_path)
           
           if not validation_result.is_valid:
               print("Validation errors found:")
               for error in validation_result.errors:
                   print(f"  - {error}")
               return None
           
           # Load data
           loader = DataLoader()
           health_data = loader.load_from_xml(file_path)
           
           print(f"Successfully loaded {len(health_data)} health records")
           return health_data
           
       except FileNotFoundError:
           print(f"Error: File {file_path} not found")
           return None
       except PermissionError:
           print(f"Error: Permission denied accessing {file_path}")
           return None
       except Exception as e:
           handle_data_loading_error(e, context=f"loading {file_path}")
           return None
   
   # Safe data loading
   health_data = safe_data_loading("export.xml")
   if health_data:
       print("Data loaded successfully")
   else:
       print("Failed to load data")

Graceful Analytics Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import DailyMetricsCalculator
   from src.utils.error_handler import handle_analytics_error
   
   def safe_metric_calculation(metric_type, start_date, end_date):
       \"\"\"Calculate metrics with proper error handling.\"\"\"
       
       try:
           calculator = DailyMetricsCalculator(health_db)
           
           # Check data availability first
           if not health_db.has_data_for_date_range(metric_type, start_date, end_date):
               print(f"No data available for {metric_type} in specified range")
               return None
           
           # Calculate metrics
           metrics = calculator.calculate_metrics(metric_type, start_date, end_date)
           
           if not metrics:
               print(f"No metrics calculated for {metric_type}")
               return None
           
           print(f"Successfully calculated {len(metrics)} daily metrics")
           return metrics
           
       except ValueError as e:
           print(f"Invalid parameters: {e}")
           return None
       except Exception as e:
           handle_analytics_error(e, context=f"calculating {metric_type} metrics")
           return None
   
   # Safe metric calculation
   metrics = safe_metric_calculation(
       "HKQuantityTypeIdentifierStepCount",
       start_date,
       end_date
   )

Performance Optimization Examples
--------------------------------

Using Cached Calculators
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import create_cached_daily_calculator, get_cache_manager
   
   # Create cached calculator for better performance
   cached_calculator = create_cached_daily_calculator(health_db)
   
   # First calculation - computed and cached
   start_time = time.time()
   metrics1 = cached_calculator.calculate_metrics(
       "HKQuantityTypeIdentifierStepCount",
       start_date,
       end_date
   )
   first_duration = time.time() - start_time
   
   # Second calculation - returned from cache
   start_time = time.time()
   metrics2 = cached_calculator.calculate_metrics(
       "HKQuantityTypeIdentifierStepCount",
       start_date,
       end_date
   )
   second_duration = time.time() - start_time
   
   print(f"First calculation: {first_duration:.2f}s")
   print(f"Second calculation: {second_duration:.2f}s")
   print(f"Speedup: {first_duration/second_duration:.1f}x")
   
   # Check cache statistics
   cache_manager = get_cache_manager()
   stats = cache_manager.get_cache_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.1%}")

Batch Processing for Large Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytics import OptimizedAnalyticsEngine, AnalyticsRequest
   from analytics import StreamingDataLoader
   
   def process_large_dataset(metric_type, start_date, end_date):
       \"\"\"Process large datasets efficiently.\"\"\"
       
       # Use optimized engine for large datasets
       engine = OptimizedAnalyticsEngine(
           database_path="health.db",
           enable_monitoring=True
       )
       
       # Create analysis request
       request = AnalyticsRequest(
           metric_type=metric_type,
           start_date=start_date,
           end_date=end_date,
           aggregation_level="daily"
       )
       
       # Process with progress monitoring
       def progress_callback(progress):
           print(f"Progress: {progress:.1%}")
       
       # Process request
       results = engine.process_request(request, progress_callback=progress_callback)
       
       return results
   
   # Process large dataset
   large_results = process_large_dataset(
       "HKQuantityTypeIdentifierStepCount",
       date(2020, 1, 1),
       date(2024, 12, 31)
   )

Common Patterns and Utilities
-----------------------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.config import get_config, update_config
   
   # Get current configuration
   config = get_config()
   print(f"Data directory: {config.DATA_DIR}")
   print(f"Cache size: {config.CACHE_SIZE_MB}MB")
   
   # Update configuration
   update_config({
       'CACHE_SIZE_MB': 512,
       'LOG_LEVEL': 'DEBUG',
       'ENABLE_PERFORMANCE_MONITORING': True
   })

Logging and Debugging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.utils.logging_config import setup_logging, get_logger
   
   # Setup logging
   setup_logging(
       level='INFO',
       log_file='health_monitor.log',
       enable_console=True
   )
   
   # Get logger for your module
   logger = get_logger(__name__)
   
   # Use logger throughout your code
   logger.info("Starting health analysis")
   logger.debug(f"Processing {len(metrics)} metrics")
   logger.warning("Low data quality detected")
   logger.error("Failed to calculate trends")

These examples provide a solid foundation for using Apple Health Monitor's features.
For more advanced usage patterns, see the other documentation sections and API reference.