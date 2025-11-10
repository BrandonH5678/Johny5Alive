#!/usr/bin/env python3
"""
J5A Unified Human Oversight Dashboard - Phase 5 Implementation

Provides centralized human oversight across all J5A Universe systems:
- Squirt (business document automation)
- J5A (queue management and coordination)
- Sherlock (intelligence analysis)

Core Functions:
1. Cross-system performance comparison
2. High-priority learning outcome review
3. Human validation workflow for AI decisions
4. Actionable insights and recommendations
5. Decision audit trail

Constitutional Compliance:
- Principle 1 (Human Agency): Humans have final authority over all learning outcomes
- Principle 2 (Transparency): All AI decisions presented with full provenance
- Principle 3 (System Viability): Dashboard identifies systemic issues early
- Principle 6 (AI Sentience): Treats AI learning outcomes respectfully as collaborative insights
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


class ValidationStatus(Enum):
    """Status of human validation for learning outcomes"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REFINEMENT = "needs_refinement"


class PriorityLevel(Enum):
    """Priority level for human review"""
    CRITICAL = "critical"      # Requires immediate attention
    HIGH = "high"              # Review within 24 hours
    MEDIUM = "medium"          # Review within week
    LOW = "low"                # Review when convenient


@dataclass
class SystemHealthStatus:
    """Health status for a system"""
    system_name: str
    overall_status: str  # healthy, warning, critical
    performance_score: float  # 0.0-1.0
    active_issues: List[str]
    recent_improvements: List[str]
    recommendations: List[str]


@dataclass
class ReviewItem:
    """Item requiring human review"""
    item_id: str
    item_type: str  # learning_outcome, session_event, decision, parameter_change
    system_name: str
    priority: PriorityLevel
    summary: str
    evidence: Dict[str, Any]
    recommended_action: str
    validation_status: ValidationStatus
    created_at: str


