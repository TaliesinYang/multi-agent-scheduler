"""
Tests for Checkpointing & Recovery System

Tests checkpoint creation, storage backends, scheduler integration, and recovery.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from src.checkpoint import (
    Checkpoint,
    CheckpointStatus,
    CheckpointManager,
    FileSystemBackend,
    SQLiteBackend
)
from src.workflow_graph import WorkflowGraph, WorkflowNode, WorkflowState, NodeType, WorkflowEdge
from src.scheduler import MultiAgentScheduler, Task
from src.agents import BaseAgent


class MockCheckpointAgent(BaseAgent):
    """Mock agent for checkpoint testing"""

    def __init__(self):
        super().__init__(name="MockCheckpoint", max_concurrent=5)

    async def call(self, prompt: str):
        await asyncio.sleep(0.01)
        return {
            "agent": self.name,
            "result": f"Processed: {prompt}",
            "latency": 0.01,
            "tokens": 10,
            "success": True
        }


class TestCheckpointBasics:
    """Test basic checkpoint functionality"""

    def test_checkpoint_creation(self):
        """Test creating checkpoint"""
        checkpoint = Checkpoint(
            checkpoint_id="test_123",
            execution_id="exec_1",
            timestamp=1234567890.0,
            status=CheckpointStatus.RUNNING,
            current_node="task1",
            completed_nodes=["start", "task1"],
            workflow_state={"key": "value"}
        )

        assert checkpoint.checkpoint_id == "test_123"
        assert checkpoint.status == CheckpointStatus.RUNNING
        assert "task1" in checkpoint.completed_nodes

    def test_checkpoint_serialization(self):
        """Test checkpoint to/from dict"""
        checkpoint = Checkpoint(
            checkpoint_id="test_123",
            execution_id="exec_1",
            timestamp=1234567890.0,
            status=CheckpointStatus.COMPLETED,
            workflow_state={"result": 42}
        )

        # To dict
        data = checkpoint.to_dict()
        assert data['checkpoint_id'] == "test_123"
        assert data['status'] == "completed"
        assert data['workflow_state'] == {"result": 42}

        # From dict
        restored = Checkpoint.from_dict(data)
        assert restored.checkpoint_id == checkpoint.checkpoint_id
        assert restored.status == checkpoint.status
        assert restored.workflow_state == checkpoint.workflow_state


class TestFileSystemBackend:
    """Test filesystem storage backend"""

    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_path):
        """Test saving and loading checkpoints"""
        backend = FileSystemBackend(str(tmp_path))

        checkpoint = Checkpoint(
            checkpoint_id="test_1",
            execution_id="exec_1",
            timestamp=1234567890.0,
            status=CheckpointStatus.RUNNING,
            workflow_state={"data": "test"}
        )

        # Save
        await backend.save(checkpoint)

        # Load
        loaded = await backend.load("test_1")
        assert loaded is not None
        assert loaded.checkpoint_id == "test_1"
        assert loaded.workflow_state == {"data": "test"}

    @pytest.mark.asyncio
    async def test_load_latest(self, tmp_path):
        """Test loading latest checkpoint"""
        backend = FileSystemBackend(str(tmp_path))

        # Save multiple checkpoints
        for i in range(3):
            checkpoint = Checkpoint(
                checkpoint_id=f"test_{i}",
                execution_id="exec_1",
                timestamp=1234567890.0 + i,
                status=CheckpointStatus.RUNNING
            )
            await backend.save(checkpoint)
            await asyncio.sleep(0.01)  # Ensure different timestamps

        # Load latest
        latest = await backend.load_latest("exec_1")
        assert latest is not None
        assert latest.checkpoint_id == "test_2"  # Last one saved

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, tmp_path):
        """Test listing checkpoints with filters"""
        backend = FileSystemBackend(str(tmp_path))

        # Save checkpoints with different statuses
        statuses = [CheckpointStatus.RUNNING, CheckpointStatus.COMPLETED, CheckpointStatus.FAILED]
        for i, status in enumerate(statuses):
            checkpoint = Checkpoint(
                checkpoint_id=f"test_{i}",
                execution_id="exec_1",
                timestamp=1234567890.0 + i,
                status=status
            )
            await backend.save(checkpoint)

        # List all
        all_checkpoints = await backend.list_checkpoints()
        assert len(all_checkpoints) == 3

        # Filter by status
        completed = await backend.list_checkpoints(status=CheckpointStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0].status == CheckpointStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cleanup(self, tmp_path):
        """Test checkpoint cleanup"""
        backend = FileSystemBackend(str(tmp_path))

        # Save old and new checkpoints
        import time
        for i in range(5):
            checkpoint = Checkpoint(
                checkpoint_id=f"test_{i}",
                execution_id="exec_1",
                timestamp=time.time() - (100 - i),  # Decreasing age
                status=CheckpointStatus.COMPLETED
            )
            await backend.save(checkpoint)

        # Cleanup - keep latest 2
        deleted = await backend.cleanup(execution_id="exec_1", keep_latest=2)
        assert deleted == 3

        # Verify only 2 remain
        remaining = await backend.list_checkpoints(execution_id="exec_1")
        assert len(remaining) == 2


class TestSQLiteBackend:
    """Test SQLite storage backend"""

    @pytest.mark.asyncio
    async def test_sqlite_save_load(self, tmp_path):
        """Test SQLite save and load"""
        db_path = str(tmp_path / "test.db")
        backend = SQLiteBackend(db_path)

        checkpoint = Checkpoint(
            checkpoint_id="sql_test_1",
            execution_id="exec_1",
            timestamp=1234567890.0,
            status=CheckpointStatus.RUNNING,
            workflow_state={"key": "value"}
        )

        await backend.save(checkpoint)
        loaded = await backend.load("sql_test_1")

        assert loaded is not None
        assert loaded.checkpoint_id == "sql_test_1"
        assert loaded.workflow_state == {"key": "value"}

    @pytest.mark.asyncio
    async def test_sqlite_queries(self, tmp_path):
        """Test SQLite query filtering"""
        db_path = str(tmp_path / "test.db")
        backend = SQLiteBackend(db_path)

        # Save multiple checkpoints
        for i in range(3):
            checkpoint = Checkpoint(
                checkpoint_id=f"sql_test_{i}",
                execution_id=f"exec_{i % 2}",  # 2 different executions
                timestamp=1234567890.0 + i,
                status=CheckpointStatus.RUNNING if i % 2 == 0 else CheckpointStatus.COMPLETED
            )
            await backend.save(checkpoint)

        # Query by execution_id
        exec_0 = await backend.list_checkpoints(execution_id="exec_0")
        assert len(exec_0) == 2

        # Query by status
        running = await backend.list_checkpoints(status=CheckpointStatus.RUNNING)
        assert len(running) == 2


class TestCheckpointManager:
    """Test checkpoint manager"""

    @pytest.mark.asyncio
    async def test_create_checkpoint(self, tmp_path):
        """Test creating checkpoint through manager"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(backend=backend)

        checkpoint = await manager.create_checkpoint(
            execution_id="exec_1",
            status=CheckpointStatus.RUNNING,
            current_node="task1",
            workflow_state={"data": "test"}
        )

        assert checkpoint is not None
        assert checkpoint.execution_id == "exec_1"
        assert checkpoint.current_node == "task1"

    @pytest.mark.asyncio
    async def test_checkpoint_interval(self, tmp_path):
        """Test checkpoint interval logic"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(
            backend=backend,
            auto_checkpoint=True,
            checkpoint_interval=1.0  # 1 second
        )

        # First checkpoint - should create
        assert await manager.should_checkpoint("exec_1")

        # Create checkpoint
        await manager.create_checkpoint("exec_1", CheckpointStatus.RUNNING)

        # Immediately after - should not create
        assert not await manager.should_checkpoint("exec_1")

        # Wait for interval
        await asyncio.sleep(1.1)

        # Should create now
        assert await manager.should_checkpoint("exec_1")

    @pytest.mark.asyncio
    async def test_can_resume(self, tmp_path):
        """Test can_resume check"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(backend=backend)

        # No checkpoint - cannot resume
        assert not await manager.can_resume("exec_1")

        # Create RUNNING checkpoint - can resume
        await manager.create_checkpoint("exec_1", CheckpointStatus.RUNNING)
        assert await manager.can_resume("exec_1")

        # Create COMPLETED checkpoint - cannot resume
        await manager.create_checkpoint("exec_1", CheckpointStatus.COMPLETED)
        assert not await manager.can_resume("exec_1")


