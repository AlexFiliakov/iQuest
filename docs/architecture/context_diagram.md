# Apple Health Monitor Dashboard - System Context Diagram

This diagram shows the high-level architecture of the Apple Health Monitor Dashboard, including external integrations, major system components, and primary data flows.

## System Context

```mermaid
C4Context
    title System Context - Apple Health Monitor Dashboard

    Person(user, "User", "Health data analyst wanting to track and visualize personal health metrics")
    
    System_Boundary(app, "Apple Health Monitor Dashboard") {
        System(ui, "User Interface Layer", "PyQt6-based desktop application with accessibility support")
        System(analytics, "Analytics Engine", "Health data analysis, trending, and scoring")
        System(data, "Data Management", "Import, storage, and access layer")
    }
    
    System_Ext(apple_health, "Apple Health App", "iOS health data export (XML format)")
    System_Ext(csv_data, "CSV Files", "External health data sources")
    System_Ext(sqlite, "SQLite Database", "Local health data storage")
    System_Ext(filesystem, "File System", "Configuration, logs, and cache storage")
    
    Rel(user, ui, "Interacts with", "Mouse, keyboard, accessibility tools")
    Rel(ui, analytics, "Requests analysis", "Qt signals/slots")
    Rel(analytics, data, "Queries data", "DAO pattern")
    Rel(data, sqlite, "Stores/retrieves", "SQL queries")
    Rel(data, apple_health, "Imports from", "XML parsing")
    Rel(data, csv_data, "Imports from", "CSV parsing")
    Rel(app, filesystem, "Reads/writes", "Config, logs, cache files")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Primary Data Flow

```mermaid
flowchart TD
    subgraph "External Data Sources"
        A[Apple Health XML Export]
        B[CSV Health Data]
    end
    
    subgraph "Import & Validation Layer"
        C[XML Streaming Processor]
        D[Data Loader]
        E[XML Validator]
    end
    
    subgraph "Data Management Layer"
        F[Database Manager<br/>Singleton Pattern]
        G[Data Access Objects<br/>DAO Pattern]
        H[SQLite Database<br/>WAL Mode]
    end
    
    subgraph "Analytics Engine"
        I[Daily Metrics Calculator]
        J[Monthly Metrics Calculator]
        K[Cache Manager<br/>3-tier Caching]
        L[Health Score Calculator]
        M[Anomaly Detection]
    end
    
    subgraph "User Interface Layer"
        N[Main Window<br/>Tab-based Navigation]
        O[Configuration Tab]
        P[Dashboard Widgets]
        Q[Chart Components<br/>WSJ Style]
    end
    
    subgraph "Storage & Caching"
        R[L1: Memory Cache<br/>LRU]
        S[L2: SQLite Cache]
        T[L3: Compressed Disk]
        U[User Preferences]
        V[Import History]
    end
    
    %% Data import flow
    A --> C
    B --> D
    C --> E
    D --> E
    E --> F
    
    %% Database operations
    F --> G
    G --> H
    
    %% Analytics processing
    G --> I
    G --> J
    I --> K
    J --> K
    K --> L
    K --> M
    
    %% Caching strategy
    K --> R
    R --> S
    S --> T
    
    %% UI interactions
    N --> O
    N --> P
    P --> Q
    O --> G
    Q --> K
    
    %% Configuration storage
    F --> U
    F --> V
    
    %% Styling
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style H fill:#f3e5f5
    style K fill:#fff3e0
    style N fill:#e8f5e8
    style R fill:#fff8e1
    style S fill:#fff8e1
    style T fill:#fff8e1
