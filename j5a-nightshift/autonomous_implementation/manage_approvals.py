#!/usr/bin/env python3
"""
Manage pre-approvals for autonomous workflow
"""
import json
import sys
from pathlib import Path

STATE_FILE = "progress/current_state.json"
QUEUE_FILE = "queue/all_tasks.json"

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_queue():
    with open(QUEUE_FILE, 'r') as f:
        return json.load(f)

def get_task_info(task_id, queue_data):
    """Get task details by ID"""
    for phase in queue_data['phases']:
        for task in phase['tasks']:
            if task['task_id'] == task_id:
                return {
                    'task_id': task_id,
                    'description': task['description'],
                    'type': task.get('type', 'unknown'),
                    'risk_level': task.get('risk_level', 'medium'),
                    'phase_name': phase['phase_name']
                }
    return None

def show_status():
    """Show current pre-approval status"""
    state = load_state()
    queue = load_queue()

    pre_approved = state.get('pre_approved_tasks', [])

    print("=" * 60)
    print("PRE-APPROVED TASKS")
    print("=" * 60)

    if not pre_approved:
        print("\nNo tasks currently pre-approved.")
    else:
        print(f"\n{len(pre_approved)} task(s) pre-approved:\n")
        for task_id in pre_approved:
            info = get_task_info(task_id, queue)
            if info:
                print(f"  ✓ {task_id}")
                print(f"    {info['description']}")
                print(f"    Phase: {info['phase_name']}")
                print(f"    Risk: {info['risk_level']}")
                print()

def add_pre_approvals(task_ids):
    """Add tasks to pre-approval list"""
    state = load_state()
    queue = load_queue()

    if 'pre_approved_tasks' not in state:
        state['pre_approved_tasks'] = []

    added = []
    for task_id in task_ids:
        if task_id not in state['pre_approved_tasks']:
            # Verify task exists
            info = get_task_info(task_id, queue)
            if info:
                state['pre_approved_tasks'].append(task_id)
                added.append(task_id)
                print(f"✓ Pre-approved: {task_id} - {info['description']}")
            else:
                print(f"✗ Task not found: {task_id}")
        else:
            print(f"  Already pre-approved: {task_id}")

    if added:
        save_state(state)
        print(f"\n{len(added)} task(s) added to pre-approval list")

    return len(added)

def clear_pre_approvals():
    """Clear all pre-approvals"""
    state = load_state()
    count = len(state.get('pre_approved_tasks', []))
    state['pre_approved_tasks'] = []
    save_state(state)
    print(f"Cleared {count} pre-approval(s)")

def recommend_batch():
    """Recommend a safe batch of tasks to pre-approve"""
    state = load_state()
    queue = load_queue()
    completed = state['completed_tasks']

    print("=" * 60)
    print("RECOMMENDED PRE-APPROVAL BATCH")
    print("=" * 60)
    print("\nSafe for autonomous execution while you're away:\n")

    # Recommend well-defined, lower-risk tasks
    recommended = [
        "phase2_task1",  # Create strategic_principles.py - well-defined module
        "phase2_task4",  # Documentation checklist
        "phase5_task1",  # Create directories - file system only
        "phase5_task3",  # Initialize data templates
        "phase9_task1",  # Create playbook directories
    ]

    # Filter to only tasks that aren't complete
    recommended = [t for t in recommended if t not in completed]

    for task_id in recommended:
        info = get_task_info(task_id, queue)
        if info:
            risk_emoji = "🟢" if info['risk_level'] == "low" else "🟡"
            print(f"  {risk_emoji} {task_id}")
            print(f"     {info['description']}")
            print(f"     Type: {info['type']} | Risk: {info['risk_level']}")
            print()

    print("\nTo pre-approve all recommended tasks:")
    print(f"  python3 manage_approvals.py add {' '.join(recommended)}")
    print()
    print("Or pre-approve individually:")
    print("  python3 manage_approvals.py add phase2_task1")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 manage_approvals.py status              # Show current pre-approvals")
        print("  python3 manage_approvals.py recommend           # Show recommended batch")
        print("  python3 manage_approvals.py add <task_id> ...   # Add pre-approvals")
        print("  python3 manage_approvals.py clear               # Clear all pre-approvals")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        show_status()
    elif command == "recommend":
        recommend_batch()
    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: Specify at least one task ID")
            sys.exit(1)
        task_ids = sys.argv[2:]
        add_pre_approvals(task_ids)
    elif command == "clear":
        clear_pre_approvals()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
