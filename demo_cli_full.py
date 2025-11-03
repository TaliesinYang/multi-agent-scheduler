#!/usr/bin/env python3
"""
Complete CLI Demonstration - 100% Real Execution

Demonstrates full workflow using CLI clients only:
1. Claude CLI automatically decomposes tasks (Meta-Agent)
2. Claude/Codex/Gemini CLI execute tasks in parallel
3. Intelligent scheduling with dependency resolution
4. Real-time performance statistics

No API keys required - only CLI tool subscriptions.

Usage:
    python demo_cli_full.py

Requirements:
    - Claude CLI: npm install -g @anthropic-ai/claude-code && claude auth login
    - Codex CLI: codex auth login (optional)
    - Gemini CLI: gemini auth login (optional)

Cost Comparison:
    - API Mode: ~$30-50/month (pay-per-token)
    - CLI Mode: ~$10/month (subscription) = 67% savings
"""

import asyncio
import time
import argparse
from typing import Dict
from datetime import datetime
from pathlib import Path
from meta_agent import MetaAgentCLI
from scheduler import MultiAgentScheduler, ExecutionMode
from agents import ClaudeCLIAgent, CodexExecAgent, GeminiAgent
from logger import ExecutionLogger
from workspace_manager import WorkspaceManager


# ============================================================================
# Preset Demo Tasks
# ============================================================================

DEMO_TASKS = [
    {
        "name": "Web Application Development",
        "description": "Build a task management web application with REST API"
    },
    {
        "name": "Data Analysis Pipeline",
        "description": "Create a data processing pipeline with visualization dashboard"
    },
    {
        "name": "Microservices Architecture",
        "description": "Design and implement a microservices-based e-commerce system"
    }
]


# ============================================================================
# Main Demo Function
# ============================================================================

