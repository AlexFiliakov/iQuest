"""Apple Health XML to SQLite Data Loader.

This module provides comprehensive functionality for converting Apple Health XML exports
to SQLite databases and performing efficient health data operations. It includes
validation, transaction handling, duplicate prevention, and optimized querying.

The module supports:
    - XML to SQLite conversion with validation and error handling
    - Date range queries with optional type filtering
    - Daily, weekly, and monthly data aggregations
    - CSV to SQLite migration for legacy data
    - Direct CSV loading for UI display
    - Database validation and integrity checking
    - Performance optimization through indexing

Examples:
    Basic XML to SQLite conversion:
        >>> records_imported = convert_xml_to_sqlite(
        ...     "export.xml", 
        ...     "health_data.db"
        ... )
        >>> print(f"Imported {records_imported} records")
        
    Query data for date range:
        >>> df = query_date_range(
        ...     "health_data.db",
        ...     "2024-01-01", 
        ...     "2024-12-31",
        ...     "StepCount"
        ... )
        >>> print(f"Found {len(df)} step records")
        
    Get daily summary:
        >>> summary = get_daily_summary("health_data.db", "StepCount")
        >>> print(summary.head())

Attributes:
    logger: Module-level logger for tracking operations and errors.
"""

import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from src.utils.logging_config import get_logger
from src.utils.error_handler import (
    safe_file_operation, safe_database_operation, 
    DataImportError, DatabaseError, ErrorContext, DataValidationError
)
from src.utils.xml_validator import validate_apple_health_xml, AppleHealthXMLValidator

# Get logger for this module
logger = get_logger(__name__)


def convert_xml_to_sqlite_with_validation(xml_path: str, db_path: str, validate_first: bool = True) -> Tuple[int, str]:
    """Convert Apple Health XML export to SQLite database with comprehensive validation.
    
    This function provides a complete XML to SQLite conversion pipeline with optional
    XML validation, transaction handling, and detailed error reporting. It performs
    duplicate detection and creates optimized database indexes for fast queries.
    
    Args:
        xml_path: Path to the Apple Health export.xml file.
        db_path: Path where the SQLite database will be created.
        validate_first: Whether to validate XML structure before processing.
            Defaults to True for safety.
    
    Returns:
        A tuple containing:
            - int: Number of new records imported (excludes duplicates)
            - str: Validation summary message with statistics
    
    Raises:
        DataValidationError: If XML validation fails with detailed error information.
        FileNotFoundError: If the XML file doesn't exist at the specified path.
        ET.ParseError: If XML structure is malformed or corrupted.
        sqlite3.Error: If database operations fail during import.
        DatabaseError: If transaction rollback occurs due to errors.
        
    Examples:
        >>> count, summary = convert_xml_to_sqlite_with_validation(
        ...     "/path/to/export.xml",
        ...     "/path/to/health.db"
        ... )
        >>> print(f"Imported {count} records")
        >>> print(summary)
        
        Skip validation for trusted files:
        >>> count, summary = convert_xml_to_sqlite_with_validation(
        ...     "export.xml",
        ...     "health.db",
        ...     validate_first=False
        ... )
    """
    validation_summary = ""
    
    # Step 1: Validate XML file if requested
    if validate_first:
        logger.info("Validating XML file before import...")
        validation_result = validate_apple_health_xml(xml_path)
        
        validator = AppleHealthXMLValidator()
        validation_summary = validator.get_user_friendly_summary(validation_result)
        
        if not validation_result.is_valid:
            logger.error(f"XML validation failed: {len(validation_result.errors)} errors")
            raise DataValidationError(f"XML validation failed with {len(validation_result.errors)} errors. " + 
                                    validation_summary)
        
        logger.info(f"XML validation successful: {validation_result.record_count:,} records")
    
    # Step 2: Import with transaction handling
    with ErrorContext("XML to SQLite conversion with transaction handling"):
        return _convert_xml_with_transaction(xml_path, db_path), validation_summary


