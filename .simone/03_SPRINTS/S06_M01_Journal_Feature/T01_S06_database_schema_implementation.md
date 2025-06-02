---
task_id: T01_S06
sprint_sequence_id: S06
status: open
complexity: Medium
last_updated: 2025-01-28T00:00:00Z
dependencies: []
---

# Task: Journal Database Schema Implementation

## Description
Implement the journal entries database schema as specified in SPECS_DB.md, including the journal_entries table with proper indexes, constraints, and database access layer methods. This is the foundation task that other journal features depend on.

## Goal / Objectives
- Create journal_entries table with all required fields
- Implement database indexes for performance
- Create data access layer with CRUD operations
- Ensure proper transaction handling and error recovery
- Navbar File > Erase All Data... should also clear journal entries

## Acceptance Criteria
- [ ] Journal entries table created with exact schema from SPECS_DB.md
- [ ] All indexes created (date, type, week, month)
- [ ] Unique constraint on (entry_date, entry_type) enforced
- [ ] Data access layer provides all required methods
- [ ] Unit tests achieve 90%+ coverage

## Implementation Analysis

### Database Migration Approach
- Require a fresh import to work.

### Full-Text Search Implementation
- **SQLite FTS5** - Built-in full-text search
   - Pros: No dependencies, fast, supports ranking
   - Cons: SQLite-specific, limited features

## Detailed Subtasks

### 1. Database Migration Setup
- [ ] Create 003_journal_entries.sql migration file with:
  - [ ] CREATE TABLE journal_entries statement
  - [ ] All column definitions with proper types and constraints
  - [ ] UNIQUE constraint on (entry_date, entry_type)
  - [ ] Add updated_at trigger for automatic timestamp updates
- [ ] Create rollback script 003_journal_entries_rollback.sql
- [ ] Update DatabaseManager.initialize_schema() to run migrations

### 2. Table Schema Implementation
- [ ] Define journal_entries table with columns:
  - [ ] id (INTEGER PRIMARY KEY AUTOINCREMENT)
  - [ ] entry_date (DATE NOT NULL)
  - [ ] entry_type (VARCHAR(10) with CHECK constraint)
  - [ ] week_start_date (DATE) - calculated for weekly entries
  - [ ] month_year (VARCHAR(7)) - YYYY-MM format
  - [ ] content (TEXT NOT NULL) - limit 10,000 chars
  - [ ] created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
  - [ ] updated_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### 3. Index Creation
- [ ] Create idx_journal_date on entry_date for date queries
- [ ] Create idx_journal_type on entry_type for filtering
- [ ] Create idx_journal_week on week_start_date for weekly views
- [ ] Create idx_journal_month on month_year for monthly views
- [ ] Create composite index on (entry_date, entry_type) for uniqueness checks

### 4. Full-Text Search Setup
- [ ] Create FTS5 virtual table for journal content:
  ```sql
  CREATE VIRTUAL TABLE journal_search USING fts5(
    entry_id, content, entry_date, entry_type,
    tokenize='porter'
  );
  ```
- [ ] Create triggers to sync journal_entries with journal_search
- [ ] Add search ranking configuration

### 5. JournalDatabase Class Implementation
- [ ] Create src/journal_database.py with JournalDatabase class
- [ ] Implement connection management with context manager
- [ ] Add error handling decorators for all methods
- [ ] Implement logging for all database operations

### 6. CRUD Operations
- [ ] save_journal_entry(date, entry_type, content):
  - [ ] Validate date format and entry_type
  - [ ] Calculate week_start_date for weekly entries
  - [ ] Calculate month_year for monthly entries
  - [ ] Implement UPSERT using INSERT OR REPLACE
  - [ ] Update FTS index
  - [ ] Return success/error status
  
- [ ] get_journal_entry(date, entry_type):
  - [ ] Query by date and type
  - [ ] Return entry dict or None
  
- [ ] get_journal_entries(start_date=None, end_date=None, entry_type=None):
  - [ ] Build dynamic query with optional filters
  - [ ] Order by entry_date DESC
  - [ ] Return list of entry dicts
  - [ ] Implement pagination (limit/offset)
  
- [ ] search_journal_entries(search_term, limit=50):
  - [ ] Use FTS5 MATCH query
  - [ ] Rank results by relevance
  - [ ] Highlight search terms in results
  - [ ] Return entries with snippets
  
- [ ] delete_journal_entry(date, entry_type):
  - [ ] Soft delete option (mark as deleted)
  - [ ] Remove from FTS index
  - [ ] Return success/error status
  
- [ ] get_entry_stats():
  - [ ] Count by type
  - [ ] Date range coverage
  - [ ] Average entry length

### 7. Transaction Management
- [ ] Implement transaction decorator for atomic operations
- [ ] Add retry logic for database locks
- [ ] Implement savepoint support for nested transactions
- [ ] Create rollback handlers for each operation

### 8. Performance Optimization
- [ ] Enable WAL mode for better concurrency
- [ ] Implement prepared statement caching
- [ ] Add connection pooling (if multi-threaded)
- [ ] Optimize FTS indexing with batch updates

### 9. Testing Implementation
- [ ] Create tests/unit/test_journal_database.py:
  - [ ] Test table creation and migration
  - [ ] Test all CRUD operations
  - [ ] Test constraint violations
  - [ ] Test transaction rollback
  - [ ] Test concurrent access
  
### 10. Documentation
- [ ] Add docstrings to all methods (Google style)
- [ ] Create docs/journal_database_api.md
- [ ] Add usage examples
- [ ] Document migration process

## Output Log
[2025-01-28 00:00:00] Task created - Database schema is foundation for all journal features