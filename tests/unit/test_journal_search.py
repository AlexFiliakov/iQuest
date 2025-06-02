"""Unit tests for journal search functionality.

Tests the journal search engine, query parser, and search UI components.
"""

import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

from src.analytics.journal_search_engine import (
    JournalSearchEngine, QueryParser, ParsedQuery, SearchResult
)
from src.models import JournalEntry


class TestQueryParser(unittest.TestCase):
    """Test query parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = QueryParser()
        
    def test_simple_terms(self):
        """Test parsing simple search terms."""
        parsed = self.parser.parse("workout exercise")
        self.assertEqual(parsed.terms, ["workout", "exercise"])
        self.assertEqual(parsed.phrases, [])
        self.assertEqual(parsed.excluded, [])
        self.assertEqual(parsed.wildcards, [])
        
    def test_phrase_matching(self):
        """Test parsing quoted phrases."""
        parsed = self.parser.parse('"morning routine" exercise')
        self.assertEqual(parsed.phrases, ["morning routine"])
        self.assertEqual(parsed.terms, ["exercise"])
        
    def test_excluded_terms(self):
        """Test parsing excluded terms."""
        parsed = self.parser.parse("workout -skip -rest")
        self.assertEqual(parsed.terms, ["workout"])
        self.assertEqual(parsed.excluded, ["skip", "rest"])
        
    def test_wildcard_terms(self):
        """Test parsing wildcard terms."""
        parsed = self.parser.parse("exerc* work*")
        self.assertEqual(parsed.wildcards, ["exerc*", "work*"])
        self.assertEqual(parsed.terms, [])
        
    def test_mixed_query(self):
        """Test parsing complex mixed query."""
        parsed = self.parser.parse('"daily workout" exerc* -skip running')
        self.assertEqual(parsed.phrases, ["daily workout"])
        self.assertEqual(parsed.wildcards, ["exerc*"])
        self.assertEqual(parsed.excluded, ["skip"])
        self.assertEqual(parsed.terms, ["running"])
        
    def test_fts_query_generation(self):
        """Test FTS5 query generation."""
        parsed = self.parser.parse('"morning routine" exercise -skip')
        expected = '"morning routine" exercise NOT skip'
        self.assertEqual(parsed.fts_query, expected)


class TestSearchScoring(unittest.TestCase):
    """Test search result scoring algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = JournalSearchEngine(":memory:")
        
    def test_recency_scoring(self):
        """Test recency score calculation."""
        # Today should score 1.0
        today = date.today().isoformat()
        score = self.engine._calculate_recency_score(today)
        self.assertAlmostEqual(score, 1.0, places=2)
        
        # 30 days ago should score ~0.5
        old_date = date.today().replace(day=1).isoformat()
        score = self.engine._calculate_recency_score(old_date)
        self.assertLess(score, 0.7)
        self.assertGreater(score, 0.3)
        
    def test_hybrid_scoring(self):
        """Test hybrid score calculation."""
        # Create mock row
        row = {
            'entry_type': 'daily',
            'entry_date': date.today().isoformat()
        }
        
        # High text score, recent date
        score = self.engine._calculate_hybrid_score(8.0, 0.9, row)
        self.assertGreater(score, 0.7)
        
        # Low text score, old date
        score = self.engine._calculate_hybrid_score(2.0, 0.2, row)
        self.assertLess(score, 0.4)


class TestHighlighting(unittest.TestCase):
    """Test text highlighting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = JournalSearchEngine(":memory:")
        
    def test_simple_highlight(self):
        """Test simple term highlighting."""
        text = "I love morning exercises"
        highlighted = self.engine.highlight_matches(text, "exercise")
        expected = "I love morning <mark>exercise</mark>s"
        self.assertEqual(highlighted, expected)
        
    def test_case_insensitive_highlight(self):
        """Test case-insensitive highlighting."""
        text = "EXERCISE is important"
        highlighted = self.engine.highlight_matches(text, "exercise")
        expected = "<mark>EXERCISE</mark> is important"
        self.assertEqual(highlighted, expected)
        
    def test_multiple_highlights(self):
        """Test highlighting multiple terms."""
        text = "Morning workout and evening workout"
        highlighted = self.engine.highlight_matches(text, "morning workout")
        self.assertIn("<mark>Morning</mark>", highlighted)
        self.assertIn("<mark>workout</mark>", highlighted)
        
    def test_wildcard_highlight(self):
        """Test wildcard pattern highlighting."""
        text = "Exercise, exercising, and exercises"
        query = "exercis*"
        parser = QueryParser()
        parsed = parser.parse(query)
        
        # The highlight_matches method should handle wildcards
        highlighted = self.engine.highlight_matches(text, query)
        self.assertEqual(highlighted.count("<mark>"), 3)


class TestSearchCache(unittest.TestCase):
    """Test search result caching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = JournalSearchEngine(":memory:")
        
    def test_cache_key_generation(self):
        """Test cache key generation for different queries."""
        key1 = self.engine._get_cache_key("test", None, 50)
        key2 = self.engine._get_cache_key("test", None, 50)
        key3 = self.engine._get_cache_key("test", None, 100)
        key4 = self.engine._get_cache_key("different", None, 50)
        
        # Same query should generate same key
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different keys
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key1, key4)
        
    def test_cache_with_filters(self):
        """Test cache key generation with filters."""
        filters1 = {'date_from': date(2024, 1, 1), 'entry_types': ['daily']}
        filters2 = {'date_from': date(2024, 1, 1), 'entry_types': ['daily']}
        filters3 = {'date_from': date(2024, 2, 1), 'entry_types': ['daily']}
        
        key1 = self.engine._get_cache_key("test", filters1, 50)
        key2 = self.engine._get_cache_key("test", filters2, 50)
        key3 = self.engine._get_cache_key("test", filters3, 50)
        
        # Same filters should generate same key
        self.assertEqual(key1, key2)
        
        # Different filters should generate different key
        self.assertNotEqual(key1, key3)


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality."""
    
    @patch('src.analytics.journal_search_engine.DatabaseManager')
    def test_search_with_mock_db(self, mock_db_class):
        """Test search execution with mock database."""
        # Set up mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        # Create mock connection context
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock search results
        mock_cursor.fetchall.return_value = [
            {
                'entry_id': 1,
                'entry_date': '2024-01-15',
                'entry_type': 'daily',
                'content': 'Test content',
                'text_score': -5.0,
                'snippet': 'Test <mark>content</mark>',
                'created_at': '2024-01-15T10:00:00',
                'updated_at': '2024-01-15T10:00:00'
            }
        ]
        
        # Execute search
        engine = JournalSearchEngine()
        results = engine.search("content")
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entry_id, 1)
        self.assertEqual(results[0].entry_type, 'daily')
        self.assertIn('<mark>content</mark>', results[0].snippet)
        
    def test_empty_search_results(self):
        """Test handling of empty search results."""
        engine = JournalSearchEngine(":memory:")
        
        # Mock empty results
        with patch.object(engine, '_execute_search', return_value=[]):
            results = engine.search("nonexistent")
            self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()