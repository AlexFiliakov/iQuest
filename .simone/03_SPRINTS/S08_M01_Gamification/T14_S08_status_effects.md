---
task_id: T14_S08
sprint_sequence_id: S08
status: open
complexity: Medium
last_updated: 2025-05-28T12:00:00Z
---

# Task: Implement Status Effects & Environmental Systems

## Description
Create the comprehensive status effect system from the gamification spec featuring positive buffs (Runner's High, Beast Mode), negative debuffs (Leg Day Aftermath, Carb Coma), and environmental hazards that add dynamic gameplay elements to the health tracking experience.

## Goal / Objectives
- Implement positive buff system with duration tracking and visual indicators
- Create negative debuff mechanics that reflect real health consequences humorously
- Build environmental hazard system for gym, home, and workplace settings
- Add status effect interaction system (stacking, cancellation, synergies)
- Include dynamic status effect generation based on user behavior patterns

## Acceptance Criteria
- [ ] Positive buffs implemented with exact spec descriptions:
  - "Runner's High": Reality seems negotiable, everything is possible
  - "Post-Workout Glow": +50 CHA, convinced you're a fitness influencer
  - "Protein Powered": Muscles visibly grow while flexing (imagination +100)
  - "Zen State": Achieved inner peace, or at least inner quiet
  - "Beast Mode": Temporary delusion of invincibility
- [ ] Negative debuffs with humorous but meaningful effects:
  - "Leg Day Aftermath": Stairs become boss battles
  - "Carb Coma": Movement speed -50%, nap resistance -100%
  - "Dehydration Nation": All water fountains appear as mirages
  - "FOMO": Fear of Missing Out on gains, anxiety +20
  - "Workout Brain": INT -30, but STR confidence +50
- [ ] Status effect duration system (temporary: 1-24 hours, contextual triggers)
- [ ] Visual status indicators in character sheet and notifications
- [ ] Status effect stacking and interaction rules
- [ ] Environmental hazard trigger system based on location and behavior
- [ ] Status effect history tracking for analytics and humor

## Important References
- Character System: `T01_S08_character_system.md`
- Boss Battles: `T13_S08_boss_battles.md`
- Gamification Spec: `.simone/02_REQUIREMENTS/SPEC_GAMIFICATION.md`
- UI Framework: `T06_S08_gamification_ui.md`

## Subtasks
- [ ] Create status effect data model with duration, intensity, and stack rules
- [ ] Implement positive buff system with trigger conditions:
  - Runner's High: Post-cardio workout (20+ min moderate+ intensity)
  - Post-Workout Glow: Any workout completion + selfie potential
  - Protein Powered: High protein meal within 2h of strength training
  - Zen State: 15+ minutes meditation or mindfulness activity
  - Beast Mode: Personal record achievement or intensity spike
- [ ] Build negative debuff mechanics with recovery conditions:
  - Leg Day Aftermath: Intense lower body workout, recovers with time/stretching
  - Carb Coma: High carb meal without activity, recovers with movement
  - Dehydration Nation: Low water intake detection, recovers with hydration
  - FOMO: Seeing others' workout posts, recovers with own activity
  - Workout Brain: Intense exercise, recovers gradually over hours
- [ ] Create environmental hazard engine:
  - Gym hazards: wet floors (dex check), mirror walls (narcissism check)
  - Home hazards: fridge raids (willpower save), comfy bed (escape velocity)
  - Workplace hazards: vending machine temptation, elevator vs stairs choice
- [ ] Implement status effect interaction system (buffs cancel debuffs, etc.)
- [ ] Add visual status effect indicators with icons and progress bars
- [ ] Create status effect notification system with humorous descriptions
- [ ] Build status effect analytics (most common effects, duration patterns)
- [ ] Add status effect removal mechanics (actions, items, time passage)
- [ ] Implement status effect intensity scaling based on user fitness level

## Status Effect Mechanics Details

### Buff Trigger Conditions
- **Activity-Based**: Workout completion, meditation sessions, sleep quality
- **Achievement-Based**: Personal records, streak milestones, consistency rewards
- **Time-Based**: Morning workouts (Coffee Buff), late night sessions
- **Social-Based**: Group workouts, sharing achievements, community participation

### Debuff Trigger Conditions
- **Overexertion**: Too much activity triggers mandatory rest periods
- **Poor Choices**: Unhealthy behaviors create temporary stat penalties
- **Environmental**: Location-based triggers (gym intimidation, home comfort zones)
- **Biological**: Natural post-workout effects, hunger, fatigue cycles

### Status Effect Interactions
- **Cancellation**: Zen State cancels FOMO, Protein Powered cancels Carb Coma
- **Stacking**: Multiple positive buffs can stack with diminishing returns
- **Synergy**: Certain combinations create enhanced effects
- **Override**: Some powerful effects temporarily suppress others

## Environmental Hazard System

### Gym Environment
- **Wet Floor Signs**: Dexterity check, failure = embarrassment damage
- **Broken Equipment**: Adaptation challenge, success = problem-solving XP
- **Mirror Walls**: Narcissism save, failure = 10 minutes of flexing
- **That One Machine**: Wisdom check to decipher, teaches humility

### Home Environment  
- **Midnight Fridge**: Willpower save vs. snack temptation
- **The Comfy Bed**: Morning escape velocity calculation
- **Roommate's Pizza**: Charisma check for guilt-free slice
- **Exercise Equipment Storage**: Accessibility check for workout motivation

### Workplace Environment
- **Elevator Temptation**: Convenience vs. stairs, builds character
- **Vending Machine**: Hunger + proximity triggers healthy choice challenge
- **Meeting Room Donuts**: Passive willpower drain, requires active resistance
- **Standing Desk**: Comfort zone challenge, stamina building opportunity

## Technical Implementation Approaches

### Approach 1: Time-Based Effect Engine (Recommended)
**Pros:** Accurate duration tracking, natural expiration, easy to understand
**Cons:** Requires persistent timers, memory overhead for long durations
**Implementation:** Timestamp-based effects with periodic cleanup

### Approach 2: Event-Driven Effect System
**Pros:** More dynamic, responsive to behavior changes, interactive
**Cons:** Complex trigger logic, potential for inconsistent states
**Implementation:** Health data events trigger effect changes

### Approach 3: Hybrid Timer + Event System
**Pros:** Best of both worlds, flexible and accurate
**Cons:** Most complex to implement and debug
**Implementation:** Time-based with event-triggered modifications

## Output Log
*(This section is populated as work progresses on the task)*