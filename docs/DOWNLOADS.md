# Download Apple Health Monitor

Choose the version that best suits your needs. All versions include the full feature set - the only difference is how they're packaged.

## 🎯 Quick Download Links

| Version | Size | Best For | Download |
|---------|------|----------|----------|
| **Installer** (Recommended) | ~65 MB | Most users - Easy installation with Start menu shortcuts | [Download v1.0.0](https://github.com/yourusername/apple-health-monitor/releases/download/v1.0.0/AppleHealthMonitor-1.0.0-installer.exe) |
| **Portable** | ~68 MB | USB drives - No installation needed | [Download v1.0.0](https://github.com/yourusername/apple-health-monitor/releases/download/v1.0.0/AppleHealthMonitor-1.0.0-portable.zip) |
| **Standalone** | ~70 MB | Advanced users - Single executable file | [Download v1.0.0](https://github.com/yourusername/apple-health-monitor/releases/download/v1.0.0/AppleHealthMonitor-1.0.0.exe) |

## 📋 System Requirements

Before downloading, ensure your system meets these requirements:

- **Operating System**: Windows 10 (version 1809 or later) or Windows 11
- **Processor**: 64-bit processor (x64)
- **Memory**: 4 GB RAM minimum (8 GB recommended)
- **Storage**: 500 MB available space
- **Display**: 1366×768 minimum resolution
- **.NET Framework**: Not required (bundled)
- **Internet**: Only for downloading (app works offline)

## 🔍 Version Details

### Windows Installer (Recommended)
Best for most users who want a traditional Windows application experience.

**Features:**
- ✅ One-click installation
- ✅ Start Menu shortcuts
- ✅ Desktop shortcut (optional)
- ✅ File associations for .healthmonitor files
- ✅ Clean uninstaller included
- ✅ Automatic PATH configuration

**Installation Steps:**
1. Download the installer
2. Run `AppleHealthMonitor-1.0.0-installer.exe`
3. Follow the installation wizard
4. Launch from Start Menu or Desktop

### Portable Version
Perfect for running from USB drives or when you don't have installation privileges.

**Features:**
- ✅ No installation required
- ✅ Settings stored with application
- ✅ Can run from USB drive
- ✅ Multiple instances possible
- ✅ Easy backup - just copy the folder

**Usage Steps:**
1. Download the ZIP file
2. Extract to any folder (e.g., USB drive)
3. Run `AppleHealthMonitor.exe` from the extracted folder
4. All settings saved in the same directory

### Standalone Executable
For advanced users who prefer a single file solution.

**Features:**
- ✅ Single file - no extraction needed
- ✅ Can be placed anywhere
- ✅ Command-line friendly
- ✅ Smallest download size

**Usage Steps:**
1. Download the EXE file
2. Place it in your preferred location
3. Double-click to run
4. Settings saved in user's AppData folder

## 🛡️ Security & Verification

### File Checksums
Verify your download hasn't been tampered with:

```
AppleHealthMonitor-1.0.0-installer.exe
SHA256: [checksum will be here]

AppleHealthMonitor-1.0.0-portable.zip
SHA256: [checksum will be here]

AppleHealthMonitor-1.0.0.exe
SHA256: [checksum will be here]
```

### Verify on Windows
```powershell
# In PowerShell, run:
Get-FileHash "AppleHealthMonitor-1.0.0-installer.exe" -Algorithm SHA256
```

### Antivirus False Positives
Some antivirus software may flag the application. This is a false positive common with PyInstaller-packaged applications. The app is safe and open source.

**If you encounter this:**
1. Add an exception for the application in your antivirus
2. Or download from GitHub and build from source
3. Check our [VirusTotal scan results](link)

## 🚀 Getting Started After Download

### First Time Setup
1. **Export your Apple Health data**
   - On iPhone: Health app → Profile → Export All Health Data
   - Transfer the `export.zip` to your PC

2. **Launch Apple Health Monitor**
   - Use the shortcut (installer version) or run the executable

3. **Import your data**
   - Click "Import Health Data" on the Configuration tab
   - Select your `export.zip` file
   - Wait for import to complete

4. **Explore your health insights**
   - Navigate through Daily, Weekly, and Monthly views
   - Check your Health Score
   - Start journaling your health journey

### Need Help?
- 📖 [User Guide](user-guide.md)
- 🎥 [Video Tutorials](tutorials.md)
- ❓ [FAQ](faq.md)
- 🐛 [Troubleshooting](troubleshooting.md)

## 📊 Version Comparison

| Feature | Installer | Portable | Standalone |
|---------|-----------|----------|------------|
| Easy installation | ✅ | ❌ | ❌ |
| No admin rights needed | ❌ | ✅ | ✅ |
| Start menu integration | ✅ | ❌ | ❌ |
| Uninstaller included | ✅ | ❌ | ❌ |
| Run from USB | ❌ | ✅ | ✅ |
| Settings location | AppData | App folder | AppData |
| Update notifications | ✅ | ✅ | ✅ |
| File associations | ✅ | ❌ | ❌ |

## 🔄 Updating

The application will notify you when updates are available. To update:

**Installer Version:**
1. Download the new installer
2. Run it - it will update your existing installation
3. Your data and settings are preserved

**Portable/Standalone:**
1. Download the new version
2. Replace the old file(s)
3. Your data is stored separately and will be preserved

## 🌍 Alternative Downloads

### Build from Source
For developers or users who prefer to build from source:

```bash
git clone https://github.com/yourusername/apple-health-monitor.git
cd apple-health-monitor
pip install -r requirements.txt
python src/main.py
```

See [Development Guide](development.md) for detailed instructions.

### Previous Versions
Need an older version? Check our [releases page](https://github.com/yourusername/apple-health-monitor/releases) for all historical versions.

## ❓ Frequently Asked Questions

**Q: Which version should I download?**
A: For most users, the Installer version is recommended. It provides the best Windows integration and easiest updates.

**Q: Can I run multiple versions?**
A: Yes, with the Portable version. The Installer version can only have one installation at a time.

**Q: Is my data safe?**
A: Yes! All data is stored locally on your computer. The app never connects to the internet except to check for updates.

**Q: Can I move my data between versions?**
A: Yes, you can export your data from one version and import it into another.

## 📞 Need Help?

- 📧 Email: support@yourdomain.com
- 💬 Discord: [Join our community](discord-link)
- 🐛 Issues: [GitHub Issues](github-issues-link)
- 📖 Docs: [Full documentation](docs-link)

---

**Note**: Apple Health Monitor is open source software distributed under the MIT License. By downloading, you agree to the [license terms](LICENSE).