# J5A Server Setup Guide
**Split Architecture: Mac Mini (Squirt) + J5A Server (Night Shift/Sherlock)**

---

## Why This Architecture?

### Mac Mini (Johnny5-Macmini) - Business Operations
**Role:** Revenue-generating Squirt operations
- ✅ **Thermal Headroom:** No heavy AI workloads = stays cool
- ✅ **Business Priority:** LibreOffice always available (6am-7pm Mon-Fri)
- ✅ **Direct Access:** You're physically present for client work
- ✅ **Voice Processing:** Can still do voice memos when thermal allows

### J5A Server - Research Operations
**Role:** Night Shift autonomous intelligence analysis
- ✅ **No Thermal Limits:** Run heavy models 24/7
- ✅ **Parallel Development:** Claude Max runs while you work on Squirt
- ✅ **Dedicated Resources:** 100% CPU/RAM for Sherlock/Phoenix
- ✅ **Uninterrupted:** No client work interruptions

---

## Migration Steps

### On Mac Mini (Current Session)

**1. Stop Night Shift timer (prevent conflicts):**
```bash
sudo systemctl stop j5a-nightshift.timer
sudo systemctl disable j5a-nightshift.timer
```

**2. Run migration script:**
```bash
cd /home/johnny5/Johny5Alive
./migrate_to_j5a_server.sh j5a-server  # Replace with your server hostname/IP
```

**3. Transfer migration packages:**
```bash
# Packages will be in /tmp/j5a_migration/
cd /tmp/j5a_migration
scp *.tar.gz j5a-server:/tmp/
```

### On J5A Server

**1. Extract migration packages:**
```bash
cd /tmp
tar xzf sherlock_*.tar.gz -C /home/johnny5/
tar xzf nightshift_*.tar.gz -C /home/johnny5/Johny5Alive/
tar xzf config_*.tar.gz -C /home/johnny5/
tar xzf systemd_*.tar.gz
```

**2. Install systemd services:**
```bash
sudo cp systemd_services/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable j5a-nightshift.timer
sudo systemctl start j5a-nightshift.timer
```

**3. Install dependencies:**
```bash
# Ollama (for local LLM)
curl -fsSL https://ollama.com/install.sh | sh

# Python packages
pip3 install anthropic openai faster-whisper jsonschema

# Verify
ollama --version
python3 -c "import anthropic; print('Anthropic SDK ready')"
```

**4. Configure Anthropic API key:**
```bash
# Add to ~/.bashrc or ~/.profile:
export ANTHROPIC_API_KEY="your-key-here"

# Or create a systemd environment file:
sudo mkdir -p /etc/systemd/system/j5a-nightshift.service.d/
sudo tee /etc/systemd/system/j5a-nightshift.service.d/api-key.conf << EOF
[Service]
Environment="ANTHROPIC_API_KEY=your-key-here"
EOF
sudo systemctl daemon-reload
```

**5. Test Night Shift:**
```bash
# Check timer is active
systemctl status j5a-nightshift.timer

# Manually trigger (for testing)
sudo systemctl start j5a-nightshift.service

# Check logs
journalctl -u j5a-nightshift.service -f

# Verify morning review
cat /home/johnny5/Sherlock/morning_review.md
```

---

## Running Claude Max Sessions on J5A Server

### Option 1: SSH Session (Recommended for iteration)

**From Mac Mini:**
```bash
ssh j5a-server

# On J5A server, start Claude Code
cd /home/johnny5/Sherlock
claude-code  # Or however you invoke Claude Code

# In Claude Code session:
# 1. Read morning review
# 2. Approve queue: cd /home/johnny5/Johny5Alive/queue && python3 approve_claude_queue.py --approve-all
# 3. Start processing approved tasks
```

### Option 2: Tmux/Screen for Long-Running Sessions

**Start persistent session:**
```bash
ssh j5a-server
tmux new -s claude-max

# In tmux:
cd /home/johnny5/Sherlock
claude-code

# Detach: Ctrl+B, then D
# Reattach later: tmux attach -t claude-max
```

### Option 3: Automated Claude Max (Future)

```bash
# Schedule Claude Max to process approved queue at specific time
# (After Phase 4 implementation - hypothesis bin + feedback loop)
```

---

## Daily Workflow (After Migration)

### Morning (7am-9am)

**On J5A Server (via SSH):**
1. Read morning review:
   ```bash
   ssh j5a-server
   cat /home/johnny5/Sherlock/morning_review.md
   ```

2. Approve queue:
   ```bash
   cd /home/johnny5/Johny5Alive/queue
   python3 approve_claude_queue.py --summary
   python3 approve_claude_queue.py --approve-all
   ```