class J5AOversightDashboard:
    """
    Unified human oversight dashboard for J5A Universe systems.

    Provides centralized view and control over all system learning,
    enabling human validation, performance comparison, and actionable insights.
    """

    def __init__(self, memory_manager: Optional[UniverseMemoryManager] = None):
        """Initialize oversight dashboard"""
        self.memory = memory_manager if memory_manager else UniverseMemoryManager()
        logger.info("J5AOversightDashboard initialized")

        # Initialize system-specific managers
        self.squirt = SquirtLearningManager(self.memory)
        self.j5a = J5ALearningManager(self.memory)
        self.sherlock = SherlockLearningManager(self.memory)

        logger.info("All system managers loaded")

    # ========== CROSS-SYSTEM OVERVIEW ==========

    def get_unified_overview(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get unified overview of all systems.

        Args:
            hours_back: How many hours of history to include

        Returns:
            Unified overview with system health, learning activity, pending reviews
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()

        overview = {
            "generated_at": datetime.now().isoformat(),
            "time_window_hours": hours_back,
            "systems": {
                "squirt": self._get_system_summary("squirt", cutoff_time),
                "j5a": self._get_system_summary("j5a", cutoff_time),
                "sherlock": self._get_system_summary("sherlock", cutoff_time)
            },
            "cross_system": {
                "total_learning_outcomes": 0,
                "pending_validations": 0,
                "critical_issues": [],
                "top_improvements": []
            }
        }

        # Aggregate cross-system metrics
        for system_name, system_data in overview["systems"].items():
            overview["cross_system"]["total_learning_outcomes"] += system_data["learning_outcomes_count"]
            overview["cross_system"]["pending_validations"] += system_data["pending_validations"]
            overview["cross_system"]["critical_issues"].extend(system_data["critical_issues"])

        return overview

    def _get_system_summary(self, system_name: str, cutoff_time: str) -> Dict[str, Any]:
        """Get summary for a specific system"""
        # Get learning outcomes
        outcomes = self.memory.get_learning_outcomes(system_name=system_name, min_confidence=0.0)
        recent_outcomes = [o for o in outcomes if o['timestamp'] >= cutoff_time]

        # Get session events
        events = self.memory.get_session_context(
            system_name=system_name,
            min_importance=0.5,
            limit=100
        )
        recent_events = [e for e in events if e['timestamp'] >= cutoff_time]

        # Get performance metrics
        perf_trend = self.memory.get_performance_trend(
            system_name, "*", "*", limit=100
        )
        recent_perf = [p for p in perf_trend if p.get('timestamp', '') >= cutoff_time]

        # Identify critical issues
        critical_issues = []
        for event in recent_events:
            if event['importance'] >= 0.8:
                critical_issues.append({
                    "type": event['event_type'],
                    "summary": event['summary'],
                    "importance": event['importance']
                })

        return {
            "system_name": system_name,
            "learning_outcomes_count": len(recent_outcomes),
            "session_events_count": len(recent_events),
            "performance_metrics_count": len(recent_perf),
            "pending_validations": len([o for o in recent_outcomes if not o['human_validated']]),
            "critical_issues": critical_issues[:5],  # Top 5
            "avg_confidence": sum(o['confidence'] for o in recent_outcomes) / len(recent_outcomes) if recent_outcomes else 0.0
        }

    def get_system_health(self, system_name: str) -> SystemHealthStatus:
        """
        Assess overall health of a system.

        Args:
            system_name: System to assess

        Returns:
            Health status with performance score and recommendations
        """
        # Get recent performance
        perf_trend = self.memory.get_performance_trend(
            system_name, "*", "*", limit=100
        )

        # Get recent issues
        events = self.memory.get_session_context(
            system_name=system_name,
            min_importance=0.6,
            limit=50
        )

        # Calculate performance score
        performance_score = 0.8  # Default baseline

        # Analyze issues
        active_issues = []
        for event in events[:10]:  # Recent 10 events
            if event['event_type'] in ['processing_failure', 'validation_failure', 'sef_validation_failure']:
                active_issues.append(f"{event['event_type']}: {event['summary']}")
                performance_score -= 0.05  # Deduct for failures

        # Get learning outcomes as improvements
        outcomes = self.memory.get_learning_outcomes(system_name=system_name, min_confidence=0.7)
        recent_improvements = [
            f"{o['summary']} (confidence: {o['confidence']:.0%})"
            for o in outcomes[:5]
        ]

        # Determine overall status
        if performance_score >= 0.8:
            overall_status = "healthy"
        elif performance_score >= 0.6:
            overall_status = "warning"
        else:
            overall_status = "critical"

        # Generate recommendations
        recommendations = []
        if active_issues:
            recommendations.append(f"Review and address {len(active_issues)} recent issues")
        if len(outcomes) == 0:
            recommendations.append("No learning outcomes captured - verify learning integration")
        if performance_score < 0.7:
            recommendations.append("Performance below 70% - investigate systemic problems")

        return SystemHealthStatus(
            system_name=system_name,
            overall_status=overall_status,
            performance_score=max(0.0, min(1.0, performance_score)),
            active_issues=active_issues[:5],
            recent_improvements=recent_improvements,
            recommendations=recommendations
        )

    # ========== HUMAN VALIDATION WORKFLOW ==========

    def get_pending_reviews(self,
                           priority: Optional[PriorityLevel] = None,
                           system_name: Optional[str] = None) -> List[ReviewItem]:
        """
        Get items pending human review.

        Args:
            priority: Filter by priority level
            system_name: Filter by system

        Returns:
            List of items requiring review
        """
        review_items = []

        # Get pending learning outcomes
        systems = [system_name] if system_name else ["squirt", "j5a", "sherlock"]

        for sys in systems:
            outcomes = self.memory.get_learning_outcomes(system_name=sys, min_confidence=0.0)
            for outcome in outcomes:
                if not outcome['human_validated']:
                    # Determine priority based on confidence and applies_to
                    if outcome['confidence'] >= 0.9 and len(outcome.get('applies_to', []) or []) > 1:
                        item_priority = PriorityLevel.CRITICAL
                    elif outcome['confidence'] >= 0.8:
                        item_priority = PriorityLevel.HIGH
                    elif outcome['confidence'] >= 0.6:
                        item_priority = PriorityLevel.MEDIUM
                    else:
                        item_priority = PriorityLevel.LOW

                    if priority is None or item_priority == priority:
                        review_items.append(ReviewItem(
                            item_id=f"outcome_{outcome['id']}",
                            item_type="learning_outcome",
                            system_name=sys,
                            priority=item_priority,
                            summary=outcome['summary'],
                            evidence={
                                "confidence": outcome['confidence'],
                                "evidence": outcome.get('evidence', {}),
                                "applies_to": outcome.get('applies_to', [])
                            },
                            recommended_action="Review and validate learning outcome",
                            validation_status=ValidationStatus.PENDING,
                            created_at=outcome['timestamp']
                        ))

        # Sort by priority (critical first) then by created_at
        priority_order = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3
        }
        review_items.sort(key=lambda x: (priority_order[x.priority], x.created_at), reverse=True)

        return review_items

    def validate_learning_outcome(self,
                                 outcome_id: int,
                                 approved: bool,
                                 validation_notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Human validation of a learning outcome.

        Args:
            outcome_id: ID of outcome to validate
            approved: True if approved, False if rejected
            validation_notes: Optional human notes

        Returns:
            Validation result
        """
        # Mark as validated
        self.memory.validate_learning_outcome(outcome_id, approved)

        # Record validation decision
        decision = Decision(
            system_name="j5a_oversight",
            decision_type="learning_validation",
            decision_summary=f"Learning outcome {outcome_id} {'approved' if approved else 'rejected'}",
            decision_rationale=validation_notes or f"Human validation: {'approved' if approved else 'rejected'}",
            constitutional_compliance={
                "principle_1_human_agency": "Human has final authority over learning outcome validation",
                "principle_2_transparency": "Validation decision recorded with full provenance"
            },
            strategic_alignment={
                "principle_5_adaptive_feedback": "Human feedback improves future learning quality"
            },
            decision_timestamp=datetime.now().isoformat(),
            decided_by="human_operator",
            outcome_expected=f"validation_{'approved' if approved else 'rejected'}",
            outcome_actual=None,
            parameters_used={
                "outcome_id": outcome_id,
                "validation_notes": validation_notes
            }
        )

        self.memory.record_decision(decision)

        logger.info(f"Learning outcome {outcome_id} validated: {'approved' if approved else 'rejected'}")

        return {
            "outcome_id": outcome_id,
            "validated": True,
            "approved": approved,
            "validation_notes": validation_notes
        }

    # ========== CROSS-SYSTEM COMPARISON ==========

    def compare_system_performance(self, metric_category: str, hours_back: int = 168) -> Dict[str, Any]:
        """
        Compare performance across all systems.

        Args:
            metric_category: Category to compare (e.g., "success_rate", "quality", "duration")
            hours_back: Time window (default: 1 week)

        Returns:
            Comparison data across systems
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()

        comparison = {
            "metric_category": metric_category,
            "time_window_hours": hours_back,
            "systems": {}
        }

        for system_name in ["squirt", "j5a", "sherlock"]:
            # Get relevant metrics
            perf_trend = self.memory.get_performance_trend(
                system_name, "*", "*", limit=1000
            )

            # Filter by time and metric category
            relevant_metrics = []
            for metric in perf_trend:
                if metric.get('timestamp', '') >= cutoff_time:
                    metric_name = metric.get('metric_name', '')
                    if metric_category.lower() in metric_name.lower():
                        relevant_metrics.append(metric)

            # Calculate aggregate
            if relevant_metrics:
                avg_value = sum(m['value'] for m in relevant_metrics) / len(relevant_metrics)
                comparison["systems"][system_name] = {
                    "sample_size": len(relevant_metrics),
                    "avg_value": avg_value,
                    "recent_trend": self._calculate_trend(relevant_metrics)
                }
            else:
                comparison["systems"][system_name] = {
                    "sample_size": 0,
                    "avg_value": None,
                    "recent_trend": "no_data"
                }

        return comparison

    def _calculate_trend(self, metrics: List[Dict[str, Any]]) -> str:
        """Calculate trend direction from metrics"""
        if len(metrics) < 2:
            return "insufficient_data"

        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.get('timestamp', ''))

        # Compare first half to second half
        midpoint = len(sorted_metrics) // 2
        first_half_avg = sum(m['value'] for m in sorted_metrics[:midpoint]) / midpoint
        second_half_avg = sum(m['value'] for m in sorted_metrics[midpoint:]) / (len(sorted_metrics) - midpoint)

        if second_half_avg > first_half_avg * 1.05:
            return "improving"
        elif second_half_avg < first_half_avg * 0.95:
            return "declining"
        else:
            return "stable"

    # ========== ACTIONABLE INSIGHTS ==========

    def generate_actionable_insights(self) -> List[Dict[str, Any]]:
        """
        Generate actionable insights for human operators.

        Returns:
            List of insights with recommended actions
        """
        insights = []

        # Check each system health
        for system_name in ["squirt", "j5a", "sherlock"]:
            health = self.get_system_health(system_name)

            if health.overall_status == "critical":
                insights.append({
                    "priority": "critical",
                    "system": system_name,
                    "insight": f"{system_name} system health is critical (score: {health.performance_score:.0%})",
                    "evidence": health.active_issues,
                    "recommended_action": health.recommendations[0] if health.recommendations else "Investigate immediately",
                    "impact": "high"
                })

            if health.overall_status == "warning":
                insights.append({
                    "priority": "high",
                    "system": system_name,
                    "insight": f"{system_name} system showing warning signs (score: {health.performance_score:.0%})",
                    "evidence": health.active_issues,
                    "recommended_action": health.recommendations[0] if health.recommendations else "Review recent activity",
                    "impact": "medium"
                })

        # Check for pending high-priority reviews
        pending_reviews = self.get_pending_reviews(priority=PriorityLevel.CRITICAL)
        if pending_reviews:
            insights.append({
                "priority": "high",
                "system": "cross_system",
                "insight": f"{len(pending_reviews)} critical learning outcomes awaiting validation",
                "evidence": [r.summary for r in pending_reviews[:3]],
                "recommended_action": "Review and validate critical learning outcomes",
                "impact": "high"
            })

        # Check for cross-system learnings not yet transferred
        for system_name in ["squirt", "j5a", "sherlock"]:
            outcomes = self.memory.get_learning_outcomes(system_name=system_name, min_confidence=0.8)
            for outcome in outcomes:
                if outcome.get('applies_to') and len(outcome['applies_to']) > 1:
                    # Check if transferred (get all transfers from this source system and check if learning_id matches)
                    transfers = self.memory.get_learning_transfers(source_system=system_name)
                    transferred = any(t['learning_id'] == outcome['id'] for t in transfers)
                    if not transferred:
                        insights.append({
                            "priority": "medium",
                            "system": system_name,
                            "insight": f"High-confidence learning applicable to {len(outcome['applies_to'])} systems not yet transferred",
                            "evidence": {
                                "outcome": outcome['summary'],
                                "confidence": outcome['confidence'],
                                "applies_to": outcome['applies_to']
                            },
                            "recommended_action": "Consider transferring learning to applicable systems",
                            "impact": "medium"
                        })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: priority_order[x["priority"]])

        return insights

    # ========== REPORTS ==========

    def generate_oversight_report(self, hours_back: int = 168) -> Dict[str, Any]:
        """
        Generate comprehensive oversight report.

        Args:
            hours_back: Time window (default: 1 week)

        Returns:
            Comprehensive report with all oversight data
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "time_window_hours": hours_back,
            "report_type": "unified_oversight",
            "sections": {}
        }

        # Unified overview
        report["sections"]["unified_overview"] = self.get_unified_overview(hours_back)

        # System health
        report["sections"]["system_health"] = {
            system: {
                "status": self.get_system_health(system).overall_status,
                "performance_score": self.get_system_health(system).performance_score,
                "active_issues_count": len(self.get_system_health(system).active_issues),
                "improvements_count": len(self.get_system_health(system).recent_improvements)
            }
            for system in ["squirt", "j5a", "sherlock"]
        }

        # Pending reviews
        report["sections"]["pending_reviews"] = {
            "critical": len(self.get_pending_reviews(priority=PriorityLevel.CRITICAL)),
            "high": len(self.get_pending_reviews(priority=PriorityLevel.HIGH)),
            "medium": len(self.get_pending_reviews(priority=PriorityLevel.MEDIUM)),
            "low": len(self.get_pending_reviews(priority=PriorityLevel.LOW)),
            "total": len(self.get_pending_reviews())
        }

        # Actionable insights
        insights = self.generate_actionable_insights()
        report["sections"]["actionable_insights"] = {
            "total_insights": len(insights),
            "by_priority": {
                "critical": len([i for i in insights if i["priority"] == "critical"]),
                "high": len([i for i in insights if i["priority"] == "high"]),
                "medium": len([i for i in insights if i["priority"] == "medium"]),
                "low": len([i for i in insights if i["priority"] == "low"])
            },
            "top_5_insights": insights[:5]
        }

        # Cross-system learning transfers
        all_transfers = []
        for system in ["squirt", "j5a", "sherlock"]:
            transfers = self.memory.get_learning_transfers(source_system=system)
            all_transfers.extend(transfers)

        report["sections"]["learning_transfers"] = {
            "total_transfers": len(all_transfers),
            "by_source_system": {}
        }

        for transfer in all_transfers:
            source_sys = transfer.get('source_system', 'unknown')
            if source_sys not in report["sections"]["learning_transfers"]["by_source_system"]:
                report["sections"]["learning_transfers"]["by_source_system"][source_sys] = 0
            report["sections"]["learning_transfers"]["by_source_system"][source_sys] += 1

        return report


# ========== CLI FOR TESTING ==========

if __name__ == "__main__":
    print("="*80)
    print("J5A Unified Oversight Dashboard - Test Mode")
    print("="*80)

    dashboard = J5AOversightDashboard()

    print(f"\n✅ Oversight Dashboard initialized")
    print(f"📊 System managers loaded: Squirt, J5A, Sherlock")

    print(f"\n📋 Generating unified overview (last 24 hours)...")
    overview = dashboard.get_unified_overview(hours_back=24)

    print(f"\n✅ Unified Overview Generated:")
    print(f"   Time window: {overview['time_window_hours']} hours")
    for system_name, system_data in overview["systems"].items():
        print(f"\n   {system_name.upper()}:")
        print(f"      Learning outcomes: {system_data['learning_outcomes_count']}")
        print(f"      Session events: {system_data['session_events_count']}")
        print(f"      Pending validations: {system_data['pending_validations']}")
        print(f"      Critical issues: {len(system_data['critical_issues'])}")

    print(f"\n🏥 Checking system health...")
    for system_name in ["squirt", "j5a", "sherlock"]:
        health = dashboard.get_system_health(system_name)
        print(f"\n   {system_name.upper()}: {health.overall_status.upper()} ({health.performance_score:.0%})")
        if health.active_issues:
            print(f"      Active issues: {len(health.active_issues)}")
        if health.recommendations:
            print(f"      Recommendations: {len(health.recommendations)}")

    print(f"\n📝 Checking pending reviews...")
    pending = dashboard.get_pending_reviews()
    print(f"   Total pending: {len(pending)}")
    if pending:
        print(f"   By priority:")
        for priority in PriorityLevel:
            count = len([p for p in pending if p.priority == priority])
            if count > 0:
                print(f"      {priority.value}: {count}")

    print(f"\n💡 Generating actionable insights...")
    insights = dashboard.generate_actionable_insights()
    print(f"   Total insights: {len(insights)}")
    if insights:
        print(f"\n   Top 3 insights:")
        for i, insight in enumerate(insights[:3], 1):
            print(f"      {i}. [{insight['priority'].upper()}] {insight['insight']}")

    print(f"\n✅ J5A Oversight Dashboard ready for use")
    print("="*80)