class TestWorkflowCheckpointing:
    """Test workflow execution with checkpointing"""

    @pytest.mark.asyncio
    async def test_workflow_with_checkpoints(self, tmp_path):
        """Test workflow execution creates checkpoints"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(backend=backend, checkpoint_interval=0.1)

        # Create simple workflow
        graph = WorkflowGraph()

        async def task1(state: WorkflowState):
            await asyncio.sleep(0.2)
            return {"value": 1}

        async def task2(state: WorkflowState):
            await asyncio.sleep(0.2)
            return {"value": 2}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=task1))
        graph.add_node(WorkflowNode("task2", NodeType.TASK, handler=task2))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "task2"))
        graph.add_edge(WorkflowEdge("task2", "end"))

        # Execute with checkpointing
        result = await graph.execute(
            checkpoint_manager=manager,
            execution_id="workflow_test_1"
        )

        # Should have created checkpoints
        checkpoints = await manager.list_checkpoints(execution_id="workflow_test_1")
        assert len(checkpoints) > 0

    @pytest.mark.asyncio
    async def test_scheduler_checkpoint_integration(self, tmp_path):
        """Test scheduler integration with checkpoints"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(backend=backend)

        agent = MockCheckpointAgent()
        scheduler = MultiAgentScheduler(
            agents={'mock': agent},
            checkpoint_manager=manager,
            enable_checkpoints=True
        )

        # Create workflow
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "end"))

        # Execute
        result = await scheduler.execute_workflow(graph, execution_id="sched_test_1")

        # Should have checkpoints
        checkpoints = await manager.list_checkpoints(execution_id="sched_test_1")
        assert len(checkpoints) > 0

    @pytest.mark.asyncio
    async def test_workflow_resume(self, tmp_path):
        """Test resuming workflow from checkpoint"""
        backend = FileSystemBackend(str(tmp_path))
        manager = CheckpointManager(backend=backend)

        agent = MockCheckpointAgent()
        scheduler = MultiAgentScheduler(
            agents={'mock': agent},
            checkpoint_manager=manager
        )

        # Create workflow that will "fail"
        execution_count = {"count": 0}

        async def failing_task(state: WorkflowState):
            execution_count["count"] += 1
            if execution_count["count"] == 1:
                raise ValueError("Simulated failure")
            return {"success": True}

        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=failing_task))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task1"))
        graph.add_edge(WorkflowEdge("task1", "end"))

        execution_id = "resume_test_1"

        # First execution - will fail
        try:
            await scheduler.execute_workflow(
                graph,
                execution_id=execution_id,
                enable_checkpoints=True
            )
        except:
            pass  # Expected failure

        # Resume - should succeed
        result = await scheduler.resume_workflow(execution_id, graph)
        assert result.get("success") is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
