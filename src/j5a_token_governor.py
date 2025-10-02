#!/usr/bin/env python3
"""
J5A Token Governor - Constraint-Aware Token Budget Management

Manages Claude Code's 200K token / 5-hour session limit with:
- Rolling window token ledger
- Adaptive task sizing based on budget
- Priority-based deferral when budget constrained
- Checkpoint/resume for multi-session execution

Based on user-provided token management scripts.
"""

from collections import deque
from time import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from datetime import datetime
import logging


# Token Budget Constants
WINDOW_SEC = 5 * 3600  # 5 hours in seconds
BUDGET = 200_000       # Claude Code session token limit
SAFETY = 0.85          # Keep 15% headroom
RESERVE = int(0.10 * BUDGET)  # 10% for retries + spikes
TARGET_RATE_TPM = int((BUDGET * SAFETY) / (5 * 60))  # Tokens per minute


class AdaptationTier(Enum):
    """Budget tiers triggering different adaptation strategies"""
    FULL = "full"          # >75% budget remaining
    MODERATE = "moderate"  # 25-75% budget remaining
    CONSTRAINED = "constrained"  # 15-25% budget remaining
    CRITICAL = "critical"  # 5-15% budget remaining
    EMERGENCY = "emergency"  # <5% budget remaining


@dataclass
class TokenEstimate:
    """Token usage estimate for a task"""
    input_tokens: int
    output_tokens: int
    total: int
    confidence: float  # 0.0-1.0


@dataclass
class AdaptivePolicy:
    """Adaptive sizing policy for a budget tier"""
    tier: AdaptationTier
    sherlock_excerpts: int
    sherlock_chunk_tokens: int
    squirt_max_input: int
    squirt_max_output: int
    max_retries: int


