"""
Workflow Graph Examples

Demonstrates how to use the graph-based workflow engine for complex
task orchestration with conditional branching, parallel execution, and loops.
"""

import asyncio
import os
from src.workflow_graph import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    WorkflowState,
    NodeType,
    EdgeType,
    create_simple_workflow
)
from src.scheduler import MultiAgentScheduler, Task
from src.agents import ClaudeAgent, OpenAIAgent


async def example_1_simple_sequential():
    """
    Example 1: Simple sequential workflow

    Demonstrates basic linear workflow with state passing between nodes.
    """
    print("\n" + "=" * 60)
    print("Example 1: Simple Sequential Workflow")
    print("=" * 60)

    graph = WorkflowGraph(graph_id="sequential_demo")

    # Define task handlers
    async def fetch_data(state: WorkflowState):
        print("  📥 Fetching data...")
        await asyncio.sleep(0.5)
        return {"data": [1, 2, 3, 4, 5]}

    async def process_data(state: WorkflowState):
        print("  ⚙️  Processing data...")
        data = state.get("data", [])
        processed = [x * 2 for x in data]
        await asyncio.sleep(0.5)
        return {"processed": processed}

    async def save_results(state: WorkflowState):
        print("  💾 Saving results...")
        processed = state.get("processed", [])
        await asyncio.sleep(0.5)
        return {"saved": True, "count": len(processed)}

    # Build workflow
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("fetch", NodeType.TASK, handler=fetch_data))
    graph.add_node(WorkflowNode("process", NodeType.TASK, handler=process_data))
    graph.add_node(WorkflowNode("save", NodeType.TASK, handler=save_results))
    graph.add_node(WorkflowNode("end", NodeType.END))

    graph.add_edge(WorkflowEdge("start", "fetch"))
    graph.add_edge(WorkflowEdge("fetch", "process"))
    graph.add_edge(WorkflowEdge("process", "save"))
    graph.add_edge(WorkflowEdge("save", "end"))

    # Execute
    result = await graph.execute()

    print(f"\n✅ Workflow completed!")
    print(f"   Path: {' → '.join(result.history)}")
    print(f"   Saved {result.get('count')} items")
    print(f"   Duration: {result.metadata.get('duration', 0):.2f}s\n")


async def example_2_conditional_branching():
    """
    Example 2: Conditional branching workflow

    Demonstrates if/else logic with conditional edges based on state.
    """
    print("\n" + "=" * 60)
    print("Example 2: Conditional Branching")
    print("=" * 60)

    graph = WorkflowGraph(graph_id="conditional_demo")

    # Define handlers
    async def check_quality(state: WorkflowState):
        print("  🔍 Checking quality...")
        await asyncio.sleep(0.3)
        # Simulate quality score
        score = 85
        return {"quality_score": score}

    async def high_quality_path(state: WorkflowState):
        print("  ✨ High quality detected - fast track!")
        return {"status": "approved", "reason": "high_quality"}

    async def manual_review_path(state: WorkflowState):
        print("  👀 Manual review required...")
        await asyncio.sleep(0.5)
        return {"status": "under_review", "reason": "manual_check"}

    async def rejection_path(state: WorkflowState):
        print("  ❌ Quality too low - rejected")
        return {"status": "rejected", "reason": "low_quality"}

    # Build workflow
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("check", NodeType.TASK, handler=check_quality))
    graph.add_node(WorkflowNode("approve", NodeType.TASK, handler=high_quality_path))
    graph.add_node(WorkflowNode("review", NodeType.TASK, handler=manual_review_path))
    graph.add_node(WorkflowNode("reject", NodeType.TASK, handler=rejection_path))
    graph.add_node(WorkflowNode("end", NodeType.END))

    graph.add_edge(WorkflowEdge("start", "check"))

    # Add conditional branches
    graph.add_edge(WorkflowEdge(
        "check", "approve",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("quality_score", 0) >= 80,
        label="score >= 80"
    ))
    graph.add_edge(WorkflowEdge(
        "check", "review",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: 50 <= s.get("quality_score", 0) < 80,
        label="50 <= score < 80"
    ))
    graph.add_edge(WorkflowEdge(
        "check", "reject",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("quality_score", 0) < 50,
        label="score < 50"
    ))

    graph.add_edge(WorkflowEdge("approve", "end"))
    graph.add_edge(WorkflowEdge("review", "end"))
    graph.add_edge(WorkflowEdge("reject", "end"))

    # Execute
    result = await graph.execute()

    print(f"\n✅ Workflow completed!")
    print(f"   Path: {' → '.join(result.history)}")
    print(f"   Status: {result.get('status')}")
    print(f"   Reason: {result.get('reason')}\n")


