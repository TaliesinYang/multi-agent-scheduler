"""
Complete System Demonstration

Shows all features working together:
- Graph-based workflows
- Checkpointing & recovery
- Human-in-the-loop
- Role abstraction
- Tool composition
- Distributed tracing
"""

import asyncio
from src.workflow_graph import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowState,
    NodeType, EdgeType, create_approval_node
)
from src.checkpoint import CheckpointManager, FileSystemBackend
from src.human_in_the_loop import HumanInputManager, CallbackInputHandler
from src.role_abstraction import (
    RoleRegistry, create_manager_role, create_coder_role,
    create_reviewer_role, RoleBasedRouter
)
from src.tool_system import (
    ToolRegistry, create_calculator_tool, create_web_search_tool,
    ToolChain
)
from src.tracing import get_tracer, TracingExporter
from src.scheduler import MultiAgentScheduler
from src.agents import BaseAgent


class DemoAgent(BaseAgent):
    """Demo agent for testing"""

    def __init__(self, name: str):
        super().__init__(name=name, max_concurrent=5)

    async def call(self, prompt: str):
        await asyncio.sleep(0.1)
        return {
            "agent": self.name,
            "result": f"{self.name} processed: {prompt[:50]}...",
            "success": True,
            "latency": 0.1,
            "tokens": 10
        }


async def demo_1_workflow_with_checkpoints():
    """Demo 1: Workflow with automatic checkpointing"""
    print("\n" + "=" * 60)
    print("DEMO 1: Workflow with Checkpointing")
    print("=" * 60)

    # Setup
    checkpoint_manager = CheckpointManager(
        backend=FileSystemBackend(".demo_checkpoints"),
        checkpoint_interval=1.0
    )

    agent = DemoAgent("demo_agent")
    scheduler = MultiAgentScheduler(
        agents={'demo': agent},
        checkpoint_manager=checkpoint_manager,
        enable_checkpoints=True
    )

    # Create workflow
    graph = WorkflowGraph(graph_id="checkpoint_demo")

    async def task1(state: WorkflowState):
        print("  Executing task 1...")
        await asyncio.sleep(0.5)
        return {"step1": "complete"}

    async def task2(state: WorkflowState):
        print("  Executing task 2...")
        await asyncio.sleep(0.5)
        return {"step2": "complete"}

    async def task3(state: WorkflowState):
        print("  Executing task 3...")
        await asyncio.sleep(0.5)
        return {"step3": "complete"}

    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=task1))
    graph.add_node(WorkflowNode("task2", NodeType.TASK, handler=task2))
    graph.add_node(WorkflowNode("task3", NodeType.TASK, handler=task3))
    graph.add_node(WorkflowNode("end", NodeType.END))

    graph.add_edge(WorkflowEdge("start", "task1"))
    graph.add_edge(WorkflowEdge("task1", "task2"))
    graph.add_edge(WorkflowEdge("task2", "task3"))
    graph.add_edge(WorkflowEdge("task3", "end"))

    # Execute with checkpointing
    result = await scheduler.execute_workflow(
        graph,
        execution_id="demo_exec_1"
    )

    print(f"\n✅ Workflow completed!")
    print(f"   Steps completed: {result.history}")

    # List checkpoints
    checkpoints = await checkpoint_manager.list_checkpoints(execution_id="demo_exec_1")
    print(f"   Checkpoints created: {len(checkpoints)}")


