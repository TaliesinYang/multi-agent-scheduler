#!/usr/bin/env python3
"""
Multi-Agent CLI Client - Reusable Tool for Task Execution

This module provides a reusable CLI client for multi-agent task execution.
It can be used both as:
1. A library (imported by test scripts)
2. A command-line tool (standalone execution)

Features:
    - Automatic task decomposition via Meta-Agent
    - Parallel execution with dependency resolution
    - Workspace management
    - Structured result output for testing/benchmarking

Usage as library:
    ```python
    from multi_agent_cli import MultiAgentCLI

    cli = MultiAgentCLI(agents=['claude', 'gemini'])
    result = await cli.decompose_and_execute("Build a REST API")
    print(f"Success rate: {result.success_rate}")
    ```

Usage as CLI tool:
    ```bash
    # Interactive mode
    python multi_agent_cli.py

    # With parameters
    python multi_agent_cli.py --task "Build a web app" --agents claude,gemini
    ```

Author: Multi-Agent Scheduler Team
License: MIT
"""

import asyncio
import time
import json
import argparse
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from src.meta_agent import MetaAgentCLI
from src.scheduler import MultiAgentScheduler, ExecutionMode, ExecutionResult, Task
from src.agents import ClaudeCLIAgent, CodexExecAgent, GeminiAgent
from src.logger import ExecutionLogger
from src.workspace_manager import WorkspaceManager
from src.task_visualizer import TaskVisualizer


# ============================================================================
# Result Data Structure
# ============================================================================