async def example_3_parallel_processing():
    """
    Example 3: Parallel processing workflow

    Demonstrates concurrent execution of independent tasks.
    """
    print("\n" + "=" * 60)
    print("Example 3: Parallel Processing")
    print("=" * 60)

    graph = WorkflowGraph(graph_id="parallel_demo")

    import time

    # Define parallel tasks
    async def analyze_text(state: WorkflowState):
        print("  📝 Analyzing text...")
        await asyncio.sleep(1.0)
        return {"text_analysis": "complete", "word_count": 1500}

    async def analyze_sentiment(state: WorkflowState):
        print("  😊 Analyzing sentiment...")
        await asyncio.sleep(1.0)
        return {"sentiment": "positive", "confidence": 0.85}

    async def extract_keywords(state: WorkflowState):
        print("  🔑 Extracting keywords...")
        await asyncio.sleep(1.0)
        return {"keywords": ["AI", "workflow", "automation"]}

    async def generate_summary(state: WorkflowState):
        print("  📊 Generating summary...")
        await asyncio.sleep(1.0)
        return {"summary": "Document processed successfully"}

    async def combine_results(state: WorkflowState):
        print("  🔀 Combining results...")
        return {"combined": True}

    # Build parallel workflow
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("text", NodeType.TASK, handler=analyze_text))
    graph.add_node(WorkflowNode("sentiment", NodeType.TASK, handler=analyze_sentiment))
    graph.add_node(WorkflowNode("keywords", NodeType.TASK, handler=extract_keywords))
    graph.add_node(WorkflowNode("summary", NodeType.TASK, handler=generate_summary))
    graph.add_node(WorkflowNode("combine", NodeType.TASK, handler=combine_results))
    graph.add_node(WorkflowNode("end", NodeType.END))

    # Add parallel branches
    graph.add_parallel_branches(
        "start",
        ["text", "sentiment", "keywords", "summary"],
        "combine"
    )
    graph.add_edge(WorkflowEdge("combine", "end"))

    # Execute and time
    start = time.time()
    result = await graph.execute()
    duration = time.time() - start

    print(f"\n✅ Workflow completed!")
    print(f"   Duration: {duration:.2f}s (would be ~4s if sequential)")
    print(f"   All tasks completed in parallel!")
    print(f"   Word count: {result.get('word_count')}")
    print(f"   Sentiment: {result.get('sentiment')}")
    print(f"   Keywords: {result.get('keywords')}\n")


async def example_4_loop_processing():
    """
    Example 4: Loop-based workflow

    Demonstrates iterative processing with loop control.
    """
    print("\n" + "=" * 60)
    print("Example 4: Loop Processing")
    print("=" * 60)

    graph = WorkflowGraph(graph_id="loop_demo")

    async def initialize(state: WorkflowState):
        print("  🎬 Initializing...")
        return {"count": 0, "sum": 0}

    async def process_iteration(state: WorkflowState):
        count = state.get("count", 0)
        current_sum = state.get("sum", 0)

        # Simulate processing
        value = count + 1
        new_sum = current_sum + value

        print(f"  ⚙️  Iteration {value}: sum = {new_sum}")
        await asyncio.sleep(0.2)

        return {"count": value, "sum": new_sum}

    async def finalize(state: WorkflowState):
        print("  ✅ Finalizing...")
        return {"final_sum": state.get("sum")}

    # Build loop workflow
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("init", NodeType.TASK, handler=initialize))
    graph.add_node(WorkflowNode("process", NodeType.TASK, handler=process_iteration))
    graph.add_node(WorkflowNode("finalize", NodeType.TASK, handler=finalize))
    graph.add_node(WorkflowNode("end", NodeType.END))

    graph.add_edge(WorkflowEdge("start", "init"))
    graph.add_edge(WorkflowEdge("init", "process"))

    # Add loop back edge (continue while count < 5)
    graph.add_edge(WorkflowEdge(
        "process", "process",
        edge_type=EdgeType.LOOP_BACK,
        condition=lambda s: s.get("count", 0) < 5,
        label="count < 5"
    ))

    # Exit loop when done
    graph.add_edge(WorkflowEdge(
        "process", "finalize",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("count", 0) >= 5,
        label="count >= 5"
    ))

    graph.add_edge(WorkflowEdge("finalize", "end"))

    # Execute
    result = await graph.execute()

    print(f"\n✅ Loop completed!")
    print(f"   Final sum: {result.get('final_sum')} (expected: 15)")
    print(f"   Iterations: {result.get('count')}\n")


