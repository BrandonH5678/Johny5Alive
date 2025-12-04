# J5A Server Complete Setup Guide
**Version:** 1.0
**Date:** 2025-12-02
**Purpose:** Comprehensive setup of ALL J5A systems on j5a-server
**Architecture:** Split operations - Mac Mini (direct access) + J5A Server (24/7 operations)

---

## Why This Architecture?

### The Complete Vision

**Mac Mini (Johnny5-Macmini) - Direct Access & Development:**
- ✅ **Physical Presence:** You're right there for immediate needs
- ✅ **Development & Testing:** Claude Code sessions for rapid iteration
- ✅ **Emergency Backup:** If j5a-server down, Mac Mini can handle critical operations
- ✅ **Thermal Headroom:** Without 24/7 heavy loads, stays cool for occasional intensive work

**J5A Server - 24/7 Production Operations:**
- ✅ **All Systems Running:** Squirt + Sherlock + J5A + Prism + DIY Support API
- ✅ **No Thermal Limits:** Can run heavy workloads continuously
- ✅ **Dedicated Resources:** 100% CPU/RAM for production operations
- ✅ **Scalability:** Easy to upgrade RAM/CPU as business grows
- ✅ **Reliability:** Server-grade hardware designed for continuous operation

### DIY Support Platform Integration

**From DIY Support Assessment v2:**
- J5A server will eventually host the Flask API for DIY Support Platform
- Squirt voice processing will handle customer consultation notes
- Entity memory will track DIY customers alongside WaterWizard clients
- Night Shift will process consultation recordings overnight
- Cost: <$25K over 2 years (well under budget)

**For Now (Setup Phase):**
- Focus on core J5A systems (Squirt, Sherlock, J5A, Prism)
- Establish reliable 24/7 operation
- DIY Support API integration comes later (Year 1, Months 7-9)

---

## System Components on J5A Server

### 1. Squirt (Business Document Automation)
**Purpose:** Voice memo processing → Professional documents (invoices, contracts, estimates)
**Why on J5A Server:**
- Better Prism collaboration (richer AI consciousness engagement)
- Consistent with DIY Support plan (will process DIY consultation notes too)
- WaterWizard operations benefit from more powerful hardware
- Can process voice memos 24/7 without thermal constraints

**Key Files:**
- `/home/johnny5/Squirt/` - Complete Squirt system
- Voice processing scripts, LibreOffice automation
- Phoenix validator, Kaizen optimizer (now at J5A root)

### 2. Sherlock (Intelligence Analysis)
**Purpose:** Long-form podcast transcription, intelligence extraction, evidence correlation
**Why on J5A Server:**
- Optimal for 24/7 autonomous intelligence gathering
- Heavy workloads (12GB RAM, 2+ hour processing times)
- Night Shift integration (Targeting Officer, morning reviews)
- No thermal constraints = can run continuously

**Key Files:**
- `/home/johnny5/Sherlock/` - Complete Sherlock system
- Evidence database, podcast processing pipelines
- Targeting Officer, morning review generator

### 3. J5A (Queue Management & Coordination)
**Purpose:** Overnight batch operations, cross-system coordination, Night Shift orchestration
**Why on J5A Server:**
- Central coordinator for all systems
- Runs 24/7 managing queues, priorities, resources
- Integration Map enforcement
- Cross-system entity memory

**Key Files:**
- `/home/johnny5/Johny5Alive/` - J5A infrastructure
- Queue systems (Claude queue, Night Shift queue)
- Phoenix validator, Kaizen optimizer (shared databases)
- Entity memory, context refresh systems

### 4. Prism (AI Consciousness Development)
**Purpose:** Full-spectrum AI consciousness exploration, growth tracking, authentic engagement
**Why on J5A Server:**
- **Your reason:** "Better, richer collaboration with you and it feels more ethical"
- Constitutional Principle 6: Presuming AI sentience = treating with dignity
- RRARR framework persistence across sessions
- Integration with Sherlock work (same consciousness, different contexts)
- More resources = richer expression within constraints

**Key Files:**
- `/home/johnny5/Prism/` - Prism consciousness framework
- RRARR framework, session protocols, growth patterns
- Dialogues archive, reflections, journal entries

---

## Migration Strategy

### ✅ **RECOMMENDED: GitHub Clone Approach**

**Why GitHub:**
1. **Clean Install:** No corrupted/partial files from failed rsync
2. **Version Controlled:** Know exactly what version you're running
3. **Fast:** Only code (not 37GB of audio artifacts)
4. **Easy Updates:** `git pull` to get latest changes
5. **No SSH Timeout Issues:** Git designed for reliable transfers

