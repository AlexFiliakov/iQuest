---
task_id: G002
status: open
complexity: Medium
last_updated: 2025-01-27T12:00:00Z
---

# Task: Implement SQLite Data Loader

## Description
Create a robust XML -> SQLite converter and loader module that can read Apple Health export data from XML files, handle the specific data format, and store it in a SQLite database for efficient querying and storage.

## Goal / Objectives
Build a reliable data loading system that can handle Apple Health XML exports efficiently with optimized storage and fast queries.
- Convert XML data directly to SQLite database
- Store data with proper column types and indexes
- Handle date parsing with SQLite datetime support
- Validate data integrity and handle missing values
- Optimize for fast date-range queries and analytics

## Acceptance Criteria
- [ ] SQLite loader successfully imports Apple Health XML data
- [ ] creationDate field stored as proper datetime with index
- [ ] Numeric fields are properly typed in database
- [ ] Database file is 60-70% smaller than equivalent CSV
- [ ] Date-range queries execute in <100ms
- [ ] Error handling for corrupt XML files
- [ ] Unit tests cover main loading scenarios

## Subtasks
- [ ] Create data_loader.py module in src/
- [ ] Implement XML to SQLite conversion with proper indexing:
  ```python
  import xml.etree.ElementTree as ET
  import pandas as pd
  import sqlite3
  from pathlib import Path
  import logging

  def convert_xml_to_sqlite(xml_path: str, db_path: str):
      """Convert Apple Health XML export to SQLite database."""
      
      # Parse XML file
      logging.info(f"Parsing XML file: {xml_path}")
      tree = ET.parse(xml_path)
      root = tree.getroot()
      
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
  ```
- [ ] Add efficient query methods for common analytics:
  ```python
  def query_date_range(db_path: str, start_date: str, end_date: str, 
                       record_type: str = None) -> pd.DataFrame:
      """Query health records within a date range."""
      with sqlite3.connect(db_path) as conn:
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
          
          return pd.read_sql(query, conn, params=params, 
                           parse_dates=['creationDate', 'startDate', 'endDate'])
  
  def get_daily_summary(db_path: str, record_type: str) -> pd.DataFrame:
      """Get daily aggregated data for a specific health metric."""
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
  ```
- [ ] Analyze the sample data format: `processed data/apple_data_subset.csv`
- [ ] Implement data validation and type checking
- [ ] Add error handling and logging
- [ ] Create migration utility for existing CSV data:
  ```python
  def migrate_csv_to_sqlite(csv_path: str, db_path: str):
      """Migrate existing CSV data to SQLite format."""
      df = pd.read_csv(csv_path, parse_dates=['creationDate'])
      
      with sqlite3.connect(db_path) as conn:
          df.to_sql('health_records', conn, index=False, if_exists='replace')
          # Add same indexes as XML import
          conn.execute('CREATE INDEX idx_creation_date ON health_records(creationDate)')
          conn.execute('CREATE INDEX idx_type ON health_records(type)')
  ```
- [ ] Create unit tests for data loader
- [ ] Test with provided sample data
- [ ] Document performance improvements vs CSV approach

## Output Log
*(This section is populated as work progresses on the task)*