#!/usr/bin/env python3
"""
J5A Resource Manager
Manages Claude token budget, RAM, and thermal constraints for overnight execution

Prevents hitting 5-hour session limit by:
- Tracking token usage per task
- Allocating token budgets across task queue
- Preserving session state before token exhaustion
- Coordinating with RAM and thermal limits
"""

import json
import logging
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing thermal management
import sys
sys.path.insert(0, '/home/johnny5/Squirt/src')
from thermal_safety_manager import ThermalSafetyManager, ThermalState


class ResourceConstraint(Enum):
    """Which resource is limiting execution"""
    NONE = "none"
    TOKENS = "tokens"
    RAM = "ram"
    THERMAL = "thermal"
    TIME = "time"


class SessionStrategy(Enum):
    """Strategy when approaching token limit"""
    PRESERVE_AND_PAUSE = "preserve_and_pause"
    COMPLETE_CURRENT = "complete_current"
    EMERGENCY_CHECKPOINT = "emergency_checkpoint"


@dataclass
class ClaudeTokenBudget:
    """Claude Code session token tracking"""

    # Session tracking
    session_start: datetime
    tokens_used: int = 0
    tokens_allocated: int = 0

    # Claude Code token limits (as of 2024)
    MAX_SESSION_TOKENS: int = 200_000  # Approximate 5-hour limit

    # Task allocation
    tokens_per_task_estimate: int = 5_000  # Conservative estimate
    emergency_reserve: int = 10_000  # For checkpointing/cleanup

    def tokens_remaining(self) -> int:
        """Available tokens before hitting limit"""
        return self.MAX_SESSION_TOKENS - self.tokens_used - self.emergency_reserve

    def can_allocate_task(self, estimated_tokens: int = None) -> bool:
        """Check if we can allocate another task"""
        estimate = estimated_tokens or self.tokens_per_task_estimate
        return self.tokens_remaining() >= estimate

    def session_age_hours(self) -> float:
        """How long has session been running"""
        return (datetime.now() - self.session_start).total_seconds() / 3600

    def tokens_per_hour(self) -> float:
        """Current token burn rate"""
        age = self.session_age_hours()
        if age == 0:
            return 0
        return self.tokens_used / age

    def estimated_hours_remaining(self) -> float:
        """Estimated hours before token limit"""
        rate = self.tokens_per_hour()
        if rate == 0:
            return 999.0  # Effectively unlimited
        return self.tokens_remaining() / rate

    def usage_percentage(self) -> float:
        """Percentage of token budget used"""
        return (self.tokens_used / self.MAX_SESSION_TOKENS) * 100


@dataclass
class ResourceSnapshot:
    """Current system resource state"""
    timestamp: datetime

    # Token resources
    tokens_used: int
    tokens_remaining: int
    token_budget_pct: float

    # RAM resources
    ram_total_gb: float
    ram_available_gb: float
    ram_used_pct: float

    # Thermal resources
    cpu_temp: Optional[float]
    thermal_state: str

    # Constraints
    limiting_resource: ResourceConstraint
    can_continue: bool
    reason: Optional[str] = None


@dataclass
class TaskResourceEstimate:
    """Estimated resource requirements for a task"""
    task_id: str
    estimated_tokens: int
    estimated_ram_gb: float
    estimated_duration_minutes: int
    thermal_risk: str  # "low", "medium", "high"


