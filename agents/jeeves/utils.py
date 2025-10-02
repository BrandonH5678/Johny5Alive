#!/usr/bin/env python3
"""Jeeves Utilities - Shared helper functions"""

from pathlib import Path
from datetime import datetime, timezone
import subprocess
from typing import Iterable
from rich.console import Console

console = Console()


def ts() -> str:
    """Generate UTC timestamp string"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def ensure_dir(p: Path) -> Path:
    """Ensure directory exists"""
    p.mkdir(parents=True, exist_ok=True)
    return p


def run(cmd: Iterable[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run command with logging"""
    console.log(f"[bold cyan]$ {' '.join(cmd)}[/]")
    return subprocess.run(list(cmd), cwd=cwd, check=True, text=True, capture_output=True)


def repo_root() -> Path:
    """Get repository root (assumes this file lives in j5a/agents/jeeves)"""
    return Path(__file__).resolve().parents[3]
