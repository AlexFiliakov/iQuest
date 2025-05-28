# Apple Health Monitor - System Context Diagram

This diagram shows the high-level architecture of the Apple Health Monitor application, including external dependencies, data sources, and major component interactions.

```mermaid
flowchart TB
    %% External Data Sources
    subgraph "Data Sources"
        XML[Apple Health XML Export]
        CSV[CSV Files]
        SQLite[SQLite Database]
    end

    %% Core Application
    subgraph "Apple Health Monitor Application"
        direction TB
        
        %% Data Layer
        subgraph "Data Processing Layer"
            DL[data_loader.py<br/>XML/CSV Parser]
            DB[database.py<br/>Database Manager]
            DA[data_access.py<br/>Data Access Objects]
            MOD[models.py<br/>Data Models]
        end
        
        %% Business Logic
        subgraph "Business Logic Layer"
            FILTER[DataFilterEngine<br/>Query & Filter]
            STATS[StatisticsCalculator<br/>Analytics]
            CACHE[CachedMetricDAO<br/>Performance Cache]
        end
        
        %% UI Layer
        subgraph "UI Layer"
            MW[main_window.py<br/>Main Application]
            CT[configuration_tab.py<br/>Import & Config]
            DASH[Dashboard Tabs<br/>Daily/Weekly/Monthly]
            CHARTS[Chart Widgets<br/>WSJ-style Visualizations]
        end
        
        %% Utilities
        subgraph "Utilities"
            ERR[error_handler.py<br/>Exception Management]
            LOG[logging_config.py<br/>Structured Logging]
            CFG[config.py<br/>App Configuration]
        end
    end

    %% External Dependencies
    subgraph "Python Dependencies"
        direction LR
        PD[pandas<br/>Data Analysis]
        QT[PyQt6<br/>Desktop UI]
        MPL[matplotlib<br/>Plotting]
        NP[numpy<br/>Numerics]
        STATS_LIB[statsmodels<br/>Statistics]
        PROPHET[prophet<br/>Forecasting]
    end

    %% User
    USER[End User]

    %% Data Flow
    XML --> DL
    CSV --> DL
    SQLite --> DB
    
    DL --> DB
    DB --> DA
    DA --> MOD
    MOD --> FILTER
    MOD --> STATS
    
    FILTER --> DASH
    STATS --> DASH
    CACHE --> FILTER
    
    CT --> DL
    DASH --> CHARTS
    MW --> CT
    MW --> DASH
    
    USER --> MW
    CHARTS --> USER
    
    %% Utility connections
    ERR -.-> DL
    ERR -.-> DB
    ERR -.-> DA
    LOG -.-> DL
    LOG -.-> DB
    CFG -.-> MW
    CFG -.-> DB
    
    %% External lib usage
    PD -.-> DL
    PD -.-> FILTER
    QT -.-> MW
    MPL -.-> CHARTS
    NP -.-> STATS
    STATS_LIB -.-> STATS
    PROPHET -.-> STATS

    %% Styling
    classDef external fill:#f9f,stroke:#333,stroke-width:2px
    classDef data fill:#bbf,stroke:#333,stroke-width:2px
    classDef ui fill:#bfb,stroke:#333,stroke-width:2px
    classDef util fill:#fbb,stroke:#333,stroke-width:2px
    classDef logic fill:#fbf,stroke:#333,stroke-width:2px
    
    class XML,CSV,SQLite,USER external
    class DL,DB,DA,MOD data
    class MW,CT,DASH,CHARTS ui
    class ERR,LOG,CFG util
    class FILTER,STATS,CACHE logic
    class PD,QT,MPL,NP,STATS_LIB,PROPHET external
```

## Component Overview

### Data Sources
- **Apple Health XML Export**: Primary data source containing all health metrics
- **CSV Files**: Alternative import format for specific metrics
- **SQLite Database**: Processed and indexed data storage

### Data Processing Layer
- **data_loader.py**: Handles XML/CSV parsing and SQLite conversion
- **database.py**: Manages database connections with singleton pattern
- **data_access.py**: Provides DAOs for each entity type
- **models.py**: Defines data structures and schemas

### Business Logic Layer
- **DataFilterEngine**: Complex query building and data filtering
- **StatisticsCalculator**: Computes health metrics and trends
- **CachedMetricDAO**: Performance optimization through caching

### UI Layer
- **main_window.py**: Main application window and navigation
- **configuration_tab.py**: Data import and filter configuration
- **Dashboard Tabs**: Daily, weekly, and monthly health views
- **Chart Widgets**: WSJ-style data visualizations

### Utilities
- **error_handler.py**: Centralized exception handling
- **logging_config.py**: Structured logging with rotation
- **config.py**: Application-wide configuration

### External Dependencies
Key libraries that power the application:
- **pandas**: DataFrame operations and data analysis
- **PyQt6**: Cross-platform desktop UI framework
- **matplotlib**: Scientific plotting and charting
- **numpy**: Numerical computations
- **statsmodels**: Statistical modeling
- **prophet**: Time series forecasting