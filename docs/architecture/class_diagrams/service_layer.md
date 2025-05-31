# Service Layer Architecture

This document illustrates the service layer architecture, UI components, and their coordination in the Apple Health Monitor Dashboard.

## Main UI Architecture

```mermaid
classDiagram
    class MainWindow {
        -QTabWidget tab_widget
        -ConfigurationTab config_tab
        -DailyDashboardWidget daily_tab
        -WeeklyDashboardWidget weekly_tab  
        -MonthlyDashboardWidget monthly_tab
        -JournalWidget journal_tab
        -StyleManager style_manager
        -SettingsManager settings_manager
        +__init__(parent: QWidget)
        +setup_ui() None
        +setup_tabs() None
        +setup_menu_bar() None
        +setup_status_bar() None
        +load_user_preferences() None
        +save_window_state() None
        -_on_tab_changed(index: int) None
        -_update_status(message: str) None
    }
    
    class ConfigurationTab {
        -DataLoader data_loader
        -FilterConfigManager filter_manager
        -ImportProgressDialog import_dialog
        -EnhancedDateEdit start_date
        -EnhancedDateEdit end_date
        -MultiSelectCombo source_filter
        -MultiSelectCombo type_filter
        +setup_ui() None
        +import_data() None
        +apply_filters() None
        +save_filter_preset() None
        -_on_import_clicked() None
        -_on_filter_changed() None
        -_update_data_statistics() None
    }
    
    class DashboardWidget {
        <<abstract>>
        #DataAccess data_access
        #CacheManager cache_manager
        #ComponentFactory component_factory
        #Logger logger
        +refresh_data() None
        +export_view() None
        #setup_layout() None
        #create_charts() None
        #update_statistics() None
    }
    
    class DailyDashboardWidget {
        -DailyMetricsCalculator calculator
        -LineChart activity_chart
        -StatisticsWidget stats_widget
        -SummaryCards summary_cards
        -ActivityTimeline timeline
        +setup_layout() None
        +create_charts() None
        +update_for_date(date: date) None
        -_create_activity_chart() LineChart
        -_create_heart_rate_chart() LineChart
    }
    
    class WeeklyDashboardWidget {
        -WeeklyMetricsCalculator calculator
        -BarChartComponent weekly_chart
        -TableComponents comparison_table
        -WeekOverWeekWidget wow_widget
        +setup_layout() None
        +create_charts() None
        +update_for_week(week_start: date) None
    }
    
    class MonthlyDashboardWidget {
        -MonthlyMetricsCalculator calculator
        -CalendarHeatmap heatmap
        -MonthOverMonthWidget mom_widget
        -TrophyCaseWidget achievements
        +setup_layout() None
        +create_charts() None
        +update_for_month(year: int, month: int) None
    }
    
    MainWindow *-- ConfigurationTab
    MainWindow *-- DailyDashboardWidget
    MainWindow *-- WeeklyDashboardWidget
    MainWindow *-- MonthlyDashboardWidget
    DashboardWidget <|-- DailyDashboardWidget
    DashboardWidget <|-- WeeklyDashboardWidget
    DashboardWidget <|-- MonthlyDashboardWidget
    
    note for MainWindow "Application shell with tab navigation"
    note for DashboardWidget "Base class for all dashboard views"
```

## Component Factory and UI Services

