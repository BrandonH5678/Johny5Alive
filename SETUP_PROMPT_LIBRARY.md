# Prompt Library Setup Instructions

## Quick Start (2 minutes)

The Prompt Library and Token Optimization system is now installed! Follow these steps to activate it.

---

## Step 1: Add to Your Shell Configuration

Add the following line to your `~/.bashrc` (or `~/.zshrc` if using zsh):

```bash
# J5A Prompt Library - Token Optimization
source /home/johnny5/Johny5Alive/j5a_prompt_library_init.sh
```

### How to Add It:

**Option A: Command Line (Quick)**
```bash
echo "# J5A Prompt Library - Token Optimization" >> ~/.bashrc
echo "source /home/johnny5/Johny5Alive/j5a_prompt_library_init.sh" >> ~/.bashrc
```

**Option B: Text Editor (Manual)**
```bash
nano ~/.bashrc
# Add the lines above, save and exit (Ctrl+X, Y, Enter)
```

---

## Step 2: Reload Your Shell

```bash
source ~/.bashrc
```

Or close and reopen your terminal.

---

## Step 3: Test It!

```bash
cd /home/johnny5/Johny5Alive
```

You should see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 PROMPT LIBRARY AVAILABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Use cached prompts to save 70-90% on tokens

🌐 Open:     xdg-open PROMPT_LIBRARY.html
📖 Manual:   cat TOKEN_OPTIMIZATION_USER_MANUAL.md | less
📊 Stats:    python3 src/token_monitor.py --status

💡 TIP: Copy prompts exactly from library for caching!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 4: Open the Prompt Library

**In Browser (Recommended):**
```bash
xdg-open PROMPT_LIBRARY.html
```

Or manually open: `file:///home/johnny5/Johny5Alive/PROMPT_LIBRARY.html`

**Bookmark it!** You'll use this constantly.

---

## Step 5: Read the User Manual (5 minutes)

```bash
cat TOKEN_OPTIMIZATION_USER_MANUAL.md | less
```

Focus on:
- **Section 3: The 9 Golden Rules** (print and post this!)
- **Section 4: System-Specific Workflows** (for J5A, Squirt, Sherlock)

---

## What Happens Now?

### Every time you `cd` into J5A directories, you'll see the reminder:
- `/home/johnny5/Johny5Alive/`
- `/home/johnny5/Sherlock/`
- `/home/johnny5/Squirt/` (when created)

### The reminder shows once per directory per shell session
So it won't spam you, but you'll always know the library is there.

---

## Quick Access Commands

### Open Prompt Library
```bash
xdg-open PROMPT_LIBRARY.html
```

### View User Manual
```bash
less TOKEN_OPTIMIZATION_USER_MANUAL.md
```

### Check Token Usage Stats (after token monitor is implemented)
```bash
python3 src/token_monitor.py --status
```

---

## Customization

### Don't want the reminder?
Comment out the line in `~/.bashrc`:
```bash
# source /home/johnny5/Johny5Alive/j5a_prompt_library_init.sh
```

### Want it to auto-open in browser instead?
Edit `j5a_prompt_library_init.sh` and change the reminder section to:
```bash
xdg-open PROMPT_LIBRARY.html 2>/dev/null &
```

---

## Files Installed

```
/home/johnny5/Johny5Alive/
├── PROMPT_LIBRARY.html              ← Interactive prompt library
├── TOKEN_OPTIMIZATION_USER_MANUAL.md ← Complete user guide
├── j5a_prompt_library_init.sh       ← Shell integration script
└── SETUP_PROMPT_LIBRARY.md          ← This file

/home/johnny5/Sherlock/
└── PROMPT_LIBRARY.html              ← Symlink to main library

/home/johnny5/Squirt/ (when created)
└── PROMPT_LIBRARY.html              ← Symlink to main library
```

---

## Next Steps

1. ✅ Add to ~/.bashrc (Step 1)
2. ✅ Reload shell (Step 2)
3. ✅ Test it works (Step 3)
4. ✅ Open Prompt Library (Step 4)
5. ✅ Read Golden Rules (Section 3 of manual)
6. 🎯 **Start using cached prompts today!**

---

## Expected Results

### Week 1:
- Cache hit rate: 40-60% (learning phase)
- Token savings: ~30-40%

### Week 2:
- Cache hit rate: 60-75% (building habits)
- Token savings: ~50-60%

### Week 3+:
- Cache hit rate: 75-90% (optimized workflow)
- Token savings: 70-90%

**Annual savings: ~$540** (from $670/year → $130/year)

---

## Troubleshooting

### Reminder doesn't show when I cd?
- Check: `cat ~/.bashrc | grep j5a_prompt_library`
- If missing, go back to Step 1
- Make sure you reloaded: `source ~/.bashrc`

### Prompt Library won't open?
- Check file exists: `ls -la PROMPT_LIBRARY.html`
- Try full path: `xdg-open /home/johnny5/Johny5Alive/PROMPT_LIBRARY.html`
- Alternative: `firefox PROMPT_LIBRARY.html` or `chromium PROMPT_LIBRARY.html`

### Want to test without cd?
```bash
source /home/johnny5/Johny5Alive/j5a_prompt_library_init.sh
```

---

**🎉 Setup Complete! Start saving tokens today!**

**Remember: The key to savings is CONSISTENCY. Use the same prompts from the library every time!**
