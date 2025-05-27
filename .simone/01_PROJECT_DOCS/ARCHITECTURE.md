# Demo Project Architecture (EXAMPLE)

This document outlines the high-level architecture of the Apple Health Monitor.

## System Overview

A Windows executable dashboard with Python to analyze Apple Health Data. The data is processed into a Pandas table and stored as a CSV. I'd like to have the EXE take the CSV file and generate a collection of tabs that have different dashboards on them.

## Technical Architecture (Example)

### Backend

- **Interface Layer**: Python compiled .EXE file
- **Data**: CSV Files for apple data, separate directory structure of Markdown files for daily/weekly/monthly user notes.
- **Testing**: `pytest` for unit and integration testing

### Frontend

- **UI Framework**: Appropriate UI for a Windows .EXE file that can display dashboards

## System Components (Example)

2. **Data Summarizer**: Manages data summaries for different views.
3. **Tabbed Graph Presenter**: Core graphics like charts notes displayed.
5. **Notes Processor**: CRUD for Markdown notes by day/week/month of data analyzed.

## Data Flow (Example)

1. Clients creates a local user account in the EXE, the account is purely local with no security. There is no web interface, just a Windows program.
2. Client imports data from a CSV that appends to any previous data and overrides old duplicates.
3. Client navigates their summaries by day/week/month
4. Client makes notes and observations as needed in the UI
5. Data and notes are stored to persist on the hard drive, there is no cloud storage or remote web storage.
6. Client exits the EXE.
7. Client returns to the EXE to update data or to read and append to old notes as needed, the data persists locally.
