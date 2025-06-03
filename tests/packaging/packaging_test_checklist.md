# Packaging Test Checklist

## Test Environment Setup

### Windows 10 (Clean VM)
- [ ] Version: 21H2 or later
- [ ] RAM: 4GB minimum  
- [ ] No development tools installed
- [ ] Windows Defender enabled
- [ ] .NET Framework 4.8 installed
- [ ] Visual C++ Redistributables installed

### Windows 11 (Clean VM)
- [ ] Version: 22H2 or later
- [ ] RAM: 4GB minimum
- [ ] No development tools installed
- [ ] Default security settings
- [ ] .NET Framework 4.8 installed
- [ ] Visual C++ Redistributables installed

## Installation Tests

### Direct EXE (`AppleHealthDashboard.exe`)
- [ ] **First Run**
  - [ ] Runs without installation
  - [ ] Creates AppData directory on first run
  - [ ] No admin rights required
  - [ ] No security warnings (if signed)
  - [ ] Application icon displays correctly
  
- [ ] **File Associations**
  - [ ] No file associations created
  - [ ] Can open from any location
  - [ ] Path with spaces handled correctly

### NSIS Installer (`AppleHealthDashboard-1.0.0-Setup.exe`)
- [ ] **Installation Process**
  - [ ] Installer launches correctly
  - [ ] License agreement displays
  - [ ] Custom install path works
  - [ ] Default path: `C:\Program Files\Apple Health Dashboard`
  - [ ] Installation progress shows correctly
  
- [ ] **Post-Installation**
  - [ ] Desktop shortcut created
  - [ ] Start menu entry created
  - [ ] Uninstaller registered in Control Panel
  - [ ] Application launches from shortcuts
  - [ ] No admin rights required for running
  
- [ ] **Upgrade Installation**
  - [ ] Detects existing installation
  - [ ] Preserves user data during upgrade
  - [ ] Updates all files correctly
  - [ ] Version number updates in About dialog

### Portable ZIP (`AppleHealthDashboard-1.0.0-Portable.zip`)
- [ ] **Extraction**
  - [ ] Extracts without errors
  - [ ] All files present
  - [ ] Directory structure preserved
  
- [ ] **Portability**
  - [ ] Runs from any directory
  - [ ] Data stored in app directory (`./data/`)
  - [ ] No registry entries created
  - [ ] No files in AppData
  - [ ] Can run from USB drive

## Feature Tests

### Data Import
- [ ] **XML Import**
  - [ ] File dialog opens correctly
  - [ ] Progress dialog displays
  - [ ] Import completes without errors
  - [ ] Large file handling (>100MB)
  - [ ] Cancel import works
  - [ ] Error messages display correctly
  
- [ ] **CSV Import**
  - [ ] File dialog opens correctly  
  - [ ] Import completes
  - [ ] Data validation works
  - [ ] Duplicate handling works

### Dashboards
- [ ] **Daily Dashboard**
  - [ ] Loads without errors
  - [ ] All metric cards display
  - [ ] Date navigation works
  - [ ] Aggregation selector works (Sum/Average/etc)
  - [ ] Activity timeline loads
  - [ ] Source filtering works
  
- [ ] **Weekly Dashboard**
  - [ ] Loads without errors
  - [ ] Week navigation works
  - [ ] Charts render correctly
  - [ ] Statistics display
  - [ ] Week-over-week comparison works
  
- [ ] **Monthly Dashboard**
  - [ ] Loads without errors
  - [ ] Calendar heatmap displays
  - [ ] Month navigation works
  - [ ] Year-over-year comparison works
  - [ ] Monthly context panel works

### Charts
- [ ] **Line Charts**
  - [ ] Render without errors
  - [ ] Tooltips work on hover
  - [ ] Zoom functionality works
  - [ ] Pan functionality works
  - [ ] Reset zoom works
  
- [ ] **Bar Charts**
  - [ ] Render correctly
  - [ ] Labels display properly
  - [ ] Colors consistent with theme
  
- [ ] **Heatmaps**
  - [ ] Calendar heatmap renders
  - [ ] Color gradients work
  - [ ] Day selection works
  - [ ] Tooltips show values
  
- [ ] **Export Functions**
  - [ ] Export to PNG works
  - [ ] Export to SVG works
  - [ ] Save dialog appears
  - [ ] Files save correctly

### Journal Feature
- [ ] **Create Entry**
  - [ ] Editor opens correctly
  - [ ] Text formatting works
  - [ ] Save button enabled on changes
  - [ ] Auto-save indicator works
  
- [ ] **Save/Edit**
  - [ ] Manual save works
  - [ ] Auto-save triggers (30s)
  - [ ] Edit existing entries
  - [ ] Conflict resolution works
  
- [ ] **Search**
  - [ ] Search bar accepts input
  - [ ] Results display correctly
  - [ ] Highlighting works
  - [ ] Clear search works
  
- [ ] **Export**
  - [ ] Export to PDF works
  - [ ] Export to JSON works
  - [ ] Date range selection works
  - [ ] File saves correctly
  
- [ ] **Persistence**
  - [ ] Entries persist after restart
  - [ ] Database file created correctly
  - [ ] No data loss on crash

### Settings
- [ ] **Preferences**
  - [ ] Settings dialog opens
  - [ ] Changes save correctly
  - [ ] Apply without restart
  - [ ] Reset to defaults works
  