```mermaid
classDiagram
    class ComponentFactory {
        -Dict~str,Type~ component_registry
        -StyleManager style_manager
        -Logger logger
        +register_component(name: str, component_class: Type) None
        +create_component(name: str, **kwargs) QWidget
        +create_chart(chart_type: str, data: DataFrame) BaseChart
        +create_input(input_type: str, **kwargs) QWidget
        +create_card(card_type: str, data: dict) QWidget
        -_apply_styling(widget: QWidget) None
    }
    
    class StyleManager {
        -Dict~str,str~ color_palette
        -Dict~str,QFont~ fonts
        -str current_theme
        +apply_theme(widget: QWidget) None
        +get_color(name: str) str
        +get_font(style: str) QFont
        +load_stylesheet(path: str) str
        +register_theme(name: str, theme: dict) None
        +switch_theme(name: str) None
    }
    
    class SettingsManager {
        -UserPreference preferences
        -DataAccess data_access
        -Signal settings_changed
        +get_setting(key: str) Any
        +set_setting(key: str, value: Any) None
        +get_all_settings() dict
        +reset_to_defaults() None
        +export_settings(path: str) None
        +import_settings(path: str) None
        -_notify_observers() None
    }
    
    class PreferenceTracker {
        -Dict~str,int~ usage_counts
        -Dict~str,datetime~ last_used
        -DataAccess data_access
        +track_usage(feature: str) None
        +get_most_used() List[str]
        +get_recommendations() List[str]
        +analyze_patterns() dict
        -_update_statistics() None
    }
    
    class SmartDefaultSelector {
        -PreferenceTracker tracker
        -DataAvailabilityService availability
        +get_default_date_range() tuple
        +get_default_metrics() List[str]
        +get_default_view() str
        +suggest_filters() dict
        -_analyze_user_behavior() dict
    }
    
    ComponentFactory --> StyleManager : uses
    SettingsManager --> DataAccess : persists
    PreferenceTracker --> DataAccess : tracks
    SmartDefaultSelector --> PreferenceTracker : analyzes
    
    note for ComponentFactory "Creates styled UI components"
    note for SmartDefaultSelector "ML-based defaults"
```

## Analytics Service Layer

```mermaid
classDiagram
    class AnalyticsOrchestrator {
        -OptimizedAnalyticsEngine engine
        -CacheManager cache_manager
        -ComputationQueue queue
        -Logger logger
        +calculate_metrics(params: dict) dict
        +schedule_calculation(task: AnalyticsTask) str
        +get_task_status(task_id: str) TaskStatus
        +cancel_task(task_id: str) bool
        -_process_queue() None
        -_handle_task_complete(result: dict) None
    }
    
    class HealthInsightsService {
        -HealthInsightsEngine insights_engine
        -CorrelationAnalyzer correlator
        -AnomalyDetectionSystem anomaly_detector
        -DataStoryGenerator story_generator
        +generate_insights(date_range: tuple) List[Insight]
        +find_correlations(metrics: List[str]) List[Correlation]
        +detect_anomalies(metric: str) List[Anomaly]
        +create_narrative(data: dict) str
        -_rank_insights(insights: List[Insight]) List[Insight]
    }
    
    class GoalManagementService {
        -GoalManagementSystem goal_system
        -NotificationManager notifier
        -PersonalRecordsTracker records
        +create_goal(goal: Goal) str
        +update_progress(goal_id: str) None
        +check_achievements() List[Achievement]
        +get_recommendations() List[str]
        -_celebrate_achievement(achievement: Achievement) None
    }
    
    class ExportService {
        -ExportReportingSystem export_system
        -ChartRenderer renderer
        -TemplateEngine template_engine
        +export_dashboard(format: str, options: dict) str
        +export_report(template: str, data: dict) str
        +share_visualization(chart: BaseChart) str
        +batch_export(tasks: List[ExportTask]) None
        -_render_to_format(content: Any, format: str) bytes
    }
    
    class CacheService {
        -CacheManager cache_manager
        -CacheBackgroundRefresh refresher
        -PerformanceMonitor monitor
        +get_or_calculate(key: str, calculator: Callable) Any
        +invalidate_pattern(pattern: str) None
        +get_cache_stats() dict
        +optimize_cache() None
        -_should_refresh(key: str) bool
    }
    
    AnalyticsOrchestrator --> HealthInsightsService : coordinates
    AnalyticsOrchestrator --> CacheService : uses
    HealthInsightsService --> GoalManagementService : informs
    ExportService --> ChartRenderer : renders
    
    note for AnalyticsOrchestrator "Coordinates all analytics"
    note for CacheService "Performance optimization"
```

## UI Component Services

