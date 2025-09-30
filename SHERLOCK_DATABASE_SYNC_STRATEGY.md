# Sherlock Database Sync Strategy

## Problem Statement

Sherlock contains 13GB of data, primarily:
- **Databases:** ~700KB (12 .db files with valuable intelligence)
- **Audio Files:** ~11GB (363 audio files, user-provided content)
- **Processing Artifacts:** ~2GB (transcripts, chunks, checkpoints)

**Goal:** Share code + databases with collaborators while excluding large audio files that users should provide themselves.

---

## Strategy: Git LFS + Selective Sync

### Architecture

```
GitHub Repositories:
├── Sherlock (Main Repo) - Code + Docs
├── Sherlock-Databases (LFS) - Intelligence databases (~700KB)
└── [Audio files NOT on GitHub] - Users provide their own

Collaborator Workflow:
1. Clone Sherlock repo (fast, ~50MB)
2. Download databases via Git LFS (automatic, ~700KB)
3. Provide own audio files or download separately
4. Run Sherlock with existing intelligence
```

### Benefits

✅ **Fast cloning** - ~50MB repo vs 13GB
✅ **Shared intelligence** - Databases contain all analysis work
✅ **User privacy** - No copyrighted audio on GitHub
✅ **Collaborative** - Multiple users contribute to same databases
✅ **GitHub-compatible** - Standard workflow, no special tools

---

## Implementation

### Phase 1: Current Setup (Completed)

**Files:**
- `.gitignore` - Excludes audio files, keeps databases
- `.gitattributes` - Configures Git LFS for *.db files

**What's excluded from GitHub:**
```
*.aaxc          # Audible encrypted audiobooks
*.aax           # Audible legacy format
*.m4a           # Audio files
*.mp3           # Audio files
*.wav           # Audio files
audiobooks/     # 2GB of audio content
chunks/         # Processing artifacts
checkpoints/    # Regenerable data
```

**What's included on GitHub:**
```
*.py            # All code
*.md            # All documentation
*.db            # All databases (via Git LFS)
*.json          # Configuration files
requirements.txt
```

### Phase 2: Git LFS Setup (Required)

**On the Mac Mini:**
```bash
# Install Git LFS
sudo apt-get install git-lfs

# Initialize Git LFS for Sherlock
cd /home/johnny5/Sherlock
git lfs install
git lfs track "*.db"
git add .gitattributes

# Verify LFS tracking
git lfs ls-files
```

**On GitHub:**
- Git LFS is included with all GitHub accounts
- Free tier: 1GB storage, 1GB bandwidth/month
- Sherlock databases (~700KB) well within limits

### Phase 3: Database Categories

**Production Databases (Include):**
- `evidence.db` (124KB) - Main evidence store
- `gladio_intelligence.db` (56KB) - Operation Gladio analysis
- `gladio_complete.db` (56KB) - Complete Gladio dataset
- `active_learning.db` (36KB) - Learning system state
- `audit.db` (68KB) - Audit trail
- `intelligence_sharing.db` (48KB) - Cross-system intelligence

**Test/Sample Databases (Include):**
- `demo_gladio_facts.db` (56KB) - Demo dataset
- `test_gladio.db` (56KB) - Test fixtures
- `validation_test.db` (56KB) - Validation data
- `gladio_sample.db` (68KB) - Sample for testing

---

## Collaborator Onboarding

### For ChatGPT or AI Collaborators

```
Sherlock Evidence Analysis System on GitHub:
- Repository: https://github.com/BrandonH5678/Sherlock
- Size: ~50MB (code + docs + databases via LFS)

To understand the codebase:
1. Review SHERLOCK_AI_OPERATOR_MANUAL.md for system overview
2. Check evidence.db schema for data model
3. Review voice_engine.py for audio processing
4. Check CLAUDE.md for design principles

Databases contain intelligence from:
- Operation Gladio: 17+ hour audiobook analysis
- Evidence cards: Atomic claims with provenance
- Active learning: Model improvement data
- Cross-system intelligence: Shared with J5A/Squirt
```

### For Human Collaborators

**Clone with databases:**
```bash
# Install Git LFS (one-time setup)
git lfs install

# Clone repository (downloads databases automatically)
git clone https://github.com/BrandonH5678/Sherlock.git
cd Sherlock

# Verify databases downloaded
ls -lh *.db

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ready to use existing intelligence!
```

**Provide your own audio:**
```bash
# Option 1: Your own AAXC audiobooks
mkdir -p audiobooks/your_book
# Place .aaxc and .voucher files there

# Option 2: Download specific Operation Gladio files (if shared separately)
# [Instructions for any separate large file distribution]
```

---

## Sync Automation

### Manual Sync (Current)
```bash
cd /home/johnny5/Johny5Alive
./sync_to_github.sh sherlock
```

