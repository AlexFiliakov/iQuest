# Installation Guide - Apple Health Monitor Dashboard

This guide covers all installation methods for the Apple Health Monitor Dashboard on Windows systems.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Installation Methods](#installation-methods)
   - [Method 1: Windows Installer (Recommended)](#method-1-windows-installer-recommended)
   - [Method 2: Portable Version](#method-2-portable-version)
   - [Method 3: MSI Package (Enterprise)](#method-3-msi-package-enterprise)
4. [Post-Installation Setup](#post-installation-setup)
5. [Uninstallation](#uninstallation)
6. [Troubleshooting Installation](#troubleshooting-installation)
7. [Advanced Options](#advanced-options)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10 (v1903+) or Windows 11 |
| **Processor** | 1.6 GHz or faster, 2-core |
| **Memory (RAM)** | 4 GB |
| **Storage** | 500 MB available space |
| **Display** | 1280 x 720 resolution |
| **.NET Framework** | 4.7.2 or higher (included) |
| **Graphics** | DirectX 9 compatible |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 11 |
| **Processor** | 2.0 GHz or faster, 4-core |
| **Memory (RAM)** | 8 GB or more |
| **Storage** | 1 GB available space (SSD preferred) |
| **Display** | 1920 x 1080 resolution or higher |
| **Graphics** | DirectX 11 compatible with WDDM 2.0 |

### Additional Notes

- ✅ **No Administrator Rights Required** for portable version
- ✅ **Works Offline** - No internet connection needed
- ✅ **Compatible** with Windows on ARM (via emulation)
- ⚠️ **Not Compatible** with Windows 7, 8, or 8.1

---

## Pre-Installation Checklist

Before installing, ensure:

- [ ] **Windows is up to date**
  - Windows Settings → Update & Security → Check for updates
  
- [ ] **Sufficient disk space available**
  - Check C: drive has at least 1 GB free
  
- [ ] **Antivirus is configured**
  - May need to add exception during installation
  
- [ ] **Previous versions uninstalled** (if applicable)
  - Uninstall via Control Panel first

- [ ] **Apple Health export ready** (optional)
  - Have your export.xml file ready to import

---

## Installation Methods

### Method 1: Windows Installer (Recommended)

Best for most users - provides Start Menu integration and automatic updates.

#### Step 1: Download the Installer

1. Visit the official website: `www.example.com`
2. Click **"Download for Windows"**
3. Save `AppleHealthMonitor-Setup-1.0.0.exe` to Downloads

![Download Page](images/install-download.png)

#### Step 2: Verify the Download

- **File Size**: Should be approximately 85 MB
- **Digital Signature**: Right-click → Properties → Digital Signatures
- **Hash Verification** (Optional):
  ```powershell
  Get-FileHash .\AppleHealthMonitor-Setup-1.0.0.exe -Algorithm SHA256
  ```

#### Step 3: Run the Installer

1. **Locate the installer** in your Downloads folder
2. **Double-click** `AppleHealthMonitor-Setup-1.0.0.exe`

![Installer Icon](images/install-exe-icon.png)

#### Step 4: Handle Security Warnings

If you see "Windows protected your PC":

![SmartScreen Warning](images/install-smartscreen.png)

1. Click **"More info"**
2. Click **"Run anyway"**
3. This is normal for new software

#### Step 5: Installation Wizard

**Welcome Screen**
![Welcome Screen](images/install-wizard-1.png)
- Click **"Next"** to continue

**License Agreement**
![License Agreement](images/install-wizard-2.png)
- Read the agreement
- Select **"I accept the agreement"**
- Click **"Next"**

**Choose Install Location**
![Install Location](images/install-wizard-3.png)
- Default: `C:\Program Files\Apple Health Monitor`
- Change if desired (not recommended)
- Click **"Next"**

**Select Components**
![Components](images/install-wizard-4.png)
- ✅ Core Application (Required)
- ✅ Desktop Shortcut
- ✅ Start Menu Shortcuts
- ☐ Launch on Windows Startup (Optional)
- Click **"Next"**

**Ready to Install**
![Ready to Install](images/install-wizard-5.png)
- Review your choices
- Click **"Install"**

**Installation Progress**
![Progress](images/install-wizard-6.png)
- Takes 30-60 seconds
- Do not interrupt

**Completion**
![Complete](images/install-wizard-7.png)
- ✅ Launch Apple Health Monitor
- Click **"Finish"**

### Method 2: Portable Version

No installation required - perfect for USB drives or restricted systems.

#### Step 1: Download Portable ZIP

1. Visit download page
2. Choose **"Portable Version (ZIP)"**
3. Save `AppleHealthMonitor-Portable-1.0.0.zip`

#### Step 2: Extract Files

1. **Right-click** the ZIP file
2. Select **"Extract All..."**

![Extract Dialog](images/install-extract.png)

3. Choose destination:
   - Recommended: `C:\PortableApps\AppleHealthMonitor`
   - Or USB drive: `E:\AppleHealthMonitor`
4. Click **"Extract"**

#### Step 3: Folder Structure

After extraction:
```
AppleHealthMonitor/
├── AppleHealthMonitor.exe      # Main application
├── AppleHealthMonitor.ini      # Configuration
├── Resources/                  # Application resources
│   ├── Icons/
│   ├── Themes/
│   └── Templates/
├── Libraries/                  # Required DLLs
└── README.txt                  # Quick instructions
```

#### Step 4: First Run

1. Open the extracted folder
2. Double-click **`AppleHealthMonitor.exe`**
3. Windows Defender may scan (normal)
4. Application starts

#### Step 5: Create Shortcuts (Optional)

**Desktop Shortcut:**
1. Right-click `AppleHealthMonitor.exe`
2. Select "Send to" → "Desktop (create shortcut)"

**Pin to Taskbar:**
1. Right-click the running application
2. Select "Pin to taskbar"

### Method 3: MSI Package (Enterprise)

For IT administrators deploying to multiple computers.

#### Features

- Silent installation support
- Group Policy deployment
- Custom configuration
- Network installation
- No user interaction required

#### Step 1: Download MSI Package

1. Visit enterprise download page
2. Download `AppleHealthMonitor-1.0.0.msi`
3. Download `AppleHealthMonitor-Config.mst` (optional)

#### Step 2: Command Line Installation

**Basic Installation:**
```cmd
msiexec /i AppleHealthMonitor-1.0.0.msi /qn
```

**With Logging:**
```cmd
msiexec /i AppleHealthMonitor-1.0.0.msi /qn /l*v install.log
```

**Custom Location:**
```cmd
msiexec /i AppleHealthMonitor-1.0.0.msi INSTALLDIR="D:\Apps\HealthMonitor" /qn
```

**With Transform File:**
```cmd
msiexec /i AppleHealthMonitor-1.0.0.msi TRANSFORMS=AppleHealthMonitor-Config.mst /qn
```

#### Step 3: Group Policy Deployment

1. Copy MSI to network share
2. Open Group Policy Management
3. Create new GPO
4. Computer Configuration → Software Installation
5. Add package → Select MSI
6. Deploy to target computers

#### Available MSI Properties

| Property | Description | Default |
|----------|-------------|---------|
| INSTALLDIR | Installation directory | C:\Program Files\Apple Health Monitor |
| SHORTCUTS | Create shortcuts (0/1) | 1 |
| AUTOSTART | Launch on startup (0/1) | 0 |
| DEFAULTTHEME | Light/Dark | Light |

---

## Post-Installation Setup

### First Launch Configuration

When you first start the application:

1. **Welcome Dialog**
   ![First Launch](images/post-install-welcome.png)
   - Introduction to features
   - Option for quick tour
   - Privacy statement

2. **Initial Preferences**
   ![Preferences](images/post-install-prefs.png)
   - **Theme**: Light or Dark mode
   - **Date Format**: MM/DD/YYYY or DD/MM/YYYY
   - **Start Tab**: Which view opens first
   - **Auto-save**: Enable journal auto-save

3. **Data Directory**
   - Default: `%APPDATA%\AppleHealthMonitor`
   - Contains:
     - Database files
     - Cache
     - User preferences
     - Journal entries

### Optional Configuration

#### File Associations

Associate `.healthexport` files:
1. Settings → File Associations
2. Check "Associate with health export files"
3. Apply changes

#### Windows Defender Exception

If experiencing slow performance:
1. Windows Security → Virus & threat protection
2. Manage settings → Exclusions
3. Add folder: Installation directory

#### Firewall Configuration

Application works offline, but for updates:
1. Windows Defender Firewall
2. Allow an app
3. Add Apple Health Monitor

---

## Uninstallation

### Uninstalling Installer Version

#### Method 1: Via Windows Settings
1. Windows Settings → Apps
2. Search "Apple Health Monitor"
3. Click app → Uninstall
4. Follow prompts

#### Method 2: Via Control Panel
1. Control Panel → Programs and Features
2. Find "Apple Health Monitor"
3. Right-click → Uninstall
4. Complete wizard

#### Method 3: Via Start Menu
1. Start Menu → Apple Health Monitor folder
2. Click "Uninstall"
3. Confirm removal

### Uninstalling Portable Version

1. Close the application
2. Delete the folder containing the app
3. Remove any shortcuts created
4. Optional: Clean registry
   ```
   HKEY_CURRENT_USER\Software\AppleHealthMonitor
   ```

### Removing User Data

User data location: `%APPDATA%\AppleHealthMonitor`

**To completely remove:**
1. Uninstall application first
2. Navigate to `%APPDATA%`
3. Delete `AppleHealthMonitor` folder
4. Empty Recycle Bin

**To preserve data:**
- Keep the folder for future installations
- Or backup before deleting

---

## Troubleshooting Installation

### Common Installation Issues

#### "This app can't run on your PC"

**Cause**: Wrong architecture or OS version
**Solution**: 
- Verify Windows 10 v1903+ or Windows 11
- Download correct version (x64 vs x86)

#### Installation Hangs

**Solutions**:
1. End task in Task Manager
2. Restart computer
3. Disable antivirus temporarily
4. Run as administrator

#### "Access Denied" Errors

**Solutions**:
1. Choose different install location
2. Run installer as administrator
3. Check disk permissions
4. Use portable version

#### Missing Dependencies

**If app won't start**:
1. Install Visual C++ Redistributables:
   - Download from Microsoft
   - Install both x64 and x86 versions
   
2. Update .NET Framework:
   - Windows Update
   - Or download from Microsoft

### Installation Logs

**Locating Logs**:
- Installer logs: `%TEMP%\AppleHealthMonitor_Install.log`
- MSI logs: Use `/l*v` parameter
- Windows Event Viewer → Application logs

**Reading Logs**:
- Search for "ERROR" or "FAIL"
- Note error codes
- Check timestamps

---

## Advanced Options

### Silent Installation

For automated deployment:

```cmd
AppleHealthMonitor-Setup-1.0.0.exe /S /D=C:\Program Files\AppleHealthMonitor
```

Parameters:
- `/S` - Silent mode
- `/D=` - Installation directory
- `/SHORTCUTS=0` - No shortcuts
- `/AUTOSTART=1` - Enable autostart

### Custom Configuration

**Pre-configure Settings**:
1. Install on reference machine
2. Configure as desired
3. Copy `%APPDATA%\AppleHealthMonitor\config.ini`
4. Deploy with installation

**Config File Example**:
```ini
[General]
Theme=Dark
DateFormat=DD/MM/YYYY
AutoSave=true
DefaultTab=Daily

[Performance]
CacheSize=500
EnableAnimations=false
ChartQuality=High

[Privacy]
Analytics=false
CrashReports=false
```

### Network Installation

**For Shared Network Drive**:
1. Install to network location
2. Create launcher script:
   ```batch
   @echo off
   "\\Server\Apps\AppleHealthMonitor\AppleHealthMonitor.exe" %*
   ```
3. Deploy launcher to users

### Portable Mode via Installer

Force portable mode:
```cmd
AppleHealthMonitor-Setup-1.0.0.exe /PORTABLE=1
```

This:
- Installs to current directory
- Stores settings locally
- No registry entries

### Command Line Options

**Application Parameters**:
- `--import <file>` - Auto-import on start
- `--tab <name>` - Open specific tab
- `--safe-mode` - Disable plugins
- `--reset` - Reset all settings

**Example**:
```cmd
AppleHealthMonitor.exe --import "C:\exports\health.xml" --tab Daily
```

---

## Quick Reference

### File Locations

| Item | Location |
|------|----------|
| **Installed Application** | `C:\Program Files\Apple Health Monitor\` |
| **User Data** | `%APPDATA%\AppleHealthMonitor\` |
| **Portable Data** | `<AppFolder>\Data\` |
| **Temp Files** | `%TEMP%\AppleHealthMonitor\` |
| **Logs** | `%APPDATA%\AppleHealthMonitor\Logs\` |

### Registry Keys

| Key | Purpose |
|-----|---------|
| `HKLM\Software\AppleHealthMonitor` | Installation info |
| `HKCU\Software\AppleHealthMonitor` | User preferences |
| `HKCR\.healthexport` | File association |

### Environment Variables

Set these for special behavior:
- `AHM_DEBUG=1` - Enable debug logging
- `AHM_PORTABLE=1` - Force portable mode
- `AHM_DATA_DIR=<path>` - Custom data location

---

**Installation Complete!** 🎉

Now proceed to the [Quick Start Guide](QUICK_START_GUIDE.md) to begin using Apple Health Monitor Dashboard.

*Version 1.0 | Last Updated: June 2025*