"""
Performance Benchmark Tests for Checkpoint System

Tests checkpoint creation and recovery performance.
"""

import pytest
import asyncio
import time
import os
import tempfile

from src.checkpoint import CheckpointManager, CheckpointStatus
from src.workflow_graph import WorkflowGraph, WorkflowNode, WorkflowEdge, NodeType, WorkflowState


class TestCheckpointPerformance:
    """Checkpoint system performance benchmarks"""

    @pytest.fixture
    def checkpoint_manager(self):
        """Create checkpoint manager with temp directory"""
        temp_dir = tempfile.mkdtemp()
        manager = CheckpointManager()
        # Override checkpoint directory
        if hasattr(manager.backend, 'checkpoint_dir'):
            manager.backend.checkpoint_dir = temp_dir
        yield manager
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_checkpoint_creation_overhead(self, checkpoint_manager, benchmark):
        """Benchmark: Checkpoint creation overhead"""
        async def create_checkpoint():
            await checkpoint_manager.create_checkpoint(
                execution_id="test_exec",
                status=CheckpointStatus.RUNNING,
                workflow_state={"data": "test" * 100},
                metadata={"test": True}
            )

        def run_create():
            loop = asyncio.get_event_loop()
            loop.run_until_complete(create_checkpoint())

        benchmark(run_create)

        # Checkpoint creation should be fast (< 50ms)
        assert benchmark.stats['mean'] < 0.05

    def test_checkpoint_loading_speed(self, checkpoint_manager, benchmark):
        """Benchmark: Checkpoint loading speed"""
        # First create a checkpoint
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            checkpoint_manager.create_checkpoint(
                execution_id="test_load",
                status=CheckpointStatus.RUNNING,
                workflow_state={"data": "test" * 100},
                metadata={"test": True}
            )
        )

        async def load_checkpoint():
            checkpoint = await checkpoint_manager.load_latest_checkpoint("test_load")
            return checkpoint

        def run_load():
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(load_checkpoint())
            return result

        result = benchmark(run_load)

        # Loading should be fast (< 50ms)
        assert benchmark.stats['mean'] < 0.05
        assert result is not None

    def test_checkpoint_with_workflow(self, checkpoint_manager):
        """Test checkpoint overhead in workflow execution"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            return {"processed": state.get("processed", 0) + 1}

        # Test WITHOUT checkpoints
        graph_no_cp = WorkflowGraph()
        graph_no_cp.add_node(WorkflowNode("start", NodeType.START))
        for i in range(10):
            graph_no_cp.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))
        graph_no_cp.add_node(WorkflowNode("end", NodeType.END))

        graph_no_cp.add_edge(WorkflowEdge("start", "task_0"))
        for i in range(9):
            graph_no_cp.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
        graph_no_cp.add_edge(WorkflowEdge("task_9", "end"))

        loop = asyncio.get_event_loop()

        start_no_cp = time.time()
        result_no_cp = loop.run_until_complete(graph_no_cp.execute())
        duration_no_cp = time.time() - start_no_cp

        # Test WITH checkpoints
        graph_with_cp = WorkflowGraph()
        graph_with_cp.add_node(WorkflowNode("start", NodeType.START))
        for i in range(10):
            graph_with_cp.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))
        graph_with_cp.add_node(WorkflowNode("end", NodeType.END))

        graph_with_cp.add_edge(WorkflowEdge("start", "task_0"))
        for i in range(9):
            graph_with_cp.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
        graph_with_cp.add_edge(WorkflowEdge("task_9", "end"))

        start_with_cp = time.time()
        result_with_cp = loop.run_until_complete(
            graph_with_cp.execute(
                checkpoint_manager=checkpoint_manager,
                execution_id="test_overhead"
            )
        )
        duration_with_cp = time.time() - start_with_cp

        # Calculate overhead
        overhead = (duration_with_cp - duration_no_cp) / duration_no_cp * 100

        print(f"\n📊 Checkpoint Overhead Analysis:")
        print(f"   Without checkpoints: {duration_no_cp:.3f}s")
        print(f"   With checkpoints: {duration_with_cp:.3f}s")
        print(f"   Overhead: {overhead:.2f}%")

        # Checkpoint overhead should be < 20%
        assert overhead < 20, f"Checkpoint overhead too high: {overhead:.2f}%"

    def test_checkpoint_recovery_speed(self, checkpoint_manager):
        """Test checkpoint recovery speed"""
        async def task_handler(state: WorkflowState):
            count = state.get("count", 0)
            if count < 3:
                # Simulate failure on first 3 attempts
                raise ValueError("Simulated failure")
            await asyncio.sleep(0.01)
            return {"count": count + 1, "success": True}

        # Create workflow that will fail and need recovery
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task", NodeType.TASK, handler=task_handler))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task"))
        graph.add_edge(WorkflowEdge("task", "end"))

        loop = asyncio.get_event_loop()

        # First attempt - will fail
        execution_id = "recovery_test"
        try:
            loop.run_until_complete(
                graph.execute(
                    checkpoint_manager=checkpoint_manager,
                    execution_id=execution_id
                )
            )
        except ValueError:
            pass  # Expected failure

        # Measure recovery time
        start_recovery = time.time()

        # Load checkpoint
        checkpoint = loop.run_until_complete(
            checkpoint_manager.load_latest_checkpoint(execution_id)
        )

        # Create new state from checkpoint
        recovered_state = WorkflowState(
            data=checkpoint.workflow_state,
            history=checkpoint.completed_nodes
        )
        recovered_state.data['count'] = 3  # Fix the condition

        # Resume execution
        result = loop.run_until_complete(
            graph.execute(
                initial_state=recovered_state,
                start_node="task"
            )
        )

        recovery_duration = time.time() - start_recovery

        print(f"\n⏱️  Checkpoint Recovery:")
        print(f"   Recovery time: {recovery_duration:.3f}s")
        print(f"   Success: {result.get('success')}")

        # Recovery should be fast (< 1s)
        assert recovery_duration < 1.0
        assert result.get("success") is True


class TestCheckpointScalability:
    """Test checkpoint system scalability"""

    @pytest.fixture
    def checkpoint_manager(self):
        temp_dir = tempfile.mkdtemp()
        manager = CheckpointManager()
        if hasattr(manager.backend, 'checkpoint_dir'):
            manager.backend.checkpoint_dir = temp_dir
        yield manager
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.parametrize("state_size_kb", [1, 10, 100, 1000])
    def test_large_state_checkpoint(self, checkpoint_manager, state_size_kb):
        """Test checkpoint performance with varying state sizes"""
        # Create large state
        large_data = "x" * (state_size_kb * 1024)
        state = {"data": large_data}

        loop = asyncio.get_event_loop()

        # Measure checkpoint creation time
        start_create = time.time()
        loop.run_until_complete(
            checkpoint_manager.create_checkpoint(
                execution_id=f"large_state_{state_size_kb}",
                status=CheckpointStatus.RUNNING,
                workflow_state=state
            )
        )
        create_duration = time.time() - start_create

        # Measure checkpoint loading time
        start_load = time.time()
        checkpoint = loop.run_until_complete(
            checkpoint_manager.load_latest_checkpoint(f"large_state_{state_size_kb}")
        )
        load_duration = time.time() - start_load

        print(f"\n📦 Large State Checkpoint ({state_size_kb}KB):")
        print(f"   Create time: {create_duration:.3f}s")
        print(f"   Load time: {load_duration:.3f}s")
        print(f"   Create speed: {state_size_kb/create_duration:.2f} KB/s")
        print(f"   Load speed: {state_size_kb/load_duration:.2f} KB/s")

        # Even large states should checkpoint reasonably fast
        # Allow 1s per 100KB
        max_time = state_size_kb / 100
        assert create_duration < max_time, f"Checkpoint creation too slow for {state_size_kb}KB"
        assert load_duration < max_time, f"Checkpoint loading too slow for {state_size_kb}KB"

    def test_multiple_checkpoints(self, checkpoint_manager):
        """Test performance with multiple checkpoints per execution"""
        loop = asyncio.get_event_loop()

        execution_id = "multi_checkpoint_test"
        checkpoint_count = 100

        # Create multiple checkpoints
        start_time = time.time()
        for i in range(checkpoint_count):
            loop.run_until_complete(
                checkpoint_manager.create_checkpoint(
                    execution_id=execution_id,
                    status=CheckpointStatus.RUNNING,
                    workflow_state={"iteration": i},
                    metadata={"checkpoint_number": i}
                )
            )
        total_duration = time.time() - start_time

        # List all checkpoints
        checkpoints = loop.run_until_complete(
            checkpoint_manager.list_checkpoints(execution_id=execution_id)
        )

        avg_time = total_duration / checkpoint_count

        print(f"\n📚 Multiple Checkpoints Test:")
        print(f"   Total checkpoints: {len(checkpoints)}")
        print(f"   Total time: {total_duration:.3f}s")
        print(f"   Average time per checkpoint: {avg_time:.4f}s")
        print(f"   Checkpoints per second: {checkpoint_count/total_duration:.2f}")

        # Should maintain reasonable performance even with many checkpoints
        assert avg_time < 0.1, f"Average checkpoint time too high: {avg_time:.4f}s"
        assert len(checkpoints) >= checkpoint_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
