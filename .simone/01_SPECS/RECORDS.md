# Records and Badges System Specification

## Overview
The Records and Badges system in Apple Health Monitor tracks personal achievements and milestones based on real health data from Apple Health exports. The system consists of two main components: Personal Records Tracker and Achievement System.

## Current Implementation Status

### Data Source: REAL DATA
- **Records are tied to actual Apple Health data**, not dummy data
- Records are generated from imported XML health data files
- Calculations are performed on actual health metrics (steps, heart rate, sleep, etc.)
- Achievement unlocks are based on real performance milestones

### Core Components

#### 1. Personal Records Tracker (`src/analytics/personal_records_tracker.py`)

**Purpose**: Tracks various types of personal records across health metrics

**Record Types**:
- `SINGLE_DAY_MAX` - Highest value recorded in a single day
- `SINGLE_DAY_MIN` - Lowest value recorded in a single day  
- `ROLLING_7_DAY` - Best 7-day rolling average
- `ROLLING_30_DAY` - Best 30-day rolling average
- `ROLLING_90_DAY` - Best 90-day rolling average
- `CONSISTENCY_STREAK` - Consecutive days with data
- `GOAL_STREAK` - Consecutive days meeting goals
- `IMPROVEMENT_STREAK` - Consecutive days of improvement
- `IMPROVEMENT_VELOCITY` - Rate of improvement over time
- `DAILY_CONSISTENCY` - Regular daily data tracking

**Data Storage**:
- Records stored in SQLite database tables:
  - `personal_records` - Individual record achievements
  - `achievements` - Unlocked badges and milestones
  - `streaks` - Current and historical streak data

**Record Processing**:
- Real-time checking when new health data is imported
- Automatic detection of new records during data processing
- Calculation of improvement margins and percentages
- Streak tracking with start/end dates

#### 2. Trophy Case Widget (`src/ui/trophy_case_widget.py`)

**Purpose**: UI component displaying records and achievements

**Features**:
- **Records Tab**: Displays personal records with filtering by metric and type
- **Badges Tab**: Shows achievement badges with rarity-based styling
- **Statistics Tab**: Summary statistics and breakdowns
- Real-time updates when new records are achieved
- Export functionality for sharing achievements

**Badge System**:
- Badge definitions with conditions for unlocking
- Rarity levels: Common, Rare, Legendary
- Visual styling based on achievement status (earned vs locked)
- Achievement notifications with confetti animations

#### 3. Achievement System

**Badge Categories**:
- **First Steps**: Initial milestones (first record, basic achievements)
- **Consistency**: Streak-based achievements (7-day, 30-day, 100-day streaks)
- **Improvement**: Progress-based badges (50%+ improvements, big leaps)
- **Milestone**: Metric-specific achievements (step goals, sleep targets)

**Badge Definitions** (from code):
- "Record Breaker" - Set your first personal record (common)
- "Week Warrior" - Maintain a 7-day streak (common)
- "Monthly Master" - Maintain a 30-day streak (rare)
- "Centurion" - Maintain a 100-day streak (legendary)
- "Big Leap" - Improve a record by 50% or more (rare)

### Integration Points

#### 1. Main Window Integration
- Trophy Case tab available in main application (`🏆 Records`)
- Connected to PersonalRecordsTracker instance
- Tooltip: "View personal records, achievements, and streaks"

#### 2. Data Processing Integration
- Records checking triggered during health data import
- Automatic processing when new metric values are loaded
- Integration with daily/weekly/monthly metric calculators

#### 3. Celebration System (`src/ui/celebration_manager.py`)
- Confetti animations for record achievements
- Achievement notification popups
- Celebration levels based on record importance
- Social sharing functionality for milestones

## Current Behavior

### Record Detection
1. **Triggered by**: Health data import/processing
2. **Process**: 
   - New metric values compared against existing records
   - Rolling averages calculated for time-window records
   - Streak continuity checked and updated
   - Improvement margins calculated
3. **Storage**: Records saved to database with metadata

### Achievement Unlocking
1. **Triggered by**: New record creation
2. **Process**:
   - Badge conditions evaluated against new record
   - Unlocked achievements stored with timestamps
   - Celebration effects triggered for user feedback
3. **Persistence**: Achievements remain unlocked permanently

### UI Display
1. **Records Display**: 
   - Grid layout with record cards
   - Filtering by metric type and record category
   - Real-time updates when new records achieved
2. **Badge Display**:
   - Visual distinction between earned and locked badges
   - Rarity-based color coding and styling
   - Achievement dates for earned badges

## Data Flow

```
Apple Health XML → Data Import → Metric Processing → Record Checking → Achievement System → UI Display
                                      ↓
                              Database Storage ← Trophy Case Widget
```

## Configuration

### Database Schema
- **personal_records**: id, record_type, metric, value, date, previous_value, improvement_margin, window_days, streak_type, metadata, created_at
- **achievements**: id, badge_id, name, description, icon, rarity, unlocked_date, trigger_record_id, metadata, created_at  
- **streaks**: id, metric, streak_type, current_length, best_length, start_date, end_date, best_start_date, best_end_date, is_active, updated_at

### Supported Metrics
- All Apple Health quantity types (steps, heart rate, weight, etc.)
- All Apple Health category types (sleep analysis, workouts, etc.)
- Custom calculated metrics from analytics engine

## Key Features

### Real Data Processing
- ✅ Records based on actual imported health data
- ✅ Dynamic record detection during data processing
- ✅ Persistent storage in SQLite database
- ✅ Historical tracking with timestamps

### Achievement System
- ✅ Badge definitions with unlock conditions
- ✅ Rarity-based badge categories
- ✅ Achievement persistence and display
- ✅ Celebration effects and notifications

### User Interface
- ✅ Dedicated Trophy Case tab in main application
- ✅ Filterable record and badge displays
- ✅ Statistics and summary views
- ✅ Export and sharing capabilities

## Implementation Notes

### Sample Data Usage
- Sample data is **only** used when no real records exist in database
- Purpose is to demonstrate UI functionality for new users
- Sample data is replaced immediately when real records are created
- Sample achievements include realistic health milestones

### Performance Considerations
- Record checking optimized for real-time processing
- Database indexes on frequently queried fields
- Efficient streak tracking with incremental updates
- UI updates batched to prevent excessive redraws

### Future Enhancements
- Advanced achievement categories (seasonal, challenge-based)
- Social features for comparing achievements
- Custom goal setting and tracking
- Integration with Apple Health workout types
- Gamification elements (points, levels, leaderboards)