async def example_5_scheduler_integration():
    """
    Example 5: Scheduler integration

    Demonstrates using workflows with the scheduler to execute AI agent tasks.
    """
    print("\n" + "=" * 60)
    print("Example 5: Scheduler Integration")
    print("=" * 60)

    # Check for API keys
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, using mock example")

        # Create mock scheduler
        from src.agents import BaseAgent

        class MockAgent(BaseAgent):
            def __init__(self):
                super().__init__(name="Mock", max_concurrent=5)

            async def call(self, prompt: str):
                await asyncio.sleep(0.1)
                return {
                    "agent": self.name,
                    "result": f"Processed: {prompt[:50]}...",
                    "success": True,
                    "latency": 0.1,
                    "tokens": 10
                }

        scheduler = MultiAgentScheduler(agents={'mock': MockAgent()})
    else:
        # Create real scheduler
        scheduler = MultiAgentScheduler(agents={
            'claude': ClaudeAgent(api_key=api_key)
        })

    # Create tasks
    tasks = [
        Task(id="design", prompt="Design a REST API for a blog", task_type="coding"),
        Task(id="implement", prompt="Implement user authentication", task_type="coding"),
        Task(id="test", prompt="Write unit tests", task_type="coding")
    ]

    # Create workflow from tasks (sequential)
    print("\n📊 Creating sequential workflow from tasks...")
    graph = scheduler.create_task_workflow(tasks, workflow_type="sequential")

    print(f"   Graph: {graph.graph_id}")
    print(f"   Nodes: {len(graph.nodes)}")
    print(f"   Edges: {len(graph.edges)}")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await scheduler.execute_workflow(graph)

    print(f"\n✅ All tasks completed!")
    print(f"   Path: {' → '.join(result.history)}\n")


