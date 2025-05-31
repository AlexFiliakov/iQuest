# System Context & Data Flow

This document illustrates the high-level system context and data flow for the Apple Health Monitor Dashboard application.

## System Context Diagram

```mermaid
flowchart TB
    %% External entities
    User[👤 User<br/>Health Data Owner]
    AppleHealth[📱 Apple Health App<br/>XML Export]
    FileSystem[💾 File System<br/>Local Storage]
    
    %% Main system
    System[Apple Health Monitor Dashboard<br/>PyQt6 Desktop Application]
    
    %% Data stores
    SQLite[(SQLite Database<br/>Journal & Cache)]
    
    %% User interactions
    User -->|Exports health data| AppleHealth
    AppleHealth -->|XML file| FileSystem
    User -->|Imports XML| System
    User -->|Views dashboards| System
    User -->|Writes journal| System
    
    %% System interactions
    System -->|Reads XML| FileSystem
    System -->|Stores/Retrieves| SQLite
    System -->|Exports reports| FileSystem
    
    %% Styling
    style System fill:#4ecdc4,color:#fff
    style SQLite fill:#f3e5f5
    style User fill:#e8f5e8
    style AppleHealth fill:#e1f5fe
    style FileSystem fill:#fff8e1
```

## Detailed Data Flow

```mermaid
flowchart LR
    subgraph Input
        XML[XML Export<br/>100MB+]
        CSV[CSV Files<br/>Legacy Support]
    end
    
    subgraph Processing
        Parser[XML/CSV Parser<br/>Streaming Mode]
        Validator[Data Validator<br/>Schema Check]
        Filter[Filter Engine<br/>Date/Type/Source]
        Processor[Data Processor<br/>Pandas DataFrames]
    end
    
    subgraph Storage
        Memory[In-Memory<br/>DataFrames]
        Cache[(Cache Layer<br/>SQLite)]
        Journal[(Journal DB<br/>SQLite)]
    end
    
    subgraph Analytics
        Daily[Daily Metrics<br/>Calculator]
        Weekly[Weekly Metrics<br/>Calculator]
        Monthly[Monthly Metrics<br/>Calculator]
        Anomaly[Anomaly<br/>Detection]
        Correlation[Correlation<br/>Analysis]
        Evidence[Evidence-Based<br/>Analysis]
    end
    
    subgraph Presentation
        Dashboard[Dashboard Views<br/>PyQt6]
        Charts[Charts<br/>Matplotlib]
        Reports[Export Reports<br/>PDF/Excel/CSV]
    end
    
    subgraph "Export & Reporting"
        ExportSys[Export System<br/>Multi-format]
        ReportGen[Report Generator<br/>Templates]
        ShareMgr[Share Manager<br/>Distribution]
        PrintLayout[Print Layout<br/>Manager]
    end
    
    %% Data flow connections
    XML --> Parser
    CSV --> Parser
    Parser --> Validator
    Validator --> Filter
    Filter --> Processor
    Processor --> Memory
    Processor --> Cache
    
    Memory --> Daily
    Memory --> Weekly  
    Memory --> Monthly
    Memory --> Anomaly
    Memory --> Correlation
    Memory --> Evidence
    
    Daily --> Dashboard
    Weekly --> Dashboard
    Monthly --> Dashboard
    Anomaly --> Dashboard
    Correlation --> Dashboard
    Evidence --> Dashboard
    
    Dashboard --> Charts
    Dashboard --> Reports
    Dashboard --> Journal
    
    Charts --> ExportSys
    Dashboard --> ExportSys
    ExportSys --> ReportGen
    ReportGen --> ShareMgr
    ReportGen --> PrintLayout
    ShareMgr --> FileSystem
    PrintLayout --> FileSystem
    
    %% Styling
    style Parser fill:#4ecdc4,color:#fff
    style Processor fill:#4ecdc4,color:#fff
    style Dashboard fill:#e8f5e8
    style Charts fill:#e8f5e8
    style Cache fill:#fff8e1
    style Journal fill:#fff8e1
    style ExportSys fill:#4ecdc4,color:#fff
    style Evidence fill:#e1f5fe
```

## Component Interactions

```mermaid
sequenceDiagram
    participant User
    participant UI as PyQt6 UI
    participant Loader as Data Loader
    participant Processor as Data Processor
    participant Analytics as Analytics Engine
    participant Cache as Cache Manager
    participant DB as SQLite DB
    
    User->>UI: Import Health Data
    UI->>Loader: Load XML/CSV file
    Loader->>Loader: Stream parse large file
    Loader->>Processor: Send data chunks
    Processor->>Processor: Validate & filter
    Processor->>Cache: Check cache
    
    alt Cache miss
        Processor->>Analytics: Calculate metrics
        Analytics->>Cache: Store results
    else Cache hit
        Cache->>Processor: Return cached results
    end
    
    Processor->>UI: Update progress
    UI->>UI: Render dashboards
    UI->>User: Display results
    
    User->>UI: Add journal entry
    UI->>DB: Save entry
    DB->>UI: Confirm save
    UI->>User: Show confirmation
```

## Key Design Decisions

### Data Processing Strategy
- **Streaming for large files**: XML files can exceed 100MB
- **Hybrid approach**: Memory for performance, streaming for scalability
- **Progressive loading**: UI remains responsive during imports

### Caching Architecture
- **Multi-level caching**: Memory (LRU) + SQLite for persistence
- **Metric-based keys**: Cache by metric type, date range, and filters
- **Background refresh**: Keep frequently accessed data fresh

### Security & Privacy
- **Local-only processing**: No cloud connectivity
- **Data stays on device**: All processing happens locally
- **Secure storage**: Journal entries encrypted in SQLite

### Performance Optimizations
- **Lazy loading**: Calculate metrics on-demand
- **Batch processing**: Group similar calculations
- **Concurrent analytics**: Parallel calculation of independent metrics