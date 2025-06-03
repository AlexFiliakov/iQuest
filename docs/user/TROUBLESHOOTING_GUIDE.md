# Troubleshooting Guide - Apple Health Monitor Dashboard

This guide helps you resolve common issues with the Apple Health Monitor Dashboard.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Import Problems](#import-problems)
3. [Performance Issues](#performance-issues)
4. [Display Problems](#display-problems)
5. [Data Issues](#data-issues)
6. [Journal Problems](#journal-problems)
7. [Export Issues](#export-issues)
8. [General Application Issues](#general-application-issues)
9. [Getting Additional Help](#getting-additional-help)

---

## Installation Issues

### Windows SmartScreen Warning

**Problem**: "Windows protected your PC" message appears

![SmartScreen Warning](images/troubleshoot-smartscreen.png)

**Solution**:
1. Click **"More info"**
2. Click **"Run anyway"**
3. This is normal for new software that hasn't built reputation yet

**Alternative**:
- Use the portable version (no installation required)
- Add an exception in Windows Security

### Installation Fails

**Problem**: Installer crashes or shows error

**Common Causes & Solutions**:

1. **Insufficient Permissions**
   - Right-click installer
   - Select "Run as administrator"
   - Try again

2. **Antivirus Blocking**
   - Temporarily disable antivirus
   - Run installation
   - Re-enable antivirus
   - Add app to exceptions

3. **Corrupted Download**
   - Clear browser cache
   - Re-download installer
   - Verify file size matches website

4. **System Requirements**
   - Ensure Windows 10 v1903+ or Windows 11
   - Check for 500MB free space
   - Update Windows if needed

### Application Won't Start

**Problem**: Nothing happens when clicking the app

**Solutions**:

1. **Check Task Manager**
   - Press Ctrl+Shift+Esc
   - Look for AppleHealthMonitor.exe
   - End task if found, try again

2. **Compatibility Mode**
   - Right-click app shortcut
   - Properties → Compatibility
   - Try Windows 8 compatibility mode

3. **Missing Dependencies**
   - Install Visual C++ Redistributables
   - Update .NET Framework
   - Restart computer

4. **Reset Application**
   ```
   1. Navigate to %AppData%\AppleHealthMonitor
   2. Rename folder to "AppleHealthMonitor_backup"
   3. Start application fresh
   ```

---

## Import Problems

### Import Takes Too Long

**Problem**: Import seems stuck or very slow

**Expected Import Times**:
| File Size | Expected Time |
|-----------|---------------|
| <50MB | 1-2 minutes |
| 50-200MB | 2-5 minutes |
| 200-500MB | 5-15 minutes |
| 500MB-1GB | 15-30 minutes |
| >1GB | 30-60 minutes |

**Solutions**:

1. **Check Progress Bar**
   - Look for movement in progress %
   - Check status messages
   - Small movements = still working

2. **Optimize Import**
   - Close other applications
   - Ensure power adapter connected
   - Disable sleep mode
   - Use SSD if available

3. **Import in Chunks**
   - Use date range filters
   - Import year by year
   - Start with recent data

### Import Fails or Crashes

**Problem**: Import stops with error or app crashes

**Diagnostic Steps**:

1. **Check File Integrity**
   ```
   - Original export.zip size correct?
   - Can you extract the ZIP?
   - Is export.xml present?
   - File not corrupted?
   ```

2. **Memory Issues**
   - Check available RAM (Task Manager)
   - Close memory-heavy apps
   - Increase virtual memory:
     ```
     System → Advanced → Performance Settings → 
     Advanced → Virtual Memory → Change
     ```

3. **File Format Issues**
   - Ensure it's an Apple Health export
   - Check XML isn't corrupted
   - Try opening in text editor

4. **Alternative Import Method**
   - Extract ZIP first
   - Import export.xml directly
   - Use "Import Selected Types" option

### Missing Data After Import

**Problem**: Import successful but data missing

**Checklist**:

1. **Date Range Filters**
   - Check Configuration tab
   - Ensure date range includes your data
   - Try "All Time" option

2. **Metric Selection**
   - Configuration → Metrics
   - Enable desired metrics
   - Click "Apply Filters"

3. **Source Filters**
   - Check if sources are filtered
   - Enable iPhone, Apple Watch, etc.
   - Include all relevant apps

4. **Import Log**
   - View → Import Log
   - Check for skipped records
   - Look for error messages

---

## Performance Issues

### Application Runs Slowly

**Problem**: Sluggish response, delays in navigation

**Quick Fixes**:

1. **Reduce Data Range**
   - Use shorter date ranges
   - Filter to essential metrics
   - Archive old data

2. **Optimize Settings**
   ![Performance Settings](images/troubleshoot-performance.png)
   - Settings → Performance
   - Reduce chart quality
   - Disable animations
   - Lower cache size

3. **System Optimization**
   - Close background apps
   - Check CPU/RAM usage
   - Disable Windows animations
   - Update graphics drivers

### Charts Load Slowly

**Problem**: Visualizations take time to appear

**Solutions**:

1. **Chart Settings**
   - Reduce data points
   - Simplify chart types
   - Disable smooth scrolling

2. **Data Optimization**
   - Use aggregated views
   - Enable smart sampling
   - Pre-calculate summaries

3. **Hardware Acceleration**
   - Settings → Display
   - Enable GPU acceleration
   - Update graphics drivers

### Memory Usage High

**Problem**: Application uses excessive RAM

**Memory Management**:

1. **Check Current Usage**
   - View → Performance Stats
   - Monitor memory graph
   - Identify memory spikes

2. **Reduce Memory Load**
   - Close unused tabs
   - Clear cache regularly
   - Limit concurrent charts

3. **Configure Limits**
   - Settings → Advanced
   - Set memory limit
   - Enable auto-cleanup

---

## Display Problems

### Charts Not Showing

**Problem**: Blank areas where charts should be

![Missing Charts](images/troubleshoot-no-charts.png)

**Troubleshooting**:

1. **Data Availability**
   - Confirm data exists for period
   - Check metric selection
   - Verify import success

2. **Display Settings**
   - Reset zoom level (Ctrl+0)
   - Check display scaling
   - Try different chart type

3. **Render Issues**
   - Update graphics drivers
   - Disable hardware acceleration
   - Clear application cache

### UI Elements Missing or Misaligned

**Problem**: Buttons, menus, or panels not displaying correctly

**Fixes**:

1. **Reset Layout**
   - View → Reset Layout
   - Restart application
   - Check improvements

2. **Display Scaling**
   - Windows Settings → Display
   - Set scaling to 100%
   - Or adjust app compatibility

3. **Resolution Issues**
   - Ensure 1280x720 minimum
   - Check multiple monitors
   - Try primary display only

### Text Too Small/Large

**Problem**: Difficulty reading interface text

**Adjustments**:

1. **Application Font Size**
   - Settings → Appearance
   - Adjust font size slider
   - Preview changes

2. **Windows Scaling**
   - Right-click desktop
   - Display settings
   - Adjust scale %

3. **Accessibility Options**
   - Settings → Accessibility
   - High contrast mode
   - Large cursor option

---

## Data Issues

### Incorrect Calculations

**Problem**: Numbers don't match Apple Health

**Verification Steps**:

1. **Check Aggregation Method**
   - Daily totals vs averages
   - Time zone considerations
   - Duplicate handling

2. **Source Filtering**
   - Include all sources
   - Check priority settings
   - Verify no exclusions

3. **Calculation Settings**
   - Settings → Calculations
   - Review methods
   - Compare with Apple Health

### Duplicate Data

**Problem**: Same activities counted multiple times

**Solutions**:

1. **Deduplication Settings**
   - Configuration → Advanced
   - Enable deduplication
   - Set priority rules

2. **Source Priority**
   - Prefer Apple Watch > iPhone
   - Set app priorities
   - Manual entry handling

3. **Clean Database**
   - Tools → Database Maintenance
   - Remove duplicates
   - Rebuild indexes

### Missing Recent Data

**Problem**: Latest activities not showing

**Quick Checks**:

1. **Refresh Data**
   - Press F5
   - Or click refresh button
   - Wait for update

2. **Re-import Recent**
   - Export fresh from iPhone
   - Import last 30 days
   - Merge with existing

3. **Auto-sync Issues**
   - Not available (privacy)
   - Must manual export/import
   - Set reminder for updates

---

## Journal Problems

### Can't Save Journal Entries

**Problem**: Journal entries won't save or disappear

**Solutions**:

1. **Check Auto-save**
   - Should save automatically
   - Look for save indicator
   - Try manual save (Ctrl+S)

2. **Database Issues**
   - Tools → Database Check
   - Repair if errors found
   - Backup before repair

3. **Permission Problems**
   - Check write permissions
   - Ensure space available
   - Try different location

### Journal Search Not Working

**Problem**: Search returns no results or wrong results

**Fixes**:

1. **Rebuild Search Index**
   - Tools → Rebuild Indexes
   - Wait for completion
   - Try search again

2. **Search Syntax**
   - Use quotes for phrases
   - Check spelling
   - Try simpler terms

3. **Filter Settings**
   - Check date range
   - Remove type filters
   - Search all fields

---

## Export Issues

### Export Fails

**Problem**: Can't export reports or data

**Common Solutions**:

1. **File Permissions**
   - Choose different folder
   - Check write access
   - Avoid system folders

2. **Format Issues**
   - Try different format
   - Reduce data size
   - Export in batches

3. **PDF Problems**
   - Update PDF viewer
   - Check printer drivers
   - Try HTML export

### Exported Files Are Empty

**Problem**: Export completes but files have no data

**Debugging**:

1. **Check Selection**
   - Verify data selected
   - Confirm date range
   - Include all metrics

2. **Export Settings**
   - Review options
   - Include all sections
   - Check filters

3. **Alternative Export**
   - Try CSV format
   - Export raw data
   - Copy from tables

---

## General Application Issues

### Settings Won't Save

**Problem**: Preferences reset after restart

**Solutions**:

1. **Config File Location**
   ```
   %AppData%\AppleHealthMonitor\config.ini
   ```
   - Check file exists
   - Verify write permissions
   - Delete to reset

2. **Registry Issues** (Installer version)
   - Run as administrator once
   - Check antivirus blocks
   - Reset preferences

3. **Portable Version**
   - Check folder permissions
   - Ensure not read-only
   - Keep in user folder

### Random Crashes

**Problem**: Application closes unexpectedly

**Diagnostic Process**:

1. **Check Error Logs**
   - Help → View Logs
   - Look for error patterns
   - Note crash timing

2. **Event Viewer**
   - Windows Event Viewer
   - Application logs
   - Find crash details

3. **Safe Mode Start**
   - Hold Shift while starting
   - Disables plugins
   - Reset if stable

### Update Problems

**Problem**: Can't update to latest version

**Update Methods**:

1. **Auto-update Failed**
   - Download manually
   - Install over existing
   - Keep settings

2. **Clean Install**
   - Backup data first
   - Uninstall old version
   - Fresh installation

3. **Portable Update**
   - Download new version
   - Copy config files
   - Replace executable

---

## Getting Additional Help

### Generate Diagnostic Report

1. **Help → Generate Diagnostic Report**
2. **Include**:
   - System information
   - Error logs
   - Configuration
   - Recent actions

3. **Privacy Note**:
   - No health data included
   - Only technical info
   - Review before sending

### Contact Support

**Email Support**:
- Email: support@example.com
- Include diagnostic report
- Describe steps to reproduce
- Attach screenshots

**Community Forum**:
- Visit: forum.example.com
- Search existing topics
- Post detailed question
- Help others too!

### Useful Information to Provide

When asking for help, include:

1. **System Details**:
   - Windows version
   - Application version
   - Installation type

2. **Problem Description**:
   - When it started
   - What you were doing
   - Error messages
   - Screenshots

3. **What You've Tried**:
   - Steps taken
   - Results
   - Workarounds

### Emergency Recovery

If all else fails:

1. **Backup Your Data**:
   ```
   %AppData%\AppleHealthMonitor\
   ```

2. **Clean Reinstall**:
   - Uninstall application
   - Delete AppData folder
   - Fresh installation
   - Restore backups

3. **Alternative Access**:
   - Use portable version
   - Try older version
   - Export data as CSV

---

## Quick Fix Checklist

Before contacting support, try:

- [ ] Restart the application
- [ ] Restart your computer
- [ ] Update Windows
- [ ] Check disk space
- [ ] Disable antivirus temporarily
- [ ] Run as administrator
- [ ] Clear application cache
- [ ] Reset to default settings
- [ ] Try portable version
- [ ] Check for updates

---

## Known Issues

### Current Version (1.0.0)

1. **Large File Performance**
   - Files >1GB may be slow
   - Working on optimization

2. **Rare Metrics**
   - Some health types not supported
   - Adding in updates

3. **Multiple Languages**
   - Currently English only
   - Translations coming

### Planned Fixes

- Improved import speed
- Better memory management
- More metric types
- Enhanced stability

---

**Remember**: Most issues have simple solutions. Don't hesitate to ask for help!

*Last Updated: June 2025 | Version 1.0*