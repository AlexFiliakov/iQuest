---
task_id: T05_S07
sprint_sequence_id: S07
status: open
complexity: High
last_updated: 2025-01-06T00:00:00Z
---

# Task: Auto-Update System Implementation

## Description
Build an auto-update functionality that allows the application to check for new versions, notify users of available updates, and facilitate the update process. This system should work across all distribution formats while respecting user preferences and maintaining data integrity during updates.

## Goal / Objectives
- Implement version checking mechanism
- Create update notification UI
- Build secure update download system
- Implement update application process
- Ensure data preservation during updates
- Support user preferences for update checking

## Related Documentation
- ADR-003: Packaging and Distribution Strategy (Auto-Update section)
- Version management in src/version.py

## Acceptance Criteria
- [ ] Application checks for updates on startup (configurable)
- [ ] Update notifications are non-intrusive
- [ ] Version comparison works correctly
- [ ] Updates can be downloaded securely
- [ ] Update process preserves user data
- [ ] Users can disable automatic update checks
- [ ] Manual update check is available
- [ ] Update history is maintained

## Subtasks
- [ ] Create update checking service
- [ ] Implement version comparison logic
- [ ] Design update notification UI
- [ ] Build update download manager
- [ ] Create update installer wrapper
- [ ] Implement rollback mechanism
- [ ] Add update preferences to settings
- [ ] Create update changelog viewer
- [ ] Test update scenarios thoroughly

## Implementation Guidance

### Update Architecture
```python
# src/update_manager.py
class UpdateManager:
    def __init__(self):
        self.update_url = "https://api.github.com/repos/USER/REPO/releases/latest"
        self.current_version = self.get_current_version()
        
    def check_for_updates(self):
        """Check if updates are available."""
        # 1. Fetch latest release info
        # 2. Compare versions
        # 3. Return update info if available
        
    def download_update(self, update_info):
        """Download update with progress tracking."""
        # 1. Create temp directory
        # 2. Download with progress callback
        # 3. Verify checksum
        # 4. Return download path
        
    def apply_update(self, update_path):
        """Apply update and restart application."""
        # 1. Close current application
        # 2. Run installer/updater
        # 3. Restart with new version
```

### Version Comparison
```python
from packaging import version

def is_newer_version(current, latest):
    """Compare semantic versions."""
    return version.parse(latest) > version.parse(current)
```

### Update Check API Response
```json
{
  "version": "1.2.0",
  "download_url": "https://github.com/.../AppleHealthMonitor-1.2.0-installer.exe",
  "portable_url": "https://github.com/.../AppleHealthMonitor-1.2.0-portable.zip",
  "exe_url": "https://github.com/.../AppleHealthMonitor-1.2.0.exe",
  "changelog": "### What's New\n- Feature 1\n- Feature 2",
  "release_date": "2024-12-01T00:00:00Z",
  "checksum": {
    "installer": "sha256:...",
    "portable": "sha256:...",
    "exe": "sha256:..."
  }
}
```

### Update Notification UI
```python
class UpdateNotificationWidget(QWidget):
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
        
    def setup_ui(self):
        # Non-intrusive notification bar
        # "Update available: v1.2.0"
        # [View Changes] [Update Now] [Remind Later] [X]
```

### Update Preferences
```python
class UpdatePreferences:
    check_on_startup: bool = True
    auto_download: bool = False
    notification_frequency: str = "once_per_version"  # always, once_per_version, never
    last_check_date: Optional[datetime] = None
    ignored_versions: List[str] = []
```

### Update Process Flow
1. **Check Phase**
   - On startup (if enabled)
   - Manual check via menu
   - Respect check frequency settings

2. **Notification Phase**
   - Show non-blocking notification
   - Allow viewing changelog
   - Provide update/dismiss options

3. **Download Phase**
   - Show progress dialog
   - Verify checksums
   - Handle interruptions gracefully

4. **Installation Phase**
   - Save current state
   - Close application cleanly
   - Launch installer
   - Restart (optional)

### Rollback Support
```python
def create_backup_before_update():
    """Backup critical files before update."""
    backup_items = [
        'data/health.db',
        'data/preferences.json',
        'data/journals/'
    ]
    # Create timestamped backup
```

### Testing Scenarios
- Update from older version
- Skip version and update later
- Interrupt download and resume
- Update with active database operations
- Portable vs installed update paths
- Rollback after failed update

## Output Log
*(This section is populated as work progresses on the task)*

[YYYY-MM-DD HH:MM:SS] Task created
