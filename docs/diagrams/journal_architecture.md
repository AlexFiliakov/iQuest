# Journal Feature Architecture Diagrams

## Overview

This document contains Mermaid diagrams illustrating the architecture of the journal feature in the Apple Health Monitor application.

## Component Architecture

```mermaid
graph TB
    subgraph "UI Layer"
        JT[JournalTabWidget]
        JE[JournalEditorWidget]
        JH[JournalHistoryWidget]
        JS[JournalSearchWidget]
        JI[JournalIndicators]
        JX[JournalExportDialog]
    end
    
    subgraph "Business Logic Layer"
        JM[JournalManager]
        SE[JournalSearchEngine]
        IS[IndicatorService]
        AS[AutoSaveManager]
        EX[Exporters]
    end
    
    subgraph "Data Access Layer"
        DAO[JournalDAO]
        DB[(SQLite Database)]
        FTS[(FTS5 Index)]
    end
    
    JT --> JE
    JT --> JH
    JT --> JS
    
    JE --> JM
    JE --> AS
    JH --> DAO
    JS --> SE
    JI --> IS
    JX --> EX
    
    JM --> DAO
    SE --> FTS
    IS --> DAO
    AS --> JM
    EX --> DAO
    
    DAO --> DB
    SE --> DB
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant JE as JournalEditor
    participant AS as AutoSaveManager
    participant JM as JournalManager
    participant JW as JournalWorker
    participant DAO as JournalDAO
    participant DB as Database
    
    U->>JE: Type content
    JE->>AS: Content changed
    AS->>AS: Start 3s timer
    Note over AS: Debounce logic
    AS->>JM: Save entry
    JM->>JM: Validate input
    JM->>JW: Queue operation
    JW->>DAO: Save to database
    DAO->>DB: INSERT/UPDATE
    DB-->>DAO: Success
    DAO-->>JW: Entry ID
    JW-->>JM: Operation complete
    JM-->>JE: Entry saved signal
    JE-->>U: Show confirmation
```

## Search System Architecture

```mermaid
graph LR
    subgraph "Search Interface"
        SB[SearchBar]
        SR[SearchResults]
        SF[SearchFilters]
    end
    
    subgraph "Search Engine"
        QP[QueryParser]
        SE[SearchEngine]
        SC[ScoreCalculator]
        HL[Highlighter]
        CA[Cache]
    end
    
    subgraph "Database"
        FTS[FTS5 Index]
        JT[journal_entries]
    end
    
    SB --> QP
    QP --> SE
    SE --> FTS
    SE --> SC
    SE --> CA
    SC --> SR
    HL --> SR
    SF --> SE
    
    FTS -.-> JT
```

## State Management

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> Editing: New/Load Entry
    Editing --> Modified: Content Changed
    Modified --> Saving: Save Triggered
    Modified --> AutoSaving: Auto-save Timer
    
    Saving --> Saved: Success
    Saving --> Error: Failure
    AutoSaving --> Saved: Success
    AutoSaving --> Error: Failure
    
    Saved --> Idle: Clear
    Saved --> Editing: Continue Editing
    Error --> Modified: Retry
    Error --> Idle: Cancel
    
    Modified --> ConfirmDiscard: Navigate Away
    ConfirmDiscard --> Idle: Discard
    ConfirmDiscard --> Modified: Keep Editing
```

## Export System Flow

```mermaid
flowchart TD
    A[User Clicks Export] --> B{Select Export Type}
    B -->|JSON| C[Configure JSON Options]
    B -->|PDF| D[Configure PDF Options]
    
    C --> E[Select Date Range]
    D --> E[Select Date Range]
    
    E --> F[Preview Entry Count]
    F --> G{Confirm Export?}
    
    G -->|Yes| H[Create Exporter]
    G -->|No| I[Cancel]
    
    H --> J[Load Entries]
    J --> K{Export Format}
    
    K -->|JSON| L[Generate JSON]
    K -->|PDF| M[Generate PDF]
    
    L --> N[Write File]
    M --> O[Render PDF]
    O --> N[Write File]
    
    N --> P[Show Success]
    N --> Q[Handle Error]
