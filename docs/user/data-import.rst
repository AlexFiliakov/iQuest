Data Import Guide
=================

This guide explains how to import Apple Health data into the Apple Health Monitor application.

Overview
--------

Apple Health Monitor supports importing data from Apple Health export files, which contain
your complete health and fitness data in XML format.

Obtaining Apple Health Data
----------------------------

To export your data from Apple Health:

1. Open the **Health** app on your iPhone
2. Tap your profile picture in the top right
3. Scroll down and tap **Export All Health Data**
4. Choose how to share the export file (AirDrop, email, etc.)
5. The export will be a `.zip` file containing `export.xml`

Supported Data Types
--------------------

Apple Health Monitor can import and analyze the following data types:

Health Metrics
~~~~~~~~~~~~~~

* **Activity**: Steps, distance, flights climbed, active energy
* **Heart**: Heart rate, heart rate variability, resting heart rate
* **Body Measurements**: Weight, height, body fat percentage, BMI
* **Sleep**: Sleep analysis, time in bed, sleep stages
* **Nutrition**: Dietary energy, water intake, macro/micronutrients
* **Vitals**: Blood pressure, body temperature, respiratory rate

Workout Data
~~~~~~~~~~~~

* Workout sessions with duration, distance, and energy burned
* Workout routes (if location data is available)
* Heart rate zones during workouts

Health Records
~~~~~~~~~~~~~~

* Clinical data from healthcare providers
* Lab results and medical observations
* Immunization records
* Medication tracking

Import Process
--------------

Using the Application
~~~~~~~~~~~~~~~~~~~~

1. Launch Apple Health Monitor
2. Click **File** → **Import Health Data**
3. Select your Apple Health export file (`.zip` or `export.xml`)
4. Choose import options:

   * **Date Range**: Specify which dates to import
   * **Data Types**: Select specific health metrics
   * **Data Sources**: Choose which apps/devices to include

5. Click **Start Import**
6. Monitor progress in the import dialog
7. Review import summary when complete

Command Line Import
~~~~~~~~~~~~~~~~~~

For advanced users, you can import data using the command line:

.. code-block:: bash

   python -m src.main --import /path/to/export.xml --output health_data.db

Import Options:

.. code-block:: bash

   # Import specific date range
   python -m src.main --import export.xml --start-date 2023-01-01 --end-date 2023-12-31
   
   # Import only specific data types
   python -m src.main --import export.xml --types "steps,heart_rate,sleep"
   
   # Verbose import with progress
   python -m src.main --import export.xml --verbose

Programmatic Import
~~~~~~~~~~~~~~~~~~

For developers, use the DataLoader API:

.. code-block:: python

   from src.data_loader import DataLoader
   from src.database import DatabaseManager
   
   # Initialize components
   loader = DataLoader()
   db = DatabaseManager()
   
   # Load and import data
   health_data = loader.load_from_xml("export.xml")
   
   # Optional: Filter data before import
   filtered_data = loader.filter_by_date_range(
       health_data, 
       start_date="2023-01-01",
       end_date="2023-12-31"
   )
   
   # Import to database
   import_stats = loader.import_to_database(filtered_data, db)
   print(f"Imported {import_stats['records']} health records")

Import Configuration
-------------------

Data Filtering
~~~~~~~~~~~~~

Configure which data to import:

.. code-block:: python

   import_config = {
       'date_range': {
           'start': '2023-01-01',
           'end': '2023-12-31'
       },
       'data_types': [
           'HKQuantityTypeIdentifierStepCount',
           'HKQuantityTypeIdentifierHeartRate',
           'HKCategoryTypeIdentifierSleepAnalysis'
       ],
       'sources': [
           'iPhone',
           'Apple Watch',
           'MyFitnessPal'
       ],
       'exclude_empty': True,
       'deduplicate': True
   }

Performance Settings
~~~~~~~~~~~~~~~~~~~

For large datasets, configure performance options:

.. code-block:: python

   performance_config = {
       'batch_size': 10000,          # Records per batch
       'use_streaming': True,        # Stream large files
       'parallel_processing': True,  # Use multiple cores
       'memory_limit_mb': 512,      # Memory usage limit
       'progress_callback': my_progress_handler
   }