async def run_cli_demo(workspace_path: str):
    """
    Run complete CLI demonstration

    Args:
        workspace_path: Path to workspace directory for agents to work in

    Workflow:
    1. Initialize CLI agents with workspace (no API keys needed)
    2. Get user input or use preset
    3. Decompose task using Claude CLI (Meta-Agent)
    4. Execute tasks in workspace using CLI scheduler
    5. Display results and statistics
    """
    print("=" * 70)
    print(" 🔥 Multi-Agent Scheduler - 100% CLI Mode")
    print("=" * 70)
    print()
    print("✅ Features:")
    print("   • Task decomposition via Claude CLI (no API key)")
    print("   • Parallel execution with multiple CLI agents ")
    print("   • Intelligent dependency resolution")
    print("   • Cost-effective subscription model (67% savings)")
    print()
    print(f"📁 Workspace: {workspace_path}")
    print()

    # ========================================================================
    # Step 1: Initialize CLI Agents with Workspace
    # ========================================================================
    print("🔧 Step 1: Initializing CLI agents...")
    print()

    agents = {}

    # Try to add Claude CLI with workspace
    try:
        agents['claude'] = ClaudeCLIAgent(workspace=workspace_path)
        print("✓ Claude CLI agent ready")
    except Exception as e:
        print(f"⚠️  Claude CLI not available: {e}")

    # Try to add Codex CLI with workspace (using CodexExecAgent for correct command format)
    try:
        agents['codex'] = CodexExecAgent(workspace=workspace_path)
        print("✓ Codex CLI agent ready")
    except Exception as e:
        print(f"⚠️  Codex CLI not available: {e}")

    # Try to add Gemini CLI with workspace
    try:
        agents['gemini'] = GeminiAgent(workspace=workspace_path)
        print("✓ Gemini CLI agent ready")
    except Exception as e:
        print(f"⚠️  Gemini CLI not available: {e}")

    if not agents:
        print()
        print("❌ No CLI agents available!")
        print()
        print("📝 Setup Instructions:")
        print("   1. Install CLI tools:")
        print("      npm install -g @anthropic-ai/claude-code")
        print("      # codex and gemini are optional")
        print()
        print("   2. Authenticate:")
        print("      claude auth login")
        print()
        return

    print(f"\n✅ {len(agents)} CLI agent(s) initialized: {', '.join(agents.keys())}")
    print()

    # ========================================================================
    # Step 2: Initialize Meta-Agent (CLI version) and Logger
    # ========================================================================
    print("🧠 Step 2: Initializing Meta-Agent (CLI version) and Logger...")
    meta = MetaAgentCLI()
    print("✓ Meta-Agent ready (uses Claude CLI for task decomposition)")

    # Initialize execution logger with workspace path
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = ExecutionLogger(session_id, workspace_path=workspace_path)
    print()

    # ========================================================================
    # Step 3: Get User Input
    # ========================================================================
    print("💬 Step 3: Task Input")
    print()
    print("Preset tasks:")
    for i, task in enumerate(DEMO_TASKS, 1):
        print(f"   {i}. {task['name']}")
    print(f"   {len(DEMO_TASKS) + 1}. Custom input")
    print()

    choice = input(f"Select task (1-{len(DEMO_TASKS) + 1}) or press Enter for #1: ").strip()

    if not choice:
        choice = "1"

    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(DEMO_TASKS):
            user_input = DEMO_TASKS[choice_idx]['description']
            print(f"\n✓ Selected: {DEMO_TASKS[choice_idx]['name']}")
        else:
            user_input = input("\n💬 Enter your task: ").strip()
            if not user_input:
                user_input = DEMO_TASKS[0]['description']
                print(f"✓ Using default: {DEMO_TASKS[0]['name']}")
    except ValueError:
        user_input = DEMO_TASKS[0]['description']
        print(f"✓ Using default: {DEMO_TASKS[0]['name']}")

    print()
    print(f"📋 Task: {user_input}")
    print()

    # ========================================================================
    # Step 4: Decompose Task (via CLI)
    # ========================================================================
    print("🔄 Step 4: Decomposing task via Claude CLI...")
    print()

    # Set user task in logger
    logger.set_user_task(user_input)

    start_time = time.time()
    tasks = await meta.decompose_task(user_input)
    decompose_time = time.time() - start_time

    # Log decomposition results
    logger.log_decomposition(len(tasks), decompose_time)

    print()
    print(f"✓ Task decomposition completed in {decompose_time:.2f}s")
    meta.print_task_tree(tasks)

    # ========================================================================
    # Step 5: Execute Tasks (via CLI)
    # ========================================================================
    print("⚡ Step 5: Executing tasks via CLI scheduler...")
    print()

    scheduler = MultiAgentScheduler(agents, logger=logger)
    result = await scheduler.schedule(tasks, mode=ExecutionMode.AUTO)

    # ========================================================================
    # Step 6: Display Results
    # ========================================================================
    print()
    print("=" * 70)
    print(" 📊 Execution Results")
    print("=" * 70)
    print()

    # Success rate
    successful = sum(1 for r in result.results if r.get('success', False))
    total = len(result.results)
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"✅ Success Rate: {successful}/{total} ({success_rate:.0f}%)")
    print(f"⏱️  Total Time: {result.total_time:.2f}s")
    print(f"⏱️  Decomposition Time: {decompose_time:.2f}s")

    # Performance gain (if available)
    if hasattr(result, 'performance_gain') and result.performance_gain is not None:
        print(f"🚀 Performance Gain: {result.performance_gain:.1f}%")

    print()

    # Task details
    print("📋 Task Results:")
    for i, (task, task_result) in enumerate(zip(tasks, result.results), 1):
        status = "✅" if task_result.get('success') else "❌"
        agent_used = task_result.get('agent', 'unknown')
        latency = task_result.get('latency', 0)
        print(f"   {status} {task.id}: {task.prompt[:50]}...")
        print(f"      Agent: {agent_used} | Time: {latency:.2f}s")

    print()

    # Agent distribution statistics
    print("📊 Agent Distribution:")
    agent_stats = {}
    agent_times = {}
    for r in result.results:
        agent = r.get('agent', 'unknown')
        latency = r.get('latency', 0)
        agent_stats[agent] = agent_stats.get(agent, 0) + 1
        agent_times[agent] = agent_times.get(agent, 0) + latency

    for agent in sorted(agent_stats.keys()):
        count = agent_stats[agent]
        percentage = (count / total * 100) if total > 0 else 0
        avg_time = agent_times[agent] / count if count > 0 else 0
        bar = "█" * int(percentage / 5)  # Scale to 20 chars max
        print(f"   {agent:12s}: {bar:20s} {count:2d} tasks ({percentage:4.1f}%) | Avg: {avg_time:.1f}s")

    # Get selector stats if available
    if hasattr(scheduler, 'agent_selector'):
        selector_stats = scheduler.agent_selector.get_selection_stats()
        print(f"\n💡 Selection Strategy: Smart (config-driven)")
    else:
        print(f"\n💡 Selection Strategy: Legacy")

    print()
    print("=" * 70)
    print("✅ Demo completed!")
    print()
    print("💡 Key Takeaways:")
    print("   • 100% CLI-based execution (no API keys)")
    print("   • Automatic task decomposition and scheduling")
    print("   • Intelligent agent selection based on task characteristics")
    print("   • Parallel execution with dependency resolution")
    print(f"   • Cost-effective: ~$10/month vs ~$30-50/month (API)")
    print()

    # ========================================================================
    # Step 7: Finalize and Save Execution Log
    # ========================================================================
    logger.finalize(result.total_time, successful, total)
    logger.save_to_file()
    print(f"💾 Log file available for analysis: {logger.get_log_path()}")
    print(f"   Use: python logger.py {logger.get_log_path()}")
    print()


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """
    Main entry point with argument parsing

    CLI Arguments:
        --workspace, -w : Workspace name or absolute path (default: auto-generated)
        --continue, -c  : Continue from existing workspace

    Examples:
        # Auto-create workspace with timestamp
        python demo_cli_full.py

        # Use named workspace
        python demo_cli_full.py --workspace my-web-app

        # Use absolute path
        python demo_cli_full.py --workspace /path/to/project

        # Continue from existing workspace
        python demo_cli_full.py --workspace my-web-app --continue
    """
    parser = argparse.ArgumentParser(
        description="Multi-Agent Scheduler - 100% CLI Mode with Workspace Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-create workspace with timestamp
  python demo_cli_full.py

  # Use named workspace
  python demo_cli_full.py --workspace my-web-app

  # Use absolute path
  python demo_cli_full.py --workspace /path/to/project

  # Continue from existing workspace
  python demo_cli_full.py --workspace my-web-app --continue
"""
    )

    parser.add_argument(
        '--workspace', '-w',
        type=str,
        default=None,
        help='Workspace name or absolute path (default: auto-generated with timestamp)'
    )

    parser.add_argument(
        '--continue', '-c',
        action='store_true',
        dest='continue_mode',
        help='Continue from existing workspace (load previous state)'
    )

    args = parser.parse_args()

    # Initialize workspace manager
    workspace_mgr = WorkspaceManager()

    # Create or get workspace path
    if args.workspace:
        if Path(args.workspace).is_absolute():
            # Use absolute path directly
            workspace_path = workspace_mgr.get_workspace_path(args.workspace)
        else:
            # Use relative name (create in workspaces/ directory)
            if args.continue_mode:
                # Use existing workspace
                workspace_path = workspace_mgr.get_workspace_path(args.workspace, create_if_missing=False)
                if not workspace_path.exists():
                    print(f"❌ Workspace '{args.workspace}' does not exist!")
                    print(f"   Available workspaces: {', '.join(workspace_mgr.list_workspaces())}")
                    return
            else:
                # Create new workspace (without timestamp if name specified)
                workspace_path = workspace_mgr.create_workspace(args.workspace, use_timestamp=False)
    else:
        # Auto-generate workspace with timestamp
        workspace_path = workspace_mgr.create_workspace()

    # Run demo with workspace
    try:
        asyncio.run(run_cli_demo(str(workspace_path)))
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
