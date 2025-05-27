---
sprint_folder_name: S01_M01_Initial_EXE
sprint_sequence_id: S01
milestone_id: M01
title: Initial API Development
status: active # pending | active | completed | aborted
goal: Implement the foundational API structure including user authentication, basic project endpoints, and the initial database models.
last_updated: 2023-07-15
---

# Sprint: Initial API Development (S01) (EXAMPLE)

## Sprint Goal
Create an Apple Health Monitor EXE for use with Apple Health Exported data in Pandas CSV format.

## Scope & Key Deliverables
1. The EXE is compiled and operational
2. Graphs and tabs display as intended
3. Notes work and persist
4. Working `pytest` unit tests for all components with 95%+ code coverage
5. Working thorough and intelligent integration tests


## Sprint Backlog


## Definition of Done (for the Sprint)
This sprint will be considered complete when:

- The EXE is compiled and operational
- Notes work and persist
- Unit tests work for all components with 95%+ code coverage
- All integration tests pass

## Notes / Context
how would you approach creating a Windows executable dashboard with Python to analyze Apple Health Data? The data is processed into a Pandas table and stored as a CSV. I'd like to have the EXE take the CSV file and generate a collection of tabs that have different dashboards on them.

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
