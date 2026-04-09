# BackPocket OS - Quick Backup & Restore

## What's Included in Backup

| Category | Files | Status |
|----------|-------|--------|
| **Core Code** | main.py, services/ | ✅ |
| **Dashboard** | static/index.html | ✅ |
| **Database** | backpocket.db | ✅ |
| **Config** | .env (not secrets) | ✅ |
| **Documentation** | docs/* (all files) | ✅ |
| **Session Logs** | SESSION_LOG.md, AGENTS.md | ✅ |

## Quick Backup (Before Changes)

### For Code (main.py, services/)
```powershell
git add -A
git commit -m "Backup before changes"
```

### For Dashboard (index.html)
```powershell
copy static\index.html "static\index.html.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

### Full System Backup (Recommended)
```powershell
.\scripts\backup_restore.ps1 -Action backup
```

This creates: `backups/backup_20260404_120000/` containing all files above.

### Restore Dashboard
```powershell
# List backups
dir static\index.html.backup*

# Restore latest
copy "static\index.html.backup-YYYYMMDD-HHMMSS" static\index.html
```

### Restore from Git
```powershell
# See recent commits
git log --oneline -10

# Restore specific file
git checkout HEAD~1 -- main.py
git checkout HEAD~1 -- static/index.html
```

## Auto-Backup Before Editing

I will now automatically:
1. Create timestamped backup before editing main.py or index.html
2. Store in same folder as the file
3. Log the backup in SESSION_LOG.md

## Recovery Commands

| Scenario | Command |
|----------|---------|
| Dashboard broken | `git checkout HEAD -- static/index.html` |
| Code broken | `git checkout HEAD -- main.py` |
| Full rollback | `git checkout HEAD~1` |
| Specific backup | `copy "static\index.html.backup-20260404-120000" static\index.html` |

## Current Backups Available

Run: `dir main.py.backup*` and `dir static\index.html.backup*`
