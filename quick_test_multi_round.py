"""
Quick test for Multi-Round Dialogue functionality

Tests basic agent-tool interaction without full AgentBench setup.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents import ClaudeAgent
from adapters import ToolRegistry
from orchestration import MultiRoundExecutor


async def quick_test():
    """
    Quick test with 1 simple OS task

    This verifies:
    1. Agent can use tools
    2. Tool registry routes correctly
    3. Multi-round loop works
    4. FINAL_ANSWER detection works
    """
    print("\n" + "="*80)
    print("QUICK TEST: Multi-Round Dialogue")
    print("="*80 + "\n")

    # Initialize
    print("[1/3] Initializing agent and tools...")
    agent = ClaudeAgent()
    registry = ToolRegistry()

    print("[2/3] Starting Docker container...")
    await registry.initialize(docker_image="ubuntu:22.04")

    executor = MultiRoundExecutor(agent=agent, tool_registry=registry)

    # Test task
    print("\n[3/3] Testing multi-round execution...\n")
    print("Task: List files in /root and commit answer")
    print("-" * 80)

    result = await executor.execute_task(
        task_prompt=(
            "Use the execute_shell tool to list files in the /root directory "
            "(run command 'ls -la /root'). "
            "After you see the file listing, use commit_final_answer to submit "
            "your answer with the list of files you found."
        ),
        max_rounds=10,
        verbose=True
    )

    # Results
    print("\n" + "="*80)
    print("TEST RESULT")
    print("="*80)

    if result["success"]:
        print(f"✅ Test PASSED")
        print(f"   - Completed in {result['rounds']} rounds")
        print(f"   - Made {result['tool_calls_count']} tool calls")
        print(f"   - Final answer: {result['final_answer'][:150]}...")
    else:
        print(f"❌ Test FAILED")
        print(f"   - Stopped after {result['rounds']} rounds")
        print(f"   - Made {result['tool_calls_count']} tool calls")
        print(f"   - Status: {result['final_answer']}")

    print("="*80 + "\n")

    # Cleanup
    await registry.shutdown()

    return result["success"]


if __name__ == "__main__":
    try:
        print("\nStarting quick multi-round test...")
        print("This will test basic agent-tool interaction.\n")

        success = asyncio.run(quick_test())

        if success:
            print("✓ All systems working correctly!")
            print("\nYou can now run the full test:")
            print("  python3 test_multi_round.py --mode full\n")
        else:
            print("⚠ Test failed - check output above for details\n")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
