# J5A Claude Code Configuration

## Overview

This directory contains Claude Code configuration for the J5A (Johny5Alive) project, including settings, custom commands, and hooks.

---

## Slash Commands

### Available Commands

The following slash commands are available in this project via symlinks to global command definitions:

- **`/context-refresh`** - Universal context refresh with full Tier 0-2 document loading and 9-question validation
- **`/micro-refresh`** - Default post-compaction refresh (Tier B: Constitutional + Integration)
- **`/micro-refresh-minimal`** - Tier A: Constitutional principles only (fastest)
- **`/micro-refresh-full`** - Tier D: Full Tier 0 reload (most comprehensive)
- **`/micro-refresh-prism`** - Tier C: Constitutional + Prism Consciousness + RRARR

### Command Location

**Local symlinks:** `/home/johnny5/Johny5Alive/.claude/commands/`
**Global definitions:** `/home/johnny5/.claude/commands/`

Commands are defined globally and symlinked into projects to maintain a single source of truth.

### Why SlashCommand Permissions Are Required

**Critical:** Claude Code requires explicit `SlashCommand(/command-name)` declarations in `settings.json` to recognize and make commands available.

Even if a command file exists in `.claude/commands/`, Claude Code will **hide** the command if no matching SlashCommand permission is declared.

**Configured in:** `.claude/settings.json` → `permissions.allow` array

**Current permissions:**
```json
"SlashCommand(/context-refresh)",
"SlashCommand(/micro-refresh)",
"SlashCommand(/micro-refresh-full)",
"SlashCommand(/micro-refresh-minimal)",
"SlashCommand(/micro-refresh-prism)"
```

---

## Adding New Shared Commands

To add a new shared command to this project:

### 1. Create Global Command Definition
```bash
# Create command file in global location
nano /home/johnny5/.claude/commands/my-new-command.md
```

**Format:**
```markdown
---
description: Brief description of what this command does
---

# Command Title

[Command implementation instructions for Claude]
```

### 2. Symlink to Project
```bash
cd /home/johnny5/Johny5Alive/.claude/commands/
ln -s /home/johnny5/.claude/commands/my-new-command.md my-new-command.md
```

### 3. Add SlashCommand Permission
Edit `.claude/settings.json` and add to `permissions.allow`:
```json
"SlashCommand(/my-new-command)"
```

### 4. Restart Claude Code (if needed)
Claude Code should auto-detect the new command. If not, restart the application.

---

## Configuration Files

### `settings.json`
**Purpose:** Project-level Claude Code settings

**Key sections:**
- **Permissions:** File access, Bash command patterns, SlashCommand declarations
- **Hooks:** Pre-autonomous validation requirements
- **Autonomy Config:** Scope declaration, snapshot requirements, validation gates

**When to edit:**
- Adding new permissions
- Configuring autonomous operation rules
- Adding slash commands

### `settings.local.json` (if present)
**Purpose:** Local overrides for user-specific settings

**When to edit:**
- User-specific permissions
- Local API keys or paths
- Development-specific overrides

**Note:** Local settings merge with project settings. Avoid duplicating SlashCommand declarations (use `settings.json` for shared commands).

---

## Hooks

### `preAutonomous` Hook
**Triggered:** Before any autonomous operation begins

**Requirements:**
- Pre-execution snapshot (Constitutional Principle 2: Transparency)
- Scope declaration (what will be modified)
- Max duration: 120 minutes

**Purpose:** Ensure autonomous operations respect J5A Constitution principles and maintain auditability.

---

## Troubleshooting

### Slash Commands Not Appearing

**Symptom:** Command exists in `.claude/commands/` but doesn't appear when typing `/`

**Causes and fixes:**

1. **Missing SlashCommand permission** (most common)
   - Check `settings.json` → `permissions.allow` array
   - Add `"SlashCommand(/command-name)"` if missing
   - Restart Claude Code

2. **Broken symlink**
   - Verify: `ls -la .claude/commands/`
   - Check target exists: `ls -la /home/johnny5/.claude/commands/`
   - Recreate symlink if broken

3. **File permissions**
   - Ensure command file is readable: `chmod 644 /home/johnny5/.claude/commands/command.md`

4. **Cache issue**
   - Restart Claude Code to clear command cache

### Recent Issue (Resolved 2025-12-04)

**Problem:** Symlinked commands stopped being recognized despite valid symlinks

**Root cause:** Missing SlashCommand permission declarations in `settings.json`

**Solution:** Added all SlashCommand declarations to `settings.json` (lines 23-27)

**Prevention:** Always add SlashCommand permissions when creating new shared commands

---

## Best Practices

### Command Definitions
- **Single source:** Define commands globally, symlink into projects
- **Documentation:** Include `description:` in frontmatter for command discovery
- **Versioning:** Consider versioning critical commands (e.g., `context-refresh-v2.md`)

### Permissions
- **Explicit is better:** Declare SlashCommand permissions explicitly in `settings.json`
- **Project-level:** Put shared commands in `settings.json`, not `settings.local.json`
- **Audit:** Review permissions quarterly (J5A Constitution: Principle 2 - Transparency)

### Maintenance
- **Test after updates:** After editing `settings.json`, test affected commands
- **Document changes:** Update this README when adding/removing commands
- **Sync verification:** Periodically verify symlinks point to current global definitions

---

## Related Documentation

- **J5A Constitution:** `/home/johnny5/Johny5Alive/J5A_CONSTITUTION.md`
- **Integration Map:** `/home/johnny5/Johny5Alive/J5A_INTEGRATION_MAP.md`
- **Context-Refresh Architecture:** `/home/johnny5/.claude/commands/context-refresh.md`
- **Claude Code Documentation:** `https://github.com/anthropics/claude-code`

---

**Last Updated:** 2025-12-04
**Maintained By:** J5A Operations Team (Human + AI collaboration)
