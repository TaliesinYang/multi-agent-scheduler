"""
Multi-Agent Scheduler Demo
Demo program: Showcasing core features and performance comparison
"""

import asyncio
import sys
from typing import Dict
from src.agents import ClaudeAgent, OpenAIAgent, GeminiAgent, MockAgent
from src.scheduler import MultiAgentScheduler, Task, ExecutionMode


def print_header(title: str):
    """Print header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def demo_basic_parallel(scheduler: MultiAgentScheduler):
    """
    Demo 1: Basic Parallel Scheduling
    Demonstrates parallel execution of multiple independent tasks
    """
    print_header("Demo 1: Basic Parallel Scheduling")

    print("\n📋 Scenario: Generate content for multiple topics simultaneously")

    # Define tasks
    tasks = [
        Task(
            id="task1",
            prompt="Explain the core concept of quantum computing in one sentence",
            task_type="simple"
        ),
        Task(
            id="task2",
            prompt="Write a Python function to calculate the nth Fibonacci number",
            task_type="coding"
        ),
        Task(
            id="task3",
            prompt="Analyze three main advantages of cloud computing compared to traditional IT architecture",
            task_type="analysis"
        ),
        Task(
            id="task4",
            prompt="Create a short slogan for a startup company (about AI education)",
            task_type="creative"
        )
    ]

    print(f"\nTask list ({len(tasks)} tasks):")
    for task in tasks:
        print(f"  - {task.id}: {task.prompt[:50]}... [{task.task_type}]")

    # Execute scheduling
    result = await scheduler.schedule(tasks, mode=ExecutionMode.AUTO)

    # Print results
    scheduler.print_summary(result)
    scheduler.print_detailed_results(result, max_length=200)


async def demo_performance_comparison(scheduler: MultiAgentScheduler):
    """
    Demo 2: Performance Comparison
    Compare performance difference between parallel vs serial execution
    """
    print_header("Demo 2: Performance Comparison (Serial vs Parallel)")

    print("\n📋 Scenario: Generate haiku poems for 4 different seasons")

    # Create similar tasks (suitable for comparison)
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    tasks = [
        Task(
            id=f"haiku_{season}",
            prompt=f"Compose a haiku (Japanese short poem) about {season}",
            task_type="creative"
        )
        for season in seasons
    ]

    print(f"\nTask list ({len(tasks)} tasks):")
    for task in tasks:
        print(f"  - {task.id}")

    # Execute comparison
    comparison = await scheduler.compare_performance(tasks)

    # Print comparison results
    print("\n" + "=" * 70)
    print("📊 Performance Comparison Results")
    print("=" * 70)
    print(f"Serial execution time: {comparison['serial_time']:.2f} seconds")
    print(f"Parallel execution time: {comparison['parallel_time']:.2f} seconds")
    print(f"Time saved: {comparison['time_saved']:.2f} seconds")
    print(f"⚡ Performance gain: {comparison['performance_gain_percent']:.1f}%")

    # Visualization comparison
    print("\nTime comparison visualization:")
    serial_bars = int(comparison['serial_time'] / 0.5)
    parallel_bars = int(comparison['parallel_time'] / 0.5)

    print(f"Serial:   {'█' * serial_bars} {comparison['serial_time']:.2f}s")
    print(f"Parallel: {'█' * parallel_bars} {comparison['parallel_time']:.2f}s")


async def demo_dependency_scheduling(scheduler: MultiAgentScheduler):
    """
    Demo 3: Dependency-based Scheduling
    Demonstrates hybrid execution mode for tasks with dependencies
    """
    print_header("Demo 3: Dependency-based Scheduling (Hybrid Mode)")

    print("\n📋 Scenario: Multiple steps in developing a web application")
    print("  Some tasks must wait for prerequisite tasks to complete")

    # Define tasks with dependencies
    tasks = [
        Task(
            id="design_api",
            prompt="Design the interface specification for a user authentication API (RESTful)",
            task_type="coding",
            priority=3
        ),
        Task(
            id="design_database",
            prompt="Design database schema for user table (including username, email, password_hash)",
            task_type="coding",
            priority=3
        ),
        Task(
            id="implement_api",
            prompt="Implement Python code for user registration API (using Flask)",
            task_type="coding",
            depends_on=["design_api", "design_database"],  # Depends on previous two tasks
            priority=2
        ),
        Task(
            id="write_tests",
            prompt="Write unit tests for the user registration API",
            task_type="coding",
            depends_on=["implement_api"],  # Depends on implementation completion
            priority=1
        )
    ]

    print(f"\nTask dependencies:")
    for task in tasks:
        if task.depends_on:
            print(f"  {task.id} → depends on: {', '.join(task.depends_on)}")
        else:
            print(f"  {task.id} → no dependencies (can execute immediately)")

    # Execute scheduling (auto-detect dependencies and batch)
    result = await scheduler.schedule(tasks, mode=ExecutionMode.AUTO)

    # Print results
    scheduler.print_summary(result)


async def demo_agent_selection(scheduler: MultiAgentScheduler):
    """
    Demo 4: Intelligent Agent Selection
    Demonstrates how the scheduler selects the most suitable AI model based on task type
    """
    print_header("Demo 4: Intelligent Agent Selection")

    print("\n📋 Scenario: Different task types assigned to the most suitable AI")
    print("  - Coding tasks → Claude (strong coding ability)")
    print("  - Simple tasks → Gemini (free)")
    print("  - Analysis tasks → OpenAI (good reasoning ability)")

    # Diverse tasks
    tasks = [
        Task(
            id="code_sorting",
            prompt="Implement quick sort algorithm (Python)",
            task_type="coding"
        ),
        Task(
            id="simple_greeting",
            prompt="Generate a friendly greeting message",
            task_type="simple"
        ),
        Task(
            id="analyze_trend",
            prompt="Analyze three major trends in AI development in 2024",
            task_type="analysis"
        )
    ]

    print(f"\nTask list:")
    for task in tasks:
        print(f"  - [{task.task_type}] {task.id}")

    # Execute
    result = await scheduler.schedule(tasks, mode=ExecutionMode.PARALLEL)

    # Display agent selection
    print("\n" + "-" * 70)
    print("🤖 Agent assignment:")
    for r in result.results:
        task_id = r['task_id']
        agent = r['agent_selected']
        task_type = r['task_type']
        print(f"  {task_id} ({task_type}) → {agent}")

    scheduler.print_summary(result)


async def demo_mock_agents():
    """
    Demo 5: Mock Agent Testing
    Use mock agents for quick testing (no real API required)
    """
    print_header("Demo 5: Mock Agent Testing (Quick Demo)")

    print("\n📋 Description: Using mock agents, no real API keys needed")
    print("  Suitable for: Quick testing, demonstration, development debugging")

    # Create Mock agents
    agents = {
        'mock_fast': MockAgent(name="Fast-Mock", delay=0.5),
        'mock_medium': MockAgent(name="Medium-Mock", delay=1.0),
        'mock_slow': MockAgent(name="Slow-Mock", delay=2.0)
    }

    scheduler = MultiAgentScheduler(agents)

    # Modify selection strategy to use Mock agents
    scheduler.agent_selection_strategy = {
        'simple': 'mock_fast',
        'general': 'mock_medium',
        'complex': 'mock_slow'
    }

    # Create tasks
    tasks = [
        Task(id=f"task_{i}", prompt=f"Mock task {i}", task_type="simple")
        for i in range(6)
    ]

    print(f"\nCreated {len(tasks)} mock tasks")

    # Performance comparison
    comparison = await scheduler.compare_performance(tasks)

    # Display results
    print("\n" + "=" * 70)
    print(f"⚡ Performance gain: {comparison['performance_gain_percent']:.1f}%")
    print(f"Serial time: {comparison['serial_time']:.2f}s")
    print(f"Parallel time: {comparison['parallel_time']:.2f}s")


def print_menu():
    """Print menu"""
    print("\n" + "=" * 70)
    print("  Multi-Agent Scheduler - Demo Menu")
    print("=" * 70)
    print("1. Basic Parallel Scheduling")
    print("2. Performance Comparison (Serial vs Parallel)")
    print("3. Dependency-based Scheduling")
    print("4. Intelligent Agent Selection")
    print("5. Mock Agent Testing (No API Required)")
    print("6. Run All Demos")
    print("0. Exit")
    print("=" * 70)


async def main():
    """Main function"""
    print("\n" + "🚀" * 35)
    print("     Multi-Agent Intelligent Scheduler Demo")
    print("     CSCI-6650 Operating Systems Term Project")
    print("🚀" * 35)

    # Prompt user to select mode
    print("\nPlease select running mode:")
    print("1. Use real APIs (requires API keys)")
    print("2. Use Mock agents (quick testing, recommended)")

    try:
        mode_choice = input("\nPlease select (1/2) [default: 2]: ").strip() or "2"

        if mode_choice == "1":
            print("\n⚠️  Real API mode requires API key configuration")
            print("Please set API keys in config.py, or use environment variables:")
            print("  export ANTHROPIC_API_KEY='your-key'")
            print("  export OPENAI_API_KEY='your-key'")

            # Try to load configuration
            try:
                from src.config import ANTHROPIC_API_KEY, OPENAI_API_KEY
            except ImportError:
                print("\n❌ config.py not found, please create the configuration file first")
                print("Or choose Mock mode for testing")
                return

            # Create real agents
            agents = {
                'claude': ClaudeAgent(api_key=ANTHROPIC_API_KEY, max_concurrent=10),
                'openai': OpenAIAgent(api_key=OPENAI_API_KEY, max_concurrent=10),
                'gemini': GeminiAgent(max_concurrent=5)
            }

        else:
            # Use Mock agents
            print("\n✅ Using Mock agent mode")
            agents = {
                'claude': MockAgent(name="Claude-Mock", delay=1.5),
                'openai': MockAgent(name="OpenAI-Mock", delay=1.2),
                'gemini': MockAgent(name="Gemini-Mock", delay=0.8)
            }

        # Create scheduler
        scheduler = MultiAgentScheduler(agents)

        # Interactive menu
        while True:
            print_menu()
            choice = input("\nPlease select (0-6): ").strip()

            if choice == "0":
                print("\n👋 Thank you for using!")
                break

            elif choice == "1":
                await demo_basic_parallel(scheduler)

            elif choice == "2":
                await demo_performance_comparison(scheduler)

            elif choice == "3":
                await demo_dependency_scheduling(scheduler)

            elif choice == "4":
                await demo_agent_selection(scheduler)

            elif choice == "5":
                await demo_mock_agents()

            elif choice == "6":
                print("\n🏃 Running all demos...")
                await demo_basic_parallel(scheduler)
                await demo_performance_comparison(scheduler)
                await demo_dependency_scheduling(scheduler)
                await demo_agent_selection(scheduler)
                await demo_mock_agents()

                print("\n" + "=" * 70)
                print("✅ All demos completed!")
                print("=" * 70)

            else:
                print("❌ Invalid selection, please try again")

            input("\nPress Enter to continue...")

    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted, exiting")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