- [ ] **Theme**
  - [ ] Theme selector works
  - [ ] Changes apply immediately
  - [ ] Persists after restart
  
- [ ] **Data Filters**
  - [ ] Source filters save
  - [ ] Date range saves
  - [ ] Metric selection saves

## Performance Tests

### Startup Performance
- [ ] **Cold Start** (first run after reboot)
  - Time: _____ seconds (target: <5s)
  - [ ] Splash screen appears quickly
  - [ ] Main window responsive
  
- [ ] **Warm Start** (subsequent runs)
  - Time: _____ seconds (target: <3s)
  - [ ] Faster than cold start

### Runtime Performance
- [ ] **Memory Usage**
  - [ ] Initial: _____ MB
  - [ ] After data load: _____ MB
  - [ ] After 10 min use: _____ MB
  - [ ] No memory leaks observed
  
- [ ] **CPU Usage**
  - [ ] Idle: _____% (target: <5%)
  - [ ] During import: _____%
  - [ ] During navigation: _____%

### Data Operations
- [ ] **Import Performance**
  - [ ] 10MB file: _____ seconds
  - [ ] 100MB file: _____ seconds
  - [ ] 500MB file: _____ seconds
  
- [ ] **Chart Rendering**
  - [ ] Line chart: _____ ms
  - [ ] Bar chart: _____ ms
  - [ ] Heatmap: _____ ms

## Security Tests

### Code Signing
- [ ] **Digital Signature**
  - [ ] EXE is signed
  - [ ] Installer is signed
  - [ ] No security warnings
  - [ ] Certificate valid
  
- [ ] **Antivirus**
  - [ ] Windows Defender: Pass/Fail
  - [ ] Submit to VirusTotal
  - [ ] Document any false positives

## Update Tests

### Clean Update (Installer)
1. [ ] Install version 1.0.0
2. [ ] Create journal entries
3. [ ] Install version 1.1.0 over existing
4. [ ] Verify journal entries preserved
5. [ ] Verify new features available
6. [ ] Old version properly replaced

### Portable Update
1. [ ] Run portable version 1.0.0
2. [ ] Create data and journal entries
3. [ ] Extract new portable version 1.1.0
4. [ ] Copy data folder
5. [ ] Verify data continuity
6. [ ] Old version can be deleted

### Direct EXE Update
1. [ ] Run version 1.0.0
2. [ ] Create app data
3. [ ] Replace with version 1.1.0
4. [ ] Verify data preserved
5. [ ] Settings maintained

## Uninstallation Tests

### NSIS Uninstaller
- [ ] **Uninstall Process**
  - [ ] Uninstaller launches
  - [ ] Confirmation dialog appears
  - [ ] Progress shows correctly
  - [ ] Application closed if running
  
- [ ] **Cleanup**
  - [ ] Program files removed
  - [ ] Start menu entries removed
  - [ ] Desktop shortcut removed
  - [ ] Registry entries cleaned
  - [ ] Option to keep user data

### Manual Cleanup
- [ ] **Portable Version**
  - [ ] Can delete folder completely
  - [ ] No leftover files
  - [ ] No registry entries
  
- [ ] **Direct EXE**
  - [ ] Can delete EXE
  - [ ] AppData remains (document)

## Accessibility Tests

- [ ] **Keyboard Navigation**
  - [ ] Tab order logical
  - [ ] All controls reachable
  - [ ] Shortcuts work (Ctrl+S, etc)
  
- [ ] **Screen Reader**
  - [ ] Controls have labels
  - [ ] Status announced
  - [ ] Errors announced

## Error Handling

- [ ] **Missing Dependencies**
  - [ ] Clear error message
  - [ ] Suggests solution
  - [ ] Graceful exit
  
- [ ] **Data Errors**
  - [ ] Corrupt XML handled
  - [ ] Invalid data handled
  - [ ] Error log created
  
- [ ] **Permission Errors**
  - [ ] Read-only directory handled
  - [ ] No write access handled
  - [ ] Network drive handled

## Documentation Tests

- [ ] **Help Menu**
  - [ ] Opens documentation
  - [ ] Links work correctly
  - [ ] Version info correct
  
- [ ] **Tooltips**
  - [ ] All buttons have tooltips
  - [ ] Tooltips helpful
  - [ ] No truncated text

## Known Issues Documentation

### Issue Template
```
Issue ID: PKG-XXX
Severity: High/Medium/Low
Format: EXE/Installer/Portable
OS: Windows 10/11
Version: 1.0.0

Description:
[Issue description]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]

Expected: [What should happen]
Actual: [What happens]

Workaround: [If available]
```

## Sign-off

### Windows 10 Testing
- [ ] Tester Name: _____________
- [ ] Date: _____________
- [ ] All critical tests passed
- [ ] Performance acceptable
- [ ] No blocking issues

### Windows 11 Testing  
- [ ] Tester Name: _____________
- [ ] Date: _____________
- [ ] All critical tests passed
- [ ] Performance acceptable
- [ ] No blocking issues

### Release Decision
- [ ] Ready for release
- [ ] Conditional release (document conditions)
- [ ] Not ready (list blockers)

**Release Manager Sign-off**: _____________
**Date**: _____________