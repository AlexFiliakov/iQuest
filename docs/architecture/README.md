# Apple Health Monitor - Architecture Documentation

This directory contains comprehensive architecture documentation for the Apple Health Monitor application, including system diagrams, class relationships, and design patterns.

## Overview

The Apple Health Monitor is a PyQt6-based desktop application that imports, processes, and visualizes Apple Health data. It uses a layered architecture with clear separation between data processing, business logic, and UI components.

## Architecture Diagrams

### 1. [System Context Diagram](./context_diagram.md)
High-level view of the system showing:
- External data sources (XML, CSV, SQLite)
- Major application components
- External dependencies
- Data flow patterns

### 2. [Module Overview](./module_overview.md)
Detailed module relationships including:
- Module dependencies
- Interaction patterns
- Key design patterns
- Module responsibilities

### 3. Class Diagrams

#### [Core Classes](./class_diagrams/core_classes.md)
- Database management (Singleton pattern)
- Data access objects (DAO pattern)
- Data loader functionality
- Class interactions and sequences

#### [Data Models](./class_diagrams/data_models.md)
- All data model classes
- Database schema (ERD)
- Model relationships
- Serialization patterns

#### [Service Layer & UI](./class_diagrams/service_layer.md)
- UI component hierarchy
- Service layer components
- Signal/slot architecture
- Component lifecycle

## Key Architectural Patterns

### 1. **Layered Architecture**
```
┌─────────────────────────┐
│     UI Layer           │ PyQt6 widgets, signals/slots
├─────────────────────────┤
│   Service Layer        │ Managers, factories, calculators
├─────────────────────────┤
│   Business Logic       │ Filters, statistics, validation
├─────────────────────────┤
│   Data Access Layer    │ DAOs, caching, queries
├─────────────────────────┤
│   Data Layer          │ SQLite, models, schemas
└─────────────────────────┘
```

### 2. **Design Patterns Used**

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| Singleton | DatabaseManager | Single DB connection |
| DAO | Data access objects | Encapsulate DB operations |
| Factory | ComponentFactory | Consistent UI creation |
| Observer | PyQt signals/slots | Event-driven communication |
| Strategy | StatisticsCalculator | Multiple calculation methods |
| Context Manager | Database connections | Resource management |
| Decorator | Error handlers | Cross-cutting concerns |

### 3. **Technology Stack**

- **Frontend**: PyQt6 for cross-platform desktop UI
- **Data Processing**: pandas for DataFrame operations
- **Database**: SQLite for local data storage
- **Visualization**: matplotlib for charts
- **Analytics**: statsmodels, prophet for forecasting

## Quick Navigation

- **New to the codebase?** Start with the [Context Diagram](./context_diagram.md)
- **Working on data import?** See [Core Classes](./class_diagrams/core_classes.md)
- **Adding new features?** Check [Module Overview](./module_overview.md)
- **UI development?** Review [Service Layer & UI](./class_diagrams/service_layer.md)
- **Database changes?** Consult [Data Models](./class_diagrams/data_models.md)

## Maintaining Architecture Docs

When making significant changes:

1. Update relevant diagrams
2. Keep class relationships current
3. Document new patterns
4. Update this README if needed

Use the `.claude/commands/simone/mermaid.md` guide for maintaining diagrams.