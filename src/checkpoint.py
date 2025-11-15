"""
Checkpointing & Recovery System

Enables saving workflow state and resuming execution from failures.
Supports multiple storage backends (filesystem, SQLite, Redis).
"""

import asyncio
import json
import pickle
import time
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class CheckpointStatus(Enum):
    """Checkpoint status"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Checkpoint:
    """
    Checkpoint data structure

    Stores complete execution state for recovery.
    """
    checkpoint_id: str
    execution_id: str
    timestamp: float
    status: CheckpointStatus

    # Execution state
    current_node: Optional[str] = None
    completed_nodes: List[str] = field(default_factory=list)
    pending_nodes: List[str] = field(default_factory=list)

    # Data state
    workflow_state: Dict[str, Any] = field(default_factory=dict)
    task_results: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'checkpoint_id': self.checkpoint_id,
            'execution_id': self.execution_id,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'current_node': self.current_node,
            'completed_nodes': self.completed_nodes,
            'pending_nodes': self.pending_nodes,
            'workflow_state': self.workflow_state,
            'task_results': self.task_results,
            'metadata': self.metadata,
            'error': self.error
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary"""
        return Checkpoint(
            checkpoint_id=data['checkpoint_id'],
            execution_id=data['execution_id'],
            timestamp=data['timestamp'],
            status=CheckpointStatus(data['status']),
            current_node=data.get('current_node'),
            completed_nodes=data.get('completed_nodes', []),
            pending_nodes=data.get('pending_nodes', []),
            workflow_state=data.get('workflow_state', {}),
            task_results=data.get('task_results', {}),
            metadata=data.get('metadata', {}),
            error=data.get('error')
        )