def _convert_xml_with_transaction(xml_path: str, db_path: str) -> int:
    """Handle XML conversion with comprehensive transaction management.
    
    Internal function that performs the actual XML parsing and database import
    with proper transaction handling, rollback on errors, and duplicate prevention.
    Creates optimized indexes and metadata tables for performance.
    
    Args:
        xml_path: Path to the validated Apple Health XML file.
        db_path: Path where the SQLite database will be created.
        
    Returns:
        Number of new records successfully imported to the database.
        
    Raises:
        FileNotFoundError: If XML file doesn't exist.
        DataValidationError: If no health records found in XML.
        ET.ParseError: If XML parsing fails.
        DatabaseError: If database transaction fails and rolls back.
        
    Note:
        This is an internal function and should not be called directly.
        Use convert_xml_to_sqlite_with_validation() instead.
    """
    # Validate input paths
    if not Path(xml_path).exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    conn = None
    try:
        # Parse XML file
        logger.info(f"Parsing XML file: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract all health records
        record_list = [x.attrib for x in root.iter('Record')]
        record_data = pd.DataFrame(record_list)
        
        if record_data.empty:
            raise DataValidationError("No health records found in XML file")
        
        logger.info(f"Extracted {len(record_data)} records from XML")
        
        # Convert date columns to datetime
        date_cols = ['creationDate', 'startDate', 'endDate']
        for col in date_cols:
            if col in record_data.columns:
                try:
                    record_data[col] = pd.to_datetime(record_data[col])
                except Exception as e:
                    logger.warning(f"Could not convert {col} to datetime: {e}")
        
        # Convert value to numeric
        if 'value' in record_data.columns:
            record_data['value'] = pd.to_numeric(record_data['value'], errors='coerce')
            # Fill NaN values with 1.0 for categorical data (e.g., sleep analysis)
            record_data['value'] = record_data['value'].fillna(1.0)
        
        # Clean type names
        if 'type' in record_data.columns:
            record_data['type'] = record_data['type'].str.replace('HKQuantityTypeIdentifier', '')
            record_data['type'] = record_data['type'].str.replace('HKCategoryTypeIdentifier', '')
        
        # Start database transaction
        logger.info(f"Creating SQLite database with transaction: {db_path}")
        conn = sqlite3.connect(db_path)
        
        # Begin explicit transaction
        conn.execute('BEGIN IMMEDIATE')
        
        try:
            # Store data using INSERT OR IGNORE to prevent duplicates
            # First ensure the table exists with unique constraint
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    type TEXT,
                    sourceName TEXT,
                    sourceVersion TEXT,
                    device TEXT,
                    unit TEXT,
                    creationDate TEXT,
                    startDate TEXT,
                    endDate TEXT,
                    value REAL,
                    UNIQUE(type, sourceName, startDate, endDate, value)
                )
            """)
            
            # Insert records one by one with INSERT OR IGNORE
            records_inserted = 0
            for _, row in record_data.iterrows():
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO health_records 
                        (type, sourceName, sourceVersion, device, unit, creationDate, startDate, endDate, value)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('type', ''),
                        row.get('sourceName', ''),
                        row.get('sourceVersion', ''),
                        row.get('device', ''),
                        row.get('unit', ''),
                        str(row.get('creationDate', '')) if pd.notna(row.get('creationDate')) else '',
                        str(row.get('startDate', '')) if pd.notna(row.get('startDate')) else '',
                        str(row.get('endDate', '')) if pd.notna(row.get('endDate')) else '',
                        row.get('value', 1.0)
                    ))
                    if conn.total_changes > records_inserted:
                        records_inserted = conn.total_changes
                except Exception as e:
                    logger.warning(f"Failed to insert record: {e}")
            
            # Log import results
            total_count = conn.execute('SELECT COUNT(*) FROM health_records').fetchone()[0]
            logger.info(f"Import complete: {records_inserted} new records added, {total_count} total records in database")
            
            # Create indexes for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_creation_date ON health_records(creationDate)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON health_records(sourceName)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON health_records(sourceName, type)')
            
            # Create metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute("INSERT OR REPLACE INTO metadata VALUES ('import_date', datetime('now'))")
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('record_count', '{records_inserted}')")
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('source_file', '{xml_path}')")
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully imported {records_inserted} new records (skipped {len(record_data) - records_inserted} duplicates)")
            
            return records_inserted
            
        except Exception as e:
            # Rollback transaction on any error
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseError(f"Database import failed and was rolled back: {e}")
    
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise DataImportError(f"XML parsing failed: {e}")
    except DatabaseError:
        # DatabaseError already handles rollback, just re-raise
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        if conn:
            try:
                conn.rollback()
                logger.info("Transaction rolled back due to unexpected error")
            except:
                pass
        raise
    finally:
        if conn:
            conn.close()


def convert_xml_to_sqlite(xml_path: str, db_path: str) -> int:
    """Convert Apple Health XML export to SQLite database with basic error handling.
    
    This is a simplified version of the conversion function without XML validation.
    It provides basic XML to SQLite conversion with duplicate prevention and
    performance optimizations through indexing.
    
    Args:
        xml_path: Path to the Apple Health export.xml file.
        db_path: Path where the SQLite database will be created.
        
    Returns:
        Number of new records imported (excludes duplicates).
        
    Raises:
        FileNotFoundError: If XML file doesn't exist at the specified path.
        ET.ParseError: If XML structure is malformed.
        sqlite3.Error: If database operations fail.
        
    Examples:
        >>> records_count = convert_xml_to_sqlite(
        ...     "health_export.xml",
        ...     "my_health_data.db"
        ... )
        >>> print(f"Successfully imported {records_count} records")
        
    Note:
        For production use, consider using convert_xml_to_sqlite_with_validation()
        which includes comprehensive validation and better error reporting.
    """
    # Validate input paths
    if not Path(xml_path).exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    try:
        # Parse XML file
        logger.info(f"Parsing XML file: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise
    
    try:
        # Extract all health records
        record_list = [x.attrib for x in root.iter('Record')]
        record_data = pd.DataFrame(record_list)
        
        # Convert date columns to datetime
        date_cols = ['creationDate', 'startDate', 'endDate']
        for col in date_cols:
            if col in record_data.columns:
                record_data[col] = pd.to_datetime(record_data[col])
        
        # Convert value to numeric
        record_data['value'] = pd.to_numeric(record_data['value'], errors='coerce')
        # Fill NaN values with 1.0 for categorical data (e.g., sleep analysis)
        record_data['value'] = record_data['value'].fillna(1.0)
        
        # Clean type names
        record_data['type'] = record_data['type'].str.replace('HKQuantityTypeIdentifier', '')
        record_data['type'] = record_data['type'].str.replace('HKCategoryTypeIdentifier', '')
        
        # Create SQLite database with indexes
        logger.info(f"Creating SQLite database: {db_path}")
        with sqlite3.connect(db_path) as conn:
            # Create table with unique constraint
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    type TEXT,
                    sourceName TEXT,
                    sourceVersion TEXT,
                    device TEXT,
                    unit TEXT,
                    creationDate TEXT,
                    startDate TEXT,
                    endDate TEXT,
                    value REAL,
                    UNIQUE(type, sourceName, startDate, endDate, value)
                )
            """)
            
            # Insert records using INSERT OR IGNORE
            records_inserted = 0
            for _, row in record_data.iterrows():
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO health_records 
                        (type, sourceName, sourceVersion, device, unit, creationDate, startDate, endDate, value)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('type', ''),
                        row.get('sourceName', ''),
                        row.get('sourceVersion', ''),
                        row.get('device', ''),
                        row.get('unit', ''),
                        str(row.get('creationDate', '')) if pd.notna(row.get('creationDate')) else '',
                        str(row.get('startDate', '')) if pd.notna(row.get('startDate')) else '',
                        str(row.get('endDate', '')) if pd.notna(row.get('endDate')) else '',
                        row.get('value', 1.0)
                    ))
                    if conn.total_changes > records_inserted:
                        records_inserted = conn.total_changes
                except Exception as e:
                    logger.warning(f"Failed to insert record: {e}")
            
            # Create indexes for fast queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_creation_date ON health_records(creationDate)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON health_records(sourceName)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON health_records(sourceName, type)')
            
            # Create metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute("INSERT OR REPLACE INTO metadata VALUES ('import_date', datetime('now'))")
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('record_count', '{records_inserted}')")
            
        logger.info(f"Successfully imported {records_inserted} new records (skipped {len(record_data) - records_inserted} duplicates)")
        return records_inserted
    except sqlite3.Error as e:
        logger.error(f"Database error during conversion: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise


def query_date_range(db_path: str, start_date: str, end_date: str, 
                     record_type: str = None) -> pd.DataFrame:
    """Query health records within a specified date range with optional type filtering.
    
    Efficiently retrieves health records from the SQLite database using optimized
    indexes. Automatically parses date columns and supports filtering by specific
    health metric types for focused analysis.
    
    Args:
        db_path: Path to the SQLite database file.
        start_date: Start date in YYYY-MM-DD format (inclusive).
        end_date: End date in YYYY-MM-DD format (inclusive).
        record_type: Optional health metric type to filter (e.g., 'StepCount',
            'HeartRate'). If None, returns all record types.
            
    Returns:
        DataFrame containing matching health records with columns:
            - type: Health metric type
            - sourceName: Source device/app name
            - sourceVersion: Version of the source
            - device: Device identifier
            - unit: Measurement unit
            - creationDate: When record was created (parsed as datetime)
            - startDate: When measurement started (parsed as datetime)
            - endDate: When measurement ended (parsed as datetime)
            - value: Measured value (numeric)
            
    Examples:
        Get all records for January 2024:
        >>> df = query_date_range(
        ...     "health.db",
        ...     "2024-01-01",
        ...     "2024-01-31"
        ... )
        
        Get only step count data:
        >>> steps_df = query_date_range(
        ...     "health.db",
        ...     "2024-01-01",
        ...     "2024-01-31",
        ...     "StepCount"
        ... )
    """
    conn = sqlite3.connect(db_path)
    try:
        if record_type:
            query = '''
                SELECT * FROM health_records 
                WHERE creationDate BETWEEN ? AND ?
                AND type = ?
            '''
            params = [start_date, end_date, record_type]
        else:
            query = '''
                SELECT * FROM health_records 
                WHERE creationDate BETWEEN ? AND ?
            '''
            params = [start_date, end_date]
        
        df = pd.read_sql(query, conn, params=params, 
                       parse_dates=['creationDate', 'startDate', 'endDate'])
        return df
    finally:
        conn.close()


def get_daily_summary(db_path: str, record_type: str) -> pd.DataFrame:
    """Generate daily aggregated statistics for a specific health metric.
    
    Computes comprehensive daily statistics including count, average, minimum,
    maximum, and total values for the specified health metric type. Results
    are ordered chronologically for time series analysis.
    
    Args:
        db_path: Path to the SQLite database file.
        record_type: Health metric type identifier (e.g., 'StepCount', 'HeartRate',
            'DistanceWalkingRunning'). Must be a non-empty string.
            
    Returns:
        DataFrame with daily aggregations containing columns:
            - date: Date of the aggregation (parsed as datetime)
            - count: Number of records for that day
            - avg_value: Average value for the day
            - min_value: Minimum value recorded
            - max_value: Maximum value recorded
            - total_value: Sum of all values for the day
            
    Raises:
        sqlite3.Error: If database connection or query execution fails.
        ValueError: If record_type is None, empty, or not a string.
        
    Examples:
        Get daily step count summaries:
        >>> daily_steps = get_daily_summary("health.db", "StepCount")
        >>> print(f"Average daily steps: {daily_steps['avg_value'].mean():.0f}")
        
        Analyze heart rate patterns:
        >>> daily_hr = get_daily_summary("health.db", "HeartRate")
        >>> print(f"Highest daily average HR: {daily_hr['avg_value'].max():.1f} bpm")
    """
    # Validate input
    if not record_type or not isinstance(record_type, str):
        raise ValueError("record_type must be a non-empty string")
    
    try:
        with sqlite3.connect(db_path) as conn:
            query = '''
                SELECT DATE(creationDate) as date,
                       COUNT(*) as count,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       SUM(value) as total_value
                FROM health_records
                WHERE type = ?
                GROUP BY DATE(creationDate)
                ORDER BY date
            '''
            return pd.read_sql(query, conn, params=[record_type], 
                             parse_dates=['date'])
    except sqlite3.Error as e:
        logger.error(f"Database error in get_daily_summary: {e}")
        raise


def get_weekly_summary(db_path: str, record_type: str) -> pd.DataFrame:
    """Generate weekly aggregated statistics for a specific health metric.
    
    Computes weekly statistics by grouping records using ISO week format (YYYY-WW).
    Provides comprehensive aggregations including count, average, minimum, maximum,
    and total values for analyzing weekly patterns and trends.
    
    Args:
        db_path: Path to the SQLite database file.
        record_type: Health metric type identifier (e.g., 'StepCount', 'HeartRate').
            Must be a non-empty string.
            
    Returns:
        DataFrame with weekly aggregations containing columns:
            - week: Week identifier in YYYY-WW format (e.g., '2024-15')
            - count: Number of records for that week
            - avg_value: Average value for the week
            - min_value: Minimum value recorded during the week
            - max_value: Maximum value recorded during the week
            - total_value: Sum of all values for the week
            
    Raises:
        sqlite3.Error: If database connection or query execution fails.
        ValueError: If record_type is None, empty, or not a string.
        
    Examples:
        Analyze weekly step patterns:
        >>> weekly_steps = get_weekly_summary("health.db", "StepCount")
        >>> weekly_steps['avg_daily'] = weekly_steps['total_value'] / 7
        >>> print(weekly_steps[['week', 'avg_daily']].head())
        
        Compare weekly workout intensities:
        >>> weekly_workouts = get_weekly_summary("health.db", "ActiveEnergyBurned")
        >>> print(f"Most active week: {weekly_workouts.loc[weekly_workouts['total_value'].idxmax(), 'week']}")
    """
    # Validate input
    if not record_type or not isinstance(record_type, str):
        raise ValueError("record_type must be a non-empty string")
    
    try:
        with sqlite3.connect(db_path) as conn:
            query = '''
                SELECT strftime('%Y-%W', creationDate) as week,
                       COUNT(*) as count,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       SUM(value) as total_value
                FROM health_records
                WHERE type = ?
                GROUP BY week
                ORDER BY week
            '''
            return pd.read_sql(query, conn, params=[record_type])
    except sqlite3.Error as e:
        logger.error(f"Database error in get_weekly_summary: {e}")
        raise


def get_monthly_summary(db_path: str, record_type: str) -> pd.DataFrame:
    """Generate monthly aggregated statistics for a specific health metric.
    
    Computes monthly statistics by grouping records using YYYY-MM format.
    Ideal for long-term trend analysis and seasonal pattern identification.
    Provides comprehensive aggregations for understanding monthly health patterns.
    
    Args:
        db_path: Path to the SQLite database file.
        record_type: Health metric type identifier (e.g., 'StepCount', 'HeartRate').
            Must be a non-empty string.
            
    Returns:
        DataFrame with monthly aggregations containing columns:
            - month: Month identifier in YYYY-MM format (e.g., '2024-03')
            - count: Number of records for that month
            - avg_value: Average value for the month
            - min_value: Minimum value recorded during the month
            - max_value: Maximum value recorded during the month
            - total_value: Sum of all values for the month
            
    Raises:
        sqlite3.Error: If database connection or query execution fails.
        ValueError: If record_type is None, empty, or not a string.
        
    Examples:
        Track monthly activity trends:
        >>> monthly_steps = get_monthly_summary("health.db", "StepCount")
        >>> monthly_steps['avg_daily'] = monthly_steps['total_value'] / 30  # Rough estimate
        >>> print("Monthly step trends:")
        >>> print(monthly_steps[['month', 'avg_daily']])
        
        Analyze seasonal heart rate variations:
        >>> monthly_hr = get_monthly_summary("health.db", "HeartRate")
        >>> seasonal_hr = monthly_hr.groupby(monthly_hr['month'].str[-2:])['avg_value'].mean()
        >>> print("Average HR by month:", seasonal_hr)
    """
    # Validate input
    if not record_type or not isinstance(record_type, str):
        raise ValueError("record_type must be a non-empty string")
    
    try:
        with sqlite3.connect(db_path) as conn:
            query = '''
                SELECT strftime('%Y-%m', creationDate) as month,
                       COUNT(*) as count,
                       AVG(value) as avg_value,
                       MIN(value) as min_value,
                       MAX(value) as max_value,
                       SUM(value) as total_value
                FROM health_records
                WHERE type = ?
                GROUP BY month
                ORDER BY month
            '''
            return pd.read_sql(query, conn, params=[record_type])
    except sqlite3.Error as e:
        logger.error(f"Database error in get_monthly_summary: {e}")
        raise


def get_available_types(db_path: str) -> List[str]:
    """Retrieve all unique health record types available in the database.
    
    Efficiently queries the database to return a sorted list of all health metric
    types present in the health_records table. Useful for populating UI filters
    and understanding what types of health data are available for analysis.
    
    Args:
        db_path: Path to the SQLite database file.
        
    Returns:
        Sorted list of unique health record type names (e.g., ['HeartRate',
        'StepCount', 'DistanceWalkingRunning']). Returns empty list if no
        records exist or database is inaccessible.
        
    Raises:
        sqlite3.Error: If database connection fails or query execution errors.
        
    Examples:
        Get all available metric types:
        >>> types = get_available_types("health.db")
        >>> print(f"Available metrics: {', '.join(types)}")
        
        Check if specific metric exists:
        >>> available_types = get_available_types("health.db")
        >>> if 'BloodPressureSystolic' in available_types:
        ...     print("Blood pressure data is available")
    """
    conn = sqlite3.connect(db_path)
    try:
        query = 'SELECT DISTINCT type FROM health_records ORDER BY type'
        result = conn.execute(query).fetchall()
        return [row[0] for row in result]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_available_types: {e}")
        raise
    finally:
        conn.close()


def get_date_range(db_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Determine the complete date range of health data in the database.
    
    Efficiently queries the database to find the earliest and latest creation
    dates across all health records. Useful for setting appropriate date range
    limits in UI components and understanding data coverage.
    
    Args:
        db_path: Path to the SQLite database file.
        
    Returns:
        Tuple containing:
            - str or None: Earliest creation date in ISO format (YYYY-MM-DD HH:MM:SS)
            - str or None: Latest creation date in ISO format (YYYY-MM-DD HH:MM:SS)
        Returns (None, None) if no records exist in the database.
        
    Raises:
        sqlite3.Error: If database connection fails or query execution errors.
        
    Examples:
        Check data coverage:
        >>> min_date, max_date = get_date_range("health.db")
        >>> if min_date and max_date:
        ...     print(f"Data spans from {min_date} to {max_date}")
        ... else:
        ...     print("No health data found")
        
        Set UI date limits:
        >>> start, end = get_date_range("health.db")
        >>> if start:
        ...     # Use dates to configure date picker widgets
        ...     pass
    """
    conn = sqlite3.connect(db_path)
    try:
        query = '''
            SELECT MIN(creationDate) as min_date, 
                   MAX(creationDate) as max_date 
            FROM health_records
        '''
        result = conn.execute(query).fetchone()
        return result if result else (None, None)
    except sqlite3.Error as e:
        logger.error(f"Database error in get_date_range: {e}")
        raise
    finally:
        conn.close()


def migrate_csv_to_sqlite(csv_path: str, db_path: str) -> int:
    """Migrate existing CSV health data to optimized SQLite format.
    
    Converts CSV files (typically exported from previous versions or other tools)
    to the standardized SQLite database format. Creates performance indexes and
    metadata tables for optimal query performance.
    
    Args:
        csv_path: Path to the CSV file containing health data. Expected to have
            columns: type, sourceName, sourceVersion, device, unit, creationDate,
            startDate, endDate, value.
        db_path: Path where the SQLite database will be created. Overwrites
            existing files.
            
    Returns:
        Number of records successfully migrated to the database.
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist at the specified path.
        sqlite3.Error: If database creation or data insertion fails.
        pd.errors.ParserError: If the CSV file is malformed or has invalid structure.
        
    Examples:
        Migrate legacy CSV data:
        >>> count = migrate_csv_to_sqlite(
        ...     "legacy_health_data.csv",
        ...     "migrated_health.db"
        ... )
        >>> print(f"Successfully migrated {count} records")
        
        Batch migration:
        >>> import glob
        >>> for csv_file in glob.glob("*.csv"):
        ...     db_file = csv_file.replace(".csv", ".db")
        ...     records = migrate_csv_to_sqlite(csv_file, db_file)
        ...     print(f"{csv_file}: {records} records")
    """
    # Validate input paths
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        logger.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=['creationDate'])
        
        logger.info(f"Creating SQLite database: {db_path}")
        with sqlite3.connect(db_path) as conn:
            df.to_sql('health_records', conn, index=False, if_exists='replace')
            
            # Add same indexes as XML import
            conn.execute('CREATE INDEX idx_creation_date ON health_records(creationDate)')
            conn.execute('CREATE INDEX idx_type ON health_records(type)')
            conn.execute('CREATE INDEX idx_type_date ON health_records(type, creationDate)')
            
            # Create metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute("INSERT OR REPLACE INTO metadata VALUES ('import_date', datetime('now'))")
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('record_count', '{len(df)}')")
        
        logger.info(f"Successfully migrated {len(df)} records")
        return len(df)
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV file: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        raise


def validate_database(db_path: str) -> dict:
    """Perform comprehensive validation of SQLite database integrity.
    
    Checks database structure, table existence, index presence, and data integrity.
    Provides detailed validation results for troubleshooting and quality assurance.
    Essential for verifying successful imports and database health.
    
    Args:
        db_path: Path to the SQLite database file to validate.
        
    Returns:
        Dictionary containing validation results with keys:
            - 'exists' (bool): Whether the database file exists
            - 'has_health_records' (bool): Whether health_records table exists
            - 'has_indexes' (bool): Whether required performance indexes exist
            - 'record_count' (int): Total number of health records
            - 'has_metadata' (bool): Whether metadata table exists
            - 'errors' (list): List of validation error messages
            
    Examples:
        Validate database after import:
        >>> validation = validate_database("health.db")
        >>> if validation['errors']:
        ...     print("Validation errors:", validation['errors'])
        ... else:
        ...     print(f"Database valid with {validation['record_count']} records")
        
        Check database health:
        >>> result = validate_database("health.db")
        >>> health_score = sum([
        ...     result['exists'],
        ...     result['has_health_records'],
        ...     result['has_indexes'],
        ...     result['has_metadata']
        ... ]) / 4 * 100
        >>> print(f"Database health: {health_score:.0f}%")
    """
    validation_results = {
        'exists': Path(db_path).exists(),
        'has_health_records': False,
        'has_indexes': False,
        'record_count': 0,
        'has_metadata': False,
        'errors': []
    }
    
    if not validation_results['exists']:
        validation_results['errors'].append('Database file does not exist')
        return validation_results
    
    conn = sqlite3.connect(db_path)
    try:
        # Check for health_records table
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        
        if 'health_records' in table_names:
            validation_results['has_health_records'] = True
            
            # Get record count
            count = conn.execute(
                'SELECT COUNT(*) FROM health_records'
            ).fetchone()[0]
            validation_results['record_count'] = count
            
            # Check indexes
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
            index_names = [i[0] for i in indexes]
            
            required_indexes = ['idx_creation_date', 'idx_type', 'idx_type_date']
            if all(idx in index_names for idx in required_indexes):
                validation_results['has_indexes'] = True
            else:
                validation_results['errors'].append('Missing required indexes')
        else:
            validation_results['errors'].append('health_records table not found')
        
        # Check metadata table
        if 'metadata' in table_names:
            validation_results['has_metadata'] = True
            
    except Exception as e:
        validation_results['errors'].append(f'Database error: {str(e)}')
    finally:
        conn.close()
    
    return validation_results


class DataLoader:
    """Comprehensive data loader for health data from CSV files and SQLite databases.
    
    Provides unified interface for loading health data from various sources with
    automatic data cleaning, type conversion, and error handling. Optimized for
    performance with SQL-based aggregations and statistics computation.
    
    Features:
        - CSV file loading with automatic date parsing
        - SQLite database integration with optimized queries
        - In-memory data cleaning and standardization
        - Statistical analysis using SQL aggregations
        - Filter options extraction for UI components
        - Type inference for missing source information
        
    Attributes:
        logger: Logger instance for tracking operations and errors.
        db_path: Path to the currently connected SQLite database.
        
    Examples:
        Basic usage:
        >>> loader = DataLoader()
        >>> loader.db_path = "health.db"
        >>> df = loader.get_all_records()
        >>> stats = loader.get_statistics_summary()
        
        Load CSV data:
        >>> loader = DataLoader()
        >>> df = loader.load_csv("health_export.csv")
        >>> print(f"Loaded {len(df)} records")
    """
    
    def __init__(self):
        """Initialize the DataLoader with logging configuration.
        
        Sets up the logger and initializes the database path to None.
        The database path must be set before using database-related methods.
        """
        self.logger = get_logger(__name__)
        self.db_path = None
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load and process CSV health data with automatic cleaning and standardization.
        
        Reads CSV files with automatic date parsing, data type conversion, and
        standardization. Handles common data quality issues and applies consistent
        formatting for downstream analysis.
        
        Args:
            file_path: Path to the CSV file containing health data.
            
        Returns:
            DataFrame with processed health data containing standardized columns:
                - creationDate, startDate, endDate: Parsed as datetime objects
                - value: Converted to numeric, NaN filled with 1.0
                - type: Cleaned health metric type names
                - Other columns preserved as-is
                
        Raises:
            FileNotFoundError: If CSV file doesn't exist at the specified path.
            DataImportError: If CSV parsing fails or data processing errors occur.
            
        Examples:
            Load health data from CSV:
            >>> loader = DataLoader()
            >>> df = loader.load_csv("exported_health_data.csv")
            >>> print(f"Loaded {len(df)} records")
            >>> print(f"Date range: {df['creationDate'].min()} to {df['creationDate'].max()}")
            
            Handle loading errors:
            >>> try:
            ...     df = loader.load_csv("data.csv")
            ... except DataImportError as e:
            ...     print(f"Failed to load CSV: {e}")
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            self.logger.info(f"Loading CSV file: {file_path}")
            
            # Read CSV with common date columns parsed
            df = pd.read_csv(
                file_path,
                parse_dates=['creationDate', 'startDate', 'endDate'],
                date_parser=pd.to_datetime,
                on_bad_lines='skip'
            )
            
            # Convert value column to numeric if it exists
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['value'] = df['value'].fillna(1.0)
            
            # Clean type names if they exist
            if 'type' in df.columns:
                df['type'] = df['type'].str.replace('HKQuantityTypeIdentifier', '')
                df['type'] = df['type'].str.replace('HKCategoryTypeIdentifier', '')
            
            self.logger.info(f"Successfully loaded {len(df)} records from CSV")
            return df
            
        except pd.errors.ParserError as e:
            self.logger.error(f"Failed to parse CSV file: {e}")
            raise DataImportError(f"Failed to parse CSV file: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error loading CSV: {e}")
            raise DataImportError(f"Unexpected error loading CSV: {str(e)}") from e
    
    def get_all_records(self) -> pd.DataFrame:
        """Retrieve all health records from the SQLite database with data processing.
        
        Loads all health records from the database with automatic date parsing,
        data type conversion, and missing column handling for backward compatibility.
        Returns an empty DataFrame with expected columns if no data exists.
        
        Returns:
            DataFrame containing all health records with columns:
                - type, sourceName, sourceVersion, device, unit: String data
                - creationDate, startDate, endDate: Parsed datetime objects
                - value: Numeric values with NaN filled as 1.0
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query fails or data processing errors occur.
            
        Examples:
            Load all data for analysis:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> df = loader.get_all_records()
            >>> print(f"Total records: {len(df)}")
            >>> print(f"Available types: {df['type'].nunique()}")
            
            Check for data availability:
            >>> df = loader.get_all_records()
            >>> if df.empty:
            ...     print("No health data available")
            ... else:
            ...     print(f"Data from {df['creationDate'].min()} to {df['creationDate'].max()}")
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info(f"Loading all records from database: {self.db_path}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if health_records table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='health_records'
            """)
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                self.logger.warning("health_records table does not exist. Creating empty DataFrame.")
                conn.close()
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    'type', 'sourceName', 'sourceVersion', 'device', 'unit',
                    'creationDate', 'startDate', 'endDate', 'value'
                ])
            
            df = pd.read_sql(
                "SELECT * FROM health_records",
                conn,
                parse_dates=['creationDate', 'startDate', 'endDate']
            )
            conn.close()
            
            # Convert value column to numeric if it exists
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df['value'] = df['value'].fillna(1.0)
            
            # Add sourceName column if it doesn't exist (for compatibility)
            if 'sourceName' not in df.columns and 'type' in df.columns:
                # Try to infer source from type
                df['sourceName'] = df['type'].apply(self._infer_source_name)
            
            self.logger.info(f"Successfully loaded {len(df)} records from database")
            return df
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise DataImportError(f"Failed to load from database: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error loading from database: {e}")
            raise DataImportError(f"Unexpected error: {str(e)}") from e
    
    def _infer_source_name(self, record_type: str) -> str:
        """Infer likely source device name from health record type.
        
        Provides fallback source name inference for records missing sourceName
        information, based on common patterns in Apple Health data.
        
        Args:
            record_type: Health metric type name (e.g., 'StepCount', 'HeartRate').
            
        Returns:
            Inferred source name based on record type patterns:
                - 'iPhone': For step, distance, and stair climbing metrics
                - 'Apple Watch': For heart rate, workout, and exercise metrics
                - 'Sleep Apps': For sleep-related metrics
                - 'Other Apps': For unrecognized types
                
        Examples:
            >>> loader = DataLoader()
            >>> print(loader._infer_source_name('StepCount'))  # 'iPhone'
            >>> print(loader._infer_source_name('HeartRate'))  # 'Apple Watch'
            >>> print(loader._infer_source_name('SleepAnalysis'))  # 'Sleep Apps'
        """
        # Common mappings
        if any(x in record_type.lower() for x in ['step', 'distance', 'flight']):
            return "iPhone"
        elif any(x in record_type.lower() for x in ['heart', 'workout', 'exercise']):
            return "Apple Watch"
        elif 'sleep' in record_type.lower():
            return "Sleep Apps"
        else:
            return "Other Apps"
    
    def get_statistics_summary(self) -> dict:
        """Compute comprehensive database statistics using optimized SQL aggregations.
        
        Efficiently calculates summary statistics directly in the database without
        loading all records into memory. Provides essential information about data
        coverage, diversity, and temporal span for UI display and analysis planning.
        
        Returns:
            Dictionary containing comprehensive statistics:
                - 'total_records' (int): Total number of health records
                - 'unique_types' (int): Number of distinct health metric types
                - 'unique_sources' (int): Number of distinct source devices/apps
                - 'date_range' (tuple): (earliest_date, latest_date) as strings or (None, None)
                - 'last_updated' (datetime): When these statistics were computed
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query execution fails.
            
        Examples:
            Get database overview:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> stats = loader.get_statistics_summary()
            >>> print(f"Database contains {stats['total_records']:,} records")
            >>> print(f"Covering {stats['unique_types']} metric types")
            >>> print(f"From {stats['unique_sources']} different sources")
            
            Check data freshness:
            >>> stats = loader.get_statistics_summary()
            >>> if stats['date_range'][1]:  # Latest date exists
            ...     latest = stats['date_range'][1]
            ...     print(f"Most recent data: {latest}")
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info("Computing statistics summary using SQL aggregation")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if health_records table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='health_records'
            """)
            if not cursor.fetchone():
                self.logger.warning("health_records table does not exist")
                return {
                    'total_records': 0,
                    'unique_types': 0,
                    'unique_sources': 0,
                    'date_range': (None, None),
                    'last_updated': datetime.now()
                }
            
            # Get all statistics in a single efficient query
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT type) as unique_types,
                    COUNT(DISTINCT sourceName) as unique_sources,
                    MIN(creationDate) as earliest_date,
                    MAX(creationDate) as latest_date
                FROM health_records
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'total_records': result[0] or 0,
                'unique_types': result[1] or 0,
                'unique_sources': result[2] or 0,
                'date_range': (result[3], result[4]) if result[3] and result[4] else (None, None),
                'last_updated': datetime.now()
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error computing statistics: {e}")
            raise DataImportError(f"Failed to compute statistics: {str(e)}") from e
    
    def get_type_counts(self) -> pd.DataFrame:
        """Generate record counts and percentages by health metric type.
        
        Efficiently computes the distribution of health records across different
        metric types using SQL aggregation. Results are sorted by count in descending
        order for easy identification of most common metrics.
        
        Returns:
            DataFrame with record type distribution containing columns:
                - 'type' (str): Health metric type name
                - 'count' (int): Number of records for this type
                - 'percentage' (float): Percentage of total records (rounded to 1 decimal)
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query execution fails.
            
        Examples:
            Analyze metric distribution:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> type_counts = loader.get_type_counts()
            >>> print("Top 5 most common metrics:")
            >>> print(type_counts.head())
            
            Find rare metrics:
            >>> type_counts = loader.get_type_counts()
            >>> rare_metrics = type_counts[type_counts['percentage'] < 1.0]
            >>> print(f"Found {len(rare_metrics)} rare metric types")
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info("Getting type counts using SQL aggregation")
            
            conn = sqlite3.connect(self.db_path)
            
            # Get counts by type
            df = pd.read_sql("""
                SELECT 
                    type,
                    COUNT(*) as count
                FROM health_records
                GROUP BY type
                ORDER BY count DESC
            """, conn)
            
            # Get total for percentage calculation
            total = df['count'].sum() if not df.empty else 1
            df['percentage'] = (df['count'] / total * 100).round(1)
            
            conn.close()
            return df
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting type counts: {e}")
            raise DataImportError(f"Failed to get type counts: {str(e)}") from e
    
    def get_source_counts(self) -> pd.DataFrame:
        """Generate record counts and percentages by source device or application.
        
        Efficiently computes the distribution of health records across different
        source devices and applications using SQL aggregation. Helps identify
        primary data sources and their relative contributions.
        
        Returns:
            DataFrame with source distribution containing columns:
                - 'sourceName' (str): Source device or application name
                - 'count' (int): Number of records from this source
                - 'percentage' (float): Percentage of total records (rounded to 1 decimal)
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query execution fails.
            
        Examples:
            Identify main data sources:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> source_counts = loader.get_source_counts()
            >>> print("Data sources by contribution:")
            >>> print(source_counts)
            
            Check device diversity:
            >>> source_counts = loader.get_source_counts()
            >>> print(f"Data collected from {len(source_counts)} different sources")
            >>> primary_source = source_counts.iloc[0]
            >>> print(f"Primary source: {primary_source['sourceName']} ({primary_source['percentage']:.1f}%)")
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info("Getting source counts using SQL aggregation")
            
            conn = sqlite3.connect(self.db_path)
            
            # Get counts by source
            df = pd.read_sql("""
                SELECT 
                    sourceName,
                    COUNT(*) as count
                FROM health_records
                GROUP BY sourceName
                ORDER BY count DESC
            """, conn)
            
            # Get total for percentage calculation
            total = df['count'].sum() if not df.empty else 1
            df['percentage'] = (df['count'] / total * 100).round(1)
            
            conn.close()
            return df
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting source counts: {e}")
            raise DataImportError(f"Failed to get source counts: {str(e)}") from e
    
    def get_record_statistics(self) -> dict:
        """Compute comprehensive record statistics using efficient SQL aggregations.
        
        Combines multiple statistical queries into a single method call for optimal
        performance in UI components like the Configuration tab. Provides detailed
        breakdown of records by type and source along with temporal coverage.
        
        Returns:
            Dictionary containing comprehensive record statistics:
                - 'total_records' (int): Total number of health records
                - 'earliest_date' (str or None): Earliest record creation date
                - 'latest_date' (str or None): Latest record creation date
                - 'type_counts' (dict): Mapping of health types to record counts
                - 'source_counts' (dict): Mapping of source names to record counts
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query execution fails.
            
        Examples:
            Get complete database statistics:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> stats = loader.get_record_statistics()
            >>> print(f"Total: {stats['total_records']:,} records")
            >>> print(f"Types: {len(stats['type_counts'])}")
            >>> print(f"Sources: {len(stats['source_counts'])}")
            
            Analyze data distribution:
            >>> stats = loader.get_record_statistics()
            >>> top_type = max(stats['type_counts'], key=stats['type_counts'].get)
            >>> top_source = max(stats['source_counts'], key=stats['source_counts'].get)
            >>> print(f"Most common type: {top_type} ({stats['type_counts'][top_type]:,} records)")
            >>> print(f"Primary source: {top_source} ({stats['source_counts'][top_source]:,} records)")
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info("Getting record statistics using SQL aggregation")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if health_records table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='health_records'
            """)
            if not cursor.fetchone():
                self.logger.warning("health_records table does not exist")
                return {
                    'total_records': 0,
                    'earliest_date': None,
                    'latest_date': None,
                    'type_counts': {},
                    'source_counts': {}
                }
            
            # Total records and date range
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    MIN(creationDate) as earliest,
                    MAX(creationDate) as latest
                FROM health_records
            """)
            total, earliest, latest = cursor.fetchone()
            
            # Type counts
            type_counts_result = cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM health_records 
                GROUP BY type
            """).fetchall()
            type_counts = dict(type_counts_result)
            
            # Source counts
            source_counts_result = cursor.execute("""
                SELECT sourceName, COUNT(*) as count 
                FROM health_records 
                GROUP BY sourceName
            """).fetchall()
            source_counts = dict(source_counts_result)
            
            conn.close()
            
            return {
                'total_records': total or 0,
                'earliest_date': earliest,
                'latest_date': latest,
                'type_counts': type_counts,
                'source_counts': source_counts
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting record statistics: {e}")
            raise DataImportError(f"Failed to get record statistics: {str(e)}") from e
    
    def get_filter_options(self) -> dict:
        """Extract unique filter values for UI components without loading full dataset.
        
        Efficiently retrieves distinct values for filter dropdowns and selection
        widgets using optimized SQL queries. Essential for populating UI filter
        components without the memory overhead of loading complete datasets.
        
        Returns:
            Dictionary containing filter options:
                - 'types' (list): Sorted list of unique health metric types
                - 'sources' (list): Sorted list of unique source device/app names
                
        Raises:
            ValueError: If database path not set on the DataLoader instance.
            FileNotFoundError: If database file doesn't exist.
            DataImportError: If database query execution fails.
            
        Examples:
            Populate UI filter components:
            >>> loader = DataLoader()
            >>> loader.db_path = "health.db"
            >>> options = loader.get_filter_options()
            >>> print(f"Available types: {len(options['types'])}")
            >>> print(f"Available sources: {len(options['sources'])}")
            
            Create filter dropdown contents:
            >>> options = loader.get_filter_options()
            >>> type_dropdown_items = options['types']
            >>> source_dropdown_items = options['sources']
            >>> # Use these lists to populate QComboBox or similar widgets
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info("Getting filter options using SQL queries")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if health_records table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='health_records'
            """)
            if not cursor.fetchone():
                self.logger.warning("health_records table does not exist")
                return {'types': [], 'sources': []}
            
            # Get unique types
            types_result = cursor.execute("""
                SELECT DISTINCT type 
                FROM health_records 
                WHERE type IS NOT NULL
                ORDER BY type
            """).fetchall()
            types = [row[0] for row in types_result]
            
            # Get unique sources
            sources_result = cursor.execute("""
                SELECT DISTINCT sourceName 
                FROM health_records 
                WHERE sourceName IS NOT NULL
                ORDER BY sourceName
            """).fetchall()
            sources = [row[0] for row in sources_result]
            
            conn.close()
            
            return {
                'types': types,
                'sources': sources
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting filter options: {e}")
            raise DataImportError(f"Failed to get filter options: {str(e)}") from e


# Example usage and testing
if __name__ == "__main__":
    # Example: Convert XML to SQLite
    # convert_xml_to_sqlite("export.xml", "health_data.db")
    
    # Example: Query date range
    # df = query_date_range("health_data.db", "2024-01-01", "2024-12-31", "StepCount")
    # print(f"Found {len(df)} step count records")
    
    # Example: Get daily summary
    # daily_steps = get_daily_summary("health_data.db", "StepCount")
    # print(daily_steps.head())
    
    pass