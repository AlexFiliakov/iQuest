# Apple Health Monitor - Service Layer & UI Architecture

This diagram shows the service layer components, UI architecture, and their interactions.

```mermaid
classDiagram
    %% Qt Base Classes
    class QMainWindow {
        <<Qt Framework>>
    }
    
    class QWidget {
        <<Qt Framework>>
    }
    
    class QComboBox {
        <<Qt Framework>>
    }

    %% Main UI Components
    class MainWindow {
        -StyleManager style_manager
        -SettingsManager settings_manager
        -ViewTransitionManager transition_manager
        -PersonalRecordsTracker records_tracker
        -QTabWidget tab_widget
        -ConfigurationTab config_tab
        +__init__()
        +setup_ui()
        +create_menus()
        -_on_tab_changed(index: int)
        -_show_help()
        -_show_about()
    }

    class ConfigurationTab {
        -StyleManager style_manager
        -ComponentFactory component_factory
        -DataLoader data_loader
        -FilterConfigManager filter_manager
        -StatisticsCalculator stats_calculator
        -CheckableComboBox device_dropdown
        -CheckableComboBox type_dropdown
        -EnhancedDateEdit start_date
        -EnhancedDateEdit end_date
        +pyqtSignal data_loaded
        +pyqtSignal filters_applied
        +__init__()
        +setup_ui()
        +import_data()
        -_apply_filters()
        -_update_statistics()
    }

    class CheckableComboBox {
        -QStandardItemModel model
        -bool prevent_popup_close
        +pyqtSignal selectionChanged
        +__init__(placeholder: str)
        +add_items(items: List)
        +get_selected_items() List
        +set_selected_items(items: List)
        -_update_text()
        -_on_item_changed(item: QStandardItem)
    }

    %% Service Layer Components
    class StyleManager {
        <<Singleton-like>>
        +COLORS: Dict
        +get_main_stylesheet() str
        +get_button_style() str
        +get_combobox_style() str
        +get_table_style() str
        +get_tab_style() str
        +apply_theme(widget: QWidget)
    }

    class SettingsManager {
        -Dict settings
        +load_settings() Dict
        +save_settings(settings: Dict)
        +get_setting(key: str, default: Any) Any
        +set_setting(key: str, value: Any)
    }

    class ViewTransitionManager {
        -QTabWidget tab_widget
        -Dict animations
        +animate_tab_change(old: int, new: int)
        +set_transition_duration(ms: int)
    }

    class PersonalRecordsTracker {
        -DatabaseManager db_manager
        -Dict records_cache
        +track_record(metric: str, value: float)
        +get_personal_best(metric: str) float
        +get_records_summary() Dict
    }

    class ComponentFactory {
        -StyleManager style_manager
        +create_button(text: str) QPushButton
        +create_date_edit() EnhancedDateEdit
        +create_dropdown(placeholder: str) CheckableComboBox
        +create_summary_card(title: str) SummaryCard
    }

    class FilterConfigManager {
        -PreferenceDAO pref_dao
        +save_filter_config(config: Dict)
        +load_filter_config() Dict
        +reset_filters()
    }

    class StatisticsCalculator {
        -DataFrame data
        +calculate_basic_stats() Dict
        +calculate_trends() Dict
        +calculate_correlations() DataFrame
    }

    class DataFilterEngine {
        +apply_filters(data: DataFrame, filters: Dict) DataFrame
        +validate_filters(filters: Dict) bool
        +get_filter_summary(filters: Dict) str
    }

    %% Relationships
    QMainWindow <|-- MainWindow : inherits
    QWidget <|-- ConfigurationTab : inherits
    QComboBox <|-- CheckableComboBox : inherits

    MainWindow *-- StyleManager : uses
    MainWindow *-- SettingsManager : uses
    MainWindow *-- ViewTransitionManager : uses
    MainWindow *-- PersonalRecordsTracker : uses
    MainWindow *-- ConfigurationTab : contains

    ConfigurationTab *-- StyleManager : uses
    ConfigurationTab *-- ComponentFactory : uses
    ConfigurationTab *-- FilterConfigManager : uses
    ConfigurationTab *-- StatisticsCalculator : uses
    ConfigurationTab *-- CheckableComboBox : contains
    ConfigurationTab ..> DataFilterEngine : uses

    ComponentFactory --> StyleManager : uses
    FilterConfigManager --> PreferenceDAO : uses
    PersonalRecordsTracker --> DatabaseManager : uses

    %% Notes
    note for StyleManager "Centralized theme management"
    note for CheckableComboBox "Custom multi-select widget"
    note for ComponentFactory "Consistent UI component creation"
```

