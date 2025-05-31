# Apple Health Monitor Dashboard - Architecture Documentation

This directory contains comprehensive architecture documentation for the Apple Health Monitor Dashboard application, including system diagrams, module relationships, and class structures.

## 📚 Documentation Structure

### [System Context & Data Flow](./context_diagram.md)
High-level system context showing how the application interacts with external entities and the overall data flow from Apple Health exports through processing to visualization.

**Key diagrams:**
- System context with external entities
- Detailed data flow pipeline
- Component interaction sequences
- Key design decisions

### [Module Overview](./module_overview.md)
Comprehensive overview of all 207 Python modules organized by architectural layers, showing dependencies and relationships between packages.

**Key sections:**
- High-level module architecture (4 layers)
- Detailed package breakdowns
- Module statistics by category
- Key integration points

### [Class Diagrams](./class_diagrams/)
Detailed UML class diagrams organized by architectural concern:

#### [Core Classes](./class_diagrams/core_classes.md)
Database management, data access patterns, and fundamental data processing classes.
- Database singleton and DAO patterns
- Data loading and XML processing
- Statistics and analytics core
- Configuration management

#### [Data Models](./class_diagrams/data_models.md)
Domain models and database schema design.
- 7 core dataclasses with validation
- Database schema (ER diagrams)
- Analytics models and transformations
- Enumerations and business logic

#### [Service Layer](./class_diagrams/service_layer.md)
UI architecture, service coordination, and component interactions.
- Main window and dashboard structure
- Component factory and UI services
- Analytics orchestration
- Service coordination patterns

## 🏗️ Architecture Overview

The application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         UI Layer (127 modules)          │  PyQt6 widgets, charts, dashboards
├─────────────────────────────────────────┤
│      Service Layer (Coordinators)       │  Orchestration, caching, exports
├─────────────────────────────────────────┤
│     Analytics Engine (61 modules)       │  Calculations, ML, insights
├─────────────────────────────────────────┤
│        Core Layer (14 modules)          │  Models, database, data loading
├─────────────────────────────────────────┤
│         Utils Layer (4 modules)         │  Error handling, logging
└─────────────────────────────────────────┘
```

## 🔑 Key Architectural Patterns

### Design Patterns Used
- **Singleton**: Database connection management
- **Factory**: Component and chart creation
- **Observer**: Settings and preference updates
- **Strategy**: Pluggable algorithms and renderers
- **DAO**: Data access abstraction
- **Command**: Analytics task queuing
- **Facade**: Simplified service interfaces

### Performance Optimizations
- **Multi-level caching**: LRU memory + SQLite persistence
- **Streaming processing**: Large XML file handling
- **Connection pooling**: Database efficiency
- **Progressive loading**: UI responsiveness
- **Background refresh**: Cache warming

### Security & Privacy
- **Local-only processing**: No cloud connectivity
- **Secure storage**: Encrypted journal entries
- **Input validation**: Comprehensive data validation
- **Error handling**: No sensitive data in logs

## 📊 Module Statistics

| Layer | Modules | Purpose |
|-------|---------|---------|
| **Core** | 14 | Entry point, models, database, data import |
| **Analytics** | 71 | Metrics, ML, insights, predictions |
| **UI** | 142 | Windows, widgets, charts, interactions |
| **Utils** | 4 | Cross-cutting concerns |
| **Total** | **232** | Complete application |

### Subsystem Breakdown
- **Charts Package**: 66 modules for visualization
- **Health Score System**: 6 modules for scoring
- **Dashboards**: 8 modules for layouts
- **Accessibility**: 9 modules for WCAG compliance
- **Evidence System**: 4 modules for medical validation
- **Reactive UI**: 4 modules for modern UI patterns
- **Export/Reporting**: 2 modules for report generation

## 🚀 Getting Started

1. **New developers**: Start with [System Context](./context_diagram.md) for the big picture
2. **Module navigation**: Use [Module Overview](./module_overview.md) to find specific components
3. **Implementation details**: Refer to class diagrams for detailed design

## 🔧 Maintaining Documentation

When updating the architecture:

1. **Adding modules**: Update module counts in [Module Overview](./module_overview.md)
2. **New patterns**: Add to relevant class diagrams
3. **Design changes**: Update affected diagrams and this README
4. **Dependencies**: Ensure module relationships are accurate

### Diagram Tools
- Diagrams use Mermaid syntax for easy maintenance
- Test diagrams at [Mermaid Live Editor](https://mermaid.live/)
- Keep diagrams focused on single concepts

## 📈 Architecture Evolution

The architecture has evolved to support:
- **Scalability**: From 100MB to 1GB+ data files
- **Performance**: Sub-200ms UI response times
- **Features**: 60+ analytics capabilities
- **Accessibility**: WCAG 2.1 AA compliance
- **Extensibility**: Plugin architecture for charts

## 🔗 Related Documentation

- [Testing Guide](../testing_guide.md) - Testing patterns and coverage
- [Performance Guide](../performance_tuning_guide.md) - Optimization strategies
- [Development Workflow](../development_workflow.md) - Development processes
- [API Documentation](../api/) - Detailed API references

---

*Last updated: 2025-05-31*