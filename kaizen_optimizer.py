#!/usr/bin/env python3
"""
Kaizen Continuous Improvement Framework - Universal J5A Implementation

Purpose: System-agnostic statistical optimization across all J5A systems
Architecture: Plugin-based improvement analysis with extensible targets
Created: 2025-11-04

Mission: Make working systems work BETTER through data-driven refinement
Philosophy: Small, incremental, statistically-validated improvements

改善 (Kaizen) = "Change for better" through continuous small improvements

Integration Points:
- Squirt: Template optimization, AAR-driven estimation refinement
- Sherlock: Transcript quality optimization, intelligence extraction tuning
- J5A: Queue management optimization, resource allocation tuning
- Context-Refresh: Validation question refinement, tier requirement optimization

Constitutional Alignment:
- Principle 3 (System Viability): Cautious optimization, don't break what works
- Principle 5 (Adaptive Feedback): Continuous learning from every operation
- Principle 8 (Strategic AI Literacy): Treat AI as collaborator to understand and train
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import statistics

# Database paths (J5A root level)
KAIZEN_DB = Path(__file__).parent / "kaizen_improvements.db"


class ImprovementStage(Enum):
    """Kaizen improvement pipeline stages"""
    MEASURE = "measure"  # Collect metrics from operational data
    ANALYZE = "analyze"  # Identify patterns and opportunities
    IMPROVE = "improve"  # Design and test improvement
    VALIDATE = "validate"  # Statistical significance testing
    REFINE = "refine"  # Deploy validated improvement


class ImprovementStatus(Enum):
    """Status of improvement proposals"""
    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    REJECTED = "rejected"


class ImprovementTarget(Enum):
    """System-specific improvement targets"""
    # Context-refresh targets
    CONTEXT_REFRESH_VALIDATION_QUESTIONS = "context_refresh_validation_questions"
    CONTEXT_REFRESH_TIER_REQUIREMENTS = "context_refresh_tier_requirements"
    CONTEXT_REFRESH_DOCUMENT_LOADING = "context_refresh_document_loading"

    # Squirt targets
    SQUIRT_TEMPLATE_ESTIMATION = "squirt_template_estimation"
    SQUIRT_MATERIAL_BUFFERS = "squirt_material_buffers"
    SQUIRT_LABOR_RATES = "squirt_labor_rates"
    SQUIRT_VOICE_PROCESSING = "squirt_voice_processing"

    # Sherlock targets
    SHERLOCK_TRANSCRIPT_QUALITY = "sherlock_transcript_quality"
    SHERLOCK_INTELLIGENCE_EXTRACTION = "sherlock_intelligence_extraction"
    SHERLOCK_DIARIZATION_ACCURACY = "sherlock_diarization_accuracy"

    # J5A targets
    J5A_QUEUE_PRIORITIZATION = "j5a_queue_prioritization"
    J5A_RESOURCE_ALLOCATION = "j5a_resource_allocation"
    J5A_CROSS_SYSTEM_COORDINATION = "j5a_cross_system_coordination"


@dataclass
class Pattern:
    """Detected pattern from operational data"""
    pattern_id: str
    system: str  # squirt, sherlock, j5a, context-refresh
    target: ImprovementTarget
    category: str  # varies by system
    item_name: str
    sample_size: int
    metric_value: float  # variance, accuracy, latency, etc.
    confidence_interval: Tuple[float, float]
    significance: str  # high, medium, low
    actionable: bool
    suggested_improvement: Optional[str] = None
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ImprovementProposal:
    """Proposed system improvement"""
    proposal_id: str
    pattern_id: str
    system: str
    target: ImprovementTarget
    improvement_type: str  # question_refinement, tier_adjustment, buffer_increase, etc.
    current_state: str
    proposed_change: str
    expected_impact: str
    confidence_level: float
    status: ImprovementStatus
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validation_result: Optional[Dict] = None
    deployment_notes: Optional[str] = None


class KaizenOptimizer:
    """
    Universal Kaizen Continuous Improvement Framework

    PDCA Cycle Implementation:
    1. MEASURE: Query operational databases for patterns
    2. ANALYZE: Identify optimization opportunities
    3. IMPROVE: Propose refinements, design tests
    4. VALIDATE: Statistical significance or expert review
    5. REFINE: Deploy validated improvements

    Plugin Architecture:
    - Systems register improvement targets and analysis functions
    - Shared database enables cross-system learning
    - Human-in-the-loop approval for all deployments
    """

    def __init__(self, kaizen_db_path: Path = KAIZEN_DB):
        """Initialize Kaizen optimizer"""
        self.kaizen_db_path = kaizen_db_path
        self.kaizen_conn = None
        self._connect_database()
        self._ensure_kaizen_schema()

    def _connect_database(self):
        """Connect to Kaizen database"""
        self.kaizen_conn = sqlite3.connect(str(self.kaizen_db_path))
        print(f"✅ Connected to Kaizen database: {self.kaizen_db_path}")

    def _ensure_kaizen_schema(self):
        """Create Kaizen database schema if not exists"""
        cursor = self.kaizen_conn.cursor()

        # Detected patterns table (system-agnostic)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kaizen_patterns (
                pattern_id TEXT PRIMARY KEY,
                system TEXT NOT NULL,
                target TEXT NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                sample_size INTEGER,
                metric_value REAL,
                confidence_interval_lower REAL,
                confidence_interval_upper REAL,
                significance TEXT,
                actionable BOOLEAN,
                suggested_improvement TEXT,
                detected_at TEXT NOT NULL,
                last_updated TEXT
            )
        """)

        # Improvement proposals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kaizen_improvement_proposals (
                proposal_id TEXT PRIMARY KEY,
                pattern_id TEXT NOT NULL,
                system TEXT NOT NULL,
                target TEXT NOT NULL,
                improvement_type TEXT NOT NULL,
                current_state TEXT,
                proposed_change TEXT,
                expected_impact TEXT,
                confidence_level REAL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                validation_result TEXT,
                deployment_notes TEXT,
                FOREIGN KEY (pattern_id) REFERENCES kaizen_patterns(pattern_id)
            )
        """)

        # Deployed improvements tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kaizen_deployed_improvements (
                deployment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                deployed_at TEXT NOT NULL,
                pre_deployment_metric REAL,
                post_deployment_metric REAL,
                sustained_improvement BOOLEAN,
                rollback_date TEXT,
                notes TEXT,
                FOREIGN KEY (proposal_id) REFERENCES kaizen_improvement_proposals(proposal_id)
            )
        """)

        # Context refresh specific optimization tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kaizen_context_refresh_optimization (
                optimization_id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                question_number INTEGER,
                original_question TEXT,
                refined_question TEXT,
                original_pass_rate REAL,
                improved_pass_rate REAL,
                deployed BOOLEAN DEFAULT 0,
                deployed_at TEXT,
                FOREIGN KEY (proposal_id) REFERENCES kaizen_improvement_proposals(proposal_id)
            )
        """)

        self.kaizen_conn.commit()

    # =========================================================================
    # Context Refresh Optimization (Core Universal Target)
    # =========================================================================

    def analyze_context_refresh_validation(
        self,
        phoenix_db_path: Path
    ) -> List[Pattern]:
        """
        Analyze context refresh validation results from Phoenix database

        Identifies:
        - Questions with low pass rates (need refinement)
        - Refresh tiers that are insufficient for certain scenarios
        - Compaction patterns that require different tier defaults
        """
        patterns = []

        # Connect to Phoenix database to query validation results
        phoenix_conn = sqlite3.connect(str(phoenix_db_path))
        cursor = phoenix_conn.cursor()

        # Analyze question-by-question pass rates
        for q_num in range(1, 10):
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN {f'q{q_num}_result'} LIKE '%pass%' THEN 1 ELSE 0 END) as passes
                FROM phoenix_context_refresh_validations
                WHERE timestamp > datetime('now', '-30 days')
            """)

            result = cursor.fetchone()
            if result and result[0] > 0:
                total, passes = result
                pass_rate = (passes / total) * 100

                if pass_rate < 80:  # Question needs refinement
                    pattern_id = f"CTX_REFRESH_Q{q_num}_{int(datetime.now().timestamp())}"

                    patterns.append(Pattern(
                        pattern_id=pattern_id,
                        system="context-refresh",
                        target=ImprovementTarget.CONTEXT_REFRESH_VALIDATION_QUESTIONS,
                        category="validation_question",
                        item_name=f"question_{q_num}",
                        sample_size=total,
                        metric_value=pass_rate,
                        confidence_interval=(pass_rate - 10, pass_rate + 10),  # Simplified
                        significance="high" if pass_rate < 60 else "medium",
                        actionable=True,
                        suggested_improvement=f"Refine question {q_num} - current pass rate {pass_rate:.1f}% below 80% threshold"
                    ))

        # Analyze tier sufficiency by compaction status
        cursor.execute("""
            SELECT
                tier_used,
                compaction_occurred,
                COUNT(*) as total,
                SUM(CASE WHEN CAST(SUBSTR(score, 1, 1) AS INTEGER) >= 7 THEN 1 ELSE 0 END) as passed
            FROM phoenix_context_refresh_validations
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY tier_used, compaction_occurred
        """)

        for row in cursor.fetchall():
            tier, compaction, total, passed = row
            pass_rate = (passed / total * 100) if total > 0 else 0

            if pass_rate < 85:  # Tier insufficient
                pattern_id = f"CTX_REFRESH_TIER_{tier}_COMP{1 if compaction else 0}_{int(datetime.now().timestamp())}"

                patterns.append(Pattern(
                    pattern_id=pattern_id,
                    system="context-refresh",
                    target=ImprovementTarget.CONTEXT_REFRESH_TIER_REQUIREMENTS,
                    category="tier_sufficiency",
                    item_name=f"tier_{tier}_compaction_{compaction}",
                    sample_size=total,
                    metric_value=pass_rate,
                    confidence_interval=(pass_rate - 10, pass_rate + 10),
                    significance="high" if pass_rate < 70 else "medium",
                    actionable=True,
                    suggested_improvement=f"Tier {tier} insufficient after compaction={compaction}: {pass_rate:.1f}% pass rate"
                ))

        phoenix_conn.close()

        # Save patterns
        for pattern in patterns:
            self._save_pattern(pattern)

        print(f"\n📊 Context Refresh Analysis: Detected {len(patterns)} patterns")
        return patterns

    def _save_pattern(self, pattern: Pattern):
        """Save detected pattern to database"""
        cursor = self.kaizen_conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO kaizen_patterns (
                pattern_id, system, target, category, item_name, sample_size,
                metric_value, confidence_interval_lower, confidence_interval_upper,
                significance, actionable, suggested_improvement, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.system,
            pattern.target.value,
            pattern.category,
            pattern.item_name,
            pattern.sample_size,
            pattern.metric_value,
            pattern.confidence_interval[0],
            pattern.confidence_interval[1],
            pattern.significance,
            pattern.actionable,
            pattern.suggested_improvement,
            pattern.detected_at
        ))

        self.kaizen_conn.commit()

    # =========================================================================
    # Improvement Proposal Generation
    # =========================================================================

    def generate_proposals(
        self,
        patterns: List[Pattern]
    ) -> List[ImprovementProposal]:
        """
        Generate improvement proposals from detected patterns

        Args:
            patterns: List of detected patterns

        Returns:
            List of improvement proposals for human review
        """
        proposals = []

        for pattern in patterns:
            if not pattern.actionable:
                continue

            # Generate proposal based on target type
            if pattern.target == ImprovementTarget.CONTEXT_REFRESH_VALIDATION_QUESTIONS:
                proposal = self._create_question_refinement_proposal(pattern)
                proposals.append(proposal)
            elif pattern.target == ImprovementTarget.CONTEXT_REFRESH_TIER_REQUIREMENTS:
                proposal = self._create_tier_adjustment_proposal(pattern)
                proposals.append(proposal)

            # Future: Add handlers for Squirt, Sherlock, J5A targets

        # Save proposals
        for proposal in proposals:
            self._save_proposal(proposal)

        print(f"\n💡 Generated {len(proposals)} improvement proposals")
        return proposals

    def _create_question_refinement_proposal(self, pattern: Pattern) -> ImprovementProposal:
        """Create validation question refinement proposal"""
        q_num = pattern.item_name.split('_')[1]  # Extract question number

        proposal_id = f"PROP_{pattern.pattern_id}"

        return ImprovementProposal(
            proposal_id=proposal_id,
            pattern_id=pattern.pattern_id,
            system="context-refresh",
            target=ImprovementTarget.CONTEXT_REFRESH_VALIDATION_QUESTIONS,
            improvement_type="question_refinement",
            current_state=f"Question {q_num} pass rate: {pattern.metric_value:.1f}%",
            proposed_change=f"Refine question {q_num} to target common failure patterns",
            expected_impact=f"Increase pass rate from {pattern.metric_value:.1f}% to >80%",
            confidence_level=0.7,
            status=ImprovementStatus.PROPOSED
        )

    def _create_tier_adjustment_proposal(self, pattern: Pattern) -> ImprovementProposal:
        """Create tier requirement adjustment proposal"""
        proposal_id = f"PROP_{pattern.pattern_id}"

        # Extract tier and compaction status from item_name
        parts = pattern.item_name.split('_')
        tier = parts[1]
        compaction = parts[3]

        return ImprovementProposal(
            proposal_id=proposal_id,
            pattern_id=pattern.pattern_id,
            system="context-refresh",
            target=ImprovementTarget.CONTEXT_REFRESH_TIER_REQUIREMENTS,
            improvement_type="tier_requirement_adjustment",
            current_state=f"Tier {tier} after compaction={compaction}: {pattern.metric_value:.1f}% pass rate",
            proposed_change=f"Recommend higher tier for compaction={compaction} scenarios",
            expected_impact=f"Increase pass rate from {pattern.metric_value:.1f}% to >85%",
            confidence_level=0.8,
            status=ImprovementStatus.PROPOSED
        )

    def _save_proposal(self, proposal: ImprovementProposal):
        """Save improvement proposal to database"""
        cursor = self.kaizen_conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO kaizen_improvement_proposals (
                proposal_id, pattern_id, system, target, improvement_type,
                current_state, proposed_change, expected_impact,
                confidence_level, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal.proposal_id,
            proposal.pattern_id,
            proposal.system,
            proposal.target.value,
            proposal.improvement_type,
            proposal.current_state,
            proposal.proposed_change,
            proposal.expected_impact,
            proposal.confidence_level,
            proposal.status.value,
            proposal.created_at
        ))

        self.kaizen_conn.commit()

    # =========================================================================
    # Interactive Review Session
    # =========================================================================

    def interactive_review_session(self):
        """
        Interactive CLI session for reviewing and approving proposals

        Human-in-the-loop approval workflow:
        1. Display all pending proposals
        2. User reviews each proposal
        3. User approves, rejects, or requests modifications
        4. Approved proposals marked for deployment
        """
        cursor = self.kaizen_conn.cursor()

        # Get all proposed improvements
        cursor.execute("""
            SELECT
                proposal_id, system, target, improvement_type,
                current_state, proposed_change, expected_impact,
                confidence_level
            FROM kaizen_improvement_proposals
            WHERE status = 'proposed'
            ORDER BY confidence_level DESC
        """)

        proposals = cursor.fetchall()

        if not proposals:
            print("\n✅ No pending proposals to review")
            return

        print("\n╔═══════════════════════════════════════════════════════════════════════╗")
        print("║         KAIZEN IMPROVEMENT PROPOSAL REVIEW SESSION                    ║")
        print("╚═══════════════════════════════════════════════════════════════════════╝\n")

        print(f"Found {len(proposals)} pending proposals\n")

        approved = []
        rejected = []

        for idx, proposal in enumerate(proposals, 1):
            (proposal_id, system, target, improvement_type,
             current_state, proposed_change, expected_impact, confidence) = proposal

            print(f"\n{'=' * 75}")
            print(f"Proposal {idx} of {len(proposals)}")
            print(f"{'=' * 75}")
            print(f"ID: {proposal_id}")
            print(f"System: {system}")
            print(f"Target: {target}")
            print(f"Type: {improvement_type}")
            print(f"\nCurrent State:")
            print(f"  {current_state}")
            print(f"\nProposed Change:")
            print(f"  {proposed_change}")
            print(f"\nExpected Impact:")
            print(f"  {expected_impact}")
            print(f"\nConfidence Level: {confidence*100:.0f}%")

            print(f"\n{'─' * 75}")
            print("Decision: (a)pprove, (r)eject, (s)kip, (q)uit review?")

            while True:
                decision = input("> ").strip().lower()

                if decision in ['a', 'approve']:
                    approved.append(proposal_id)
                    print("✅ Approved for deployment")
                    break
                elif decision in ['r', 'reject']:
                    rejected.append(proposal_id)
                    print("❌ Rejected")
                    break
                elif decision in ['s', 'skip']:
                    print("⏭️  Skipped")
                    break
                elif decision in ['q', 'quit']:
                    print("\n⏸️  Review session paused")
                    break
                else:
                    print("Invalid input. Please enter 'a', 'r', 's', or 'q'")

            if decision in ['q', 'quit']:
                break

        # Update database with decisions
        for proposal_id in approved:
            cursor.execute("""
                UPDATE kaizen_improvement_proposals
                SET status = 'validated'
                WHERE proposal_id = ?
            """, (proposal_id,))

        for proposal_id in rejected:
            cursor.execute("""
                UPDATE kaizen_improvement_proposals
                SET status = 'rejected'
                WHERE proposal_id = ?
            """, (proposal_id,))

        self.kaizen_conn.commit()

        print(f"\n{'=' * 75}")
        print("REVIEW SESSION COMPLETE")
        print(f"{'=' * 75}")
        print(f"✅ Approved: {len(approved)}")
        print(f"❌ Rejected: {len(rejected)}")
        print(f"⏭️  Skipped: {len(proposals) - len(approved) - len(rejected)}")

        if approved:
            print(f"\nApproved proposals are now marked 'validated' and ready for deployment.")
            print(f"Deploy using: kaizen_optimizer.deploy_approved_improvements()")

    # =========================================================================
    # Reporting
    # =========================================================================

    def generate_improvement_report(
        self,
        system: Optional[str] = None
    ) -> str:
        """Generate comprehensive improvement report"""
        cursor = self.kaizen_conn.cursor()

        # Filter by system if specified
        where_clause = f"WHERE system = '{system}'" if system else ""

        # Count patterns by significance
        cursor.execute(f"""
            SELECT significance, COUNT(*) as count
            FROM kaizen_patterns
            {where_clause}
            GROUP BY significance
        """)

        significance_counts = dict(cursor.fetchall())

        # Count proposals by status
        cursor.execute(f"""
            SELECT status, COUNT(*) as count
            FROM kaizen_improvement_proposals
            {where_clause}
            GROUP BY status
        """)

        proposal_counts = dict(cursor.fetchall())

        system_filter = f" ({system})" if system else " (All Systems)"
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                KAIZEN CONTINUOUS IMPROVEMENT REPORT{system_filter:>25} ║
╚═══════════════════════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 PATTERNS DETECTED:
   High Significance:   {significance_counts.get('high', 0)}
   Medium Significance: {significance_counts.get('medium', 0)}
   Low Significance:    {significance_counts.get('low', 0)}

