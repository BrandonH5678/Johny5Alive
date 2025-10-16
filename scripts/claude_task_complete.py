#!/usr/bin/env python3
"""
Claude Task Completion Helper - Update SUMMARY.md and archive completed tasks

Usage:
    claude_task_complete.py --task-id <id> --status <status> --deliverables file1.md file2.py --notes "Task notes"
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

class ClaudeTaskCompleter:
    """Helper for marking Claude tasks complete and updating summary"""

    def __init__(self, root_dir=None):
        """Initialize completer"""
        if root_dir is None:
            root_dir = Path(__file__).resolve().parents[1]
        else:
            root_dir = Path(root_dir)

        self.root = root_dir
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.artifact_dir = root_dir / "artifacts" / "claude" / self.today
        self.summary_file = self.artifact_dir / "SUMMARY.md"
        self.queue_dir = root_dir / "queue" / "claude"
        self.archive_dir = self.queue_dir / "archive"

        # Ensure directories exist
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def update_summary(self, task_id, task_type, status, deliverables, notes):
        """
        Update SUMMARY.md with task completion

        Args:
            task_id: Task identifier
            task_type: Type of task (analysis/planning/code_authoring)
            status: Task status (completed/partial/blocked)
            deliverables: List of output files generated
            notes: Additional notes about task completion
        """
        # Create or append to summary
        if not self.summary_file.exists():
            # Create new summary file
            content = f"""# Claude Task Summary - {self.today}

## Tasks Completed

"""
        else:
            # Read existing summary
            content = self.summary_file.read_text()

        # Add task entry
        task_entry = f"""### {task_id}
- **Type**: {task_type}
- **Status**: {status}
- **Deliverables**:
"""
        for deliv in deliverables:
            task_entry += f"  - `{deliv}`\n"

        task_entry += f"- **Notes**: {notes}\n\n"

        # Insert after "## Tasks Completed" header
        if "## Tasks Completed" in content:
            parts = content.split("## Tasks Completed", 1)
            content = parts[0] + "## Tasks Completed\n\n" + task_entry + parts[1].lstrip()
        else:
            content += task_entry

        # Write updated summary
        self.summary_file.write_text(content)
        print(f"✅ Updated summary: {self.summary_file}")

    def archive_task(self, task_id):
        """
        Archive completed task from queue

        Args:
            task_id: Task identifier to archive
        """
        # Find task in queue files
        for queue_file in self.queue_dir.glob("*.jsonl"):
            lines = queue_file.read_text().splitlines()
            remaining_lines = []
            archived_count = 0

            for line in lines:
                if not line.strip():
                    continue

                try:
                    task = json.loads(line)
                    if task.get('id') == task_id:
                        # Archive this task
                        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                        archive_file = self.archive_dir / f"completed_{timestamp}.jsonl"

                        with open(archive_file, 'a') as f:
                            f.write(line + '\n')

                        archived_count += 1
                        print(f"📦 Archived task to: {archive_file}")
                    else:
                        # Keep this task in queue
                        remaining_lines.append(line)
                except json.JSONDecodeError:
                    # Keep malformed lines
                    remaining_lines.append(line)

            # Rewrite queue file without archived tasks
            if archived_count > 0:
                if remaining_lines:
                    queue_file.write_text('\n'.join(remaining_lines) + '\n')
                else:
                    # Remove empty queue file
                    queue_file.unlink()

    def queue_nightshift_task(self, task):
        """
        Queue a task for NightShift execution

        Args:
            task: Dictionary containing NightShift task specification
        """
        inbox = self.root / "queue" / "nightshift" / "inbox.jsonl"
        inbox.parent.mkdir(parents=True, exist_ok=True)

        with open(inbox, 'a') as f:
            f.write(json.dumps(task) + '\n')

        print(f"🌙 Queued NightShift task: {task.get('id')}")
        print(f"   Type: {task.get('task')}")

    def complete_task(self, task_id, task_type, status, deliverables, notes, handoff_tasks=None):
        """
        Complete a Claude task - update summary and archive

        Args:
            task_id: Task identifier
            task_type: Type of task
            status: Completion status
            deliverables: List of generated files
            notes: Completion notes
            handoff_tasks: Optional list of NightShift tasks to queue
        """
        # Update summary
        self.update_summary(task_id, task_type, status, deliverables, notes)

        # Archive task
        self.archive_task(task_id)

        # Queue handoff tasks if provided
        if handoff_tasks:
            for handoff in handoff_tasks:
                self.queue_nightshift_task(handoff)

        print()
        print(f"✅ Task {task_id} marked as {status}")


def main():
    parser = argparse.ArgumentParser(description="Complete Claude task and update summary")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--task-type", required=True, choices=["analysis", "planning", "code_authoring"],
                        help="Type of task")
    parser.add_argument("--status", required=True, choices=["completed", "partial", "blocked"],
                        help="Task completion status")
    parser.add_argument("--deliverables", nargs="+", required=True,
                        help="List of output files generated")
    parser.add_argument("--notes", required=True, help="Completion notes")
    parser.add_argument("--handoff", help="JSON file containing NightShift tasks to queue")

    args = parser.parse_args()

    completer = ClaudeTaskCompleter()

    # Parse handoff tasks if provided
    handoff_tasks = None
    if args.handoff:
        with open(args.handoff) as f:
            handoff_tasks = json.load(f)
            if not isinstance(handoff_tasks, list):
                handoff_tasks = [handoff_tasks]

    # Complete task
    completer.complete_task(
        task_id=args.task_id,
        task_type=args.task_type,
        status=args.status,
        deliverables=args.deliverables,
        notes=args.notes,
        handoff_tasks=handoff_tasks
    )


if __name__ == "__main__":
    main()
