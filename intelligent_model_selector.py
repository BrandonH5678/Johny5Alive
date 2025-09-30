#!/usr/bin/env python3
"""
Intelligent Model Selection System for Sherlock
Automatically selects the most appropriate transcription model based on:
- Available system RAM
- Audio duration
- Quality requirements
- Processing constraints

This prevents OOM crashes and ensures system viability over quality preferences.
"""

import os
import subprocess
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class QualityPreference(Enum):
    """Quality preference for transcription"""
    MINIMUM = "minimum"      # Fastest, lowest accuracy (tiny)
    BALANCED = "balanced"    # Good balance (base/small)
    HIGH = "high"           # High accuracy (small/medium)
    MAXIMUM = "maximum"     # Best accuracy (large-v3)


@dataclass
class ModelSelection:
    """Result of model selection"""
    engine: str              # "faster-whisper" or "openai-whisper"
    model_size: str         # "tiny", "base", "small", "medium", "large-v3"
    reason: str             # Human-readable explanation
    chunking_required: bool # Whether audio should be chunked
    chunk_duration: int     # Recommended chunk duration in seconds
    estimated_ram_mb: int   # Estimated RAM usage
    warning: Optional[str] = None  # Warning message if constraints tight


class IntelligentModelSelector:
    """
    Constraint-aware model selection for Sherlock audio processing

    Key Principle: System viability ALWAYS trumps quality preferences.
    A completed 85% accurate transcription beats a crashed 95% accurate attempt.
    """

    # Model RAM requirements (in MB)
    MODEL_RAM_REQUIREMENTS = {
        "faster-whisper": {
            "tiny": 300,     # 39MB model + 250MB overhead
            "base": 400,     # 74MB model + 300MB overhead
            "small": 600,    # 244MB model + 350MB overhead
            "medium": 1200,  # 769MB model + 450MB overhead
        },
        "openai-whisper": {
            "tiny": 400,     # Less optimized than faster-whisper
            "base": 500,
            "small": 800,
            "medium": 1500,
            "large-v3": 3000,  # 2.9GB model + overhead
        }
    }

    # Quality metrics (accuracy percentages)
    MODEL_QUALITY = {
        "faster-whisper": {
            "tiny": 85,
            "base": 88,
            "small": 92,
            "medium": 94,
        },
        "openai-whisper": {
            "tiny": 83,
            "base": 87,
            "small": 90,
            "medium": 93,
            "large-v3": 96,
        }
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def get_available_ram_gb(self) -> float:
        """Get available system RAM in GB"""
        try:
            result = subprocess.run(
                ['free', '-b'],
                capture_output=True,
                text=True
            )

            # Parse available RAM from 'free' output
            for line in result.stdout.split('\n'):
                if line.startswith('Mem:'):
                    parts = line.split()
                    available_bytes = int(parts[6])  # 'available' column
                    return available_bytes / (1024**3)  # Convert to GB

            self.logger.warning("Could not parse RAM, assuming 2GB available")
            return 2.0

        except Exception as e:
            self.logger.error(f"Error getting RAM: {e}")
            return 2.0  # Conservative fallback

    def get_audio_duration_hours(self, audio_path: str) -> float:
        """Get audio duration in hours using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ], capture_output=True, text=True)

            duration_seconds = float(result.stdout.strip())
            return duration_seconds / 3600.0

        except Exception as e:
            self.logger.error(f"Error getting duration: {e}")
            return 0.0

    def select_model(
        self,
        audio_path: Optional[str] = None,
        audio_duration_hours: Optional[float] = None,
        available_ram_gb: Optional[float] = None,
        quality_preference: QualityPreference = QualityPreference.BALANCED
    ) -> ModelSelection:
        """
        Select optimal model based on constraints

        Args:
            audio_path: Path to audio file (will auto-detect duration)
            audio_duration_hours: Manual duration override
            available_ram_gb: Manual RAM override
            quality_preference: Desired quality level

        Returns:
            ModelSelection with recommended configuration
        """

        # Get system information
        if available_ram_gb is None:
            available_ram_gb = self.get_available_ram_gb()

        if audio_duration_hours is None and audio_path:
            audio_duration_hours = self.get_audio_duration_hours(audio_path)
        elif audio_duration_hours is None:
            audio_duration_hours = 0.0

        self.logger.info(f"Model selection inputs: {available_ram_gb:.2f}GB RAM, {audio_duration_hours:.2f}h audio, {quality_preference.value} quality")

        # CRITICAL: Emergency RAM constraints
        if available_ram_gb < 1.5:
            return ModelSelection(
                engine="faster-whisper",
                model_size="tiny",
                reason="CRITICAL: Very low RAM (<1.5GB) - using minimal model only",
                chunking_required=True,
                chunk_duration=300,  # 5-minute chunks
                estimated_ram_mb=300,
                warning="⚠️ CRITICAL RAM CONSTRAINT: System may be unstable"
            )

        # CRITICAL: Low RAM with long audio
        if available_ram_gb < 2.5 and audio_duration_hours > 2.0:
            return ModelSelection(
                engine="faster-whisper",
                model_size="tiny",
                reason="Low RAM (<2.5GB) + long audio (>2h) = tiny model with aggressive chunking",
                chunking_required=True,
                chunk_duration=600,  # 10-minute chunks
                estimated_ram_mb=300,
                warning="⚠️ RAM CONSTRAINT: Using smallest model for safety"
            )

        # CONSTRAINT: Moderate RAM with very long audio (Operation Gladio scenario)
        if 2.5 <= available_ram_gb < 3.5 and audio_duration_hours > 8.0:
            return ModelSelection(
                engine="faster-whisper",
                model_size="small",
                reason="Moderate RAM (2.5-3.5GB) + very long audio (>8h) = small model with chunking",
                chunking_required=True,
                chunk_duration=600,  # 10-minute chunks
                estimated_ram_mb=600
            )

        # BALANCED: Moderate RAM with long audio
        if 2.5 <= available_ram_gb < 3.5 and audio_duration_hours > 2.0:
            model = "small" if quality_preference in [QualityPreference.HIGH, QualityPreference.MAXIMUM] else "base"
            return ModelSelection(
                engine="faster-whisper",
                model_size=model,
                reason=f"Moderate RAM + long audio = faster-whisper {model} with chunking",
                chunking_required=True,
                chunk_duration=600,
                estimated_ram_mb=self.MODEL_RAM_REQUIREMENTS["faster-whisper"][model]
            )

        # SAFE: Good RAM with moderate audio
        if 3.5 <= available_ram_gb < 5.0 and audio_duration_hours < 4.0:
            if quality_preference == QualityPreference.MAXIMUM:
                # Can use medium model safely
                return ModelSelection(
                    engine="faster-whisper",
                    model_size="medium",
                    reason="Good RAM + moderate audio + max quality = faster-whisper medium",
                    chunking_required=audio_duration_hours > 2.0,
                    chunk_duration=900,  # 15-minute chunks if needed
                    estimated_ram_mb=1200
                )
            else:
                return ModelSelection(
                    engine="faster-whisper",
                    model_size="small",
                    reason="Good RAM + moderate audio = faster-whisper small (balanced)",
                    chunking_required=audio_duration_hours > 3.0,
                    chunk_duration=900,
                    estimated_ram_mb=600
                )

        # OPTIMAL: High RAM with short audio
        if available_ram_gb >= 5.0 and audio_duration_hours < 1.0:
            if quality_preference == QualityPreference.MAXIMUM:
                return ModelSelection(
                    engine="openai-whisper",
                    model_size="large-v3",
                    reason="High RAM (>5GB) + short audio (<1h) + max quality = OpenAI Whisper large-v3",
                    chunking_required=False,
                    chunk_duration=0,
                    estimated_ram_mb=3000
                )
            else:
                return ModelSelection(
                    engine="faster-whisper",
                    model_size="medium",
                    reason="High RAM + short audio = faster-whisper medium (fast & accurate)",
                    chunking_required=False,
                    chunk_duration=0,
                    estimated_ram_mb=1200
                )

        # OPTIMAL: High RAM with moderate audio
        if available_ram_gb >= 5.0:
            return ModelSelection(
                engine="faster-whisper",
                model_size="medium",
                reason="High RAM = faster-whisper medium with optional chunking",
                chunking_required=audio_duration_hours > 4.0,
                chunk_duration=1200,  # 20-minute chunks
                estimated_ram_mb=1200
            )

        # DEFAULT FALLBACK: Safe conservative choice
        return ModelSelection(
            engine="faster-whisper",
            model_size="base",
            reason="DEFAULT: Safe balanced choice for unknown constraints",
            chunking_required=audio_duration_hours > 2.0,
            chunk_duration=600,
            estimated_ram_mb=400
        )

    def validate_selection(self, selection: ModelSelection) -> bool:
        """
        Validate that selected model will fit in available RAM

        Returns:
            True if safe, False if would likely cause OOM
        """
        available_ram_mb = self.get_available_ram_gb() * 1024

        # Need 500MB buffer minimum
        safety_buffer_mb = 500

        if selection.estimated_ram_mb + safety_buffer_mb > available_ram_mb:
            self.logger.error(
                f"❌ UNSAFE MODEL SELECTION: {selection.model_size} needs "
                f"{selection.estimated_ram_mb}MB + {safety_buffer_mb}MB buffer, "
                f"but only {available_ram_mb:.0f}MB available"
            )
            return False

        self.logger.info(
            f"✅ SAFE: {selection.model_size} needs {selection.estimated_ram_mb}MB, "
            f"{available_ram_mb:.0f}MB available ({available_ram_mb - selection.estimated_ram_mb:.0f}MB buffer)"
        )
        return True

    def log_selection(self, selection: ModelSelection):
        """Log model selection decision with rationale"""
        self.logger.info("=" * 60)
        self.logger.info("🤖 INTELLIGENT MODEL SELECTION")
        self.logger.info("=" * 60)
        self.logger.info(f"Engine: {selection.engine}")
        self.logger.info(f"Model: {selection.model_size}")
        self.logger.info(f"Estimated RAM: {selection.estimated_ram_mb}MB")
        self.logger.info(f"Chunking: {'YES' if selection.chunking_required else 'NO'}")
        if selection.chunking_required:
            self.logger.info(f"Chunk duration: {selection.chunk_duration}s ({selection.chunk_duration/60:.0f} minutes)")
        self.logger.info(f"Quality: ~{self.MODEL_QUALITY[selection.engine][selection.model_size]}% accuracy")
        self.logger.info(f"Reason: {selection.reason}")
        if selection.warning:
            self.logger.warning(selection.warning)
        self.logger.info("=" * 60)


def main():
    """Test model selector with various scenarios"""
    selector = IntelligentModelSelector()

    print("\n🧪 Testing Intelligent Model Selection\n")

    test_scenarios = [
        ("Low RAM, long audio (Operation Gladio)", None, 12.0, 2.5, QualityPreference.BALANCED),
        ("Very low RAM, any audio", None, 2.0, 1.0, QualityPreference.BALANCED),
        ("High RAM, short audio, max quality", None, 0.5, 6.0, QualityPreference.MAXIMUM),
        ("Moderate RAM, moderate audio", None, 3.0, 3.0, QualityPreference.BALANCED),
        ("Current system state", None, None, None, QualityPreference.BALANCED),
    ]

    for name, audio_path, duration, ram, quality in test_scenarios:
        print(f"\n📋 Scenario: {name}")
        print(f"   RAM: {ram if ram else 'auto-detect'}GB, Duration: {duration if duration else 'auto-detect'}h, Quality: {quality.value}")

        selection = selector.select_model(
            audio_path=audio_path,
            audio_duration_hours=duration,
            available_ram_gb=ram,
            quality_preference=quality
        )

        selector.log_selection(selection)

        is_safe = selector.validate_selection(selection)
        print(f"   Validation: {'✅ SAFE' if is_safe else '❌ UNSAFE'}")


if __name__ == "__main__":
    main()