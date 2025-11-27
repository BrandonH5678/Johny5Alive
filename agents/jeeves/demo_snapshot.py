#!/usr/bin/env python3
"""
Jeeves Snapshot Demo - Example usage of SnapshotManager

This demonstrates how to use the snapshot system for safe repository operations.
"""

from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from snapshot import SnapshotManager

console = Console()


def demo_snapshot_workflow():
    """Demonstrate the snapshot workflow"""

    console.print("\n[bold cyan]═══ Jeeves Snapshot Manager Demo ═══[/bold cyan]\n")

    # Load configuration
    config_path = Path("../../configs/jeeves.yml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize manager
    manager = SnapshotManager(config)
    console.print("[green]✓[/green] SnapshotManager initialized")
    console.print(f"[dim]  Snapshot location: {manager.snapshot_root}[/dim]\n")

    # Example 1: Create a snapshot
    console.print("[bold]Example 1: Creating a Snapshot[/bold]")
    console.print("[dim]Before making any automated changes, create a snapshot...[/dim]\n")

    try:
        repo_path = Path("/home/johnny5/Johny5Alive")
        metadata = manager.create_snapshot(
            repo_path=repo_path,
            repo_name="j5a",
            reason="Demo: Before tidy cleanup operation"
        )
        console.print(f"\n[green]✓[/green] Snapshot created: {metadata.snapshot_id}")
        console.print(f"[dim]  Size: {metadata.size_bytes / (1024*1024):.1f}MB[/dim]")
        console.print(f"[dim]  Files: {metadata.file_count}[/dim]")
        console.print(f"[dim]  Verified: {metadata.verified}[/dim]\n")
    except Exception as e:
        console.print(f"[yellow]Note: {e}[/yellow]")
        console.print("[dim](This is expected if running from outside repo)[/dim]\n")

    # Example 2: List snapshots
    console.print("[bold]Example 2: Listing Available Snapshots[/bold]\n")

    snapshots = manager.list_snapshots()
    if snapshots:
        table = Table(title="Available Snapshots")
        table.add_column("Snapshot ID", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Reason", style="white")
        table.add_column("Size (MB)", justify="right")

        for snap in snapshots:
            size_mb = snap.size_bytes / (1024 * 1024)
            table.add_row(
                snap.snapshot_id,
                snap.repo_name,
                snap.created_at.split("T")[0],
                snap.reason[:40] + "..." if len(snap.reason) > 40 else snap.reason,
                f"{size_mb:.1f}"
            )

        console.print(table)
    else:
        console.print("[dim]No snapshots found (registry is empty)[/dim]")

    console.print()

    # Example 3: Usage pattern
    console.print("[bold]Example 3: Typical Usage Pattern[/bold]\n")

    example_code = """
# In your automation script:

from agents.jeeves.snapshot import SnapshotManager
import yaml

# Initialize
with open("configs/jeeves.yml") as f:
    config = yaml.safe_load(f)
manager = SnapshotManager(config)

# BEFORE making changes:
snapshot = manager.create_snapshot(
    repo_path=Path("/home/johnny5/Johny5Alive"),
    repo_name="j5a",
    reason="Before automated tidy cleanup"
)

try:
    # Perform automated changes here...
    delete_old_files()
    move_to_legacy()

    print(f"✓ Changes complete")

except Exception as e:
    # If something goes wrong, restore from snapshot
    print(f"✗ Error occurred: {e}")
    print(f"Restoring from snapshot {snapshot.snapshot_id}...")

    manager.restore_snapshot(
        snapshot.snapshot_id,
        Path("/home/johnny5/Johny5Alive")
    )
"""

    console.print("[dim]" + example_code + "[/dim]")

    # Constitutional compliance note
    console.print("\n[bold]Constitutional Compliance:[/bold]")
    console.print("  [green]✓[/green] Principle 3 (System Viability): Snapshots ensure reliability")
    console.print("  [green]✓[/green] Principle 2 (Transparency): All snapshots logged in registry")
    console.print("  [green]✓[/green] Principle 4 (Resource Stewardship): Compression enabled\n")


if __name__ == "__main__":
    demo_snapshot_workflow()
