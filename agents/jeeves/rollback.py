#!/usr/bin/env python3
"""
J5A Rollback Script - Quick recovery from pre-autonomous snapshots

Usage:
    python rollback.py list <repo_path>                    # List available snapshots
    python rollback.py rollback <repo_path> <tag_name>     # Rollback to specific tag
    python rollback.py latest <repo_path>                  # Rollback to most recent snapshot

Constitutional Basis:
- Principle 1 (Human Agency): Interactive confirmation required
- Principle 3 (System Viability): Enables safe autonomous work
"""

import sys
import argparse
from pathlib import Path

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.jeeves.snapshot import SnapshotManager
from agents.jeeves.utils import load_config


def list_snapshots(repo_path: Path):
    """List all pre-autonomous snapshots for a repository"""
    config = load_config()
    manager = SnapshotManager(config)

    snapshots = manager.list_pre_autonomous_snapshots(repo_path)

    if not snapshots:
        print(f"No pre-autonomous snapshots found for {repo_path}")
        return

    print(f"\n📸 Pre-Autonomous Snapshots for {repo_path.name}:")
    print("-" * 70)

    for snap in snapshots:
        print(f"  Tag: {snap['name']}")
        print(f"  Commit: {snap['commit']}")
        print(f"  Date: {snap['date']}")
        if snap['message']:
            # First line of message only
            msg_line = snap['message'].split('\n')[0]
            print(f"  Task: {msg_line}")
        print()


def rollback(repo_path: Path, tag_name: str, force: bool = False):
    """Rollback repository to specific tag"""
    config = load_config()
    manager = SnapshotManager(config)

    print(f"\n⚠️  ROLLBACK OPERATION")
    print(f"Repository: {repo_path}")
    print(f"Target tag: {tag_name}")
    print()

    if not force:
        print("This will DISCARD all changes since the snapshot.")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Rollback cancelled.")
            return False

    return manager.rollback_to_tag(repo_path, tag_name, confirm=True)


def rollback_latest(repo_path: Path, force: bool = False):
    """Rollback to most recent pre-autonomous snapshot"""
    config = load_config()
    manager = SnapshotManager(config)

    snapshots = manager.list_pre_autonomous_snapshots(repo_path)

    if not snapshots:
        print(f"No pre-autonomous snapshots found for {repo_path}")
        return False

    latest = snapshots[0]  # Already sorted by date descending
    print(f"Latest snapshot: {latest['name']}")
    print(f"Date: {latest['date']}")

    return rollback(repo_path, latest['name'], force)


def main():
    parser = argparse.ArgumentParser(
        description="J5A Rollback Script - Recovery from pre-autonomous snapshots"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List available snapshots")
    list_parser.add_argument("repo_path", type=Path, help="Path to repository")

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to specific tag")
    rollback_parser.add_argument("repo_path", type=Path, help="Path to repository")
    rollback_parser.add_argument("tag_name", help="Tag name to rollback to")
    rollback_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # Latest command
    latest_parser = subparsers.add_parser("latest", help="Rollback to most recent snapshot")
    latest_parser.add_argument("repo_path", type=Path, help="Path to repository")
    latest_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if args.command == "list":
        list_snapshots(args.repo_path)
    elif args.command == "rollback":
        success = rollback(args.repo_path, args.tag_name, args.force)
        sys.exit(0 if success else 1)
    elif args.command == "latest":
        success = rollback_latest(args.repo_path, args.force)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
