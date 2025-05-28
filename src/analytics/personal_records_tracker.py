"""
Personal Records Tracker for Apple Health Monitor Dashboard.
Tracks all-time bests, worsts, and streaks across different record categories.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import pandas as pd
import numpy as np
from collections import defaultdict, deque

from ..database import DatabaseManager
from .daily_metrics_calculator import DailyMetricsCalculator
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator

logger = logging.getLogger(__name__)


class RecordType(Enum):
    """Types of personal records that can be tracked."""
    SINGLE_DAY_MAX = "single_day_max"
    SINGLE_DAY_MIN = "single_day_min"
    ROLLING_7_DAY = "rolling_7_day"
    ROLLING_30_DAY = "rolling_30_day"
    ROLLING_90_DAY = "rolling_90_day"
    CONSISTENCY_STREAK = "consistency_streak"
    GOAL_STREAK = "goal_streak"
    IMPROVEMENT_STREAK = "improvement_streak"
    IMPROVEMENT_VELOCITY = "improvement_velocity"
    DAILY_CONSISTENCY = "daily_consistency"


class CelebrationLevel(Enum):
    """Levels of celebration for achievements."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    LEGENDARY = 4


@dataclass
class Record:
    """Represents a personal record achievement."""
    id: Optional[int] = None
    record_type: RecordType = RecordType.SINGLE_DAY_MAX
    metric: str = ""
    value: float = 0.0
    date: date = field(default_factory=date.today)
    previous_value: Optional[float] = None
    improvement_margin: Optional[float] = None
    window_days: Optional[int] = None
    streak_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate improvement margin if previous value exists."""
        if self.previous_value is not None and self.previous_value != 0:
            self.improvement_margin = ((self.value - self.previous_value) / abs(self.previous_value)) * 100


@dataclass
class StreakInfo:
    """Information about a streak."""
    metric: str
    streak_type: str
    current_length: int = 0
    best_length: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    best_start_date: Optional[date] = None
    best_end_date: Optional[date] = None
    is_record: bool = False
    previous_length: int = 0


@dataclass
class StreakType:
    """Definition of a streak type."""
    name: str
    condition: Callable[[str, date, float], bool]
    description: str


@dataclass
class Achievement:
    """Represents an achievement earned."""
    id: Optional[int] = None
    badge_id: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    rarity: str = "common"
    unlocked_date: date = field(default_factory=date.today)
    trigger_record_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Badge:
    """Definition of an achievement badge."""
    id: str
    name: str
    description: str
    icon: str
    rarity: str
    condition: Callable[[Record], bool]


class PersonalRecordsTracker:
    """Main class for tracking personal records and achievements."""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        self.record_store = RecordStore(database)
        self.achievement_system = AchievementSystem(database)
        self.streak_tracker = StreakTracker()
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure personal records tables exist in database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create personal_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_type VARCHAR(50) NOT NULL,
                    metric VARCHAR(100) NOT NULL,
                    value REAL NOT NULL,
                    date DATE NOT NULL,
                    previous_value REAL,
                    improvement_margin REAL,
                    window_days INTEGER,
                    streak_type VARCHAR(50),
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    badge_id VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    icon VARCHAR(50),
                    rarity VARCHAR(20) DEFAULT 'common',
                    unlocked_date DATE NOT NULL,
                    trigger_record_id INTEGER,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trigger_record_id) REFERENCES personal_records (id)
                )
            """)
            
            # Create streaks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS streaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric VARCHAR(100) NOT NULL,
                    streak_type VARCHAR(50) NOT NULL,
                    current_length INTEGER DEFAULT 0,
                    best_length INTEGER DEFAULT 0,
                    start_date DATE,
                    end_date DATE,
                    best_start_date DATE,
                    best_end_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric, streak_type)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_metric_type ON personal_records(metric, record_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON personal_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_date ON achievements(unlocked_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_streaks_metric ON streaks(metric)")
            
            conn.commit()
    
    def check_for_records(self, metric: str, value: float, date_val: date, 
                         source_data: Optional[pd.DataFrame] = None) -> List[Record]:
        """Check if new value sets any records."""
        new_records = []
        
        try:
            # Check single-day records
            single_day_records = self._check_single_day_records(metric, value, date_val)
            new_records.extend(single_day_records)
            
            # Check rolling average records if we have source data
            if source_data is not None:
                rolling_records = self._check_rolling_average_records(metric, value, date_val, source_data)
                new_records.extend(rolling_records)
            
            # Check streak records
            streak_records = self._check_streak_records(metric, value, date_val, source_data)
            new_records.extend(streak_records)
            
            # Process new records
            for record in new_records:
                self.process_new_record(record)
                
        except Exception as e:
            logger.error(f"Error checking records for {metric}: {e}")
        
        return new_records
    
    def _check_single_day_records(self, metric: str, value: float, date_val: date) -> List[Record]:
        """Check for single-day records (max/min)."""
        records = []
        
        # Get current records
        current_max = self.record_store.get_record(metric, RecordType.SINGLE_DAY_MAX)
        current_min = self.record_store.get_record(metric, RecordType.SINGLE_DAY_MIN)
        
        # Check for new max record
        if current_max is None or value > current_max.value:
            record = Record(
                record_type=RecordType.SINGLE_DAY_MAX,
                metric=metric,
                value=value,
                date=date_val,
                previous_value=current_max.value if current_max else None
            )
            records.append(record)
        
        # Check for new min record
        if current_min is None or value < current_min.value:
            record = Record(
                record_type=RecordType.SINGLE_DAY_MIN,
                metric=metric,
                value=value,
                date=date_val,
                previous_value=current_min.value if current_min else None
            )
            records.append(record)
        
        return records
    
    def _check_rolling_average_records(self, metric: str, value: float, date_val: date, 
                                     source_data: pd.DataFrame) -> List[Record]:
        """Check for rolling average records."""
        records = []
        
        # Calculate rolling averages for different windows
        for window in [7, 30, 90]:
            try:
                # Get data for rolling calculation
                end_date = date_val
                start_date = end_date - timedelta(days=window-1)
                
                # Filter data for the window
                mask = (pd.to_datetime(source_data['date']).dt.date >= start_date) & \
                       (pd.to_datetime(source_data['date']).dt.date <= end_date)
                window_data = source_data[mask]
                
                if len(window_data) >= window * 0.7:  # At least 70% data coverage
                    avg_value = window_data['value'].mean()
                    
                    # Get current rolling record
                    record_type = getattr(RecordType, f"ROLLING_{window}_DAY")
                    current_record = self.record_store.get_record(metric, record_type)
                    
                    # Check if new record
                    if current_record is None or avg_value > current_record.value:
                        record = Record(
                            record_type=record_type,
                            metric=metric,
                            value=avg_value,
                            date=date_val,
                            previous_value=current_record.value if current_record else None,
                            window_days=window
                        )
                        records.append(record)
                        
            except Exception as e:
                logger.warning(f"Error calculating {window}-day rolling average for {metric}: {e}")
        
        return records
    
    def _check_streak_records(self, metric: str, value: float, date_val: date,
                            source_data: Optional[pd.DataFrame]) -> List[Record]:
        """Check for streak records."""
        records = []
        
        try:
            # Update streak information
            streak_info = self.streak_tracker.update_streak(metric, date_val, value, source_data)
            
            # Check if new streak record
            if streak_info.is_record:
                record = Record(
                    record_type=RecordType.CONSISTENCY_STREAK,
                    metric=metric,
                    value=float(streak_info.best_length),
                    date=date_val,
                    previous_value=float(streak_info.previous_length) if streak_info.previous_length > 0 else None,
                    streak_type=streak_info.streak_type
                )
                records.append(record)
                
        except Exception as e:
            logger.warning(f"Error checking streak records for {metric}: {e}")
        
        return records
    
    def process_new_record(self, record: Record):
        """Process a new record achievement."""
        try:
            # Store record
            record_id = self.record_store.add_record(record)
            record.id = record_id
            
            # Check for achievements
            achievements = self.achievement_system.check_achievements(record)
            
            # Log achievement
            logger.info(f"New {record.record_type.value} record for {record.metric}: {record.value}")
            
            return record, achievements
            
        except Exception as e:
            logger.error(f"Error processing new record: {e}")
            return record, []
    
    def get_all_records(self, metric: Optional[str] = None) -> Dict[str, List[Record]]:
        """Get all records, optionally filtered by metric."""
        return self.record_store.get_all_records(metric)
    
    def get_achievements(self, limit: Optional[int] = None) -> List[Achievement]:
        """Get user achievements."""
        return self.achievement_system.get_user_achievements(limit)
    
    def get_streak_info(self, metric: str) -> Optional[StreakInfo]:
        """Get current streak information for a metric."""
        return self.streak_tracker.get_streak_info(metric)


class RecordStore:
    """Handles storage and retrieval of personal records."""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
    
    def add_record(self, record: Record) -> int:
        """Add a new record to the database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO personal_records 
                (record_type, metric, value, date, previous_value, improvement_margin, 
                 window_days, streak_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_type.value,
                record.metric,
                record.value,
                record.date.isoformat(),
                record.previous_value,
                record.improvement_margin,
                record.window_days,
                record.streak_type,
                json.dumps(record.metadata)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_record(self, metric: str, record_type: RecordType) -> Optional[Record]:
        """Get the current record for a metric and type."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM personal_records 
                WHERE metric = ? AND record_type = ?
                ORDER BY created_at DESC LIMIT 1
            """, (metric, record_type.value))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_record(row)
            return None
    
    def get_all_records(self, metric: Optional[str] = None) -> Dict[str, List[Record]]:
        """Get all records, optionally filtered by metric."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if metric:
                cursor.execute("SELECT * FROM personal_records WHERE metric = ? ORDER BY created_at DESC", (metric,))
            else:
                cursor.execute("SELECT * FROM personal_records ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            
            # Group by record type
            records_by_type = defaultdict(list)
            for row in rows:
                record = self._row_to_record(row)
                records_by_type[record.record_type.value].append(record)
            
            return dict(records_by_type)
    
    def _row_to_record(self, row) -> Record:
        """Convert database row to Record object."""
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        return Record(
            id=row['id'],
            record_type=RecordType(row['record_type']),
            metric=row['metric'],
            value=row['value'],
            date=date.fromisoformat(row['date']),
            previous_value=row['previous_value'],
            improvement_margin=row['improvement_margin'],
            window_days=row['window_days'],
            streak_type=row['streak_type'],
            metadata=metadata,
            created_at=datetime.fromisoformat(row['created_at'])
        )


class StreakTracker:
    """Tracks consistency and improvement streaks."""
    
    def __init__(self):
        self.active_streaks = {}
    
    def update_streak(self, metric: str, date_val: date, value: float,
                     source_data: Optional[pd.DataFrame] = None) -> StreakInfo:
        """Update streak information for a metric."""
        streak_key = f"{metric}_consistency"
        
        if streak_key not in self.active_streaks:
            self.active_streaks[streak_key] = StreakInfo(
                metric=metric,
                streak_type="consistency",
                start_date=date_val
            )
        
        streak = self.active_streaks[streak_key]
        
        # Check if streak continues (has any data)
        if value is not None:
            streak.current_length += 1
            streak.end_date = date_val
            
            # Check if new record
            if streak.current_length > streak.best_length:
                streak.best_length = streak.current_length
                streak.best_start_date = streak.start_date
                streak.best_end_date = date_val
                streak.is_record = True
            else:
                streak.is_record = False
        else:
            # Streak broken
            streak.previous_length = streak.current_length
            streak.current_length = 0
            streak.start_date = date_val
            streak.is_record = False
        
        return streak
    
    def get_streak_info(self, metric: str) -> Optional[StreakInfo]:
        """Get current streak information for a metric."""
        streak_key = f"{metric}_consistency"
        return self.active_streaks.get(streak_key)
    
    def get_streak_types(self) -> List[StreakType]:
        """Define different types of streaks to track."""
        return [
            StreakType(
                name='consistency',
                condition=lambda metric, date_val, value: value is not None,
                description='Days with any data'
            ),
            StreakType(
                name='improvement',
                condition=lambda metric, date_val, value: value > 0,  # Simplified condition
                description='Consecutive days of improvement'
            )
        ]


class AchievementSystem:
    """Manages achievement badges and unlocks."""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        self.badges = self._create_badge_definitions()
        self.user_achievements = set(self._load_user_achievements())
    
    def check_achievements(self, record: Record) -> List[Achievement]:
        """Check if record unlocks any achievements."""
        new_achievements = []
        
        for badge in self.badges:
            if badge.condition(record) and badge.id not in self.user_achievements:
                achievement = Achievement(
                    badge_id=badge.id,
                    name=badge.name,
                    description=badge.description,
                    icon=badge.icon,
                    rarity=badge.rarity,
                    unlocked_date=record.date,
                    trigger_record_id=record.id
                )
                
                # Store achievement
                achievement_id = self._store_achievement(achievement)
                achievement.id = achievement_id
                
                new_achievements.append(achievement)
                self.user_achievements.add(badge.id)
        
        return new_achievements
    
    def _create_badge_definitions(self) -> List[Badge]:
        """Define all available badges."""
        return [
            Badge(
                id='first_record',
                name='Record Breaker',
                description='Set your first personal record',
                icon='trophy_bronze',
                rarity='common',
                condition=lambda r: True  # Any record
            ),
            Badge(
                id='streak_week',
                name='Week Warrior',
                description='Maintain a 7-day streak',
                icon='fire',
                rarity='common',
                condition=lambda r: r.record_type == RecordType.CONSISTENCY_STREAK and r.value >= 7
            ),
            Badge(
                id='streak_month',
                name='Monthly Master',
                description='Maintain a 30-day streak',
                icon='fire_gold',
                rarity='rare',
                condition=lambda r: r.record_type == RecordType.CONSISTENCY_STREAK and r.value >= 30
            ),
            Badge(
                id='century_streak',
                name='Centurion',
                description='Maintain a 100-day streak',
                icon='fire_platinum',
                rarity='legendary',
                condition=lambda r: r.record_type == RecordType.CONSISTENCY_STREAK and r.value >= 100
            ),
            Badge(
                id='big_improvement',
                name='Big Leap',
                description='Improve a record by 50% or more',
                icon='arrow_up',
                rarity='rare',
                condition=lambda r: r.improvement_margin is not None and r.improvement_margin >= 50
            )
        ]
    
    def _load_user_achievements(self) -> List[str]:
        """Load user's current achievements."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT badge_id FROM achievements")
                return [row['badge_id'] for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _store_achievement(self, achievement: Achievement) -> int:
        """Store achievement in database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO achievements 
                (badge_id, name, description, icon, rarity, unlocked_date, trigger_record_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                achievement.badge_id,
                achievement.name,
                achievement.description,
                achievement.icon,
                achievement.rarity,
                achievement.unlocked_date.isoformat(),
                achievement.trigger_record_id,
                json.dumps(achievement.metadata)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_achievements(self, limit: Optional[int] = None) -> List[Achievement]:
        """Get user's achievements."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM achievements ORDER BY unlocked_date DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            achievements = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                achievement = Achievement(
                    id=row['id'],
                    badge_id=row['badge_id'],
                    name=row['name'],
                    description=row['description'],
                    icon=row['icon'],
                    rarity=row['rarity'],
                    unlocked_date=date.fromisoformat(row['unlocked_date']),
                    trigger_record_id=row['trigger_record_id'],
                    metadata=metadata
                )
                achievements.append(achievement)
            
            return achievements