@dataclass
class CLIExecutionResult:
    """
    Structured execution result for CLI operations

    This dataclass provides a clean interface for accessing execution results,
    designed specifically for testing and benchmarking purposes.

    Attributes:
        tasks: List of decomposed tasks
        execution_result: Raw execution result from scheduler
        decompose_time: Time spent on task decomposition (seconds)
        total_time: Total execution time including decomposition (seconds)
        success_rate: Ratio of successful tasks (0.0 to 1.0)
        workspace_path: Path to workspace directory
    """
    tasks: List[Task]
    execution_result: ExecutionResult
    decompose_time: float
    total_time: float
    success_rate: float
    workspace_path: Optional[str] = None

    @property
    def task_count(self) -> int:
        """Number of decomposed tasks"""
        return len(self.tasks)

    @property
    def execution_time(self) -> float:
        """Execution time (excluding decomposition)"""
        return self.execution_result.total_time

    @property
    def speedup(self) -> Optional[float]:
        """
        Speedup ratio if available

        Returns None if serial comparison wasn't performed
        """
        if hasattr(self.execution_result, 'speedup'):
            return self.execution_result.speedup
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization

        Returns:
            Dictionary with all relevant metrics
        """
        return {
            'task_count': self.task_count,
            'decompose_time': self.decompose_time,
            'execution_time': self.execution_time,
            'total_time': self.total_time,
            'success_rate': self.success_rate,
            'speedup': self.speedup,
            'workspace_path': self.workspace_path,
            'tasks': [
                {
                    'id': t.id,
                    'prompt': t.prompt,
                    'task_type': t.task_type,
                    'depends_on': t.depends_on
                }
                for t in self.tasks
            ],
            'results': [
                {
                    'task_id': r.get('task_id'),
                    'success': r.get('success'),
                    'latency': r.get('latency'),
                    'agent': r.get('agent')
                }
                for r in self.execution_result.results
            ]
        }


# ============================================================================
# Multi-Agent CLI Client
# ============================================================================

class MultiAgentCLI:
    """
    Multi-Agent CLI Client for task decomposition and execution

    This class provides a high-level interface for multi-agent task execution,
    combining Meta-Agent decomposition with intelligent scheduling.

    Example:
        ```python
        # Initialize with default agents (auto-detect)
        cli = MultiAgentCLI()

        # Execute a task
        result = await cli.decompose_and_execute("Build a web application")

        # Access results
        print(f"Tasks: {result.task_count}")
        print(f"Time: {result.total_time:.2f}s")
        print(f"Success: {result.success_rate * 100:.1f}%")
        ```
    """

    def __init__(
        self,
        agents: Optional[List[str]] = None,
        workspace: Optional[str] = None,
        logger: Optional[ExecutionLogger] = None,
        quiet: bool = False
    ):
        """
        Initialize Multi-Agent CLI client

        Args:
            agents: List of agent names to use ['claude', 'gemini', 'codex']
                   If None, auto-detects available agents
            workspace: Workspace directory path
                      If None, creates temporary workspace
            logger: Execution logger instance
                   If None, creates default logger
            quiet: Suppress output messages
        """
        self.quiet = quiet
        self.workspace_manager = WorkspaceManager()

        # Initialize workspace
        if workspace:
            self.workspace_path = Path(workspace)
        else:
            # Auto-create workspace with timestamp
            self.workspace_path = self.workspace_manager.create_workspace()

        # Initialize agents
        self.agents = self._initialize_agents(agents, str(self.workspace_path))

        # Initialize Meta-Agent (CLI-based)
        self.meta_agent = MetaAgentCLI()

        # Initialize logger
        if logger:
            self.logger = logger
        else:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.logger = ExecutionLogger(session_id, workspace_path=str(self.workspace_path))

        # Initialize scheduler
        self.scheduler = MultiAgentScheduler(self.agents, logger=self.logger)

        # Task visualizer (lazy-loaded)
        self.visualizer = None

    def _initialize_agents(self, agent_names: Optional[List[str]], workspace: str) -> Dict[str, Any]:
        """
        Initialize available CLI agents

        Args:
            agent_names: Requested agent names, None for auto-detect
            workspace: Workspace path for agents

        Returns:
            Dictionary of initialized agents {name: agent_instance}
        """
        agents = {}

        # Define available agents
        available_agents = {
            'claude': lambda: ClaudeCLIAgent(workspace=workspace),
            'codex': lambda: CodexExecAgent(workspace=workspace),
            'gemini': lambda: GeminiAgent(workspace=workspace)
        }

        # Determine which agents to initialize
        if agent_names:
            # Use specified agents
            agent_list = agent_names
        else:
            # Auto-detect all available agents
            agent_list = list(available_agents.keys())

        # Initialize each agent
        for name in agent_list:
            if name not in available_agents:
                if not self.quiet:
                    print(f"[WARN] Unknown agent: {name}")
                continue

            try:
                agents[name] = available_agents[name]()
                if not self.quiet:
                    print(f"[OK] {name.capitalize()} CLI ready")
            except Exception as e:
                if not self.quiet:
                    print(f"[WARN] {name.capitalize()} CLI not available: {e}")

        if not agents:
            raise RuntimeError("No CLI agents available! Please install at least one CLI tool.")

        return agents

    # ========================================================================
    # Public API - Main Execution Methods
    # ========================================================================

    async def decompose_and_execute(
        self,
        task_description: str,
        mode: ExecutionMode = ExecutionMode.AUTO
    ) -> CLIExecutionResult:
        """
        Decompose and execute a task (one-step operation)

        This is the primary API method for end-to-end task execution.

        Args:
            task_description: Natural language task description
            mode: Execution mode (AUTO/SERIAL/PARALLEL)

        Returns:
            CLIExecutionResult with complete execution metrics

        Example:
            ```python
            result = await cli.decompose_and_execute(
                "Build a REST API with authentication",
                mode=ExecutionMode.AUTO
            )
            ```
        """
        start_time = time.time()

        # Step 1: Decompose task
        if not self.quiet:
            print(f"\n[1/2] Decomposing task...")

        decompose_start = time.time()
        tasks = await self.meta_agent.decompose_task(task_description)
        decompose_time = time.time() - decompose_start

        if not self.quiet:
            print(f"      Decomposed into {len(tasks)} subtasks ({decompose_time:.2f}s)")

        # Step 2: Execute tasks
        if not self.quiet:
            print(f"\n[2/2] Executing tasks ({mode.value} mode)...")

        exec_result = await self.scheduler.schedule(tasks, mode=mode)

        # Calculate statistics
        successful = sum(1 for r in exec_result.results if r.get('success', False))
        total_time = time.time() - start_time
        success_rate = successful / len(tasks) if tasks else 0.0

        return CLIExecutionResult(
            tasks=tasks,
            execution_result=exec_result,
            decompose_time=decompose_time,
            total_time=total_time,
            success_rate=success_rate,
            workspace_path=str(self.workspace_path)
        )

    async def decompose_task(self, task_description: str) -> List[Task]:
        """
        Decompose task without executing (preview only)

        Useful for:
        - Previewing task decomposition
        - Manual task adjustment before execution

        Args:
            task_description: Natural language task description

        Returns:
            List of decomposed Task objects
        """
        return await self.meta_agent.decompose_task(task_description)

    async def execute_tasks(
        self,
        tasks: List[Task],
        mode: ExecutionMode = ExecutionMode.AUTO
    ) -> ExecutionResult:
        """
        Execute pre-decomposed tasks

        Useful for:
        - Executing manually created tasks
        - Re-executing previously decomposed tasks

        Args:
            tasks: List of Task objects to execute
            mode: Execution mode (AUTO/SERIAL/PARALLEL)

        Returns:
            Raw ExecutionResult from scheduler
        """
        return await self.scheduler.schedule(tasks, mode=mode)

    # ========================================================================
    # Utility Methods - Output and Visualization
    # ========================================================================

    def print_summary(self, result: CLIExecutionResult):
        """
        Print execution summary to console

        Args:
            result: Execution result to summarize
        """
        print("\n" + "=" * 70)
        print("  Execution Summary")
        print("=" * 70)
        print(f"\nTasks: {result.task_count}")
        print(f"Decompose Time: {result.decompose_time:.2f}s")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Total Time: {result.total_time:.2f}s")
        print(f"Success Rate: {result.success_rate * 100:.1f}%")

        if result.speedup:
            print(f"Speedup: {result.speedup:.2f}x")

        print()

    def visualize_tasks(self, tasks: List[Task]) -> str:
        """
        Generate ASCII task dependency tree

        Args:
            tasks: List of tasks to visualize

        Returns:
            ASCII art representation of task dependencies
        """
        if not self.visualizer:
            self.visualizer = TaskVisualizer(tasks)
        return self.visualizer.build_tree()

    def export_results(
        self,
        result: CLIExecutionResult,
        output_path: str,
        format: str = "json"
    ):
        """
        Export results to file

        Args:
            result: Execution result to export
            output_path: Output file path
            format: Export format ('json', 'yaml', 'csv')
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        if not self.quiet:
            print(f"✅ Results exported to {output_file}")


