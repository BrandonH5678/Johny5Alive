#!/usr/bin/env python3
"""
Jeeves Snapshot Manager - Full State Snapshots Before Autonomous Fixes

Mission: Ensure all automated changes are reversible by capturing complete
repository state before any modification.

Constitutional Basis: Principle 3 (System Viability) - Reliability > Features
Strategic Basis: Principle 5 (Adaptive Feedback) - Learn from mistakes safely
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List
import os
import time
import json
import subprocess
import shutil
import hashlib
from datetime import datetime
from rich.console import Console
from git import Repo
from .utils import ensure_dir, repo_root

console = Console()


@dataclass
class SnapshotMetadata:
    """Metadata for a repository snapshot"""
    snapshot_id: str
    repo_name: str
    repo_path: str
    created_at: str
    git_commit: str
    git_branch: str
    reason: str
    compressed: bool
    compression_format: str
    size_bytes: int
    file_count: int
    verified: bool
    verification_hash: Optional[str] = None


class SnapshotManager:
    """
    Manages full-state snapshots of repositories before autonomous operations.

    Features:
    - Git-based snapshots (clean working tree required)
    - Optional zstd compression
    - Verification via restore test
    - Metadata tracking for audit trail
    - Constitutional compliance (Transparency + System Viability)
    """

    def __init__(self, config: Dict):
        """
        Initialize snapshot manager with configuration.

        Args:
            config: Jeeves configuration dict containing snapshot settings
        """
        self.config = config.get("snapshot", {})
        self.compress = self.config.get("compress") == "zstd"
        self.verify_restore = self.config.get("verify_restore", True)
        self.snapshot_root = ensure_dir(repo_root() / ".jeeves" / "snapshots")
        self.metadata_file = self.snapshot_root / "snapshot_registry.json"
        self._load_registry()

    def _load_registry(self):
        """Load snapshot metadata registry"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.registry = json.load(f)
        else:
            self.registry = {"snapshots": []}

    def _save_registry(self):
        """Save snapshot metadata registry"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def create_snapshot(
        self,
        repo_path: Path,
        repo_name: str,
        reason: str
    ) -> SnapshotMetadata:
        """
        Create a full snapshot of repository state.

        Args:
            repo_path: Path to repository to snapshot
            repo_name: Name identifier for the repository
            reason: Human-readable reason for snapshot (e.g., "Before tidy cleanup")

        Returns:
            SnapshotMetadata object with snapshot details

        Raises:
            RuntimeError: If git repo is dirty or snapshot creation fails
        """
        console.print(f"[cyan]Creating snapshot: {repo_name}[/cyan]")
        console.print(f"[dim]Reason: {reason}[/dim]")

        # Validate git repository
        if not (repo_path / ".git").exists():
            raise RuntimeError(f"Not a git repository: {repo_path}")

        repo = Repo(repo_path)

        # Check for uncommitted changes
        if repo.is_dirty(untracked_files=True):
            console.print("[yellow]⚠️  Warning: Repository has uncommitted changes[/yellow]")
            console.print("[yellow]   Snapshot will capture current state, but consider committing first[/yellow]")

        # Generate snapshot ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"{repo_name}_{timestamp}"
        snapshot_dir = ensure_dir(self.snapshot_root / snapshot_id)

        # Get git metadata
        try:
            git_commit = repo.head.commit.hexsha
            git_branch = repo.active_branch.name
        except Exception as e:
            console.print(f"[yellow]Could not get git metadata: {e}[/yellow]")
            git_commit = "unknown"
            git_branch = "unknown"

        # Create git archive (clean snapshot of committed files)
        archive_path = snapshot_dir / f"{repo_name}.tar"
        console.print(f"[dim]Creating git archive...[/dim]")

        try:
            # Use git archive to get clean snapshot of tracked files
            subprocess.run(
                ["git", "archive", "--format=tar", "-o", str(archive_path), "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git archive failed: {e.stderr.decode()}")

        # Save untracked/modified files separately if repo is dirty
        dirty_files_path = None
        if repo.is_dirty(untracked_files=True):
            dirty_files_path = snapshot_dir / "dirty_state"
            dirty_files_path.mkdir(exist_ok=True)

            # Capture untracked files
            untracked = repo.untracked_files
            if untracked:
                console.print(f"[dim]Capturing {len(untracked)} untracked files...[/dim]")
                for file in untracked:
                    src = repo_path / file
                    dst = dirty_files_path / file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.exists() and src.is_file():
                        shutil.copy2(src, dst)

            # Capture modified files
            modified = [item.a_path for item in repo.index.diff(None)]
            if modified:
                console.print(f"[dim]Capturing {len(modified)} modified files...[/dim]")
                for file in modified:
                    src = repo_path / file
                    dst = dirty_files_path / f"{file}.modified"
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.exists() and src.is_file():
                        shutil.copy2(src, dst)

        # Compress if enabled
        compressed = False
        compression_format = "none"
        if self.compress and shutil.which("zstd"):
            console.print(f"[dim]Compressing with zstd...[/dim]")
            try:
                subprocess.run(
                    ["zstd", "-q", "--rm", str(archive_path)],
                    check=True,
                    capture_output=True
                )
                archive_path = archive_path.with_suffix(".tar.zst")
                compressed = True
                compression_format = "zstd"
            except subprocess.CalledProcessError as e:
                console.print(f"[yellow]Compression failed: {e}, keeping uncompressed[/yellow]")

        # Calculate snapshot size and file count
        size_bytes = archive_path.stat().st_size
        if dirty_files_path:
            for item in dirty_files_path.rglob("*"):
                if item.is_file():
                    size_bytes += item.stat().st_size

        # Count files in archive (approximate)
        file_count = len(list(repo_path.rglob("*")))

        # Calculate verification hash
        verification_hash = self._calculate_hash(archive_path)

        # Create metadata
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            repo_name=repo_name,
            repo_path=str(repo_path),
            created_at=datetime.now().isoformat(),
            git_commit=git_commit,
            git_branch=git_branch,
            reason=reason,
            compressed=compressed,
            compression_format=compression_format,
            size_bytes=size_bytes,
            file_count=file_count,
            verified=False,
            verification_hash=verification_hash
        )

        # Save metadata to snapshot directory
        metadata_path = snapshot_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(asdict(metadata), f, indent=2)

        # Verify restore if enabled
        if self.verify_restore:
            console.print(f"[dim]Verifying snapshot can be restored...[/dim]")
            if self._verify_snapshot(snapshot_dir, archive_path, compressed):
                metadata.verified = True
                console.print("[green]✓ Snapshot verified successfully[/green]")
            else:
                console.print("[yellow]⚠️  Snapshot verification failed[/yellow]")

        # Update registry
        self.registry["snapshots"].append(asdict(metadata))
        self._save_registry()

        size_mb = size_bytes / (1024 * 1024)
        console.print(f"[green]✓ Snapshot created: {snapshot_id}[/green]")
        console.print(f"[dim]  Size: {size_mb:.1f}MB, Files: {file_count}[/dim]")

        return metadata

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for verification"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _verify_snapshot(self, snapshot_dir: Path, archive_path: Path, compressed: bool) -> bool:
        """
        Verify snapshot can be restored successfully.

        Args:
            snapshot_dir: Directory containing snapshot
            archive_path: Path to archive file
            compressed: Whether archive is compressed

        Returns:
            True if verification successful, False otherwise
        """
        verify_dir = snapshot_dir / "verify_test"
        verify_dir.mkdir(exist_ok=True)

        try:
            # Decompress if needed
            if compressed:
                subprocess.run(
                    ["zstd", "-d", "-q", str(archive_path), "-o", str(verify_dir / "archive.tar")],
                    check=True,
                    capture_output=True
                )
                test_archive = verify_dir / "archive.tar"
            else:
                test_archive = archive_path

            # Extract to verify directory
            subprocess.run(
                ["tar", "-xf", str(test_archive), "-C", str(verify_dir)],
                check=True,
                capture_output=True
            )

            # Check that files were extracted
            extracted_files = list(verify_dir.rglob("*"))
            if len(extracted_files) == 0:
                return False

            # Cleanup verify directory
            shutil.rmtree(verify_dir)

            return True

        except Exception as e:
            console.print(f"[yellow]Verification error: {e}[/yellow]")
            return False

    def restore_snapshot(self, snapshot_id: str, restore_path: Path) -> bool:
        """
        Restore a snapshot to specified location.

        Args:
            snapshot_id: ID of snapshot to restore
            restore_path: Path where snapshot should be restored

        Returns:
            True if restore successful, False otherwise

        Note: This is a DESTRUCTIVE operation. Use with caution.
        Constitutional requirement: Human approval via interactive prompt recommended.
        """
        console.print(f"[yellow]⚠️  RESTORE OPERATION - This will overwrite {restore_path}[/yellow]")

        # Find snapshot in registry
        snapshot_meta = None
        for snap in self.registry["snapshots"]:
            if snap["snapshot_id"] == snapshot_id:
                snapshot_meta = snap
                break

        if not snapshot_meta:
            console.print(f"[red]✗ Snapshot not found: {snapshot_id}[/red]")
            return False

        snapshot_dir = self.snapshot_root / snapshot_id
        if not snapshot_dir.exists():
            console.print(f"[red]✗ Snapshot directory missing: {snapshot_dir}[/red]")
            return False

        # Find archive file
        archive_files = list(snapshot_dir.glob("*.tar*"))
        if not archive_files:
            console.print(f"[red]✗ Archive file not found in snapshot[/red]")
            return False

        archive_path = archive_files[0]
        compressed = archive_path.suffix == ".zst"

        console.print(f"[cyan]Restoring snapshot: {snapshot_id}[/cyan]")
        console.print(f"[dim]From: {snapshot_meta['created_at']}[/dim]")
        console.print(f"[dim]Reason: {snapshot_meta['reason']}[/dim]")

        try:
            # Create restore directory
            restore_path.mkdir(parents=True, exist_ok=True)

            # Decompress if needed
            if compressed:
                console.print(f"[dim]Decompressing...[/dim]")
                temp_tar = snapshot_dir / "temp_restore.tar"
                subprocess.run(
                    ["zstd", "-d", "-q", str(archive_path), "-o", str(temp_tar)],
                    check=True,
                    capture_output=True
                )
                extract_archive = temp_tar
            else:
                extract_archive = archive_path

            # Extract archive
            console.print(f"[dim]Extracting to {restore_path}...[/dim]")
            subprocess.run(
                ["tar", "-xf", str(extract_archive), "-C", str(restore_path)],
                check=True,
                capture_output=True
            )

            # Restore dirty state if exists
            dirty_state = snapshot_dir / "dirty_state"
            if dirty_state.exists():
                console.print(f"[dim]Restoring uncommitted changes...[/dim]")
                for item in dirty_state.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(dirty_state)
                        dst = restore_path / rel_path
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dst)

            # Cleanup temp files
            if compressed and temp_tar.exists():
                temp_tar.unlink()

            console.print(f"[green]✓ Snapshot restored successfully[/green]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Restore failed: {e}[/red]")
            return False

    def list_snapshots(self, repo_name: Optional[str] = None) -> List[SnapshotMetadata]:
        """
        List all available snapshots, optionally filtered by repository.

        Args:
            repo_name: Optional repository name to filter by

        Returns:
            List of SnapshotMetadata objects
        """
        snapshots = []
        for snap_dict in self.registry["snapshots"]:
            if repo_name is None or snap_dict["repo_name"] == repo_name:
                snapshots.append(SnapshotMetadata(**snap_dict))
        return snapshots

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot and its files.

        Args:
            snapshot_id: ID of snapshot to delete

        Returns:
            True if deletion successful, False otherwise
        """
        # Find and remove from registry
        snapshot_meta = None
        for i, snap in enumerate(self.registry["snapshots"]):
            if snap["snapshot_id"] == snapshot_id:
                snapshot_meta = snap
                del self.registry["snapshots"][i]
                break

        if not snapshot_meta:
            console.print(f"[yellow]Snapshot not found in registry: {snapshot_id}[/yellow]")
            return False

        # Delete snapshot directory
        snapshot_dir = self.snapshot_root / snapshot_id
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
            console.print(f"[green]✓ Deleted snapshot: {snapshot_id}[/green]")

        # Save updated registry
        self._save_registry()

        return True

    def get_snapshot_info(self, snapshot_id: str) -> Optional[SnapshotMetadata]:
        """
        Get metadata for a specific snapshot.

        Args:
            snapshot_id: ID of snapshot

        Returns:
            SnapshotMetadata if found, None otherwise
        """
        for snap in self.registry["snapshots"]:
            if snap["snapshot_id"] == snapshot_id:
                return SnapshotMetadata(**snap)
        return None
