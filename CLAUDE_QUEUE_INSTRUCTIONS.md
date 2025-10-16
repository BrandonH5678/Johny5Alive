# Claude Queue Instructions

## Task Processing

Read all `queue/claude/*.jsonl` (newest first). Each line is a JSON task object.

### Task Schema

```json
{
  "id": "2025-10-11T18:00:12Z-anti-grav-brief",
  "type": "analysis|planning|code_authoring",
  "priority": "high|normal|low",
  "inputs": ["artifacts/nightshift/2025-10-11/sherlock/anti_gravity_packet.jsonl"],
  "deliverables": ["reports/anti_gravity_lit_review.md"],
  "constraints": {"max_tokens": 60000, "style": "concise", "citations": true},
  "notes": "Cross-reference packet entities with new web sources; propose data model changes."
}
```

### Required Fields
- `id`: Unique identifier (ISO timestamp + slug)
- `type`: Task type (analysis, planning, code_authoring)
- `deliverables`: Array of expected output file paths

### Optional Fields
- `inputs`: Source files/data (often from `artifacts/nightshift/`)
- `constraints`: Processing constraints (token limits, style requirements, etc.)
- `notes`: Additional context or special instructions
- `priority`: Task priority (defaults to "normal")

## Output Structure

### File Locations

All outputs go under: `artifacts/claude/YYYY-MM-DD/`

**Code patches:**
```
artifacts/claude/YYYY-MM-DD/patches/*.diff
```

**Analysis reports:**
```
artifacts/claude/YYYY-MM-DD/reports/*.md
```

**Task summary:**
```
artifacts/claude/YYYY-MM-DD/SUMMARY.md
```

### Summary Format

```markdown
# Claude Task Summary - YYYY-MM-DD

## Tasks Completed

### [Task ID]
- **Type**: analysis|planning|code_authoring
- **Status**: completed|partial|blocked
- **Deliverables**: List of generated files
- **Notes**: Key findings, decisions, follow-up items

## Hand-off to NightShift

Tasks queued in `queue/nightshift/inbox.jsonl`:
- [task_id]: Brief description
```

## Hand-off to NightShift

When a task requires execution (applying patches, running scripts, syncing repos), emit a new JSONL record:

```bash
echo '{"id":"2025-10-11T22:00:00Z-apply-patch","task":"repo_sync","args":{"manifest":"configs/repos.json"},"priority":"normal"}' >> queue/nightshift/inbox.jsonl
```

## Task Types

### Analysis
- Deep analysis of data, documents, code
- Cross-referencing sources
- Literature reviews
- Pattern identification

### Planning
- Architecture design
- Implementation roadmaps
- Strategic planning
- System design

### Code Authoring
- New feature implementation
- Refactoring existing code
- Bug fixes
- Script creation

## Safety Rules

1. **Never execute commands directly** - write patches/scripts for review
2. **Always validate inputs** - check file existence before processing
3. **Respect constraints** - honor token limits, style requirements
4. **Document decisions** - explain reasoning in SUMMARY.md
5. **Hand-off execution** - queue NightShift tasks for code application

## Example Workflow

1. Read task from `queue/claude/2025-10-11.jsonl`
2. Load inputs from `artifacts/nightshift/`
3. Perform analysis/planning/authoring
4. Write outputs to `artifacts/claude/2025-10-11/`
5. Update `SUMMARY.md`
6. If execution needed, queue NightShift task
