"""Journal search engine with full-text search capabilities using SQLite FTS5.

This module provides comprehensive full-text search functionality for journal entries
using SQLite's FTS5 module. It implements query parsing, result ranking, snippet
generation, and search suggestions.

The search engine supports:
    - Full-text search with FTS5 
    - Query parsing with operators (AND, OR, NOT, quotes, wildcards)
    - Hybrid scoring combining text relevance and recency
    - Search result highlighting and snippet extraction
    - Search history tracking and suggestions
    - Performance optimization with caching

Examples:
    Basic search operation:
        >>> engine = JournalSearchEngine(db_path)
        >>> results = engine.search("workout", limit=10)
        >>> for result in results:
        ...     print(f"{result.entry_date}: {result.snippet}")
        
    Search with filters:
        >>> filters = {
        ...     'date_from': date(2024, 1, 1),
        ...     'date_to': date(2024, 1, 31),
        ...     'entry_types': ['daily']
        ... }
        >>> results = engine.search("goals", filters=filters)
        
    Get search suggestions:
        >>> suggestions = engine.suggest_queries("exer")
        >>> print(suggestions)  # ["exercise", "exercises", "exercising"]
"""

import sqlite3
import logging
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json

from ..database import DatabaseManager
from ..models import JournalEntry

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result with metadata and relevance scoring.
    
    Attributes:
        entry_id (int): ID of the matched journal entry.
        entry_date (date): Date of the journal entry.
        entry_type (str): Type of entry ('daily', 'weekly', 'monthly').
        score (float): Relevance score combining text match and recency.
        snippet (str): Text snippet with search terms highlighted.
        highlights (List[Tuple[int, int]]): Character positions of matched terms.
        metadata (Dict[str, Any]): Additional metadata about the result.
    """
    entry_id: int
    entry_date: date
    entry_type: str
    score: float
    snippet: str
    highlights: List[Tuple[int, int]]
    metadata: Dict[str, Any]


@dataclass
class ParsedQuery:
    """Represents a parsed search query with extracted components.
    
    Attributes:
        original (str): The original query string.
        terms (List[str]): Individual search terms.
        phrases (List[str]): Exact phrase matches (quoted strings).
        excluded (List[str]): Terms to exclude (prefixed with -).
        wildcards (List[str]): Wildcard patterns (ending with *).
        fts_query (str): Formatted query for FTS5 MATCH clause.
    """
    original: str
    terms: List[str]
    phrases: List[str]
    excluded: List[str]
    wildcards: List[str]
    fts_query: str


class QueryParser:
    """Parse user search queries into structured format for FTS5.
    
    Handles various query operators:
        - "exact phrase": Match exact phrases
        - word*: Wildcard suffix matching
        - -exclude: Exclude terms from results
        - AND/OR: Boolean operators (implicit AND)
    """
    
    def __init__(self):
        """Initialize the query parser with regex patterns."""
        # Pattern to extract quoted phrases
        self.phrase_pattern = re.compile(r'"([^"]+)"')
        # Pattern to extract excluded terms
        self.exclude_pattern = re.compile(r'-(\S+)')
        # Pattern to extract wildcard terms
        self.wildcard_pattern = re.compile(r'(\S+\*)')
        
    def parse(self, query: str) -> ParsedQuery:
        """Parse a search query into components.
        
        Args:
            query: The user's search query string.
            
        Returns:
            ParsedQuery object with extracted components.
            
        Examples:
            >>> parser = QueryParser()
            >>> parsed = parser.parse('"daily workout" exercise -skip')
            >>> print(parsed.phrases)  # ["daily workout"]
            >>> print(parsed.excluded)  # ["skip"]
        """
        original = query
        
        # Extract phrases
        phrases = self.phrase_pattern.findall(query)
        query = self.phrase_pattern.sub('', query)
        
        # Extract excluded terms
        excluded = self.exclude_pattern.findall(query)
        query = self.exclude_pattern.sub('', query)
        
        # Extract wildcards
        wildcards = self.wildcard_pattern.findall(query)
        query = self.wildcard_pattern.sub('', query)
        
        # Remaining terms
        terms = [term for term in query.split() if term]
        
        # Build FTS5 query
        fts_query = self._build_fts_query(terms, phrases, excluded, wildcards)
        
        return ParsedQuery(
            original=original,
            terms=terms,
            phrases=phrases,
            excluded=excluded,
            wildcards=wildcards,
            fts_query=fts_query
        )
    
    def _build_fts_query(self, terms: List[str], phrases: List[str], 
                        excluded: List[str], wildcards: List[str]) -> str:
        """Build FTS5 MATCH query from parsed components.
        
        Args:
            terms: Individual search terms.
            phrases: Exact phrase matches.
            excluded: Terms to exclude.
            wildcards: Wildcard patterns.
            
        Returns:
            Formatted query string for FTS5 MATCH clause.
        """
        query_parts = []
        
        # Add phrases
        for phrase in phrases:
            query_parts.append(f'"{phrase}"')
        
        # Add regular terms
        query_parts.extend(terms)
        
        # Add wildcards
        query_parts.extend(wildcards)
        
        # Join with implicit AND
        positive_query = ' '.join(query_parts)
        
        # Add exclusions
        if excluded:
            exclude_query = ' '.join(f'NOT {term}' for term in excluded)
            if positive_query:
                return f'{positive_query} {exclude_query}'
            else:
                return exclude_query
        
        return positive_query


class JournalSearchEngine:
    """Full-text search engine for journal entries using SQLite FTS5.
    
    Provides comprehensive search functionality including query parsing,
    result ranking, snippet generation, and search suggestions.
    
    Attributes:
        db (DatabaseManager): Database connection manager.
        parser (QueryParser): Query parser instance.
        _cache (dict): LRU cache for search results.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the search engine with database connection.
        
        Args:
            db_path: Optional path to database file. If not provided,
                uses the default DatabaseManager instance.
        """
        self.db = DatabaseManager() if not db_path else None
        self.db_path = db_path
        self.parser = QueryParser()
        self._cache = {}
        
    def _get_connection(self):
        """Get database connection based on initialization method."""
        if self.db:
            return self.db.get_connection()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
            
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None, 
              limit: int = 50) -> List[SearchResult]:
        """Search journal entries with optional filters.
        
        Args:
            query: The search query string.
            filters: Optional filters dict with keys:
                - date_from: Start date for results
                - date_to: End date for results  
                - entry_types: List of entry types to include
                - sort_by: Sort order ('relevance' or 'date')
            limit: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects sorted by relevance.
            
        Examples:
            >>> engine = JournalSearchEngine()
            >>> results = engine.search("exercise routine")
            >>> results = engine.search(
            ...     "workout",
            ...     filters={'entry_types': ['daily'], 'date_from': date(2024, 1, 1)}
            ... )
        """
        # Check cache
        cache_key = self._get_cache_key(query, filters, limit)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for query: {query}")
            return self._cache[cache_key]
        
        # Parse query
        parsed_query = self.parser.parse(query)
        
        # Execute search
        results = self._execute_search(parsed_query, filters, limit)
        
        # Cache results
        self._cache[cache_key] = results
        if len(self._cache) > 100:  # Simple cache eviction
            self._cache.pop(next(iter(self._cache)))
        
        # Log search for history
        self._log_search(query, len(results))
        
        return results
    
    def _execute_search(self, parsed_query: ParsedQuery, 
                       filters: Optional[Dict[str, Any]], 
                       limit: int) -> List[SearchResult]:
        """Execute the actual database search query.
        
        Args:
            parsed_query: Parsed query object.
            filters: Optional search filters.
            limit: Result limit.
            
        Returns:
            List of SearchResult objects.
        """
        if self.db:
            with self.db.get_connection() as conn:
                return self._search_with_connection(conn, parsed_query, filters, limit)
        else:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                return self._search_with_connection(conn, parsed_query, filters, limit)
    
    def _search_with_connection(self, conn: sqlite3.Connection,
                               parsed_query: ParsedQuery,
                               filters: Optional[Dict[str, Any]], 
                               limit: int) -> List[SearchResult]:
        """Execute search with provided connection."""
        cursor = conn.cursor()
        
        # Build SQL query
        sql_parts = ["""
            SELECT 
                js.entry_id,
                je.entry_date,
                je.entry_type,
                je.content,
                bm25(journal_search) as text_score,
                snippet(journal_search, 3, '<mark>', '</mark>', '...', 32) as snippet,
                je.created_at,
                je.updated_at
            FROM journal_search js
            JOIN journal_entries je ON js.entry_id = je.id
            WHERE journal_search MATCH ?
        """]
        
        params = [parsed_query.fts_query]
        
        # Apply filters
        if filters:
            if filters.get('date_from'):
                sql_parts.append("AND je.entry_date >= ?")
                params.append(filters['date_from'].isoformat())
                
            if filters.get('date_to'):
                sql_parts.append("AND je.entry_date <= ?")
                params.append(filters['date_to'].isoformat())
                
            if filters.get('entry_types'):
                placeholders = ','.join(['?' for _ in filters['entry_types']])
                sql_parts.append(f"AND je.entry_type IN ({placeholders})")
                params.extend(filters['entry_types'])
        
        # Add ordering
        sort_by = filters.get('sort_by', 'relevance') if filters else 'relevance'
        if sort_by == 'date':
            sql_parts.append("ORDER BY je.entry_date DESC")
        else:
            sql_parts.append("ORDER BY text_score DESC")
            
        sql_parts.append("LIMIT ?")
        params.append(limit)
        
        # Execute query
        sql = ' '.join(sql_parts)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert to SearchResult objects
        results = []
        for row in rows:
            # Calculate hybrid score
            text_score = abs(row['text_score'])  # BM25 returns negative values
            recency_score = self._calculate_recency_score(row['entry_date'])
            hybrid_score = self._calculate_hybrid_score(text_score, recency_score, row)
            
            # Extract highlights from snippet
            highlights = self._extract_highlights(row['snippet'])
            
            results.append(SearchResult(
                entry_id=row['entry_id'],
                entry_date=date.fromisoformat(row['entry_date']),
                entry_type=row['entry_type'],
                score=hybrid_score,
                snippet=row['snippet'],
                highlights=highlights,
                metadata={
                    'text_score': text_score,
                    'recency_score': recency_score,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            ))
        
        return results
    
    def _calculate_recency_score(self, entry_date_str: str) -> float:
        """Calculate recency score with exponential decay.
        
        Args:
            entry_date_str: ISO format date string.
            
        Returns:
            Score between 0 and 1, with recent dates scoring higher.
        """
        entry_date = date.fromisoformat(entry_date_str)
        days_ago = (date.today() - entry_date).days
        
        # Exponential decay with half-life of 30 days
        half_life = 30
        return 0.5 ** (days_ago / half_life)
    
    def _calculate_hybrid_score(self, text_score: float, recency_score: float,
                               row: sqlite3.Row) -> float:
        """Calculate hybrid relevance score.
        
        Args:
            text_score: BM25 text relevance score.
            recency_score: Time-based recency score.
            row: Database row with additional metadata.
            
        Returns:
            Combined relevance score.
        """
        # Normalize text score (BM25 typically ranges from 0 to ~10)
        normalized_text_score = min(text_score / 10, 1.0)
        
        # Entry type weight (daily entries might be more relevant)
        type_weight = 1.0
        if row['entry_type'] == 'daily':
            type_weight = 1.1
        elif row['entry_type'] == 'monthly':
            type_weight = 0.9
        
        # Combine scores
        hybrid_score = (
            normalized_text_score * 0.6 +
            recency_score * 0.3 +
            type_weight * 0.1
        )
        
        return hybrid_score
    
    def _extract_highlights(self, snippet: str) -> List[Tuple[int, int]]:
        """Extract highlight positions from snippet HTML.
        
        Args:
            snippet: Snippet text with <mark> tags.
            
        Returns:
            List of (start, end) tuples for highlighted regions.
        """
        highlights = []
        # Remove mark tags and track positions
        pattern = re.compile(r'<mark>(.*?)</mark>')
        offset = 0
        
        for match in pattern.finditer(snippet):
            start = match.start() - offset
            text_length = len(match.group(1))
            highlights.append((start, start + text_length))
            offset += 13  # Length of <mark></mark> tags
            
        return highlights
    
    def get_snippets(self, results: List[SearchResult], query: str,
                    context_length: int = 100) -> List[str]:
        """Generate snippets for search results with more context.
        
        Args:
            results: List of search results.
            query: Original search query.
            context_length: Number of characters of context around matches.
            
        Returns:
            List of snippet strings with highlighted matches.
        """
        snippets = []
        
        for result in results:
            # Fetch full content
            if self.db:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT content FROM journal_entries WHERE id = ?",
                        (result.entry_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        content = row['content']
                        snippet = self._generate_snippet(content, query, context_length)
                        snippets.append(snippet)
            
        return snippets
    
    def _generate_snippet(self, content: str, query: str, 
                         context_length: int) -> str:
        """Generate a snippet from content with query highlights.
        
        Args:
            content: Full text content.
            query: Search query.
            context_length: Context characters around matches.
            
        Returns:
            Snippet with highlighted matches.
        """
        # Simple implementation - find first occurrence
        query_lower = query.lower()
        content_lower = content.lower()
        
        pos = content_lower.find(query_lower)
        if pos == -1:
            # If exact match not found, try first term
            terms = query.split()
            if terms:
                pos = content_lower.find(terms[0].lower())
        
        if pos == -1:
            # Return beginning of content
            snippet = content[:context_length * 2]
            if len(content) > context_length * 2:
                snippet += '...'
        else:
            # Extract context around match
            start = max(0, pos - context_length)
            end = min(len(content), pos + len(query) + context_length)
            
            snippet = ''
            if start > 0:
                snippet = '...'
            
            snippet += content[start:pos]
            snippet += f'<mark>{content[pos:pos + len(query)]}</mark>'
            snippet += content[pos + len(query):end]
            
            if end < len(content):
                snippet += '...'
        
        return snippet
    
    def highlight_matches(self, text: str, query: str) -> str:
        """Highlight all query matches in text.
        
        Args:
            text: Text to highlight matches in.
            query: Search query.
            
        Returns:
            Text with HTML mark tags around matches.
            
        Examples:
            >>> engine = JournalSearchEngine()
            >>> highlighted = engine.highlight_matches(
            ...     "I love morning exercises",
            ...     "exercise"
            ... )
            >>> print(highlighted)
            I love morning <mark>exercise</mark>s
        """
        parsed = self.parser.parse(query)
        highlighted_text = text
        
        # Highlight phrases first
        for phrase in parsed.phrases:
            pattern = re.compile(f'({re.escape(phrase)})', re.IGNORECASE)
            highlighted_text = pattern.sub(r'<mark>\1</mark>', highlighted_text)
        
        # Then highlight individual terms
        for term in parsed.terms:
            pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
            highlighted_text = pattern.sub(r'<mark>\1</mark>', highlighted_text)
        
        # Handle wildcards
        for wildcard in parsed.wildcards:
            # Convert wildcard to regex
            regex_pattern = wildcard.replace('*', '\\w*')
            pattern = re.compile(f'({regex_pattern})', re.IGNORECASE)
            highlighted_text = pattern.sub(r'<mark>\1</mark>', highlighted_text)
        
        return highlighted_text
    
    def suggest_queries(self, partial_query: str, limit: int = 10) -> List[str]:
        """Generate query suggestions based on partial input and history.
        
        Args:
            partial_query: Partial query string.
            limit: Maximum number of suggestions.
            
        Returns:
            List of suggested query strings.
            
        Examples:
            >>> engine = JournalSearchEngine()
            >>> suggestions = engine.suggest_queries("wor")
            >>> print(suggestions)
            ["workout", "work", "working from home"]
        """
        suggestions = []
        
        if self.db:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get suggestions from search history
                cursor.execute("""
                    SELECT DISTINCT query, COUNT(*) as frequency
                    FROM search_history
                    WHERE query LIKE ? || '%'
                    GROUP BY query
                    ORDER BY frequency DESC, searched_at DESC
                    LIMIT ?
                """, (partial_query, limit))
                
                for row in cursor.fetchall():
                    suggestions.append(row['query'])
                
                # If not enough suggestions, add from content
                if len(suggestions) < limit:
                    remaining = limit - len(suggestions)
                    cursor.execute("""
                        SELECT DISTINCT content
                        FROM journal_entries
                        WHERE content LIKE '%' || ? || '%'
                        LIMIT ?
                    """, (partial_query, remaining * 3))
                    
                    # Extract relevant terms from content
                    pattern = re.compile(
                        f'\\b{re.escape(partial_query)}\\w*\\b',
                        re.IGNORECASE
                    )
                    
                    terms_seen = set(suggestions)
                    for row in cursor.fetchall():
                        matches = pattern.findall(row['content'])
                        for match in matches:
                            if match.lower() not in terms_seen:
                                suggestions.append(match)
                                terms_seen.add(match.lower())
                                if len(suggestions) >= limit:
                                    break
                        if len(suggestions) >= limit:
                            break
        
        return suggestions[:limit]
    
    def _log_search(self, query: str, result_count: int):
        """Log search query to history for suggestions.
        
        Args:
            query: The search query.
            result_count: Number of results found.
        """
        if self.db:
            try:
                self.db.execute_command(
                    "INSERT INTO search_history (query, result_count) VALUES (?, ?)",
                    (query, result_count)
                )
            except Exception as e:
                logger.error(f"Failed to log search history: {e}")
    
    def _get_cache_key(self, query: str, filters: Optional[Dict[str, Any]], 
                      limit: int) -> str:
        """Generate cache key for search query.
        
        Args:
            query: Search query.
            filters: Search filters.
            limit: Result limit.
            
        Returns:
            Hash key for caching.
        """
        key_data = {
            'query': query,
            'filters': filters or {},
            'limit': limit
        }
        # Convert dates to strings for JSON serialization
        def serialize_dates(obj):
            if isinstance(obj, date):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_dates(v) for v in obj]
            return obj
        
        serializable_data = serialize_dates(key_data)
        key_str = json.dumps(serializable_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the search result cache."""
        self._cache.clear()
        logger.info("Search cache cleared")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search usage statistics.
        
        Returns:
            Dictionary with search statistics including popular queries,
            recent searches, and success rates.
        """
        stats = {
            'cache_size': len(self._cache),
            'popular_queries': [],
            'recent_searches': [],
            'zero_result_queries': []
        }
        
        if self.db:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Popular queries
                cursor.execute("""
                    SELECT query, COUNT(*) as count, AVG(result_count) as avg_results
                    FROM search_history
                    WHERE searched_at > datetime('now', '-30 days')
                    GROUP BY query
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats['popular_queries'] = [
                    {
                        'query': row['query'],
                        'count': row['count'],
                        'avg_results': row['avg_results']
                    }
                    for row in cursor.fetchall()
                ]
                
                # Recent searches
                cursor.execute("""
                    SELECT query, result_count, searched_at
                    FROM search_history
                    ORDER BY searched_at DESC
                    LIMIT 20
                """)
                stats['recent_searches'] = [
                    {
                        'query': row['query'],
                        'result_count': row['result_count'],
                        'searched_at': row['searched_at']
                    }
                    for row in cursor.fetchall()
                ]
                
                # Zero result queries
                cursor.execute("""
                    SELECT DISTINCT query, COUNT(*) as attempts
                    FROM search_history
                    WHERE result_count = 0
                    AND searched_at > datetime('now', '-7 days')
                    GROUP BY query
                    ORDER BY attempts DESC
                    LIMIT 10
                """)
                stats['zero_result_queries'] = [
                    {
                        'query': row['query'],
                        'attempts': row['attempts']
                    }
                    for row in cursor.fetchall()
                ]
        
        return stats