```

## Journal Entry Types

```mermaid
graph TD
    JE[Journal Entry]
    
    JE --> D[Daily Entry]
    JE --> W[Weekly Entry]
    JE --> M[Monthly Entry]
    
    D --> D1[entry_date: specific date]
    D --> D2[entry_type: 'daily']
    D --> D3[content: daily notes]
    
    W --> W1[entry_date: week end date]
    W --> W2[entry_type: 'weekly']
    W --> W3[week_start_date: Monday]
    W --> W4[content: weekly reflection]
    
    M --> M1[entry_date: month last day]
    M --> M2[entry_type: 'monthly']
    M --> M3[month_year: 'YYYY-MM']
    M --> M4[content: monthly summary]
```

## Database Schema

```mermaid
erDiagram
    journal_entries {
        INTEGER id PK
        DATE entry_date
        TEXT entry_type
        TEXT content
        DATE week_start_date
        TEXT month_year
        INTEGER version
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    journal_entries_fts {
        INTEGER rowid FK
        TEXT content
    }
    
    search_history {
        INTEGER id PK
        TEXT query
        INTEGER result_count
        TIMESTAMP searched_at
    }
    
    journal_drafts {
        INTEGER id PK
        TEXT session_id
        DATE entry_date
        TEXT entry_type
        TEXT content
        TIMESTAMP saved_at
    }
    
    journal_entries ||--|| journal_entries_fts : "FTS index"
```

## Signal Flow

```mermaid
graph LR
    subgraph "JournalManager Signals"
        ES[entrySaved]
        ED[entryDeleted]
        EO[errorOccurred]
        CD[conflictDetected]
    end
    
    subgraph "UI Components"
        JE[JournalEditor]
        JH[JournalHistory]
        JT[JournalTab]
        TN[ToastNotification]
    end
    
    ES --> JH
    ES --> JT
    ES --> TN
    
    ED --> JH
    ED --> JT
    
    EO --> TN
    CD --> JE
```

## Thread Architecture

```mermaid
graph TD
    subgraph "Main Thread"
        UI[UI Components]
        JM[JournalManager]
    end
    
    subgraph "Worker Thread"
        JW[JournalWorker]
        OP[Operation Queue]
    end
    
    subgraph "Database Thread"
        DAO[JournalDAO]
        DB[(Database)]
    end
    
    UI --> JM
    JM --> OP
    OP --> JW
    JW --> DAO
    DAO --> DB
    
    DB -.-> DAO
    DAO -.-> JW
    JW -.-> JM
    JM -.-> UI
```

## Performance Optimization

```mermaid
flowchart LR
    subgraph "Caching Layer"
        IC[Indicator Cache]
        SC[Search Cache]
        EC[Entry Cache]
    end
    
    subgraph "Optimization Techniques"
        VS[Virtual Scrolling]
        DB[Debouncing]
        LP[Lazy Loading]
        BP[Batch Processing]
    end
    
    subgraph "Performance Benefits"
        FR[Fast Response]
        LM[Low Memory]
        SM[Smooth UI]
    end
    
    IC --> FR
    SC --> FR
    EC --> FR
    
    VS --> LM
    LP --> LM
    
    DB --> SM
    BP --> SM
```

## Integration Points

```mermaid
graph TB
    subgraph "Journal Feature"
        JF[Journal Core]
    end
    
    subgraph "Calendar Integration"
        CH[Calendar Heatmap]
        DV[Daily View]
        MV[Monthly View]
    end
    
    subgraph "Analytics Integration"
        HA[Health Analytics]
        TR[Trend Reports]
        CO[Correlations]
    end
    
    subgraph "Export Integration"
        RE[Report Export]
        BA[Backup System]
    end
    
    JF --> CH
    JF --> DV
    JF --> MV
    
    JF --> HA
    JF --> TR
    JF --> CO
    
    JF --> RE
    JF --> BA
    
    style JF fill:#f9f,stroke:#333,stroke-width:4px
```