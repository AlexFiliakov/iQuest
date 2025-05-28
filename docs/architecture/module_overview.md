# Apple Health Monitor - Module Overview

This diagram shows the detailed relationships between modules, their dependencies, and data flow patterns.

```mermaid
flowchart LR
    %% Entry Point
    MAIN[main.py<br/>Application Entry]

    %% Core Modules
    subgraph "Core Data Processing"
        DL[data_loader.py<br/>Import & Parse]
        DB[database.py<br/>DB Management]
        DA[data_access.py<br/>Data Access]
        MOD[models.py<br/>Data Models]
    end

    %% UI Modules
    subgraph "User Interface"
        MW[main_window.py<br/>Main Window]
        CT[configuration_tab.py<br/>Config Tab]
        SM[style_manager.py<br/>Theme Manager]
        MSC[multi_select_combo.py<br/>Multi-Select Widget]
    end

    %% Utility Modules
    subgraph "Utilities"
        ERR[error_handler.py<br/>Error Handling]
        LOG[logging_config.py<br/>Logging]
        CFG[config.py<br/>Configuration]
        VER[version.py<br/>Version Info]
    end

    %% Module Dependencies
    MAIN --> MW
    MAIN --> SM
    MAIN --> LOG
    MAIN --> ERR

    MW --> CT
    MW --> SM
    MW --> CFG
    MW --> VER

    CT --> DL
    CT --> DA
    CT --> MSC
    CT --> ERR

    DL --> DB
    DL --> MOD
    DL --> LOG
    DL --> ERR

    DB --> MOD
    DB --> LOG
    DB --> ERR
    DB --> CFG

    DA --> DB
    DA --> MOD
    DA --> LOG

    %% Utility usage (dotted lines)
    MW -.-> LOG
    CT -.-> LOG
    DL -.-> CFG
    DA -.-> ERR

    %% Styling
    classDef entry fill:#faa,stroke:#333,stroke-width:3px
    classDef core fill:#aaf,stroke:#333,stroke-width:2px
    classDef ui fill:#afa,stroke:#333,stroke-width:2px
    classDef util fill:#ffa,stroke:#333,stroke-width:2px

    class MAIN entry
    class DL,DB,DA,MOD core
    class MW,CT,SM,MSC ui
    class ERR,LOG,CFG,VER util
```

## Module Interaction Patterns

```mermaid
sequenceDiagram
    participant U as User
    participant MW as MainWindow
    participant CT as ConfigurationTab
    participant DL as DataLoader
    participant DB as Database
    participant DA as DataAccess
    participant UI as UI Components

    Note over U,UI: Application Startup
    U->>MW: Launch Application
    MW->>DB: Initialize Database
    DB->>DB: Create/Update Schema
    MW->>CT: Create Configuration Tab

    Note over U,UI: Data Import Flow
    U->>CT: Select Import File
    CT->>DL: Import Data
    DL->>DL: Parse XML/CSV
    DL->>DB: Store in SQLite
    DB->>DA: Update DAOs
    DA->>CT: Return Success
    CT->>U: Show Progress

    Note over U,UI: Data Query Flow
    U->>UI: Apply Filters
    UI->>DA: Query Data
    DA->>DB: Execute SQL
    DB->>DA: Return Results
    DA->>DA: Apply Caching
    DA->>UI: Return DataFrame
    UI->>U: Display Charts
```

## Key Design Patterns

### 1. Singleton Pattern
- **Database Manager**: Ensures single database connection
- **Style Manager**: Consistent theme application

### 2. Data Access Object (DAO) Pattern
- Separate DAO for each entity type
- Abstracts database operations
- Provides caching layer

### 3. Observer Pattern
- PyQt signals/slots for UI updates
- Event-driven architecture

### 4. Decorator Pattern
- Error handling decorators
- Logging decorators
- Performance monitoring

### 5. Context Manager Pattern
- Database connections
- File operations
- Error contexts

## Module Responsibilities

### Core Modules

| Module | Primary Responsibility | Key Functions |
|--------|----------------------|---------------|
| data_loader.py | Data import and conversion | parse_xml(), import_to_sqlite(), query_data() |
| database.py | Database lifecycle management | initialize(), get_connection(), execute_query() |
| data_access.py | Entity-specific data operations | get_all(), get_by_id(), save(), delete() |
| models.py | Data structure definitions | Model classes with validation |

### UI Modules

| Module | Primary Responsibility | Key Functions |
|--------|----------------------|---------------|
| main_window.py | Application shell and navigation | Setup tabs, handle navigation, manage state |
| configuration_tab.py | Import and filter configuration | Import data, configure filters, manage preferences |
| style_manager.py | Visual theme management | Apply warm theme, manage colors |
| multi_select_combo.py | Enhanced dropdown widget | Multi-selection, keyboard navigation |

### Utility Modules

| Module | Primary Responsibility | Key Functions |
|--------|----------------------|---------------|
| error_handler.py | Exception management | Custom exceptions, decorators, context managers |
| logging_config.py | Application logging | Setup loggers, rotation, formatting |
| config.py | Central configuration | Constants, paths, limits |
| version.py | Version tracking | Version string, build info |