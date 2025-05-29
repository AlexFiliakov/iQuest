---
task_id: T05_S06
sprint_sequence_id: S06
status: open
complexity: High
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T01_S06"]
---

# Task: Journal Search Functionality

## Description
Implement full-text search functionality for journal entries using SQLite FTS (Full-Text Search) capabilities. Users should be able to quickly find entries by content, with results highlighted and sorted by relevance.

## Goal / Objectives
- Enable fast full-text search across all journal entries
- Implement search result highlighting
- Support date range filtering in search
- Provide search suggestions/history
- Ensure search performance with large datasets

## Acceptance Criteria
- [ ] Search returns results in <500ms for 1000+ entries
- [ ] Search terms highlighted in results
- [ ] Search supports phrases and wildcards
- [ ] Date range filter works with search
- [ ] Entry type filter works with search
- [ ] Recent searches saved and suggested
- [ ] Search results show preview snippets
- [ ] Results sorted by relevance score
- [ ] Empty search shows recent entries

## Implementation Analysis

### FTS Implementation Strategy
**Options:**
1. **SQLite FTS5** - Latest full-text search module
   - Pros: Built-in, fast, supports ranking, phrase queries
   - Cons: SQLite 3.9+ required, complex queries need parsing
2. **SQLite FTS4** - Older but stable FTS
   - Pros: Wider compatibility, simpler API
   - Cons: Missing features, deprecated
3. **Custom Inverted Index** - Build our own search
   - Pros: Full control, portable
   - Cons: Reinventing wheel, performance challenges

