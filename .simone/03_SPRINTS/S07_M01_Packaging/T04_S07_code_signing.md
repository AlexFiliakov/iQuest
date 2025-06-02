---
task_id: T04_S07
sprint_sequence_id: S07
status: open
complexity: High
last_updated: 2025-01-06T00:00:00Z
---

# Task: Code Signing Implementation and Security

## Description
Implement code signing for the Windows executable and installer to prevent antivirus warnings and establish trust with users. This task includes setting up the signing process, creating signed manifests, and documenting the antivirus vendor submission process to minimize false positives.

## Goal / Objectives
- Set up code signing infrastructure
- Obtain or configure code signing certificate
- Implement automated signing in build process
- Create signed application manifest
- Document antivirus submission process
- Minimize security warnings for end users

## Related Documentation
- ADR-003: Packaging and Distribution Strategy (Security section)
- Windows Authenticode documentation
- Antivirus vendor submission guidelines

## Acceptance Criteria
- [ ] Code signing process is documented and repeatable
- [ ] Executable and installer are properly signed
- [ ] Windows SmartScreen warnings are minimized
- [ ] Signed manifest is included in executable
- [ ] Antivirus submission checklist is created
- [ ] Build process automatically signs artifacts
- [ ] Signature verification passes on target systems

## Subtasks
- [ ] Research code signing certificate options
- [ ] Set up certificate storage (secure, not in repository)
- [ ] Implement signing in build.py script
- [ ] Create application manifest with trust levels
- [ ] Test signed executable on clean Windows systems
- [ ] Document certificate renewal process
- [ ] Create antivirus vendor submission guide
- [ ] Test with major antivirus products
- [ ] Implement signature verification in CI/CD

## Implementation Guidance

### Code Signing Options
1. **Extended Validation (EV) Certificate** (Recommended)
   - Immediate SmartScreen reputation
   - Higher trust level
   - More expensive (~$300-500/year)

2. **Standard Code Signing Certificate**
   - Lower cost (~$100-200/year)
   - Builds reputation over time
   - May show warnings initially

3. **Self-Signed Certificate** (Development only)
   - Free but not trusted
   - Only for internal testing

### Signing Implementation
```python
# In build.py
def sign_executable(exe_path, cert_path, password):
    """Sign executable with code signing certificate."""
    import subprocess
    
    signtool_cmd = [
        'signtool', 'sign',
        '/f', cert_path,         # Certificate file
        '/p', password,          # Certificate password
        '/t', 'http://timestamp.digicert.com',  # Timestamp server
        '/d', 'Apple Health Monitor',  # Description
        '/du', 'https://github.com/...',  # Info URL
        exe_path
    ]
    
    result = subprocess.run(signtool_cmd, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Signing failed: {result.stderr}")
```

### Application Manifest
Create `app.manifest`:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="AppleHealthMonitor"
    type="win32"
  />
  <description>Apple Health Monitor Dashboard</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 11 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
    </application>
  </compatibility>
</assembly>
```

### Certificate Storage
- Never commit certificates to repository
- Use environment variables in CI/CD:
  - `CERT_FILE`: Base64 encoded certificate
  - `CERT_PASSWORD`: Certificate password
- Local development: Store in secure location outside repo

### Antivirus Submission Process
1. **Microsoft Defender**
   - Submit via Microsoft Security Intelligence
   - URL: https://www.microsoft.com/wdsi/filesubmission

2. **Major Vendors to Submit**
   - Norton/Symantec
   - McAfee
   - Avast/AVG
   - Bitdefender
   - Kaspersky
   - ESET

3. **Submission Checklist**
   - [ ] Clean, signed executable
   - [ ] Version information included
   - [ ] Contact information
   - [ ] Brief description of software
   - [ ] Website/documentation links

### Verification Process
Add to build script:
```python
def verify_signature(exe_path):
    """Verify executable signature."""
    cmd = ['signtool', 'verify', '/pa', exe_path]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0
```

## Output Log
*(This section is populated as work progresses on the task)*

[YYYY-MM-DD HH:MM:SS] Task created
