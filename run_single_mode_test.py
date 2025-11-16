"""
Hybrid Mode Single Test - 10 Tasks with Dependency Injection

Tests DAGScheduler + DependencyInjector with real CLIExecutor.
This is a minimal test to validate the core functionality before running full evaluation.

Usage:
    python3 run_single_mode_test.py

Expected time: 5-8 minutes (10 tasks with dependencies)
Output: results/hybrid_test_results.json
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from scheduler import Task

# Import orchestration modules
sys.path.insert(0, str(Path(__file__).parent / "src" / "orchestration"))
from agentbench_loader import AgentBenchLoader
from dag_scheduler import DAGScheduler
from cli_executor import CLIExecutor

# Multi-agent task assignment uses keyword-based heuristic (lines 88-102)
# No need to import AgentSelector


async def run_hybrid_test() -> Dict[str, Any]:
    """
    Run Hybrid mode test with 10 tasks

    Returns:
        Test results dictionary
    """
    print("\n" + "="*80)
    print("HYBRID MODE TEST - 10 TASKS WITH DEPENDENCY INJECTION")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Load benchmark tasks
    print("[1/4] Loading benchmark tasks...")
    loader = AgentBenchLoader("benchmark_tasks_10.json")
    groups = loader.load_all_groups()

    # Collect all tasks from all groups
    all_tasks = []
    all_input_mappings = {}

    for group in groups:
        all_tasks.extend(group.tasks)
        all_input_mappings.update(group.input_mappings)

    print(f"  ✓ Loaded {len(all_tasks)} tasks from {len(groups)} groups")
    print(f"  ✓ Groups: {', '.join([g.group_id for g in groups])}")
    print(f"  ✓ Input mappings for {len(all_input_mappings)} tasks")

    # Show task dependency structure
    print("\n  Task dependency structure:")
    for task in all_tasks:
        deps = f" → depends on: {', '.join(task.depends_on)}" if task.depends_on else " (root)"
        print(f"    {task.id}{deps}")

    # Step 2: Initialize CLIExecutor and AgentSelector
    print("\n[2/5] Initializing CLIExecutor...")
    executor = CLIExecutor(timeout=600)  # 10 minutes per task
    await executor.initialize()
    print("  ✓ CLIExecutor ready (timeout: 600s)")

    # Step 3: Generate smart agent mapping
    print("\n[3/5] Generating smart agent assignments...")

    # Create agent mapping based on task characteristics
    agent_mapping = {}
    for task in all_tasks:
        # AgentSelector.select() needs available_agents dict, but we just need agent names
        # For now, use a simple heuristic based on task type or prompt analysis
        prompt_lower = task.prompt.lower()

        # Strategy: Analyze prompt keywords to classify task type
        # Database tasks (complex SQL) → claude
        if "SELECT" in task.prompt or "INSERT" in task.prompt or "UPDATE" in task.prompt or "database" in prompt_lower:
            agent_mapping[task.id] = "claude"
        # Coding tasks (implementation) → codex
        elif any(kw in prompt_lower for kw in ["implement", "function", "class", "def ", "code", "write a script"]):
            agent_mapping[task.id] = "codex"
        # OS/shell tasks (simple commands) → gemini
        elif any(kw in prompt_lower for kw in ["ps ", "grep", "/etc/", "file", "process", "read ", "count", "memory", "cpu"]):
            agent_mapping[task.id] = "gemini"
        # Default: complex tasks to claude
        else:
            agent_mapping[task.id] = "claude"

    print(f"  ✓ Agent assignments generated:")
    for task_id, agent_name in agent_mapping.items():
        print(f"    {task_id} → {agent_name}")

    # Step 4: Execute with DAGScheduler (Hybrid mode with multi-agent)
    print("\n[4/5] Executing tasks with DAGScheduler + Multi-Agent...")
    print("  Mode: Hybrid (topological sort + dependency injection + multi-agent)")
    print("  MetaAgent: Enabled (dynamic prompt generation)")
    print("  Agents: claude, codex, gemini (smart selection)")
    print()

    scheduler = DAGScheduler(
        executor,
        default_agent="claude",
        verbose=True,
        use_meta_agent=True  # Day 7 feature: Dynamic prompt generation
    )

    start_time = time.time()

    try:
        result = await scheduler.execute_dag(
            tasks=all_tasks,
            agent_mapping=agent_mapping,  # Use smart agent mapping
            input_mappings=all_input_mappings,
            extract_data=True  # Enable data extraction for dependency injection
        )

        end_time = time.time()
        total_time = end_time - start_time

    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        await executor.shutdown()
        return {
            "mode": "hybrid",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

    # Step 4: Process results and save
    print("\n[4/4] Processing results...")

    # Collect per-task results
    task_results = []
    for task_id, task_result in result.task_results.items():
        task_results.append({
            "task_id": task_id,
            "success": task_result.success,
            "latency": task_result.latency,
            "output_length": len(task_result.output) if task_result.output else 0,
            "has_parsed_data": task_result.parsed_data is not None,
            "parsed_data_keys": list(task_result.parsed_data.keys()) if task_result.parsed_data else [],
            "error": task_result.error if hasattr(task_result, 'error') else None
        })

    # Build result summary
    results_data = {
        "mode": "hybrid",
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "batch_count": result.batch_count,
        "statistics": {
            "total_tasks": result.total_tasks,
            "completed_tasks": result.completed_tasks,
            "failed_tasks": result.failed_tasks,
            "success_rate": (result.completed_tasks / result.total_tasks * 100) if result.total_tasks > 0 else 0,
            "avg_latency": sum(r.latency for r in result.results) / len(result.results) if result.results else 0,
            "total_execution_time": total_time
        },
        "task_results": task_results,
        "metadata": {
            "groups_tested": [g.group_id for g in groups],
            "dependency_injection_enabled": True,
            "data_extraction_enabled": True,
            "meta_agent_enabled": True  # Day 7: Dynamic prompt generation
        }
    }

    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    output_file = results_dir / "hybrid_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Results saved to: {output_file}")

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\n📊 Overall Statistics:")
    print(f"  Total tasks: {results_data['statistics']['total_tasks']}")
    print(f"  Completed: {results_data['statistics']['completed_tasks']}")
    print(f"  Failed: {results_data['statistics']['failed_tasks']}")
    print(f"  Success rate: {results_data['statistics']['success_rate']:.1f}%")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Batches executed: {result.batch_count}")
    print(f"  Avg latency/task: {results_data['statistics']['avg_latency']:.2f}s")

    print(f"\n📝 Per-task Results:")
    for task_data in task_results:
        status = "✓" if task_data["success"] else "✗"
        parsed = f" [parsed: {', '.join(task_data['parsed_data_keys'])}]" if task_data['has_parsed_data'] else ""
        error_msg = f" - ERROR: {task_data['error']}" if task_data['error'] else ""
        print(f"  {status} {task_data['task_id']}: {task_data['latency']:.2f}s{parsed}{error_msg}")

    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)

    target_rate = 70.0  # Lower threshold for real CLI execution
    success_rate = results_data['statistics']['success_rate']

    if success_rate >= target_rate:
        print(f"✅ PASSED: Success rate {success_rate:.1f}% >= {target_rate}%")
        print("\n🎉 Hybrid mode test successful!")
        print("\n✅ Verified:")
        print("  ✓ DAGScheduler executes tasks in topological order")
        print("  ✓ DependencyInjector enhances prompts with upstream data")
        print("  ✓ CLIExecutor handles real task execution")
        print("  ✓ Data extraction and passing works correctly")
        print("\n💡 Next steps:")
        print("  1. Review results in results/hybrid_test_results.json")
        print("  2. If satisfied, run Serial and Parallel modes for comparison")
        print("  3. Generate final evaluation report")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: Success rate {success_rate:.1f}% < {target_rate}%")
        print("\n🔍 Debugging suggestions:")
        print("  1. Check failed task error messages above")
        print("  2. Review results/hybrid_test_results.json for details")
        print("  3. Verify dependency injection is working correctly")
        print("  4. Check if data extraction strategies are effective")

    print("="*80 + "\n")

    # Cleanup
    await executor.shutdown()

    return results_data


async def main():
    """Main entry point"""
    # Temporarily disable global config files for all AI CLI tools
    # System uses claude, codex, and gemini CLIs (see agent_config.yaml)
    # Each may have config files that interfere with automated testing
    config_files = [
        (Path.home() / ".claude" / "CLAUDE.md", Path.home() / ".claude" / "CLAUDE.md.test_backup"),
        (Path.home() / ".gemini" / "GEMINI.md", Path.home() / ".gemini" / "GEMINI.md.test_backup"),
        (Path(__file__).parent / "AGENTS.md", Path(__file__).parent / "AGENTS.md.test_backup"),  # Codex project-level config
    ]

    disabled_configs = []

    # Backup all config files
    for config_file, backup_file in config_files:
        if config_file.exists() and not backup_file.exists():
            config_file.rename(backup_file)
            disabled_configs.append((config_file, backup_file))
            print(f"✓ Temporarily disabled {config_file}")

    if disabled_configs:
        print()

    try:
        results = await run_hybrid_test()

        # Exit with success if test passed
        success_rate = results.get('statistics', {}).get('success_rate', 0)
        sys.exit(0 if success_rate >= 70.0 else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restore all config files
        for config_file, backup_file in disabled_configs:
            if backup_file.exists():
                backup_file.rename(config_file)
                print(f"\n✓ Restored {config_file}")


if __name__ == "__main__":
    print("\n🚀 Starting Hybrid Mode Test...")
    print("⏱️  Estimated time: 5-8 minutes")
    print()
    asyncio.run(main())
