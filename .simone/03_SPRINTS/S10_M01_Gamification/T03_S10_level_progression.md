---
task_id: T03_S10
sprint_sequence_id: S10
status: open
complexity: Medium
last_updated: 2025-05-28T12:00:00Z
---

# Task: Implement Level and Experience Point System

## Description
Implement the comprehensive XP and leveling system from the gamification spec, featuring the exponential progression curve, streak bonuses, and humorous level-up celebrations. This system should encourage sustainable healthy habits while preventing gaming through anti-exploitation measures.

## Goal / Objectives
- Implement exact XP formula: `XP Required = 100 * (Level ^ 1.5)`
- Create all XP sources with specified base values and bonus conditions
- Build streak system with protection and bonuses
- Add anti-gaming measures and variety bonuses
- Include humorous notifications and milestone celebrations

## Acceptance Criteria
- [ ] XP formula matches spec: Level 1→2: 100 XP, Level 10→11: 3,162 XP, Level 50→51: 35,355 XP
- [ ] All XP sources implemented with base values:
  - Daily Login: 10 XP (+5 for streak)
  - Steps: 20 XP per 1000 (double at 10k)
  - Workout Minutes: 2 XP/min (triple for 60+ min)
  - Sleep 7-9 hours: 50 XP (+25 for consistency)
  - Heart Rate Zones: 1 XP/min (x3 in peak zone)
- [ ] Streak system: 2x XP at 7 days, 3x at 30 days, 5x at 100 days
- [ ] Streak protection: One rest day per week, bank up to 3 days
- [ ] Anti-gaming measures: Daily XP caps, variety bonuses, overtraining protection
- [ ] Level rewards: 3 skill points per level, stat boosts every 5 levels
- [ ] Humorous level-up notifications and milestone messages
- [ ] Performance: XP calculations < 50ms for daily batch processing

## Important References
- Character System: `T01_S08_character_system.md`
- Database Schema: `.simone/02_REQUIREMENTS/M01/SPECS_DB.md`
- UI Framework: `src/ui/main_window.py`
- Analytics: `src/analytics/`

## Subtasks
- [ ] Implement exponential level progression formula with exact curve
- [ ] Create comprehensive XP earning system for all health activities
- [ ] Build streak tracking engine with daily/weekly/monthly bonuses
- [ ] Add streak protection mechanics (rest days, insurance system)
- [ ] Implement "Phoenix Mode" - faster streak rebuilding after breaks
- [ ] Create anti-gaming protection systems:
  - Daily XP caps per source (no 1000 bicep curls)
  - Variety bonuses for different activities
  - Overtraining triggers mandatory rest quests
- [ ] Build level reward distribution system (skill points, stat boosts, items)
- [ ] Add humorous milestone celebrations and achievement triggers
- [ ] Create XP visualization with progress bars and streak counters
- [ ] Implement time-based bonus systems (morning workouts, weekend warrior)
- [ ] Add special XP events (New Personal Best: 100 XP, Pizza Powered Performance)

## XP Source Implementation Details

### Core Activity XP
- **Daily Login**: 10 base + 5 streak bonus (max 50/day from streaks)
- **Steps**: 20 XP per 1000, double at 10k+ (max 400/day)
- **Active Minutes**: 2 XP/min, triple for 60+ sessions (max 360/day)
- **Sleep Quality**: 50 XP for 7-9 hours + 25 consistency bonus (max 75/day)
- **Heart Rate Training**: 1 XP/min in zones, 3x in peak (max 180/day)

### Bonus XP Events
- **New PR**: 100 XP one-time per metric type
- **Perfect Week**: 200 XP for hitting all targets 7 days
- **Variety Bonus**: +50% XP when trying 3+ different activities per week
- **Social Workouts**: +25% XP when exercising with others
- **Mindfulness**: 3 XP/min meditation, 2x bonus for 20+ minute sessions

## Technical Implementation Approaches

### Approach 1: Event-Driven XP System (Recommended)
**Pros:** Real-time feedback, accurate tracking, immediate gratification
**Cons:** More complex event handling, requires robust notification system
**Implementation:** Health data changes trigger XP calculation events

### Approach 2: Batch Processing System
**Pros:** Simpler implementation, better performance for large datasets
**Cons:** Delayed feedback, potential for missed edge cases
**Implementation:** Daily/hourly batch jobs calculate XP from accumulated data

### Approach 3: Hybrid Real-time + Batch
**Pros:** Best user experience with performance optimization
**Cons:** Most complex to implement and debug
**Implementation:** Real-time for immediate actions, batch for historical recalculation

## Output Log
*(This section is populated as work progresses on the task)*