Validation Options
~~~~~~~~~~~~~~~~~

Control data validation during import:

.. code-block:: python

   validation_config = {
       'strict_dates': False,        # Allow invalid dates
       'validate_ranges': True,      # Check value ranges
       'fix_duplicates': True,       # Merge duplicate records
       'log_warnings': True,         # Log validation issues
       'skip_invalid': False         # Stop on validation errors
   }

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~

**Large File Import Timeout**

If importing very large files (>500MB):

.. code-block:: python

   # Increase timeout and use streaming
   loader = DataLoader(
       timeout=3600,      # 1 hour timeout
       use_streaming=True,
       chunk_size=50000
   )

**Memory Issues**

For memory-constrained environments:

.. code-block:: python

   # Reduce memory usage
   loader = DataLoader(
       memory_limit_mb=256,
       batch_size=5000,
       clear_cache_interval=1000
   )

**Encoding Issues**

If the XML file has encoding problems:

.. code-block:: python

   # Try different encodings
   loader = DataLoader()
   try:
       data = loader.load_from_xml("export.xml", encoding="utf-8")
   except UnicodeDecodeError:
       data = loader.load_from_xml("export.xml", encoding="latin-1")

**Corrupted Export Files**

If the Apple Health export appears corrupted:

1. Try re-exporting from Apple Health
2. Verify the ZIP file extracts properly
3. Check that `export.xml` is present and readable
4. Use XML validation to check file structure:

.. code-block:: python

   from src.utils.xml_validator import XMLValidator
   
   validator = XMLValidator()
   result = validator.validate_health_export("export.xml")
   
   if not result.is_valid:
       print("Validation errors:")
       for error in result.errors:
           print(f"  - {error}")

Import Verification
------------------

After importing, verify your data:

.. code-block:: python

   from src.health_database import HealthDatabase
   
   db = HealthDatabase()
   
   # Check overall import stats
   summary = db.get_data_summary()
   print(f"Total records: {summary['total_records']}")
   print(f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
   print(f"Available types: {summary['available_types']}")
   
   # Check specific data types
   types = db.get_available_types()
   for data_type in types:
       count = db.get_record_count_for_type(data_type)
       date_range = db.get_date_range_for_type(data_type)
       print(f"{data_type}: {count} records ({date_range[0]} to {date_range[1]})")

Data Quality Checks
~~~~~~~~~~~~~~~~~~~

Run quality checks on imported data:

.. code-block:: python

   from src.analytics.data_quality import DataQualityChecker
   
   checker = DataQualityChecker(db)
   quality_report = checker.run_comprehensive_check()
   
   # Review quality metrics
   print(f"Completeness: {quality_report.completeness_score}%")
   print(f"Consistency: {quality_report.consistency_score}%")
   print(f"Validity: {quality_report.validity_score}%")
   
   # Check for issues
   if quality_report.issues:
       print("Data quality issues found:")
       for issue in quality_report.issues:
           print(f"  - {issue.severity}: {issue.description}")

Best Practices
--------------

Data Management
~~~~~~~~~~~~~~

1. **Regular Backups**: Backup your health database regularly
2. **Incremental Imports**: Import new data periodically rather than full re-imports
3. **Data Validation**: Always validate imports for data quality
4. **Storage Management**: Monitor database size and archive old data if needed

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~

1. **Batch Processing**: Use appropriate batch sizes for your system
2. **Memory Management**: Set memory limits to prevent system issues
3. **Parallel Processing**: Enable parallel processing for large datasets
4. **Caching**: Use caching for repeated operations

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~

1. **Data Privacy**: Health data is sensitive - use appropriate security measures
2. **Local Storage**: Keep data on local, encrypted storage
3. **Access Control**: Limit access to health databases
4. **Data Retention**: Establish policies for how long to retain imported data

Next Steps
----------

After importing your data:

1. :doc:`analytics-overview` - Learn about available analytics
2. :doc:`visualizations` - Explore visualization options  
3. :doc:`health-scoring` - Understand health scoring system
4. :doc:`export-reporting` - Generate reports from your data