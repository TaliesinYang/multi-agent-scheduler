"""
Performance Benchmark Tests for Scheduler

Tests scheduler performance under various loads to ensure production readiness.
"""

import pytest
import asyncio
import time
from typing import List

from src.scheduler import Scheduler
from src.models import Task, Agent


class TestSchedulerPerformance:
    """Scheduler performance benchmarks"""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance"""
        return Scheduler()

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing"""
        class MockAgent(Agent):
            def __init__(self):
                super().__init__("mock", "mock")

            async def call(self, prompt: str, **kwargs) -> str:
                # Simulate 10ms processing time
                await asyncio.sleep(0.01)
                return f"Response to: {prompt}"

        return MockAgent()

    def test_sequential_tasks_10(self, scheduler, mock_agent, benchmark):
        """Benchmark: 10 sequential tasks"""
        def run_sequential():
            tasks = [
                Task(
                    task_id=f"task_{i}",
                    description=f"Sequential task {i}",
                    agent_type="mock",
                    dependencies=[]
                )
                for i in range(10)
            ]

            # Run synchronously for benchmark
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
            )
            return result

        result = benchmark(run_sequential)

        # Verification
        assert len(result) == 10
        # Should complete in reasonable time (10 tasks * 10ms + overhead < 1s)
        assert benchmark.stats['mean'] < 1.0

    def test_sequential_tasks_50(self, scheduler, mock_agent, benchmark):
        """Benchmark: 50 sequential tasks"""
        def run_sequential():
            tasks = [
                Task(
                    task_id=f"task_{i}",
                    description=f"Sequential task {i}",
                    agent_type="mock"
                )
                for i in range(50)
            ]

            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
            )
            return result

        result = benchmark(run_sequential)

        # Verification
        assert len(result) == 50
        # Should complete in reasonable time (50 tasks * 10ms + overhead < 3s)
        assert benchmark.stats['mean'] < 3.0

    def test_parallel_tasks_10(self, scheduler, mock_agent, benchmark):
        """Benchmark: 10 parallel tasks"""
        def run_parallel():
            tasks = [
                Task(
                    task_id=f"task_{i}",
                    description=f"Parallel task {i}",
                    agent_type="mock",
                    dependencies=[]
                )
                for i in range(10)
            ]

            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
            )
            return result

        result = benchmark(run_parallel)

        # Verification
        assert len(result) == 10
        # Parallel execution should be much faster than sequential
        # 10 tasks in parallel ~10ms + overhead < 0.5s
        assert benchmark.stats['mean'] < 0.5

    def test_parallel_tasks_100(self, scheduler, mock_agent, benchmark):
        """Benchmark: 100 parallel tasks"""
        def run_parallel():
            tasks = [
                Task(
                    task_id=f"task_{i}",
                    description=f"Parallel task {i}",
                    agent_type="mock",
                    dependencies=[]
                )
                for i in range(100)
            ]

            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
            )
            return result

        result = benchmark(run_parallel)

        # Verification
        assert len(result) == 100
        # 100 parallel tasks should complete in reasonable time < 2s
        assert benchmark.stats['mean'] < 2.0

    def test_mixed_dependency_tasks(self, scheduler, mock_agent, benchmark):
        """Benchmark: Mixed dependency graph (realistic scenario)"""
        def run_mixed():
            # Create a realistic dependency graph
            tasks = [
                Task("analysis", "Analyze requirements", "mock", []),
                Task("design_db", "Design database", "mock", ["analysis"]),
                Task("design_api", "Design API", "mock", ["analysis"]),
                Task("design_ui", "Design UI", "mock", ["analysis"]),
                Task("impl_db", "Implement database", "mock", ["design_db"]),
                Task("impl_api", "Implement API", "mock", ["design_api", "impl_db"]),
                Task("impl_ui", "Implement UI", "mock", ["design_ui", "impl_api"]),
                Task("test_integration", "Integration tests", "mock", ["impl_ui"]),
                Task("deploy", "Deploy", "mock", ["test_integration"]),
            ]

            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
            )
            return result

        result = benchmark(run_mixed)

        # Verification
        assert len(result) == 9
        # Mixed tasks should benefit from parallelization
        assert benchmark.stats['mean'] < 1.5

    def test_memory_usage(self, scheduler, mock_agent):
        """Test memory usage with large number of tasks"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Create 1000 tasks
        tasks = [
            Task(
                task_id=f"task_{i}",
                description=f"Memory test task {i}",
                agent_type="mock"
            )
            for i in range(1000)
        ]

        # Execute
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
        )

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        # Verification
        assert len(result) == 1000
        # Memory increase should be reasonable (< 100MB for 1000 tasks)
        assert mem_increase < 100, f"Memory increased by {mem_increase}MB"

        print(f"\n📊 Memory Test:")
        print(f"   Before: {mem_before:.2f}MB")
        print(f"   After: {mem_after:.2f}MB")
        print(f"   Increase: {mem_increase:.2f}MB")


class TestSchedulerScalability:
    """Test scheduler scalability"""

    @pytest.fixture
    def scheduler(self):
        return Scheduler()

    @pytest.fixture
    def mock_agent(self):
        class MockAgent(Agent):
            def __init__(self):
                super().__init__("mock", "mock")

            async def call(self, prompt: str, **kwargs) -> str:
                await asyncio.sleep(0.01)
                return "response"

        return MockAgent()

    @pytest.mark.parametrize("task_count", [10, 50, 100, 200])
    def test_scalability(self, scheduler, mock_agent, task_count):
        """Test scalability with varying task counts"""
        tasks = [
            Task(f"task_{i}", f"Task {i}", "mock")
            for i in range(task_count)
        ]

        start_time = time.time()

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            scheduler.execute_tasks(tasks, agents={"mock": mock_agent})
        )

        duration = time.time() - start_time

        # Verification
        assert len(result) == task_count

        # Calculate throughput
        throughput = task_count / duration

        print(f"\n📈 Scalability Test ({task_count} tasks):")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Throughput: {throughput:.2f} tasks/sec")

        # Minimum acceptable throughput: 20 tasks/sec
        assert throughput > 20, f"Throughput too low: {throughput:.2f} tasks/sec"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