class TokenGovernor:
    """
    Token budget manager with rolling window and adaptive policies.

    Core Functions:
    - Track token usage in 5-hour rolling window
    - Estimate task costs before execution
    - Adapt task sizing based on remaining budget
    - Defer tasks when budget insufficient
    - Checkpoint/resume across sessions
    """

    # Adaptive policies per budget tier
    POLICIES = {
        AdaptationTier.FULL: AdaptivePolicy(
            tier=AdaptationTier.FULL,
            sherlock_excerpts=5,
            sherlock_chunk_tokens=170,
            squirt_max_input=1200,
            squirt_max_output=220,
            max_retries=2
        ),
        AdaptationTier.MODERATE: AdaptivePolicy(
            tier=AdaptationTier.MODERATE,
            sherlock_excerpts=4,
            sherlock_chunk_tokens=160,
            squirt_max_input=1000,
            squirt_max_output=180,
            max_retries=2
        ),
        AdaptationTier.CONSTRAINED: AdaptivePolicy(
            tier=AdaptationTier.CONSTRAINED,
            sherlock_excerpts=3,
            sherlock_chunk_tokens=150,
            squirt_max_input=800,
            squirt_max_output=150,
            max_retries=1
        ),
        AdaptationTier.CRITICAL: AdaptivePolicy(
            tier=AdaptationTier.CRITICAL,
            sherlock_excerpts=2,
            sherlock_chunk_tokens=130,
            squirt_max_input=600,
            squirt_max_output=120,
            max_retries=1
        ),
        AdaptationTier.EMERGENCY: AdaptivePolicy(
            tier=AdaptationTier.EMERGENCY,
            sherlock_excerpts=1,
            sherlock_chunk_tokens=100,
            squirt_max_input=400,
            squirt_max_output=80,
            max_retries=0
        )
    }

    def __init__(self, checkpoint_path: str = "j5a_token_checkpoint.json"):
        """
        Initialize Token Governor.

        Args:
            checkpoint_path: Path to save/load token usage checkpoints
        """
        self.ledger: deque = deque()  # (timestamp, tokens) pairs
        self.checkpoint_path = Path(checkpoint_path)
        self.logger = logging.getLogger("J5ATokenGovernor")

        # Load checkpoint if exists
        self._load_checkpoint()

    def _prune(self):
        """Remove entries outside 5-hour window"""
        now = time()
        while self.ledger and (now - self.ledger[0][0]) > WINDOW_SEC:
            self.ledger.popleft()

    def used_tokens(self) -> int:
        """Get total tokens used in current 5-hour window"""
        self._prune()
        return sum(t for _, t in self.ledger)

    def remaining(self) -> int:
        """Get remaining tokens in budget"""
        return BUDGET - self.used_tokens()

    def remaining_ratio(self) -> float:
        """Get remaining budget as ratio (0.0-1.0)"""
        return self.remaining() / BUDGET

    def current_tier(self) -> AdaptationTier:
        """Determine current adaptation tier based on remaining budget"""
        ratio = self.remaining_ratio()

        if ratio > 0.75:
            return AdaptationTier.FULL
        elif ratio > 0.25:
            return AdaptationTier.MODERATE
        elif ratio > 0.15:
            return AdaptationTier.CONSTRAINED
        elif ratio > 0.05:
            return AdaptationTier.CRITICAL
        else:
            return AdaptationTier.EMERGENCY

    def get_policy(self) -> AdaptivePolicy:
        """Get current adaptive policy based on budget tier"""
        return self.POLICIES[self.current_tier()]

    def can_run(self, estimate: TokenEstimate) -> bool:
        """
        Check if task can run within budget constraints.

        Args:
            estimate: Token usage estimate for task

        Returns:
            True if task fits within budget (including reserve)
        """
        # Keep reserve so we never paint ourselves into a corner
        available = max(0, self.remaining() - RESERVE)
        return estimate.total <= available

    def record(self, input_tokens: int, output_tokens: int):
        """
        Record actual token usage.

        Args:
            input_tokens: Tokens used for input
            output_tokens: Tokens used for output
        """
        total = input_tokens + output_tokens
        self.ledger.append((time(), total))
        self._save_checkpoint()

        self.logger.info(f"Recorded: {input_tokens} in + {output_tokens} out = {total} total "
                        f"(remaining: {self.remaining():,} / {BUDGET:,})")

    def estimate_sherlock_task(
        self,
        package_type: str,
        url_count: int,
        policy: Optional[AdaptivePolicy] = None
    ) -> TokenEstimate:
        """
        Estimate tokens for Sherlock research task.

        Args:
            package_type: 'youtube', 'document', or 'composite'
            url_count: Number of URLs to process
            policy: Override default policy (uses current tier if None)

        Returns:
            TokenEstimate for task
        """
        if policy is None:
            policy = self.get_policy()

        # Input: Query scaffold + excerpts
        input_base = 150  # Query template
        input_per_excerpt = policy.sherlock_chunk_tokens
        input_tokens = input_base + (policy.sherlock_excerpts * input_per_excerpt)

        # Output: Analysis per URL
        output_per_url = {
            'youtube': 350,      # Transcript analysis
            'document': 200,     # Document analysis
            'composite': 250     # Multi-source synthesis
        }
        output_tokens = output_per_url.get(package_type, 250) * url_count

        # Cap output at policy limit
        output_tokens = min(output_tokens, policy.squirt_max_output * url_count)

        total = input_tokens + output_tokens

        return TokenEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total=total,
            confidence=0.85  # High confidence for structured tasks
        )

    def estimate_squirt_task(
        self,
        audio_minutes: int,
        policy: Optional[AdaptivePolicy] = None
    ) -> TokenEstimate:
        """
        Estimate tokens for Squirt voice processing task.

        Args:
            audio_minutes: Length of audio in minutes
            policy: Override default policy (uses current tier if None)

        Returns:
            TokenEstimate for task
        """
        if policy is None:
            policy = self.get_policy()

        # Input: ~150 words/minute transcription
        words_per_minute = 150
        tokens_per_word = 1.3  # Average
        input_tokens = int(audio_minutes * words_per_minute * tokens_per_word)

        # Cap at policy limit
        input_tokens = min(input_tokens, policy.squirt_max_input)

        # Output: Summary/formatting
        output_tokens = policy.squirt_max_output

        total = input_tokens + output_tokens

        return TokenEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total=total,
            confidence=0.7  # Medium confidence (audio length varies)
        )

    def adapt_or_defer(
        self,
        task_id: str,
        estimate: TokenEstimate,
        priority: int
    ) -> Tuple[bool, str, Optional[TokenEstimate]]:
        """
        Decide whether to run, adapt, or defer task.

        Args:
            task_id: Task identifier
            estimate: Initial token estimate
            priority: Task priority (1=highest)

        Returns:
            (can_execute, reason, adapted_estimate)
            - can_execute: True if task can run
            - reason: Explanation of decision
            - adapted_estimate: New estimate if adapted, None if deferred
        """
        tier = self.current_tier()

        # Emergency: Only P0/P1 critical tasks
        if tier == AdaptationTier.EMERGENCY:
            if priority > 1:
                return (False, f"EMERGENCY tier - deferring P{priority} task", None)
            # Try emergency adaptation
            emergency_policy = self.POLICIES[AdaptationTier.EMERGENCY]
            adapted = self.estimate_sherlock_task(
                package_type="composite",  # Conservative estimate
                url_count=1,
                policy=emergency_policy
            )
            if self.can_run(adapted):
                return (True, f"EMERGENCY tier - adapted to minimal config", adapted)
            else:
                return (False, f"EMERGENCY tier - insufficient budget even with adaptation", None)

        # Try current tier first
        if self.can_run(estimate):
            return (True, f"Within budget at {tier.value} tier", estimate)

        # Try adapting to lower tier
        lower_tiers = [
            AdaptationTier.MODERATE,
            AdaptationTier.CONSTRAINED,
            AdaptationTier.CRITICAL
        ]

        for adapt_tier in lower_tiers:
            if adapt_tier.value == tier.value:
                continue  # Skip current tier

            adapted_policy = self.POLICIES[adapt_tier]
            # Re-estimate with adapted policy (conservative: assume composite)
            adapted = self.estimate_sherlock_task(
                package_type="composite",
                url_count=1,
                policy=adapted_policy
            )

            if self.can_run(adapted):
                return (True, f"Adapted from {tier.value} to {adapt_tier.value} tier", adapted)

        # Cannot adapt - must defer
        return (False, f"Cannot fit in budget - defer until next session", None)

    def _save_checkpoint(self):
        """Save current token ledger to checkpoint file"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'ledger': list(self.ledger),
            'used_tokens': self.used_tokens(),
            'remaining': self.remaining(),
            'current_tier': self.current_tier().value
        }

        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def _load_checkpoint(self):
        """Load token ledger from checkpoint file"""
        if not self.checkpoint_path.exists():
            self.logger.info("No checkpoint found - starting fresh")
            return

        try:
            with open(self.checkpoint_path) as f:
                checkpoint = json.load(f)

            # Restore ledger entries still within window
            now = time()
            for ts, tokens in checkpoint['ledger']:
                if (now - ts) <= WINDOW_SEC:
                    self.ledger.append((ts, tokens))

            self.logger.info(f"Loaded checkpoint - {self.used_tokens():,} tokens in window")

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")

    def get_status(self) -> Dict:
        """Get current token governor status"""
        tier = self.current_tier()
        policy = self.get_policy()

        return {
            'budget_total': BUDGET,
            'used': self.used_tokens(),
            'remaining': self.remaining(),
            'remaining_ratio': self.remaining_ratio(),
            'current_tier': tier.value,
            'policy': {
                'sherlock_excerpts': policy.sherlock_excerpts,
                'sherlock_chunk_tokens': policy.sherlock_chunk_tokens,
                'squirt_max_input': policy.squirt_max_input,
                'squirt_max_output': policy.squirt_max_output,
                'max_retries': policy.max_retries
            },
            'reserve': RESERVE,
            'available_for_tasks': max(0, self.remaining() - RESERVE)
        }


if __name__ == "__main__":
    # Test Token Governor
    logging.basicConfig(level=logging.INFO)

    gov = TokenGovernor()

    print("=" * 70)
    print("J5A TOKEN GOVERNOR - Status")
    print("=" * 70)
    print()

    status = gov.get_status()
    print(f"Budget: {status['budget_total']:,} tokens")
    print(f"Used: {status['used']:,} tokens ({status['remaining_ratio']:.1%} remaining)")
    print(f"Available for tasks: {status['available_for_tasks']:,} tokens")
    print(f"Current tier: {status['current_tier'].upper()}")
    print()

    print("Current Policy:")
    for key, val in status['policy'].items():
        print(f"  {key}: {val}")
    print()

    # Test estimates
    print("=" * 70)
    print("TASK ESTIMATES")
    print("=" * 70)
    print()

    # Sherlock composite (2 URLs)
    est1 = gov.estimate_sherlock_task('composite', 2)
    print(f"Sherlock Composite (2 URLs):")
    print(f"  Input: {est1.input_tokens:,} | Output: {est1.output_tokens:,} | Total: {est1.total:,}")
    print(f"  Can run: {gov.can_run(est1)}")
    print()

    # Squirt voice (5 min)
    est2 = gov.estimate_squirt_task(5)
    print(f"Squirt Voice (5 min audio):")
    print(f"  Input: {est2.input_tokens:,} | Output: {est2.output_tokens:,} | Total: {est2.total:,}")
    print(f"  Can run: {gov.can_run(est2)}")
    print()
