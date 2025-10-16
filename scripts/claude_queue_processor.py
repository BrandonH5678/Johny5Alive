#!/usr/bin/env python3
"""
Claude Queue Processor - Read and display Claude queue tasks

This script reads tasks from queue/claude/*.jsonl and prepares them
for processing by Claude Code. It does NOT execute the tasks - it only
displays them for Claude to read and process.

Claude Code should read this output and then:
1. Process each task according to its type (analysis/planning/code_authoring)
2. Write outputs to artifacts/claude/YYYY-MM-DD/
3. Update SUMMARY.md
4. Queue NightShift tasks if execution is needed
"""
import json
import sys
from pathlib import Path
from datetime import datetime

class ClaudeQueueReader:
    """Read and parse Claude queue tasks"""

    def __init__(self, queue_dir=None):
        """Initialize queue reader"""
        if queue_dir is None:
            root = Path(__file__).resolve().parents[1]
            queue_dir = root / "queue" / "claude"

        self.queue_dir = Path(queue_dir)

        if not self.queue_dir.exists():
            self.queue_dir.mkdir(parents=True, exist_ok=True)

    def read_tasks(self, limit=None):
        """
        Read tasks from queue files (newest first)

        Args:
            limit: Maximum number of tasks to read

        Returns:
            List of task dictionaries
        """
        tasks = []

        # Get all JSONL files, sorted by modification time (newest first)
        queue_files = sorted(
            self.queue_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for queue_file in queue_files:
            with open(queue_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        task = json.loads(line)
                        tasks.append({
                            **task,
                            "_source_file": str(queue_file),
                            "_line": line
                        })

                        if limit and len(tasks) >= limit:
                            return tasks
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Invalid JSON in {queue_file}: {e}", file=sys.stderr)
                        continue

        return tasks

    def display_tasks(self, tasks):
        """Display tasks in human-readable format"""
        if not tasks:
            print("📭 No tasks in Claude queue")
            return

        print(f"📬 {len(tasks)} task(s) in Claude queue")
        print()

        for i, task in enumerate(tasks, 1):
            print(f"{'='*80}")
            print(f"TASK {i}: {task.get('id', 'NO_ID')}")
            print(f"{'='*80}")
            print(f"Type: {task.get('type', 'UNKNOWN')}")
            print(f"Priority: {task.get('priority', 'normal')}")

            if task.get('inputs'):
                print(f"\nInputs:")
                for inp in task['inputs']:
                    print(f"  - {inp}")

            if task.get('deliverables'):
                print(f"\nDeliverables:")
                for deliv in task['deliverables']:
                    print(f"  - {deliv}")

            if task.get('constraints'):
                print(f"\nConstraints:")
                for key, val in task['constraints'].items():
                    print(f"  {key}: {val}")

            if task.get('notes'):
                print(f"\nNotes:")
                print(f"  {task['notes']}")

            print(f"\nSource: {task.get('_source_file')}")
            print()

    def format_for_claude(self, tasks):
        """Format tasks as JSON for Claude to parse"""
        # Remove internal metadata
        clean_tasks = []
        for task in tasks:
            clean = {k: v for k, v in task.items() if not k.startswith('_')}
            clean_tasks.append(clean)

        return json.dumps(clean_tasks, indent=2)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Read Claude queue tasks")
    parser.add_argument("--limit", type=int, help="Maximum number of tasks to read")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of human-readable")
    parser.add_argument("--queue-dir", help="Custom queue directory")

    args = parser.parse_args()

    reader = ClaudeQueueReader(queue_dir=args.queue_dir)
    tasks = reader.read_tasks(limit=args.limit)

    if args.json:
        print(reader.format_for_claude(tasks))
    else:
        reader.display_tasks(tasks)

        if tasks:
            print()
            print("💡 Next steps for Claude Code:")
            print("   1. Read input files specified in task.inputs")
            print("   2. Perform analysis/planning/code_authoring")
            print("   3. Write outputs to artifacts/claude/YYYY-MM-DD/")
            print("   4. Update artifacts/claude/YYYY-MM-DD/SUMMARY.md")
            print("   5. If execution needed, queue NightShift task:")
            print("      echo '{...}' >> queue/nightshift/inbox.jsonl")


if __name__ == "__main__":
    main()
