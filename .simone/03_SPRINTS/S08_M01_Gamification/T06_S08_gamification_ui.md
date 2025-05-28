---
task_id: T06_S08
sprint_sequence_id: S08
status: open
complexity: Medium
last_updated: 2025-05-28T12:00:00Z
---

# Task: Build Gamification Tab with Sub-Navigation

## Description
Create a new main tab for gamification features with sub-tabs for Character Sheet, Inventory, Skills, Achievements, and World/Quests. The UI should maintain the warm color theme while adding fantasy RPG elements.

## Goal / Objectives
- Add Gamification as a main navigation tab
- Implement sub-tab navigation within gamification
- Create layouts for each game section
- Maintain consistent styling with existing UI

## Acceptance Criteria
- [ ] Gamification tab added to main navigation, tab name is "iQuest"
- [ ] Sub-tabs: Character, Inventory, Skills, Achievements, World
- [ ] Character sheet displays all stats and equipment
- [ ] Inventory grid shows items with filtering
- [ ] Skills tab shows interactive skill trees
- [ ] Achievements page lists unlocked/locked achievements
- [ ] World tab shows quests and progress
- [ ] Smooth transitions between sub-tabs
- [ ] Responsive layout adapts to window size

## Important References
- Main Window: `src/ui/main_window.py`
- Tab Navigation: `src/ui/configuration_tab.py`
- Style Manager: `src/ui/style_manager.py`
- UI Specs: `.simone/02_REQUIREMENTS/M01/SPECS_UI.md`

## Subtasks
- [ ] Extend main window tab widget for gamification, tab name "iQuest"
- [ ] Create GamificationTab main container
- [ ] Implement sub-tab navigation widget
- [ ] Design CharacterSheetWidget layout, with character images corresponding to the current class sourced from PNGs in `assets/characters/`
  - [ ] Cleric is `cleric.png`
  - [ ] Ranger is `ranger.png`
  - [ ] Rogue is `rogue.png`
  - [ ] Warrior is `warrior.png`
  - [ ] Wizard is `wizard.png`
- [ ] Build InventoryWidget with grid system
- [ ] Create SkillTreeWidget container
- [ ] Design AchievementsWidget with progress
- [ ] Build WorldQuestsWidget interface
- [ ] Add fantasy-themed visual elements
- [ ] Ensure keyboard navigation works

## Output Log
*(This section is populated as work progresses on the task)*