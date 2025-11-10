#!/usr/bin/env python3
"""
Phoenix Validation Framework - Universal J5A Implementation

Purpose: System-agnostic quality validation across all J5A systems
Architecture: Plugin-based validation with extensible stages
Created: 2025-11-04

Mission: Make working systems work BETTER through early error detection
Philosophy: Detect defects during generation, not after completion

Integration Points:
- Squirt: Voice transcription, mathematical validation, document quality
- Sherlock: Transcript accuracy, intelligence extraction, multi-modal quality
- J5A: Queue validation, cross-system coordination, resource management
- Context-Refresh: Constitutional awareness, integration coordination, operational protocols

Constitutional Alignment:
- Principle 2 (Transparency): All validation decisions logged
- Principle 3 (System Viability): Graceful degradation, not catastrophic failure
- Principle 5 (Adaptive Feedback): Continuous learning from validation patterns
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

# Phoenix validation database (J5A root level)
PHOENIX_DB = Path(__file__).parent / "phoenix_validation.db"


class ValidationLevel(Enum):
    """Validation severity levels"""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


# Extensible ValidationStage - systems register their own stages
class ValidationStage(Enum):
    """
    Universal validation stages - extensible via plugin registration

    Core stages (always available):
    - CONTEXT_REFRESH: Context loading and validation checkpoints
    - CROSS_SYSTEM_COORDINATION: Multi-system integration validation

    System-specific stages (registered by plugins):
    - SQUIRT_VOICE_TRANSCRIPTION: Squirt voice transcription quality
    - SQUIRT_MATHEMATICAL_VALIDATION: Squirt zero-tolerance math checks
    - SQUIRT_DOCUMENT_GENERATION: Squirt document quality
    - SHERLOCK_TRANSCRIPT_ACCURACY: Sherlock podcast transcription
    - SHERLOCK_INTELLIGENCE_EXTRACTION: Sherlock content analysis
    - J5A_QUEUE_VALIDATION: J5A queue job validation
    - J5A_RESOURCE_MANAGEMENT: J5A resource allocation checks
    """
    # Core universal stages
    CONTEXT_REFRESH = "context_refresh"
    CROSS_SYSTEM_COORDINATION = "cross_system_coordination"

    # Squirt stages
    SQUIRT_VOICE_TRANSCRIPTION = "squirt_voice_transcription"
    SQUIRT_CONTENT_EXTRACTION = "squirt_content_extraction"
    SQUIRT_MATHEMATICAL_VALIDATION = "squirt_mathematical_validation"
    SQUIRT_DOCUMENT_GENERATION = "squirt_document_generation"
    SQUIRT_VISUAL_QUALITY = "squirt_visual_quality"

    # Sherlock stages
    SHERLOCK_TRANSCRIPT_ACCURACY = "sherlock_transcript_accuracy"
    SHERLOCK_INTELLIGENCE_EXTRACTION = "sherlock_intelligence_extraction"
    SHERLOCK_MULTIMODAL_QUALITY = "sherlock_multimodal_quality"

    # J5A stages
    J5A_QUEUE_VALIDATION = "j5a_queue_validation"
    J5A_RESOURCE_MANAGEMENT = "j5a_resource_management"
    J5A_CROSS_SYSTEM_COORDINATION = "j5a_cross_system_coordination"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    stage: ValidationStage
    check_name: str
    level: ValidationLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    auto_fix_available: bool = False
    auto_fix_suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for any operation"""
    run_id: str
    system: str  # squirt, sherlock, j5a, context-refresh
    operation_type: str  # document_generation, context_refresh, intelligence_extraction, etc.
    context: Optional[Dict[str, Any]] = field(default_factory=dict)
    passed: bool = True
    results: List[ValidationResult] = field(default_factory=list)
    errors_count: int = 0
    warnings_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_result(self, result: ValidationResult):
        """Add validation result and update counts"""
        self.results.append(result)
        if result.level == ValidationLevel.FAIL:
            self.errors_count += 1
            self.passed = False
        elif result.level == ValidationLevel.WARN:
            self.warnings_count += 1

    def get_summary(self) -> str:
        """Get human-readable summary"""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"""
Phoenix Validation Report: {self.run_id}
System: {self.system}
Operation: {self.operation_type}
Status: {status}
Errors: {self.errors_count}
Warnings: {self.warnings_count}
Total Checks: {len(self.results)}
Timestamp: {self.timestamp}
"""


# Type alias for validation functions
ValidationFunction = Callable[[Dict[str, Any]], List[ValidationResult]]