class J5AResourceManager:
    """
    Coordinate all resources for J5A overnight execution

    Manages:
    - Claude token budget (prevent 5-hour session timeout)
    - RAM availability (3.7GB total, 2.4GB target available)
    - Thermal safety (coordinate with Squirt thermal manager)
    - Time constraints (overnight execution window)
    """

    def __init__(self,
                 max_ram_gb: float = 3.7,
                 target_available_ram_gb: float = 2.4,
                 thermal_manager: Optional[ThermalSafetyManager] = None):

        self.logger = logging.getLogger("J5AResourceManager")

        # Resource limits
        self.max_ram_gb = max_ram_gb
        self.target_available_ram_gb = target_available_ram_gb

        # Token budget tracking
        self.token_budget = ClaudeTokenBudget(
            session_start=datetime.now(),
            tokens_used=0
        )

        # Thermal management
        self.thermal_manager = thermal_manager or ThermalSafetyManager()

        # Resource tracking
        self.snapshots: List[ResourceSnapshot] = []
        self.session_log_path = Path("j5a_session_log.json")

        # Task estimates
        self.task_estimates: Dict[str, TaskResourceEstimate] = {}

        # Session preservation
        self.checkpoint_path = Path("j5a_checkpoint.json")

        self.logger.info("🎛️  J5A Resource Manager initialized")
        self.logger.info(f"   Max RAM: {max_ram_gb:.1f}GB")
        self.logger.info(f"   Token budget: {self.token_budget.MAX_SESSION_TOKENS:,}")

    def get_resource_snapshot(self) -> ResourceSnapshot:
        """Get current resource availability snapshot"""

        # RAM status
        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_available_gb = ram.available / (1024**3)
        ram_used_pct = ram.percent

        # Thermal status
        try:
            thermal_reading = self.thermal_manager.take_reading()
            cpu_temp = thermal_reading.cpu_temp if thermal_reading else None
            thermal_state = thermal_reading.thermal_state.value if thermal_reading else "unknown"
        except Exception as e:
            self.logger.warning(f"Failed to read thermal status: {e}")
            thermal_reading = None
            cpu_temp = None
            thermal_state = "unknown"

        # Determine limiting resource
        limiting_resource = ResourceConstraint.NONE
        can_continue = True
        reason = None

        # Check tokens (highest priority)
        if self.token_budget.tokens_remaining() < 15000:
            limiting_resource = ResourceConstraint.TOKENS
            can_continue = False
            reason = f"Token budget exhausted ({self.token_budget.usage_percentage():.1f}% used)"

        # Check thermal (safety priority)
        elif thermal_reading and thermal_reading.thermal_state in [ThermalState.CRITICAL, ThermalState.EMERGENCY]:
            limiting_resource = ResourceConstraint.THERMAL
            can_continue = False
            reason = f"Thermal state: {thermal_state} ({cpu_temp}°C)"

        # Check RAM
        elif ram_available_gb < 1.5:  # Critical threshold
            limiting_resource = ResourceConstraint.RAM
            can_continue = False
            reason = f"Insufficient RAM ({ram_available_gb:.1f}GB available)"

        # Warnings (can continue but cautiously)
        elif self.token_budget.tokens_remaining() < 30000:
            limiting_resource = ResourceConstraint.TOKENS
            reason = f"Token budget low ({self.token_budget.tokens_remaining():,} remaining)"

        elif ram_available_gb < 2.0:
            limiting_resource = ResourceConstraint.RAM
            reason = f"RAM constrained ({ram_available_gb:.1f}GB available)"

        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            tokens_used=self.token_budget.tokens_used,
            tokens_remaining=self.token_budget.tokens_remaining(),
            token_budget_pct=self.token_budget.usage_percentage(),
            ram_total_gb=ram_total_gb,
            ram_available_gb=ram_available_gb,
            ram_used_pct=ram_used_pct,
            cpu_temp=cpu_temp,
            thermal_state=thermal_state,
            limiting_resource=limiting_resource,
            can_continue=can_continue,
            reason=reason
        )

        self.snapshots.append(snapshot)
        self._log_snapshot(snapshot)

        return snapshot

    def can_execute_task(self, task_id: str,
                         estimated_tokens: Optional[int] = None,
                         estimated_ram_gb: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if task can execute within resource constraints

        Returns:
            (can_execute: bool, reason: str)
        """
        snapshot = self.get_resource_snapshot()

        # Can't continue at all
        if not snapshot.can_continue:
            return False, snapshot.reason

        # Get task estimate or use defaults
        estimate = self.task_estimates.get(task_id)
        tokens_needed = estimated_tokens or (estimate.estimated_tokens if estimate else 5000)
        ram_needed = estimated_ram_gb or (estimate.estimated_ram_gb if estimate else 0.5)

        # Check token budget
        if not self.token_budget.can_allocate_task(tokens_needed):
            return False, f"Insufficient tokens ({self.token_budget.tokens_remaining():,} remaining, need ~{tokens_needed:,})"

        # Check RAM availability
        ram_after_task = snapshot.ram_available_gb - ram_needed
        if ram_after_task < 1.0:  # Minimum 1GB free
            return False, f"Insufficient RAM ({snapshot.ram_available_gb:.1f}GB available, need {ram_needed:.1f}GB)"

        # Check thermal state
        if snapshot.thermal_state in ["hot", "critical", "emergency"]:
            return False, f"Thermal constraint: {snapshot.thermal_state} ({snapshot.cpu_temp}°C)"

        return True, "All resources available"

    def allocate_task_resources(self, task_id: str, estimate: TaskResourceEstimate):
        """Allocate resources for task execution"""
        self.task_estimates[task_id] = estimate
        self.token_budget.tokens_allocated += estimate.estimated_tokens
        self.logger.info(f"📊 Allocated resources for {task_id}:")
        self.logger.info(f"   Tokens: {estimate.estimated_tokens:,}")
        self.logger.info(f"   RAM: {estimate.estimated_ram_gb:.1f}GB")
        self.logger.info(f"   Duration: {estimate.estimated_duration_minutes}min")

    def record_task_completion(self, task_id: str, actual_tokens: int):
        """Record actual token usage after task completion"""
        self.token_budget.tokens_used += actual_tokens

        estimate = self.task_estimates.get(task_id)
        if estimate:
            # Update estimate accuracy
            variance = actual_tokens - estimate.estimated_tokens
            self.logger.info(f"✅ Task {task_id} completed")
            self.logger.info(f"   Tokens used: {actual_tokens:,} (estimate: {estimate.estimated_tokens:,}, variance: {variance:+,})")

    def get_token_allocation_plan(self, task_queue: List[Dict]) -> Dict:
        """
        Plan token allocation across task queue

        Returns:
            Allocation plan with tasks that fit in budget
        """
        available_tokens = self.token_budget.tokens_remaining()

        plan = {
            "available_tokens": available_tokens,
            "tasks_can_execute": [],
            "tasks_deferred": [],
            "estimated_completion_time": None
        }

        tokens_allocated = 0
        time_allocated = 0

        for task in task_queue:
            task_id = task.get("task_id", "unknown")
            estimate = self.task_estimates.get(task_id)

            estimated_tokens = estimate.estimated_tokens if estimate else 5000
            estimated_time = estimate.estimated_duration_minutes if estimate else 10

            if tokens_allocated + estimated_tokens <= available_tokens:
                plan["tasks_can_execute"].append({
                    "task_id": task_id,
                    "tokens": estimated_tokens,
                    "minutes": estimated_time
                })
                tokens_allocated += estimated_tokens
                time_allocated += estimated_time
            else:
                plan["tasks_deferred"].append({
                    "task_id": task_id,
                    "reason": "insufficient_tokens"
                })

        plan["estimated_completion_time"] = f"{time_allocated // 60}h {time_allocated % 60}m"

        return plan

    def should_checkpoint_session(self) -> Tuple[bool, SessionStrategy]:
        """
        Determine if we should checkpoint and pause session

        Returns:
            (should_checkpoint: bool, strategy: SessionStrategy)
        """
        snapshot = self.get_resource_snapshot()

        # Emergency: <10k tokens remaining
        if self.token_budget.tokens_remaining() < 10000:
            return True, SessionStrategy.EMERGENCY_CHECKPOINT

        # Planned: <30k tokens, can complete current task
        if self.token_budget.tokens_remaining() < 30000:
            return True, SessionStrategy.COMPLETE_CURRENT

        # Thermal emergency
        if snapshot.thermal_state in ["critical", "emergency"]:
            return True, SessionStrategy.EMERGENCY_CHECKPOINT

        return False, SessionStrategy.PRESERVE_AND_PAUSE

    def create_checkpoint(self, queue_state: Dict, current_task: Optional[Dict] = None):
        """Create session checkpoint for resumption"""
        checkpoint = {
            "created_at": datetime.now().isoformat(),
            "session_start": self.token_budget.session_start.isoformat(),
            "tokens_used": self.token_budget.tokens_used,
            "session_hours": self.token_budget.session_age_hours(),
            "queue_state": queue_state,
            "current_task": current_task,
            "resource_snapshot": asdict(self.get_resource_snapshot()),
            "reason": "Token budget preservation"
        }

        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        self.logger.info(f"💾 Session checkpoint saved: {self.checkpoint_path}")
        self.logger.info(f"   Session duration: {checkpoint['session_hours']:.1f}h")
        self.logger.info(f"   Tokens used: {checkpoint['tokens_used']:,}")
        self.logger.info(f"   Tasks remaining: {len(queue_state.get('queued_tasks', []))}")

    def load_checkpoint(self) -> Optional[Dict]:
        """Load previous session checkpoint"""
        if not self.checkpoint_path.exists():
            return None

        try:
            with open(self.checkpoint_path, 'r') as f:
                checkpoint = json.load(f)

            self.logger.info(f"📂 Loaded checkpoint from {checkpoint['created_at']}")
            return checkpoint

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def _log_snapshot(self, snapshot: ResourceSnapshot):
        """Log resource snapshot for analysis"""
        log_entry = {
            "timestamp": snapshot.timestamp.isoformat(),
            "tokens": {
                "used": snapshot.tokens_used,
                "remaining": snapshot.tokens_remaining,
                "budget_pct": round(snapshot.token_budget_pct, 2)
            },
            "ram": {
                "available_gb": round(snapshot.ram_available_gb, 2),
                "used_pct": round(snapshot.ram_used_pct, 1)
            },
            "thermal": {
                "cpu_temp": snapshot.cpu_temp,
                "state": snapshot.thermal_state
            },
            "status": {
                "limiting_resource": snapshot.limiting_resource.value,
                "can_continue": snapshot.can_continue,
                "reason": snapshot.reason
            }
        }

        # Append to session log
        with open(self.session_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        snapshot = self.get_resource_snapshot()

        return {
            "session_age_hours": round(self.token_budget.session_age_hours(), 2),
            "tokens": {
                "used": self.token_budget.tokens_used,
                "remaining": self.token_budget.tokens_remaining(),
                "budget_pct": round(self.token_budget.usage_percentage(), 1),
                "burn_rate_per_hour": round(self.token_budget.tokens_per_hour(), 0),
                "hours_remaining": round(self.token_budget.estimated_hours_remaining(), 2)
            },
            "ram": {
                "total_gb": round(snapshot.ram_total_gb, 2),
                "available_gb": round(snapshot.ram_available_gb, 2),
                "used_pct": round(snapshot.ram_used_pct, 1)
            },
            "thermal": {
                "cpu_temp": snapshot.cpu_temp,
                "state": snapshot.thermal_state
            },
            "status": {
                "can_continue": snapshot.can_continue,
                "limiting_resource": snapshot.limiting_resource.value,
                "reason": snapshot.reason
            }
        }

    def print_session_summary(self):
        """Print human-readable session summary"""
        summary = self.get_session_summary()

        print("\n" + "=" * 80)
        print("🎛️  J5A RESOURCE MANAGER - SESSION SUMMARY")
        print("=" * 80)

        print(f"\n⏱️  Session Duration: {summary['session_age_hours']}h")

        print(f"\n🎫 Token Budget:")
        print(f"   Used: {summary['tokens']['used']:,} / 200,000 ({summary['tokens']['budget_pct']}%)")
        print(f"   Remaining: {summary['tokens']['remaining']:,}")
        print(f"   Burn rate: {summary['tokens']['burn_rate_per_hour']:,.0f} tokens/hour")
        print(f"   Est. time remaining: {summary['tokens']['hours_remaining']:.1f}h")

        print(f"\n💾 RAM Status:")
        print(f"   Available: {summary['ram']['available_gb']:.2f}GB / {summary['ram']['total_gb']:.2f}GB")
        print(f"   Used: {summary['ram']['used_pct']:.1f}%")

        print(f"\n🌡️  Thermal Status:")
        print(f"   CPU Temp: {summary['thermal']['cpu_temp']}°C")
        print(f"   State: {summary['thermal']['state']}")

        print(f"\n📊 Execution Status:")
        can_continue_icon = "✅" if summary['status']['can_continue'] else "🛑"
        print(f"   {can_continue_icon} Can continue: {summary['status']['can_continue']}")
        print(f"   Limiting resource: {summary['status']['limiting_resource']}")
        if summary['status']['reason']:
            print(f"   Reason: {summary['status']['reason']}")

        print("=" * 80)


if __name__ == "__main__":
    """Test resource manager"""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing J5A Resource Manager")
    print("=" * 80)

    # Create resource manager
    rm = J5AResourceManager()

    # Simulate session with token usage
    rm.token_budget.tokens_used = 50000

    # Add task estimates
    rm.allocate_task_resources("test_task_1", TaskResourceEstimate(
        task_id="test_task_1",
        estimated_tokens=5000,
        estimated_ram_gb=0.5,
        estimated_duration_minutes=10,
        thermal_risk="low"
    ))

    # Check if task can execute
    can_execute, reason = rm.can_execute_task("test_task_1")
    print(f"\n✅ Task execution check: {can_execute}")
    print(f"   Reason: {reason}")

    # Get session summary
    rm.print_session_summary()

    # Check checkpoint status
    should_checkpoint, strategy = rm.should_checkpoint_session()
    print(f"\n💾 Should checkpoint: {should_checkpoint}")
    print(f"   Strategy: {strategy.value if should_checkpoint else 'N/A'}")

    print("\n" + "=" * 80)
    print("✅ Resource manager test complete")