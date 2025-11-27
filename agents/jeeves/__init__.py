"""
Jeeves - J5A House-Cleaner & Standards Enforcer

Mission:
- Tidy: Find dead/legacy artifacts and overlapping/duplicated functionality
- Safeguard: Full state snapshots before any autonomous fix/refactor
- Enforce: Continuously check against engineering standards

Validation Model: Existence → Process → Outputs
"""

__version__ = "1.0.0"

# Import implemented modules
from .scanner import TidyScanner
from .overlap import OverlapDetector
from .snapshot import SnapshotManager

# TODO: Not yet implemented - will import when ready
# from .standards import StandardsEnforcer
# from .planner import FixPlanner
# from .exec import GuardrailedExecutor
# from .report import ReportGenerator

__all__ = [
    "TidyScanner",
    "OverlapDetector",
    "SnapshotManager",
    # Future exports when implemented:
    # "StandardsEnforcer",
    # "FixPlanner",
    # "GuardrailedExecutor",
    # "ReportGenerator",
]
