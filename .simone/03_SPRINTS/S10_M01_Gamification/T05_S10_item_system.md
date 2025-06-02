---
task_id: T05_S10
sprint_sequence_id: S10
status: open
complexity: Medium
last_updated: 2025-05-28T12:00:00Z
---

# Task: Create Item and Equipment System

## Description
Implement the comprehensive item and equipment system from the gamification spec, featuring 6 equipment slots, 5 rarity tiers with specific drop rates, equipment set bonuses, and hilariously named items like "The Apple Watch of Omniscient Judgment" and "Schrodinger's Gym Bag".

## Goal / Objectives
- Implement exact 6 equipment slots with stat focus from spec
- Create 5 rarity tiers with specified drop rates (60% Common to 1% Legendary)
- Build 50+ unique items with humorous names and meaningful stat bonuses
- Add equipment set bonus system (Morning Person, Night Owl, Procrastinator's Paradox)
- Create item acquisition through achievements, levels, and quest completion

## Acceptance Criteria
- [ ] 6 equipment slots implemented: Head (INT/WIS), Chest (VIT/HP), Legs (STA/DEX), Feet (DEX/Speed), Weapon (STR/Primary), Accessory (Various)
- [ ] 5 rarity tiers with exact drop rates:
  - Common (Gray): 60% drop rate, +5-10% single stat
  - Uncommon (Green): 25% drop rate, two +10-15% bonuses
  - Rare (Blue): 10% drop rate, multiple bonuses + special effect
  - Epic (Purple): 4% drop rate, major bonuses + unique ability
  - Legendary (Orange): 1% drop rate, massive bonuses + game-changing effect
- [ ] 50+ unique items with humorous names and descriptions from spec
- [ ] Equipment set bonuses for 3+ complete sets (Morning Person, Night Owl, Procrastinator's Paradox)
- [ ] Item acquisition through achievements, level milestones, quest rewards, workout drops
- [ ] Equipment comparison tooltips showing stat changes
- [ ] Item effects system (auto-skips ads, reminds to drink water, etc.)
- [ ] Drag-and-drop equipment management with visual feedback

## Important References
- Character System: `T01_S08_character_system.md`
- Database: `.simone/02_REQUIREMENTS/M01/SPECS_DB.md`
- UI Framework: `src/ui/`
- Achievement System: `T07_S08_achievements.md`

## Subtasks
- [ ] Create comprehensive item database with 50+ items across all rarity tiers
- [ ] Implement exact equipment slots with stat focus areas:
  - Head: "Coffee-Stained Workout Shirt", "Bluetooth Earbuds of Selective Deafness"
  - Chest: Armor pieces focusing on VIT/HP bonuses
  - Legs: Movement and stamina focused gear
  - Feet: Speed and dexterity focused footwear
  - Weapon: Dumbbells, yoga mats, water bottles with STR bonuses
  - Accessory: Fitness trackers, medals, charms with varied effects
- [ ] Build rarity system with exact drop rate percentages and color coding
- [ ] Implement item special effects system ("Zone Out", "Hydro Homie", "Stand Up!")
- [ ] Create equipment set bonus engine for complete sets:
  - Morning Person Set (4 pieces): +20% XP before noon, Early Bird Special
  - Night Owl Gear (3 pieces): +30% XP after 8 PM, Midnight Run stealth
  - Procrastinator's Paradox (5 pieces): Last-minute +40% XP, Clutch Performance
- [ ] Add item acquisition mechanics (achievement rewards, level drops, quest completion)
- [ ] Build equipment comparison system with stat change previews
- [ ] Create inventory grid UI with filtering by rarity and type
- [ ] Implement drag-and-drop equipment with visual slot highlighting
- [ ] Add item tooltip system with humor text and stat breakdown
- [ ] Create equipment visual customization (character appearance changes)

## Featured Items Implementation

### Legendary Items (1% drop rate)
- **"The Apple Watch of Omniscient Judgment"**: +25% all stats, auto-logs everything, haunts dreams
- **"The One Ring of Fitness"**: Massive bonuses, precious gains, corruption optional
- **"Excali-Burpee"**: The chosen one's exercise, +50% STR, medieval workout music

### Epic Items (4% drop rate)
- **"Schrodinger's Gym Bag"**: Contains clean and dirty clothes simultaneously, quantum preparedness
- **"Legendary Lifting Belt of Dad Strength"**: Enables jar opening, lawn mowing prowess
- **"Yoga Pants of Quantum Flexibility"**: Defy physics, achieve impossible poses

### Item Acquisition Methods
- **Achievement Unlocks**: Specific items tied to milestone achievements
- **Level Rewards**: Every 10 levels guarantees Epic/Legendary item
- **Quest Completion**: Story quest chains reward themed equipment sets
- **Workout Drops**: Random chance during activities (higher intensity = better drops)
- **Special Events**: Holiday/seasonal items with unique bonuses

## Technical Implementation Approaches

### Approach 1: JSON Item Database (Recommended)
**Pros:** Easy to modify, human-readable, version controllable
**Cons:** Requires parsing, potential for inconsistency
**Implementation:** JSON files with item definitions, validation schema

### Approach 2: SQLite Item Database
**Pros:** Relational integrity, complex queries, better performance
**Cons:** Schema migration complexity, less human-readable
**Implementation:** Normalized tables for items, effects, and sets

### Approach 3: Hybrid JSON + Database
**Pros:** Best of both worlds, easy content updates
**Cons:** Synchronization complexity
**Implementation:** JSON for item definitions, SQLite for user inventory

## Output Log
*(This section is populated as work progresses on the task)*