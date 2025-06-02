---
task_id: T02_S10
sprint_sequence_id: S10
status: open
complexity: Medium
last_updated: 2025-05-28T12:00:00Z
---

# Task: Implement Class System with Activity-Based Assignment

## Description
Implement the full class system from the gamification spec with humorous character classes, multi-classing support, and detailed subclass trees. Each class reflects specific health activity patterns and provides unique stat bonuses, special abilities, and progression paths complete with witty descriptions and class-specific humor.

## Goal / Objectives
- Implement exact 5 base classes: Warrior (Iron Pumper), Ranger (Compulsive Step Counter), Wizard (Zen Overlord), Cleric (Sleep Schedule Evangelist), Rogue (Chaos Athlete)
- Create class assignment algorithm based on 30-day activity dominance patterns
- Add humorous class descriptions and signature moves from the spec
- Implement multi-classing for balanced lifestyles ("The Chronically Indecisive")
- Build subclass progression system with 2 specializations per base class

## Acceptance Criteria
- [ ] All 5 base classes implemented with exact spec bonuses:
  - Warrior: +20% STR, +10% VIT, -5% INT
  - Ranger: +20% DEX, +10% STA, +5% WIS
  - Wizard: +20% INT, +15% WIS, -10% STR
  - Cleric: +15% VIT, +15% WIS, +10% all others
  - Rogue: +15% DEX, +10% CHA, +5% all others
- [ ] Class assignment analyzes 30-day patterns with <40% dominance triggering multi-class
- [ ] Subclass unlocking at level 10 with specialization trees
- [ ] Multi-classing combines top 2 classes at 60% effectiveness
- [ ] Humorous class quotes and descriptions from spec implemented
- [ ] Class special abilities and signature moves functional
- [ ] Class change mechanics allow switching based on new activity patterns
- [ ] Visual class badges with fantasy RPG styling

## Important References
- Character System: `T01_S08_character_system.md`
- UI Components: `src/ui/`
- Analytics Engine: `src/analytics/`
- Style Guide: `.simone/02_REQUIREMENTS/M01/SPECS_UI.md`

## Subtasks
- [ ] Implement exact base class definitions with spec requirements and humor:
  - **Warrior "Iron Pumper"**: High intensity workouts, grunting optional
  - **Ranger "Compulsive Step Counter"**: High steps, outdoor activities, 47 hiking boots
  - **Wizard "Zen Overlord"**: Meditation focus, owns more yoga mats than furniture
  - **Cleric "Sleep Schedule Evangelist"**: Consistent sleep, bedroom for sleeping
  - **Rogue "Chaos Athlete"**: 3 AM gym, noon yoga, midnight runs
- [ ] Create activity pattern analysis engine (30-day rolling window)
- [ ] Implement class assignment thresholds and dominance calculations
- [ ] Build multi-classing system for balanced patterns ("Renaissance Athlete")
- [ ] Add subclass progression trees with 2 specializations each:
  - Warrior → Berserker/Paladin
  - Ranger → Scout/Beastmaster
  - Wizard → Sage/Dreamweaver
  - Cleric → Healer/Monk
  - Rogue → Assassin/Trickster
- [ ] Implement class-specific special abilities and signature moves
- [ ] Create class badge system with fantasy RPG artwork
- [ ] Add humorous class quotes and flavor text throughout UI
- [ ] Build class change detection and notification system
- [ ] Implement "Analysis Paralysis" ability for multi-class users

## Class Assignment Algorithm Details

### Activity Pattern Analysis
- **Warrior Detection**: >40% high-intensity workouts, strength training dominance
- **Ranger Detection**: >40% step-based activities, outdoor exercise preference
- **Wizard Detection**: >40% mindfulness/meditation minutes, low physical intensity
- **Cleric Detection**: >40% consistent sleep patterns, regular bedtime ±30min
- **Rogue Detection**: >40% varied workout times, inconsistent schedule patterns
- **Multi-class Trigger**: No single pattern >40%, combine top 2 at 60% effectiveness

### Technical Implementation Approaches

### Approach 1: Rules-Based Classification (Recommended)
**Pros:** Transparent, predictable, easy to debug and tune
**Cons:** May miss nuanced patterns, requires manual threshold tuning
**Implementation:** Weighted activity pattern scoring with threshold comparisons

### Approach 2: Machine Learning Classification
**Pros:** Can discover hidden patterns, self-improving
**Cons:** Black box decisions, requires training data, overkill for this use case
**Implementation:** Scikit-learn clustering or classification models

### Approach 3: Hybrid Rule-ML System
**Pros:** Best of both worlds, fallback to rules
**Cons:** Most complex, harder to maintain
**Implementation:** ML suggestions with rule-based validation

## Output Log
*(This section is populated as work progresses on the task)*