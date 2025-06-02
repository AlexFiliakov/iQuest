"""Shared fixtures for journal tests.

This module provides common test fixtures and utilities for testing
the journal feature functionality.
"""

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
from unittest.mock import Mock, MagicMock

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDate

from src.models import JournalEntry
from src.data_access import DataAccess


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def tmp_db_path(tmp_path):
    """Create temporary database path."""
    return tmp_path / "test_journal.db"


@pytest.fixture
def mock_data_access():
    """Create mock data access object with journal methods."""
    mock = Mock(spec=DataAccess)
    
    # Mock journal-related methods
    mock.get_journal_entries = Mock(return_value=[])
    mock.save_journal_entry = Mock(return_value=1)
    mock.update_journal_entry = Mock(return_value=True)
    mock.delete_journal_entry = Mock(return_value=True)
    mock.search_journal_entries = Mock(return_value=[])
    mock.get_journal_entry = Mock(return_value=None)
    mock.get_journal_entries_by_date_range = Mock(return_value=[])
    
    return mock


@pytest.fixture
def sample_journal_entries():
    """Create sample journal entries for testing."""
    return [
        JournalEntry(
            id=1,
            entry_date=date(2024, 1, 1),
            entry_type='daily',
            content='New Year resolutions and health goals.',
            week_start_date=None,
            month_year=None,
            version=1,
            created_at=datetime(2024, 1, 1, 10, 0),
            updated_at=datetime(2024, 1, 1, 10, 0)
        ),
        JournalEntry(
            id=2,
            entry_date=date(2024, 1, 2),
            entry_type='daily',
            content='Second day of the year. Feeling motivated!',
            week_start_date=None,
            month_year=None,
            version=1,
            created_at=datetime(2024, 1, 2, 9, 30),
            updated_at=datetime(2024, 1, 2, 9, 30)
        ),
        JournalEntry(
            id=3,
            entry_date=date(2024, 1, 7),
            entry_type='weekly',
            content='First week reflection. Made good progress on exercise goals.',
            week_start_date=date(2024, 1, 1),
            month_year=None,
            version=1,
            created_at=datetime(2024, 1, 7, 20, 0),
            updated_at=datetime(2024, 1, 7, 20, 0)
        ),
        JournalEntry(
            id=4,
            entry_date=date(2024, 1, 31),
            entry_type='monthly',
            content='January summary: established good habits, lost 3 pounds.',
            week_start_date=None,
            month_year='2024-01',
            version=1,
            created_at=datetime(2024, 1, 31, 21, 0),
            updated_at=datetime(2024, 1, 31, 21, 0)
        )
    ]


@pytest.fixture
def long_journal_entry():
    """Create a journal entry with long content for testing limits."""
    long_content = """
    This is a very long journal entry that tests the character limit functionality.
    """ + ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 200)
    
    return JournalEntry(
        id=5,
        entry_date=date(2024, 2, 1),
        entry_type='daily',
        content=long_content[:10000],  # Ensure it's within limit
        week_start_date=None,
        month_year=None,
        version=1,
        created_at=datetime(2024, 2, 1, 10, 0),
        updated_at=datetime(2024, 2, 1, 10, 0)
    )


@pytest.fixture
def export_test_dir(tmp_path):
    """Create temporary directory for export tests."""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir


class MockJournalDatabase:
    """Mock journal database for testing."""
    
    def __init__(self):
        self.entries = {}
        self.next_id = 1
        
    def save_entry(self, entry_date, entry_type, content, **kwargs):
        """Save a journal entry."""
        entry_id = self.next_id
        self.next_id += 1
        
        entry = JournalEntry(
            id=entry_id,
            entry_date=entry_date,
            entry_type=entry_type,
            content=content,
            week_start_date=kwargs.get('week_start_date'),
            month_year=kwargs.get('month_year'),
            version=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.entries[entry_id] = entry
        return entry
        
    def get_entry(self, entry_id):
        """Get entry by ID."""
        return self.entries.get(entry_id)
        
    def get_entries_by_date_range(self, start_date, end_date):
        """Get entries in date range."""
        return [
            entry for entry in self.entries.values()
            if start_date <= entry.entry_date <= end_date
        ]
        
    def delete_entry(self, entry_id):
        """Delete entry."""
        if entry_id in self.entries:
            del self.entries[entry_id]
            return True
        return False
        
    def search_entries(self, query):
        """Search entries by content."""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries.values():
            if query_lower in entry.content.lower():
                results.append(entry)
                
        return results


@pytest.fixture
def mock_journal_db():
    """Create mock journal database instance."""
    return MockJournalDatabase()


def create_test_entry(**kwargs):
    """Helper to create test journal entries with defaults."""
    defaults = {
        'id': None,
        'entry_date': date.today(),
        'entry_type': 'daily',
        'content': 'Test entry content',
        'week_start_date': None,
        'month_year': None,
        'version': 1,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    defaults.update(kwargs)
    return JournalEntry(**defaults)


@pytest.fixture
def performance_test_entries():
    """Create large set of entries for performance testing."""
    entries = []
    base_date = date(2020, 1, 1)
    
    # Create 3 years of daily entries
    for i in range(1095):  # 3 years
        entry_date = base_date + timedelta(days=i)
        entries.append(
            JournalEntry(
                id=i + 1,
                entry_date=entry_date,
                entry_type='daily',
                content=f'Daily entry for {entry_date}. ' * 10,
                week_start_date=None,
                month_year=None,
                version=1,
                created_at=datetime.combine(entry_date, datetime.min.time()),
                updated_at=datetime.combine(entry_date, datetime.min.time())
            )
        )
        
    return entries


@pytest.fixture
def qt_test_helpers():
    """Provide Qt testing helper functions."""
    
    def wait_for_signal(signal, timeout=1000):
        """Wait for a Qt signal to be emitted."""
        from PyQt6.QtCore import QEventLoop, QTimer
        
        loop = QEventLoop()
        signal.connect(loop.quit)
        
        timer = QTimer()
        timer.timeout.connect(loop.quit)
        timer.start(timeout)
        
        loop.exec()
        timer.stop()
        
        return timer.isActive()  # True if signal fired before timeout
        
    def process_events():
        """Process pending Qt events."""
        QApplication.processEvents()
        
    return {
        'wait_for_signal': wait_for_signal,
        'process_events': process_events
    }