async def demo_2_hitl_approval_workflow():
    """Demo 2: Human-in-the-loop approval workflow"""
    print("\n" + "=" * 60)
    print("DEMO 2: Human-in-the-Loop Approval")
    print("=" * 60)

    # Setup with auto-approve for demo
    hitl_manager = HumanInputManager(auto_approve=True)

    # Create approval workflow
    graph = WorkflowGraph(graph_id="approval_demo")

    async def prepare_deployment(state: WorkflowState):
        print("  Preparing deployment...")
        await asyncio.sleep(0.3)
        return {"version": "1.2.3", "environment": "production"}

    async def deploy(state: WorkflowState):
        print("  Deploying to production...")
        await asyncio.sleep(0.3)
        return {"deployed": True}

    async def rollback(state: WorkflowState):
        print("  Rolling back deployment...")
        return {"deployed": False}

    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("prepare", NodeType.TASK, handler=prepare_deployment))

    # Add approval node
    approval = create_approval_node(
        "approve_deploy",
        "Approve deployment to production?",
        hitl_manager=hitl_manager,
        timeout=10.0
    )
    graph.add_node(approval)

    graph.add_node(WorkflowNode("deploy", NodeType.TASK, handler=deploy))
    graph.add_node(WorkflowNode("rollback", NodeType.TASK, handler=rollback))
    graph.add_node(WorkflowNode("end", NodeType.END))

    # Connect nodes
    graph.add_edge(WorkflowEdge("start", "prepare"))
    graph.add_edge(WorkflowEdge("prepare", "approve_deploy"))

    # Conditional routing based on approval
    graph.add_edge(WorkflowEdge(
        "approve_deploy", "deploy",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: s.get("approve_deploy_approved", False),
        label="approved"
    ))
    graph.add_edge(WorkflowEdge(
        "approve_deploy", "rollback",
        edge_type=EdgeType.CONDITIONAL,
        condition=lambda s: not s.get("approve_deploy_approved", False),
        label="rejected"
    ))

    graph.add_edge(WorkflowEdge("deploy", "end"))
    graph.add_edge(WorkflowEdge("rollback", "end"))

    # Execute
    result = await graph.execute()

    print(f"\n✅ Approval workflow completed!")
    print(f"   Path: {' → '.join(result.history)}")
    print(f"   Deployed: {result.get('deployed', False)}")


async def demo_3_role_based_routing():
    """Demo 3: Role-based agent routing"""
    print("\n" + "=" * 60)
    print("DEMO 3: Role-Based Routing")
    print("=" * 60)

    # Setup agents with roles
    registry = RoleRegistry()

    # Register roles
    manager = create_manager_role("project_manager")
    coder = create_coder_role("senior_coder", languages=["python", "javascript"])
    reviewer = create_reviewer_role("code_reviewer")

    # Create demo agents
    agents = {
        'manager_agent': DemoAgent("Manager"),
        'coder_agent': DemoAgent("Coder"),
        'reviewer_agent': DemoAgent("Reviewer")
    }

    # Assign roles to agents
    registry.register_role(manager, 'manager_agent')
    registry.register_role(coder, 'coder_agent')
    registry.register_role(reviewer, 'reviewer_agent')

    # Create router
    router = RoleBasedRouter(registry)

    # Route tasks
    print("\n  Routing tasks to appropriate roles:")

    tasks = [
        ("Implement login feature", ["python", "coding"]),
        ("Review pull request #123", ["code_review"]),
        ("Plan Q4 roadmap", ["planning", "coordination"])
    ]

    for task_desc, skills in tasks:
        agent_name = router.route_task(task_desc, required_skills=skills)
        assigned_role = None
        for role_name, role in registry.roles.items():
            if registry.get_agent_for_role(role_name) == agent_name:
                assigned_role = role.name
                break

        print(f"  - '{task_desc}'")
        print(f"    → Assigned to: {agent_name} ({assigned_role})")


async def demo_4_tool_composition():
    """Demo 4: Tool composition and chaining"""
    print("\n" + "=" * 60)
    print("DEMO 4: Tool Composition")
    print("=" * 60)

    # Setup tools
    registry = ToolRegistry()
    registry.register(create_calculator_tool())
    registry.register(create_web_search_tool())

    print("\n  Executing tool chain:")

    # Create tool chain
    chain = ToolChain(registry)
    chain.add_step("calculator", {"expression": "(10 + 5) * 2"})
    chain.add_step("web_search", {"query": "python async programming", "num_results": 3})

    # Execute chain
    results = await chain.execute()

    for result in results:
        print(f"\n  Tool: {result.tool_name}")
        print(f"  Success: {result.success}")
        if result.success:
            print(f"  Result: {result.result}")
            print(f"  Time: {result.execution_time:.3f}s")
        else:
            print(f"  Error: {result.error}")


async def demo_5_distributed_tracing():
    """Demo 5: Distributed tracing"""
    print("\n" + "=" * 60)
    print("DEMO 5: Distributed Tracing")
    print("=" * 60)

    # Get tracer
    tracer = get_tracer("demo_service")
    tracer.start_trace()

    print("\n  Executing traced workflow:")

    # Create traced workflow
    async with tracer.trace("workflow.execution") as workflow_span:
        workflow_span.set_attribute("workflow.type", "demo")

        async with tracer.trace("step.1") as step1:
            step1.add_event("processing_started")
            await asyncio.sleep(0.1)
            step1.add_event("processing_completed")

        async with tracer.trace("step.2") as step2:
            step2.set_attribute("step.number", 2)
            await asyncio.sleep(0.15)

        async with tracer.trace("step.3") as step3:
            await asyncio.sleep(0.08)

    # Export trace
    exporter = TracingExporter(tracer)
    print("\n  Trace structure:")
    exporter.export_to_console(tracer.current_trace_id)