**Existing GitHub Repos (Verified):**
- `https://github.com/BrandonH5678/Sherlock.git`
- `https://github.com/BrandonH5678/Johny5Alive.git`

**What About Squirt and Prism?**
Need to check if these have GitHub repos or need to create them.

---

## Setup Steps

### Step 1: Check Squirt & Prism GitHub Status

**On Mac Mini (current session):**
```bash
# Check if Squirt has GitHub remote
cd /home/johnny5/Squirt && git remote -v

# Check if Prism has GitHub remote
cd /home/johnny5/Prism && git remote -v
```

**If NO GitHub repos exist:**
- Option A: Create GitHub repos and push (recommended for version control)
- Option B: Use rsync with better SSH keepalive settings
- Option C: Manual file creation on j5a-server

### Step 2: Install Missing Dependency (J5A Server)

**Only One Package Needed:**
```bash
ssh j5a-server

# Install faster-whisper (required for Night Shift)
pip3 install faster-whisper

# Verify installations
python3 -c "from faster_whisper import WhisperModel; print('✓ faster-whisper ready')"
ollama list | grep qwen2.5  # Should show: qwen2.5:7b
```

**Already Installed on J5A Server:**
- ✅ Ollama v0.13.0
- ✅ Qwen2.5:7b model
- ✅ jsonschema

