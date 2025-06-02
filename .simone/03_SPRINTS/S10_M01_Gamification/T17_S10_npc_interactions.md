---
task_id: T17_S10
sprint_sequence_id: S10
status: open
complexity: Low
last_updated: 2025-05-28T12:00:00Z
---

# Task: Implement NPC Interactions & Special Vendors

## Description
Create the NPC (Non-Player Character) interaction system from the gamification spec addendum, featuring gym personalities like "Chad the Bro" and "Karen the Cardio Queen", special vendors like "Protein Pete's Powder Emporium", and the mysterious NPCs that add personality and humor to the health journey experience.

## Goal / Objectives
- Implement gym NPC encounters with personality-driven interactions
- Create special vendor system for purchasing power-ups and equipment
- Add mysterious NPCs that provide wisdom and special abilities
- Build social interaction challenges and relationship systems
- Include humorous dialogue and personality-driven quest mechanics

## Acceptance Criteria
- [ ] Gym NPCs implemented with unique personalities:
  - "Chad the Bro": Offers unsolicited advice, "Spot Me Bro" quest
  - "Karen the Cardio Queen": Treadmill hoarding challenge
  - "The Ghost of Workouts Past": Motivational mirror appearances
- [ ] Special vendor system functional:
  - "Protein Pete's Powder Emporium": Sells potions and scrolls
  - "The Mysterious Yoga Instructor": Random park appearances, secret poses
- [ ] NPC interaction mechanics with dialogue trees and consequences
- [ ] Currency system using "Sweat Tokens" earned through workouts
- [ ] NPC-specific quest chains and relationship progression
- [ ] Randomized NPC encounters based on location and activity type
- [ ] NPC personality persistence and relationship memory

## Important References
- Quest System: `T12_S08_quest_system.md`
- Item System: `T05_S08_item_system.md`
- Achievement System: `T07_S08_achievements.md`
- Gamification Spec Addendum: `.simone/02_REQUIREMENTS/SPEC_GAMIFICATION_ADDENDUM.md`

## Subtasks
- [ ] Create NPC data model with personality traits, dialogue trees, and quest chains
- [ ] Implement gym NPC encounters:
  - Chad the Bro: Unsolicited advice, spotting quests, "Bro Code" skill unlock
  - Karen the Cardio Queen: Cardio machine challenges, endurance competitions
  - Ghost of Workouts Past: Mirror appearances, motivational haunting
- [ ] Build special vendor system:
  - Protein Pete: Potions of Gains, Elixir of Recovery, Meal Prep Scrolls
  - Mysterious Yoga Instructor: Secret poses, meditation metaphors, park encounters
- [ ] Create "Sweat Tokens" currency system earned through workout intensity
- [ ] Implement NPC dialogue system with branching conversations
- [ ] Add NPC quest mechanics with unique rewards and story progression
- [ ] Build randomized encounter system based on workout location/type
- [ ] Create NPC relationship tracking with friendship/reputation levels
- [ ] Add NPC personality quirks and memorable catchphrases
- [ ] Implement social challenge mechanics (outlasting Karen, impressing Chad)

## NPC Personality Profiles

### Gym NPCs
- **Chad the Bro**
  - Personality: Enthusiastic, helpful, slightly overwhelming
  - Catchphrases: "Spot me, bro!", "Do you even lift?", "Protein gains, bro!"
  - Quests: Teaching proper form, spotting challenges, supplement education
  - Rewards: "Bro Code" skill (+10% STR when working out with others)

- **Karen the Cardio Queen**
  - Personality: Territorial, competitive, cardio obsessed
  - Behavior: Hoards treadmills, judges others' pace, marathon stories
  - Challenges: Outlast her on adjacent machines, cardio endurance contests
  - Rewards: "Endurance Legend" achievement, cardio efficiency bonuses

- **The Ghost of Workouts Past**
  - Personality: Nostalgic, motivational, slightly guilt-inducing
  - Appearance: Mirrors during rest periods, reflection moments
  - Messages: "Remember when you could do 20 push-ups?", inspirational memories
  - Effect: Motivation boosts, workout intensity reminders

### Special Vendors

- **Protein Pete's Powder Emporium**
  - Location: Appears near gym areas and supplement stores
  - Inventory: Potions of Gains (temporary STR boost), Elixir of Recovery (faster rest)
  - Currency: Sweat Tokens earned through workout intensity
  - Personality: Overly enthusiastic about protein, counts macros obsessively

- **The Mysterious Yoga Instructor**
  - Location: Random park appearances, meditation areas
  - Services: Teaches secret poses, meditation techniques
  - Dialogue: Speaks only in metaphors about inner peace and balance
  - Rewards: Hidden stat bonuses, "Zen Master" progression paths

## NPC Interaction Mechanics

### Encounter Triggers
- **Location-Based**: Gym NPCs appear during workout sessions
- **Activity-Based**: Cardio activities trigger Karen encounters
- **Time-Based**: Ghost appears during rest periods or missed workouts
- **Random Events**: Mysterious instructor appears during outdoor activities

### Dialogue System
- **Branching Conversations**: Multiple response options with consequences
- **Personality Responses**: NPC reactions based on user's class and stats
- **Memory System**: NPCs remember previous interactions and progress
- **Humor Integration**: Witty responses and personality-driven comedy

### Quest Mechanics
- **NPC-Specific Quests**: Each character offers unique challenges
- **Relationship Progression**: Better rewards as friendship/respect increases
- **Repeatable Content**: Daily/weekly interactions for ongoing engagement
- **Story Arcs**: Multi-part quest chains revealing NPC backstories

### Currency and Trading
- **Sweat Token Economy**: Earned through workout intensity and consistency
- **Vendor Inventories**: Rotating stock with seasonal items
- **Price Scaling**: Costs adjust based on user level and relationship
- **Special Offers**: Discounts for loyal customers or achievement holders

## Technical Implementation Approaches

### Approach 1: State Machine NPC System (Recommended)
**Pros:** Predictable behavior, easy to debug, consistent personality
**Cons:** May feel scripted, limited dynamic responses
**Implementation:** NPC state machines with trigger-based transitions

### Approach 2: AI-Driven Personality Engine
**Pros:** More natural conversations, adaptive responses, emergent behavior
**Cons:** Complex implementation, unpredictable responses, resource intensive
**Implementation:** Natural language processing with personality models

### Approach 3: Template-Based Dialogue System
**Pros:** Easy content creation, predictable responses, translation-friendly
**Cons:** Limited flexibility, may feel repetitive over time
**Implementation:** Template engine with variable substitution and branching

## Output Log
*(This section is populated as work progresses on the task)*