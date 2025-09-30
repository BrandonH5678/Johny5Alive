"""
J5A Work Assignment: Propagate Incremental Save Pattern to Squirt and Sherlock
Task definitions for overnight/background execution

CRITICAL: Prevents catastrophic data loss from crashes during long-running processes
Origin: Operation Gladio lesson learned (Sept 2024)
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
    """Defines how to validate task completion"""
    validation_commands: List[str]
    expected_outputs: List[str]
    quality_criteria: Dict[str, any]


@dataclass
class J5AWorkAssignment:
    """Complete specification for J5A overnight task"""
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


def create_incremental_save_propagation_tasks() -> List[J5AWorkAssignment]:
    """
    Create task definitions for propagating incremental save pattern to Squirt/Sherlock
    """
    tasks = []

    # ============================================================================
    # PHASE 1: Squirt Voice Queue Checkpoint System
    # ============================================================================

    task_1_1 = J5AWorkAssignment(
        task_id="incremental_save_1_1",
        task_name="Add Incremental Save Pattern to Squirt CLAUDE.md",
        domain="documentation",
        description="Document incremental save pattern in Squirt CLAUDE.md with voice queue specific implementation requirements",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/CLAUDE.md",
            "/home/johnny5/Squirt/CLAUDE.md.backup"
        ],

        success_criteria={
            "incremental_save_section_present": True,
            "voice_queue_examples_included": True,
            "when_to_apply_rules_documented": True,
            "correct_wrong_pattern_examples": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'incremental save' /home/johnny5/Squirt/CLAUDE.md",
                "grep -i 'checkpoint' /home/johnny5/Squirt/CLAUDE.md",
                "grep -A 10 'WRONG.*accumulate' /home/johnny5/Squirt/CLAUDE.md",
            ],
            expected_outputs=[
                "Incremental save pattern documented",
                "Checkpoint examples present",
                "Wrong pattern examples included"
            ],
            quality_criteria={
                "code_examples": 2,  # Wrong and correct patterns
                "when_to_apply_rules": 4,
                "cross_reference_to_j5a": True
            }
        ),

        estimated_tokens=8000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=20,
        thermal_risk="low",

        dependencies=[],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Squirt/CLAUDE.md from backup",

        implementation_notes="""
        Add section based on J5A CLAUDE.md pattern:

        ## 🆕 Incremental Save Pattern (Mandatory for Squirt Batch Processing)

        **CRITICAL DESIGN PRINCIPLE** learned from Operation Gladio (Sept 2024):

        **Rule:** Any long-running voice queue batch processing that accumulates results MUST save intermediate results incrementally.

        **When to Apply in Squirt:**
        - ✅ Voice queue batch processing (>10 memos)
        - ✅ Multi-input document generation sequences
        - ❌ Single voice memo processing (completes in <5 min)

        Include code examples showing wrong (accumulate) vs correct (checkpoint) patterns.
        """
    )
    tasks.append(task_1_1)

    task_1_2 = J5AWorkAssignment(
        task_id="incremental_save_1_2",
        task_name="Implement VoiceCheckpointManager for Squirt",
        domain="system_development",
        description="Create checkpoint manager module for Squirt voice queue to enable incremental saves and resume capability",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/src/voice_checkpoint_manager.py",
            "/home/johnny5/Squirt/tests/test_voice_checkpoint_manager.py"
        ],

        success_criteria={
            "checkpoint_save_functional": True,
            "checkpoint_manifest_tracking": True,
            "resume_capability_implemented": True,
            "atomic_file_operations": True,
            "test_suite_passes": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -c 'from src.voice_checkpoint_manager import VoiceCheckpointManager; v = VoiceCheckpointManager(\"test\"); print(\"✅ Import successful\")'",
                "python3 -m pytest /home/johnny5/Squirt/tests/test_voice_checkpoint_manager.py -v",
            ],
            expected_outputs=[
                "VoiceCheckpointManager imports successfully",
                "All checkpoint tests pass"
            ],
            quality_criteria={
                "test_coverage": 0.90,
                "atomic_operations": True,
                "resume_functional": True
            }
        ),

        estimated_tokens=12000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=35,
        thermal_risk="low",

        dependencies=["incremental_save_1_1"],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Squirt/src/voice_checkpoint_manager.py and restore voice_queue_manager.py",

        implementation_notes="""
        Implementation requirements:

        class VoiceCheckpointManager:
            def __init__(self, batch_id: str):
                self.batch_id = batch_id
                self.checkpoint_dir = Path(f"checkpoints/{batch_id}")
                self.manifest_file = self.checkpoint_dir / "manifest.json"

            def save_result(self, memo_id: str, result: dict):
                '''Save individual voice memo result immediately'''
                # Atomic write to checkpoint_dir/memo_id.json

            def update_manifest(self, memo_id: str, status: str):
                '''Track completion status in manifest'''
                # Update manifest.json with atomic write

            def get_completed_memos(self) -> List[str]:
                '''Return list of already-completed memo IDs'''

            def has_checkpoint(self) -> bool:
                '''Check if checkpoint exists for this batch'''

            def load_results(self) -> Dict[str, dict]:
                '''Load all checkpoint results for resume'''

            def clear_checkpoint(self):
                '''Clean up after successful batch completion'''

        Key requirements:
        - Atomic file writes (write to temp, then rename)
        - JSON format for portability
        - Manifest tracks: memo_id, timestamp, status (pending/complete/error)
        - Resume logic: skip already-completed memos
        """
    )
    tasks.append(task_1_2)

    task_1_3 = J5AWorkAssignment(
        task_id="incremental_save_1_3",
        task_name="Integrate checkpoints into voice_queue_manager.py",
        domain="system_development",
        description="Modify Squirt voice queue manager to use VoiceCheckpointManager for incremental saves",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Squirt/src/voice_queue_manager.py",
            "/home/johnny5/Squirt/src/voice_queue_manager.py.backup"
        ],

        success_criteria={
            "checkpoint_manager_integrated": True,
            "save_after_each_memo": True,
            "resume_capability_functional": True,
            "backward_compatible": True,
            "tests_pass": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 /home/johnny5/Squirt/src/voice_queue_manager.py --test-checkpoint-integration",
                "python3 -m pytest /home/johnny5/Squirt/tests/test_voice_queue_manager.py -v",
            ],
            expected_outputs=[
                "Checkpoint integration test passes",
                "All voice queue tests pass"
            ],
            quality_criteria={
                "saves_per_memo": 1,
                "resume_functional": True,
                "no_duplicate_processing": True
            }
        ),

        estimated_tokens=10000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=30,
        thermal_risk="low",

        dependencies=["incremental_save_1_2"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Squirt/src/voice_queue_manager.py from backup",

        implementation_notes="""
        Integration pattern:

        def process_voice_queue(self, batch_id: str):
            checkpoint_mgr = VoiceCheckpointManager(batch_id)

            # Check for existing checkpoint (resume capability)
            completed_memos = set(checkpoint_mgr.get_completed_memos())

            for voice_memo in self.queue:
                # Skip already-completed memos
                if voice_memo.id in completed_memos:
                    self.logger.info(f"Skipping {voice_memo.id} (already complete)")
                    continue

                # Process voice memo
                result = self.process_voice_memo(voice_memo)

                # ✅ INCREMENTAL SAVE: Immediately persist result
                checkpoint_mgr.save_result(voice_memo.id, result)
                checkpoint_mgr.update_manifest(voice_memo.id, status="complete")

            # After successful batch completion, clear checkpoints
            checkpoint_mgr.clear_checkpoint()

        Maintain backward compatibility:
        - If checkpoint system fails, log error but continue processing
        - Graceful degradation to non-checkpoint mode
        """
    )
    tasks.append(task_1_3)

    # ============================================================================
    # PHASE 2: Sherlock Audio Transcription Checkpoints
    # ============================================================================

    task_2_1 = J5AWorkAssignment(
        task_id="incremental_save_2_1",
        task_name="Add Incremental Save Pattern to Sherlock CLAUDE.md",
        domain="documentation",
        description="Document incremental save pattern in Sherlock CLAUDE.md with long-form audio specific requirements",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/CLAUDE.md",
            "/home/johnny5/Sherlock/CLAUDE.md.backup"
        ],

        success_criteria={
            "incremental_save_section_present": True,
            "long_form_audio_examples_included": True,
            "operation_gladio_reference": True,
            "chunk_based_checkpoint_pattern": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'incremental save' /home/johnny5/Sherlock/CLAUDE.md",
                "grep -i 'operation gladio' /home/johnny5/Sherlock/CLAUDE.md",
                "grep -A 10 'chunk.*checkpoint' /home/johnny5/Sherlock/CLAUDE.md",
            ],
            expected_outputs=[
                "Incremental save pattern documented",
                "Operation Gladio lesson referenced",
                "Chunk-based checkpoint pattern included"
            ],
            quality_criteria={
                "code_examples": 2,
                "operation_gladio_context": True,
                "when_to_apply_rules": 4
            }
        ),

        estimated_tokens=8000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=20,
        thermal_risk="low",

        dependencies=["incremental_save_1_3"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Sherlock/CLAUDE.md from backup",

        implementation_notes="""
        Add section with Operation Gladio context:

        ## 🆕 Incremental Save Pattern (Mandatory for Long-Form Audio)

        **CRITICAL DESIGN PRINCIPLE** learned from Operation Gladio (Sept 2024):

        **Origin:** 17+ hours of audiobook transcription work at risk in volatile memory. System crash at 99% complete = 100% data loss.

        **Rule:** Any long-form audio transcription that processes in chunks MUST save intermediate results incrementally.

        **When to Apply in Sherlock:**
        - ✅ Long-form audio transcription (>1 hour runtime)
        - ✅ Large audiobook processing (Operation Gladio: 17+ hours)
        - ✅ Batch evidence analysis (>50 items)
        - ❌ Single short audio clip (completes quickly)

        Include Operation Gladio as motivating example with chunk-based checkpoint pattern.
        """
    )
    tasks.append(task_2_1)

    task_2_2 = J5AWorkAssignment(
        task_id="incremental_save_2_2",
        task_name="Implement AudioTranscriptionCheckpointManager for Sherlock",
        domain="system_development",
        description="Create checkpoint manager for Sherlock long-form audio transcription with chunk-based saves",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/audio_transcription_checkpoint_manager.py",
            "/home/johnny5/Sherlock/tests/test_audio_checkpoint_manager.py"
        ],

        success_criteria={
            "chunk_checkpoint_save_functional": True,
            "progress_tracking_implemented": True,
            "resume_from_last_chunk": True,
            "gladio_scenario_prevented": True,
            "test_suite_passes": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -c 'from audio_transcription_checkpoint_manager import AudioTranscriptionCheckpointManager; a = AudioTranscriptionCheckpointManager(\"test\"); print(\"✅ Import successful\")'",
                "python3 -m pytest /home/johnny5/Sherlock/tests/test_audio_checkpoint_manager.py -v",
            ],
            expected_outputs=[
                "AudioTranscriptionCheckpointManager imports successfully",
                "All checkpoint tests pass"
            ],
            quality_criteria={
                "test_coverage": 0.90,
                "resume_functional": True,
                "operation_gladio_prevented": True
            }
        ),

        estimated_tokens=13000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=40,
        thermal_risk="low",

        dependencies=["incremental_save_2_1"],
        blocking_conditions=[],

        rollback_plan="Remove /home/johnny5/Sherlock/audio_transcription_checkpoint_manager.py",

        implementation_notes="""
        Implementation requirements:

        class AudioTranscriptionCheckpointManager:
            def __init__(self, audiobook_id: str):
                self.audiobook_id = audiobook_id
                self.checkpoint_dir = Path(f"checkpoints/audio/{audiobook_id}")
                self.manifest_file = self.checkpoint_dir / "manifest.json"

            def save_chunk_transcript(self, chunk_index: int, transcript: str):
                '''Save individual chunk transcript immediately'''
                # Atomic write to checkpoint_dir/chunk_{index}.json

            def update_progress(self, chunks_complete: int, total_chunks: int):
                '''Track overall progress in manifest'''
                # Update manifest.json with atomic write

            def get_last_completed_chunk(self) -> int:
                '''Return index of last completed chunk for resume'''

            def has_checkpoint(self, audiobook_id: str) -> bool:
                '''Check if checkpoint exists for this audiobook'''

            def load_completed_transcripts(self) -> List[str]:
                '''Load all checkpoint transcripts for resume'''

            def get_completion_percentage(self) -> float:
                '''Calculate % complete for progress reporting'''

            def clear_checkpoint(self):
                '''Clean up after successful transcription completion'''

        Key requirements:
        - Chunk-based saves (10-minute audio segments)
        - Progress tracking (N of M chunks complete)
        - Resume from last completed chunk
        - Operation Gladio scenario: 17 hours recoverable if crash occurs
        """
    )
    tasks.append(task_2_2)

    task_2_3 = J5AWorkAssignment(
        task_id="incremental_save_2_3",
        task_name="Integrate checkpoints into Sherlock voice_engine.py",
        domain="system_development",
        description="Modify Sherlock voice engine to use AudioTranscriptionCheckpointManager for long-form audio",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Sherlock/voice_engine.py",
            "/home/johnny5/Sherlock/voice_engine.py.backup"
        ],

        success_criteria={
            "checkpoint_manager_integrated": True,
            "chunk_based_saves_implemented": True,
            "resume_capability_functional": True,
            "operation_gladio_scenario_handled": True,
            "tests_pass": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 /home/johnny5/Sherlock/voice_engine.py --test-checkpoint-integration",
                "python3 -m pytest /home/johnny5/Sherlock/tests/test_voice_engine.py -k checkpoint -v",
            ],
            expected_outputs=[
                "Checkpoint integration test passes",
                "Resume-from-chunk test passes"
            ],
            quality_criteria={
                "saves_per_chunk": 1,
                "resume_functional": True,
                "no_duplicate_chunk_processing": True
            }
        ),

        estimated_tokens=12000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=35,
        thermal_risk="low",

        dependencies=["incremental_save_2_2"],
        blocking_conditions=[],

        rollback_plan="Restore /home/johnny5/Sherlock/voice_engine.py from backup",

        implementation_notes="""
        Integration pattern for long-form audio:

        def transcribe_long_form_audio(self, audio_path: str, audiobook_id: str):
            checkpoint_mgr = AudioTranscriptionCheckpointManager(audiobook_id)

            # Split audio into 10-minute chunks
            chunks = self.split_audio_into_chunks(audio_path, chunk_duration=600)

            # Check for existing checkpoint (resume capability)
            if checkpoint_mgr.has_checkpoint(audiobook_id):
                last_chunk = checkpoint_mgr.get_last_completed_chunk()
                self.logger.info(f"Resuming from chunk {last_chunk+1}")
                chunks = chunks[last_chunk+1:]  # Resume from interruption

            for i, chunk in enumerate(chunks):
                # Transcribe chunk
                transcript = self.transcribe_chunk(chunk)

                # ✅ INCREMENTAL SAVE: Immediately persist chunk transcript
                checkpoint_mgr.save_chunk_transcript(i, transcript)
                checkpoint_mgr.update_progress(
                    chunks_complete=i+1,
                    total_chunks=len(chunks)
                )

                self.logger.info(f"Chunk {i+1}/{len(chunks)} complete ({checkpoint_mgr.get_completion_percentage()}%)")

            # After successful completion, combine and clear checkpoints
            full_transcript = checkpoint_mgr.load_completed_transcripts()
            checkpoint_mgr.clear_checkpoint()
            return "".join(full_transcript)

        Operation Gladio scenario: If crash occurs after 15 hours:
        - 90+ chunks already saved to disk
        - Resume restarts from chunk 91, not chunk 0
        - Only ~2 hours of work lost (not 15 hours)
        """
    )
    tasks.append(task_2_3)

    # ============================================================================
    # PHASE 3: Documentation Propagation
    # ============================================================================

    task_3_1 = J5AWorkAssignment(
        task_id="incremental_save_3_1",
        task_name="Update J5A documentation with cross-system references",
        domain="documentation",
        description="Add cross-references in J5A docs pointing to Squirt/Sherlock incremental save implementations",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/CLAUDE.md",
            "/home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md"
        ],

        success_criteria={
            "cross_references_added": True,
            "system_specific_examples_documented": True,
            "validation_gate_updated": True,
            "consistent_pattern_across_systems": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "grep -i 'squirt.*checkpoint' /home/johnny5/Johny5Alive/CLAUDE.md",
                "grep -i 'sherlock.*checkpoint' /home/johnny5/Johny5Alive/CLAUDE.md",
                "grep 'incremental.*save.*validation' /home/johnny5/Johny5Alive/JOHNY5_AI_OPERATOR_MANUAL.md",
            ],
            expected_outputs=[
                "Squirt checkpoint implementation referenced",
                "Sherlock checkpoint implementation referenced",
                "Validation gate includes incremental save check"
            ],
            quality_criteria={
                "cross_references": 2,  # Squirt + Sherlock
                "validation_gate_updated": True
            }
        ),

        estimated_tokens=4000,
        estimated_ram_gb=0.1,
        estimated_duration_minutes=15,
        thermal_risk="low",

        dependencies=["incremental_save_2_3"],
        blocking_conditions=[],

        rollback_plan="Restore J5A documentation from backups",

        implementation_notes="""
        Add to J5A CLAUDE.md Incremental Save Pattern section:

        **See Also:**
        - Squirt implementation: `VoiceCheckpointManager` for voice queue batch processing
        - Sherlock implementation: `AudioTranscriptionCheckpointManager` for long-form audio
        - Tasks defined: `j5a_plans/incremental_save_propagation_tasks.py`

        Update J5A validation gate to check:
        - Long-running tasks (>1 hour) must use incremental saves
        - Tasks with >10 chunks must save after each chunk
        - Checkpoint managers must be used for all batch processing
        """
    )
    tasks.append(task_3_1)

    # ============================================================================
    # PHASE 4: Validation and Testing
    # ============================================================================

    task_4_1 = J5AWorkAssignment(
        task_id="incremental_save_4_1",
        task_name="Validate incremental save pattern with simulated crash tests",
        domain="validation",
        description="Test checkpoint systems with simulated crashes to verify zero data loss and resume capability",
        priority=Priority.CRITICAL,
        risk_level=RiskLevel.LOW,

        expected_outputs=[
            "/home/johnny5/Johny5Alive/tests/incremental_save_validation_results.json"
        ],

        success_criteria={
            "squirt_crash_recovery_works": True,
            "sherlock_crash_recovery_works": True,
            "zero_data_loss_confirmed": True,
            "resume_capability_validated": True,
            "checkpoint_overhead_acceptable": True
        },

        test_oracle=TestOracle(
            validation_commands=[
                "python3 -m pytest /home/johnny5/Squirt/tests/test_voice_checkpoint_manager.py::test_crash_recovery -v",
                "python3 -m pytest /home/johnny5/Sherlock/tests/test_audio_checkpoint_manager.py::test_crash_recovery -v",
                "cat /home/johnny5/Johny5Alive/tests/incremental_save_validation_results.json | jq '.all_tests_passed'",
            ],
            expected_outputs=[
                "Squirt crash recovery test passes",
                "Sherlock crash recovery test passes",
                "Validation results show 100% success"
            ],
            quality_criteria={
                "data_loss_percentage": 0.0,
                "resume_success_rate": 1.0,
                "checkpoint_overhead_percent": 5.0  # Max acceptable
            }
        ),

        estimated_tokens=2000,
        estimated_ram_gb=0.2,
        estimated_duration_minutes=10,
        thermal_risk="low",

        dependencies=["incremental_save_3_1"],
        blocking_conditions=[],

        rollback_plan="N/A (test-only task, no production changes)",

        implementation_notes="""
        Test scenarios:

        1. Squirt Voice Queue Crash Test:
           - Start processing 20 voice memos
           - Simulate crash after 10 complete
           - Resume and verify: 10 skipped (already complete), 10 processed
           - Zero data loss for completed memos

        2. Sherlock Long-Form Audio Crash Test:
           - Start 2-hour audiobook transcription (120 chunks)
           - Simulate crash after 30 chunks (25% complete)
           - Resume and verify: Starts from chunk 31, not chunk 1
           - Only in-progress chunk lost (~1 minute)

        3. Checkpoint Overhead Test:
           - Measure processing time with checkpoints enabled
           - Compare to baseline (no checkpoints)
           - Verify overhead < 5% of total time

        Document all results with timestamps, data loss measurements, and overhead metrics.
        """
    )
    tasks.append(task_4_1)

    return tasks


if __name__ == "__main__":
    tasks = create_incremental_save_propagation_tasks()
    print(f"Created {len(tasks)} tasks for Incremental Save Pattern Propagation")
    for task in tasks:
        print(f"  - {task.task_id}: {task.task_name} ({task.priority.value}, {task.risk_level.value})")