### Automated Sync (J5A Overnight Job)

**Frequency:** Weekly (databases change infrequently)
**Trigger:** Sunday night 2am
**Duration:** ~5 minutes (only databases, ~700KB)

**J5A Task Definition:**
```python
J5AWorkAssignment(
    task_id="sherlock_db_sync_001",
    task_name="Weekly Sherlock database sync to GitHub",
    domain="system_maintenance",
    priority=Priority.LOW,

    expected_outputs=[
        "Sherlock databases pushed to GitHub",
        "Git commit with db changes",
        "Sync confirmation log"
    ],

    success_criteria={
        "databases_updated": True,
        "git_push_successful": True,
        "no_audio_files_pushed": True,
        "sync_time_under_10_minutes": True
    }
)
```

### Alternative: Database Export Strategy

If Git LFS causes issues, alternative approach:

**Periodic Database Snapshots:**
```bash
# Create database bundle (weekly)
cd /home/johnny5/Sherlock
tar -czf sherlock_databases_$(date +%Y%m%d).tar.gz *.db

# Upload to GitHub Releases (not main repo)
# File: ~1MB compressed
# Location: https://github.com/BrandonH5678/Sherlock/releases
# Collaborators download specific snapshot
```

---

## Data Sharing Ethics

### Audio Files (Excluded)

**Why NOT on GitHub:**
- Copyright concerns (Audible audiobooks)
- File size (100MB-1GB each)
- User-provided content
- Privacy considerations

**How collaborators get audio:**
- Provide their own audiobooks
- Download from legitimate sources
- Request specific public domain content

### Databases (Included)

**Why on GitHub:**
- Original analysis work (not copyrighted content)
- Small size (~700KB total)
- High value for collaborators
- Enables immediate productivity

**What's in databases:**
- Evidence cards (extracted claims, not raw audio)
- Entity relationships
- Analysis metadata
- Learning system state
- Cross-references and citations

---

## Maintenance

### Weekly Tasks (Automated by J5A)

1. **Check database sizes**
   ```bash
   du -sh /home/johnny5/Sherlock/*.db
   ```

2. **Verify .gitignore working**
   ```bash
   cd /home/johnny5/Sherlock
   git status | grep -E "\.aaxc|\.wav|\.m4a"
   # Should return nothing (all ignored)
   ```

3. **Sync databases**
   ```bash
   ./sync_to_github.sh sherlock
   ```

4. **Verify LFS tracking**
   ```bash
   git lfs ls-files | grep "\.db"
   # Should list all database files
   ```

### Monthly Tasks (Manual)

1. **Review database growth**
   - If any database >50MB, consider archival strategy
   - Audit old test databases for deletion

2. **Update collaborator documentation**
   - Add new databases to SHERLOCK_STATUS.md
   - Document new intelligence sources

3. **Check GitHub LFS bandwidth**
   - Free tier: 1GB/month
   - Monitor at: https://github.com/settings/billing

---

## Emergency Procedures

### If Sync Fails

```bash
# Check what's being staged
cd /home/johnny5/Sherlock
git status

# Check for large files
git ls-files --others --exclude-standard | while read f; do
    [ -f "$f" ] && [ $(stat -c%s "$f") -gt 10485760 ] && echo "$f"
done

# Reset if needed
git reset --hard HEAD
git clean -fd
```

### If Audio Files Accidentally Staged

```bash
# Remove from staging
git reset HEAD *.aaxc *.wav *.m4a

# Add to .gitignore (if not already there)
echo "*.aaxc" >> .gitignore
echo "*.wav" >> .gitignore
echo "*.m4a" >> .gitignore

git add .gitignore
git commit -m "Fix: Exclude audio files from git"
```

### If LFS Quota Exceeded

```bash
# Check LFS usage
git lfs ls-files | wc -l

# Option 1: Remove LFS tracking
git lfs untrack "*.db"
# Use database snapshot approach instead

# Option 2: GitHub Pro ($4/month)
# Increases LFS to 2GB storage, 50GB bandwidth
```

---

## Performance Metrics

### Current State (Before Optimization)
- **Total Directory:** 13GB
- **GitHub Target:** ~50MB (code only)
- **Database Payload:** ~700KB (12 files)

### After Implementation
- **Clone Time:** <1 minute (vs 20+ minutes for 13GB)
- **Database Download:** <5 seconds via LFS
- **Collaborator Onboarding:** <5 minutes total
- **Weekly Sync Time:** <5 minutes (databases only)

---

**Status:** Strategy designed, ready for implementation
**Next Steps:**
1. Install Git LFS on Mac Mini
2. Initialize LFS tracking in Sherlock
3. Create J5A overnight sync job
4. Test with trial push

**Created:** 2025-09-30
**Version:** 1.0