async def demo_6_complete_integration():
    """Demo 6: All features integrated"""
    print("\n" + "=" * 60)
    print("DEMO 6: Complete System Integration")
    print("=" * 60)

    # Initialize all systems
    checkpoint_manager = CheckpointManager(
        backend=FileSystemBackend(".complete_demo"),
        checkpoint_interval=2.0
    )
    hitl_manager = HumanInputManager(auto_approve=True)
    tool_registry = ToolRegistry()
    tool_registry.register(create_calculator_tool())

    # Setup scheduler
    agent = DemoAgent("complete_agent")
    scheduler = MultiAgentScheduler(
        agents={'agent': agent},
        checkpoint_manager=checkpoint_manager,
        enable_checkpoints=True
    )

    # Start tracing
    tracer = get_tracer("complete_demo")
    trace_id = tracer.start_trace()

    async with tracer.trace("complete.workflow") as root_span:
        root_span.set_attribute("features", "all")

        # Create complex workflow
        graph = WorkflowGraph(graph_id="complete_demo")

        async def analyze_task(state: WorkflowState):
            async with tracer.trace("task.analyze"):
                await asyncio.sleep(0.2)
                return {"complexity": "medium", "estimated_time": 2.5}

        async def calculate_metrics(state: WorkflowState):
            # Use tool within workflow
            tool = tool_registry.get("calculator")
            result = await tool.execute(expression="100 * 0.95")
            return {"score": result}

        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("analyze", NodeType.TASK, handler=analyze_task))

        # Add approval
        approval = create_approval_node(
            "approve_execution",
            "Proceed with execution?",
            hitl_manager=hitl_manager
        )
        graph.add_node(approval)

        graph.add_node(WorkflowNode("calculate", NodeType.TASK, handler=calculate_metrics))
        graph.add_node(WorkflowNode("end", NodeType.END))

        # Connect
        graph.add_edge(WorkflowEdge("start", "analyze"))
        graph.add_edge(WorkflowEdge("analyze", "approve_execution"))
        graph.add_edge(WorkflowEdge(
            "approve_execution", "calculate",
            edge_type=EdgeType.CONDITIONAL,
            condition=lambda s: s.get("approve_execution_approved"),
            label="approved"
        ))
        graph.add_edge(WorkflowEdge(
            "approve_execution", "end",
            edge_type=EdgeType.CONDITIONAL,
            condition=lambda s: not s.get("approve_execution_approved"),
            label="rejected"
        ))
        graph.add_edge(WorkflowEdge("calculate", "end"))

        # Execute
        print("\n  Executing integrated workflow...")
        result = await scheduler.execute_workflow(
            graph,
            execution_id="complete_demo_1"
        )

        print(f"\n✅ Complete workflow finished!")
        print(f"   Complexity: {result.get('complexity')}")
        print(f"   Score: {result.get('score')}")
        print(f"   Checkpoints: Created automatically")

    # Show trace
    print("\n  Trace:")
    exporter = TracingExporter(tracer)
    exporter.export_to_console(trace_id)


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("🚀 MULTI-AGENT SCHEDULER - COMPLETE SYSTEM DEMO")
    print("=" * 60)
    print("\nDemonstrating all production features:")
    print("  1. Workflows with checkpointing")
    print("  2. Human-in-the-loop approvals")
    print("  3. Role-based agent routing")
    print("  4. Tool composition")
    print("  5. Distributed tracing")
    print("  6. Complete system integration")
    print("=" * 60)

    await demo_1_workflow_with_checkpoints()
    await demo_2_hitl_approval_workflow()
    await demo_3_role_based_routing()
    await demo_4_tool_composition()
    await demo_5_distributed_tracing()
    await demo_6_complete_integration()

    print("\n" + "=" * 60)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe Multi-Agent Scheduler now includes:")
    print("  ✓ Graph-based workflow engine (LangGraph-like)")
    print("  ✓ Checkpointing & recovery (Temporal-like)")
    print("  ✓ Human-in-the-loop (Enterprise workflows)")
    print("  ✓ Role abstraction (CrewAI-like)")
    print("  ✓ Tool composition (LangChain-like)")
    print("  ✓ Distributed tracing (OpenTelemetry-compatible)")
    print("\n🎉 Production-ready multi-agent orchestration system!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
