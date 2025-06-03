# Release Checklist - Apple Health Monitor v{VERSION}

**Release Date**: {DATE}  
**Release Manager**: {NAME}  
**Type**: ☐ Major ☐ Minor ☐ Patch ☐ Hotfix  

## Pre-Release Phase (T-7 days)

### Planning & Preparation
- [ ] Confirm release date and scope
- [ ] Assign release manager
- [ ] Review milestone completion
- [ ] Identify any blockers

### Feature Freeze (T-7)
- [ ] Merge all feature branches
- [ ] Lock main branch for features
- [ ] Communicate freeze to team
- [ ] Document any exceptions

## Testing Phase (T-6 to T-3 days)

### Automated Testing
- [ ] Run full test suite: `pytest tests/`
- [ ] Check test coverage: `pytest --cov=src --cov-report=html`
- [ ] Run performance tests: `pytest tests/performance/`
- [ ] Verify all tests pass

### Manual Testing
- [ ] Test installation on clean Windows 10
- [ ] Test installation on Windows 11
- [ ] Verify all UI functions work
- [ ] Test data import process
- [ ] Check all visualizations render
- [ ] Verify export functions

### Documentation
- [ ] Update user documentation
- [ ] Review API documentation
- [ ] Update screenshots if UI changed
- [ ] Spell check all docs

## Release Preparation (T-2 to T-1 days)

### Version Updates
- [ ] Update `src/version.py`:
  ```python
  __version__ = "{VERSION}"
  __release_date__ = "{DATE}"
  ```
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Create `RELEASE_NOTES_v{VERSION}.md`
- [ ] Update README.md if needed

### Final Review
- [ ] Code review any last-minute changes
- [ ] Security scan: `pip-audit`
- [ ] License check: all dependencies compatible
- [ ] Final proofreading of release notes

### Build Preparation
- [ ] Clean build environment
- [ ] Update requirements.txt if needed
- [ ] Test build process locally
- [ ] Verify artifact naming convention

## Release Day (T-0)

### Final Checks (Morning)
- [ ] Pull latest from main branch
- [ ] Run final test suite
- [ ] Verify version number is correct
- [ ] Check CI/CD pipeline status

### Git Operations
- [ ] Create release tag:
  ```bash
  git tag -a v{VERSION} -m "Release version {VERSION}"
  git push origin v{VERSION}
  ```
- [ ] Verify tag on GitHub

### Build Artifacts
- [ ] Clean previous builds: `rm -rf build/ dist/`
- [ ] Build standalone exe: `python build.py --exe`
- [ ] Build installer: `python build.py --installer`
- [ ] Build portable: `python build.py --portable`
- [ ] Verify all artifacts created

### Artifact Testing
- [ ] Test standalone exe launches
- [ ] Test installer process
- [ ] Test uninstaller works
- [ ] Test portable version
- [ ] Scan with antivirus

### Code Signing (if applicable)
- [ ] Sign all executables
- [ ] Verify signatures
- [ ] Test signed artifacts

### GitHub Release
- [ ] Create new release on GitHub
- [ ] Select correct tag (v{VERSION})
- [ ] Add release title
- [ ] Paste release notes
- [ ] Upload artifacts:
  - [ ] AppleHealthMonitor-{VERSION}.exe
  - [ ] AppleHealthMonitor-{VERSION}-installer.exe
  - [ ] AppleHealthMonitor-{VERSION}-portable.zip
- [ ] Set as latest release
- [ ] Publish release

### Verification
- [ ] Download artifacts from GitHub
- [ ] Quick test each artifact
- [ ] Verify file sizes are reasonable
- [ ] Check download links work

## Post-Release (T+0 to T+1 hours)

### Communications
- [ ] Send release announcement email
- [ ] Post on social media:
  - [ ] Twitter/X
  - [ ] LinkedIn
  - [ ] Reddit (r/quantifiedself)
- [ ] Update project website
- [ ] Notify beta testers

### Documentation Updates
- [ ] Update download links in docs
- [ ] Deploy updated documentation
- [ ] Update installation guide
- [ ] Check all links work

### Monitoring
- [ ] Monitor GitHub issues
- [ ] Check Discord/community channels
- [ ] Watch for crash reports
- [ ] Track download statistics

## Follow-Up (T+1 to T+7 days)

### Day 1
- [ ] Review any immediate feedback
- [ ] Address critical issues
- [ ] Respond to user questions
- [ ] Update FAQ if needed

### Day 3
- [ ] Analyze download statistics
- [ ] Review user feedback trends
- [ ] Plan any hotfix if needed
- [ ] Thank contributors

### Day 7
- [ ] Compile release retrospective
- [ ] Document lessons learned
- [ ] Update release process if needed
- [ ] Plan next release cycle

## Rollback Plan

If critical issues discovered:

### Immediate Actions
- [ ] Mark release as pre-release on GitHub
- [ ] Post known issues warning
- [ ] Communicate via all channels
- [ ] Begin hotfix process

### Hotfix Process
- [ ] Create hotfix branch
- [ ] Apply minimal fix
- [ ] Fast-track testing
- [ ] Release as {VERSION}.1

## Notes Section

### What Went Well
- 

### Issues Encountered
- 

### Improvements for Next Time
- 

## Sign-Off

- [ ] Release Manager: _________________ Date: _______
- [ ] QA Lead: _______________________ Date: _______
- [ ] Technical Lead: __________________ Date: _______

---

**Remember**: Quality > Speed. If something feels wrong, investigate before proceeding.