"""
Demo: Complex workflow with realistic task decomposition
Shows how the scheduler handles complex dependencies
"""

import asyncio
from src.scheduler import MultiAgentScheduler, Task, ExecutionMode
from src.agents import MockAgent

async def main():
    print("\n" + "="*60)
    print("🎯 DEMO: Complex Website Development Project")
    print("="*60)

    # Setup agents
    agents = {
        'claude': MockAgent(name="Claude", delay=0.5),
        'openai': MockAgent(name="OpenAI", delay=0.5),
        'gemini': MockAgent(name="Gemini", delay=0.3)
    }

    scheduler = MultiAgentScheduler(agents)

    # Define a complex task graph
    tasks = [
        Task(id="task1", prompt="Design database schema",
             task_type="coding", priority=1),

        Task(id="task2", prompt="Design UI mockups",
             task_type="coding", priority=1),

        Task(id="task3", prompt="Implement backend API",
             task_type="coding", priority=2, depends_on=["task1"]),

        Task(id="task4", prompt="Implement frontend components",
             task_type="coding", priority=2, depends_on=["task2"]),

        Task(id="task5", prompt="Write integration tests",
             task_type="coding", priority=3, depends_on=["task3", "task4"]),

        Task(id="task6", prompt="Deploy to staging",
             task_type="simple", priority=4, depends_on=["task5"])
    ]

    print("\n📋 Task Dependency Graph:")
    print("  Batch 1 (Parallel): task1, task2 - Design phase")
    print("  Batch 2 (Parallel): task3, task4 - Implementation phase")
    print("  Batch 3 (Serial):   task5 - Testing phase")
    print("  Batch 4 (Serial):   task6 - Deployment phase")

    print("\n🚀 Starting intelligent scheduling...\n")

    # Execute with auto mode (will use hybrid mode due to dependencies)
    result = await scheduler.schedule(tasks, mode=ExecutionMode.AUTO)

    # Print summary
    print("\n" + "="*60)
    print("📊 Execution Summary")
    print("="*60)
    print(f"⏱️  Total Time: {result.total_time:.2f}s")
    print(f"✅ Tasks Completed: {result.task_count}")
    print(f"📈 Success Rate: {sum(1 for r in result.results if r.get('success'))/len(result.results)*100:.1f}%")

    # Calculate theoretical serial time
    serial_time = sum(0.5 for _ in range(4)) + sum(0.3 for _ in range(2))
    improvement = (serial_time - result.total_time) / serial_time * 100

    print(f"\n💡 Performance Analysis:")
    print(f"  Serial execution would take: ~{serial_time:.2f}s")
    print(f"  Actual parallel time: {result.total_time:.2f}s")
    print(f"  Performance improvement: {improvement:.1f}%")

    print("\n🎯 Agent Task Distribution:")
    agent_counts = {}
    for r in result.results:
        agent = r.get('agent_selected', 'unknown')
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    for agent, count in agent_counts.items():
        print(f"  {agent}: {count} tasks")

    print("\n✅ Demo completed successfully!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