```mermaid
classDiagram
    class ChartService {
        -ChartRendererFactory renderer_factory
        -ChartPerformanceOptimizer optimizer
        -ChartAccessibilityManager accessibility
        +create_chart(type: str, data: DataFrame) BaseChart
        +update_chart(chart: BaseChart, data: DataFrame) None
        +export_chart(chart: BaseChart, format: str) bytes
        +optimize_rendering(chart: BaseChart) None
        -_select_renderer(data_size: int) ChartRenderer
    }
    
    class InteractionService {
        -ChartInteractionManager interaction_manager
        -ZoomController zoom_controller
        -BrushSelector brush_selector
        -DrillDownNavigator drill_down
        +enable_interactions(chart: BaseChart) None
        +handle_zoom(event: ZoomEvent) None
        +handle_selection(event: SelectionEvent) None
        +navigate_detail(context: dict) None
        -_coordinate_interactions() None
    }
    
    class AccessibilityService {
        -AccessibilityManager manager
        -ScreenReaderSupport screen_reader
        -KeyboardNavigation keyboard_nav
        -ColorAccessibility color_manager
        +enable_accessibility(widget: QWidget) None
        +validate_wcag_compliance() ValidationReport
        +generate_alt_text(chart: BaseChart) str
        +apply_high_contrast() None
        -_announce_change(message: str) None
    }
    
    class NotificationService {
        -NotificationManager manager
        -CelebrationManager celebrations
        -ToastNotification toast
        +show_notification(message: str, type: str) None
        +celebrate_achievement(achievement: Achievement) None
        +show_insight(insight: Insight) None
        +queue_notification(notification: Notification) None
        -_manage_notification_stack() None
    }
    
    class ViewTransitionService {
        -ViewTransitions transitions
        -AnimationController animator
        +transition_to(view: str, params: dict) None
        +animate_change(widget: QWidget, animation: str) None
        +preload_view(view: str) None
        -_cleanup_previous_view() None
    }
    
    ChartService --> ChartRendererFactory : uses
    InteractionService --> ChartInteractionManager : manages
    AccessibilityService --> ScreenReaderSupport : coordinates
    NotificationService --> CelebrationManager : triggers
    
    note for AccessibilityService "WCAG 2.1 AA compliance"
    note for ViewTransitionService "Smooth UI transitions"
```

## Service Coordination Pattern

```mermaid
sequenceDiagram
    participant User
    participant MainWindow
    participant DashboardWidget
    participant AnalyticsOrchestrator
    participant CacheService
    participant ChartService
    participant DataAccess
    
    User->>MainWindow: Switch to Daily View
    MainWindow->>DashboardWidget: activate()
    DashboardWidget->>AnalyticsOrchestrator: request_metrics()
    
    AnalyticsOrchestrator->>CacheService: check_cache()
    alt Cache Hit
        CacheService-->>AnalyticsOrchestrator: return cached data
    else Cache Miss
        AnalyticsOrchestrator->>DataAccess: query_data()
        DataAccess-->>AnalyticsOrchestrator: raw data
        AnalyticsOrchestrator->>AnalyticsOrchestrator: calculate_metrics()
        AnalyticsOrchestrator->>CacheService: store_result()
    end
    
    AnalyticsOrchestrator-->>DashboardWidget: metrics data
    DashboardWidget->>ChartService: create_charts()
    ChartService->>ChartService: optimize_rendering()
    ChartService-->>DashboardWidget: chart widgets
    DashboardWidget->>DashboardWidget: update_layout()
    DashboardWidget-->>User: display dashboard
```

## Reactive UI Architecture

