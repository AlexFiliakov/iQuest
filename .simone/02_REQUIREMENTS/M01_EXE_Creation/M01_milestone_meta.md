---
milestone_id: M01
title: Workable EXE Creation
status: active # pending | active | completed | blocked | on_hold
last_updated: 2025-05-27
---

# Milestone: Backend Setup (EXAMPLE)

## Goals
Create an Apple Health Monitor EXE for use with Apple Health Exported data in Pandas CSV format.

## Key Documents
- TODO: Create PRD

## Definition of Done (DoD)
This milestone will be considered complete when:

- The EXE is compiled and operational
- Notes work and persist
- Unit tests work for all components with 95%+ code coverage
- All integration tests pass

## Notes / Context
I'd like to have a Configuration tab where the user can select the following:
- Subset data on date range using field "creationDate".
- Subset data by combination of fields "sourceName and "type" representing the device the metric came from and the type of health metric.

Then I’d like dashboards that have different summaries of the various metrics:
- Daily metric summaries of average, min, max
- Weekly metric summaries of average, min, max
- Monthly metric summaries of average, min, max
- On daily summaries, compare to corresponding weekly and monthly statistics
- On weekly summaries, compare to corresponding monthly statistics
- If the data range is less than a month, display only daily and weekly statistics
- If the data range is less than a week, display only daily statistics

On each tab, I’d like to include a “Journal” feature to write notes on a specific day, week, month to provide some color commentary on the statistics.

Make the charts friendly and engaging, use warm welcome colors like a tan background with oranges and yellows for the main interface UI, with brown text. Make it inviting to use. Make the charts and the UI easy to follow and understand for nontechnical users who may not read charts often.

A small dataset for 2 months is available in `processed data/apple_data_subset.csv`

## Related Sprints

- [S01_M01_Initial_EXE](../../03_SPRINTS/S01_M01_Initial_EXE/S01_sprint_meta.md)

