"""
Apple Health XML to SQLite Data Loader

This module provides functionality to:
- Convert Apple Health XML exports to SQLite database
- Query health records efficiently with date ranges
- Generate daily/weekly/monthly summaries
- Migrate existing CSV data to SQLite format
"""

import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from pathlib import Path
import logging
from typing import Optional, Tuple, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_xml_to_sqlite(xml_path: str, db_path: str) -> int:
    """Convert Apple Health XML export to SQLite database.
    
    Args:
        xml_path: Path to the Apple Health export.xml file
        db_path: Path where the SQLite database will be created
        
    Returns:
        Number of records imported
        
    Raises:
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed
        sqlite3.Error: If database operation fails
    """
    # Validate input paths
    if not Path(xml_path).exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    try:
        # Parse XML file
        logging.info(f"Parsing XML file: {xml_path}")
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
        logging.info(f"Creating SQLite database: {db_path}")
        with sqlite3.connect(db_path) as conn:
            # Store data
            record_data.to_sql('health_records', conn, 
                             index=False, if_exists='replace')
            
            # Create indexes for fast queries
            conn.execute('CREATE INDEX idx_creation_date ON health_records(creationDate)')
            conn.execute('CREATE INDEX idx_type ON health_records(type)')
            conn.execute('CREATE INDEX idx_type_date ON health_records(type, creationDate)')
            
            # Create metadata table
            conn.execute('''
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute("INSERT INTO metadata VALUES ('import_date', datetime('now'))")
            conn.execute(f"INSERT INTO metadata VALUES ('record_count', '{len(record_data)}')")
            
        logging.info(f"Successfully imported {len(record_data)} records")
        return len(record_data)
    except sqlite3.Error as e:
        logger.error(f"Database error during conversion: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise


def query_date_range(db_path: str, start_date: str, end_date: str, 
                     record_type: str = None) -> pd.DataFrame:
    """Query health records within a date range.
    
    Args:
        db_path: Path to the SQLite database
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        record_type: Optional specific health metric type to filter
        
    Returns:
        DataFrame with matching health records
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
    """Get daily aggregated data for a specific health metric.
    
    Args:
        db_path: Path to the SQLite database
        record_type: Health metric type (e.g., 'StepCount', 'HeartRate')
        
    Returns:
        DataFrame with daily aggregations
        
    Raises:
        sqlite3.Error: If database operation fails
        ValueError: If record_type is invalid
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
    """Get weekly aggregated data for a specific health metric.
    
    Args:
        db_path: Path to the SQLite database
        record_type: Health metric type
        
    Returns:
        DataFrame with weekly aggregations
        
    Raises:
        sqlite3.Error: If database operation fails
        ValueError: If record_type is invalid
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
    """Get monthly aggregated data for a specific health metric.
    
    Args:
        db_path: Path to the SQLite database
        record_type: Health metric type
        
    Returns:
        DataFrame with monthly aggregations
        
    Raises:
        sqlite3.Error: If database operation fails
        ValueError: If record_type is invalid
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
    """Get list of all available health record types in the database.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        List of unique record types
        
    Raises:
        sqlite3.Error: If database operation fails
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
    """Get the date range of data in the database.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        Tuple of (min_date, max_date) as strings
        
    Raises:
        sqlite3.Error: If database operation fails
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
    """Migrate existing CSV data to SQLite format.
    
    Args:
        csv_path: Path to the CSV file
        db_path: Path where the SQLite database will be created
        
    Returns:
        Number of records migrated
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        sqlite3.Error: If database operation fails
        pd.errors.ParserError: If CSV is malformed
    """
    # Validate input paths
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        logging.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=['creationDate'])
        
        logging.info(f"Creating SQLite database: {db_path}")
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
        
        logging.info(f"Successfully migrated {len(df)} records")
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
    """Validate the integrity of the SQLite database.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        Dictionary with validation results
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