## UI Signal Flow

```mermaid
sequenceDiagram
    participant User
    participant MainWindow
    participant ConfigTab as ConfigurationTab
    participant DataLoader
    participant FilterEngine as DataFilterEngine
    participant StatsCalc as StatisticsCalculator
    participant UI as UI Components

    Note over User,UI: Data Import Flow
    User->>ConfigTab: Click Import
    ConfigTab->>ConfigTab: Show file dialog
    ConfigTab->>DataLoader: Import file
    DataLoader-->>ConfigTab: Progress updates
    ConfigTab->>ConfigTab: Update progress bar
    DataLoader-->>ConfigTab: Import complete
    ConfigTab-->>MainWindow: emit data_loaded
    MainWindow->>MainWindow: Update status

    Note over User,UI: Filter Application Flow
    User->>ConfigTab: Select filters
    ConfigTab->>FilterEngine: Apply filters
    FilterEngine->>FilterEngine: Process DataFrame
    FilterEngine-->>ConfigTab: Filtered data
    ConfigTab->>StatsCalc: Calculate stats
    StatsCalc-->>ConfigTab: Statistics
    ConfigTab->>UI: Update display
    ConfigTab-->>MainWindow: emit filters_applied
```

## Component Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initialization
    
    Initialization --> LoadingSettings: App Start
    LoadingSettings --> ApplyingTheme: Settings Loaded
    ApplyingTheme --> CreatingUI: Theme Applied
    CreatingUI --> Ready: UI Created
    
    Ready --> ImportingData: User Import
    ImportingData --> DataLoaded: Import Complete
    
    Ready --> ApplyingFilters: User Filter
    DataLoaded --> ApplyingFilters: Filter Action
    ApplyingFilters --> Filtered: Filters Applied
    
    Filtered --> UpdatingStats: Calculate
    UpdatingStats --> DisplayingResults: Stats Ready
    DisplayingResults --> Ready: Complete
    
    Ready --> [*]: App Close
```

## Service Layer Patterns

### Manager Pattern
Services that manage cross-cutting concerns:

```python
# Style Manager - Singleton-like theme management
class StyleManager:
    COLORS = {
        'primary': '#D2691E',
        'secondary': '#F4A460',
        # ...
    }
    
    @staticmethod
    def get_main_stylesheet() -> str:
        # Returns complete app stylesheet
        pass

# Settings Manager - Persistent configuration
class SettingsManager:
    def save_settings(self, settings: Dict):
        # Saves to preferences database
        pass
```

### Factory Pattern
Consistent UI component creation:

```python
class ComponentFactory:
    def create_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setStyleSheet(self.style_manager.get_button_style())
        return button
```

### Strategy Pattern
Different calculation strategies:

```python
class StatisticsCalculator:
    def calculate_basic_stats(self) -> Dict:
        # Basic statistics strategy
        pass
    
    def calculate_trends(self) -> Dict:
        # Trend analysis strategy
        pass
```

### Observer Pattern
PyQt's signal/slot mechanism:

```python
class ConfigurationTab(QWidget):
    data_loaded = pyqtSignal(int)  # Emits row count
    filters_applied = pyqtSignal(dict)  # Emits filter summary
```

## Key Design Decisions

1. **Separation of Concerns**: Business logic (data processing, statistics) separated from UI
2. **Consistent Styling**: Centralized StyleManager for uniform appearance
3. **Reusable Components**: Factory pattern for UI consistency
4. **Event-Driven**: Signals/slots for loose coupling
5. **Performance**: Caching in PersonalRecordsTracker and filter results