async def example_6_complex_code_review():
    """
    Example 6: Complex code review workflow

    Demonstrates a real-world scenario combining conditional logic,
    parallel processing, and loops.
    """
    print("\n" + "=" * 60)
    print("Example 6: Code Review Workflow")
    print("=" * 60)

    graph = WorkflowGraph(graph_id="code_review")

    # Define handlers
    async def submit_code(state: WorkflowState):
        print("  📤 Code submitted for review")
        return {
            "code_quality": 75,
            "test_coverage": 80,
            "security_issues": 2,
            "review_attempts": 0
        }

    async def automated_checks(state: WorkflowState):
        print("  🤖 Running automated checks...")
        await asyncio.sleep(0.5)
        return {"automated_passed": True}

    async def security_scan(state: WorkflowState):
        print("  🔒 Running security scan...")
        await asyncio.sleep(0.5)
        issues = state.get("security_issues", 0)
        return {"security_passed": issues == 0}

    async def test_validation(state: WorkflowState):
        print("  🧪 Validating tests...")
        await asyncio.sleep(0.5)
        coverage = state.get("test_coverage", 0)
        return {"tests_passed": coverage >= 80}

    async def gather_checks(state: WorkflowState):
        print("  📊 Gathering check results...")
        auto = state.get("automated_passed", False)
        security = state.get("security_passed", False)
        tests = state.get("tests_passed", False)

        all_passed = auto and security and tests
        return {"all_checks_passed": all_passed}

    async def manual_review(state: WorkflowState):
        attempts = state.get("review_attempts", 0)
        print(f"  👤 Manual review (attempt {attempts + 1})...")
        await asyncio.sleep(0.5)

        # Simulate review decision
        quality = state.get("code_quality", 0)
        approved = quality >= 80 or attempts >= 2

        return {
            "review_approved": approved,
            "review_attempts": attempts + 1
        }

    async def request_changes(state: WorkflowState):
        print("  📝 Requesting changes...")
        # Simulate improvement
        quality = state.get("code_quality", 0)
        return {"code_quality": min(quality + 10, 100)}

    async def approve_merge(state: WorkflowState):
        print("  ✅ Code approved for merge!")
        return {"status": "approved"}

    async def reject_pr(state: WorkflowState):
        print("  ❌ PR rejected")
        return {"status": "rejected"}

    # Build workflow
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("submit", NodeType.TASK, handler=submit_code))
    graph.add_node(WorkflowNode("auto_check", NodeType.TASK, handler=automated_checks))
    graph.add_node(WorkflowNode("security", NodeType.TASK, handler=security_scan))
    graph.add_node(WorkflowNode("tests", NodeType.TASK, handler=test_validation))
    graph.add_node(WorkflowNode("gather", NodeType.TASK, handler=gather_checks))
    graph.add_node(WorkflowNode("manual", NodeType.TASK, handler=manual_review))
    graph.add_node(WorkflowNode("changes", NodeType.TASK, handler=request_changes))
    graph.add_node(WorkflowNode("approve", NodeType.TASK, handler=approve_merge))
    graph.add_node(WorkflowNode("reject", NodeType.TASK, handler=reject_pr))
    graph.add_node(WorkflowNode("end", NodeType.END))

    # Connect nodes
    graph.add_edge(WorkflowEdge("start", "submit"))

    # Parallel automated checks
    graph.add_parallel_branches("submit", ["auto_check", "security", "tests"], "gather")

    # Conditional: if checks pass, go to manual review
    graph.add_edge(WorkflowEdge(
        "gather", "manual",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("all_checks_passed", False),
        label="checks passed"
    ))

    # If checks fail, reject
    graph.add_edge(WorkflowEdge(
        "gather", "reject",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: not s.get("all_checks_passed", False),
        label="checks failed"
    ))

    # After manual review: approve or request changes
    graph.add_edge(WorkflowEdge(
        "manual", "approve",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("review_approved", False),
        label="approved"
    ))

    graph.add_edge(WorkflowEdge(
        "manual", "changes",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: not s.get("review_approved", False),
        label="changes requested"
    ))

    # Loop back from changes to manual review (with limit)
    graph.add_edge(WorkflowEdge(
        "changes", "manual",
        edge_type=EdgeType.LOOP_BACK,
        condition=lambda s: s.get("review_attempts", 0) < 3,
        label="retry"
    ))

    # If too many attempts, reject
    graph.add_edge(WorkflowEdge(
        "changes", "reject",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("review_attempts", 0) >= 3,
        label="max attempts"
    ))

    # Connect to end
    graph.add_edge(WorkflowEdge("approve", "end"))
    graph.add_edge(WorkflowEdge("reject", "end"))

    # Execute
    result = await graph.execute()

    print(f"\n✅ Review workflow completed!")
    print(f"   Status: {result.get('status')}")
    print(f"   Review attempts: {result.get('review_attempts', 0)}")
    print(f"   Path: {' → '.join(result.history[-10:])}")  # Last 10 nodes

    # Generate visualization
    print(f"\n📊 Workflow visualization (DOT format):")
    print("=" * 60)
    dot = graph.visualize()
    print(dot[:500] + "..." if len(dot) > 500 else dot)
    print()


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("🔀 WORKFLOW GRAPH EXAMPLES")
    print("=" * 60)
    print("\nThese examples demonstrate the workflow engine capabilities:")
    print("  1. Sequential workflows")
    print("  2. Conditional branching")
    print("  3. Parallel processing")
    print("  4. Loop control")
    print("  5. Scheduler integration")
    print("  6. Complex real-world scenario")
    print("=" * 60)

    # Run examples
    await example_1_simple_sequential()
    await example_2_conditional_branching()
    await example_3_parallel_processing()
    await example_4_loop_processing()
    await example_5_scheduler_integration()
    await example_6_complex_code_review()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
