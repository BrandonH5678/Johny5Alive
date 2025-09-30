# J5A GitHub Synchronization Guide

## Quick Start

### First Time Setup

1. **Create GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens/new
   - Token name: `J5A System Sync`
   - Expiration: 90 days (or No expiration)
   - Scopes needed:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Configure GitHub Credentials**
   ```bash
   cd /home/johnny5/Johny5Alive
   ./update_github_token.sh
   ```
   - Enter username: `BrandonH5678`
   - Paste the token when prompted

3. **Initial Sync (creates repos if needed)**
   ```bash
   ./sync_to_github.sh --setup
   ```

---

## Regular Usage

### Sync All Systems
```bash
cd /home/johnny5/Johny5Alive
./sync_to_github.sh
```

This will:
- Commit any uncommitted changes in J5A, Squirt, Sherlock
- Push all changes to GitHub
- Show status and repository links

### Sync Individual Systems
```bash
./sync_to_github.sh j5a        # Only J5A
./sync_to_github.sh squirt     # Only Squirt
./sync_to_github.sh sherlock   # Only Sherlock
```

---

## Repository Structure

### J5A (Johny5Alive)
- **Repository:** https://github.com/BrandonH5678/Johny5Alive
- **Description:** Overnight queue/batch management and cross-system coordination
- **Key Features:**
  - Intelligent Model Selection enforcement
  - Incremental Save Pattern protocols
  - Statistical Sampling validation
  - Cross-system resource coordination

### Squirt
- **Repository:** https://github.com/BrandonH5678/Squirt
- **Description:** WaterWizard business document automation with voice processing
- **Key Features:**
  - Voice-to-document workflow (<5 minutes)
  - LibreOffice integration
  - Visual validation system
  - Business hours coordination

### Sherlock
- **Repository:** https://github.com/BrandonH5678/Sherlock
- **Description:** Evidence analysis system with multi-modal processing
- **Key Features:**
  - AAXC audiobook decryption
  - Long-form audio transcription
  - Evidence database
  - Active learning framework

---

## Automation Options

### Add to Cron for Automatic Syncs

Sync every night at midnight:
```bash
# Edit crontab
crontab -e

# Add this line:
0 0 * * * /home/johnny5/Johny5Alive/sync_to_github.sh >> /home/johnny5/Johny5Alive/sync.log 2>&1
```

### Create Desktop Shortcut

Create `~/Desktop/Sync-J5A-GitHub.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Sync J5A to GitHub
Exec=/home/johnny5/Johny5Alive/sync_to_github.sh
Terminal=true
Icon=software-update-available
Categories=Development;
```

Make it executable:
```bash
chmod +x ~/Desktop/Sync-J5A-GitHub.desktop
```

---

## Sharing with Collaborators

### For ChatGPT Integration

When sharing repository links with ChatGPT:

```
I have three AI systems on GitHub:

1. J5A (Overnight Manager): https://github.com/BrandonH5678/Johny5Alive
2. Squirt (Document Automation): https://github.com/BrandonH5678/Squirt
3. Sherlock (Evidence Analysis): https://github.com/BrandonH5678/Sherlock

J5A coordinates overnight operations for Squirt and Sherlock with:
- Intelligent Model Selection (prevents OOM crashes)
- Incremental Save Pattern (prevents data loss)
- Statistical Sampling (early quality validation)
- Cross-system resource management

Please review [specific file/feature] in [repository].
```

### For Human Collaborators

Share repository with read access:
1. Go to repository → Settings → Collaborators
2. Add collaborator by username
3. They can clone with: `git clone https://github.com/BrandonH5678/[repo-name].git`

---

## Troubleshooting

### Permission Denied (403 Error)

Your GitHub token has expired or is invalid.

**Solution:**
```bash
./update_github_token.sh
```

Create new token at: https://github.com/settings/tokens/new

### Repository Already Exists

The script will detect existing repos and just push updates.

If you need to force recreate:
1. Delete repo on GitHub
2. Run: `./sync_to_github.sh --setup`

### Merge Conflicts

If you've made changes on GitHub web interface:

```bash
cd /home/johnny5/[System]
git pull origin main
# Resolve any conflicts
./sync_to_github.sh
```

### Check Current Status

```bash
# J5A
cd /home/johnny5/Johny5Alive && git status

# Squirt
cd /home/johnny5/Squirt && git status

# Sherlock
cd /home/johnny5/Sherlock && git status
```

---

## Best Practices

### Before Major Changes
```bash
# Sync current state to GitHub (creates backup)
./sync_to_github.sh
```

### After Completing Work Session
```bash
# Sync all systems with latest changes
./sync_to_github.sh
```

### Weekly Maintenance
```bash
# Check if token needs renewal (90-day expiration)
# Update if needed
./update_github_token.sh

# Full sync of all systems
./sync_to_github.sh
```

---

## Script Files

- `sync_to_github.sh` - Main synchronization script
- `update_github_token.sh` - GitHub token management
- `GITHUB_SYNC_GUIDE.md` - This guide

All scripts are located in: `/home/johnny5/Johny5Alive/`

---

**Last Updated:** 2025-09-30
