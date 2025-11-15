"""
CLI-based AgentBench Task Execution Test

Uses Claude CLI with local Bash tools instead of Docker/API.
No API key required.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from adapters.cli_tool_executor import CLIToolExecutor


# Test tasks (simplified for CLI mode)
CLI_TEST_TASKS = [
    {
        "id": "cli_os_1",
        "prompt": """Task: List all files in the current directory with details.

Use the command 'ls -la' to list files.
After running the command, provide a summary of what files you found.
When done, say "FINAL_ANSWER: " followed by your summary.""",
        "type": "shell"
    },
    {
        "id": "cli_os_2",
        "prompt": """Task: Check if the file 'README.md' exists in the current directory.

Use the command 'test -f README.md && echo "exists" || echo "not found"' to check.
When done, say "FINAL_ANSWER: " followed by whether the file exists or not.""",
        "type": "shell"
    },
    {
        "id": "cli_os_3",
        "prompt": """Task: Find the current working directory.

Use the command 'pwd' to print working directory.
When done, say "FINAL_ANSWER: " followed by the directory path.""",
        "type": "shell"
    },
    {
        "id": "cli_db_1",
        "prompt": """Task: Query the SQLite database to list all tables.

Use the command: sqlite3 agentbench_cli.db "SELECT name FROM sqlite_master WHERE type='table';"
After running the command, provide a list of tables found.
When done, say "FINAL_ANSWER: " followed by the table names.""",
        "type": "database"
    },
    {
        "id": "cli_db_2",
        "prompt": """Task: Count the number of users in the users table.

Use the command: sqlite3 agentbench_cli.db "SELECT COUNT(*) as user_count FROM users;"
When done, say "FINAL_ANSWER: " followed by the count.""",
        "type": "database"
    }
]


async def execute_cli_task(task: dict, executor: CLIToolExecutor) -> dict:
    """
    Execute a single task using Claude CLI

    Args:
        task: Task specification
        executor: CLI tool executor (for DB setup)

    Returns:
        Result dict with success status
    """
    print(f"\n{'─'*80}")
    print(f"Task: {task['id']}")
    print(f"{'─'*80}")
    print(f"Prompt: {task['prompt'][:100]}...")

    # Build CLI command
    cmd = [
        "claude",
        "-p",  # Print mode
        "--tools", "Bash",  # Enable Bash tool
        "--dangerously-skip-permissions",  # Skip permission prompts
        task["prompt"]
    ]

    try:
        # Execute via CLI
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60.0
        )

        output = stdout.decode('utf-8', errors='replace')

        # Check for FINAL_ANSWER
        success = "FINAL_ANSWER:" in output

        if success:
            # Extract answer
            answer_part = output.split("FINAL_ANSWER:", 1)[1]
            final_answer = answer_part.strip().split('\n')[0][:200]
        else:
            final_answer = "No final answer provided"

        print(f"\n✓ Task completed")
        print(f"  Final answer: {final_answer}")

        return {
            "task_id": task["id"],
            "success": success,
            "final_answer": final_answer,
            "full_output": output
        }

    except asyncio.TimeoutError:
        print(f"\n✗ Task timeout")
        return {
            "task_id": task["id"],
            "success": False,
            "final_answer": "Timeout after 60s",
            "full_output": ""
        }

    except Exception as e:
        print(f"\n✗ Task error: {e}")
        return {
            "task_id": task["id"],
            "success": False,
            "final_answer": f"Error: {str(e)}",
            "full_output": ""
        }


async def main():
    """Run CLI AgentBench test"""
    print("\n" + "="*80)
    print("CLI-BASED AGENTBENCH TEST")
    print("="*80)
    print("\nUsing Claude CLI with local Bash tools")
    print("No API key required\n")

    # Setup database
    print("[1/3] Setting up test database...")
    executor = CLIToolExecutor()
    await executor.initialize()

    # Run tasks
    print(f"\n[2/3] Executing {len(CLI_TEST_TASKS)} tasks...")
    results = []

    for i, task in enumerate(CLI_TEST_TASKS, 1):
        print(f"\n[Task {i}/{len(CLI_TEST_TASKS)}]")
        result = await execute_cli_task(task, executor)
        results.append(result)

        # Small delay between tasks
        await asyncio.sleep(1)

    # Calculate statistics
    print("\n[3/3] Calculating results...")
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    success_rate = (successful / total) * 100 if total > 0 else 0

    # Print summary
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"\nTotal tasks: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {success_rate:.1f}%")

    print("\nPer-task results:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['task_id']}: {r['final_answer'][:60]}...")

    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)

    target_rate = 80.0
    if success_rate >= target_rate:
        print(f"✅ PASSED: Success rate {success_rate:.1f}% >= {target_rate}%")
        print("\nCLI-based AgentBench execution is working!")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: Success rate {success_rate:.1f}% < {target_rate}%")
        print("\nSome tasks failed - review output above")

    print("="*80 + "\n")

    # Cleanup
    await executor.close()

    return success_rate >= target_rate


if __name__ == "__main__":
    try:
        print("\n🚀 Starting CLI AgentBench test...\n")
        success = asyncio.run(main())
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
