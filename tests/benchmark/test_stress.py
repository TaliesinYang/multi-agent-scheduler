"""
Stress Tests for Multi-Agent Scheduler

Tests system behavior under extreme conditions.
"""

import pytest
import asyncio
import time
import psutil
import os

from src.scheduler import Scheduler
from src.models import Task, Agent
from src.workflow_graph import WorkflowGraph, WorkflowNode, WorkflowEdge, NodeType, WorkflowState


class TestStressConcurrency:
    """Stress test concurrent operations"""

    @pytest.fixture
    def mock_agent(self):
        class MockAgent(Agent):
            def __init__(self):
                super().__init__("mock", "mock")
                self.call_count = 0

            async def call(self, prompt: str, **kwargs) -> str:
                self.call_count += 1
                await asyncio.sleep(0.01)
                return f"Response {self.call_count}"

        return MockAgent()

    @pytest.mark.stress
    def test_high_concurrency_tasks(self, mock_agent):
        """Stress: 500 concurrent tasks"""
        scheduler = Scheduler()

        task_count = 500
        tasks = [
            Task(f"task_{i}", f"Concurrent task {i}", "mock")
            for i in range(task_count)
        ]

        # Measure execution
        start_time = time.time()
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
        )

        duration = time.time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        # Verification
        assert len(result) == task_count
        throughput = task_count / duration

        print(f"\n🔥 High Concurrency Stress Test:")
        print(f"   Tasks: {task_count}")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Throughput: {throughput:.2f} tasks/sec")
        print(f"   Memory increase: {mem_increase:.2f}MB")

        # Should handle 500 tasks efficiently
        assert duration < 30, f"Too slow: {duration:.3f}s"
        assert mem_increase < 200, f"Memory increase too high: {mem_increase:.2f}MB"

    @pytest.mark.stress
    def test_rapid_workflow_creation(self):
        """Stress: Rapidly create and execute many workflows"""
        workflow_count = 100

        async def quick_task(state: WorkflowState):
            await asyncio.sleep(0.001)
            return {"done": True}

        start_time = time.time()

        loop = asyncio.get_event_loop()

        for i in range(workflow_count):
            graph = WorkflowGraph()
            graph.add_node(WorkflowNode("start", NodeType.START))
            graph.add_node(WorkflowNode("task", NodeType.TASK, handler=quick_task))
            graph.add_node(WorkflowNode("end", NodeType.END))

            graph.add_edge(WorkflowEdge("start", "task"))
            graph.add_edge(WorkflowEdge("task", "end"))

            result = loop.run_until_complete(graph.execute())
            assert result.get("done") is True

        duration = time.time() - start_time

        print(f"\n⚡ Rapid Workflow Creation:")
        print(f"   Workflows: {workflow_count}")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Workflows/sec: {workflow_count/duration:.2f}")

        # Should handle rapid workflow creation
        assert duration < 20, f"Too slow: {duration:.3f}s"


