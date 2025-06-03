# Packaging Issues Log

This document tracks all issues discovered during packaging testing of the Apple Health Dashboard.

## Issue Tracking Template

```markdown
## Issue ID: PKG-XXX
**Severity**: High/Medium/Low  
**Format**: EXE/Installer/Portable  
**OS**: Windows 10/11  
**Version**: 1.0.0  
**Date Found**: YYYY-MM-DD  
**Tester**: Name  

### Description
[Clear description of the issue]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Screenshots/Logs
[Attach if relevant]

### Workaround
[If available]

### Resolution
[How it was fixed, or "Pending"]
```

---

## Known Issues

### PKG-001: Antivirus False Positive (Example)
**Severity**: Medium  
**Format**: EXE  
**OS**: Windows 10/11  
**Version**: 1.0.0  
**Date Found**: 2025-06-02  
**Tester**: System  

**Description**: Windows Defender may flag the unsigned executable as potentially unsafe.

**Steps to Reproduce**:
1. Download AppleHealthDashboard.exe
2. Run the executable
3. Windows Defender SmartScreen appears

**Expected Behavior**: Application should run without security warnings.

**Actual Behavior**: SmartScreen warning appears for unsigned application.

**Workaround**: 
- Click "More info" then "Run anyway"
- Or right-click exe → Properties → Unblock

**Resolution**: Implement code signing in T04_S07

---

### PKG-002: Missing Visual C++ Redistributable (Example)
**Severity**: High  
**Format**: All  
**OS**: Windows 10/11  
**Version**: 1.0.0  
**Date Found**: 2025-06-02  
**Tester**: System  

**Description**: Application fails to start on clean Windows with missing VCRUNTIME140.dll

**Steps to Reproduce**:
1. Fresh Windows installation
2. Run AppleHealthDashboard.exe
3. Error dialog appears

**Expected Behavior**: Application should start normally.

**Actual Behavior**: "VCRUNTIME140.dll was not found" error.

**Workaround**: Install Visual C++ Redistributable 2015-2022

**Resolution**: Bundle redistributables or add to installer

---

## Performance Baselines

### Startup Times
| Format | Windows 10 | Windows 11 | Target |
|--------|------------|------------|--------|
| EXE    | X.X s      | X.X s      | <5s    |
| Installer | X.X s   | X.X s      | <5s    |
| Portable | X.X s    | X.X s      | <5s    |

### Memory Usage (Idle)
| Format | Windows 10 | Windows 11 | Target |
|--------|------------|------------|--------|
| EXE    | XXX MB     | XXX MB     | <500MB |
| Installer | XXX MB  | XXX MB     | <500MB |
| Portable | XXX MB   | XXX MB     | <500MB |

### File Sizes
| Format | Size | Compressed |
|--------|------|------------|
| EXE    | XX MB | N/A       |
| Installer | XX MB | XX MB  |
| Portable ZIP | XX MB | XX MB |

---

## Test Environment Issues

### ENV-001: Insufficient Disk Space
**Description**: Test VM ran out of disk space during large file import test.
**Impact**: Could not complete performance testing with 500MB file.
**Resolution**: Increase VM disk to 50GB minimum.

### ENV-002: Windows Defender Interference  
**Description**: Real-time scanning significantly slowed startup time measurements.
**Impact**: Startup times 2-3x slower than expected.
**Resolution**: Add test directory to Windows Defender exclusions.

---

## Deferred Issues

Issues that will not be fixed in v1.0.0:

### DEF-001: Auto-update Not Implemented
**Reason**: Scheduled for v1.1.0 release
**Workaround**: Manual download and install

### DEF-002: Localization Support
**Reason**: English-only for MVP
**Workaround**: None needed for target audience

---

## Testing Notes

### General Observations
- Performance is generally better on Windows 11
- Portable version has slightly slower startup due to no installation optimization
- Memory usage increases with data file size (approximately 2x file size)

### Compatibility Notes
- Requires .NET Framework 4.8 (included in Windows 10 1903+)
- Requires Visual C++ Redistributable 2015-2022
- Works with Windows 10 version 1809 and later
- No issues found with high DPI displays

### Security Considerations
- Unsigned executables trigger SmartScreen
- Some corporate environments may block unsigned apps
- No elevation required for any distribution format
- User data stored in standard user directories only