**Recommendation:** SQLite FTS5 (#1) - Modern, performant, feature-rich

### Search UI Pattern
**Options:**
1. **Inline Search Bar** - Always visible in journal tab
   - Pros: Discoverable, quick access
   - Cons: Takes UI space
2. **Modal Search Dialog** - Ctrl+F opens overlay
   - Pros: Full-featured, doesn't clutter UI
   - Cons: Extra step to access
3. **Command Palette Style** - Quick launcher approach
   - Pros: Power user friendly, fast
   - Cons: Less discoverable

**Recommendation:** Inline Search Bar with Modal for Advanced (#1+#2)

### Result Ranking Algorithm
**Options:**
1. **BM25 (FTS5 Default)** - Probabilistic ranking
   - Pros: Well-tested, good for most cases
   - Cons: May need tuning for short entries
2. **TF-IDF Custom** - Term frequency weighting
   - Pros: Customizable, predictable
   - Cons: More complex implementation
3. **Hybrid Scoring** - Combine text relevance + recency
   - Pros: Better UX, considers time factor
   - Cons: Needs careful balancing

**Recommendation:** Hybrid Scoring (#3) - Best user experience

## Detailed Subtasks

### 1. FTS5 Virtual Table Setup
- [ ] Create FTS5 virtual table:
  ```sql
  CREATE VIRTUAL TABLE journal_search USING fts5(
      entry_id UNINDEXED,
      entry_date UNINDEXED,
      entry_type UNINDEXED,
      content,
      tokenize='porter unicode61',
      content_rowid='entry_id'
  );
  ```
- [ ] Configure FTS5 options:
  - [ ] Enable porter stemming for better matches
  - [ ] Configure unicode tokenization
  - [ ] Set up auxiliary functions (highlight, snippet)
- [ ] Create sync triggers:
  ```sql
  CREATE TRIGGER journal_search_insert AFTER INSERT ON journal_entries
  BEGIN
      INSERT INTO journal_search(entry_id, entry_date, entry_type, content)
      VALUES (NEW.id, NEW.entry_date, NEW.entry_type, NEW.content);
  END;
  ```
- [ ] Add update and delete triggers
- [ ] Test trigger cascading

### 2. JournalSearchEngine Class
- [ ] Create src/analytics/journal_search_engine.py:
  ```python
  class JournalSearchEngine:
      def __init__(self, db_path: str):
          self.db = sqlite3.connect(db_path)
          self.db.create_function("rank", 1, self._custom_rank)
  ```
- [ ] Implement core search methods:
  - [ ] search(query, filters=None, limit=50)
  - [ ] get_snippets(results, query)
  - [ ] highlight_matches(text, query)
  - [ ] suggest_queries(partial_query)
- [ ] Add search analytics:
  - [ ] Track query performance
  - [ ] Log popular searches
  - [ ] Monitor result quality

### 3. Query Parser Implementation
- [ ] Create QueryParser class:
  ```python
  class QueryParser:
      def parse(self, query: str) -> ParsedQuery:
          # Handle operators: AND, OR, NOT, quotes, wildcards
          tokens = self.tokenize(query)
          ast = self.build_ast(tokens)
          return self.to_fts_query(ast)
  ```
- [ ] Support query syntax:
  - [ ] "exact phrase" matching
  - [ ] word* wildcard suffix
  - [ ] -exclude negative terms
  - [ ] field:value for metadata
- [ ] Add query validation:
  - [ ] Check for SQL injection
  - [ ] Validate special characters
  - [ ] Limit query complexity
- [ ] Create query builder for FTS5:
  ```python
  def build_fts_query(self, parsed: ParsedQuery) -> str:
      # Convert to FTS5 MATCH syntax
      return f'"{parsed.phrases}" {parsed.terms}'
  ```

### 4. Search Result Model
- [ ] Define SearchResult dataclass:
  ```python
  @dataclass
  class SearchResult:
      entry_id: int
      entry_date: date
      entry_type: str
      score: float
      snippet: str
      highlights: List[Tuple[int, int]]
      metadata: Dict[str, Any]
  ```
- [ ] Implement result processing:
  - [ ] Extract snippets around matches
  - [ ] Calculate match positions
  - [ ] Generate preview text
- [ ] Add result grouping:
  - [ ] Group by date
  - [ ] Group by entry type
  - [ ] Cluster similar results

### 5. Relevance Scoring System
- [ ] Implement hybrid scoring:
  ```python
  def calculate_score(self, text_score: float, entry: JournalEntry) -> float:
      recency_score = self._recency_factor(entry.date)
      length_score = self._length_factor(len(entry.content))
      type_score = self._type_factor(entry.type)
      return (text_score * 0.6 + 
              recency_score * 0.3 + 
              length_score * 0.05 + 
              type_score * 0.05)
  ```
- [ ] Add scoring factors:
  - [ ] Text relevance (BM25)
  - [ ] Recency boost (exponential decay)
  - [ ] Entry length normalization
  - [ ] Entry type weighting
- [ ] Implement score explanation:
  - [ ] Debug mode shows score breakdown
  - [ ] Tuning interface for weights

### 6. Search UI Components
- [ ] Create SearchBar widget:
  ```python
  class JournalSearchBar(QWidget):
      def __init__(self):
          self.search_input = QLineEdit()
          self.search_button = QPushButton("Search")
          self.filter_button = QPushButton("Filters")
  ```
- [ ] Style with warm colors:
  ```css
  QLineEdit {
      background-color: #FFF8F0;
      border: 2px solid #E8DCC8;
      border-radius: 20px;
      padding: 8px 16px;
      font-size: 14px;
  }
  ```
- [ ] Add search icon and clear button
- [ ] Implement live search preview
- [ ] Add loading spinner during search

### 7. Search History & Suggestions
- [ ] Create search_history table:
  ```sql
  CREATE TABLE search_history (
      id INTEGER PRIMARY KEY,
      query TEXT NOT NULL,
      result_count INTEGER,
      clicked_result_id INTEGER,
      searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- [ ] Implement SearchHistoryManager:
  - [ ] Record searches
  - [ ] Track result clicks
  - [ ] Generate suggestions
  - [ ] Clean old history (>90 days)
- [ ] Build suggestion algorithm:
  - [ ] Recent searches (weighted by recency)
  - [ ] Popular searches (weighted by frequency)
  - [ ] Contextual suggestions (based on current date/type)
- [ ] Create suggestion dropdown:
  - [ ] Show on focus
  - [ ] Update as user types
  - [ ] Keyboard navigation

### 8. Advanced Filter UI
- [ ] Create FilterPanel widget:
  ```python
  class SearchFilterPanel(QWidget):
      def __init__(self):
          self.date_from = EnhancedDateEdit()
          self.date_to = EnhancedDateEdit()
          self.type_selector = SegmentedControl()
          self.sort_options = QComboBox()
  ```
- [ ] Implement filter options:
  - [ ] Date range (from/to)
  - [ ] Entry type (multi-select)
  - [ ] Sort by (relevance/date/type)
  - [ ] Results per page
- [ ] Add filter presets:
  - [ ] "This week"
  - [ ] "This month"
  - [ ] "Last 30 days"
- [ ] Save filter preferences

### 9. Result Highlighting
- [ ] Implement HTML highlighting:
  ```python
  def highlight_text(self, text: str, terms: List[str]) -> str:
      for term in terms:
          pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
          text = pattern.sub(r'<mark>\1</mark>', text)
      return text
  ```
- [ ] Add CSS for highlights:
  ```css
  mark {
      background-color: #FFD166;
      color: #5D4E37;
      padding: 2px 4px;
      border-radius: 3px;
  }
  ```
- [ ] Handle overlapping highlights
- [ ] Preserve text formatting
- [ ] Add highlight navigation (F3/Shift+F3)

### 10. Search Results View
- [ ] Create SearchResultsWidget:
  ```python
  class SearchResultsWidget(QListWidget):
      def __init__(self):
          self.setItemDelegate(SearchResultDelegate())
          self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
  ```
- [ ] Implement custom result items:
  - [ ] Entry date and type badges
  - [ ] Snippet with highlights
  - [ ] Match count indicator
  - [ ] Click to open entry
- [ ] Add result actions:
  - [ ] Copy snippet
  - [ ] Open in editor
  - [ ] Export results
- [ ] Implement infinite scroll

### 11. Performance Optimization
- [ ] Add search caching:
  ```python
  class SearchCache:
      def __init__(self, max_size=100):
          self.cache = LRUCache(max_size)
      
      def get_or_search(self, query, search_func):
          key = self._cache_key(query)
          if key in self.cache:
              return self.cache[key]
  ```
- [ ] Implement query optimization:
  - [ ] Precompile common queries
  - [ ] Use prepared statements
  - [ ] Batch result fetching
- [ ] Add background indexing:
  - [ ] Index new entries asynchronously
  - [ ] Rebuild index periodically
  - [ ] Monitor index health

### 12. Search Analytics
- [ ] Track search metrics:
  ```python
  class SearchAnalytics:
      def log_search(self, query, result_count, duration):
          self.metrics.append({
              'query': query,
              'results': result_count,
              'duration_ms': duration,
              'timestamp': datetime.now()
          })
  ```
- [ ] Generate insights:
  - [ ] Most searched terms
  - [ ] Failed searches (0 results)
  - [ ] Search performance trends
  - [ ] Click-through rates
- [ ] Create analytics dashboard
- [ ] Export analytics data

### 13. Testing Implementation
- [ ] Create tests/unit/test_journal_search.py:
  - [ ] Test query parsing
  - [ ] Test scoring algorithm
  - [ ] Test highlight generation
  - [ ] Test filter combinations
  - [ ] Test edge cases (empty, special chars)
  
- [ ] Create tests/integration/test_search_integration.py:
  - [ ] Test with real FTS5 table
  - [ ] Test concurrent searches
  - [ ] Test large result sets
  - [ ] Test index updates
  
- [ ] Create tests/performance/test_search_performance.py:
  - [ ] Benchmark with 10,000 entries
  - [ ] Test query complexity impact
  - [ ] Profile memory usage
  - [ ] Test UI responsiveness

### 14. Search Help & Documentation
- [ ] Create search syntax guide:
  - [ ] Basic search examples
  - [ ] Advanced operators
  - [ ] Filter combinations
  - [ ] Keyboard shortcuts
- [ ] Add inline help tooltips
- [ ] Create search tips widget:
  ```python
  class SearchTips(QWidget):
      tips = [
          "Use quotes for exact phrases",
          "Add * for wildcard searches",
          "Use - to exclude terms"
      ]
  ```
- [ ] Add contextual help based on query

## Output Log
[2025-01-28 00:00:00] Task created - Full-text search enables quick journal entry discovery