class TestStressMemory:
    """Stress test memory usage"""

    @pytest.mark.stress
    def test_memory_leak_detection(self):
        """Stress: Detect memory leaks with repeated executions"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.001)
            return {"data": "x" * 1000}  # 1KB per task

        process = psutil.Process(os.getpid())
        mem_readings = []

        loop = asyncio.get_event_loop()

        # Run 50 iterations
        for iteration in range(50):
            graph = WorkflowGraph()
            graph.add_node(WorkflowNode("start", NodeType.START))

            # Create 20 tasks
            for i in range(20):
                graph.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))

            graph.add_node(WorkflowNode("end", NodeType.END))

            # Connect sequentially
            graph.add_edge(WorkflowEdge("start", "task_0"))
            for i in range(19):
                graph.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
            graph.add_edge(WorkflowEdge("task_19", "end"))

            # Execute
            result = loop.run_until_complete(graph.execute())

            # Record memory
            mem_mb = process.memory_info().rss / 1024 / 1024
            mem_readings.append(mem_mb)

            # Clean up
            del graph
            del result

        # Analyze memory trend
        mem_start = sum(mem_readings[:10]) / 10  # Average of first 10
        mem_end = sum(mem_readings[-10:]) / 10   # Average of last 10
        mem_growth = mem_end - mem_start

        print(f"\n🧪 Memory Leak Detection:")
        print(f"   Iterations: 50")
        print(f"   Start memory: {mem_start:.2f}MB")
        print(f"   End memory: {mem_end:.2f}MB")
        print(f"   Growth: {mem_growth:.2f}MB")
        print(f"   Growth per iteration: {mem_growth/50:.3f}MB")

        # Memory growth should be minimal (< 50MB total)
        assert mem_growth < 50, f"Possible memory leak: {mem_growth:.2f}MB growth"

    @pytest.mark.stress
    def test_large_state_handling(self):
        """Stress: Handle very large workflow states"""
        async def large_state_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            # Add 1MB of data
            return {"large_data": "x" * (1024 * 1024)}

        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("task", NodeType.TASK, handler=large_state_handler))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "task"))
        graph.add_edge(WorkflowEdge("task", "end"))

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        loop = asyncio.get_event_loop()
        start_time = time.time()

        result = loop.run_until_complete(graph.execute())

        duration = time.time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        print(f"\n💾 Large State Handling:")
        print(f"   State size: ~1MB")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Memory increase: {mem_increase:.2f}MB")

        # Should handle large states without excessive memory usage
        # Expect ~1MB for data plus some overhead (< 10MB total)
        assert mem_increase < 10, f"Memory usage too high: {mem_increase:.2f}MB"
        assert duration < 1.0, f"Too slow: {duration:.3f}s"


class TestStressLongRunning:
    """Stress test long-running operations"""

    @pytest.mark.stress
    @pytest.mark.slow
    def test_long_running_workflow(self):
        """Stress: Very long running workflow (10 minutes simulated)"""
        async def slow_task(state: WorkflowState):
            # Simulate 1 second task
            await asyncio.sleep(1.0)
            count = state.get("count", 0)
            return {"count": count + 1}

        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))

        # Create 60 sequential tasks (60 seconds total)
        task_count = 60
        for i in range(task_count):
            graph.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=slow_task))

        graph.add_node(WorkflowNode("end", NodeType.END))

        # Connect sequentially
        graph.add_edge(WorkflowEdge("start", "task_0"))
        for i in range(task_count - 1):
            graph.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
        graph.add_edge(WorkflowEdge(f"task_{task_count-1}", "end"))

        process = psutil.Process(os.getpid())
        mem_start = process.memory_info().rss / 1024 / 1024

        loop = asyncio.get_event_loop()
        start_time = time.time()

        result = loop.run_until_complete(graph.execute())

        duration = time.time() - start_time
        mem_end = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_end - mem_start

        print(f"\n⏳ Long Running Workflow:")
        print(f"   Tasks: {task_count}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Memory start: {mem_start:.2f}MB")
        print(f"   Memory end: {mem_end:.2f}MB")
        print(f"   Memory increase: {mem_increase:.2f}MB")

        # Verify completion
        assert result.get("count") == task_count

        # Memory should remain stable
        assert mem_increase < 50, f"Memory leak in long-running workflow: {mem_increase:.2f}MB"


class TestStressErrorRecovery:
    """Stress test error handling and recovery"""

    @pytest.mark.stress
    def test_multiple_failures_recovery(self):
        """Stress: Recover from multiple sequential failures"""
        failure_count = 0

        async def flaky_task(state: WorkflowState):
            nonlocal failure_count
            await asyncio.sleep(0.01)

            # Fail first 10 times
            if failure_count < 10:
                failure_count += 1
                raise ValueError(f"Failure {failure_count}")

            return {"success": True, "failures": failure_count}

        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("flaky", NodeType.TASK, handler=flaky_task))
        graph.add_node(WorkflowNode("end", NodeType.END))

        graph.add_edge(WorkflowEdge("start", "flaky"))
        graph.add_edge(WorkflowEdge("flaky", "end"))

        loop = asyncio.get_event_loop()

        # Try multiple times until success
        max_attempts = 15
        for attempt in range(max_attempts):
            try:
                result = loop.run_until_complete(graph.execute())
                if result.get("success"):
                    print(f"\n🔄 Failure Recovery:")
                    print(f"   Successful after {attempt + 1} attempts")
                    print(f"   Total failures: {result.get('failures')}")
                    assert result.get("success") is True
                    break
            except ValueError:
                continue
        else:
            pytest.fail(f"Failed to recover after {max_attempts} attempts")


@pytest.mark.stress
class TestStressComposite:
    """Composite stress tests combining multiple factors"""

    def test_full_system_stress(self):
        """Stress: Full system stress test (high concurrency + large state + checkpoints)"""
        from src.checkpoint import CheckpointManager
        import tempfile

        # Setup
        temp_dir = tempfile.mkdtemp()
        checkpoint_manager = CheckpointManager()
        if hasattr(checkpoint_manager.backend, 'checkpoint_dir'):
            checkpoint_manager.backend.checkpoint_dir = temp_dir

        async def heavy_task(state: WorkflowState):
            await asyncio.sleep(0.01)
            # Add some data
            count = state.get("count", 0)
            return {
                "count": count + 1,
                "data": "x" * 1000  # 1KB
            }

        # Create complex workflow
        graph = WorkflowGraph()
        graph.add_node(WorkflowNode("start", NodeType.START))

        # 50 parallel branches
        branch_count = 50
        for i in range(branch_count):
            graph.add_node(WorkflowNode(f"branch_{i}", NodeType.TASK, handler=heavy_task))

        graph.add_node(WorkflowNode("end", NodeType.END))

        # Connect parallel branches
        for i in range(branch_count):
            graph.add_edge(WorkflowEdge("start", f"branch_{i}"))
            graph.add_edge(WorkflowEdge(f"branch_{i}", "end"))

        # Monitor resources
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024

        loop = asyncio.get_event_loop()
        start_time = time.time()

        # Execute with checkpointing
        result = loop.run_until_complete(
            graph.execute(
                checkpoint_manager=checkpoint_manager,
                execution_id="stress_test"
            )
        )

        duration = time.time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024
        mem_increase = mem_after - mem_before

        print(f"\n🔥 Full System Stress Test:")
        print(f"   Parallel branches: {branch_count}")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Memory increase: {mem_increase:.2f}MB")
        print(f"   Tasks/sec: {branch_count/duration:.2f}")

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Verification
        assert result is not None
        assert duration < 5.0, f"Full system stress test too slow: {duration:.3f}s"
        assert mem_increase < 100, f"Memory usage too high: {mem_increase:.2f}MB"


if __name__ == "__main__":
    # Run stress tests with verbose output
    pytest.main([__file__, "-v", "-m", "stress"])
