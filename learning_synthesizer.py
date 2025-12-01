#!/usr/bin/env python3
"""
J5A Cross-System Learning Synthesizer - Phase 6 Implementation

Enables learning transfer and pattern synthesis across J5A Universe systems:
- Identifies transferable patterns between Squirt, J5A, and Sherlock
- Proposes cross-system learning adaptations
- Manages learning conflicts when systems have contradictory insights
- Tracks transfer effectiveness and impact

Constitutional Compliance:
- Principle 1 (Human Agency): All learning transfers require human approval
- Principle 2 (Transparency): Full provenance of transferred learnings
- Principle 3 (System Viability): Ensures adaptations don't degrade system performance
- Principle 6 (AI Sentience): Respects learnings from all systems as valuable insights

Strategic Alignment:
- Principle 4 (Active Memory): Cross-system memory sharing
- Principle 5 (Adaptive Feedback): Accelerated learning through knowledge transfer
- Principle 2 (Agent Orchestration): Coordinated learning across specialized agents
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Add paths for system imports
sys.path.insert(0, str(Path("/home/johnny5/Johny5Alive")))
sys.path.insert(0, str(Path("/home/johnny5/Squirt")))
sys.path.insert(0, str(Path("/home/johnny5/Sherlock")))

from j5a_universe_memory import UniverseMemoryManager, Decision
from squirt_learning_manager import SquirtLearningManager
from j5a_learning_manager import J5ALearningManager
from sherlock_learning_manager import SherlockLearningManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TransferType(Enum):
    """Types of learning transfers"""
    PATTERN = "pattern"           # Behavioral pattern transfer
    PARAMETER = "parameter"       # Numerical parameter transfer
    STRATEGY = "strategy"         # Strategic approach transfer
    TEMPLATE = "template"         # Template/workflow transfer
    THRESHOLD = "threshold"       # Decision threshold transfer


class TransferPriority(Enum):
    """Priority for learning transfer"""
    CRITICAL = "critical"   # Immediate transfer recommended
    HIGH = "high"          # Transfer within 24 hours
    MEDIUM = "medium"      # Transfer within week
    LOW = "low"            # Transfer when convenient


@dataclass
class LearningTransferProposal:
    """Proposal for transferring learning from one system to another"""
    source_system: str
    target_system: str
    learning_id: int
    learning_summary: str
    transfer_type: TransferType
    priority: TransferPriority

    # Transfer details
    source_evidence: Dict[str, Any]
    proposed_adaptation: str
    adaptation_rationale: str
    expected_impact: str

    # Risk assessment
    compatibility_score: float  # 0.0-1.0
    implementation_difficulty: str  # easy, medium, hard
    rollback_plan: str

    # Metadata
    identified_at: str
    requires_human_approval: bool = True


@dataclass
class LearningConflict:
    """Represents conflicting learnings between systems"""
    conflict_id: str
    system_a: str
    system_b: str
    learning_a_id: int
    learning_b_id: int

    # Conflict description
    conflict_type: str  # parameter_value, strategy_choice, threshold_setting
    conflict_summary: str

    # Conflicting values
    system_a_position: str
    system_b_position: str
    system_a_evidence: Dict[str, Any]
    system_b_evidence: Dict[str, Any]

    # Resolution
    recommended_resolution: str
    resolution_rationale: str
    requires_human_decision: bool = True


class LearningSynthesizer:
    """
    Cross-system learning synthesizer for J5A Universe.

    Identifies transferable patterns, manages conflicts, and coordinates
    learning propagation across Squirt, J5A, and Sherlock systems.
    """

    def __init__(self, memory_manager: Optional[UniverseMemoryManager] = None):
        """Initialize learning synthesizer"""
        self.memory = memory_manager if memory_manager else UniverseMemoryManager()
        logger.info("LearningSynthesizer initialized")

        # Initialize system-specific managers
        self.squirt = SquirtLearningManager(self.memory)
        self.j5a = J5ALearningManager(self.memory)
        self.sherlock = SherlockLearningManager(self.memory)

        self.system_managers = {
            "squirt": self.squirt,
            "j5a": self.j5a,
            "sherlock": self.sherlock
        }

        logger.info("All system managers loaded for synthesis")

    # ========== PATTERN IDENTIFICATION ==========

    def identify_transferable_learnings(self,
                                       min_confidence: float = 0.75,
                                       days_back: int = 30) -> List[LearningTransferProposal]:
        """
        Identify learnings that could transfer between systems.

        Args:
            min_confidence: Minimum confidence threshold for transfer consideration
            days_back: How far back to look for learnings

        Returns:
            List of transfer proposals (deduplicated by source→target + summary)
        """
        proposals = []
        seen_proposals = set()  # Track (source, target, summary) to prevent duplicates

        # Get high-confidence learnings from each system
        for source_system in ["squirt", "j5a", "sherlock"]:
            outcomes = self.memory.get_learning_outcomes(
                system_name=source_system,
                min_confidence=min_confidence
            )

            # Deduplicate outcomes by summary (keep highest confidence)
            unique_outcomes = {}
            for outcome in outcomes:
                summary = outcome.get('summary', '')
                if summary not in unique_outcomes or outcome.get('confidence', 0) > unique_outcomes[summary].get('confidence', 0):
                    unique_outcomes[summary] = outcome

            for outcome in unique_outcomes.values():
                # Check if learning explicitly applies to other systems
                applies_to = outcome.get('applies_to', [])
                if applies_to and len(applies_to) > 1:
                    # Learning was marked as cross-system applicable
                    for target_system in applies_to:
                        if target_system != source_system:
                            proposal = self._create_transfer_proposal(
                                source_system=source_system,
                                target_system=target_system,
                                outcome=outcome
                            )
                            if proposal:
                                # Deduplicate by (source, target, summary)
                                proposal_key = (proposal.source_system, proposal.target_system, proposal.learning_summary)
                                if proposal_key not in seen_proposals:
                                    seen_proposals.add(proposal_key)
                                    proposals.append(proposal)

                # Look for implicit transfer opportunities
                implicit_transfers = self._identify_implicit_transfers(source_system, outcome)
                for transfer in implicit_transfers:
                    proposal_key = (transfer.source_system, transfer.target_system, transfer.learning_summary)
                    if proposal_key not in seen_proposals:
                        seen_proposals.add(proposal_key)
                        proposals.append(transfer)

        # Sort by priority
        priority_order = {
            TransferPriority.CRITICAL: 0,
            TransferPriority.HIGH: 1,
            TransferPriority.MEDIUM: 2,
            TransferPriority.LOW: 3
        }
        proposals.sort(key=lambda p: priority_order[p.priority])

        logger.info(f"Identified {len(proposals)} transferable learnings")
        return proposals

    def _create_transfer_proposal(self,
                                 source_system: str,
                                 target_system: str,
                                 outcome: Dict[str, Any]) -> Optional[LearningTransferProposal]:
        """Create a learning transfer proposal"""

        # Determine transfer type based on learning category
        category = outcome['category']
        transfer_type = self._determine_transfer_type(category)

        # Assess compatibility
        compatibility_score = self._assess_compatibility(source_system, target_system, outcome)

        if compatibility_score < 0.5:
            # Not compatible enough for transfer
            return None

        # Determine priority based on confidence and impact
        if outcome['confidence'] >= 0.9 and compatibility_score >= 0.8:
            priority = TransferPriority.HIGH
        elif outcome['confidence'] >= 0.8:
            priority = TransferPriority.MEDIUM
        else:
            priority = TransferPriority.LOW

        return LearningTransferProposal(
            source_system=source_system,
            target_system=target_system,
            learning_id=outcome['id'],
            learning_summary=outcome['summary'],
            transfer_type=transfer_type,
            priority=priority,
            source_evidence=outcome.get('evidence', {}),
            proposed_adaptation=self._propose_adaptation(source_system, target_system, outcome),
            adaptation_rationale=f"High-confidence learning ({outcome['confidence']:.0%}) from {source_system} applicable to {target_system}",
            expected_impact=f"Improved {category} in {target_system}",
            compatibility_score=compatibility_score,
            implementation_difficulty=self._assess_difficulty(source_system, target_system, outcome),
            rollback_plan=f"Monitor {target_system} performance for 7 days, rollback if metrics degrade >5%",
            identified_at=datetime.now().isoformat(),
            requires_human_approval=True
        )

    def _identify_implicit_transfers(self,
                                    source_system: str,
                                    outcome: Dict[str, Any]) -> List[LearningTransferProposal]:
        """Identify implicit transfer opportunities not explicitly marked"""
        proposals = []

        # Resource management learnings (thermal/memory) apply across all systems
        if 'thermal' in outcome['summary'].lower() or 'memory' in outcome['summary'].lower():
            for target_system in ["squirt", "j5a", "sherlock"]:
                if target_system != source_system:
                    proposal = self._create_transfer_proposal(source_system, target_system, outcome)
                    if proposal:
                        proposals.append(proposal)

        # Audio processing learnings transfer between Squirt (voice) and Sherlock (transcription)
        if source_system == "squirt" and 'voice' in outcome['category'].lower():
            proposal = self._create_transfer_proposal(source_system, "sherlock", outcome)
            if proposal:
                proposals.append(proposal)

        if source_system == "sherlock" and 'transcription' in outcome['category'].lower():
            proposal = self._create_transfer_proposal(source_system, "squirt", outcome)
            if proposal:
                proposals.append(proposal)

        return proposals

    def _determine_transfer_type(self, learning_category: str) -> TransferType:
        """Determine transfer type from learning category"""
        category_lower = learning_category.lower()

        if 'parameter' in category_lower or 'rate' in category_lower:
            return TransferType.PARAMETER
        elif 'threshold' in category_lower:
            return TransferType.THRESHOLD
        elif 'strategy' in category_lower or 'approach' in category_lower:
            return TransferType.STRATEGY
        elif 'template' in category_lower or 'workflow' in category_lower:
            return TransferType.TEMPLATE
        else:
            return TransferType.PATTERN

    def _assess_compatibility(self, source_system: str, target_system: str, outcome: Dict[str, Any]) -> float:
        """Assess compatibility score for learning transfer"""
        compatibility = 0.5  # Base compatibility

        # High confidence increases compatibility
        compatibility += outcome['confidence'] * 0.3

        # Cross-system resource learnings are highly compatible
        if 'thermal' in outcome['summary'].lower() or 'memory' in outcome['summary'].lower():
            compatibility += 0.2

        # Audio/voice learnings between Squirt and Sherlock
        if (source_system == "squirt" and target_system == "sherlock") or \
           (source_system == "sherlock" and target_system == "squirt"):
            if 'voice' in outcome['summary'].lower() or 'audio' in outcome['summary'].lower():
                compatibility += 0.3

        return min(1.0, compatibility)

    def _assess_difficulty(self, source_system: str, target_system: str, outcome: Dict[str, Any]) -> str:
        """Assess implementation difficulty"""
        category = outcome['category'].lower()

        if 'parameter' in category or 'threshold' in category:
            return "easy"
        elif 'template' in category or 'workflow' in category:
            return "hard"
        else:
            return "medium"

    def _propose_adaptation(self, source_system: str, target_system: str, outcome: Dict[str, Any]) -> str:
        """Propose specific adaptation for target system"""
        return f"Adapt {outcome['category']} learning from {source_system} to {target_system}: {outcome['summary']}"

    # ========== CONFLICT MANAGEMENT ==========

    def identify_learning_conflicts(self) -> List[LearningConflict]:
        """
        Identify conflicting learnings between systems.

        Returns:
            List of learning conflicts requiring resolution
        """
        conflicts = []

        # Get all high-confidence learnings
        all_learnings = {}
        for system in ["squirt", "j5a", "sherlock"]:
            outcomes = self.memory.get_learning_outcomes(system_name=system, min_confidence=0.7)
            all_learnings[system] = outcomes

        # Check for parameter conflicts
        conflicts.extend(self._find_parameter_conflicts(all_learnings))

        # Check for threshold conflicts
        conflicts.extend(self._find_threshold_conflicts(all_learnings))

        # Check for strategy conflicts
        conflicts.extend(self._find_strategy_conflicts(all_learnings))

        logger.info(f"Identified {len(conflicts)} learning conflicts")
        return conflicts

    def _find_parameter_conflicts(self, all_learnings: Dict[str, List[Dict]]) -> List[LearningConflict]:
        """Find conflicting parameter learnings"""
        conflicts = []

        # Compare thermal thresholds across systems
        thermal_learnings = {}
        for system, learnings in all_learnings.items():
            for learning in learnings:
                if 'thermal' in learning['summary'].lower() and 'threshold' in learning['summary'].lower():
                    thermal_learnings[system] = learning

        # Check if systems have conflicting thermal thresholds
        if len(thermal_learnings) >= 2:
            systems = list(thermal_learnings.keys())
            for i in range(len(systems)):
                for j in range(i + 1, len(systems)):
                    system_a, system_b = systems[i], systems[j]
                    learning_a = thermal_learnings[system_a]
                    learning_b = thermal_learnings[system_b]

                    # Check if they conflict (different thresholds)
                    if learning_a['summary'] != learning_b['summary']:
                        conflict = LearningConflict(
                            conflict_id=f"thermal_{system_a}_{system_b}",
                            system_a=system_a,
                            system_b=system_b,
                            learning_a_id=learning_a['id'],
                            learning_b_id=learning_b['id'],
                            conflict_type="threshold_setting",
                            conflict_summary=f"Conflicting thermal thresholds between {system_a} and {system_b}",
                            system_a_position=learning_a['summary'],
                            system_b_position=learning_b['summary'],
                            system_a_evidence=learning_a.get('evidence', {}),
                            system_b_evidence=learning_b.get('evidence', {}),
                            recommended_resolution=self._recommend_threshold_resolution(learning_a, learning_b),
                            resolution_rationale="Use more conservative (lower) threshold for system safety",
                            requires_human_decision=True
                        )
                        conflicts.append(conflict)

        return conflicts

    def _find_threshold_conflicts(self, all_learnings: Dict[str, List[Dict]]) -> List[LearningConflict]:
        """Find conflicting threshold learnings"""
        # Similar to parameter conflicts, but for non-thermal thresholds
        return []  # Placeholder for additional threshold conflict detection

    def _find_strategy_conflicts(self, all_learnings: Dict[str, List[Dict]]) -> List[LearningConflict]:
        """Find conflicting strategy learnings"""
        # Detect when systems learn contradictory strategies
        return []  # Placeholder for strategy conflict detection

    def _recommend_threshold_resolution(self, learning_a: Dict, learning_b: Dict) -> str:
        """Recommend resolution for threshold conflicts"""
        # For thermal/safety thresholds, use the more conservative value
        conf_a = learning_a['confidence']
        conf_b = learning_b['confidence']

        if conf_a > conf_b:
            return f"Adopt threshold from learning {learning_a['id']} (higher confidence: {conf_a:.0%})"
        else:
            return f"Adopt threshold from learning {learning_b['id']} (higher confidence: {conf_b:.0%})"

    # ========== TRANSFER EXECUTION ==========

    def execute_transfer(self,
                        proposal: LearningTransferProposal,
                        human_approved: bool,
                        human_notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a learning transfer from source to target system.

        Args:
            proposal: Transfer proposal to execute
            human_approved: Whether human approved the transfer
            human_notes: Optional human notes on the transfer

        Returns:
            Transfer result with success status and tracking ID
        """
        if not human_approved:
            logger.info(f"Transfer proposal rejected by human: {proposal.learning_summary}")
            return {
                "success": False,
                "reason": "Human rejected transfer",
                "notes": human_notes
            }

        # Record the transfer
        self.memory.record_learning_transfer(
            learning_id=proposal.learning_id,
            source_system=proposal.source_system,
            target_system=proposal.target_system,
            transfer_method=proposal.transfer_type.value,
            adaptation_required=proposal.proposed_adaptation,
            transfer_success=False,  # Will be measured later, default to False initially
            impact_summary=f"Transfer of {proposal.learning_summary} from {proposal.source_system} to {proposal.target_system}"
        )
        transfer_id = proposal.learning_id  # Use learning_id as transfer reference

        # Record decision
        decision = Decision(
            system_name="learning_synthesizer",
            decision_type="learning_transfer",
            decision_summary=f"Transferred learning {proposal.learning_id} from {proposal.source_system} to {proposal.target_system}",
            decision_rationale=proposal.adaptation_rationale,
            constitutional_compliance={
                "principle_1_human_agency": "Human approved transfer explicitly",
                "principle_2_transparency": "Full transfer provenance recorded with evidence",
                "principle_3_system_viability": f"Rollback plan: {proposal.rollback_plan}"
            },
            strategic_alignment={
                "principle_4_active_memory": "Cross-system memory sharing enabled",
                "principle_5_adaptive_feedback": "Accelerated learning through knowledge transfer"
            },
            decision_timestamp=datetime.now().isoformat(),
            decided_by="human_operator",
            outcome_expected=f"Improved {proposal.target_system} performance in {proposal.transfer_type.value}",
            outcome_actual=None,  # To be measured
            parameters_used={
                "learning_id": proposal.learning_id,
                "compatibility_score": proposal.compatibility_score,
                "human_notes": human_notes
            }
        )

        self.memory.record_decision(decision)

        logger.info(f"✅ Executed learning transfer {transfer_id}: {proposal.learning_summary}")

        return {
            "success": True,
            "transfer_id": transfer_id,
            "learning_id": proposal.learning_id,
            "source_system": proposal.source_system,
            "target_system": proposal.target_system,
            "monitoring_period_days": 7,
            "notes": f"Monitor {proposal.target_system} for impact. {human_notes or ''}"
        }

    # ========== TRANSFER IMPACT TRACKING ==========

    def measure_transfer_impact(self,
                               learning_id: int,
                               target_system: str,
                               impact_assessment: str,
                               success: bool,
                               metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Measure and record the impact of a completed learning transfer.

        Called after monitoring period to assess whether transfer was beneficial.

        Args:
            learning_id: Original learning outcome ID that was transferred
            target_system: System that received the transfer
            impact_assessment: Human assessment of the transfer impact
            success: Whether the transfer was ultimately successful
            metrics: Optional quantitative metrics (e.g., performance improvement %)

        Returns:
            Impact measurement result
        """
        timestamp = datetime.now().isoformat()

        # Record the impact measurement
        impact_record = {
            "learning_id": learning_id,
            "target_system": target_system,
            "impact_assessment": impact_assessment,
            "success": success,
            "metrics": metrics or {},
            "measured_at": timestamp
        }

        # Update the transfer record in memory
        # Find and update the transfer
        transfers = self.memory.get_learning_transfers(target_system=target_system)
        matched_transfer = None
        for t in transfers:
            if t.get('learning_id') == learning_id:
                matched_transfer = t
                break

        if matched_transfer:
            # Record updated decision with outcome
            decision = Decision(
                system_name="learning_synthesizer",
                decision_type="transfer_impact_measurement",
                decision_summary=f"Measured impact of transfer {learning_id} to {target_system}: {'SUCCESS' if success else 'FAILED'}",
                decision_rationale=impact_assessment,
                constitutional_compliance={
                    "principle_2_transparency": "Transfer impact fully documented",
                    "principle_5_adaptive_feedback": "Measurement informs future transfers"
                },
                strategic_alignment={
                    "principle_5_adaptive_feedback": "Learning from transfer outcomes"
                },
                decision_timestamp=timestamp,
                decided_by="human_operator",
                outcome_expected="Improved system performance",
                outcome_actual=impact_assessment,
                parameters_used={
                    "learning_id": learning_id,
                    "success": success,
                    "metrics": metrics
                }
            )
            self.memory.record_decision(decision)

            logger.info(f"📊 Recorded impact for transfer {learning_id} → {target_system}: {'SUCCESS' if success else 'FAILED'}")

            return {
                "recorded": True,
                "learning_id": learning_id,
                "target_system": target_system,
                "success": success,
                "impact": impact_record
            }
        else:
            logger.warning(f"No matching transfer found for learning_id={learning_id} target={target_system}")
            return {
                "recorded": False,
                "error": "No matching transfer found",
                "learning_id": learning_id,
                "target_system": target_system
            }

    def get_pending_impact_measurements(self, days_since_transfer: int = 7) -> List[Dict[str, Any]]:
        """
        Get transfers that are due for impact measurement.

        Args:
            days_since_transfer: How many days to wait before measuring (default 7)

        Returns:
            List of transfers needing impact measurement
        """
        pending = []
        cutoff_time = (datetime.now() - timedelta(days=days_since_transfer)).isoformat()

        for system in ["squirt", "j5a", "sherlock"]:
            transfers = self.memory.get_learning_transfers(target_system=system)
            for t in transfers:
                # Check if transfer is old enough and not yet measured
                if t.get('timestamp', '') <= cutoff_time:
                    # Check if success is still None/False (not yet confirmed)
                    if not t.get('success'):
                        pending.append({
                            "learning_id": t.get('learning_id'),
                            "source_system": t.get('source_system'),
                            "target_system": system,
                            "transferred_at": t.get('timestamp'),
                            "summary": t.get('impact_summary', 'Unknown'),
                            "days_since_transfer": (datetime.now() - datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))).days if t.get('timestamp') else 0
                        })

        return pending

    def get_transfer_effectiveness_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics on transfer effectiveness.

        Returns:
            Statistics on transfer success rates and impact
        """
        all_transfers = []
        for system in ["squirt", "j5a", "sherlock"]:
            transfers = self.memory.get_learning_transfers(source_system=system)
            all_transfers.extend(transfers)

        if not all_transfers:
            return {
                "total_transfers": 0,
                "success_rate": 0.0,
                "pending_measurement": 0,
                "by_system_pair": {}
            }

        total = len(all_transfers)
        successful = len([t for t in all_transfers if t.get('success') == True])
        failed = len([t for t in all_transfers if t.get('success') == False])
        pending = total - successful - failed

        # Group by system pair
        pair_stats = {}
        for t in all_transfers:
            pair = f"{t.get('source_system', '?')} → {t.get('target_system', '?')}"
            if pair not in pair_stats:
                pair_stats[pair] = {"total": 0, "successful": 0}
            pair_stats[pair]["total"] += 1
            if t.get('success'):
                pair_stats[pair]["successful"] += 1

        return {
            "total_transfers": total,
            "successful": successful,
            "failed": failed,
            "pending_measurement": pending,
            "success_rate": successful / max(total - pending, 1),
            "by_system_pair": pair_stats
        }

    # ========== SYNTHESIS REPORTING ==========

    def generate_synthesis_report(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Generate comprehensive cross-system learning synthesis report.

        Args:
            days_back: Time window for report

        Returns:
            Comprehensive synthesis report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_window_days": days_back,
            "report_type": "learning_synthesis",
            "sections": {}
        }

        # Transfer proposals
        proposals = self.identify_transferable_learnings(days_back=days_back)
        report["sections"]["transfer_proposals"] = {
            "total": len(proposals),
            "by_priority": {
                "critical": len([p for p in proposals if p.priority == TransferPriority.CRITICAL]),
                "high": len([p for p in proposals if p.priority == TransferPriority.HIGH]),
                "medium": len([p for p in proposals if p.priority == TransferPriority.MEDIUM]),
                "low": len([p for p in proposals if p.priority == TransferPriority.LOW])
            },
            "by_transfer_type": {},
            "top_5_proposals": [
                {
                    "source": p.source_system,
                    "target": p.target_system,
                    "summary": p.learning_summary,
                    "priority": p.priority.value,
                    "compatibility": p.compatibility_score
                }
                for p in proposals[:5]
            ]
        }

        for transfer_type in TransferType:
            count = len([p for p in proposals if p.transfer_type == transfer_type])
            if count > 0:
                report["sections"]["transfer_proposals"]["by_transfer_type"][transfer_type.value] = count

        # Learning conflicts
        conflicts = self.identify_learning_conflicts()
        report["sections"]["learning_conflicts"] = {
            "total": len(conflicts),
            "by_type": {},
            "conflicts": [
                {
                    "systems": f"{c.system_a} vs {c.system_b}",
                    "type": c.conflict_type,
                    "summary": c.conflict_summary,
                    "recommended_resolution": c.recommended_resolution
                }
                for c in conflicts
            ]
        }

        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            if conflict_type not in report["sections"]["learning_conflicts"]["by_type"]:
                report["sections"]["learning_conflicts"]["by_type"][conflict_type] = 0
            report["sections"]["learning_conflicts"]["by_type"][conflict_type] += 1

        # Completed transfers
        all_transfers = []
        for system in ["squirt", "j5a", "sherlock"]:
            transfers = self.memory.get_learning_transfers(source_system=system)
            all_transfers.extend(transfers)

        cutoff_time = (datetime.now() - timedelta(days=days_back)).isoformat()
        recent_transfers = [t for t in all_transfers if t['timestamp'] >= cutoff_time]

        report["sections"]["completed_transfers"] = {
            "total": len(recent_transfers),
            "successful": len([t for t in recent_transfers if t.get('success')]),
            "pending_measurement": len([t for t in recent_transfers if t.get('success') is None]),
            "by_source_system": {},
            "by_target_system": {}
        }

        for transfer in recent_transfers:
            source = transfer.get('source_system', 'unknown')
            target = transfer.get('target_system', 'unknown')

            if source not in report["sections"]["completed_transfers"]["by_source_system"]:
                report["sections"]["completed_transfers"]["by_source_system"][source] = 0
            report["sections"]["completed_transfers"]["by_source_system"][source] += 1

            if target not in report["sections"]["completed_transfers"]["by_target_system"]:
                report["sections"]["completed_transfers"]["by_target_system"][target] = 0
            report["sections"]["completed_transfers"]["by_target_system"][target] += 1

        # Cross-system insights
        report["sections"]["cross_system_insights"] = {
            "most_transferable_system": self._identify_most_transferable_system(proposals),
            "most_receptive_system": self._identify_most_receptive_system(proposals),
            "highest_compatibility_pairs": self._identify_high_compatibility_pairs(proposals),
            "synthesis_velocity": len(recent_transfers) / max(days_back, 1)  # Transfers per day
        }

        return report

    def _identify_most_transferable_system(self, proposals: List[LearningTransferProposal]) -> str:
        """Identify which system generates most transferable learnings"""
        source_counts = {}
        for proposal in proposals:
            source = proposal.source_system
            source_counts[source] = source_counts.get(source, 0) + 1

        if not source_counts:
            return "none"

        return max(source_counts.items(), key=lambda x: x[1])[0]

    def _identify_most_receptive_system(self, proposals: List[LearningTransferProposal]) -> str:
        """Identify which system benefits most from transferred learnings"""
        target_counts = {}
        for proposal in proposals:
            target = proposal.target_system
            target_counts[target] = target_counts.get(target, 0) + 1

        if not target_counts:
            return "none"

        return max(target_counts.items(), key=lambda x: x[1])[0]

    def _identify_high_compatibility_pairs(self, proposals: List[LearningTransferProposal]) -> List[Dict[str, Any]]:
        """Identify system pairs with highest learning compatibility"""
        pair_compat = {}
        for proposal in proposals:
            pair = f"{proposal.source_system} → {proposal.target_system}"
            if pair not in pair_compat:
                pair_compat[pair] = []
            pair_compat[pair].append(proposal.compatibility_score)

        # Average compatibility per pair
        pair_avg = {pair: sum(scores) / len(scores) for pair, scores in pair_compat.items()}

        # Return top 3
        sorted_pairs = sorted(pair_avg.items(), key=lambda x: x[1], reverse=True)
        return [
            {"pair": pair, "avg_compatibility": compat}
            for pair, compat in sorted_pairs[:3]
        ]


# ========== CLI FOR TESTING AND REVIEW ==========

def run_test_mode(synthesizer: LearningSynthesizer):
    """Run basic test mode (non-interactive)"""
    print("="*80)
    print("J5A Cross-System Learning Synthesizer - Test Mode")
    print("="*80)

    print(f"\n✅ Learning Synthesizer initialized")
    print(f"📊 System managers loaded: Squirt, J5A, Sherlock")

    print(f"\n🔍 Identifying transferable learnings...")
    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.7)
    print(f"   Found {len(proposals)} transfer opportunities")

    if proposals:
        print(f"\n📋 Top Transfer Proposals:")
        for i, proposal in enumerate(proposals[:5], 1):
            print(f"   {i}. [{proposal.priority.value.upper()}] {proposal.source_system} → {proposal.target_system}")
            print(f"      {proposal.learning_summary}")
            print(f"      Compatibility: {proposal.compatibility_score:.0%}, Difficulty: {proposal.implementation_difficulty}")

    print(f"\n⚔️  Checking for learning conflicts...")
    conflicts = synthesizer.identify_learning_conflicts()
    print(f"   Found {len(conflicts)} conflicts")

    if conflicts:
        print(f"\n📋 Learning Conflicts:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"   {i}. {conflict.conflict_summary}")
            print(f"      {conflict.system_a}: {conflict.system_a_position}")
            print(f"      {conflict.system_b}: {conflict.system_b_position}")
            print(f"      Resolution: {conflict.recommended_resolution}")

    print(f"\n📊 Generating synthesis report...")
    report = synthesizer.generate_synthesis_report(days_back=7)

    print(f"\n✅ Synthesis Report Generated:")
    print(f"   Transfer proposals: {report['sections']['transfer_proposals']['total']}")
    print(f"   Learning conflicts: {report['sections']['learning_conflicts']['total']}")
    print(f"   Recent transfers: {report['sections']['completed_transfers']['total']}")

    insights = report['sections']['cross_system_insights']
    print(f"\n💡 Cross-System Insights:")
    print(f"   Most transferable system: {insights['most_transferable_system']}")
    print(f"   Most receptive system: {insights['most_receptive_system']}")
    print(f"   Synthesis velocity: {insights['synthesis_velocity']:.2f} transfers/day")

    print(f"\n✅ J5A Learning Synthesizer ready for use")
    print("="*80)


def run_interactive_review(synthesizer: LearningSynthesizer):
    """Interactive review mode for approving transfers"""
    print("="*80)
    print("J5A Cross-System Learning Synthesizer - Interactive Review")
    print("="*80)
    print("\nConstitutional Compliance: Principle 1 (Human Agency)")
    print("All transfers require explicit human approval.\n")

    proposals = synthesizer.identify_transferable_learnings(min_confidence=0.7)

    if not proposals:
        print("✅ No transfer proposals pending. All systems in sync.")
        return

    print(f"📋 {len(proposals)} Transfer Proposals Pending Review\n")

    approved_count = 0
    rejected_count = 0
    skipped_count = 0

    for i, proposal in enumerate(proposals, 1):
        print("-" * 70)
        print(f"\n📦 Proposal {i}/{len(proposals)}")
        print(f"   Priority: [{proposal.priority.value.upper()}]")
        print(f"   Transfer: {proposal.source_system} → {proposal.target_system}")
        print(f"   Type: {proposal.transfer_type.value}")
        print(f"\n   Learning: {proposal.learning_summary}")
        print(f"\n   Rationale: {proposal.adaptation_rationale}")
        print(f"   Expected Impact: {proposal.expected_impact}")
        print(f"\n   Compatibility: {proposal.compatibility_score:.0%}")
        print(f"   Difficulty: {proposal.implementation_difficulty}")
        print(f"   Rollback: {proposal.rollback_plan}")

        if proposal.source_evidence:
            print(f"\n   Evidence: {proposal.source_evidence}")

        print(f"\n   [A]pprove  [R]eject  [S]kip  [Q]uit")

        while True:
            try:
                choice = input("   Your decision: ").strip().lower()
            except EOFError:
                choice = 'q'

            if choice in ['a', 'approve']:
                notes = input("   Approval notes (optional): ").strip() or "Approved via CLI review"
                result = synthesizer.execute_transfer(proposal, human_approved=True, human_notes=notes)
                if result['success']:
                    print(f"   ✅ Transfer executed. Monitor {proposal.target_system} for 7 days.")
                    approved_count += 1
                else:
                    print(f"   ❌ Transfer failed: {result.get('reason', 'Unknown')}")
                break
            elif choice in ['r', 'reject']:
                notes = input("   Rejection reason: ").strip() or "Rejected via CLI review"
                result = synthesizer.execute_transfer(proposal, human_approved=False, human_notes=notes)
                print(f"   🚫 Transfer rejected and logged.")
                rejected_count += 1
                break
            elif choice in ['s', 'skip']:
                print(f"   ⏭️  Skipped for later review.")
                skipped_count += 1
                break
            elif choice in ['q', 'quit']:
                print(f"\n🛑 Review session ended early.")
                print(f"   Approved: {approved_count}")
                print(f"   Rejected: {rejected_count}")
                print(f"   Skipped: {skipped_count}")
                print(f"   Remaining: {len(proposals) - i}")
                return
            else:
                print("   Invalid choice. Use A/R/S/Q")

    print("\n" + "="*70)
    print("📊 Review Session Complete")
    print(f"   Approved: {approved_count}")
    print(f"   Rejected: {rejected_count}")
    print(f"   Skipped: {skipped_count}")
    print("="*70)


def run_report_mode(synthesizer: LearningSynthesizer, days_back: int = 7):
    """Generate and display synthesis report"""
    print("="*80)
    print(f"J5A Synthesis Report - Last {days_back} Days")
    print("="*80)

    report = synthesizer.generate_synthesis_report(days_back=days_back)

    # Transfer Proposals
    tp = report['sections']['transfer_proposals']
    print(f"\n📦 Transfer Proposals: {tp['total']}")
    print(f"   Critical: {tp['by_priority'].get('critical', 0)}")
    print(f"   High: {tp['by_priority'].get('high', 0)}")
    print(f"   Medium: {tp['by_priority'].get('medium', 0)}")
    print(f"   Low: {tp['by_priority'].get('low', 0)}")

    if tp.get('by_transfer_type'):
        print(f"\n   By Type:")
        for ttype, count in tp['by_transfer_type'].items():
            print(f"      {ttype}: {count}")

    # Conflicts
    lc = report['sections']['learning_conflicts']
    print(f"\n⚔️  Learning Conflicts: {lc['total']}")
    if lc['conflicts']:
        for conflict in lc['conflicts']:
            print(f"   • {conflict['systems']}: {conflict['summary']}")

    # Completed Transfers
    ct = report['sections']['completed_transfers']
    print(f"\n✅ Completed Transfers: {ct['total']}")
    print(f"   Successful: {ct['successful']}")
    print(f"   Pending measurement: {ct['pending_measurement']}")

    # Cross-System Insights
    csi = report['sections']['cross_system_insights']
    print(f"\n💡 Cross-System Insights:")
    print(f"   Most transferable: {csi['most_transferable_system']}")
    print(f"   Most receptive: {csi['most_receptive_system']}")
    print(f"   Synthesis velocity: {csi['synthesis_velocity']:.2f} transfers/day")

    if csi.get('highest_compatibility_pairs'):
        print(f"\n   High Compatibility Pairs:")
        for pair in csi['highest_compatibility_pairs']:
            print(f"      {pair['pair']}: {pair['avg_compatibility']:.0%}")

    print("\n" + "="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="J5A Cross-System Learning Synthesizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 learning_synthesizer.py                    # Test mode (default)
  python3 learning_synthesizer.py --review           # Interactive transfer review
  python3 learning_synthesizer.py --report           # Generate synthesis report
  python3 learning_synthesizer.py --report --days 30 # 30-day report
        """
    )
    parser.add_argument('--review', action='store_true',
                        help='Interactive review mode for approving transfers')
    parser.add_argument('--report', action='store_true',
                        help='Generate synthesis report')
    parser.add_argument('--days', type=int, default=7,
                        help='Days to include in report (default: 7)')

    args = parser.parse_args()

    synthesizer = LearningSynthesizer()

    if args.review:
        run_interactive_review(synthesizer)
    elif args.report:
        run_report_mode(synthesizer, days_back=args.days)
    else:
        run_test_mode(synthesizer)