💡 IMPROVEMENT PROPOSALS:
   Proposed:  {proposal_counts.get('proposed', 0)}
   Testing:   {proposal_counts.get('testing', 0)}
   Validated: {proposal_counts.get('validated', 0)}
   Deployed:  {proposal_counts.get('deployed', 0)}
   Rejected:  {proposal_counts.get('rejected', 0)}

"""

        # List high priority patterns
        cursor.execute(f"""
            SELECT item_name, category, metric_value, suggested_improvement
            FROM kaizen_patterns
            {where_clause + ' AND' if where_clause else 'WHERE'} actionable = 1 AND significance = 'high'
            ORDER BY metric_value ASC
            LIMIT 5
        """)

        high_priority = cursor.fetchall()

        if high_priority:
            report += "🎯 HIGH PRIORITY OPPORTUNITIES:\n\n"
            for item, category, metric, suggestion in high_priority:
                report += f"   • {item} ({category}): metric={metric:.1f}\n"
                if suggestion:
                    report += f"     → {suggestion}\n"
                report += "\n"

        report += "=" * 75 + "\n"
        report += "Next Steps: Review proposals using interactive_review_session()\n"

        return report

    def close(self):
        """Close database connection"""
        if self.kaizen_conn:
            self.kaizen_conn.close()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point for Kaizen optimizer"""
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║      KAIZEN OPTIMIZER - Universal J5A Continuous Improvement          ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝\n")

    optimizer = KaizenOptimizer()

    # Example: Analyze context refresh validation
    phoenix_db = Path(__file__).parent / "phoenix_validation.db"

    if phoenix_db.exists():
        print("Analyzing context-refresh validation patterns...")
        patterns = optimizer.analyze_context_refresh_validation(phoenix_db)

        if patterns:
            print("\nGenerating improvement proposals...")
            proposals = optimizer.generate_proposals(patterns)

            # Generate report
            report = optimizer.generate_improvement_report(system="context-refresh")
            print(f"\n{report}")

            # Offer interactive review
            if proposals:
                print("\nWould you like to review proposals interactively? (y/n)")
                response = input("> ").strip().lower()
                if response in ['y', 'yes']:
                    optimizer.interactive_review_session()
        else:
            print("✅ No patterns detected - system performing well!")
    else:
        print(f"⚠️  Phoenix database not found: {phoenix_db}")
        print("   Run Phoenix validation first to collect operational data")

    optimizer.close()


if __name__ == "__main__":
    main()
