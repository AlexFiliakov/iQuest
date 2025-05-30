#!/usr/bin/env python3
"""Populate the database with test data for source-specific metrics."""

import sys
sys.path.insert(0, 'src')

from src.database import DatabaseManager
from datetime import datetime, date, timedelta
import random

db = DatabaseManager()

# Create health_records table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    sourceName TEXT,
    sourceVersion TEXT,
    device TEXT,
    unit TEXT,
    creationDate TEXT,
    startDate TEXT,
    endDate TEXT,
    value TEXT,
    metadata TEXT
)
"""

db.execute_query(create_table_query)
print("Ensured health_records table exists")

# Define test sources and metrics
sources = {
    "iPhone 14 Pro": ["StepCount", "DistanceWalkingRunning", "FlightsClimbed"],
    "Apple Watch Series 8": ["StepCount", "HeartRate", "ActiveEnergyBurned", "RestingHeartRate"],
    "Omron Blood Pressure": ["BloodPressureSystolic", "BloodPressureDiastolic"],
    "Withings Scale": ["BodyMass", "BodyFatPercentage"],
    "Sleep Cycle": ["SleepAnalysis"]
}

# Generate test data for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

records = []
current_date = start_date

while current_date <= end_date:
    for source, metrics in sources.items():
        for metric in metrics:
            # Add HK prefix
            if metric == "SleepAnalysis":
                full_type = f"HKCategoryTypeIdentifier{metric}"
            else:
                full_type = f"HKQuantityTypeIdentifier{metric}"
            
            # Generate appropriate values
            if metric == "StepCount":
                if source == "iPhone 14 Pro":
                    value = random.randint(5000, 12000)
                else:  # Apple Watch
                    value = random.randint(2000, 5000)
            elif metric == "HeartRate":
                value = random.randint(60, 100)
            elif metric == "RestingHeartRate":
                value = random.randint(50, 70)
            elif metric == "DistanceWalkingRunning":
                value = random.uniform(2000, 10000)  # meters
            elif metric == "FlightsClimbed":
                value = random.randint(0, 20)
            elif metric == "ActiveEnergyBurned":
                value = random.randint(200, 800)
            elif metric == "BloodPressureSystolic":
                value = random.randint(110, 130)
            elif metric == "BloodPressureDiastolic":
                value = random.randint(70, 85)
            elif metric == "BodyMass":
                value = random.uniform(70, 75)  # kg
            elif metric == "BodyFatPercentage":
                value = random.uniform(15, 25)
            elif metric == "SleepAnalysis":
                value = 1  # Category type
            else:
                value = random.uniform(50, 200)
            
            # Create record
            record = (
                full_type,
                source,
                "1.0",
                source,
                "count" if metric == "StepCount" else "kg" if metric == "BodyMass" else "",
                current_date.isoformat(),
                current_date.isoformat(),
                current_date.isoformat(),
                value  # Use numeric value directly
            )
            records.append(record)
    
    current_date += timedelta(days=1)

# Insert records
insert_query = """
INSERT INTO health_records 
(type, sourceName, sourceVersion, device, unit, creationDate, startDate, endDate, value)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for record in records:
    db.execute_query(insert_query, record)

print(f"\nInserted {len(records)} test records")

# Verify the data
count_query = "SELECT COUNT(*) FROM health_records"
count_result = db.execute_query(count_query)
print(f"Total records in database: {count_result[0][0]}")

# Show sources
sources_query = "SELECT DISTINCT sourceName FROM health_records"
db_sources = db.execute_query(sources_query)
print(f"\nSources in database:")
for source in db_sources:
    print(f"  - {source[0]}")

# Show metric-source combinations
combo_query = """
SELECT type, sourceName, COUNT(*) as count 
FROM health_records 
GROUP BY type, sourceName 
ORDER BY sourceName, type
"""
combos = db.execute_query(combo_query)
print(f"\nMetric-source combinations:")
for type_name, source, count in combos:
    clean_type = type_name.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
    print(f"  - {clean_type} from {source}: {count} records")