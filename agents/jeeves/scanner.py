#!/usr/bin/env python3
"""
Jeeves Scanner - Repository Analysis & Tidy Detection
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Iterable
import os, time, yaml, json
from rich.console import Console
from .utils import ensure_dir, repo_root
from git import Repo

console = Console()

@dataclass
class RepoTarget:
    name: str
    path: str  # relative to monorepo root

@dataclass
class TidyFinding:
    id: str
    repo: str
    path: str
    reason: str
    risk: str
    size_bytes: int
    last_touched_days: int
    proposed: str  # e.g., "move_to_legacy", "delete_duplicate", "convert_to_lfs"

class TidyScanner:
    def __init__(self, config_path: Path):
        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)
        self.inactive_days = int(self.cfg.get("inactive_days", 60))
        self.max_binary_mb = int(self.cfg.get("max_binary_mb", 50))
        self.ignore_globs: List[str] = self.cfg.get("ignore_globs", [])
        self.treat_as_data: List[str] = self.cfg.get("treat_as_data", [])
        self.repos = [RepoTarget(**r) for r in self.cfg.get("repos", [])]

    def _should_ignore(self, rel_path: str) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(rel_path, g) for g in self.ignore_globs)

    def _days_since_commit(self, repo: Repo, file_path: Path) -> int:
        rel = os.path.relpath(file_path, repo.working_dir)
        try:
            commits = list(repo.iter_commits(paths=rel, max_count=1))
            if not commits:
                return 99999
            last = commits[0].committed_date
        except Exception:
            return 99999
        return int((time.time() - last) / 86400)

    def scan(self, out_dir: Path) -> Dict[str, List[TidyFinding]]:
        results: Dict[str, List[TidyFinding]] = {}
        monoroot = repo_root()
        out_dir = ensure_dir(out_dir)

        for target in self.repos:
            repo_dir = monoroot / target.path
            if not repo_dir.exists():
                console.print(f"[yellow]Repo path missing: {repo_dir}", highlight=False)
                continue
            repo = Repo(repo_dir)
            findings: List[TidyFinding] = []

            for p in repo_dir.rglob("*"):
                if not p.is_file():
                    continue
                rel = str(p.relative_to(monoroot))
                if self._should_ignore(rel):
                    continue
                size = p.stat().st_size
                days = self._days_since_commit(repo, p)

                # Heuristics
                reasons = []
                proposed = None
                risk = "low"

                if size > self.max_binary_mb * 1024 * 1024 and not any(p.match(g) for g in self.treat_as_data):
                    reasons.append(f"Large binary ({size//1024//1024}MB) not marked as data")
                    proposed = proposed or "convert_to_lfs"
                    risk = "medium"

                if days >= self.inactive_days:
                    reasons.append(f"Inactive ({days}d since last commit)")
                    proposed = proposed or "move_to_legacy"

                if p.suffix in {".bak", ".old"} or any(seg in {"tmp","temp"} for seg in p.parts):
                    reasons.append("Looks like backup/tmp")
                    proposed = proposed or "delete"

                if not reasons:
                    continue

                fid = f"{target.name}:{rel}"
                findings.append(TidyFinding(
                    id=fid, repo=target.name, path=rel, reason="; ".join(reasons),
                    risk=risk, size_bytes=size, last_touched_days=days, proposed=proposed or "review"
                ))

            results[target.name] = findings

            # Write per-repo JSON
            with open(out_dir / f"{target.name}_tidy_findings.json", "w") as f:
                json.dump([asdict(x) for x in findings], f, indent=2)

        # Consolidated JSON
        with open(out_dir / "tidy_findings.json", "w") as f:
            json.dump({k:[asdict(x) for x in v] for k,v in results.items()}, f, indent=2)
        return results
