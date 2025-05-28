"""
Apple Health XML to SQLite Data Loader

This module provides functionality to:
- Convert Apple Health XML exports to SQLite database
- Query health records efficiently with date ranges
- Generate daily/weekly/monthly summaries
- Migrate existing CSV data to SQLite format
- Load CSV data directly for UI usage
"""

import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from utils.logging_config import get_logger
from utils.error_handler import (
    safe_file_operation, safe_database_operation, 
    DataImportError, DatabaseError, ErrorContext, DataValidationError
)
from utils.xml_validator import validate_apple_health_xml, AppleHealthXMLValidator

# Get logger for this module
logger = get_logger(__name__)


def convert_xml_to_sqlite_with_validation(xml_path: str, db_path: str, validate_first: bool = True) -> Tuple[int, str]:
    """Convert Apple Health XML export to SQLite database with validation and transaction handling.
    
    Args:
        xml_path: Path to the Apple Health export.xml file
        db_path: Path where the SQLite database will be created
        validate_first: Whether to validate XML before processing
        
    Returns:
        Tuple of (number of records imported, validation summary message)
        
    Raises:
        DataValidationError: If XML validation fails
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed
        sqlite3.Error: If database operation fails
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
    """Internal function to handle XML conversion with proper transaction management."""
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
            # Store data
            record_data.to_sql('health_records', conn, 
                             index=False, if_exists='replace')
            
            # Validate the import by checking record count
            imported_count = conn.execute('SELECT COUNT(*) FROM health_records').fetchone()[0]
            if imported_count != len(record_data):
                raise DatabaseError(f"Import verification failed: expected {len(record_data)} records, found {imported_count}")
            
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
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('record_count', '{len(record_data)}')")
            conn.execute(f"INSERT OR REPLACE INTO metadata VALUES ('source_file', '{xml_path}')")
            
            # Commit transaction
            conn.commit()
            logger.info(f"Successfully imported {len(record_data)} records with transaction")
            
            return len(record_data)
            
        except Exception as e:
            # Rollback transaction on any error
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseError(f"Database import failed and was rolled back: {e}")
    
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file: {e}")
        raise DataImportError(f"XML parsing failed: {e}")
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
            # Store data
            record_data.to_sql('health_records', conn, 
                             index=False, if_exists='replace')
            
            # Create indexes for fast queries
            conn.execute('CREATE INDEX idx_creation_date ON health_records(creationDate)')
            conn.execute('CREATE INDEX idx_type ON health_records(type)')
            conn.execute('CREATE INDEX idx_type_date ON health_records(type, creationDate)')
            conn.execute('CREATE INDEX idx_source ON health_records(sourceName)')
            conn.execute('CREATE INDEX idx_source_type ON health_records(sourceName, type)')
            
            # Create metadata table
            conn.execute('''
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute("INSERT INTO metadata VALUES ('import_date', datetime('now'))")
            conn.execute(f"INSERT INTO metadata VALUES ('record_count', '{len(record_data)}')")
            
        logger.info(f"Successfully imported {len(record_data)} records")
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


class DataLoader:
    """Simple data loader class for CSV files and SQLite databases."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.logger = get_logger(__name__)
        self.db_path = None
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load CSV file and return as DataFrame.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame with the CSV data
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            pd.errors.ParserError: If CSV is malformed
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
        """Get all records from the SQLite database.
        
        Returns:
            DataFrame with all health records
            
        Raises:
            FileNotFoundError: If database doesn't exist
            sqlite3.Error: If database query fails
        """
        if not self.db_path:
            raise ValueError("Database path not set")
        
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        try:
            self.logger.info(f"Loading all records from database: {self.db_path}")
            
            conn = sqlite3.connect(self.db_path)
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
        """Infer source device name from record type."""
        # Common mappings
        if any(x in record_type.lower() for x in ['step', 'distance', 'flight']):
            return "iPhone"
        elif any(x in record_type.lower() for x in ['heart', 'workout', 'exercise']):
            return "Apple Watch"
        elif 'sleep' in record_type.lower():
            return "Sleep Apps"
        else:
            return "Other Apps"


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