Journal Module API Reference
============================

The journal module provides comprehensive functionality for creating, managing, and analyzing health journal entries.

.. contents:: Table of Contents
   :local:
   :depth: 2

Core Components
---------------

JournalEntry Model
~~~~~~~~~~~~~~~~~~

.. autoclass:: src.models.JournalEntry
   :members:
   :undoc-members:
   :show-inheritance:

   The JournalEntry dataclass represents a single journal entry with support for daily, weekly, and monthly entry types.

   **Attributes:**

   - ``id`` (Optional[int]): Unique identifier
   - ``entry_date`` (date): Date of the journal entry
   - ``entry_type`` (str): Type of entry ('daily', 'weekly', 'monthly')
   - ``content`` (str): Journal entry content (max 10,000 characters)
   - ``week_start_date`` (Optional[date]): For weekly entries, the Monday of the week
   - ``month_year`` (Optional[str]): For monthly entries, format 'YYYY-MM'
   - ``version`` (int): Version number for optimistic locking
   - ``created_at`` (datetime): Timestamp when entry was created
   - ``updated_at`` (datetime): Timestamp when entry was last updated

Journal Manager
---------------

JournalManager
~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_manager.JournalManager
   :members:
   :undoc-members:
   :show-inheritance:

   Singleton manager for all journal operations with thread safety and conflict resolution.

   **Example Usage:**

   .. code-block:: python

      from src.ui.journal_manager import JournalManager
      
      manager = JournalManager()
      
      # Connect signals
      manager.entrySaved.connect(on_entry_saved)
      manager.errorOccurred.connect(show_error)
      
      # Save an entry
      manager.save_entry(
          QDate.currentDate(),
          'daily',
          'Today I exercised for 30 minutes...',
          callback=lambda success, entry_id: print(f"Saved: {entry_id}")
      )

   **Signals:**

   - ``entrySaved(str, str)``: Emitted when entry saved (date, type)
   - ``entryDeleted(str, str)``: Emitted when entry deleted (date, type)
   - ``errorOccurred(str)``: Emitted on error with message
   - ``conflictDetected(str, str, str)``: Emitted on version conflict

UI Components
-------------

JournalEditorWidget
~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_editor_widget.JournalEditorWidget
   :members:
   :undoc-members:
   :show-inheritance:

   Main editor widget for creating and editing journal entries.

   **Key Features:**

   - Character limit enforcement (10,000 chars)
   - Auto-save functionality
   - Unsaved changes detection
   - Entry type selection (daily/weekly/monthly)
   - Keyboard shortcuts support

   **Example:**

   .. code-block:: python

      editor = JournalEditorWidget(data_access)
      editor.entrySaved.connect(lambda: print("Entry saved!"))
      
      # Load existing entry
      editor.load_entry(journal_entry)
      
      # Create new entry
      editor.new_entry()

JournalHistoryWidget
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_history_widget.JournalHistoryWidget
   :members:
   :undoc-members:
   :show-inheritance:

   Widget for browsing and managing journal entry history.

   **Features:**

   - Virtual scrolling for performance
   - Filtering by entry type
   - Sorting (newest/oldest first)
   - Entry preview panel
   - Bulk operations support

JournalTabWidget
~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_tab_widget.JournalTabWidget
   :members:
   :undoc-members:
   :show-inheritance:

   Main container integrating all journal components.

Search System
-------------

JournalSearchEngine
~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.analytics.journal_search_engine.JournalSearchEngine
   :members:
   :undoc-members:
   :show-inheritance:

   Full-text search engine for journal entries using SQLite FTS5.

   **Search Syntax:**

   - Simple terms: ``exercise``
   - Phrases: ``"morning routine"``
   - Exclusions: ``exercise -skip``
   - Wildcards: ``exerc*``

   **Example:**

   .. code-block:: python

      engine = JournalSearchEngine()
      
      # Basic search
      results = engine.search("exercise routine")
      
      # With filters
      results = engine.search(
          "exercise",
          filters={
              'date_from': date(2024, 1, 1),
              'entry_types': ['daily', 'weekly']
          },
          limit=50
      )
      
      for result in results:
          print(f"{result.entry_date}: {result.snippet}")

JournalSearchWidget
~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_search_widget.JournalSearchWidget
   :members:
   :undoc-members:
   :show-inheritance:

   Complete search interface with filtering and result display.

Export System
-------------

Exporters
~~~~~~~~~

