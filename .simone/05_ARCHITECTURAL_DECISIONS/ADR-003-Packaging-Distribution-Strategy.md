# ADR-003: Packaging and Distribution Strategy

## Status
Accepted

## Context
We need to distribute the Apple Health Monitor Dashboard to non-technical Windows users who expect a simple installation experience. The solution must:
- Work without Python installation
- Include all dependencies
- Provide a familiar Windows installation experience
- Support automatic updates
- Maintain reasonable file size

## Decision
We will use **PyInstaller** to create a standalone executable, distributed via **NSIS installer** with an optional portable mode.

## Rationale

### Options Considered

#### 1. PyInstaller
**Pros:**
- Mature and well-supported
- Handles complex dependencies well
- Single executable output
- Good PyQt6 support

**Cons:**
- Large file size
- Slower startup time
- Antivirus false positives

#### 2. cx_Freeze
**Pros:**
- Cross-platform support
- Smaller output size
- MSI installer support

**Cons:**
- More configuration required
- Less community support
- Issues with some Qt dependencies

#### 3. Nuitka
**Pros:**
- Compiles to C++
- Better performance
- Smaller size potential

**Cons:**
- Longer build times
- Complex debugging
- Less mature for Qt apps

#### 4. py2exe
**Pros:**
- Windows-specific optimizations
- DLL bundling options

**Cons:**
- Windows only
- Less active development
- Compatibility issues with newer Python

### Packaging Architecture

```
Distribution Package/
├── HealthMonitor-Setup.exe    # NSIS Installer
├── HealthMonitor-Portable.zip # Portable Version
└── Updates/
    └── HealthMonitor.exe      # Direct executable
```

### Build Configuration

```python
# pyinstaller.spec
a = Analysis(
    ['src/main.py'],
    hiddenimports=[
        'PyQt6.QtPrintSupport',  # Often missed
        'matplotlib.backends.backend_qt5agg',
        'pandas._libs.tslibs.parsing',
    ],
    excludes=[
        'tkinter',      # Not needed
        'unittest',     # Development only
        'pip',          # Not needed in exe
        'setuptools',   # Not needed in exe
    ],
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HealthMonitor',
    debug=False,
    console=False,  # No console window
    icon='assets/icon.ico',
    version='version_info.txt',
    uac_admin=False,  # No admin required
)
```

## Distribution Strategy

### 1. Installer (Recommended)
```nsis
; NSIS script excerpt
!define MUI_WELCOMEPAGE_TITLE "Health Monitor Setup"
!define MUI_WELCOMEPAGE_TEXT "Monitor your Apple Health data with ease"

Section "Core Files" SEC_CORE
    SetOutPath "$INSTDIR"
    File /r "dist\*.*"
    
    ; Create shortcuts
    CreateShortcut "$DESKTOP\Health Monitor.lnk" "$INSTDIR\HealthMonitor.exe"
    CreateShortcut "$SMPROGRAMS\Health Monitor\Health Monitor.lnk" "$INSTDIR\HealthMonitor.exe"
    
    ; Register uninstaller
    WriteRegStr HKLM "${REGKEY}" "InstallPath" "$INSTDIR"
    WriteRegStr HKLM "${REGKEY}" "Version" "${VERSION}"
SectionEnd
```

### 2. Portable Version
- No installation required
- Saves data in application directory
- Ideal for USB drives or restricted environments

### 3. Auto-Update System
```python
class UpdateManager:
    UPDATE_URL = "https://api.healthmonitor.app/updates/windows"
    
    def check_updates(self):
        current = self.get_current_version()
        latest = self.fetch_latest_version()
        
        if latest > current:
            return UpdateInfo(
                version=latest,
                download_url=f"{self.UPDATE_URL}/{latest}/HealthMonitor.exe",
                changelog_url=f"{self.UPDATE_URL}/{latest}/changelog.md"
            )
```

## Size Optimization

### Strategies Applied
1. **Exclude Unused Modules**: Remove tkinter, test frameworks
2. **UPX Compression**: Compress executable (~40% reduction)
3. **Optimize Images**: Convert to optimized formats
4. **Strip Debug Symbols**: Remove unnecessary debugging info

### Expected Sizes
- Uncompressed: ~120MB
- UPX Compressed: ~70MB
- Installer: ~65MB
- Portable ZIP: ~68MB

## Security Considerations

### Code Signing
```bash
# Sign executable to prevent antivirus warnings
signtool sign /f certificate.pfx /p password /t http://timestamp.url HealthMonitor.exe
```

### Antivirus Whitelisting
- Submit to major antivirus vendors
- Include signed manifest
- Document false positive solutions

## Consequences

### Positive
- Simple one-click installation for users
- No Python knowledge required
- Professional appearance
- Automatic updates possible
- Portable option available

### Negative
- Large download size
- Potential antivirus false positives
- Slower startup than native apps
- Complex build process
- Platform-specific builds needed

### Mitigation
- Provide clear download progress
- Include antivirus whitelist instructions
- Implement splash screen for startup
- Automate build process with CI/CD
- Clear documentation for build process

## Build Automation

### GitHub Actions Workflow
```yaml
name: Build Windows Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller pyinstaller.spec
      
      - name: Compress with UPX
        run: upx --best dist/HealthMonitor.exe
      
      - name: Create installer
        run: makensis installer.nsi
      
      - name: Sign executables
        run: |
          signtool sign /f ${{ secrets.CERT }} dist/HealthMonitor.exe
          signtool sign /f ${{ secrets.CERT }} HealthMonitor-Setup.exe
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: windows-release
          path: |
            HealthMonitor-Setup.exe
            dist/HealthMonitor.exe
```

## References
- [PyInstaller Documentation](https://pyinstaller.org/)
- [NSIS Documentation](https://nsis.sourceforge.io/)
- [UPX Compression](https://upx.github.io/)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)