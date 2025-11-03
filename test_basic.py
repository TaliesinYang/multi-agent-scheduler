"""
Basic Test - Core System Functionality Test Suite
Verify that core system functionality works properly
"""

import asyncio
from agents import MockAgent
from scheduler import MultiAgentScheduler, Task, ExecutionMode


async def test_mock_agents():
    """Test Mock Agents"""
    print("=" * 60)
    print("Test 1: Mock Agent Basic Functionality")
    print("=" * 60)

    agent = MockAgent(name="TestAgent", delay=0.5)

    result = await agent.call("Test prompt")

    assert result['success'] == True
    assert result['agent'] == "TestAgent"
    assert 'result' in result
    assert 'latency' in result

    print("✓ Mock agent test passed")
    print(f"  - Result: {result['result'][:50]}")
    print(f"  - Latency: {result['latency']:.2f} seconds")


async def test_parallel_execution():
    """Test Parallel Execution"""
    print("\n" + "=" * 60)
    print("Test 2: Parallel Execution")
    print("=" * 60)

    agents = {
        'agent1': MockAgent(name="Agent1", delay=1.0),
        'agent2': MockAgent(name="Agent2", delay=1.0),
        'agent3': MockAgent(name="Agent3", delay=1.0)
    }

    scheduler = MultiAgentScheduler(agents)

    tasks = [
        Task(id="task1", prompt="Task 1", task_type="general"),
        Task(id="task2", prompt="Task 2", task_type="general"),
        Task(id="task3", prompt="Task 3", task_type="general")
    ]

    result = await scheduler.execute_parallel(tasks)

    # Verify parallel execution (3 tasks of 1 second each should complete in ~1 second, not 3 seconds)
    assert result.total_time < 2.0, f"Parallel execution should be <2 seconds, actual: {result.total_time:.2f} seconds"
    assert result.task_count == 3
    assert len(result.results) == 3

    print(f"✓ Parallel execution test passed")
    print(f"  - 3 tasks completed in: {result.total_time:.2f} seconds (expected ~1 second)")


async def test_serial_execution():
    """Test Serial Execution"""
    print("\n" + "=" * 60)
    print("Test 3: Serial Execution")
    print("=" * 60)

    agents = {
        'agent1': MockAgent(name="Agent1", delay=0.5)
    }

    scheduler = MultiAgentScheduler(agents)

    tasks = [
        Task(id="task1", prompt="Task 1", task_type="general"),
        Task(id="task2", prompt="Task 2", task_type="general"),
        Task(id="task3", prompt="Task 3", task_type="general")
    ]

    result = await scheduler.execute_serial(tasks)

    # Verify serial execution (3 tasks of 0.5 seconds each should take ~1.5 seconds)
    assert result.total_time >= 1.3, f"Serial execution should be >=1.3 seconds, actual: {result.total_time:.2f} seconds"
    assert result.task_count == 3
    assert len(result.results) == 3

    print(f"✓ Serial execution test passed")
    print(f"  - 3 tasks completed in: {result.total_time:.2f} seconds (expected ~1.5 seconds)")


async def test_dependency_scheduling():
    """Test Dependency-based Scheduling"""
    print("\n" + "=" * 60)
    print("Test 4: Dependency-based Scheduling")
    print("=" * 60)

    agents = {
        'agent1': MockAgent(name="Agent1", delay=0.3)
    }

    scheduler = MultiAgentScheduler(agents)

    tasks = [
        Task(id="task1", prompt="Task 1", task_type="general"),
        Task(id="task2", prompt="Task 2", task_type="general"),
        Task(id="task3", prompt="Task 3", depends_on=["task1", "task2"]),
        Task(id="task4", prompt="Task 4", depends_on=["task3"])
    ]

    result = await scheduler.execute_with_dependencies(tasks)

    # Verify correct batching
    assert result.task_count == 4
    assert len(result.results) == 4

    print(f"✓ Dependency-based scheduling test passed")
    print(f"  - 4 tasks completed in batches")


async def test_performance_comparison():
    """Test Performance Comparison"""
    print("\n" + "=" * 60)
    print("Test 5: Performance Comparison")
    print("=" * 60)

    agents = {
        'agent1': MockAgent(name="Agent1", delay=0.8)
    }

    scheduler = MultiAgentScheduler(agents)

    tasks = [
        Task(id=f"task{i}", prompt=f"Task {i}", task_type="general")
        for i in range(4)
    ]

    comparison = await scheduler.compare_performance(tasks)

    # Verify performance improvement
    assert comparison['performance_gain_percent'] > 30, "Parallel execution should have >30% performance gain"
    assert comparison['time_saved'] > 0

    print(f"✓ Performance comparison test passed")
    print(f"  - Serial: {comparison['serial_time']:.2f} seconds")
    print(f"  - Parallel: {comparison['parallel_time']:.2f} seconds")
    print(f"  - Performance gain: {comparison['performance_gain_percent']:.1f}%")


async def test_agent_selection():
    """Test Intelligent Agent Selection"""
    print("\n" + "=" * 60)
    print("Test 6: Intelligent Agent Selection")
    print("=" * 60)

    agents = {
        'claude': MockAgent(name="Claude", delay=0.5),
        'openai': MockAgent(name="OpenAI", delay=0.5),
        'gemini': MockAgent(name="Gemini", delay=0.5)
    }

    scheduler = MultiAgentScheduler(agents)

    # Test agent selection for different task types
    tasks = [
        Task(id="coding_task", prompt="Write code", task_type="coding"),
        Task(id="simple_task", prompt="Simple task", task_type="simple"),
        Task(id="analysis_task", prompt="Analyze", task_type="analysis")
    ]

    result = await scheduler.schedule(tasks, mode=ExecutionMode.PARALLEL)

    # Verify agent selection strategy
    agent_map = {r['task_id']: r['agent_selected'] for r in result.results}

    assert agent_map['coding_task'] == 'claude', "Coding task should select Claude"
    assert agent_map['simple_task'] == 'gemini', "Simple task should select Gemini"
    assert agent_map['analysis_task'] == 'openai', "Analysis task should select OpenAI"

    print(f"✓ Intelligent agent selection test passed")
    print(f"  - coding → {agent_map['coding_task']}")
    print(f"  - simple → {agent_map['simple_task']}")
    print(f"  - analysis → {agent_map['analysis_task']}")


async def run_all_tests():
    """Run All Tests"""
    print("\n" + "🚀" * 30)
    print("  Multi-Agent Scheduler - Basic Test Suite")
    print("🚀" * 30)

    try:
        await test_mock_agents()
        await test_parallel_execution()
        await test_serial_execution()
        await test_dependency_scheduling()
        await test_performance_comparison()
        await test_agent_selection()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nCore system functionality is working properly. Ready for demo.")
        print("Run 'python demo.py' to start the demonstration.")

        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
