# Apple Health Monitor Release Process

This document outlines the complete release process for Apple Health Monitor, ensuring consistent and reliable releases.

## Overview

Our release process follows semantic versioning (MAJOR.MINOR.PATCH) and includes automated builds, testing, and distribution through GitHub Releases.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes that require user action
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes and minor improvements

Examples:
- `1.0.0` → `2.0.0`: Major UI overhaul, database format change
- `1.0.0` → `1.1.0`: Added new chart type, new analytics feature
- `1.0.0` → `1.0.1`: Fixed import bug, improved performance

## Pre-Release Checklist

### One Week Before Release

- [ ] **Feature Freeze**: No new features, only bug fixes
- [ ] **Testing Sprint**: Run full test suite
  ```bash
  pytest tests/ --cov=src --cov-report=html
  pytest tests/performance/ --benchmark-only
  ```
- [ ] **Documentation Review**: Ensure all docs are up-to-date
  ```bash
  cd docs/
  make clean html
  # Review generated docs in docs/_build/html/
  ```
- [ ] **Draft Release Notes**: Start writing release notes
- [ ] **Beta Testing**: Deploy to beta testers if major release

### Three Days Before Release

- [ ] **Final Bug Fixes**: Address any critical issues
- [ ] **Update Version Number**:
  ```python
  # Edit src/version.py
  __version__ = "X.Y.Z"
  __release_date__ = "YYYY-MM-DD"
  ```
- [ ] **Update CHANGELOG.md**: Add new version section
- [ ] **Security Scan**: Run security checks
  ```bash
  # Check for known vulnerabilities
  pip-audit
  ```

### One Day Before Release

- [ ] **Final Testing**: Complete test run on clean environment
- [ ] **Build Test Artifacts**: Ensure build process works
- [ ] **Prepare Announcement**: Draft social media and email content
- [ ] **Review Release Notes**: Final proofreading

## Release Day Process

### 1. Final Preparations

```bash
# Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# Run final test suite
pytest tests/

# Verify version number
python -c "from src.version import __version__; print(f'Version: {__version__}')"
```

### 2. Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0

- Feature 1
- Feature 2
- Bug fixes"

# Push tag to GitHub
git push origin v1.0.0
```

### 3. Build Release Artifacts

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Clean previous builds
rm -rf build/ dist/ *.spec

# Build all distribution formats
python build.py --all

# This creates:
# - dist/AppleHealthMonitor-1.0.0.exe (standalone executable)
# - dist/AppleHealthMonitor-1.0.0-installer.exe (NSIS installer)
# - dist/AppleHealthMonitor-1.0.0-portable.zip (portable version)
```

### 4. Test Release Artifacts

Test each artifact on a clean Windows system:

- [ ] **Standalone EXE**: Runs without installation
- [ ] **Installer**: Installs correctly, creates shortcuts
- [ ] **Portable**: Runs from USB drive
- [ ] **Uninstaller**: Removes application cleanly

### 5. Sign Artifacts (if code signing is set up)

```bash
# Sign all executables
python build.py --sign

# Verify signatures
signtool verify /pa dist/*.exe
```

### 6. Create GitHub Release

#### Via GitHub Web Interface:

1. Go to https://github.com/yourusername/apple-health-monitor/releases
2. Click "Draft a new release"
3. Select the tag you created (v1.0.0)
4. Set release title: "Apple Health Monitor v1.0.0"
5. Paste release notes from RELEASE_NOTES_v1.0.0.md
6. Upload artifacts:
   - AppleHealthMonitor-1.0.0.exe
   - AppleHealthMonitor-1.0.0-installer.exe
   - AppleHealthMonitor-1.0.0-portable.zip
7. Check "Set as the latest release"
8. Click "Publish release"

#### Via GitHub CLI:

```bash
# Create release with GitHub CLI
gh release create v1.0.0 \
  --title "Apple Health Monitor v1.0.0" \
  --notes-file RELEASE_NOTES_v1.0.0.md \
  dist/AppleHealthMonitor-1.0.0.exe \
  dist/AppleHealthMonitor-1.0.0-installer.exe \
  dist/AppleHealthMonitor-1.0.0-portable.zip
```

