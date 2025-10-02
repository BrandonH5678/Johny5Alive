#!/usr/bin/env python3
"""
J5A Session Manager - Multi-Session Queue Execution

Handles checkpoint/resume logic for overnight queues that span multiple
Claude Code sessions due to 200K token / 5-hour limit.

Key Features:
- Save queue progress at session boundaries
- Resume from last completed task
- Token budget tracking across sessions
- Priority re-evaluation on resume
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging


@dataclass
class SessionCheckpoint:
    """Session execution checkpoint"""
    session_id: str
    session_start: str
    session_end: Optional[str]
    tasks_completed: List[str]
    tasks_deferred: List[str]
    tasks_failed: List[str]
    token_budget_used: int
    token_budget_remaining: int
    next_task_id: Optional[str]
    completion_reason: str  # 'token_exhausted', 'queue_complete', 'error'


class J5ASessionManager:
    """
    Multi-session queue execution manager.

    Handles:
    - Session checkpointing
    - Queue state preservation
    - Resume from interruption
    - Token budget tracking across sessions
    """

    def __init__(
        self,
        db_path: str = "j5a_queue_manager.db",
        checkpoint_path: str = "j5a_session_checkpoint.json"
    ):
        """
        Initialize Session Manager.

        Args:
            db_path: Path to J5A queue database
            checkpoint_path: Path to session checkpoint file
        """
        self.db_path = Path(db_path)
        self.checkpoint_path = Path(checkpoint_path)
        self.logger = logging.getLogger("J5ASessionManager")
        self.current_session: Optional[SessionCheckpoint] = None

    def start_session(self, session_id: Optional[str] = None) -> SessionCheckpoint:
        """
        Start new session or resume from checkpoint.

        Args:
            session_id: Optional session ID (generated if None)

        Returns:
            SessionCheckpoint for current session
        """
        # Check for existing checkpoint
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path) as f:
                checkpoint_data = json.load(f)

            # Check if previous session incomplete
            if checkpoint_data.get('session_end') is None:
                self.logger.info("Resuming from previous session checkpoint")
                self.current_session = SessionCheckpoint(**checkpoint_data)
                return self.current_session

        # Start new session
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.current_session = SessionCheckpoint(
            session_id=session_id,
            session_start=datetime.now().isoformat(),
            session_end=None,
            tasks_completed=[],
            tasks_deferred=[],
            tasks_failed=[],
            token_budget_used=0,
            token_budget_remaining=200000,
            next_task_id=None,
            completion_reason=""
        )

        self._save_checkpoint()
        self.logger.info(f"Started new session: {session_id}")
        return self.current_session

    def record_task_completion(
        self,
        task_id: str,
        status: str,
        tokens_used: int
    ):
        """
        Record task completion in session.

        Args:
            task_id: Completed task ID
            status: 'completed', 'deferred', or 'failed'
            tokens_used: Tokens consumed by task
        """
        if not self.current_session:
            raise RuntimeError("No active session - call start_session() first")

        if status == 'completed':
            self.current_session.tasks_completed.append(task_id)
        elif status == 'deferred':
            self.current_session.tasks_deferred.append(task_id)
        elif status == 'failed':
            self.current_session.tasks_failed.append(task_id)

        self.current_session.token_budget_used += tokens_used
        self.current_session.token_budget_remaining -= tokens_used

        self._save_checkpoint()

    def set_next_task(self, task_id: Optional[str]):
        """
        Set next task to execute.

        Args:
            task_id: ID of next task (None if queue complete)
        """
        if not self.current_session:
            raise RuntimeError("No active session")

        self.current_session.next_task_id = task_id
        self._save_checkpoint()

    def end_session(self, reason: str):
        """
        End current session.

        Args:
            reason: Completion reason ('token_exhausted', 'queue_complete', 'error')
        """
        if not self.current_session:
            raise RuntimeError("No active session")

        self.current_session.session_end = datetime.now().isoformat()
        self.current_session.completion_reason = reason

        self._save_checkpoint()

        self.logger.info(
            f"Session ended: {reason} | "
            f"Completed: {len(self.current_session.tasks_completed)}, "
            f"Deferred: {len(self.current_session.tasks_deferred)}, "
            f"Failed: {len(self.current_session.tasks_failed)}"
        )

    def get_resume_task_id(self) -> Optional[str]:
        """
        Get task ID to resume from.

        Returns:
            Task ID to start from, or None if starting fresh
        """
        if not self.current_session:
            return None

        return self.current_session.next_task_id

    def get_queued_tasks(self) -> List[str]:
        """
        Get list of queued task IDs.

        Returns:
            List of task IDs still in queue
        """
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT te.task_id
            FROM task_executions te
            WHERE te.status = 'queued'
            ORDER BY te.created_timestamp ASC
        ''')

        task_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return task_ids

    def should_continue(self, token_governor) -> bool:
        """
        Check if session should continue based on token budget.

        Args:
            token_governor: TokenGovernor instance

        Returns:
            True if session can continue, False if should checkpoint and stop
        """
        if not self.current_session:
            return True

        # Update budget from governor
        self.current_session.token_budget_remaining = token_governor.remaining()

        # Stop if budget critically low (< 5%)
        if token_governor.remaining_ratio() < 0.05:
            self.logger.warning("Token budget critical - stopping session")
            return False

        return True

    def _save_checkpoint(self):
        """Save current session checkpoint to file"""
        if not self.current_session:
            return

        checkpoint_data = asdict(self.current_session)

        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def get_session_report(self) -> Dict:
        """
        Get session execution report.

        Returns:
            Dict with session statistics
        """
        if not self.current_session:
            return {"error": "No active session"}

        return {
            "session_id": self.current_session.session_id,
            "session_start": self.current_session.session_start,
            "session_end": self.current_session.session_end,
            "tasks_completed": len(self.current_session.tasks_completed),
            "tasks_deferred": len(self.current_session.tasks_deferred),
            "tasks_failed": len(self.current_session.tasks_failed),
            "token_budget_used": self.current_session.token_budget_used,
            "token_budget_remaining": self.current_session.token_budget_remaining,
            "next_task_id": self.current_session.next_task_id,
            "completion_reason": self.current_session.completion_reason
        }


if __name__ == "__main__":
    # Test Session Manager
    logging.basicConfig(level=logging.INFO)

    session_mgr = J5ASessionManager()

    # Start session
    checkpoint = session_mgr.start_session()
    print(f"Started session: {checkpoint.session_id}")

    # Simulate task execution
    session_mgr.record_task_completion("task_1", "completed", 5000)
    session_mgr.record_task_completion("task_2", "completed", 8000)
    session_mgr.record_task_completion("task_3", "deferred", 0)

    session_mgr.set_next_task("task_4")

    # Get report
    report = session_mgr.get_session_report()
    print("\nSession Report:")
    for key, val in report.items():
        print(f"  {key}: {val}")

    # End session
    session_mgr.end_session("token_exhausted")
