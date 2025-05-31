# Module Overview

This document provides a comprehensive overview of the 232 Python modules in the Apple Health Monitor Dashboard, organized by their architectural layers and relationships.

## High-Level Module Architecture

```mermaid
flowchart TB
    subgraph "Core Layer (14 modules)"
        MAIN[main.py<br/>Entry Point]
        CONFIG[config.py<br/>Configuration]
        MODELS[models.py<br/>Data Models]
        DB[database.py<br/>DB Manager]
        LOADER[data_loader.py<br/>Import Engine]
        XML[xml_streaming_processor.py<br/>XML Parser]
    end
    
    subgraph "Analytics Engine (71 modules)"
        subgraph "Calculators"
            DAILY_CALC[daily_metrics_calculator.py<br/>Daily Stats]
            WEEKLY_CALC[weekly_metrics_calculator.py<br/>Weekly Stats]
            MONTHLY_CALC[monthly_metrics_calculator.py<br/>Monthly Stats]
        end
        
        subgraph "Advanced Analytics"
            ANOMALY[anomaly_detection.py<br/>Outlier Detection]
            CORRELATION[correlation_analyzer.py<br/>Correlations]
            PREDICT[predictive_analytics.py<br/>Predictions]
        end
        
        subgraph "Health Score System"
            HEALTH_SCORE[health_score_calculator.py<br/>Overall Score]
            COMPONENTS[component_calculators.py<br/>Sub-scores]
        end
        
        CACHE[cache_manager.py<br/>Performance Cache]
    end
    
    subgraph "UI Layer (142 modules)"
        subgraph "Main Windows"
            MAIN_WIN[main_window.py<br/>Application Shell]
            CONFIG_TAB[configuration_tab.py<br/>Settings UI]
            DASH_DAILY[daily_dashboard_widget.py<br/>Daily View]
            DASH_WEEKLY[weekly_dashboard_widget.py<br/>Weekly View]
            DASH_MONTHLY[monthly_dashboard_widget.py<br/>Monthly View]
        end
        
        subgraph "Charts Package (51 modules)"
            CHART_BASE[base_chart.py<br/>Chart Framework]
            LINE_CHART[line_chart.py<br/>Time Series]
            HEATMAP[calendar_heatmap.py<br/>Calendar View]
        end
        
        STYLE[style_manager.py<br/>Theme Engine]
    end
    
    subgraph "Utils Layer (4 modules)"
        ERROR[error_handler.py<br/>Error Management]
        LOG[logging_config.py<br/>Logging]
        VALIDATOR[xml_validator.py<br/>Validation]
    end
    
    %% Key relationships
    MAIN --> MAIN_WIN
    MAIN_WIN --> CONFIG_TAB
    MAIN_WIN --> DASH_DAILY
    MAIN_WIN --> DASH_WEEKLY
    MAIN_WIN --> DASH_MONTHLY
    
    CONFIG_TAB --> LOADER
    LOADER --> XML
    LOADER --> DB
    
    DASH_DAILY --> DAILY_CALC
    DASH_WEEKLY --> WEEKLY_CALC
    DASH_MONTHLY --> MONTHLY_CALC
    
    DAILY_CALC --> CACHE
    WEEKLY_CALC --> CACHE
    MONTHLY_CALC --> CACHE
    
    DASH_DAILY --> LINE_CHART
    DASH_MONTHLY --> HEATMAP
    
    %% Styling
    style MAIN fill:#4ecdc4,color:#fff
    style MAIN_WIN fill:#e8f5e8
    style CACHE fill:#fff8e1
    style DB fill:#f3e5f5
```

## Detailed Module Breakdown by Package

### Core Layer Structure

```mermaid
flowchart LR
    subgraph "Entry & Config"
        MAIN[main.py]
        CONFIG[config.py]
        VERSION[version.py]
    end
    
    subgraph "Data Models"
        MODELS[models.py<br/>• HealthRecord<br/>• JournalEntry<br/>• UserPreference<br/>• ImportHistory<br/>• CachedMetric<br/>• AggregatedData<br/>• DataAvailability]
    end
    
    subgraph "Database Layer"
        DATABASE[database.py<br/>Thread-safe SQLite]
        HEALTH_DB[health_database.py<br/>Health-specific ops]
        DATA_ACCESS[data_access.py<br/>DAO Pattern]
    end
    
    subgraph "Data Processing"
        LOADER[data_loader.py<br/>Import orchestrator]
        XML_PROC[xml_streaming_processor.py<br/>SAX parser]
        FILTER[data_filter_engine.py<br/>Query engine]
        AVAIL[data_availability_service.py<br/>Coverage tracking]
    end
    
    subgraph "Core Services"
        FILTER_MGR[filter_config_manager.py<br/>Filter persistence]
        STATS_CALC[statistics_calculator.py<br/>Basic statistics]
        PREDICT_CORE[predictive_analytics.py<br/>ML predictions]
    end
    
    MAIN --> CONFIG
    MAIN --> MAIN_WIN[To UI Layer]
    LOADER --> XML_PROC
    LOADER --> DATABASE
    DATABASE --> DATA_ACCESS
    FILTER --> DATA_ACCESS
    STATS_CALC --> DATA_ACCESS
    
    style MAIN fill:#4ecdc4,color:#fff
    style DATABASE fill:#f3e5f5
    style LOADER fill:#4ecdc4,color:#fff
```