3. Start Claude Max session (optional):
   ```bash
   tmux new -s claude-max
   cd /home/johnny5/Sherlock
   claude-code
   # Work on approved queue, then detach
   ```

**On Mac Mini (Local):**
- Start Squirt work
- LibreOffice document generation
- Client communications

### During Day (9am-7pm)

**Mac Mini:** Focus on revenue operations
- Squirt voice processing (when thermal allows)
- LibreOffice manual work
- Client-facing tasks

**J5A Server:** Runs in background
- Claude Max processing approved tasks (if session active)
- Sherlock database updates
- No competition for resources with Squirt

### Evening (7pm onwards)

**J5A Server (automatic):**
- 19:03: Night Shift starts
  - Targeting Officer sweep (create/refresh packages)
  - Process nightshift queue
  - Generate morning review
- Throughout night: Claude Max can continue (if session active)

**Mac Mini:**
- Lower priority AI work (if desired)
- Or: Keep it free for personal Prism sessions

---

## Integration Map Compliance

### Business Hours (6am-7pm Mon-Fri)

| System | Machine | Priority | Notes |
|--------|---------|----------|-------|
| LibreOffice | Mac Mini | 1 | Revenue-critical |
| Squirt Manual | Mac Mini | 2 | Client work |
| Squirt Voice | Mac Mini | 3 | When thermal allows |
| Sherlock | **J5A Server** | 4 | Background only |
| J5A Queue | **J5A Server** | 5 | Scheduled off-hours |

### Off-Hours (7pm-6am + Weekends)

| System | Machine | Priority | Notes |
|--------|---------|----------|-------|
| Night Shift | **J5A Server** | 1 | Autonomous operation |
| Sherlock | **J5A Server** | 2 | Full resources available |
| Claude Max | **J5A Server** | 3 | Long-running sessions |
| Squirt (if needed) | Mac Mini | 4 | Available but lower priority |

---

## Monitoring Both Machines

### Check Night Shift Status (from Mac Mini)

```bash
# SSH to J5A server and check
ssh j5a-server 'systemctl status j5a-nightshift.timer'

# Or: Set up monitoring dashboard
# (Future enhancement)
```

### Thermal Monitoring

**Mac Mini (keep it cool):**
```bash
# Check temperature
sensors | grep "Package id 0"

# Should stay <75°C during business hours
```

**J5A Server (can run hot):**
```bash
ssh j5a-server 'sensors | grep "Package id 0"'

# Can safely run up to 85°C (higher thermal limit since no client work)
```

---

## Backup & Sync Considerations

### Shared Data (Sync Between Machines)

**J5A Universe Memory:**
```bash
# J5A server has authoritative copy
# Mac Mini can query via SSH if needed (future enhancement)

# For now: J5A server is source of truth for:
# - Sherlock evidence database
# - Phoenix validation data
# - Kaizen learning database
# - Entity memory
```

**Squirt Data:**
```bash
# Mac Mini has authoritative copy
# Keep Squirt operations entirely on Mac Mini
```

**Prism Reflections:**
```bash
# Mac Mini for direct sessions
# Optionally sync to J5A server for backup:
rsync -av /home/johnny5/Prism/ j5a-server:/home/johnny5/Prism/
```

---

## Advantages of This Setup

✅ **Thermal Safety:** Mac Mini no longer risks overheating from heavy AI work
✅ **Parallel Work:** You work on Squirt while Claude Max runs autonomously on J5A
✅ **Resource Isolation:** Client work never competes with research workloads
✅ **24/7 Operations:** J5A server can run Night Shift without affecting Squirt
✅ **Scalability:** Easy to upgrade J5A server resources without touching Squirt
✅ **Development Speed:** Rapid iterations on Sherlock don't impact production Squirt

---

## Next Steps After Migration

1. **Test Night Shift on J5A server** (wait for tonight's 19:03 run)
2. **Tomorrow morning:** Read morning review, approve queue
3. **Start Claude Max session** on J5A server for Sherlock work
4. **Continue Squirt development** on Mac Mini without conflicts
5. **Phase 4: Implement Hypothesis Bin** (on J5A server during Claude Max session)

---

**Migration script ready at:** `/home/johnny5/Johny5Alive/migrate_to_j5a_server.sh`

**Questions? Check:**
- Integration Map: `/home/johnny5/J5A_INTEGRATION_MAP.md`
- Constitution: `/home/johnny5/J5A_CONSTITUTION.md`
- Session Summary: `/home/johnny5/Johny5Alive/j5a-nightshift/ops/SESSION_SUMMARY_20251201.md`
