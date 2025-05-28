"""
Time mocking utilities for testing time-dependent functionality.
Provides consistent time mocking for TTL tests and other time-sensitive operations.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import patch
from contextlib import contextmanager
from typing import Union


class TimeMocker:
    """Mock time with controllable advancement for testing."""
    
    def __init__(self, start_time: Union[datetime, float, None] = None):
        """Initialize with optional start time."""
        if isinstance(start_time, datetime):
            self.current_time = start_time.timestamp()
        elif isinstance(start_time, float):
            self.current_time = start_time
        else:
            self.current_time = time.time()
        
        self.start_time = self.current_time
        
    def advance(self, seconds: float) -> None:
        """Advance mocked time by seconds."""
        self.current_time += seconds
        
    def set_time(self, new_time: Union[datetime, float]) -> None:
        """Set absolute time."""
        if isinstance(new_time, datetime):
            self.current_time = new_time.timestamp()
        else:
            self.current_time = new_time
            
    def get_time(self) -> float:
        """Get current mocked time as timestamp."""
        return self.current_time
    
    def get_datetime(self) -> datetime:
        """Get current mocked time as datetime."""
        return datetime.fromtimestamp(self.current_time)
    
    def reset(self) -> None:
        """Reset time to start time."""
        self.current_time = self.start_time
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed seconds since start."""
        return self.current_time - self.start_time


@contextmanager
def mock_time(start_time: Union[datetime, float, None] = None):
    """Context manager for time mocking."""
    mocker = TimeMocker(start_time)
    
    with patch('time.time', mocker.get_time), \
         patch('datetime.datetime.now', mocker.get_datetime):
        yield mocker


@contextmanager 
def freeze_time(frozen_time: Union[datetime, float]):
    """Context manager that freezes time at a specific moment."""
    mocker = TimeMocker(frozen_time)
    
    with patch('time.time', mocker.get_time), \
         patch('datetime.datetime.now', mocker.get_datetime):
        yield mocker


class SQLiteTimeMocker:
    """Special time mocker for SQLite cache tests that handles both Python and SQLite time."""
    
    def __init__(self, start_time: Union[datetime, None] = None):
        if start_time is None:
            start_time = datetime.now()
        self.current_datetime = start_time
        
    def advance(self, seconds: float) -> None:
        """Advance time by seconds."""
        self.current_datetime += timedelta(seconds=seconds)
    
    def get_time(self) -> float:
        """Get current time as timestamp."""
        return self.current_datetime.timestamp()
    
    def get_datetime(self) -> datetime:
        """Get current time as datetime."""
        return self.current_datetime
    
    def get_sqlite_datetime(self) -> str:
        """Get current time formatted for SQLite."""
        return self.current_datetime.strftime('%Y-%m-%d %H:%M:%S')


@contextmanager
def mock_sqlite_time(start_time: Union[datetime, None] = None):
    """Context manager for SQLite time mocking."""
    mocker = SQLiteTimeMocker(start_time)
    
    # Mock both Python datetime and time modules
    with patch('time.time', mocker.get_time), \
         patch('datetime.datetime.now', mocker.get_datetime):
        yield mocker