### Analytics Engine Architecture

```mermaid
flowchart TB
    subgraph "Analytics Orchestration"
        ENGINE[optimized_analytics_engine.py<br/>Main coordinator]
        STREAM_LOAD[streaming_data_loader.py<br/>Data streaming]
        PROG_LOAD[progressive_loader.py<br/>Incremental loading]
        QUEUE[computation_queue.py<br/>Task queue]
    end
    
    subgraph "Metric Calculators"
        DAILY[daily_metrics_calculator.py]
        WEEKLY[weekly_metrics_calculator.py]
        MONTHLY[monthly_metrics_calculator.py]
        CACHED_CALC[cached_calculators.py<br/>Memoized calculations]
        COMP_OVERLAY[comparison_overlay_calculator.py]
    end
    
    subgraph "Pattern Analysis"
        DOW[day_of_week_analyzer.py<br/>Weekly patterns]
        SEASONAL[seasonal_pattern_analyzer.py<br/>Yearly patterns]
        WOW[week_over_week_trends.py<br/>Weekly trends]
        MOM[month_over_month_trends.py<br/>Monthly trends]
    end
    
    subgraph "Advanced Analytics"
        subgraph "Anomaly Detection"
            ANOMALY_SYS[anomaly_detection_system.py]
            ANOMALY_DET[anomaly_detectors.py]
            ENSEMBLE[ensemble_detector.py]
            TEMPORAL[temporal_anomaly_detector.py]
        end
        
        subgraph "Correlation & Insights"
            CORR[correlation_analyzer.py]
            CAUSAL[causality_detector.py]
            STORY[data_story_generator.py]
            INSIGHTS[health_insights_engine.py]
        end
        
        subgraph "Goals & Records"
            GOALS[goal_management_system.py]
            RECORDS[personal_records_tracker.py]
            PEER[peer_group_comparison.py]
            FEEDBACK[feedback_processor.py]
        end
        
        subgraph "Evidence-Based System"
            EVIDENCE_DB[evidence_database.py<br/>Medical guidelines]
            MED_VALID[medical_evidence_validator.py<br/>Validation]
            ANNOTATION[health_annotation_system.py<br/>Data annotation]
            ANNOT_MODELS[annotation_models.py<br/>Annotation types]
        end
        
        subgraph "Advanced Trends & Discovery"
            TREND_ENGINE[advanced_trend_engine.py<br/>Trend analysis]
            TREND_MODELS[advanced_trend_models.py<br/>Trend models]
            CORR_DISC[correlation_discovery.py<br/>Pattern discovery]
            SUMMARY_CALC[summary_calculator.py<br/>Summaries]
        end
        
        subgraph "Export & Reporting"
            EXPORT_SYS[export_reporting_system.py<br/>Report generation]
            OPT_CALC[optimized_calculator_integration.py<br/>Optimized calcs]
        end
    end
    
    subgraph "Performance Layer"
        CACHE[cache_manager.py<br/>LRU + SQLite]
        BG_REFRESH[cache_background_refresh.py]
        CONN_POOL[connection_pool.py<br/>DB connections]
        PERF_MON[performance_monitor.py]
    end
    
    ENGINE --> STREAM_LOAD
    ENGINE --> QUEUE
    ENGINE --> DAILY
    ENGINE --> WEEKLY
    ENGINE --> MONTHLY
    
    DAILY --> CACHE
    WEEKLY --> CACHE
    MONTHLY --> CACHE
    
    ANOMALY_SYS --> ENSEMBLE
    CORR --> INSIGHTS
    INSIGHTS --> STORY
    
    EVIDENCE_DB --> MED_VALID
    ANNOTATION --> ANNOT_MODELS
    INSIGHTS --> EVIDENCE_DB
    
    TREND_ENGINE --> TREND_MODELS
    TREND_ENGINE --> CORR_DISC
    CORR --> CORR_DISC
    
    EXPORT_SYS --> OPT_CALC
    ENGINE --> OPT_CALC
    
    style ENGINE fill:#4ecdc4,color:#fff
    style CACHE fill:#fff8e1
    style INSIGHTS fill:#f3e5f5
    style EVIDENCE_DB fill:#e1f5fe
    style EXPORT_SYS fill:#4ecdc4,color:#fff
```

