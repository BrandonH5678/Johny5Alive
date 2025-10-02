"""
Jeeves - J5A House-Cleaner & Standards Enforcer

Mission:
- Tidy: Find dead/legacy artifacts and overlapping/duplicated functionality
- Safeguard: Full state snapshots before any autonomous fix/refactor
- Enforce: Continuously check against engineering standards

Validation Model: Existence → Process → Outputs
"""

__version__ = "1.0.0"

from .scanner import Scanner
from .overlap import OverlapDetector
from .standards import StandardsEnforcer
from .snapshot import SnapshotManager
from .planner import FixPlanner
from .exec import GuardrailedExecutor
from .report import ReportGenerator

__all__ = [
    "Scanner",
    "OverlapDetector",
    "StandardsEnforcer",
    "SnapshotManager",
    "FixPlanner",
    "GuardrailedExecutor",
    "ReportGenerator",
]
