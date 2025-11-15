"""
Test Multi-Round Dialogue Execution

Day 3 Validation: Test 5 simple tasks (3 OS + 2 DB) to achieve >80% success rate
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

from agents import ClaudeAgent
from adapters import ToolRegistry
from orchestration import MultiRoundExecutor


def get_api_key() -> str:
    """Get Anthropic API key from environment"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ ANTHROPIC_API_KEY not found!")
        print("Please set it:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("Or create a .env file with:")
        print("  ANTHROPIC_API_KEY=your-key-here\n")
        sys.exit(1)
    return api_key


# Test tasks
OS_TASKS = [
    {
        "id": "os_1",
        "prompt": "List all files in the /root directory. Use the execute_shell tool to run 'ls -la /root'. Then commit your final answer with the file listing.",
        "expected_tool": "execute_shell"
    },
    {
        "id": "os_2",
        "prompt": "Check if the file /etc/passwd exists. Use execute_shell to run 'test -f /etc/passwd && echo \"exists\" || echo \"not found\"'. Commit the result.",
        "expected_tool": "execute_shell"
    },
    {
        "id": "os_3",
        "prompt": "Find the current user. Use execute_shell to run 'whoami'. Commit the username.",
        "expected_tool": "execute_shell"
    }
]

DB_TASKS_MYSQL = [
    {
        "id": "db_1",
        "prompt": "Show all tables in the database. Use execute_sql to run 'SHOW TABLES;'. Then commit your final answer with the table list.",
        "expected_tool": "execute_sql"
    },
    {
        "id": "db_2",
        "prompt": "Count the number of users in the users table. Use execute_sql to run 'SELECT COUNT(*) as user_count FROM users;'. Commit the count.",
        "expected_tool": "execute_sql"
    }
]

DB_TASKS_SQLITE = [
    {
        "id": "db_1",
        "prompt": "Show all tables in the database. Use execute_sql to run 'SELECT name FROM sqlite_master WHERE type=\"table\";'. Then commit your final answer with the table list.",
        "expected_tool": "execute_sql"
    },
    {
        "id": "db_2",
        "prompt": "Count the number of users in the users table. Use execute_sql to run 'SELECT COUNT(*) as user_count FROM users;'. Commit the count.",
        "expected_tool": "execute_sql"
    }
]


async def setup_test_database(db_executor):
    """Create test database with sample data"""
    print("  - Creating test table and sample data...")

    # Create users table
    await db_executor.execute_sql("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT
        )
    """)

    # Insert sample data
    await db_executor.execute_sql("""
        INSERT OR REPLACE INTO users (id, name, age, email) VALUES
        (1, 'Alice', 25, 'alice@example.com'),
        (2, 'Bob', 30, 'bob@example.com'),
        (3, 'Charlie', 22, 'charlie@example.com'),
        (4, 'David', 35, 'david@example.com'),
        (5, 'Eve', 28, 'eve@example.com')
    """)

    print("  - Test database ready (5 users)")


async def test_multi_round_execution(db_type="sqlite"):
    """
    Test multi-round dialogue with 5 simple tasks

    Args:
        db_type: "sqlite" or "mysql" (default: sqlite for easier testing)

    Success criteria:
    - All tasks should complete
    - Success rate > 80% (at least 4/5 tasks)
    - Average rounds < 5
    """
    print("\n" + "="*80)
    print("DAY 3 VALIDATION: Multi-Round Dialogue Execution")
    print("="*80)

    # Initialize components
    print("\n[1/4] Initializing Claude agent...")
    api_key = get_api_key()
    agent = ClaudeAgent(api_key=api_key)

    print("[2/4] Initializing tool registry...")
    registry = ToolRegistry()

    # Initialize executors
    print("  - Starting Docker container (ubuntu:22.04)...")

    if db_type == "sqlite":
        print("  - Using SQLite database (test_agentbench.db)...")
        await registry.initialize(
            docker_image="ubuntu:22.04",
            db_type="sqlite",
            database="test_agentbench.db"
        )

        # Setup test database
        await setup_test_database(registry.database_executor)
        db_tasks = DB_TASKS_SQLITE

    else:
        print("  - Using MySQL database...")
        await registry.initialize(
            docker_image="ubuntu:22.04",
            db_type="mysql",
            host="localhost",
            user="root",
            password="",  # Update with your MySQL password
            database="test"  # Update with your database name
        )
        db_tasks = DB_TASKS_MYSQL

    print("[3/4] Creating multi-round executor...")
    executor = MultiRoundExecutor(agent=agent, tool_registry=registry)

    # Combine all tasks
    all_tasks = OS_TASKS + db_tasks
    print(f"\n[4/4] Executing {len(all_tasks)} tasks (3 OS + 2 DB)...\n")

    # Execute tasks
    results = []

    for i, task_spec in enumerate(all_tasks, 1):
        task_id = task_spec["id"]
        prompt = task_spec["prompt"]

        print(f"\n{'─'*80}")
        print(f"TASK {i}/{len(all_tasks)}: {task_id}")
        print(f"{'─'*80}")
        print(f"Prompt: {prompt[:100]}...")

        try:
            result = await executor.execute_task(
                task_prompt=prompt,
                max_rounds=10,
                verbose=True
            )

            results.append({
                "task_id": task_id,
                "task_type": task_spec.get("expected_tool", "unknown"),
                **result
            })

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            results.append({
                "task_id": task_id,
                "task_type": task_spec.get("expected_tool", "unknown"),
                "final_answer": f"Error: {str(e)}",
                "rounds": 0,
                "success": False,
                "tool_calls_count": 0
            })

    # Calculate statistics
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    stats = executor.get_statistics(results)

    print(f"\nOverall Performance:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Successful: {stats['successful_tasks']}")
    print(f"  Failed: {stats['failed_tasks']}")
    print(f"  Success rate: {stats['success_rate']*100:.1f}%")
    print(f"  Avg rounds: {stats['avg_rounds']:.2f}")
    print(f"  Avg tool calls: {stats['avg_tool_calls']:.2f}")

    # Per-task breakdown
    print(f"\nPer-Task Results:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['task_id']}: {r['rounds']} rounds, "
              f"{r['tool_calls_count']} tool calls")
        if not r["success"]:
            print(f"    Answer: {r['final_answer'][:100]}")

    # OS vs DB performance
    os_results = [r for r in results if r["task_type"] == "execute_shell"]
    db_results = [r for r in results if r["task_type"] == "execute_sql"]

    if os_results:
        os_success = sum(1 for r in os_results if r["success"]) / len(os_results)
        print(f"\nOS Tasks Performance:")
        print(f"  Success rate: {os_success*100:.1f}% ({sum(1 for r in os_results if r['success'])}/{len(os_results)})")

    if db_results:
        db_success = sum(1 for r in db_results if r["success"]) / len(db_results)
        print(f"\nDB Tasks Performance:")
        print(f"  Success rate: {db_success*100:.1f}% ({sum(1 for r in db_results if r['success'])}/{len(db_results)})")

    # Check success criteria
    print("\n" + "="*80)
    print("VALIDATION CRITERIA")
    print("="*80)

    criteria_met = []

    # Criterion 1: Success rate > 80%
    success_rate_ok = stats['success_rate'] >= 0.8
    criteria_met.append(success_rate_ok)
    print(f"  {'✓' if success_rate_ok else '✗'} Success rate > 80%: "
          f"{stats['success_rate']*100:.1f}%")

    # Criterion 2: Average rounds < 5
    avg_rounds_ok = stats['avg_rounds'] < 5
    criteria_met.append(avg_rounds_ok)
    print(f"  {'✓' if avg_rounds_ok else '✗'} Avg rounds < 5: "
          f"{stats['avg_rounds']:.2f}")

    # Criterion 3: No max rounds hit
    max_rounds_ok = stats['max_rounds_hit'] == 0
    criteria_met.append(max_rounds_ok)
    print(f"  {'✓' if max_rounds_ok else '✗'} No tasks hit max rounds: "
          f"{stats['max_rounds_hit']} tasks")

    # Overall verdict
    print("\n" + "="*80)
    if all(criteria_met):
        print("✅ DAY 3 VALIDATION: PASSED")
        print("Multi-round dialogue execution is working correctly!")
    else:
        print("⚠️  DAY 3 VALIDATION: NEEDS ATTENTION")
        print("Some criteria not met - review failed tasks above")
    print("="*80 + "\n")

    # Cleanup
    print("Cleaning up...")
    await registry.shutdown()

    return stats['success_rate'] >= 0.8


async def test_simple_example():
    """
    Simple standalone test for basic functionality
    """
    print("\n" + "="*80)
    print("SIMPLE TEST: Basic Multi-Round Execution")
    print("="*80)

    # Initialize
    api_key = get_api_key()
    agent = ClaudeAgent(api_key=api_key)
    registry = ToolRegistry()

    await registry.initialize(docker_image="ubuntu:22.04")

    executor = MultiRoundExecutor(agent=agent, tool_registry=registry)

    # Simple task
    result = await executor.execute_task(
        task_prompt="Use execute_shell to list files in /root directory (ls /root), then commit your answer.",
        max_rounds=5,
        verbose=True
    )

    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Rounds: {result['rounds']}")
    print(f"  Answer: {result['final_answer'][:200]}")

    await registry.shutdown()

    return result['success']


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test multi-round dialogue execution")
    parser.add_argument(
        "--mode",
        choices=["simple", "full"],
        default="full",
        help="Test mode (simple: 1 task, full: 5 tasks)"
    )
    parser.add_argument(
        "--db",
        choices=["sqlite", "mysql"],
        default="sqlite",
        help="Database type (default: sqlite)"
    )

    args = parser.parse_args()

    try:
        if args.mode == "simple":
            success = asyncio.run(test_simple_example())
        else:
            success = asyncio.run(test_multi_round_execution(db_type=args.db))

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
