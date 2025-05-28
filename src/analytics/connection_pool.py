"""Database connection pooling for improved performance."""

import sqlite3
import threading
import queue
import time
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import atexit

logger = logging.getLogger(__name__)


@dataclass
class PooledConnection:
    """Wrapper for pooled database connections."""
    connection: sqlite3.Connection
    created_at: datetime
    last_used: datetime
    in_use: bool = False
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if connection is too old."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > max_age_seconds
    
    def is_idle(self, idle_timeout_seconds: int = 60) -> bool:
        """Check if connection has been idle too long."""
        idle_time = (datetime.now() - self.last_used).total_seconds()
        return idle_time > idle_timeout_seconds


class ConnectionPool:
    """
    Thread-safe SQLite connection pool with optimizations.
    
    Features:
    - Configurable pool size
    - Connection health checks
    - Automatic connection recycling
    - Performance statistics
    - Query caching support
    """
    
    def __init__(self,
                 database_path: str,
                 min_connections: int = 2,
                 max_connections: int = 10,
                 connection_timeout: float = 5.0,
                 enable_wal: bool = True,
                 enable_query_cache: bool = True):
        """
        Initialize connection pool.
        
        Args:
            database_path: Path to SQLite database
            min_connections: Minimum connections to maintain
            max_connections: Maximum connections allowed
            connection_timeout: Timeout for getting connection
            enable_wal: Enable Write-Ahead Logging
            enable_query_cache: Enable query result caching
        """
        self.database_path = database_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.enable_wal = enable_wal
        self.enable_query_cache = enable_query_cache
        
        # Pool management
        self._pool = queue.Queue(maxsize=max_connections)
        self._all_connections: Dict[int, PooledConnection] = {}
        self._lock = threading.RLock()
        self._closed = False
        
        # Statistics
        self._stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'connections_recycled': 0,
            'wait_time_total': 0.0,
            'queries_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Query cache
        if enable_query_cache:
            from cachetools import TTLCache
            self._query_cache = TTLCache(maxsize=1000, ttl=60)
        else:
            self._query_cache = None
        
        # Initialize pool with minimum connections
        self._initialize_pool()
        
        # Register cleanup
        atexit.register(self.close)
        
        # Start maintenance thread
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_worker,
            daemon=True
        )
        self._maintenance_thread.start()
    
    def _initialize_pool(self):
        """Initialize pool with minimum connections."""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new database connection."""
        try:
            # Create connection
            connection = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Configure for performance
            self._configure_connection(connection)
            
            # Wrap in pooled connection
            pooled = PooledConnection(
                connection=connection,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            # Track connection
            with self._lock:
                self._all_connections[id(connection)] = pooled
                self._stats['connections_created'] += 1
            
            logger.debug(f"Created new connection (total: {len(self._all_connections)})")
            
            return pooled
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def _configure_connection(self, connection: sqlite3.Connection):
        """Configure connection for optimal performance."""
        cursor = connection.cursor()
        
        # Enable Write-Ahead Logging for better concurrency
        if self.enable_wal:
            cursor.execute("PRAGMA journal_mode=WAL")
        
        # Performance optimizations
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
        
        # Enable query planner optimizations
        cursor.execute("PRAGMA optimize")
        
        connection.commit()
        cursor.close()
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            sqlite3.Connection
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        start_time = time.time()
        pooled_conn = None
        
        try:
            # Try to get from pool
            try:
                pooled_conn = self._pool.get(timeout=self.connection_timeout)
                wait_time = time.time() - start_time
                self._stats['wait_time_total'] += wait_time
                
                # Check if connection is still valid
                if pooled_conn.is_stale() or not self._is_connection_alive(pooled_conn.connection):
                    logger.debug("Recycling stale connection")
                    self._close_connection(pooled_conn)
                    pooled_conn = self._create_connection()
                    self._stats['connections_recycled'] += 1
                else:
                    self._stats['connections_reused'] += 1
                    
            except queue.Empty:
                # Pool exhausted, try to create new connection
                with self._lock:
                    if len(self._all_connections) < self.max_connections:
                        pooled_conn = self._create_connection()
                    else:
                        raise RuntimeError("Connection pool exhausted")
            
            if not pooled_conn:
                raise RuntimeError("Failed to get connection")
            
            # Mark as in use
            pooled_conn.in_use = True
            pooled_conn.last_used = datetime.now()
            
            yield pooled_conn.connection
            
        finally:
            # Return to pool
            if pooled_conn:
                pooled_conn.in_use = False
                pooled_conn.last_used = datetime.now()
                
                if not self._closed:
                    self._pool.put(pooled_conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None,
                     fetch_all: bool = True) -> Any:
        """
        Execute a query with optional caching.
        
        Args:
            query: SQL query
            params: Query parameters
            fetch_all: Whether to fetch all results
            
        Returns:
            Query results
        """
        # Check cache if enabled
        cache_key = None
        if self._query_cache is not None and query.upper().startswith('SELECT'):
            cache_key = (query, params)
            cached_result = self._query_cache.get(cache_key)
            if cached_result is not None:
                self._stats['cache_hits'] += 1
                return cached_result
            else:
                self._stats['cache_misses'] += 1
        
        # Execute query
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                
                self._stats['queries_executed'] += 1
                
                # Cache result if applicable
                if cache_key and self._query_cache is not None:
                    self._query_cache[cache_key] = result
                
                return result
                
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: list):
        """Execute multiple queries efficiently."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                self._stats['queries_executed'] += len(params_list)
            finally:
                cursor.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            active_connections = sum(
                1 for conn in self._all_connections.values()
                if conn.in_use
            )
            
            return {
                **self._stats,
                'pool_size': len(self._all_connections),
                'active_connections': active_connections,
                'idle_connections': self._pool.qsize(),
                'cache_size': len(self._query_cache) if self._query_cache else 0
            }
    
    def close(self):
        """Close all connections and shutdown pool."""
        if self._closed:
            return
        
        logger.info("Closing connection pool")
        self._closed = True
        
        # Close all connections
        with self._lock:
            while not self._pool.empty():
                try:
                    pooled_conn = self._pool.get_nowait()
                    self._close_connection(pooled_conn)
                except queue.Empty:
                    break
            
            # Close any remaining connections
            for pooled_conn in list(self._all_connections.values()):
                self._close_connection(pooled_conn)
            
            self._all_connections.clear()
    
    def _close_connection(self, pooled_conn: PooledConnection):
        """Close a single connection."""
        try:
            pooled_conn.connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
        
        # Remove from tracking
        with self._lock:
            self._all_connections.pop(id(pooled_conn.connection), None)
    
    def _is_connection_alive(self, connection: sqlite3.Connection) -> bool:
        """Check if connection is still alive."""
        try:
            connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def _maintenance_worker(self):
        """Background thread for pool maintenance."""
        while not self._closed:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                with self._lock:
                    # Remove idle connections above minimum
                    current_size = len(self._all_connections)
                    if current_size > self.min_connections:
                        idle_connections = []
                        
                        # Find idle connections
                        for pooled_conn in self._all_connections.values():
                            if not pooled_conn.in_use and pooled_conn.is_idle():
                                idle_connections.append(pooled_conn)
                        
                        # Close excess idle connections
                        to_close = min(
                            len(idle_connections),
                            current_size - self.min_connections
                        )
                        
                        for i in range(to_close):
                            self._close_connection(idle_connections[i])
                            logger.debug(f"Closed idle connection (pool size: {len(self._all_connections)})")
                
            except Exception as e:
                logger.error(f"Error in maintenance worker: {e}")