### UI Layer Components

```mermaid
flowchart TB
    subgraph "Application Shell"
        MAIN_WIN[main_window.py<br/>Tab container]
        STYLE_MGR[style_manager.py<br/>WSJ theming]
        SETTINGS[settings_manager.py<br/>Preferences]
        PREF_TRACK[preference_tracker.py<br/>Usage tracking]
    end
    
    subgraph "Configuration UI"
        CONFIG_TAB[configuration_tab.py]
        ADAPT_CONFIG[adaptive_configuration_tab.py]
        IMPORT_DLG[import_progress_dialog.py]
        IMPORT_WORK[import_worker.py]
    end
    
    subgraph "Dashboard Widgets"
        DAILY_DASH[daily_dashboard_widget.py]
        WEEKLY_DASH[weekly_dashboard_widget.py]
        MONTHLY_DASH[monthly_dashboard_widget.py]
        
        subgraph "Common Components"
            STATS_WID[statistics_widget.py]
            SUMM_CARDS[summary_cards.py]
            TABLE_COMP[table_components.py]
            TIMELINE[activity_timeline_component.py]
        end
        
        subgraph "Specialized Views"
            GOAL_PROG[goal_progress_widget.py]
            TROPHY[trophy_case_widget.py]
            STORY_WID[data_story_widget.py]
            INSIGHTS_WID[health_insights_widget.py]
            HEALTH_SCORE_VIZ[health_score_visualizations.py<br/>Score displays]
            METRIC_COMP[metric_comparison_view.py<br/>Metric comparison]
        end
        
        subgraph "Modern UI Variants"
            CONFIG_MODERN[configuration_tab_modern.py]
            GOAL_MODERN[goal_progress_widget_modern.py]
            DAILY_MODERN[daily_dashboard_widget_modern.py]
            WEEKLY_MODERN[weekly_dashboard_widget_modern.py]
            MONTHLY_MODERN[monthly_dashboard_widget_modern.py]
        end
        
        subgraph "Core UI Services"
            CORE_DASH[core_health_dashboard.py<br/>Dashboard core]
            EXPORT_DLG[export_dialog.py<br/>Export UI]
            COVERAGE_INT[coverage_integration.py<br/>Coverage display]
            COVERAGE_SVC[coverage_service.py<br/>Coverage data]
        end
        
        subgraph "UI Enhancements"
            DIALOG_ANIM[dialog_animations.py<br/>Animations]
            VIEW_TRANS[view_transitions.py<br/>Transitions]
            STYLED_CAL[styled_calendar_widget.py<br/>Styled calendar]
            CELEBRATION[celebration_manager.py<br/>Celebrations]
        end
    end
    
    subgraph "Input Components"
        DATE_EDIT[enhanced_date_edit.py]
        ADAPT_DATE[adaptive_date_edit.py]
        MULTI_SEL[multi_select_combo.py]
        TIME_RANGE[adaptive_time_range_selector.py]
        SMART_DEF[smart_default_selector.py]
    end
    
    subgraph "Visualization Components"
        TREND_IND[daily_trend_indicator.py]
        AVAIL_IND[data_availability_indicator.py]
        COMP_VIZ[comparative_visualization.py]
        CORR_MATRIX[correlation_matrix_widget.py]
        OVERLAY[comparison_overlay_widget.py]
    end
    
    MAIN_WIN --> CONFIG_TAB
    MAIN_WIN --> DAILY_DASH
    MAIN_WIN --> WEEKLY_DASH
    MAIN_WIN --> MONTHLY_DASH
    
    DAILY_DASH --> STATS_WID
    DAILY_DASH --> SUMM_CARDS
    WEEKLY_DASH --> TABLE_COMP
    MONTHLY_DASH --> TIMELINE
    
    CONFIG_TAB --> DATE_EDIT
    CONFIG_TAB --> MULTI_SEL
    
    style MAIN_WIN fill:#e8f5e8
    style DAILY_DASH fill:#e8f5e8
    style STATS_WID fill:#e8f5e8
```

### Charts Subsystem (66 modules)