class CheckpointBackend(ABC):
    """Abstract checkpoint storage backend"""

    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint"""
        pass

    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint by ID"""
        pass

    @abstractmethod
    async def load_latest(self, execution_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint for execution"""
        pass

    @abstractmethod
    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        limit: int = 100
    ) -> List[Checkpoint]:
        """List checkpoints with filters"""
        pass

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        pass

    @abstractmethod
    async def cleanup(
        self,
        execution_id: Optional[str] = None,
        older_than: Optional[float] = None,
        keep_latest: int = 1
    ) -> int:
        """Cleanup old checkpoints"""
        pass


class FileSystemBackend(CheckpointBackend):
    """
    File system checkpoint backend

    Stores checkpoints as JSON files in a directory.
    """

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """
        Initialize filesystem backend

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get path for checkpoint file"""
        return self.checkpoint_dir / f"{checkpoint_id}.json"

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to JSON file"""
        path = self._get_checkpoint_path(checkpoint.checkpoint_id)

        # Save to file
        with open(path, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from JSON file"""
        path = self._get_checkpoint_path(checkpoint_id)

        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = json.load(f)

        return Checkpoint.from_dict(data)

    async def load_latest(self, execution_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint for execution"""
        checkpoints = await self.list_checkpoints(execution_id=execution_id, limit=1)
        return checkpoints[0] if checkpoints else None

    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        limit: int = 100
    ) -> List[Checkpoint]:
        """List checkpoints with filters"""
        checkpoints = []

        # Read all checkpoint files
        for path in sorted(self.checkpoint_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                checkpoint = Checkpoint.from_dict(data)

                # Apply filters
                if execution_id and checkpoint.execution_id != execution_id:
                    continue
                if status and checkpoint.status != status:
                    continue

                checkpoints.append(checkpoint)

                if len(checkpoints) >= limit:
                    break

            except Exception as e:
                print(f"⚠️  Failed to load checkpoint {path}: {e}")
                continue

        return checkpoints

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint file"""
        path = self._get_checkpoint_path(checkpoint_id)

        if path.exists():
            path.unlink()
            return True

        return False

    async def cleanup(
        self,
        execution_id: Optional[str] = None,
        older_than: Optional[float] = None,
        keep_latest: int = 1
    ) -> int:
        """Cleanup old checkpoints"""
        deleted_count = 0

        # Get all checkpoints grouped by execution_id
        all_checkpoints = await self.list_checkpoints(execution_id=execution_id, limit=10000)

        # Group by execution_id
        by_execution: Dict[str, List[Checkpoint]] = {}
        for cp in all_checkpoints:
            if cp.execution_id not in by_execution:
                by_execution[cp.execution_id] = []
            by_execution[cp.execution_id].append(cp)

        # Cleanup each execution's checkpoints
        for exec_id, checkpoints in by_execution.items():
            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

            # Keep latest N checkpoints
            to_delete = checkpoints[keep_latest:]

            # Filter by age if specified
            if older_than:
                current_time = time.time()
                to_delete = [c for c in to_delete if (current_time - c.timestamp) > older_than]

            # Delete
            for cp in to_delete:
                if await self.delete(cp.checkpoint_id):
                    deleted_count += 1

        return deleted_count


class SQLiteBackend(CheckpointBackend):
    """
    SQLite checkpoint backend

    Stores checkpoints in SQLite database for better querying.
    """

    def __init__(self, db_path: str = ".checkpoints/checkpoints.db"):
        """
        Initialize SQLite backend

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                current_node TEXT,
                completed_nodes TEXT,
                pending_nodes TEXT,
                workflow_state TEXT,
                task_results TEXT,
                metadata TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_id ON checkpoints(execution_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON checkpoints(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON checkpoints(status)")

        conn.commit()
        conn.close()

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO checkpoints
            (checkpoint_id, execution_id, timestamp, status, current_node,
             completed_nodes, pending_nodes, workflow_state, task_results, metadata, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            checkpoint.checkpoint_id,
            checkpoint.execution_id,
            checkpoint.timestamp,
            checkpoint.status.value,
            checkpoint.current_node,
            json.dumps(checkpoint.completed_nodes),
            json.dumps(checkpoint.pending_nodes),
            json.dumps(checkpoint.workflow_state),
            json.dumps(checkpoint.task_results),
            json.dumps(checkpoint.metadata),
            checkpoint.error
        ))

        conn.commit()
        conn.close()

    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, execution_id, timestamp, status, current_node,
                   completed_nodes, pending_nodes, workflow_state, task_results, metadata, error
            FROM checkpoints
            WHERE checkpoint_id = ?
        """, (checkpoint_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_checkpoint(row)

    async def load_latest(self, execution_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint for execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, execution_id, timestamp, status, current_node,
                   completed_nodes, pending_nodes, workflow_state, task_results, metadata, error
            FROM checkpoints
            WHERE execution_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (execution_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_checkpoint(row)

    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        limit: int = 100
    ) -> List[Checkpoint]:
        """List checkpoints with filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT checkpoint_id, execution_id, timestamp, status, current_node,
                   completed_nodes, pending_nodes, workflow_state, task_results, metadata, error
            FROM checkpoints
            WHERE 1=1
        """
        params = []

        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_checkpoint(row) for row in rows]

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    async def cleanup(
        self,
        execution_id: Optional[str] = None,
        older_than: Optional[float] = None,
        keep_latest: int = 1
    ) -> int:
        """Cleanup old checkpoints"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if execution_id:
            # Cleanup specific execution
            query = """
                DELETE FROM checkpoints
                WHERE execution_id = ?
                AND checkpoint_id NOT IN (
                    SELECT checkpoint_id FROM checkpoints
                    WHERE execution_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """
            params = [execution_id, execution_id, keep_latest]

            if older_than:
                cutoff_time = time.time() - older_than
                query += " AND timestamp < ?"
                params.append(cutoff_time)

            cursor.execute(query, params)
        else:
            # Cleanup all executions
            # This is more complex - would need to iterate through executions
            # For now, just delete old checkpoints
            if older_than:
                cutoff_time = time.time() - older_than
                cursor.execute("DELETE FROM checkpoints WHERE timestamp < ?", (cutoff_time,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def _row_to_checkpoint(self, row: tuple) -> Checkpoint:
        """Convert database row to Checkpoint"""
        return Checkpoint(
            checkpoint_id=row[0],
            execution_id=row[1],
            timestamp=row[2],
            status=CheckpointStatus(row[3]),
            current_node=row[4],
            completed_nodes=json.loads(row[5]) if row[5] else [],
            pending_nodes=json.loads(row[6]) if row[6] else [],
            workflow_state=json.loads(row[7]) if row[7] else {},
            task_results=json.loads(row[8]) if row[8] else {},
            metadata=json.loads(row[9]) if row[9] else {},
            error=row[10]
        )


class CheckpointManager:
    """
    Checkpoint manager

    Manages checkpointing and recovery for workflows and tasks.
    """

    def __init__(
        self,
        backend: Optional[CheckpointBackend] = None,
        auto_checkpoint: bool = True,
        checkpoint_interval: float = 60.0  # seconds
    ):
        """
        Initialize checkpoint manager

        Args:
            backend: Storage backend (defaults to FileSystemBackend)
            auto_checkpoint: Enable automatic checkpointing
            checkpoint_interval: Minimum interval between checkpoints
        """
        self.backend = backend or FileSystemBackend()
        self.auto_checkpoint = auto_checkpoint
        self.checkpoint_interval = checkpoint_interval

        # Track last checkpoint time per execution
        self._last_checkpoint: Dict[str, float] = {}

    async def create_checkpoint(
        self,
        execution_id: str,
        status: CheckpointStatus,
        current_node: Optional[str] = None,
        completed_nodes: Optional[List[str]] = None,
        pending_nodes: Optional[List[str]] = None,
        workflow_state: Optional[Dict[str, Any]] = None,
        task_results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Checkpoint:
        """
        Create and save checkpoint

        Args:
            execution_id: Unique execution identifier
            status: Current status
            current_node: Current node being executed
            completed_nodes: List of completed nodes
            pending_nodes: List of pending nodes
            workflow_state: Current workflow state
            task_results: Task execution results
            metadata: Additional metadata
            error: Error message if failed

        Returns:
            Created checkpoint
        """
        checkpoint_id = f"{execution_id}_{int(time.time() * 1000)}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            timestamp=time.time(),
            status=status,
            current_node=current_node,
            completed_nodes=completed_nodes or [],
            pending_nodes=pending_nodes or [],
            workflow_state=workflow_state or {},
            task_results=task_results or {},
            metadata=metadata or {},
            error=error
        )

        await self.backend.save(checkpoint)
        self._last_checkpoint[execution_id] = checkpoint.timestamp

        return checkpoint

    async def should_checkpoint(self, execution_id: str) -> bool:
        """
        Check if should create checkpoint based on interval

        Args:
            execution_id: Execution ID

        Returns:
            True if should checkpoint
        """
        if not self.auto_checkpoint:
            return False

        last_time = self._last_checkpoint.get(execution_id, 0)
        current_time = time.time()

        return (current_time - last_time) >= self.checkpoint_interval

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint by ID"""
        return await self.backend.load(checkpoint_id)

    async def load_latest_checkpoint(self, execution_id: str) -> Optional[Checkpoint]:
        """Load latest checkpoint for execution"""
        return await self.backend.load_latest(execution_id)

    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        limit: int = 100
    ) -> List[Checkpoint]:
        """List checkpoints with filters"""
        return await self.backend.list_checkpoints(
            execution_id=execution_id,
            status=status,
            limit=limit
        )

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint"""
        return await self.backend.delete(checkpoint_id)

    async def cleanup_checkpoints(
        self,
        execution_id: Optional[str] = None,
        older_than_seconds: Optional[float] = None,
        keep_latest: int = 1
    ) -> int:
        """
        Cleanup old checkpoints

        Args:
            execution_id: Specific execution ID (None for all)
            older_than_seconds: Delete checkpoints older than this
            keep_latest: Keep this many latest checkpoints per execution

        Returns:
            Number of deleted checkpoints
        """
        return await self.backend.cleanup(
            execution_id=execution_id,
            older_than=older_than_seconds,
            keep_latest=keep_latest
        )

    async def can_resume(self, execution_id: str) -> bool:
        """
        Check if execution can be resumed

        Args:
            execution_id: Execution ID

        Returns:
            True if checkpoint exists and can resume
        """
        checkpoint = await self.load_latest_checkpoint(execution_id)

        if not checkpoint:
            return False

        # Can resume if status is RUNNING or PAUSED
        return checkpoint.status in [CheckpointStatus.RUNNING, CheckpointStatus.PAUSED]