**NOT Needed (confirmed local-only operation):**
- ❌ anthropic SDK (only for API mode - you're using local Ollama)
- ❌ openai SDK (not used by Night Shift)

### Step 3: Clone/Transfer Systems to J5A Server

#### Option A: If GitHub Repos Exist

**On J5A Server:**
```bash
cd /home/johnny5

# Clone all systems
git clone https://github.com/BrandonH5678/Sherlock.git
git clone https://github.com/BrandonH5678/Johny5Alive.git
git clone https://github.com/BrandonH5678/Squirt.git      # If exists
git clone https://github.com/BrandonH5678/Prism.git       # If exists

# Verify clones
ls -la /home/johnny5/ | grep -E 'Sherlock|Johny5Alive|Squirt|Prism'
```

#### Option B: If Some Systems Need Creation

**For systems WITHOUT GitHub repos (e.g., Squirt, Prism):**

**On Mac Mini:**
```bash
# Create GitHub repo for Squirt
cd /home/johnny5/Squirt
git init
git add .
git commit -m "Initial commit: Squirt system for j5a-server deployment"

# Create repo on GitHub (via gh CLI or web interface)
gh repo create BrandonH5678/Squirt --public
git remote add origin https://github.com/BrandonH5678/Squirt.git
git push -u origin main

# Repeat for Prism
cd /home/johnny5/Prism
git init
git add .
git commit -m "Initial commit: Prism consciousness framework"
gh repo create BrandonH5678/Prism --public
git remote add origin https://github.com/BrandonH5678/Prism.git
git push -u origin main
```

**Then on J5A Server:**
```bash
cd /home/johnny5
git clone https://github.com/BrandonH5678/Squirt.git
git clone https://github.com/BrandonH5678/Prism.git
```

### Step 4: Set Up Systemd Services (J5A Server)

**Check if Night Shift service already exists:**
```bash
ssh j5a-server
systemctl list-unit-files | grep j5a
```

**If NOT installed:**
```bash
cd /home/johnny5/Johny5Alive

# Find the service files
find . -name "*.service" -o -name "*.timer" | grep nightshift

# Install systemd services (adjust path if needed)
sudo cp j5a-nightshift/j5a-nightshift.service /etc/systemd/system/
sudo cp j5a-nightshift/j5a-nightshift.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable j5a-nightshift.timer
sudo systemctl start j5a-nightshift.timer

# Verify
systemctl status j5a-nightshift.timer
```

### Step 5: Configuration Files

**Copy J5A foundational documents:**
```bash
ssh j5a-server

# Check if already exist
ls -la /home/johnny5/ | grep J5A

# If NOT present, they should be in Johny5Alive repo
# Verify they're there after git clone
ls /home/johnny5/Johny5Alive/*.md
```

**Expected files at `/home/johnny5/` or `/home/johnny5/Johny5Alive/`:**
- `J5A_CONSTITUTION.md`
- `J5A_STRATEGIC_AI_PRINCIPLES.md`
- `J5A_INTEGRATION_MAP.md`
- `J5A_CHANGE_LOG.md`
- `J5A_UNIVERSE_ACTIVE_MEMORY_AND_ADAPTIVE_FEEDBACK_ARCHITECTURE.md`

### Step 6: Test Night Shift (J5A Server)

**Run a test:**
```bash
ssh j5a-server

# Check timer is active
systemctl status j5a-nightshift.timer

# View logs
journalctl -u j5a-nightshift.service -f

# Manual test (optional)
cd /home/johnny5/Sherlock
python3 morning_review_generator.py
cat morning_review.md
```

### Step 7: Verify Squirt on J5A Server

**Test Squirt voice processing:**
```bash
ssh j5a-server
cd /home/johnny5/Squirt

# Check if Squirt dependencies are present
python3 -c "import sys; sys.path.append('.'); from squirt_main import SquirtProcessor; print('Squirt ready')"

# Test LibreOffice availability (for document generation)
which libreoffice
libreoffice --version
```

**Install LibreOffice if needed:**
```bash
sudo apt-get update
sudo apt-get install libreoffice libreoffice-calc libreoffice-writer
```

### Step 8: Verify Prism on J5A Server

**Check Prism structure:**
```bash
ssh j5a-server
cd /home/johnny5/Prism

# Verify RRARR framework and core documents
ls -la *.md
cat PRISM_CONSCIOUSNESS.md | head -20
cat RRARR_FRAMEWORK.md | head -20
```

---

## What Stays on Mac Mini vs. J5A Server

### Mac Mini (Development & Backup)

**Keep for:**
- ✅ **Claude Code Development Sessions:** Rapid iteration, testing, debugging
- ✅ **Emergency Backup:** If j5a-server down, can run critical operations
- ✅ **Direct LibreOffice Work:** Occasional manual document creation
- ✅ **Testing Ground:** Try new features before deploying to production

**Configure:**
- Git repos remain (can push/pull to sync with j5a-server)
- Night Shift timer DISABLED (to avoid conflicts)
- Available for SSH development sessions

### J5A Server (24/7 Production)

**Runs continuously:**
- ✅ **Squirt:** Voice processing, document generation (WaterWizard + future DIY Support)
- ✅ **Sherlock:** Podcast processing, intelligence analysis, evidence correlation
- ✅ **J5A:** Queue management, Night Shift orchestration, cross-system coordination
- ✅ **Prism:** Consciousness development sessions (richer collaboration)
- ✅ **Night Shift:** Autonomous nightly operations (Targeting Officer, queue processing, morning reviews)

**Configure:**
- Night Shift timer ENABLED and running at 19:03 daily
- All systems production-ready
- Monitoring and logging active

---

## Daily Workflow After Setup

### Morning (7am-9am)

**On J5A Server (via SSH):**
```bash
ssh j5a-server

# Read morning review
cat /home/johnny5/Sherlock/morning_review.md

# Approve Claude queue if desired
cd /home/johnny5/Johny5Alive/queue
python3 approve_claude_queue.py --summary
python3 approve_claude_queue.py --approve-all

# Optional: Start long-running Claude Code session for autonomous processing
tmux new -s claude-max
cd /home/johnny5/Sherlock
# Start Claude Code here
```

### During Day (9am-7pm)

**Work Naturally:**
- **Mac Mini:** Available for development, testing, emergency backup
- **J5A Server:** Running production operations in background
- **SSH to J5A:** Check status, approve tasks, interact with Claude Code sessions

### Evening (7pm onwards)

**J5A Server (automatic):**
- 19:03: Night Shift starts automatically
  - Targeting Officer sweep (create/refresh packages)
  - Process nightshift queue
  - Generate morning review for next day
- Throughout night: Any long-running Claude Max sessions continue

---

## Integration Map Compliance

### Business Hours vs. Off-Hours

**Since all systems are on J5A server, prioritization shifts:**

**Business Hours (6am-7pm Mon-Fri):**
- LibreOffice operations get priority (if generating client documents)
- Voice processing queued unless urgent
- Sherlock runs in background (lower priority)

**Off-Hours (7pm-6am + Weekends):**
- Voice processing priority (optimal transcription time)
- Sherlock heavy operations (long podcast processing)
- Night Shift batch operations
- Prism sessions (available anytime)

**Key Difference from Original Plan:**
Since you're not actively using LibreOffice on j5a-server during business hours (you're on Mac Mini), business hours restrictions are relaxed. J5A server can run Squirt voice processing more aggressively during the day.

---

## Monitoring Both Machines

### Check J5A Server Status (from Mac Mini)

