"""
Tests for Streaming Responses

Tests the streaming functionality for agents and scheduler.
"""

import pytest
import asyncio
from src.agents import BaseAgent
from src.scheduler import Task


class MockStreamingAgent(BaseAgent):
    """Mock agent for testing streaming"""

    def __init__(self):
        super().__init__(name="MockStream", max_concurrent=5)
        self.chunks = ["Hello", " ", "world", "!", " ", "How", " ", "are", " ", "you", "?"]

    async def call(self, prompt: str):
        """Regular call (non-streaming)"""
        return {
            "agent": self.name,
            "result": "".join(self.chunks),
            "latency": 0.1,
            "tokens": 10,
            "success": True
        }

    async def call_stream(self, prompt: str):
        """Streaming call"""
        for chunk in self.chunks:
            await asyncio.sleep(0.01)  # Simulate network delay
            yield chunk


class TestAgentStreaming:
    """Test agent-level streaming"""

    @pytest.mark.asyncio
    async def test_mock_agent_stream(self):
        """Test mock agent streaming"""
        agent = MockStreamingAgent()

        chunks = []
        async for chunk in agent.call_stream("Test prompt"):
            chunks.append(chunk)

        assert len(chunks) == 11
        assert "".join(chunks) == "Hello world! How are you?"

    @pytest.mark.asyncio
    async def test_stream_collects_all_chunks(self):
        """Test that all chunks are collected"""
        agent = MockStreamingAgent()

        result = ""
        async for chunk in agent.call_stream("Test"):
            result += chunk

        expected = "Hello world! How are you?"
        assert result == expected


class TestSchedulerStreaming:
    """Test scheduler-level streaming"""

    @pytest.mark.asyncio
    async def test_execute_task_stream_basic(self):
        """Test basic task streaming"""
        from src.scheduler import MultiAgentScheduler

        agent = MockStreamingAgent()
        scheduler = MultiAgentScheduler(agents={'mock': agent})

        task = Task(
            id="stream_task1",
            prompt="Test streaming",
            task_type="general"
        )

        chunks = []
        final_result = None

        async for chunk_data in scheduler.execute_task_stream(task, 'mock'):
            if not chunk_data['done']:
                chunks.append(chunk_data['chunk'])
            else:
                final_result = chunk_data

        # Check chunks were received
        assert len(chunks) == 11
        assert "".join(chunks) == "Hello world! How are you?"

        # Check final result
        assert final_result is not None
        assert final_result['done'] is True
        assert final_result['success'] is True
        assert final_result['task_id'] == "stream_task1"
        assert final_result['result'] == "Hello world! How are you?"

    @pytest.mark.asyncio
    async def test_stream_with_metrics(self):
        """Test streaming with metrics enabled"""
        from src.scheduler import MultiAgentScheduler
        from src.metrics import MetricsCollector

        agent = MockStreamingAgent()
        metrics = MetricsCollector()

        # Create dependencies with metrics
        from src.dependency_injection import SchedulerDependencies
        deps = SchedulerDependencies(
            agents={'mock': agent},
            metrics=metrics
        )

        scheduler = MultiAgentScheduler(dependencies=deps)

        task = Task(id="metrics_task", prompt="Test", task_type="general")

        # Execute streaming
        async for chunk_data in scheduler.execute_task_stream(task, 'mock'):
            pass

        # Check metrics were recorded
        stats = metrics.get_all_stats()
        assert 'tasks.stream_started' in stats['counters']
        assert stats['counters']['tasks.stream_started'] == 1
        assert 'tasks.stream_completed' in stats['counters']
        assert stats['counters']['tasks.stream_completed'] == 1

    @pytest.mark.asyncio
    async def test_stream_error_handling(self):
        """Test error handling in streaming"""

        class FailingStreamAgent(BaseAgent):
            def __init__(self):
                super().__init__(name="FailStream", max_concurrent=5)

            async def call(self, prompt: str):
                return {"agent": self.name, "result": "fallback", "success": False}

            async def call_stream(self, prompt: str):
                yield "Start"
                await asyncio.sleep(0.01)
                raise Exception("Stream failed")

        agent = FailingStreamAgent()
        from src.scheduler import MultiAgentScheduler
        scheduler = MultiAgentScheduler(agents={'fail': agent})

        task = Task(id="fail_task", prompt="Test", task_type="general")

        chunks = []
        final_result = None

        async for chunk_data in scheduler.execute_task_stream(task, 'fail'):
            if not chunk_data['done']:
                chunks.append(chunk_data['chunk'])
            else:
                final_result = chunk_data

        # Should have received at least one chunk before failure
        assert len(chunks) >= 1
        assert chunks[0] == "Start"

        # Final result should indicate failure
        assert final_result is not None
        assert final_result['success'] is False
        assert final_result['error'] is not None


class TestStreamingIntegration:
    """Integration tests for streaming"""

    @pytest.mark.asyncio
    async def test_streaming_vs_regular(self):
        """Compare streaming vs regular execution"""
        agent = MockStreamingAgent()

        # Regular call
        regular_result = await agent.call("Test")

        # Streaming call
        stream_result = ""
        async for chunk in agent.call_stream("Test"):
            stream_result += chunk

        # Both should produce same result
        assert regular_result['result'] == stream_result

    @pytest.mark.asyncio
    async def test_real_time_processing(self):
        """Test that chunks arrive in real-time"""
        import time

        agent = MockStreamingAgent()

        start_time = time.time()
        chunk_times = []

        async for chunk in agent.call_stream("Test"):
            chunk_times.append(time.time() - start_time)

        # Chunks should arrive incrementally (not all at once)
        # Each chunk has 0.01s delay, so we expect spacing
        assert len(chunk_times) == 11

        # First chunk should arrive quickly
        assert chunk_times[0] < 0.05

        # Later chunks should be spaced out
        if len(chunk_times) >= 5:
            # Check that there's a delay between chunks
            time_diff = chunk_times[5] - chunk_times[0]
            assert time_diff > 0.03  # At least some delay


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