```mermaid
flowchart TB
    subgraph "Chart Infrastructure"
        BASE[base_chart.py<br/>Abstract base]
        ENH_BASE[enhanced_base_chart.py<br/>Extended features]
        CONFIG[chart_config.py<br/>Configuration]
        FACTORY_MPL[matplotlib_chart_factory.py]
        FACTORY_PQG[pyqtgraph_chart_factory.py]
        RENDER_FACTORY[chart_renderer_factory.py]
        QPAINTER[qpainter_chart_widget.py<br/>QPainter rendering]
    end
    
    subgraph "Chart Types"
        LINE[line_chart.py<br/>Time series]
        ENH_LINE[enhanced_line_chart.py<br/>Interactive]
        BAR[../bar_chart_component.py]
        HEATMAP[calendar_heatmap.py<br/>Monthly view]
        WATERFALL[waterfall_chart.py<br/>Changes]
        STREAM[stream_graph.py<br/>Stacked area]
        BUMP[bump_chart.py<br/>Rankings]
        SMALL_MULT[small_multiples.py<br/>Grid layout]
    end
    
    subgraph "Enhancements"
        ANNOTATE[annotation_renderer.py]
        LAYOUT[annotation_layout_manager.py]
        RESPONSIVE[responsive_chart_manager.py]
        OPTIMIZE[chart_performance_optimizer.py]
        ACCESS[chart_accessibility_manager.py]
        ADAPTIVE[adaptive_chart_renderer.py<br/>Adaptive rendering]
        ANNOTATED_WID[annotated_chart_widget.py<br/>Annotation support]
        ANNOT_INT[annotation_integration.py<br/>Annotation system]
        OPT_STRUCT[optimized_data_structures.py<br/>Data structures]
        OPT_LINE[optimized_line_chart.py<br/>Optimized charts]
        REACTIVE_ENH[reactive_chart_enhancements.py<br/>Reactive features]
        VIZ_PERF[visualization_performance_optimizer.py]
    end
    
    subgraph "Export System"
        EXPORT_MGR[wsj_export_manager.py]
        IMG_EXPORT[image_exporter.py]
        PDF_EXPORT[pdf_export_thread.py]
        HTML_BUILD[html_export_builder.py]
        DATA_EXPORT[data_exporter.py]
        SHARE[share_manager.py]
    end
    
    subgraph "Interactions"
        INTERACT[chart_interaction_manager.py]
        ZOOM[zoom_controller.py]
        BRUSH[brush_selector.py]
        TOOLTIP[wsj_tooltip.py]
        KEYBOARD[keyboard_navigation.py]
        DRILL[drill_down_navigator.py]
        PROG_DRILL[progressive_drill_down.py<br/>Progressive detail]
        CROSSFILTER[crossfilter_manager.py<br/>Cross-filtering]
        PERF_MON_INT[performance_monitor.py<br/>Interaction perf]
    end
    
    subgraph "Advanced Visualizations"
        TREND_VIZ[trend_visualization.py<br/>Trend displays]
        WSJ_SUITE[wsj_health_visualization_suite.py<br/>WSJ style suite]
        WSJ_STYLE[wsj_style_manager.py<br/>WSJ theming]
        SHARE_DASH[shareable_dashboard.py<br/>Sharing support]
        VIZ_EXAMPLE[visualization_example.py<br/>Demo views]
    end
    
    BASE --> LINE
    BASE --> HEATMAP
    ENH_BASE --> ENH_LINE
    
    LINE --> ANNOTATE
    ENH_LINE --> INTERACT
    INTERACT --> ZOOM
    INTERACT --> BRUSH
    
    style BASE fill:#e8f5e8
    style EXPORT_MGR fill:#4ecdc4,color:#fff
    style INTERACT fill:#e8f5e8
```

### Module Statistics Summary

| Package | Module Count | Key Responsibilities |
|---------|--------------|---------------------|
| Core | 14 | Entry point, data models, database, data loading |
| Analytics | 71 | Metrics calculation, anomaly detection, insights |
| └─ Health Score | 6 | Health scoring subsystem |
| └─ Evidence System | 4 | Medical evidence validation |
| └─ Advanced Trends | 4 | Trend analysis and discovery |
| └─ Export/Reporting | 2 | Report generation system |
| UI | 142 | User interface components and widgets |
| └─ Charts | 66 | Visualization components |
| └─ Dashboards | 8 | Dashboard management |
| └─ Accessibility | 9 | WCAG compliance |
| └─ Reactive UI | 4 | Reactive data binding system |
| Utils | 4 | Error handling, logging, validation |
| **Total** | **232** | Complete health monitoring application |

## Key Integration Points

1. **Data Pipeline**: `main.py` → `data_loader.py` → `xml_streaming_processor.py` → `database.py`
2. **Analytics Flow**: `database.py` → calculators → `cache_manager.py` → UI widgets
3. **UI Updates**: Analytics results → dashboard widgets → chart components → user display
4. **Performance**: All analytics use `cache_manager.py` and `connection_pool.py`
5. **Consistency**: `style_manager.py` ensures uniform theming across all UI components