```mermaid
classDiagram
    class ReactiveDataBinding {
        -ObservableDict data_sources
        -BindingEngine binding_engine
        -UpdateScheduler scheduler
        +bind(widget: QWidget, path: str, transform: Callable) Binding
        +unbind(binding: Binding) None
        +update_source(path: str, value: Any) None
        +batch_update(updates: dict) None
        -_propagate_changes(path: str) None
        -_schedule_ui_update(widget: QWidget) None
    }
    
    class ReactiveChangeDetection {
        -ChangeDetector detector
        -DiffEngine diff_engine
        -ChangeHistory history
        +track_changes(model: Any) None
        +detect_changes() List[Change]
        +get_change_summary() dict
        +revert_changes(change_id: str) None
        -_compute_diff(old: Any, new: Any) Diff
    }
    
    class ReactiveDataTransformations {
        -TransformationPipeline pipeline
        -DataFlowGraph flow_graph
        -MemoizationCache cache
        +add_transformation(name: str, transform: Callable) None
        +chain_transformations(*transforms: str) Pipeline
        +apply_pipeline(data: Any, pipeline: Pipeline) Any
        +visualize_data_flow() Graph
        -_optimize_pipeline(pipeline: Pipeline) Pipeline
    }
    
    class ReactiveHealthIntegration {
        -HealthDataStream data_stream
        -RealtimeProcessor processor
        -EventDispatcher dispatcher
        +connect_to_health_data() None
        +subscribe_to_metric(metric: str, callback: Callable) str
        +unsubscribe(subscription_id: str) None
        +get_live_metrics() dict
        -_process_health_event(event: HealthEvent) None
    }
    
    class ReactiveComponentBase {
        <<abstract>>
        #ReactiveDataBinding data_binding
        #ReactiveChangeDetection change_detection
        #Logger logger
        +setup_reactive_bindings() None
        +on_data_change(change: Change) None
        #bind_property(property: str, source: str) None
        #transform_data(data: Any) Any
    }
    
    class ModernDashboardWidget {
        -ReactiveHealthIntegration health_integration
        -ReactiveDataTransformations transformations
        -AnimationController animator
        +initialize_reactive_ui() None
        +update_with_animation(data: dict) None
        +apply_modern_theme() None
        -_setup_data_pipelines() None
    }
    
    ReactiveComponentBase <|-- ModernDashboardWidget
    ReactiveComponentBase --> ReactiveDataBinding : uses
    ReactiveComponentBase --> ReactiveChangeDetection : uses
    ModernDashboardWidget --> ReactiveHealthIntegration : integrates
    ModernDashboardWidget --> ReactiveDataTransformations : transforms
    
    ReactiveDataBinding --> BindingEngine : manages
    ReactiveChangeDetection --> DiffEngine : detects
    ReactiveDataTransformations --> TransformationPipeline : processes
    ReactiveHealthIntegration --> EventDispatcher : dispatches
    
    note for ReactiveDataBinding "Two-way data binding with observables"
    note for ReactiveHealthIntegration "Real-time health data streaming"
    note for ModernDashboardWidget "Modern UI with reactive patterns"
```

### Reactive Data Flow

```mermaid
flowchart TB
    subgraph "Data Sources"
        HS[Health Stream]
        DB[Database]
        CACHE[Cache Layer]
        USER[User Input]
    end
    
    subgraph "Reactive Layer"
        BIND[Data Binding]
        DETECT[Change Detection]
        TRANS[Transformations]
        STREAM[Event Stream]
    end
    
    subgraph "UI Components"
        MODERN_DAILY[Modern Daily Dashboard]
        MODERN_WEEKLY[Modern Weekly Dashboard]
        MODERN_MONTHLY[Modern Monthly Dashboard]
        MODERN_CONFIG[Modern Configuration]
    end
    
    HS --> STREAM
    DB --> BIND
    CACHE --> BIND
    USER --> DETECT
    
    STREAM --> TRANS
    BIND --> TRANS
    DETECT --> TRANS
    
    TRANS --> MODERN_DAILY
    TRANS --> MODERN_WEEKLY
    TRANS --> MODERN_MONTHLY
    TRANS --> MODERN_CONFIG
    
    MODERN_DAILY --> USER
    MODERN_WEEKLY --> USER
    MODERN_MONTHLY --> USER
    
    style STREAM fill:#4ecdc4,color:#fff
    style TRANS fill:#f3e5f5
    style BIND fill:#fff8e1
```

## Key Service Layer Patterns

### Dependency Injection
- Services receive dependencies through constructors
- Promotes testability and loose coupling

### Observer Pattern
- Settings changes notify all observers
- Real-time UI updates on data changes

### Command Pattern
- Analytics tasks queued as commands
- Supports undo/redo for user actions

### Facade Pattern
- High-level service interfaces hide complexity
- Simplified API for UI components

### Strategy Pattern
- Pluggable renderers and calculators
- Runtime algorithm selection based on context

### Reactive Patterns
- Observable data sources with automatic UI updates
- Immutable state management with change detection
- Declarative data transformations and pipelines
- Event-driven architecture with stream processing