```

## Component Interactions

```mermaid
flowchart LR
    subgraph "Presentation Layer"
        UI[UI Components<br/>PyQt6 Widgets]
        CHARTS[Chart Components<br/>Interactive Visualizations]
        CONFIG[Configuration Interface<br/>Data Import & Filtering]
    end
    
    subgraph "Business Logic Layer"
        ANALYTICS[Analytics Engine<br/>Health Data Analysis]
        CACHE[Cache Manager<br/>Performance Optimization]
        FILTERS[Data Filter Engine<br/>Query Building]
    end
    
    subgraph "Data Access Layer"
        DAO[Data Access Objects<br/>CRUD Operations]
        MODELS[Data Models<br/>7 Dataclasses]
        LOADER[Data Loader<br/>XML/CSV Import]
    end
    
    subgraph "Persistence Layer"
        DB[Database Manager<br/>SQLite with WAL]
        FILES[File System<br/>Config & Logs]
    end
    
    %% UI to Business Logic
    UI --> ANALYTICS
    CHARTS --> CACHE
    CONFIG --> FILTERS
    
    %% Business Logic to Data Access
    ANALYTICS --> DAO
    CACHE --> DAO
    FILTERS --> DAO
    LOADER --> MODELS
    
    %% Data Access to Persistence
    DAO --> DB
    MODELS --> DB
    LOADER --> DB
    
    %% Configuration flow
    CONFIG --> FILES
    UI --> FILES
    
    %% Bidirectional data flow
    DAO <--> CACHE
    ANALYTICS <--> CACHE
    
    %% Styling
    style UI fill:#e8f5e8
    style CHARTS fill:#e8f5e8
    style CONFIG fill:#e8f5e8
    style ANALYTICS fill:#fff3e0
    style CACHE fill:#fff8e1
    style FILTERS fill:#fff3e0
    style DAO fill:#f3e5f5
    style MODELS fill:#f3e5f5
    style LOADER fill:#f3e5f5
    style DB fill:#e1f5fe
    style FILES fill:#e1f5fe
```

## Technology Stack Context

```mermaid
graph TB
    subgraph "Desktop Application"
        APP[Apple Health Monitor Dashboard]
    end
    
    subgraph "UI Framework"
        PYQT6[PyQt6<br/>Modern Desktop UI]
        MATPLOTLIB[Matplotlib<br/>Chart Rendering]
        ACCESSIBILITY[Accessibility<br/>WCAG 2.1 AA]
    end
    
    subgraph "Data Processing"
        PANDAS[Pandas<br/>Data Analysis]
        NUMPY[NumPy<br/>Numerical Computing]
        SQLITE3[SQLite3<br/>Database Driver]
    end
    
    subgraph "Development Tools"
        PYTEST[PyTest<br/>Testing Framework]
        SPHINX[Sphinx<br/>Documentation]
        RUFF[Ruff<br/>Code Quality]
    end
    
    subgraph "System Integration"
        PYTHON[Python 3.10+<br/>Runtime Environment]
        OS[Operating System<br/>Windows/Linux/macOS]
        FS[File System<br/>Local Storage]
    end
    
    APP --> PYQT6
    APP --> PANDAS
    APP --> SQLITE3
    
    PYQT6 --> MATPLOTLIB
    PYQT6 --> ACCESSIBILITY
    
    PANDAS --> NUMPY
    SQLITE3 --> FS
    
    APP --> PYTHON
    PYTHON --> OS
    OS --> FS
    
    %% Development dependencies (dashed)
    APP -.-> PYTEST
    APP -.-> SPHINX
    APP -.-> RUFF
    
    %% Styling
    style APP fill:#4caf50,color:#fff
    style PYQT6 fill:#2196f3,color:#fff
    style PANDAS fill:#ff9800,color:#fff
    style SQLITE3 fill:#9c27b0,color:#fff
    style PYTHON fill:#f44336,color:#fff
```

## Key Architectural Principles

1. **Layered Architecture**: Clear separation between presentation, business logic, data access, and persistence layers
2. **Singleton Pattern**: Database manager ensures single connection point with connection pooling
3. **DAO Pattern**: Data access objects provide clean abstraction over database operations
4. **Protocol-Based Design**: Interfaces enable flexibility and testability
5. **3-Tier Caching**: Performance optimization through memory, SQLite, and disk caching
6. **Observer Pattern**: Qt signals/slots enable reactive UI updates
7. **Factory Pattern**: Component factories ensure consistent styling and behavior
8. **Local-First**: All data remains on user's machine for privacy and security

## Security & Privacy Features

- **Local Data Only**: No cloud storage or external data transmission
- **Input Validation**: Comprehensive XML and data validation
- **Secure File Handling**: Proper permissions and path validation
- **Error Isolation**: Secure error messages without data leakage
- **Database Integrity**: Foreign key constraints and transaction safety