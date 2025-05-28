# Architecture Overview

This document provides a comprehensive overview of the Apple Health Monitor Dashboard architecture, including system design, component relationships, and key architectural decisions.

## Table of Contents

- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Technology Stack](#technology-stack)
- [Security Considerations](#security-considerations)
- [Performance Optimization](#performance-optimization)
- [Future Extensibility](#future-extensibility)

## System Architecture

The Apple Health Monitor Dashboard follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                      │
│  (PyQt6 UI Components, Charts, Tables, Style Manager)    │
├─────────────────────────────────────────────────────────┤
│                   Business Logic Layer                    │
│  (Analytics Engine, Calculators, Pattern Detection)      │
├─────────────────────────────────────────────────────────┤
│                    Data Access Layer                      │
│  (DAOs, Models, Caching, Query Optimization)            │
├─────────────────────────────────────────────────────────┤
│                    Storage Layer                          │
│  (SQLite Database, File System, Import History)          │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### Data Layer

#### Database Manager (`src/database.py`)
- Singleton pattern implementation for database connection management
- SQLite with WAL mode for improved concurrency
- Automatic schema initialization and migration support
- Connection pooling and transaction management

#### Data Access Objects (`src/data_access.py`)
Provides abstraction for database operations:
- **JournalDAO**: Manages journal entries with full CRUD operations
- **PreferencesDAO**: User preferences and settings persistence
- **RecentFilesDAO**: Track recently accessed files
- **CacheDAO**: Performance caching with TTL support
- **MetricsDAO**: Health metrics metadata storage
- **DataSourcesDAO**: Track imported data sources
- **ImportHistoryDAO**: Maintain import audit trail

#### Data Models (`src/models.py`)
Type-safe dataclasses for all entities:
```python
@dataclass
class HealthMetricsMetadata:
    metric_type: str
    source_name: str
    unit: Optional[str]
    creation_date: Optional[datetime]
    # ... additional fields
```

### Presentation Layer

#### Main Window (`src/ui/main_window.py`)
- Central application controller
- Tab-based navigation system
- Keyboard shortcut management
- Window state persistence

#### Configuration Tab (`src/ui/configuration_tab.py`)
- Data import interface (XML/CSV)
- Advanced filtering options
- Date range selection
- Source and metric type filtering

#### Visualization Components
- **Summary Cards**: Key metrics display with animations
- **Charts**: Matplotlib-based interactive visualizations
- **Tables**: Sortable, filterable data grids
- **Timeline**: Activity visualization over time
- **Heatmaps**: Calendar-based metric density

#### Style Management (`src/ui/style_manager.py`)
- Centralized theme management
- Warm color palette (tan #F5E6D3, orange #FF8C42, yellow #FFD166)
- Consistent styling across all components
- Dark mode support (future)

### Business Logic Layer

#### Analytics Engine
- **Daily Metrics Calculator**: Computes min/max/average/sum statistics
- **Weekly Metrics Calculator**: 7-day rolling averages and trends
- **Monthly Metrics Calculator**: Monthly aggregations and comparisons
- **Pattern Analyzers**: Detect behavioral patterns (Weekend Warrior, etc.)

#### Advanced Analytics
- **Correlation Engine**: Identify relationships between metrics
- **Anomaly Detection**: Statistical and ML-based outlier detection
- **Personal Records Tracker**: Achievement tracking and celebrations
- **Trend Analysis**: Linear regression and forecasting

#### Data Processing (`src/data_loader.py`)
- XML to SQLite conversion with streaming parser
- CSV import with pandas integration
- Data validation and error handling
- Progress tracking for large files

### Support Systems

#### Error Handling (`src/utils/error_handler.py`)
- Decorator-based error handling
- Context-aware error messages
- User-friendly error display
- Automatic error logging

#### Logging (`src/utils/logging_config.py`)
- Structured logging with rotation
- Separate error log files
- Configurable log levels
- Performance metrics logging

## Data Flow

### Import Flow
```
User selects file → Validation → Parser → 
Database Transaction → Import History → UI Update
```

### Query Flow
```
UI Request → DAO Layer → Cache Check → 
Database Query → Analytics Processing → 
Cache Update → UI Response
```

### Analytics Flow
```
Raw Data → Filter Application → Calculation → 
Statistical Analysis → Visualization → Display
```

## Design Patterns

### Singleton Pattern
Used for DatabaseManager to ensure single point of database access:
```python
class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Data Access Object (DAO) Pattern
Abstracts database operations for maintainability:
```python
class BaseDAO:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create(self, entity):
        # Implementation
```

### Observer Pattern
PyQt6 signals and slots for event-driven architecture:
```python
data_imported = pyqtSignal(str)  # Emitted when import completes
filter_changed = pyqtSignal(dict)  # Emitted when filters update
```

### Strategy Pattern
Different calculation strategies for metrics:
```python
class MetricsCalculator(ABC):
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> Dict:
        pass
```

### Factory Pattern
Component creation with consistent configuration:
```python
class ComponentFactory:
    @staticmethod
    def create_summary_card(card_type: str, **kwargs):
        # Returns appropriate card component
```

## Technology Stack

### Core Technologies

- **Python 3.10+**: Modern Python features and type hints
- **PyQt6**: Cross-platform UI framework
- **SQLite**: Embedded database with excellent performance
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Scientific plotting and visualization

### Development Tools

- **pytest**: Comprehensive testing framework
- **PyInstaller**: Windows executable packaging
- **Black**: Code formatting
- **Pylint**: Code quality checks

### Key Libraries

- **lxml**: Efficient XML parsing
- **python-dateutil**: Date parsing and manipulation
- **numpy**: Numerical computations
- **scipy**: Statistical analysis

## Security Considerations

### Data Privacy
- All data stored locally on user's machine
- No network communication or cloud storage
- Encrypted preferences storage (future)

### Input Validation
- Strict XML schema validation
- SQL injection prevention through parameterized queries
- File type verification before import

### Error Handling
- No sensitive data in error messages
- Secure logging practices
- Graceful degradation on errors

## Performance Optimization

### Database Optimization
- Comprehensive indexing strategy
- Query optimization with EXPLAIN ANALYZE
- Batch operations for bulk imports
- Connection pooling

### Memory Management
- Streaming XML parser for large files
- Chunked data processing
- Efficient pandas operations
- Memory profiling in development

### Caching Strategy
- TTL-based cache for expensive calculations
- Invalidation on data changes
- Memory-limited cache size
- Cache warming on startup

### UI Responsiveness
- Asynchronous operations for long tasks
- Progress indicators for user feedback
- Lazy loading for large datasets
- Virtual scrolling in tables

## Future Extensibility

### Plugin Architecture
- Planned support for custom analytics plugins
- Extensible visualization types
- Custom data importers

### API Development
- RESTful API for external integrations
- Export capabilities (PDF, Excel)
- Webhook support for automation

### Cloud Features
- Optional cloud backup
- Multi-device synchronization
- Sharing capabilities

### Advanced Analytics
- Machine learning predictions
- Advanced statistical models
- Real-time health monitoring
- Integration with wearables

## Architectural Decisions

### Why SQLite?
- Zero configuration required
- Excellent performance for desktop applications
- ACID compliance
- Small footprint

### Why PyQt6?
- Native look and feel
- Comprehensive widget library
- Excellent documentation
- Cross-platform compatibility

### Why Layered Architecture?
- Clear separation of concerns
- Easy testing and maintenance
- Technology independence
- Scalability

## Conclusion

The Apple Health Monitor Dashboard architecture prioritizes:
- **User Experience**: Fast, responsive interface with warm aesthetics
- **Data Integrity**: Robust validation and error handling
- **Performance**: Optimized queries and caching
- **Maintainability**: Clean code structure and patterns
- **Extensibility**: Plugin architecture and modular design

This architecture provides a solid foundation for current features while allowing for future growth and enhancement.