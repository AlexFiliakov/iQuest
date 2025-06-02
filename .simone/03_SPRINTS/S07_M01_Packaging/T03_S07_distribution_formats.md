---
task_id: T03_S07
sprint_sequence_id: S07
status: open
complexity: High
last_updated: 2025-01-06T00:00:00Z
---

# Task: Create All Three Distribution Formats

## Description
Implement the three distribution methods specified in ADR-003: direct executable, NSIS installer with UI, and portable ZIP version. Each format serves different user needs and installation scenarios, from simple executable distribution to professional Windows installation experiences.

## Goal / Objectives
- Create standalone executable for direct distribution
- Develop NSIS installer with professional UI and user experience
- Build portable ZIP version with self-contained data storage
- Ensure all formats maintain full functionality
- Implement format-specific optimizations and configurations

## Related Documentation
- ADR-003: Packaging and Distribution Strategy (Distribution Methods section)
- NSIS documentation: https://nsis.sourceforge.io/

## Acceptance Criteria
- [ ] Direct executable runs without installation
- [ ] NSIS installer provides professional installation experience
- [ ] Installer creates desktop/start menu shortcuts
- [ ] Installer doesn't require admin rights
- [ ] Portable ZIP version stores data in application directory
- [ ] All three formats pass functionality tests
- [ ] Each format handles paths and data storage correctly
- [ ] Uninstaller cleanly removes all application files

## Subtasks
- [ ] Configure PyInstaller for direct executable output
- [ ] Create NSIS installer script based on ADR-003 template
- [ ] Design installer UI with custom graphics
- [ ] Implement portable mode detection and path handling
- [ ] Create portable ZIP packaging script
- [ ] Test data persistence in each format
- [ ] Implement uninstaller functionality
- [ ] Create format-specific README files
- [ ] Test on clean Windows 10/11 systems

## Implementation Guidance

### Direct Executable
- Single file output from PyInstaller
- Stores data in user's AppData directory
- No installation required
- Suitable for quick testing or advanced users

### NSIS Installer Script
Key sections to implement:
```nsis
; Basic installer configuration
Name "Apple Health Monitor"
OutFile "AppleHealthMonitor-${VERSION}-installer.exe"
InstallDir "$LOCALAPPDATA\AppleHealthMonitor"
RequestExecutionLevel user ; No admin required

; Modern UI
!include "MUI2.nsh"
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
```

### Portable ZIP Structure
```
AppleHealthMonitor-portable/
├── AppleHealthMonitor.exe
├── data/              ; User data stored here
│   ├── health.db
│   ├── journals/
│   └── preferences.json
├── README.txt
└── portable.marker    ; Indicates portable mode
```

### Portable Mode Detection
Implement in main.py or config.py:
```python
def is_portable_mode():
    """Check if running in portable mode."""
    app_dir = os.path.dirname(sys.executable)
    return os.path.exists(os.path.join(app_dir, 'portable.marker'))

def get_data_directory():
    """Get appropriate data directory based on mode."""
    if is_portable_mode():
        return os.path.join(os.path.dirname(sys.executable), 'data')
    else:
        return os.path.join(os.environ['APPDATA'], 'AppleHealthMonitor')
```

### Installer Features
- Custom welcome/finish pages
- License agreement display
- Installation directory selection
- Start menu shortcut creation
- Desktop shortcut (optional)
- File association for .health files (future)
- Uninstaller with data removal option

### Testing Requirements
- Test installation without admin rights
- Verify shortcuts work correctly
- Test uninstallation process
- Verify portable mode data isolation
- Test upgrades over existing installations

## Output Log
*(This section is populated as work progresses on the task)*

[YYYY-MM-DD HH:MM:SS] Task created
