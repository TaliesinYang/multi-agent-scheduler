"""
Performance Benchmark Tests for Scheduler

Simplified benchmarks using actual project structure.
"""

import pytest
import asyncio
import time
import psutil
import os

from src.scheduler import MultiAgentScheduler, Task
from src.agents import MockAgent


class TestSchedulerPerformance:
    """Scheduler performance benchmarks"""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance"""
        mock_agent = MockAgent()
        return MultiAgentScheduler(agents={"mock": mock_agent})

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing"""
        return MockAgent()

    def test_sequential_tasks_10(self, scheduler, benchmark):
        """Benchmark: 10 sequential tasks"""
        async def run_sequential():
            tasks = [
                Task(
                    id=f"task_{i}",
                    prompt=f"Sequential task {i}",
                    task_type="general",
                    depends_on=[] if i == 0 else [f"task_{i-1}"]
                )
                for i in range(10)
            ]

            result = await scheduler.schedule(tasks)
            return result

        def run_sync():
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(run_sequential())

        result = benchmark(run_sync)

        # Verification
        print(f"\n✅ Completed 10 sequential tasks")
        # Should complete in reasonable time
        assert benchmark.stats['mean'] < 5.0

    def test_parallel_tasks_10(self, scheduler, benchmark):
        """Benchmark: 10 parallel tasks (no dependencies)"""
        async def run_parallel():
            tasks = [
                Task(
                    id=f"task_{i}",
                    prompt=f"Parallel task {i}",
                    task_type="general",
                    depends_on=[]
                )
                for i in range(10)
            ]

            result = await scheduler.schedule(tasks)
            return result

        def run_sync():
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(run_parallel())

        result = benchmark(run_sync)

        # Verification
        print(f"\n✅ Completed 10 parallel tasks")
        # Parallel execution should be faster
        assert benchmark.stats['mean'] < 3.0

    def test_memory_usage(self, scheduler):
        """Test memory usage with moderate number of tasks"""
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        async def run_tasks():
            tasks = [
                Task(
                    id=f"task_{i}",
                    prompt=f"Memory test task {i}",
                    task_type="general",
                    depends_on=[]
                )
                for i in range(100)
            ]

            result = await scheduler.schedule(tasks)
            return result

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_tasks())

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before

        # Verification
        print(f"\n📊 Memory Test:")
        print(f"   Before: {mem_before:.2f}MB")
        print(f"   After: {mem_after:.2f}MB")
        print(f"   Increase: {mem_increase:.2f}MB")

        # Memory increase should be reasonable (< 50MB for 100 tasks)
        assert mem_increase < 50, f"Memory increased by {mem_increase}MB"


class TestSchedulerScalability:
    """Test scheduler scalability"""

    @pytest.fixture
    def scheduler(self):
        mock_agent = MockAgent()
        return MultiAgentScheduler(agents={"mock": mock_agent})

    @pytest.mark.parametrize("task_count", [10, 20, 50])
    def test_scalability(self, scheduler, task_count):
        """Test scalability with varying task counts"""
        async def run_tasks():
            tasks = [
                Task(id=f"task_{i}", prompt=f"Task {i}", task_type="general", depends_on=[])
                for i in range(task_count)
            ]

            start_time = time.time()
            result = await scheduler.schedule(tasks)
            duration = time.time() - start_time

            return duration

        loop = asyncio.get_event_loop()
        duration = loop.run_until_complete(run_tasks())

        # Calculate throughput
        throughput = task_count / duration if duration > 0 else 0

        print(f"\n📈 Scalability Test ({task_count} tasks):")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Throughput: {throughput:.2f} tasks/sec")

        # Should complete successfully
        assert duration < 30, f"Too slow for {task_count} tasks: {duration:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