# ============================================================================
# Command-Line Interface
# ============================================================================

def main():
    """
    Command-line entry point

    Supports two modes:
    1. Interactive: python multi_agent_cli.py
    2. Batch: python multi_agent_cli.py --task "..." --agents claude,gemini
    """
    parser = argparse.ArgumentParser(
        description="Multi-Agent CLI Client - Task Decomposition and Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python multi_agent_cli.py

  # Batch mode with task
  python multi_agent_cli.py --task "Build a REST API"

  # Specify agents
  python multi_agent_cli.py --task "..." --agents claude,gemini

  # Export results
  python multi_agent_cli.py --task "..." --output results.json

  # Quiet mode (for scripting)
  python multi_agent_cli.py --task "..." --quiet
"""
    )

    # Task input
    parser.add_argument(
        '--task', '-t',
        type=str,
        help='Task description (interactive mode if not provided)'
    )

    # Agent selection
    parser.add_argument(
        '--agents', '-a',
        type=str,
        default=None,
        help='Comma-separated agent list (e.g., "claude,gemini"). Auto-detect if not specified.'
    )

    # Execution mode
    parser.add_argument(
        '--mode', '-m',
        type=str,
        choices=['auto', 'serial', 'parallel'],
        default='auto',
        help='Execution mode (default: auto)'
    )

    # Workspace
    parser.add_argument(
        '--workspace', '-w',
        type=str,
        default=None,
        help='Workspace directory (auto-create if not specified)'
    )

    # Output
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file path for results (JSON format)'
    )

    # Quiet mode
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (minimal output, for scripting)'
    )

    args = parser.parse_args()

    # Parse agent list
    agent_list = args.agents.split(',') if args.agents else None

    # Initialize CLI client
    try:
        cli = MultiAgentCLI(
            agents=agent_list,
            workspace=args.workspace,
            quiet=args.quiet
        )
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("\nSetup Instructions:")
        print("  1. Install at least one CLI tool:")
        print("     npm install -g @anthropic-ai/claude-code")
        print("  2. Authenticate:")
        print("     claude auth login")
        return 1

    # Get task description
    if args.task:
        task_description = args.task
    else:
        # Interactive mode
        if not args.quiet:
            print("\n" + "=" * 70)
            print("  Multi-Agent CLI Client")
            print("=" * 70)
            print()

        task_description = input("Enter task description: ").strip()

        if not task_description:
            print("No task provided. Exiting.")
            return 0

    # Map mode string to ExecutionMode
    mode_map = {
        'auto': ExecutionMode.AUTO,
        'serial': ExecutionMode.SERIAL,
        'parallel': ExecutionMode.PARALLEL
    }

    # Execute task
    try:
        result = asyncio.run(
            cli.decompose_and_execute(
                task_description,
                mode=mode_map[args.mode]
            )
        )

        # Display results (unless quiet)
        if not args.quiet:
            cli.print_summary(result)
            print(cli.visualize_tasks(result.tasks))

        # Export results if requested
        if args.output:
            cli.export_results(result, args.output, format='json')

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
