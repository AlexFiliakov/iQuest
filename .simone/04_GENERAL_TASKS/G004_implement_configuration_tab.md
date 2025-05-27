---
task_id: G004
status: open
complexity: Medium
last_updated: 2025-01-27T12:00:00Z
---

# Task: Implement Configuration Tab

## Description
Create the Configuration tab interface where users can filter and subset their Apple Health data by date range and by device/metric type combinations. This tab serves as the control center for data filtering before analysis.

## Goal / Objectives
Build an intuitive configuration interface that allows users to easily filter their health data for focused analysis.
- Date range selector using creationDate field
- Multi-select for sourceName (devices)
- Multi-select for type (health metrics)
- Apply filters button with feedback

## Acceptance Criteria
- [ ] Date range picker with calendar widgets
- [ ] Dropdowns populated with unique sourceNames from data
- [ ] Dropdowns populated with unique types from data
- [ ] Multi-selection capability for both dropdowns
- [ ] Clear visual feedback when filters are applied
- [ ] Reset filters button functional
- [ ] Filtered data passed to other tabs

## Subtasks
- [ ] Create configuration_tab.py module
- [ ] Implement date range selector widgets
- [ ] Create device (sourceName) multi-select dropdown
- [ ] Create metric type multi-select dropdown
- [ ] Implement filter application logic
- [ ] Add visual feedback for active filters
- [ ] Connect to data loader for dropdown population
- [ ] Add reset functionality

## Output Log
*(This section is populated as work progresses on the task)*