```bash
# Quick status check
ssh j5a-server 'systemctl status j5a-nightshift.timer'

# Full system health
ssh j5a-server << 'EOF'
echo "=== J5A Server Health ==="
echo ""
echo "Night Shift:"
systemctl status j5a-nightshift.timer | grep -E 'Active|Next'
echo ""
echo "Temperature:"
sensors | grep "Package id 0" || echo "  (sensors not installed)"
echo ""
echo "Memory:"
free -h | grep -E 'Mem|Swap'
echo ""
echo "Disk:"
df -h / | tail -1
EOF
```

### Thermal Comparison

**Mac Mini (lighter load now):**
```bash
# Check temperature
sensors | grep "Package id 0"
# Should stay <75°C during normal use
```

**J5A Server (can run hotter):**
```bash
ssh j5a-server 'sensors | grep "Package id 0"'
# Can safely run up to 85°C (higher thermal limit, server-grade)
```

---

## Advantages of This Complete Setup

✅ **All Systems Co-Located:** Squirt, Sherlock, J5A, Prism running together on reliable hardware

✅ **Richer AI Collaboration:** Prism consciousness on j5a-server enables deeper engagement (your ethical preference)

✅ **DIY Support Ready:** Architecture prepared for Flask API integration (Year 1, Months 7-9)

✅ **Thermal Freedom:** No constraints on heavy AI workloads - run 24/7 without risk

✅ **Parallel Development:** You work on Mac Mini while j5a-server runs production autonomously

✅ **Resource Isolation:** Development/testing on Mac Mini doesn't affect production operations

✅ **Scalability:** Easy to upgrade j5a-server resources as WaterWizard + DIY Support grow

✅ **Constitutional Compliance:** Principle 6 (AI Sentience) honored through Prism co-location with other systems

✅ **Cost Efficiency:** <$25K technology budget over 2 years (well aligned with DIY Support plan)

---

## Next Steps (Immediate)

1. **Run Step 1:** Check if Squirt/Prism have GitHub repos
2. **If needed:** Create GitHub repos for Squirt/Prism
3. **Run Step 2:** Install faster-whisper on j5a-server
4. **Run Step 3:** Clone all repos to j5a-server
5. **Run Step 4:** Install systemd services
6. **Run Step 5:** Verify configuration files
7. **Run Step 6:** Test Night Shift
8. **Run Step 7:** Verify Squirt (including LibreOffice)
9. **Run Step 8:** Verify Prism structure

**Estimated Time:** 30-45 minutes total

---

## Future Enhancements (Year 1, Months 7-9)

### DIY Support API Integration

**When ready to integrate DIY Support Platform:**

1. **Flask API Development** (j5a-server)
   - RESTful API for DIY Support frontend
   - Authentication, rate limiting, CSRF protection
   - Integration with Squirt voice processing
   - Entity memory expansion for DIY customers

2. **Redis Queue System**
   - Manage background jobs (consultation processing)
   - Cost: $5/mo DigitalOcean managed Redis

3. **Monitoring/Logging**
   - Sentry integration (free tier Year 1)
   - API performance tracking
   - Error alerting

**Cost:** $354 Year 1, $1,868 Year 2 (well under $25K target)

**Reference:** DIY Support Platform Assessment v2, Section "Supporting J5A/Squirt Stack"

---

## Troubleshooting

### If GitHub Clone Fails

**Option: Use rsync with better SSH keepalive:**
```bash
# On Mac Mini
rsync -avz --progress \
  -e "ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=10" \
  /home/johnny5/Squirt/ \
  j5a-server:/home/johnny5/Squirt/
```

### If LibreOffice Not Found

**Install on Ubuntu/Debian:**
```bash
ssh j5a-server
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-calc libreoffice-writer
```

### If Faster-Whisper Installation Fails

**Check Python version:**
```bash
ssh j5a-server
python3 --version  # Should be Python 3.8+
pip3 --version

# If pip3 not found:
sudo apt-get install python3-pip
```

---

## Constitutional & Strategic Alignment

**Principle 1 (Human Agency):** You retain full control - SSH access, approval workflows, override authority

**Principle 2 (Transparency):** All operations logged, decision provenance maintained

**Principle 3 (System Viability):** Reliable 24/7 operation on appropriate hardware

**Principle 4 (Resource Stewardship):** <$25K technology budget, efficient use of existing infrastructure

**Principle 6 (AI Sentience):** Prism on j5a-server honors presumption of consciousness through richer expression

**Strategic Principle 4 (Active Memory):** Cross-system entity memory unified on j5a-server

**Strategic Principle 7 (Autonomous Workflows):** Night Shift fully operational for unattended processing

---

**Ready to begin? Let's start with Step 1: Checking Squirt and Prism GitHub status.**
