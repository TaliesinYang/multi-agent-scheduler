"""
Performance Benchmark Tests for Workflow Engine

Tests workflow execution performance under various scenarios.
"""

import pytest
import asyncio
import time

from src.workflow_graph import WorkflowGraph, WorkflowNode, WorkflowEdge, NodeType, WorkflowState


class TestWorkflowPerformance:
    """Workflow execution performance benchmarks"""

    def test_linear_workflow_10_nodes(self, benchmark):
        """Benchmark: Linear workflow with 10 nodes"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.01)  # Simulate 10ms work
            return {"processed": state.get("processed", 0) + 1}

        def run_linear():
            graph = WorkflowGraph()

            # Create linear workflow
            graph.add_node(WorkflowNode("start", NodeType.START))
            for i in range(10):
                graph.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))
            graph.add_node(WorkflowNode("end", NodeType.END))

            # Link nodes sequentially
            graph.add_edge(WorkflowEdge("start", "task_0"))
            for i in range(9):
                graph.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
            graph.add_edge(WorkflowEdge("task_9", "end"))

            # Execute
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(graph.execute())
            return result

        result = benchmark(run_linear)

        # Verification
        assert result.get("processed") == 10
        # 10 sequential tasks * 10ms + overhead < 1s
        assert benchmark.stats['mean'] < 1.0

    def test_parallel_workflow_10_branches(self, benchmark):
        """Benchmark: Parallel workflow with 10 branches"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.1)  # Simulate 100ms work
            return {"count": state.get("count", 0) + 1}

        def run_parallel():
            graph = WorkflowGraph()

            # Create parallel workflow
            graph.add_node(WorkflowNode("start", NodeType.START))
            for i in range(10):
                graph.add_node(WorkflowNode(f"branch_{i}", NodeType.TASK, handler=task_handler))
            graph.add_node(WorkflowNode("end", NodeType.END))

            # All branches start from start node
            for i in range(10):
                graph.add_edge(WorkflowEdge("start", f"branch_{i}"))
                graph.add_edge(WorkflowEdge(f"branch_{i}", "end"))

            # Execute
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(graph.execute())
            return result

        result = benchmark(run_parallel)

        # Verification - all branches should execute
        assert "count" in result.data or len(result.history) > 11
        # Parallel execution should be much faster than 10 * 100ms
        # Should complete in ~100ms + overhead < 0.5s
        assert benchmark.stats['mean'] < 0.5

    def test_complex_dag_workflow(self, benchmark):
        """Benchmark: Complex DAG with multiple levels"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            return {"processed": state.get("processed", 0) + 1}

        def run_complex():
            graph = WorkflowGraph()

            # Create complex DAG
            #       start
            #      /  |  \
            #     a   b   c
            #     |\ /|\ /|
            #     | X | X |
            #     |/ \|/ \|
            #     d   e   f
            #      \  |  /
            #        end

            graph.add_node(WorkflowNode("start", NodeType.START))
            for node_id in ["a", "b", "c", "d", "e", "f"]:
                graph.add_node(WorkflowNode(node_id, NodeType.TASK, handler=task_handler))
            graph.add_node(WorkflowNode("end", NodeType.END))

            # First level
            graph.add_edge(WorkflowEdge("start", "a"))
            graph.add_edge(WorkflowEdge("start", "b"))
            graph.add_edge(WorkflowEdge("start", "c"))

            # Second level (cross connections)
            graph.add_edge(WorkflowEdge("a", "d"))
            graph.add_edge(WorkflowEdge("a", "e"))
            graph.add_edge(WorkflowEdge("b", "d"))
            graph.add_edge(WorkflowEdge("b", "e"))
            graph.add_edge(WorkflowEdge("b", "f"))
            graph.add_edge(WorkflowEdge("c", "e"))
            graph.add_edge(WorkflowEdge("c", "f"))

            # Final convergence
            graph.add_edge(WorkflowEdge("d", "end"))
            graph.add_edge(WorkflowEdge("e", "end"))
            graph.add_edge(WorkflowEdge("f", "end"))

            # Execute
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(graph.execute())
            return result

        result = benchmark(run_complex)

        # Verification
        assert result.get("processed") == 6
        # Complex DAG should benefit from parallelization
        assert benchmark.stats['mean'] < 0.5

    def test_conditional_workflow(self, benchmark):
        """Benchmark: Workflow with conditional branches"""
        async def decision_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            # Simulate decision logic
            return {"decision": "path_a"}

        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            return {"processed": True}

        def run_conditional():
            graph = WorkflowGraph()

            graph.add_node(WorkflowNode("start", NodeType.START))
            graph.add_node(WorkflowNode("decision", NodeType.TASK, handler=decision_handler))
            graph.add_node(WorkflowNode("path_a", NodeType.TASK, handler=task_handler))
            graph.add_node(WorkflowNode("path_b", NodeType.TASK, handler=task_handler))
            graph.add_node(WorkflowNode("end", NodeType.END))

            graph.add_edge(WorkflowEdge("start", "decision"))
            graph.add_edge(WorkflowEdge("decision", "path_a", condition=lambda s: s.get("decision") == "path_a"))
            graph.add_edge(WorkflowEdge("decision", "path_b", condition=lambda s: s.get("decision") == "path_b"))
            graph.add_edge(WorkflowEdge("path_a", "end"))
            graph.add_edge(WorkflowEdge("path_b", "end"))

            # Execute
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(graph.execute())
            return result

        result = benchmark(run_conditional)

        # Verification
        assert result.get("decision") == "path_a"
        assert result.get("processed") is True
        assert benchmark.stats['mean'] < 0.5

    def test_workflow_with_loops(self, benchmark):
        """Benchmark: Workflow with loop control"""
        async def loop_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            count = state.get("loop_count", 0) + 1
            return {"loop_count": count}

        def run_loop():
            graph = WorkflowGraph()

            graph.add_node(WorkflowNode("start", NodeType.START))
            graph.add_node(WorkflowNode("loop_body", NodeType.TASK, handler=loop_handler))
            graph.add_node(WorkflowNode("end", NodeType.END))

            graph.add_edge(WorkflowEdge("start", "loop_body"))
            # Loop back if count < 5
            graph.add_edge(WorkflowEdge("loop_body", "loop_body", condition=lambda s: s.get("loop_count", 0) < 5))
            # Exit loop if count >= 5
            graph.add_edge(WorkflowEdge("loop_body", "end", condition=lambda s: s.get("loop_count", 0) >= 5))

            # Execute
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(graph.execute())
            return result

        result = benchmark(run_loop)

        # Verification
        assert result.get("loop_count") == 5
        # 5 iterations * 10ms + overhead < 0.5s
        assert benchmark.stats['mean'] < 0.5


class TestWorkflowScalability:
    """Test workflow scalability with large graphs"""

    @pytest.mark.parametrize("node_count", [10, 50, 100])
    def test_large_parallel_workflow(self, node_count):
        """Test scalability with large number of parallel nodes"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.01)
            return {}

        graph = WorkflowGraph()

        # Create large parallel workflow
        graph.add_node(WorkflowNode("start", NodeType.START))
        for i in range(node_count):
            graph.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))
        graph.add_node(WorkflowNode("end", NodeType.END))

        # Connect all tasks in parallel
        for i in range(node_count):
            graph.add_edge(WorkflowEdge("start", f"task_{i}"))
            graph.add_edge(WorkflowEdge(f"task_{i}", "end"))

        # Execute and measure
        start_time = time.time()

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(graph.execute())

        duration = time.time() - start_time

        # Verification
        assert len(result.history) >= node_count

        print(f"\n📈 Workflow Scalability ({node_count} parallel nodes):")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Nodes/sec: {node_count/duration:.2f}")

        # Should handle large workflows efficiently
        # Even 100 parallel nodes should complete in reasonable time
        assert duration < 2.0, f"Too slow for {node_count} nodes: {duration:.3f}s"

    def test_deep_sequential_workflow(self):
        """Test deep sequential workflow (stress test)"""
        async def task_handler(state: WorkflowState):
            await asyncio.sleep(0.001)  # 1ms per task
            return {}

        graph = WorkflowGraph()

        # Create deep sequential workflow (100 levels)
        depth = 100
        graph.add_node(WorkflowNode("start", NodeType.START))
        for i in range(depth):
            graph.add_node(WorkflowNode(f"task_{i}", NodeType.TASK, handler=task_handler))
        graph.add_node(WorkflowNode("end", NodeType.END))

        # Link sequentially
        graph.add_edge(WorkflowEdge("start", "task_0"))
        for i in range(depth - 1):
            graph.add_edge(WorkflowEdge(f"task_{i}", f"task_{i+1}"))
        graph.add_edge(WorkflowEdge(f"task_{depth-1}", "end"))

        # Execute and measure
        start_time = time.time()

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(graph.execute())

        duration = time.time() - start_time

        # Verification
        assert len(result.history) >= depth

        print(f"\n📊 Deep Sequential Workflow ({depth} levels):")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Per-node overhead: {(duration - depth*0.001)*1000/depth:.3f}ms")

        # Should handle deep workflows without stack overflow
        assert duration < 5.0, f"Too slow for {depth} sequential nodes"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
