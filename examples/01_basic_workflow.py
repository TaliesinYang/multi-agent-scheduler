"""
Example 1: Basic Workflow
==========================

This example demonstrates how to create a simple workflow with the Multi-Agent Scheduler.
"""

import asyncio
from src.agents import MockAgent
from src.scheduler import MultiAgentScheduler, Task, ExecutionMode


async def main():
    """Run basic workflow example"""

    print("=" * 60)
    print("Example 1: Basic Multi-Agent Workflow")
    print("=" * 60)

    # Step 1: Create agents
    print("\n📦 Step 1: Creating agents...")
    agents = {
        'claude': MockAgent(name="Claude", delay=0.5),
        'openai': MockAgent(name="OpenAI", delay=0.5),
        'gemini': MockAgent(name="Gemini", delay=0.5)
    }
    print(f"✓ Created {len(agents)} agents")

    # Step 2: Create scheduler
    print("\n📦 Step 2: Initializing scheduler...")
    scheduler = MultiAgentScheduler(agents)
    print("✓ Scheduler initialized")

    # Step 3: Define tasks
    print("\n📦 Step 3: Defining tasks...")
    tasks = [
        Task(
            id="task1",
            prompt="Write a Python function to calculate Fibonacci numbers",
            task_type="coding"
        ),
        Task(
            id="task2",
            prompt="Explain quantum computing in simple terms",
            task_type="analysis"
        ),
        Task(
            id="task3",
            prompt="What is 2+2?",
            task_type="simple"
        )
    ]
    print(f"✓ Defined {len(tasks)} tasks")

    # Step 4: Execute in parallel
    print("\n📦 Step 4: Executing tasks in parallel...")
    result = await scheduler.schedule(tasks, mode=ExecutionMode.PARALLEL)

    print(f"\n✅ Execution completed!")
    print(f"  - Total time: {result.total_time:.2f}s")
    print(f"  - Tasks completed: {result.task_count}")
    print(f"  - Mode: {result.mode.value}")

    # Step 5: Display results
    print("\n📋 Results:")
    for task_result in result.results:
        print(f"\n  Task: {task_result['task_id']}")
        print(f"  Agent: {task_result['agent_selected']}")
        print(f"  Success: {task_result['success']}")
        print(f"  Result: {task_result['result'][:100]}...")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
