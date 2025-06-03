# Installation Troubleshooting Guide - Apple Health Monitor Dashboard

This guide helps resolve installation and runtime issues specific to the Windows executable version of Apple Health Monitor Dashboard.

---

## Table of Contents

1. [Before You Begin](#before-you-begin)
2. [Installation Issues](#installation-issues)
   - [Windows SmartScreen & Security Warnings](#windows-smartscreen--security-warnings)
   - [Antivirus Blocking Installation](#antivirus-blocking-installation)
   - [Installation Failures](#installation-failures)
   - [Missing Dependencies](#missing-dependencies)
3. [Runtime Issues](#runtime-issues)
   - [Application Won't Start](#application-wont-start)
   - [Crashes on Startup](#crashes-on-startup)
   - [Performance Problems](#performance-problems)
   - [Memory Issues](#memory-issues)
4. [Data Import Problems](#data-import-problems)
5. [Feature-Specific Issues](#feature-specific-issues)
6. [Diagnostic Tools](#diagnostic-tools)
7. [Getting Additional Help](#getting-additional-help)

---

## Before You Begin

### System Requirements Check

Run this PowerShell script to verify your system meets requirements:

```powershell
# Save as check-requirements.ps1 and run in PowerShell
Write-Host "Checking System Requirements..." -ForegroundColor Cyan

# Check Windows Version
$os = Get-WmiObject -Class Win32_OperatingSystem
$version = [System.Version]$os.Version
Write-Host "Windows Version: $($os.Caption) - Build $($os.BuildNumber)"

if ($version.Major -eq 10 -and $os.BuildNumber -ge 18362) {
    Write-Host "✓ Windows version OK" -ForegroundColor Green
} elseif ($version.Major -gt 10) {
    Write-Host "✓ Windows version OK" -ForegroundColor Green
} else {
    Write-Host "✗ Windows 10 v1903+ or Windows 11 required" -ForegroundColor Red
}

# Check .NET Framework
$dotnet = Get-ItemProperty "HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" -Name Release -ErrorAction SilentlyContinue
if ($dotnet.Release -ge 461808) {
    Write-Host "✓ .NET Framework 4.7.2+ installed" -ForegroundColor Green
} else {
    Write-Host "✗ .NET Framework 4.7.2+ required" -ForegroundColor Red
}

# Check available disk space
$drive = Get-PSDrive C
$freeGB = [math]::Round($drive.Free / 1GB, 2)
Write-Host "Free disk space: $freeGB GB"
if ($freeGB -gt 0.5) {
    Write-Host "✓ Sufficient disk space" -ForegroundColor Green
} else {
    Write-Host "✗ At least 500MB free space required" -ForegroundColor Red
}

# Check Visual C++ Redistributables
$vcredist = Get-ItemProperty HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | 
    Where-Object { $_.DisplayName -like "*Visual C++ 2015-2022*" }
if ($vcredist) {
    Write-Host "✓ Visual C++ Redistributables installed" -ForegroundColor Green
} else {
    Write-Host "⚠ Visual C++ Redistributables may be needed" -ForegroundColor Yellow
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

### Download Verification

Always verify your download before installation:

1. **Check file size**: Should be approximately 85 MB
2. **Verify digital signature**:
   - Right-click the installer
   - Properties → Digital Signatures tab
   - Verify signature is valid

3. **Calculate hash** (optional):
   ```powershell
   $hash = Get-FileHash "AppleHealthMonitor-Setup-1.0.0.exe" -Algorithm SHA256
   Write-Host "SHA256: $($hash.Hash)"
   # Compare with official hash from website
   ```

---

## Installation Issues

### Windows SmartScreen & Security Warnings

#### "Windows protected your PC" Message

![SmartScreen Warning](images/troubleshoot-smartscreen-detailed.png)

**Why this happens:**
- Windows SmartScreen warns about new or uncommonly downloaded software
- Our application hasn't built enough reputation yet
- This is normal for new releases

**Solution 1: Proceed with Installation**
1. Click **"More info"** link
2. Application name and publisher will appear
3. Click **"Run anyway"** button
4. Installation will proceed normally

**Solution 2: Temporarily Disable SmartScreen**
1. Open Windows Security:
   - Press `Win + I` → Update & Security → Windows Security
2. Click "App & browser control"
3. Under "Check apps and files", select "Warn" or "Off"
4. Run installer
5. **Important**: Re-enable SmartScreen after installation

**Solution 3: Unblock the File**
1. Right-click the installer file
2. Select Properties
3. Check "Unblock" at the bottom
4. Click OK
5. Try running again

### Antivirus Blocking Installation

Different antivirus software requires different approaches:

#### Windows Defender

**Real-time Protection Interference:**
1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Temporarily turn off "Real-time protection"
4. Install the application
5. Turn protection back on
6. Add exclusion:
   - Exclusions → Add or remove exclusions
   - Add folder: `C:\Program Files\Apple Health Monitor`

#### Norton/Symantec

**If Norton blocks or quarantines:**
1. Open Norton
2. Security → History
3. Find "AppleHealthMonitor-Setup.exe" in Quarantine
4. Select the file
5. Click "Restore & Exclude"
6. Choose "Exclude from future scans"

**Disable Auto-Protect temporarily:**
1. Right-click Norton icon in system tray
2. "Disable Auto-Protect"
3. Select duration (15 minutes)
4. Install application
5. Auto-Protect re-enables automatically

#### McAfee

**If McAfee blocks installation:**
1. Open McAfee
2. PC Security → Real-Time Scanning
3. Turn off temporarily
4. Install application
5. Re-enable scanning
6. Add to exceptions:
   - Settings → Excluded Files
   - Add: `C:\Program Files\Apple Health Monitor\`

#### Bitdefender

**Whitelist the application:**
1. Open Bitdefender
2. Protection → Antivirus → Settings
3. Manage Exceptions
4. Add exception → "Application" tab
5. Browse to installer
6. Add and apply

#### Kaspersky

**Add to Trusted Applications:**
1. Open Kaspersky
2. Settings → Additional → Threats and Exclusions
3. Manage exclusions → Add
4. Select the installer file
5. Check "Do not scan opened files"

### Installation Failures

#### "Installation has failed" Error

**Common causes and solutions:**

1. **Corrupted Download**
   ```powershell
   # Check if file is complete
   $file = Get-Item "AppleHealthMonitor-Setup-1.0.0.exe"
   if ($file.Length -lt 80MB) {
       Write-Host "File appears incomplete. Please re-download."
   }
   ```
   - Clear browser cache
   - Use different browser
   - Try download manager

2. **Insufficient Permissions**
   - Right-click installer
   - "Run as administrator"
   - Or use portable version

3. **Conflicting Software**
   - Close all applications
   - Restart in Safe Mode:
     - Hold Shift while clicking Restart
     - Troubleshoot → Advanced → Startup Settings
     - Restart → Press 4 for Safe Mode
     - Try installation

4. **Disk Errors**
   ```cmd
   # Run as administrator
   chkdsk C: /f /r
   # Restart when prompted
   ```

#### Installation Hangs/Freezes

**If progress bar stops moving:**

1. **Check Task Manager**:
   - Press `Ctrl+Shift+Esc`
   - Look for "AppleHealthMonitor-Setup.exe"
   - Check CPU usage (should be >0%)
   - If 0%, end task and retry

2. **Clean Boot**:
   ```cmd
   # Run as administrator
   msconfig
   ```
   - Services tab → Hide Microsoft services → Disable all
   - Startup tab → Open Task Manager → Disable all
   - Restart and try installation
   - Re-enable services after

3. **Windows Installer Issues**:
   ```cmd
   # Reset Windows Installer
   msiexec /unregister
   msiexec /regserver
   
   # Clear installer cache
   cd %TEMP%
   del /q /s *.msi *.msp
   ```

### Missing Dependencies

#### Visual C++ Redistributables

**Symptoms:**
- Error about missing VCRUNTIME140.dll
- Error about missing MSVCP140.dll
- Application exits immediately

**Solution:**
1. Download from Microsoft:
   - [Visual C++ Redistributables](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Install x64 version (required)
3. Install x86 version (optional)
4. Restart computer
5. Try application again

#### .NET Framework Issues

**Symptoms:**
- Error about .NET Framework version
- "This application requires .NET Framework 4.7.2"

**Solution:**
1. Windows Update method:
   - Settings → Update & Security
   - Check for updates
   - Install all updates
   
2. Manual download:
   - [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48)
   - Run installer
   - Restart when prompted

#### Missing Windows Features

**Enable required features:**
```powershell
# Run as administrator
Enable-WindowsOptionalFeature -Online -FeatureName NetFx3 -All
Enable-WindowsOptionalFeature -Online -FeatureName NetFx4-AdvSrvs -All
```

---

## Runtime Issues

### Application Won't Start

#### Nothing Happens When Clicking Icon

**Diagnostic steps:**

1. **Check if already running**:
   ```powershell
   Get-Process | Where-Object {$_.Name -like "*HealthMonitor*"}
   ```
   If found, kill and retry:
   ```powershell
   Stop-Process -Name "AppleHealthMonitor" -Force
   ```

2. **Run from command line** for error messages:
   ```cmd
   cd "C:\Program Files\Apple Health Monitor"
   AppleHealthMonitor.exe --debug
   ```

3. **Check Event Viewer**:
   - Press `Win + X` → Event Viewer
   - Windows Logs → Application
   - Look for red error entries
   - Note error codes and messages

4. **Verify file integrity**:
   ```powershell
   # Check all files present
   $installPath = "C:\Program Files\Apple Health Monitor"
   $requiredFiles = @(
       "AppleHealthMonitor.exe",
       "Qt6Core.dll",
       "Qt6Gui.dll",
       "Qt6Widgets.dll"
   )
   
   foreach ($file in $requiredFiles) {
       if (Test-Path "$installPath\$file") {
           Write-Host "✓ $file found" -ForegroundColor Green
       } else {
           Write-Host "✗ $file MISSING" -ForegroundColor Red
       }
   }
   ```

### Crashes on Startup

#### Immediate Crash

**Common fixes:**

1. **Reset configuration**:
   ```cmd
   # Delete config file
   del "%APPDATA%\AppleHealthMonitor\config.ini"
   ```

2. **Safe mode start**:
   ```cmd
   AppleHealthMonitor.exe --safe-mode
   ```
   This disables:
   - Custom themes
   - Plugins
   - Hardware acceleration

3. **Graphics driver issues**:
   - Update graphics drivers
   - Or disable hardware acceleration:
   ```cmd
   AppleHealthMonitor.exe --no-gpu
   ```

4. **Compatibility mode**:
   - Right-click exe → Properties
   - Compatibility tab
   - Try "Windows 8" mode
   - Check "Disable fullscreen optimizations"

#### Crash with Error Dialog

**If you see an error dialog:**

1. **Note the error** exactly
2. **Screenshot** if possible
3. **Check logs**:
   ```powershell
   notepad "%APPDATA%\AppleHealthMonitor\Logs\crash.log"
   ```

4. **Common error solutions**:
   
   | Error | Solution |
   |-------|----------|
   | "Access violation" | Run as administrator once |
   | "Out of memory" | Close other apps, increase virtual memory |
   | "Database locked" | Delete `%APPDATA%\AppleHealthMonitor\*.db-journal` |
   | "Permission denied" | Check folder permissions |

### Performance Problems

#### Slow Startup

**Optimize startup time:**

1. **Disable startup features**:
   Edit `%APPDATA%\AppleHealthMonitor\config.ini`:
   ```ini
   [Performance]
   CheckUpdatesOnStart=false
   LoadLastFile=false
   PreloadCharts=false
   ```

2. **Clean cache**:
   ```cmd
   rd /s /q "%APPDATA%\AppleHealthMonitor\Cache"
   ```

3. **Defragment database**:
   - Tools → Database Maintenance
   - Click "Optimize Database"

4. **Reduce data scope**:
   - Limit date range on startup
   - Archive old data

#### UI Lag and Freezing

**Improve responsiveness:**

1. **Adjust performance settings**:
   ```ini
   [Performance]
   AnimationSpeed=0
   ChartQuality=Low
   MaxDataPoints=1000
   EnableCaching=true
   ```

2. **GPU acceleration issues**:
   - Settings → Display → Hardware Acceleration → Off
   - Or force software rendering:
   ```cmd
   set QT_QUICK_BACKEND=software
   AppleHealthMonitor.exe
   ```

3. **Windows performance**:
   - Control Panel → System → Advanced
   - Performance Settings → Adjust for performance

### Memory Issues

#### High Memory Usage

**Monitor and manage memory:**

1. **Check current usage**:
   - Help → System Information
   - View memory graph

2. **Reduce memory footprint**:
   ```ini
   [Memory]
   MaxCacheSize=100
   ChartBufferSize=50
   DataPageSize=1000
   EnableMemoryLimit=true
   MemoryLimitMB=500
   ```

3. **Clear unnecessary data**:
   - Close unused tabs
   - Tools → Clear Working Set
   - Restart application periodically

#### Out of Memory Errors

**For large datasets:**

1. **Increase virtual memory**:
   ```
   System Properties → Advanced → Performance Settings
   → Advanced → Virtual Memory → Change
   Set to System managed or 2x RAM
   ```

2. **Use 64-bit version** (if available)

3. **Process in batches**:
   - Import data in chunks
   - Use date filters aggressively

---

## Data Import Problems

### "Invalid XML" Errors

**When importing fails:**

1. **Verify file format**:
   ```powershell
   # Check if valid XML
   [xml]$xml = Get-Content "export.xml" -First 10
   $xml.ChildNodes[0].Name  # Should show health data root
   ```

2. **Check file encoding**:
   - Must be UTF-8
   - Convert if needed:
   ```powershell
   $content = Get-Content "export.xml" -Encoding UTF8
   $content | Set-Content "export_fixed.xml" -Encoding UTF8
   ```

3. **Repair corrupted XML**:
   - Use online XML validators
   - Remove invalid characters
   - Fix unclosed tags

### Import Performance

**For slow imports:**

1. **Pre-process large files**:
   ```cmd
   # Extract from zip first
   # Import XML directly, not ZIP
   ```

2. **Optimize system**:
   - Close other applications
   - Disable antivirus scanning temporarily
   - Use SSD if available

3. **Monitor progress**:
   - View → Import Log
   - Check for errors or warnings

### Missing Data After Import

**Troubleshooting steps:**

1. **Verify import completed**:
   - Check import log
   - Look for "Import completed" message

2. **Check filters**:
   - Configuration → Reset All Filters
   - Set date range to "All Time"

3. **Database integrity**:
   ```sql
   -- In Tools → Database Console
   PRAGMA integrity_check;
   SELECT COUNT(*) FROM health_records;
   ```

---

## Feature-Specific Issues

### Charts Not Displaying

**Blank chart areas:**

1. **Graphics compatibility**:
   ```cmd
   # Force OpenGL mode
   set QT_OPENGL=software
   AppleHealthMonitor.exe
   ```

2. **Reset chart settings**:
   - View → Reset All Views
   - Delete `%APPDATA%\AppleHealthMonitor\charts.ini`

3. **Reinstall Visual C++ Redistributables**

### Journal Save Failures

**If journal entries won't save:**

1. **Check permissions**:
   ```powershell
   icacls "%APPDATA%\AppleHealthMonitor" /grant %USERNAME%:F
   ```

2. **Database locks**:
   - Close and reopen application
   - Delete `.db-journal` files

3. **Repair database**:
   - Tools → Database Maintenance → Repair

### Export Not Working

**Export failures:**

1. **Check disk space** for export location
2. **Try different format** (CSV instead of PDF)
3. **Run as administrator** for system folders
4. **Use portable path** (no special characters)

---

## Diagnostic Tools

### Generate Diagnostic Report

Create comprehensive diagnostic information:

```powershell
# Save as diagnostic.ps1
$report = @"
Apple Health Monitor Diagnostic Report
Generated: $(Get-Date)

SYSTEM INFORMATION
==================
$([System.Environment]::OSVersion)
RAM: $([Math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory/1GB,2)) GB
CPU: $((Get-WmiObject Win32_Processor).Name)

APPLICATION INFO
================
"@

# Check installation
$installPath = "C:\Program Files\Apple Health Monitor"
if (Test-Path $installPath) {
    $exe = Get-Item "$installPath\AppleHealthMonitor.exe"
    $report += "`nInstalled Version: $($exe.VersionInfo.FileVersion)"
    $report += "`nInstall Date: $($exe.CreationTime)"
}

# Check data directory
$dataPath = "$env:APPDATA\AppleHealthMonitor"
if (Test-Path $dataPath) {
    $size = (Get-ChildItem $dataPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    $report += "`nData Directory Size: $([Math]::Round($size,2)) MB"
}

# Check for errors
$logPath = "$dataPath\Logs"
if (Test-Path $logPath) {
    $errors = Get-Content "$logPath\*.log" | Select-String "ERROR" | Select -Last 10
    $report += "`n`nRECENT ERRORS`n============="
    $report += "`n$errors"
}

# Save report
$report | Out-File "HealthMonitor_Diagnostic.txt"
Write-Host "Diagnostic report saved to: HealthMonitor_Diagnostic.txt" -ForegroundColor Green
```

### Enable Debug Logging

For detailed troubleshooting:

1. **Enable debug mode**:
   ```ini
   # Add to config.ini
   [Debug]
   EnableLogging=true
   LogLevel=DEBUG
   LogToFile=true
   MaxLogSize=50
   ```

2. **Run with debug flag**:
   ```cmd
   AppleHealthMonitor.exe --debug --log-level=TRACE
   ```

3. **View logs**:
   - Help → View Logs
   - Or navigate to `%APPDATA%\AppleHealthMonitor\Logs`

### System Information Collection

Built-in diagnostic tool:

1. Help → Generate System Report
2. Includes:
   - System specifications
   - Application version
   - Loaded modules
   - Configuration
   - Recent errors
3. Save report for support

---

## Getting Additional Help

### Before Contacting Support

**Try these steps:**

- [ ] Restart the application
- [ ] Restart your computer
- [ ] Update Windows
- [ ] Check disk space (>1GB free)
- [ ] Temporarily disable antivirus
- [ ] Run as administrator
- [ ] Clear application cache
- [ ] Try portable version
- [ ] Check for updates

### Information to Gather

When seeking help, provide:

1. **System Information**:
   - Windows version (Settings → System → About)
   - Application version (Help → About)
   - Installation type (installer/portable/MSI)

2. **Problem Details**:
   - Exact error messages
   - When problem occurs
   - Steps to reproduce
   - What you've tried

3. **Diagnostic Files**:
   - Screenshot of error
   - Diagnostic report
   - Recent log files
   - Crash dumps (if any)

### Contact Support

**Email Support**:
```
To: support@example.com
Subject: [Installation Issue] Brief description

Include:
- Diagnostic report (attached)
- Screenshots (attached)
- Clear problem description
- Steps already tried
```

**Community Forum**:
- Search existing issues first
- Post in appropriate category
- Include diagnostic information
- Follow up with solutions

### Emergency Recovery

**If all else fails:**

1. **Complete Removal**:
   ```powershell
   # Uninstall application
   # Then remove all traces:
   Remove-Item -Recurse -Force "$env:APPDATA\AppleHealthMonitor"
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\AppleHealthMonitor"
   Remove-Item -Recurse -Force "HKCU:\Software\AppleHealthMonitor"
   ```

2. **Fresh Installation**:
   - Download latest version
   - Run as administrator
   - Choose different install location

3. **Alternative Options**:
   - Try portable version
   - Use older stable version
   - Run in Windows Sandbox
   - Use virtual machine

---

## Quick Fix Reference

### Common Fixes by Symptom

| Symptom | Quick Fix |
|---------|-----------|
| Won't install | Run as admin, disable antivirus |
| Won't start | Delete config.ini, run safe mode |
| Crashes | Update graphics drivers, disable GPU |
| Slow | Clear cache, reduce data range |
| Import fails | Check file size, use XML not ZIP |
| Missing data | Reset filters, check date range |
| Can't save | Check permissions, repair database |

### Command Line Switches

```cmd
AppleHealthMonitor.exe [options]

--safe-mode          # Disable all customizations
--reset              # Reset to factory settings
--debug              # Enable debug output
--no-gpu             # Disable hardware acceleration
--portable           # Run in portable mode
--import <file>      # Auto-import file on start
--log-level <level>  # Set logging verbosity
--help               # Show all options
```

### Registry Cleanup

If needed, remove these keys:
```
HKEY_CURRENT_USER\Software\AppleHealthMonitor
HKEY_LOCAL_MACHINE\SOFTWARE\AppleHealthMonitor
HKEY_CLASSES_ROOT\.healthexport
```

---

**Remember**: Most installation issues have simple solutions. This guide covers 95% of problems users encounter. For issues not covered here, our support team is ready to help!

*Version 1.0 | Last Updated: June 2025*