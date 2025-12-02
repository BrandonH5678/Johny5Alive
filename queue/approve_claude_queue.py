#!/usr/bin/env python3
"""
Claude Queue Approval CLI
Allows human to approve/reject Claude Max tasks

Constitutional Principle 1: Human Agency
All significant autonomous operations require explicit human approval
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class ClaudeQueueApprover:
    """Manage approval workflow for Claude queue tasks"""

    def __init__(self, queue_dir: str = "/home/johnny5/Johny5Alive/queue/claude"):
        self.queue_dir = Path(queue_dir)
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.queue_file = self.queue_dir / f"{self.today}.jsonl"

    def load_queue(self) -> List[Dict]:
        """Load all tasks from today's queue"""
        if not self.queue_file.exists():
            return []

        tasks = []
        with open(self.queue_file) as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))

        return tasks

    def save_queue(self, tasks: List[Dict]):
        """Save tasks back to queue file"""
        with open(self.queue_file, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')

    def get_pending_summary(self) -> Dict[str, Any]:
        """Get summary of pending tasks grouped by category"""
        tasks = self.load_queue()

        summary = {
            'total_pending': 0,
            'by_category': {},
            'total_estimated_hours': 0,
            'tasks': []
        }

        for task in tasks:
            status = task.get('approval_status', 'pending')
            if status == 'pending':
                summary['total_pending'] += 1

                category = task.get('type') or task.get('category', 'unknown')
                if category not in summary['by_category']:
                    summary['by_category'][category] = {
                        'count': 0,
                        'estimated_hours': 0,
                        'task_ids': []
                    }

                summary['by_category'][category]['count'] += 1
                summary['by_category'][category]['task_ids'].append(task['id'])

                # Add estimated duration
                duration = task.get('estimated_duration_hours', 0.5)
                summary['by_category'][category]['estimated_hours'] += duration
                summary['total_estimated_hours'] += duration

                summary['tasks'].append(task)

        return summary

    def approve_category(self, category: str, approved_by: str = "human") -> int:
        """
        Approve all tasks in a category

        Args:
            category: Task category to approve
            approved_by: Username approving the tasks

        Returns:
            Number of tasks approved
        """
        tasks = self.load_queue()
        approved_count = 0

        for task in tasks:
            task_category = task.get('type') or task.get('category', 'unknown')
            status = task.get('approval_status', 'pending')

            if task_category == category and status == 'pending':
                task['approval_status'] = 'approved'
                task['approval_timestamp'] = datetime.now().isoformat()
                task['approved_by'] = approved_by
                approved_count += 1

        if approved_count > 0:
            self.save_queue(tasks)

        return approved_count

    def approve_all(self, approved_by: str = "human") -> int:
        """
        Approve all pending tasks

        Args:
            approved_by: Username approving the tasks

        Returns:
            Number of tasks approved
        """
        tasks = self.load_queue()
        approved_count = 0

        for task in tasks:
            status = task.get('approval_status', 'pending')

            if status == 'pending':
                task['approval_status'] = 'approved'
                task['approval_timestamp'] = datetime.now().isoformat()
                task['approved_by'] = approved_by
                approved_count += 1

        if approved_count > 0:
            self.save_queue(tasks)

        return approved_count

    def reject_task(self, task_id: str, reason: str = "") -> bool:
        """
        Reject a specific task

        Args:
            task_id: Task ID to reject
            reason: Optional rejection reason

        Returns:
            True if task was found and rejected
        """
        tasks = self.load_queue()

        for task in tasks:
            if task['id'] == task_id:
                task['approval_status'] = 'rejected'
                task['approval_timestamp'] = datetime.now().isoformat()
                if reason:
                    task['rejection_reason'] = reason

                self.save_queue(tasks)
                return True

        return False

    def print_summary(self):
        """Print human-friendly summary of pending tasks"""
        summary = self.get_pending_summary()

        print("=" * 70)
        print("Claude Queue - Pending Approval")
        print("=" * 70)
        print()

        if summary['total_pending'] == 0:
            print("✅ No tasks awaiting approval")
            return

        print(f"**Total Pending:** {summary['total_pending']} tasks")
        print(f"**Estimated Duration:** ~{summary['total_estimated_hours']:.1f} hours")
        print()

        print("BY CATEGORY:")
        print()
        for category, info in sorted(summary['by_category'].items()):
            print(f"  📁 {category.upper()}")
            print(f"     Tasks: {info['count']}")
            print(f"     Duration: ~{info['estimated_hours']:.1f} hours")
            print()

        print("TO APPROVE:")
        print()
        print(f"  # Approve all categories")
        print(f"  python3 approve_claude_queue.py --approve-all")
        print()
        print(f"  # Approve specific category")
        for category in sorted(summary['by_category'].keys()):
            print(f"  python3 approve_claude_queue.py --approve {category}")
        print()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Approve or reject Claude Max tasks (Constitutional Principle 1: Human Agency)"
    )

    parser.add_argument(
        '--approve',
        type=str,
        metavar='CATEGORY',
        help='Approve all tasks in specified category'
    )

    parser.add_argument(
        '--approve-all',
        action='store_true',
        help='Approve all pending tasks'
    )

    parser.add_argument(
        '--reject',
        type=str,
        metavar='TASK_ID',
        help='Reject specific task by ID'
    )

    parser.add_argument(
        '--reason',
        type=str,
        help='Rejection reason (use with --reject)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of pending tasks (default if no action specified)'
    )

    parser.add_argument(
        '--approved-by',
        type=str,
        default=os.getenv('USER', 'human'),
        help='Username approving tasks (default: current user)'
    )

    args = parser.parse_args()

    approver = ClaudeQueueApprover()

    # Determine action
    if args.approve:
        print(f"Approving category: {args.approve}")
        count = approver.approve_category(args.approve, args.approved_by)
        print(f"✅ Approved {count} tasks in category '{args.approve}'")

    elif args.approve_all:
        print("Approving all pending tasks...")
        count = approver.approve_all(args.approved_by)
        print(f"✅ Approved {count} tasks")

    elif args.reject:
        print(f"Rejecting task: {args.reject}")
        reason = args.reason or "Human rejection"
        if approver.reject_task(args.reject, reason):
            print(f"✅ Rejected task {args.reject}")
        else:
            print(f"❌ Task {args.reject} not found")

    else:
        # Default: show summary
        approver.print_summary()


if __name__ == "__main__":
    main()
