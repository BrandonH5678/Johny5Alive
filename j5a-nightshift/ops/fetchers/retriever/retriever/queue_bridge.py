"""
QueueBridge - Task queue integration with publishing and status tracking
"""
from __future__ import annotations
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QueueBridge:
    """
    Bridges retrieval tasks to queue systems for async execution

    Supports:
    - Task publishing to queues
    - Status tracking
    - Multiple backend types (process, file, database)
    - Result retrieval
    - Task cancellation
    """

    def __init__(
        self,
        backend: str = 'process',
        queue_path: Optional[str] = None
    ):
        """
        Initialize QueueBridge

        Args:
            backend: Queue backend type ('process', 'file', 'database')
            queue_path: Path for file/database backend storage
        """
        self.backend = backend.lower()
        self.queue_path = Path(queue_path) if queue_path else Path('/tmp/retriever_queue')

        # Initialize backend
        if self.backend == 'database':
            self._init_database()
        elif self.backend == 'file':
            self.queue_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"QueueBridge initialized with {self.backend} backend")

    def _init_database(self):
        """Initialize database backend"""
        db_path = self.queue_path / 'queue.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                result TEXT,
                error TEXT
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database backend initialized at {db_path}")

    def publish(
        self,
        channel: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish task to queue

        Args:
            channel: Queue channel/topic name
            payload: Task payload data
            task_id: Optional task identifier (generated if not provided)

        Returns:
            {
                'task_id': 'abc-123',
                'channel': 'retrieval',
                'status': 'queued',
                'published_at': '2024-01-01T12:00:00'
            }
        """
        task_id = task_id or self._generate_task_id()

        logger.info(f"Publishing task {task_id} to channel '{channel}'")

        if self.backend == 'process':
            result = self._publish_process(channel, payload, task_id)
        elif self.backend == 'file':
            result = self._publish_file(channel, payload, task_id)
        elif self.backend == 'database':
            result = self._publish_database(channel, payload, task_id)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        return result

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status

        Args:
            task_id: Task identifier

        Returns:
            {
                'task_id': 'abc-123',
                'status': 'completed',
                'created_at': '2024-01-01T12:00:00',
                'updated_at': '2024-01-01T12:05:00',
                'result': {...} or None,
                'error': 'Error message' or None
            }
        """
        logger.info(f"Getting status for task {task_id}")

        if self.backend == 'process':
            return self._get_status_process(task_id)
        elif self.backend == 'file':
            return self._get_status_file(task_id)
        elif self.backend == 'database':
            return self._get_status_database(task_id)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def list_tasks(
        self,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tasks in queue

        Args:
            channel: Filter by channel (optional)
            status: Filter by status (optional)
            limit: Maximum number of tasks to return

        Returns:
            List of task dictionaries
        """
        logger.info(f"Listing tasks (channel={channel}, status={status}, limit={limit})")

        if self.backend == 'process':
            return self._list_tasks_process(channel, status, limit)
        elif self.backend == 'file':
            return self._list_tasks_file(channel, status, limit)
        elif self.backend == 'database':
            return self._list_tasks_database(channel, status, limit)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel pending task

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled, False otherwise
        """
        logger.info(f"Cancelling task {task_id}")

        if self.backend == 'database':
            return self._cancel_task_database(task_id)
        elif self.backend == 'file':
            return self._cancel_task_file(task_id)
        else:
            logger.warning(f"Cancel not supported for {self.backend} backend")
            return False

    # Process backend methods

    def _publish_process(self, channel: str, payload: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Publish to process-based queue (in-memory, no persistence)"""
        return {
            'task_id': task_id,
            'channel': channel,
            'status': 'queued',
            'published_at': datetime.now().isoformat(),
            'note': 'Process backend does not persist tasks'
        }

    def _get_status_process(self, task_id: str) -> Dict[str, Any]:
        """Get status from process backend"""
        return {
            'task_id': task_id,
            'status': 'unknown',
            'note': 'Process backend does not track status'
        }

    def _list_tasks_process(self, channel: Optional[str], status: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """List tasks from process backend"""
        return []

    # File backend methods

    def _publish_file(self, channel: str, payload: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Publish to file-based queue"""
        channel_dir = self.queue_path / channel
        channel_dir.mkdir(parents=True, exist_ok=True)

        task_file = channel_dir / f'{task_id}.json'

        task_data = {
            'task_id': task_id,
            'channel': channel,
            'payload': payload,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Task written to {task_file}")

        return {
            'task_id': task_id,
            'channel': channel,
            'status': 'queued',
            'published_at': task_data['created_at']
        }

    def _get_status_file(self, task_id: str) -> Dict[str, Any]:
        """Get status from file backend"""
        # Search all channels for this task
        for channel_dir in self.queue_path.iterdir():
            if not channel_dir.is_dir():
                continue

            task_file = channel_dir / f'{task_id}.json'
            if task_file.exists():
                with open(task_file, 'r') as f:
                    return json.load(f)

        return {
            'task_id': task_id,
            'status': 'not_found'
        }

    def _list_tasks_file(self, channel: Optional[str], status: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """List tasks from file backend"""
        tasks = []

        search_dirs = [self.queue_path / channel] if channel else list(self.queue_path.iterdir())

        for channel_dir in search_dirs:
            if not channel_dir.is_dir():
                continue

            for task_file in channel_dir.glob('*.json'):
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                # Filter by status if specified
                if status and task_data.get('status') != status:
                    continue

                tasks.append(task_data)

                if len(tasks) >= limit:
                    break

        return tasks[:limit]

    def _cancel_task_file(self, task_id: str) -> bool:
        """Cancel task in file backend"""
        # Search all channels for this task
        for channel_dir in self.queue_path.iterdir():
            if not channel_dir.is_dir():
                continue

            task_file = channel_dir / f'{task_id}.json'
            if task_file.exists():
                # Update status to cancelled
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                task_data['status'] = 'cancelled'
                task_data['updated_at'] = datetime.now().isoformat()

                with open(task_file, 'w') as f:
                    json.dump(task_data, f, indent=2)

                return True

        return False

    # Database backend methods

    def _publish_database(self, channel: str, payload: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Publish to database-based queue"""
        db_path = self.queue_path / 'queue.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        created_at = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO tasks (task_id, channel, payload, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (task_id, channel, json.dumps(payload), created_at))

        conn.commit()
        conn.close()

        logger.info(f"Task inserted into database")

        return {
            'task_id': task_id,
            'channel': channel,
            'status': 'queued',
            'published_at': created_at
        }

    def _get_status_database(self, task_id: str) -> Dict[str, Any]:
        """Get status from database backend"""
        db_path = self.queue_path / 'queue.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT task_id, channel, status, created_at, updated_at, result, error
            FROM tasks
            WHERE task_id = ?
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {'task_id': task_id, 'status': 'not_found'}

        return {
            'task_id': row[0],
            'channel': row[1],
            'status': row[2],
            'created_at': row[3],
            'updated_at': row[4],
            'result': json.loads(row[5]) if row[5] else None,
            'error': row[6]
        }

    def _list_tasks_database(self, channel: Optional[str], status: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """List tasks from database backend"""
        db_path = self.queue_path / 'queue.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        query = "SELECT task_id, channel, status, created_at, updated_at FROM tasks WHERE 1=1"
        params = []

        if channel:
            query += " AND channel = ?"
            params.append(channel)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'task_id': row[0],
                'channel': row[1],
                'status': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })

        conn.close()

        return tasks

    def _cancel_task_database(self, task_id: str) -> bool:
        """Cancel task in database backend"""
        db_path = self.queue_path / 'queue.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks
            SET status = 'cancelled', updated_at = ?
            WHERE task_id = ? AND status = 'pending'
        """, (datetime.now().isoformat(), task_id))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def _generate_task_id(self) -> str:
        """Generate unique task identifier"""
        return f'task_{uuid.uuid4().hex[:12]}'