class PooledDataAccess:
    """
    Data access layer with connection pooling.
    
    Drop-in replacement for standard DataAccess with pooling.
    """
    
    def __init__(self, pool: ConnectionPool):
        """Initialize with connection pool."""
        self.pool = pool
    
    def get_records_by_date_range(self, start_date: datetime, end_date: datetime) -> list:
        """Get records using pooled connection."""
        query = """
            SELECT * FROM health_records 
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """
        
        return self.pool.execute_query(
            query,
            (start_date.isoformat(), end_date.isoformat())
        )
    
    def get_metrics_summary(self, metric: str, start_date: datetime, end_date: datetime) -> dict:
        """Get metric summary using pooled connection."""
        query = """
            SELECT 
                COUNT(*) as count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                SUM(value) as total_value
            FROM health_records
            WHERE type = ? AND date >= ? AND date <= ?
        """
        
        result = self.pool.execute_query(
            query,
            (metric, start_date.isoformat(), end_date.isoformat()),
            fetch_all=False
        )
        
        if result:
            return {
                'count': result[0],
                'average': result[1],
                'minimum': result[2],
                'maximum': result[3],
                'total': result[4]
            }
        
        return {}
    
    def close(self):
        """Close the connection pool."""
        self.pool.close()


def create_optimized_pool(database_path: str, **kwargs) -> ConnectionPool:
    """Create an optimized connection pool for analytics workloads."""
    return ConnectionPool(
        database_path=database_path,
        min_connections=kwargs.get('min_connections', 3),
        max_connections=kwargs.get('max_connections', 10),
        enable_wal=True,
        enable_query_cache=True,
        **kwargs
    )