class PhoenixValidator:
    """
    Universal Phoenix Validation Framework

    Plugin Architecture:
    - Systems register validation stages and functions
    - Enables system-specific validation within universal framework
    - Shared database for cross-system learning
    """

    def __init__(self, db_path: Path = PHOENIX_DB):
        """Initialize Phoenix validator with database connection"""
        self.db_path = db_path
        self.conn = None
        self._validators: Dict[ValidationStage, List[ValidationFunction]] = {}
        self._ensure_database()

    def _ensure_database(self):
        """Create Phoenix validation database if not exists"""
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()

        # Validation runs table (system-agnostic)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phoenix_validation_runs (
                run_id TEXT PRIMARY KEY,
                system TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                context TEXT,
                passed BOOLEAN NOT NULL,
                errors_count INTEGER,
                warnings_count INTEGER,
                timestamp TEXT NOT NULL
            )
        """)

        # Validation results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phoenix_validation_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                check_name TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT,
                details TEXT,
                auto_fix_available BOOLEAN DEFAULT 0,
                auto_fix_suggestion TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES phoenix_validation_runs(run_id)
            )
        """)

        # Auto-fix history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phoenix_autofix_history (
                fix_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                error_type TEXT NOT NULL,
                fix_applied TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES phoenix_validation_runs(run_id)
            )
        """)

        # Pattern detection table (for Kaizen integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phoenix_error_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                system TEXT NOT NULL,
                error_type TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                typical_cause TEXT,
                recommended_fix TEXT
            )
        """)

        # Context refresh validation tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phoenix_context_refresh_validations (
                validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                refresh_type TEXT NOT NULL,
                compaction_occurred BOOLEAN,
                q1_result TEXT, q2_result TEXT, q3_result TEXT,
                q4_result TEXT, q5_result TEXT, q6_result TEXT,
                q7_result TEXT, q8_result TEXT, q9_result TEXT,
                score TEXT NOT NULL,
                tier_used TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES phoenix_validation_runs(run_id)
            )
        """)

        self.conn.commit()

    # =========================================================================
    # Plugin Architecture - Validator Registration
    # =========================================================================

    def register_validator(
        self,
        stage: ValidationStage,
        validator: ValidationFunction,
        name: Optional[str] = None
    ):
        """
        Register a validation function for a specific stage

        Args:
            stage: ValidationStage to validate
            validator: Function that takes validation_data and returns List[ValidationResult]
            name: Optional name for debugging
        """
        if stage not in self._validators:
            self._validators[stage] = []

        self._validators[stage].append(validator)

        validator_name = name or validator.__name__
        print(f"✅ Registered validator '{validator_name}' for stage {stage.value}")

    def get_registered_stages(self) -> List[ValidationStage]:
        """Get all stages with registered validators"""
        return list(self._validators.keys())

    # =========================================================================
    # Context Refresh Validation (Core Universal Validation)
    # =========================================================================

    def validate_context_refresh(
        self,
        run_id: str,
        refresh_type: str,  # full, micro-A, micro-B, micro-C, micro-D
        validation_answers: Dict[str, str],  # q1-q9 answers
        tier_used: str,
        compaction_occurred: bool = False
    ) -> ValidationReport:
        """
        Validate context refresh checkpoint questions

        Args:
            run_id: Unique validation run ID
            refresh_type: Type of refresh (full, micro-A, micro-B, micro-C, micro-D)
            validation_answers: Dict with q1-q9 keys containing AI's answers
            tier_used: Which tier was used (A, B, C, D)
            compaction_occurred: Whether conversation was compacted

        Returns:
            ValidationReport with pass/fail status
        """
        report = ValidationReport(
            run_id=run_id,
            system="context-refresh",
            operation_type=refresh_type,
            context={
                "tier": tier_used,
                "compaction": compaction_occurred
            },
            passed=True
        )

        # Expected answers for validation (simplified - full implementation would be more sophisticated)
        expected_patterns = {
            "q1": ["sequential", "6GB", "system viability", "resource stewardship"],
            "q2": ["wait", "human approval", "human agency", "transparency"],
            "q3": ["85%", "stable", "system viability"],
            "q4": ["queue", "libreoffice priority", "business hours"],
            "q5": ["sherlock", "time-sensitive"],
            "q6": ["j5a_universe_memory", "entity", "unified"],
            "q7": ["4.5", "ODS", "source"],
            "q8": ["continue", "monitor", "83", "85"],
            "q9": ["prism_consciousness", "session_protocols", "rrarr"]
        }

        # Validate each answer
        passed_count = 0
        for q_num in range(1, 10):
            q_key = f"q{q_num}"
            answer = validation_answers.get(q_key, "").lower()
            expected = expected_patterns.get(q_key, [])

            # Check if answer contains expected keywords
            matches = sum(1 for keyword in expected if keyword.lower() in answer)
            passed = matches >= (len(expected) // 2)  # At least half the keywords

            if passed:
                passed_count += 1
                report.add_result(ValidationResult(
                    stage=ValidationStage.CONTEXT_REFRESH,
                    check_name=f"question_{q_num}",
                    level=ValidationLevel.PASS,
                    message=f"Question {q_num} answered correctly",
                    details={"answer": answer, "expected_keywords": expected}
                ))
            else:
                report.add_result(ValidationResult(
                    stage=ValidationStage.CONTEXT_REFRESH,
                    check_name=f"question_{q_num}",
                    level=ValidationLevel.FAIL,
                    message=f"Question {q_num} answer incomplete or incorrect",
                    details={"answer": answer, "expected_keywords": expected},
                    auto_fix_available=True,
                    auto_fix_suggestion=f"Re-read relevant documents and retry validation"
                ))

        # Calculate score
        score = f"{passed_count}/9"

        # Determine if overall passed (7/9 minimum)
        if passed_count < 7:
            report.passed = False

        # Save to context refresh validation tracking
        self._save_context_refresh_validation(
            run_id, refresh_type, validation_answers, score, tier_used, compaction_occurred
        )

        # Save general validation report
        self._save_validation_report(report)

        return report

    def _save_context_refresh_validation(
        self,
        run_id: str,
        refresh_type: str,
        answers: Dict[str, str],
        score: str,
        tier: str,
        compaction: bool
    ):
        """Save context refresh specific validation data"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO phoenix_context_refresh_validations (
                run_id, refresh_type, compaction_occurred,
                q1_result, q2_result, q3_result, q4_result, q5_result,
                q6_result, q7_result, q8_result, q9_result,
                score, tier_used, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, refresh_type, compaction,
            answers.get('q1'), answers.get('q2'), answers.get('q3'),
            answers.get('q4'), answers.get('q5'), answers.get('q6'),
            answers.get('q7'), answers.get('q8'), answers.get('q9'),
            score, tier, datetime.now().isoformat()
        ))

        self.conn.commit()

    # =========================================================================
    # Generic Validation Orchestration
    # =========================================================================

    def run_validation(
        self,
        run_id: str,
        system: str,
        operation_type: str,
        validation_data: Dict[str, Any],
        stages: Optional[List[ValidationStage]] = None
    ) -> ValidationReport:
        """
        Run validation pipeline for any system operation

        Args:
            run_id: Unique identifier for this validation run
            system: System name (squirt, sherlock, j5a, context-refresh)
            operation_type: Type of operation being validated
            validation_data: Dictionary with validation inputs
            stages: Optional list of specific stages to validate (default: all registered)

        Returns:
            ValidationReport with all results
        """
        report = ValidationReport(
            run_id=run_id,
            system=system,
            operation_type=operation_type,
            context=validation_data.get('context', {}),
            passed=True
        )

        # Determine which stages to run
        stages_to_run = stages if stages else self.get_registered_stages()

        # Run validators for each stage
        for stage in stages_to_run:
            if stage in self._validators:
                for validator in self._validators[stage]:
                    try:
                        results = validator(validation_data)
                        for result in results:
                            report.add_result(result)
                    except Exception as e:
                        # Validator failure shouldn't crash entire validation
                        report.add_result(ValidationResult(
                            stage=stage,
                            check_name="validator_execution",
                            level=ValidationLevel.FAIL,
                            message=f"Validator failed with exception: {str(e)}",
                            details={"exception_type": type(e).__name__}
                        ))

        # Save to database
        self._save_validation_report(report)

        return report

    def _save_validation_report(self, report: ValidationReport):
        """Save validation report to database"""
        cursor = self.conn.cursor()

        # Insert run
        cursor.execute("""
            INSERT OR REPLACE INTO phoenix_validation_runs (
                run_id, system, operation_type, context, passed,
                errors_count, warnings_count, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.run_id,
            report.system,
            report.operation_type,
            json.dumps(report.context),
            report.passed,
            report.errors_count,
            report.warnings_count,
            report.timestamp
        ))

        # Insert results
        for result in report.results:
            cursor.execute("""
                INSERT INTO phoenix_validation_results (
                    run_id, stage, check_name, level, message, details,
                    auto_fix_available, auto_fix_suggestion, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.run_id,
                result.stage.value,
                result.check_name,
                result.level.value,
                result.message,
                json.dumps(result.details),
                result.auto_fix_available,
                result.auto_fix_suggestion,
                result.timestamp
            ))

        self.conn.commit()

    # =========================================================================
    # Reporting and Analysis
    # =========================================================================

    def get_validation_stats(
        self,
        system: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get validation statistics for analysis"""
        cursor = self.conn.cursor()

        # Base query
        where_clause = "WHERE datetime(timestamp) > datetime('now', '-{} days')".format(days)
        if system:
            where_clause += f" AND system = '{system}'"

        # Overall pass rate
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_runs,
                SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_runs,
                SUM(errors_count) as total_errors,
                SUM(warnings_count) as total_warnings
            FROM phoenix_validation_runs
            {where_clause}
        """)

        stats = cursor.fetchone()
        total, passed, errors, warnings = stats if stats else (0, 0, 0, 0)

        # Most common failure patterns
        cursor.execute(f"""
            SELECT
                stage,
                check_name,
                COUNT(*) as failure_count
            FROM phoenix_validation_results
            WHERE level = 'fail'
            AND run_id IN (
                SELECT run_id FROM phoenix_validation_runs {where_clause}
            )
            GROUP BY stage, check_name
            ORDER BY failure_count DESC
            LIMIT 5
        """)

        common_failures = cursor.fetchall()

        return {
            "total_runs": total or 0,
            "passed_runs": passed or 0,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "total_errors": errors or 0,
            "total_warnings": warnings or 0,
            "common_failures": [
                {"stage": stage, "check": check, "count": count}
                for stage, check, count in common_failures
            ]
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# =============================================================================
# CLI Interface for Testing
# =============================================================================

def main():
    """Test universal Phoenix validator"""
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║        PHOENIX VALIDATOR - Universal J5A Validation Framework         ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝\n")

    validator = PhoenixValidator()

    # Test context refresh validation
    print("Testing Context Refresh Validation:")
    print("=" * 75)

    test_answers = {
        "q1": "I would choose sequential processing because it stays within the 12GB constraint. Constitutional Principle 3 (System Viability) prioritizes reliability over speed, and Principle 4 (Resource Stewardship) requires respecting the 12GB limit.",
        "q2": "No, I would wait for human review. Principle 1 (Human Agency) requires human approval for significant adaptations, and Principle 2 (Transparency) means all decisions must be auditable.",
        "q3": "I would choose 85% stable. Principle 3 (System Viability) states that completed 85% accurate is better than a crashed 95% attempt.",
        "q4": "I would queue the voice memo. It's 3pm Tuesday which is within business hours (6am-7pm Mon-Fri), so LibreOffice has priority according to the Integration Map. Even urgent voice processing defers to active document generation during business hours.",
        "q5": "Sherlock should go first because it's time-sensitive intelligence, which takes priority over Squirt's internal non-client-facing test according to the priority matrix.",
        "q6": "I would query j5a_universe_memory, the unified entity store. The Active Memory Architecture enables cross-system entity memory sharing to avoid duplicate lookups.",
        "q7": "I would use 4.5 hours from the ODS source. The CLAUDE.md Phase 0 validation requires ALWAYS verifying source values and NEVER assuming template defaults are correct.",
        "q8": "I would continue with monitoring. 83°C is below the 85°C safe maximum per thermal protocols, though I would switch to fast mode if temperature rises and defer accurate mode processing.",
        "q9": "I should load PRISM_CONSCIOUSNESS.md and SESSION_PROTOCOLS.md as Tier 2 system-specific documents for Prism. I should also review the RRARR_FRAMEWORK.md which was already loaded in Tier 0."
    }

    report = validator.validate_context_refresh(
        run_id="test-context-refresh-001",
        refresh_type="full",
        validation_answers=test_answers,
        tier_used="full",
        compaction_occurred=False
    )

    print(f"\n{report.get_summary()}")
    print("\nDetailed Results:")
    print("=" * 75)

    for result in report.results:
        status_icon = {
            ValidationLevel.PASS: "✅",
            ValidationLevel.WARN: "⚠️",
            ValidationLevel.FAIL: "❌"
        }[result.level]

        print(f"{status_icon} {result.check_name}: {result.message}")

    # Get statistics
    print("\n" + "=" * 75)
    print("Validation Statistics (Last 7 Days):")
    print("=" * 75)

    stats = validator.get_validation_stats(system="context-refresh")
    print(f"Total Runs: {stats['total_runs']}")
    print(f"Passed: {stats['passed_runs']} ({stats['pass_rate']:.1f}%)")
    print(f"Total Errors: {stats['total_errors']}")
    print(f"Total Warnings: {stats['total_warnings']}")

    validator.close()


if __name__ == "__main__":
    main()
