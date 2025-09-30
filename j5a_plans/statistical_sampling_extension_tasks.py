"""
J5A Work Assignment: Extend Statistical Sampling to Squirt and Sherlock
Task definitions for overnight/background execution

Purpose: Enable early quality assessment to prevent resource waste
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TestOracle:
    validation_commands: List[str]
    expected_outputs: List[str]
    quality_criteria: Dict[str, any]


@dataclass
class J5AWorkAssignment:
    task_id: str
    task_name: str
    domain: str
    description: str
    priority: Priority
    risk_level: RiskLevel
    expected_outputs: List[str]
    success_criteria: Dict[str, any]
    test_oracle: TestOracle
    estimated_tokens: int
    estimated_ram_gb: float
    estimated_duration_minutes: int
    thermal_risk: str
    dependencies: List[str]
    blocking_conditions: List[str]
    rollback_plan: str
    implementation_notes: Optional[str] = None


def create_statistical_sampling_extension_tasks() -> List[J5AWorkAssignment]:
    """
    Create task definitions for extending statistical sampling to Squirt/Sherlock
    """
    tasks = []

    # ============================================================================
    # PHASE 1: Squirt Voice Processing Statistical Validation
    # ============================================================================

    task_1_1 = J5AWorkAssignment(
        task_id="stat_sample_1_1",
        task_name="Create SquirtVoiceQualityValidator module",
        domain="system_development",
        description="Implement 3-sample statistical validation for Squirt voice queue quality assessment",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/src/voice_quality_validator.py",
            "/home/johnny5/Squirt/tests/test_voice_quality_validator.py"
        ],

        success_criteria={
            "three_sample_validation_implemented": True,
            "quality_thresholds_enforced": True,
            "transcription_accuracy_estimation": True,
            "content_extraction_validation": True,
            "test_suite_passes": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -c 'from src.voice_quality_validator import SquirtVoiceQualityValidator; v = SquirtVoiceQualityValidator(); print(\"✅ Import successful\")'",
                "python3 -m pytest /home/johnny5/Squirt/tests/test_voice_quality_validator.py -v",
            ],
            expected_outputs=[
                "SquirtVoiceQualityValidator imports successfully",
                "All quality validation tests pass"
            ],
            quality_criteria={
                "test_coverage": 0.85,
                "validation_time_seconds": 300,  # <5 minutes for 3 samples
                "false_positive_rate": 0.05
            }
        ),

        estimated_tokens=10000,
        estimated_ram_gb=0.3,
        estimated_duration_minutes=30,
        thermal_risk="low",

        dependencies=[],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Squirt/src/voice_quality_validator.py",

        implementation_notes="""
        Implementation requirements:

        class SquirtVoiceQualityValidator:
            def __init__(self):
                self.quality_thresholds = {
                    "format_success_rate": 0.90,      # 90%+ valid audio format
                    "transcription_success_rate": 0.70,  # 70%+ transcribe successfully
                    "content_extraction_rate": 0.60,  # 60%+ extract business fields
                    "avg_transcription_confidence": 0.70  # 70%+ average confidence
                }

            def validate_voice_queue(self, voice_memos: List[VoiceMemo]) -> ValidationResult:
                '''Perform 3-sample statistical validation on voice queue'''
                # Select samples: beginning (first 2), middle (2), end (last 2)
                samples = self._select_stratified_samples(voice_memos)

                # Process samples and collect metrics
                results = []
                for memo in samples:
                    result = self._validate_single_memo(memo)
                    results.append(result)

                # Calculate aggregate quality metrics
                metrics = self._calculate_quality_metrics(results)

                # Check against thresholds
                viable = self._check_viability(metrics)

                return ValidationResult(
                    viable=viable,
                    metrics=metrics,
                    samples_processed=len(samples),
                    recommendations=self._generate_recommendations(metrics)
                )

            def _validate_single_memo(self, memo: VoiceMemo) -> dict:
                '''Validate single voice memo'''
                return {
                    "format_valid": self._check_audio_format(memo),
                    "transcription_success": self._test_transcription(memo),
                    "content_extraction_success": self._test_content_extraction(memo),
                    "transcription_confidence": self._estimate_confidence(memo)
                }

            def _check_viability(self, metrics: dict) -> bool:
                '''Check if metrics meet quality thresholds'''
                return all([
                    metrics["format_success_rate"] >= self.quality_thresholds["format_success_rate"],
                    metrics["transcription_success_rate"] >= self.quality_thresholds["transcription_success_rate"],
                    metrics["content_extraction_rate"] >= self.quality_thresholds["content_extraction_rate"],
                    metrics["avg_confidence"] >= self.quality_thresholds["avg_transcription_confidence"]
                ])

        Key requirements:
        - 3-sample stratified selection (beginning, middle, end)
        - Quality thresholds specific to Squirt business needs
        - Fast validation (<5 minutes for 3 samples)
        - Actionable recommendations for quality improvements
        """
    )
    tasks.append(task_1_1)

    task_1_2 = J5AWorkAssignment(
        task_id="stat_sample_1_2",
        task_name="Integrate statistical validation into Squirt voice queue manager",
        domain="system_development",
        description="Add quality gate to voice_queue_manager.py using SquirtVoiceQualityValidator",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/src/voice_queue_manager.py",
            "/home/johnny5/Squirt/src/voice_queue_manager.py.backup"
        ],

        success_criteria={
            "quality_gate_integrated": True,
            "blocking_gate_on_failure": True,
            "bypass_option_for_override": True,
            "validation_results_logged": True,
            "tests_pass": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 /home/johnny5/Squirt/src/voice_queue_manager.py --test-quality-gate",
                "python3 -m pytest /home/johnny5/Squirt/tests/test_voice_queue_manager.py -k quality -v",
            ],
            expected_outputs=[
                "Quality gate test passes",
                "Quality validation integration tests pass"
            ],
            quality_criteria={
                "blocks_bad_queues": True,
                "allows_good_queues": True,
                "validation_overhead_percent": 5.0
            }
        ),

        estimated_tokens=8000,
        estimated_ram_gb=0.3,
        estimated_duration_minutes=25,
        thermal_risk="low",

        dependencies=["stat_sample_1_1"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Squirt/src/voice_queue_manager.py from backup",

        implementation_notes="""
        Integration pattern:

        def process_voice_queue_batch(self, batch_id: str, skip_validation: bool = False):
            voice_memos = self.load_queue_batch(batch_id)

            # PHASE 1: Statistical Quality Validation (BLOCKING GATE)
            if not skip_validation:
                validator = SquirtVoiceQualityValidator()
                validation_result = validator.validate_voice_queue(voice_memos)

                self.logger.info(f"Quality validation: {validation_result.metrics}")

                if not validation_result.viable:
                    self.logger.error(f"Quality gate BLOCKED batch processing")
                    self.logger.error(f"Recommendations: {validation_result.recommendations}")
                    raise QualityGateFailure(
                        f"Voice queue quality below thresholds. "
                        f"Metrics: {validation_result.metrics}. "
                        f"Fix quality issues or use --skip-validation to override."
                    )

                self.logger.info("✅ Quality gate PASSED - proceeding with batch processing")

            # PHASE 2: Full Batch Processing (after quality validation)
            for voice_memo in voice_memos:
                result = self.process_voice_memo(voice_memo)
                # ... existing processing logic ...

        Benefits:
        - Detects systematic quality issues in first 3 memos
        - Prevents processing 100 bad memos
        - Saves 95%+ resources on bad batches
        - Override option for special cases
        """
    )
    tasks.append(task_1_2)

    task_1_3 = J5AWorkAssignment(
        task_id="stat_sample_1_3",
        task_name="Document statistical sampling in Squirt AI Operator Manual",
        domain="documentation",
        description="Add statistical validation protocols to Squirt documentation with quality thresholds",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md",
            "/home/johnny5/Squirt/CLAUDE.md"
        ],

        success_criteria={
            "statistical_sampling_section_added": True,
            "quality_thresholds_documented": True,
            "when_to_apply_rules_clear": True,
            "cross_reference_to_j5a": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'statistical.*sampling' /home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md",
                "grep -i 'quality.*threshold' /home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md",
                "grep 'j5a.*validation' /home/johnny5/Squirt/SQUIRT_AI_OPERATOR_MANUAL.md",
            ],
            expected_outputs=[
                "Statistical sampling documented",
                "Quality thresholds listed",
                "J5A cross-reference present"
            ],
            quality_criteria={
                "threshold_specifications": 4,
                "code_examples": 1,
                "cross_references": 1
            }
        ),

        estimated_tokens=5000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=15,
        thermal_risk="low",

        dependencies=["stat_sample_1_2"],
        blocking_conditions=[],

        rollback_plan="Restore Squirt documentation from backups",

        implementation_notes="""
        Add to Squirt AI Operator Manual:

        ## 📊 STATISTICAL SAMPLING VALIDATION

        ### Voice Queue Quality Gates

        **MANDATORY BEFORE BATCH PROCESSING:**
        - [ ] 3-sample validation executed (beginning, middle, end of queue)
        - [ ] Format validation rate ≥90% (9 of 10 samples valid audio)
        - [ ] Transcription success rate ≥70% (7 of 10 successful)
        - [ ] Content extraction rate ≥60% (6 of 10 extract business fields)
        - [ ] Average confidence ≥70%

        **Quality Thresholds (Squirt-Specific):**
        - Format Validation: 90%+ (higher threshold for business-critical docs)
        - Transcription Success: 70%+ (reliable voice-to-text conversion)
        - Content Extraction: 60%+ (business field extraction viable)
        - Overall Quality: 70%+ average confidence

        Cross-reference J5A statistical validation methodology.
        """
    )
    tasks.append(task_1_3)

    # ============================================================================
    # PHASE 2: Sherlock Evidence Quality Statistical Validation
    # ============================================================================

    task_2_1 = J5AWorkAssignment(
        task_id="stat_sample_2_1",
        task_name="Create SherlockEvidenceQualityValidator module",
        domain="system_development",
        description="Implement 3-chunk statistical validation for Sherlock long-form audio quality assessment",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/evidence_quality_validator.py",
            "/home/johnny5/Sherlock/tests/test_evidence_quality_validator.py"
        ],

        success_criteria={
            "three_chunk_validation_implemented": True,
            "audio_format_detection": True,
            "transcription_viability_prediction": True,
            "operation_gladio_prevention": True,
            "test_suite_passes": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -c 'from evidence_quality_validator import SherlockEvidenceQualityValidator; e = SherlockEvidenceQualityValidator(); print(\"✅ Import successful\")'",
                "python3 -m pytest /home/johnny5/Sherlock/tests/test_evidence_quality_validator.py -v",
            ],
            expected_outputs=[
                "SherlockEvidenceQualityValidator imports successfully",
                "All evidence quality tests pass"
            ],
            quality_criteria={
                "test_coverage": 0.85,
                "validation_time_seconds": 600,  # <10 minutes for 3 chunks
                "format_detection_accuracy": 0.95
            }
        ),

        estimated_tokens=12000,
        estimated_ram_gb=0.5,
        estimated_duration_minutes=40,
        thermal_risk="low",

        dependencies=["stat_sample_1_3"],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Sherlock/evidence_quality_validator.py",

        implementation_notes="""
        Implementation requirements:

        class SherlockEvidenceQualityValidator:
            def __init__(self):
                self.quality_thresholds = {
                    "format_success_rate": 0.80,      # 80%+ valid audio format
                    "transcription_success_rate": 0.60,  # 60%+ transcribe successfully
                    "entity_extraction_rate": 0.30,   # 30%+ extract entities
                    "avg_quality_score": 0.50         # 50%+ average quality
                }

            def validate_long_form_audio(self, audio_path: str) -> ValidationResult:
                '''Perform 3-chunk statistical validation on long-form audio'''
                # Extract sample chunks: beginning (0-10min), middle, end
                duration = get_audio_duration(audio_path)
                sample_chunks = self._extract_stratified_chunks(audio_path, duration)

                # Process sample chunks and collect metrics
                results = []
                for position, chunk in sample_chunks.items():
                    result = self._validate_single_chunk(chunk, position)
                    results.append(result)

                # Calculate aggregate quality metrics
                metrics = self._calculate_quality_metrics(results)

                # Check against thresholds
                viable = self._check_viability(metrics)

                # Estimate full processing time and success probability
                estimated_duration_hours = duration / 3600
                success_probability = self._estimate_success_probability(metrics)

                return ValidationResult(
                    viable=viable,
                    metrics=metrics,
                    chunks_processed=len(sample_chunks),
                    estimated_full_duration_hours=estimated_duration_hours,
                    success_probability=success_probability,
                    recommendations=self._generate_recommendations(metrics)
                )

            def _validate_single_chunk(self, chunk: AudioChunk, position: str) -> dict:
                '''Validate single 10-minute audio chunk'''
                return {
                    "format_valid": self._check_audio_format(chunk),
                    "transcription_success": self._test_transcription(chunk),
                    "transcription_quality": self._estimate_wer(chunk),  # Word Error Rate
                    "entity_extraction_success": self._test_entity_extraction(chunk),
                    "position": position
                }

        Key requirements:
        - 3-chunk stratified sampling (beginning, middle, end of long-form audio)
        - Audio format detection before committing 17+ hours
        - Transcription viability prediction
        - Success probability estimation for user decision-making
        - Operation Gladio prevention (detect issues in 10 minutes, not 17 hours)
        """
    )
    tasks.append(task_2_1)

    task_2_2 = J5AWorkAssignment(
        task_id="stat_sample_2_2",
        task_name="Integrate statistical validation into Sherlock voice_engine.py",
        domain="system_development",
        description="Add quality gate to voice_engine.py using SherlockEvidenceQualityValidator for long-form audio",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/voice_engine.py",
            "/home/johnny5/Sherlock/voice_engine.py.backup"
        ],

        success_criteria={
            "quality_gate_integrated": True,
            "operation_gladio_prevented": True,
            "user_decision_support": True,
            "validation_results_logged": True,
            "tests_pass": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 /home/johnny5/Sherlock/voice_engine.py --test-quality-gate",
                "python3 -m pytest /home/johnny5/Sherlock/tests/test_voice_engine.py -k quality -v",
            ],
            expected_outputs=[
                "Quality gate test passes",
                "Long-form audio validation tests pass"
            ],
            quality_criteria={
                "detects_bad_format": True,
                "allows_good_audio": True,
                "gladio_scenario_prevented": True
            }
        ),

        estimated_tokens=10000,
        estimated_ram_gb=0.5,
        estimated_duration_minutes=30,
        thermal_risk="low",

        dependencies=["stat_sample_2_1"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Sherlock/voice_engine.py from backup",

        implementation_notes="""
        Integration pattern:

        def transcribe_long_form_audio(self, audio_path: str, skip_validation: bool = False):
            # PHASE 1: Statistical Quality Validation (BLOCKING GATE)
            if not skip_validation:
                validator = SherlockEvidenceQualityValidator()
                validation_result = validator.validate_long_form_audio(audio_path)

                self.logger.info(f"Quality validation: {validation_result.metrics}")
                self.logger.info(f"Estimated duration: {validation_result.estimated_full_duration_hours:.1f} hours")
                self.logger.info(f"Success probability: {validation_result.success_probability:.1%}")

                if not validation_result.viable:
                    self.logger.error("Quality gate BLOCKED transcription")
                    self.logger.error(f"Issues detected: {validation_result.recommendations}")
                    raise QualityGateFailure(
                        f"Audio quality below thresholds. "
                        f"Would waste {validation_result.estimated_full_duration_hours:.1f} hours on likely failure. "
                        f"Fix audio issues or use --skip-validation to override."
                    )

                # Warn if marginal quality (viable but low success probability)
                if validation_result.success_probability < 0.75:
                    self.logger.warning(
                        f"Quality marginal: {validation_result.success_probability:.1%} success probability. "
                        f"Proceeding but results may be suboptimal."
                    )

                self.logger.info("✅ Quality gate PASSED - proceeding with full transcription")

            # PHASE 2: Full Transcription (after quality validation)
            return self._transcribe_full_audio(audio_path)

        Operation Gladio Prevention:
        - Detects format issues in 10 minutes, not 17 hours
        - Estimates success probability before commitment
        - Provides user decision support with cost/benefit data
        """
    )
    tasks.append(task_2_2)

    task_2_3 = J5AWorkAssignment(
        task_id="stat_sample_2_3",
        task_name="Document statistical sampling in Sherlock AI Operator Manual",
        domain="documentation",
        description="Add statistical validation protocols to Sherlock documentation with Operation Gladio context",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md",
            "/home/johnny5/Sherlock/CLAUDE.md"
        ],

        success_criteria={
            "statistical_sampling_section_added": True,
            "operation_gladio_context_included": True,
            "quality_thresholds_documented": True,
            "cross_reference_to_j5a": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'statistical.*sampling' /home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md",
                "grep -i 'operation gladio' /home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md",
                "grep 'j5a.*validation' /home/johnny5/Sherlock/SHERLOCK_AI_OPERATOR_MANUAL.md",
            ],
            expected_outputs=[
                "Statistical sampling documented",
                "Operation Gladio prevention context included",
                "J5A cross-reference present"
            ],
            quality_criteria={
                "threshold_specifications": 4,
                "gladio_context": True,
                "cross_references": 1
            }
        ),

        estimated_tokens=5000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=15,
        thermal_risk="low",

        dependencies=["stat_sample_2_2"],
        blocking_conditions=[],

        rollback_plan="Restore Sherlock documentation from backups",

        implementation_notes="""
        Add to Sherlock AI Operator Manual:

        ## 📊 STATISTICAL SAMPLING VALIDATION

        ### Long-Form Audio Quality Gates

        **OPERATION GLADIO PREVENTION:**
        Statistical sampling prevents 17+ hour commitments to likely-failing transcriptions.

        **MANDATORY BEFORE LONG-FORM TRANSCRIPTION:**
        - [ ] 3-chunk validation executed (beginning, middle, end of audio)
        - [ ] Format validation rate ≥80% (8 of 10 chunks valid)
        - [ ] Transcription success rate ≥60% (6 of 10 successful)
        - [ ] Entity extraction rate ≥30% (3 of 10 extract entities)
        - [ ] Average quality score ≥50%

        **Quality Thresholds (Sherlock-Specific):**
        - Format Validation: 80%+ (detect incompatible formats early)
        - Transcription Success: 60%+ (viability for long-form processing)
        - Entity Extraction: 30%+ (meaningful intelligence extractable)
        - Overall Quality: 50%+ average score (research-grade acceptable)

        Cross-reference J5A statistical validation methodology and Operation Gladio lesson learned.
        """
    )
    tasks.append(task_2_3)

    # ============================================================================
    # PHASE 3: Validation and Testing
    # ============================================================================

    task_3_1 = J5AWorkAssignment(
        task_id="stat_sample_3_1",
        task_name="Validate statistical sampling with quality gate tests",
        domain="validation",
        description="Test quality gates with known-bad inputs to verify early detection and resource savings",
        priority=Priority.NORMAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/tests/statistical_sampling_validation_results.json"
        ],

        success_criteria={
            "squirt_quality_gate_functional": True,
            "sherlock_quality_gate_functional": True,
            "early_detection_confirmed": True,
            "resource_savings_measured": True,
            "false_positive_rate_acceptable": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -m pytest /home/johnny5/Squirt/tests/ -k quality_gate -v",
                "python3 -m pytest /home/johnny5/Sherlock/tests/ -k quality_gate -v",
                "cat /home/johnny5/Johny5Alive/tests/statistical_sampling_validation_results.json | jq '.resource_savings_percent'",
            ],
            expected_outputs=[
                "Squirt quality gate tests pass",
                "Sherlock quality gate tests pass",
                "Resource savings >90%"
            ],
            quality_criteria={
                "early_detection_accuracy": 0.85,
                "false_positive_rate": 0.05,
                "resource_savings_percent": 90.0
            }
        ),

        estimated_tokens=2000,
        estimated_ram_gb=0.3,
        estimated_duration_minutes=10,
        thermal_risk="low",

        dependencies=["stat_sample_2_3"],
        blocking_conditions=[],

        rollback_plan="N/A (test-only task)",

        implementation_notes="""
        Test scenarios:

        1. Squirt Bad Voice Queue Test:
           - Create queue with 10 voice memos (3 good, 7 corrupted audio)
           - Run quality gate validation
           - Expected: Detects issues in 3 samples, blocks full processing
           - Measure: Time saved (3 samples vs 10 full processing)

        2. Sherlock Incompatible Format Test (Operation Gladio Scenario):
           - Create 17-hour audiobook with incompatible format
           - Run quality gate validation
           - Expected: Detects format issues in 10 minutes (3 chunks)
           - Measure: Time saved (10 min vs 17 hours)

        3. False Positive Test:
           - Create queue/audio with good quality
           - Run quality gate validation
           - Expected: Passes validation, proceeds to full processing
           - Measure: Validation overhead (<5% of total time)

        Document:
        - Resource savings: (time_without_gate - time_with_gate) / time_without_gate
        - Early detection accuracy: correctly_identified_bad / total_bad
        - False positive rate: incorrectly_blocked_good / total_good
        """
    )
    tasks.append(task_3_1)

    return tasks


if __name__ == "__main__":
    tasks = create_statistical_sampling_extension_tasks()
    print(f"Created {len(tasks)} tasks for Statistical Sampling Extension")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_name} ({task.priority.value}, {task.risk_level.value})")
