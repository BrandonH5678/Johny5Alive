#!/usr/bin/env python3
"""
Governance Logger - Strategic Principle 8

Logs all significant decisions for auditability and accountability.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class GovernanceLogger:
    """
    Strategic Principle 8: Governance & Alignment

    Constitutional Alignment:
    - Principle 2: Transparent, auditable decisions
    """

    def __init__(self, log_dir: str = "governance/decisions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_decision(self, decision_type: str = None, context: Dict = None,
                    decision: Dict = None, principle_alignment: List[str] = None,
                    # Legacy parameters for backward compatibility
                    decision_point: str = None, choice: str = None,
                    rationale: str = None, alternatives: List[str] = None):
        """
        Record significant decision

        Args:
            decision_type: Type of decision being made (new API)
            context: Decision context (new API)
            decision: Decision details (new API)
            principle_alignment: Constitutional principles aligned (new API)
            decision_point: Legacy parameter
            choice: Legacy parameter
            rationale: Legacy parameter
            alternatives: Legacy parameter
        """
        # Support both old and new API
        if decision_type:
            # New API
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'decision_type': decision_type,
                'context': context or {},
                'decision': decision or {},
                'principle_alignment': principle_alignment or [],
                'human_override_available': True
            }
        else:
            # Legacy API
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'decision_point': decision_point,
                'chosen_option': choice,
                'rationale': rationale,
                'alternatives_considered': alternatives or [],
                'principle_alignment': principle_alignment,
                'human_override_available': True
            }

        # Save to timestamped file
        filename = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.log_dir / filename

        with open(filepath, 'w') as f:
            json.dump(log_entry, f, indent=2)

        decision_desc = decision_type or decision_point
        logger.info(f"Decision logged: {decision_desc}")

    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Retrieve recent decisions"""
        decisions = []
        files = sorted(self.log_dir.glob("decision_*.json"),
                      key=lambda p: p.stat().st_mtime,
                      reverse=True)

        for file in files[:limit]:
            with open(file, 'r') as f:
                decisions.append(json.load(f))

        return decisions