.. autoclass:: src.exporters.JSONExporter
   :members:
   :undoc-members:
   :show-inheritance:

   Export journal entries to JSON format.

   **Example:**

   .. code-block:: python

      exporter = JSONExporter(ExportOptions(
          pretty_print=True,
          include_metadata=True,
          include_statistics=True
      ))
      
      result = exporter.export(entries, "journal_backup.json")
      print(f"Exported {result.entries_exported} entries")

.. autoclass:: src.exporters.PDFExporter
   :members:
   :undoc-members:
   :show-inheritance:

   Export journal entries to PDF format with markdown support.

JournalExportDialog
~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_export_dialog.JournalExportDialog
   :members:
   :undoc-members:
   :show-inheritance:

   Dialog for configuring and executing journal exports.

Indicators System
-----------------

JournalIndicator
~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.journal_indicator.JournalIndicator
   :members:
   :undoc-members:
   :show-inheritance:

   Visual indicator widget for journal entries on calendars and charts.

JournalIndicatorService
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.analytics.journal_indicator_service.JournalIndicatorService
   :members:
   :undoc-members:
   :show-inheritance:

   Service for managing journal entry indicators with caching.

   **Example:**

   .. code-block:: python

      service = JournalIndicatorService(data_access)
      
      # Get indicators for date range
      indicators = service.get_indicators_for_date_range(
          date(2024, 1, 1),
          date(2024, 1, 31)
      )
      
      # Check specific date
      indicator = service.get_indicator_for_date(
          date(2024, 1, 15),
          'daily'
      )

Database Operations
-------------------

JournalDAO
~~~~~~~~~~

.. automodule:: src.data_access
   :members: JournalDAO
   :undoc-members:
   :show-inheritance:

   Data Access Object for journal database operations.

   **Key Methods:**

   - ``save_journal_entry()``: Save or update entry with version checking
   - ``get_journal_entries()``: Retrieve entries by date range
   - ``delete_journal_entry()``: Delete entry by date and type
   - ``search_journal_entries()``: Full-text search

Auto-Save System
----------------

AutoSaveManager
~~~~~~~~~~~~~~~

.. autoclass:: src.ui.auto_save_manager.AutoSaveManager
   :members:
   :undoc-members:
   :show-inheritance:

   Manages automatic saving of journal entries with debouncing.

   **Features:**

   - 3-second debounce after typing stops
   - Maximum 30-second interval
   - Draft recovery on crash
   - Background save operations

Best Practices
--------------

Error Handling
~~~~~~~~~~~~~~

Always handle potential errors when working with journal operations:

.. code-block:: python

   try:
       entry_id = manager.save_entry(date, type, content)
   except ValidationError as e:
       show_error(f"Invalid input: {e}")
   except DatabaseError as e:
       show_error(f"Database error: {e}")

Thread Safety
~~~~~~~~~~~~~

The JournalManager handles threading internally, but when integrating:

- Use Qt signals/slots for cross-thread communication
- Don't access database directly from UI thread
- Let JournalManager handle all database operations

Performance
~~~~~~~~~~~

For optimal performance:

- Use pagination when loading many entries
- Leverage search engine caching
- Use virtual scrolling in UI components
- Batch operations when possible

Testing
~~~~~~~

When testing journal components:

.. code-block:: python

   # Use mock data access
   mock_data_access = Mock(spec=DataAccess)
   widget = JournalEditorWidget(mock_data_access)
   
   # Test with fixtures
   from tests.journal.conftest import sample_journal_entries
   entries = sample_journal_entries()

Integration Example
-------------------

Complete example integrating journal features:

.. code-block:: python

   from PyQt6.QtWidgets import QMainWindow, QTabWidget
   from src.data_access import DataAccess
   from src.ui.journal_tab_widget import JournalTabWidget
   
   class HealthMonitorApp(QMainWindow):
       def __init__(self):
           super().__init__()
           
           # Initialize data access
           self.data_access = DataAccess("health.db")
           
           # Create tab widget
           tabs = QTabWidget()
           
           # Add journal tab
           journal_tab = JournalTabWidget(self.data_access)
           tabs.addTab(journal_tab, "Journal")
           
           self.setCentralWidget(tabs)
           
           # Connect to journal manager for notifications
           from src.ui.journal_manager import JournalManager
           manager = JournalManager(self.data_access)
           manager.entrySaved.connect(self.show_save_notification)
           
       def show_save_notification(self, date, entry_type):
           # Show toast notification
           print(f"Saved {entry_type} entry for {date}")

Migration Guide
---------------

If upgrading from a previous version:

1. Run database migrations to add journal tables
2. Update imports to use new journal modules
3. Connect journal indicators to existing calendar views
4. Add journal tab to main navigation

See migration scripts in ``scripts/migrations/`` for details.