### 7. Verify Release

- [ ] Download each artifact from GitHub
- [ ] Run quick smoke test on each
- [ ] Verify download counts are incrementing
- [ ] Check that release appears on GitHub main page

## Post-Release Tasks

### Immediate (Within 1 Hour)

- [ ] **Update Documentation Site**: Deploy latest docs
- [ ] **Send Announcements**:
  - Email to mailing list
  - Post on social media
  - Update project website
- [ ] **Monitor Feedback Channels**:
  - GitHub Issues
  - Discord/Community channels
  - Email support

### Within 24 Hours

- [ ] **Monitor Crash Reports**: Check for immediate issues
- [ ] **Respond to User Feedback**: Address questions/concerns
- [ ] **Update Download Links**: Ensure all links work
- [ ] **Analytics Review**: Check download statistics

### Within 1 Week

- [ ] **Gather Feedback**: Compile user feedback
- [ ] **Plan Hotfix**: If critical issues found
- [ ] **Start Next Cycle**: Plan next release features
- [ ] **Update Roadmap**: Reflect completed features

## Hotfix Process

For critical bugs requiring immediate fix:

1. **Create Hotfix Branch**:
   ```bash
   git checkout -b hotfix/1.0.1 v1.0.0
   ```

2. **Apply Fix**: Make minimal necessary changes

3. **Test Thoroughly**: Focus on regression testing

4. **Update Version**:
   ```python
   # src/version.py
   __version__ = "1.0.1"
   ```

5. **Fast-Track Release**: Follow abbreviated release process

## Build Artifact Naming Convention

Consistent naming ensures clarity and automation compatibility:

```
Format: AppleHealthMonitor-{version}[-{variant}].{ext}

Examples:
- AppleHealthMonitor-1.0.0.exe          (standalone)
- AppleHealthMonitor-1.0.0-installer.exe (installer)
- AppleHealthMonitor-1.0.0-portable.zip  (portable)
- AppleHealthMonitor-1.0.0-update.exe    (future: auto-update)
```

## Release Channels

### Stable (Default)
- Thoroughly tested
- Recommended for all users
- Major/Minor/Patch releases

### Beta (Opt-in)
- Preview features
- May have minor bugs
- Format: X.Y.Z-beta.N

### Development (Internal)
- Nightly builds
- Unstable, for testing only
- Format: X.Y.Z-dev.YYYYMMDD

## Troubleshooting Common Issues

### Build Fails

```bash
# Clean build environment
rm -rf build/ dist/ *.spec
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-build.txt
```

### GitHub Release Upload Fails

- Check file size limits (2GB per file)
- Verify GitHub token permissions
- Use GitHub CLI for large files

### Code Signing Issues

- Ensure certificate is valid
- Check timestamp server connectivity
- Verify signtool.exe is in PATH

## Security Considerations

- Never commit signing certificates
- Use GitHub Secrets for sensitive data
- Scan artifacts with antivirus before release
- Monitor for security advisories in dependencies

## Automation Opportunities

Future improvements to automate:
- Build artifact creation via GitHub Actions
- Automated testing of release artifacts
- Auto-generation of release notes from commits
- Deployment to distribution channels

## Release Communication Templates

### Email Template
```
Subject: Apple Health Monitor v{VERSION} Released!

Hello {NAME},

We're excited to announce the release of Apple Health Monitor v{VERSION}!

[Brief description of major features/fixes]

Download now: [GitHub Release Link]

Full release notes: [Release Notes Link]

Thank you for your continued support!

Best regards,
The Apple Health Monitor Team
```

### Social Media Template
```
🎉 Apple Health Monitor v{VERSION} is now available!

✨ What's new:
• Feature 1
• Feature 2
• Performance improvements

📥 Download: [link]
📖 Release notes: [link]

#HealthTech #OpenSource #QuantifiedSelf
```

## Metrics to Track

- Download counts per artifact
- Issue reports within 48 hours
- User engagement (if applicable)
- Performance metrics from users
- Adoption rate of new features

---

Remember: Quality over speed. It's better to delay a release than ship with known critical issues.