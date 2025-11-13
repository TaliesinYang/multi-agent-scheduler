"""
Multi-Agent Intelligent Scheduler
Core scheduler implementing parallel vs serial intelligent scheduling decisions
"""

import asyncio
import time
from typing import List, Dict, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from src.agents import BaseAgent
    from src.logger import ExecutionLogger
    from src.config import AgentConfig
    from src.agent_selector import SmartAgentSelector


class ExecutionMode(Enum):
    """Execution mode"""
    PARALLEL = "parallel"
    SERIAL = "serial"
    AUTO = "auto"


@dataclass
class Task:
    """Task definition"""
    id: str
    prompt: str
    task_type: str = "general"  # general, coding, simple, analysis
    depends_on: Optional[List[str]] = None  # List of dependent task IDs
    priority: int = 0  # Priority (higher number = higher priority)
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.depends_on is None:
            self.depends_on = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """Execution result"""
    mode: ExecutionMode
    total_time: float
    task_count: int
    results: List[Dict[str, Any]]
    performance_gain: Optional[float] = None  # Performance gain percentage compared to serial


class MultiAgentScheduler:
    """Multi-Agent Intelligent Scheduler"""

    agents: Dict[str, 'BaseAgent']
    execution_history: List[ExecutionResult]
    logger: Optional['ExecutionLogger']
    config: 'AgentConfig'
    agent_selector: 'SmartAgentSelector'
    agent_selection_strategy: Dict[str, str]

    def __init__(
        self,
        agents: Dict[str, 'BaseAgent'],
        logger: Optional['ExecutionLogger'] = None,
        config_path: Optional[str] = None
    ) -> None:
        """
        Args:
            agents: Agent dictionary, key is agent type, value is agent instance
                   Example: {'claude': ClaudeAgent(...), 'openai': OpenAIAgent(...)}
            logger: ExecutionLogger instance for logging (optional)
            config_path: Path to agent configuration YAML file (optional)
                        If None, uses default configuration
        """
        self.agents = agents
        self.execution_history = []
        self.logger = logger

        # Load agent configuration
        from src.config import AgentConfig
        from src.agent_selector import SmartAgentSelector

        self.config = AgentConfig.load(config_path)
        self.agent_selector = SmartAgentSelector(self.config)

        # Legacy support: keep old strategy as fallback
        self.agent_selection_strategy = {
            'coding': 'claude',
            'simple': 'gemini',
            'analysis': 'openai',
            'general': 'claude',
            'creative': 'openai'
        }

    def analyze_dependencies(self, tasks: List[Task]) -> bool:
        """
        Analyze task dependencies

        Returns:
            True means tasks can be executed in parallel
            False means tasks must be executed serially
        """
        # Check if any task depends on other tasks
        for task in tasks:
            if task.depends_on and len(task.depends_on) > 0:
                return False  # Dependencies exist, must execute serially

        # No dependencies, can execute in parallel
        return True

    def select_agent(self, task: Task) -> str:
        """
        Select the most suitable agent based on task characteristics

        Uses SmartAgentSelector with configuration-driven selection logic.

        Args:
            task: Task object

        Returns:
            Agent name (key in self.agents)
        """
        try:
            # Use smart selector
            selected_agent = self.agent_selector.select(task, self.agents)

            # Log selection rationale if configured
            if self.config.should_log_rationale():
                rationale = self.agent_selector.get_last_selection_rationale()
                if self.logger:
                    # Logger will handle rationale logging
                    pass
                else:
                    # Print rationale if no logger
                    print(f"  🎯 Selected {selected_agent} for {task.id}: "
                          f"{rationale.get('reason', 'N/A')}")

            return selected_agent

        except Exception as e:
            # Fallback to legacy strategy
            print(f"  [WARN] Agent selection error: {e}, using fallback")
            task_type = task.task_type.lower()
            selected_agent = self.agent_selection_strategy.get(task_type, 'claude')

            # If selected agent doesn't exist, use the first available agent
            if selected_agent not in self.agents:
                selected_agent = list(self.agents.keys())[0]

            return selected_agent

    def build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """
        Build task dependency graph (DAG)

        Returns:
            Dependency graph dictionary
        """
        graph: Dict[str, List[str]] = {task.id: [] for task in tasks}
        task_map: Dict[str, Task] = {task.id: task for task in tasks}

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in graph:
                    graph[dep_id].append(task.id)

        return graph

    def topological_sort(self, tasks: List[Task]) -> List[List[Task]]:
        """
        Topologically sort tasks, returning batches that can be executed in parallel

        Returns:
            List[List[Task]]: List of task batches, tasks within the same batch can execute in parallel
        """
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: len(task.depends_on) for task in tasks}

        batches = []
        processed = set()

        while len(processed) < len(tasks):
            # Find all tasks with in-degree of 0 (currently executable)
            current_batch = []
            for task in tasks:
                if task.id not in processed and in_degree[task.id] == 0:
                    current_batch.append(task)

            if not current_batch:
                raise ValueError("Circular dependency detected!")

            batches.append(current_batch)

            # Update in-degrees
            for task in current_batch:
                processed.add(task.id)
                # Find other tasks that depend on the current task
                for other_task in tasks:
                    if task.id in other_task.depends_on:
                        in_degree[other_task.id] -= 1

        return batches

    async def execute_task(
        self,
        task: Task,
        agent_name: str,
        batch: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a single task

        Args:
            task: Task object
            agent_name: Agent name to use
            batch: Batch number (for logging)

        Returns:
            Execution result dictionary
        """
        agent = self.agents[agent_name]

        # Get selection rationale if available
        rationale: Optional[Dict[str, Any]] = None
        if hasattr(self, 'agent_selector') and self.config.should_log_rationale():
            rationale = self.agent_selector.get_last_selection_rationale()

        # Log task start
        if self.logger:
            self.logger.log_task_start(task.id, task.prompt, agent.name, batch, rationale)
        else:
            print(f"  ⚡ [{agent_name}] Executing task: {task.id}")

        result = await agent.call(task.prompt)
        result['task_id'] = task.id
        result['task_type'] = task.task_type
        result['agent_selected'] = agent_name

        # Log task complete with full result
        if self.logger:
            self.logger.log_task_complete(
                task.id,
                result.get('success', False),
                result.get('latency', 0),
                result.get('error'),
                result.get('result')  # Save full task output
            )

        return result

    async def execute_parallel(self, tasks: List[Task]) -> ExecutionResult:
        """
        Execute tasks in parallel

        Args:
            tasks: Task list

        Returns:
            Execution result
        """
        print(f"\n[PARALLEL] Executing {len(tasks)} tasks simultaneously")
        start_time = time.time()

        # Select agent for each task
        task_agent_pairs = [(task, self.select_agent(task)) for task in tasks]

        # Execute all tasks concurrently
        results = await asyncio.gather(*[
            self.execute_task(task, agent_name)
            for task, agent_name in task_agent_pairs
        ])

        total_time = time.time() - start_time

        return ExecutionResult(
            mode=ExecutionMode.PARALLEL,
            total_time=total_time,
            task_count=len(tasks),
            results=results
        )

    async def execute_serial(self, tasks: List[Task]) -> ExecutionResult:
        """
        Execute tasks serially

        Args:
            tasks: Task list

        Returns:
            Execution result
        """
        print(f"\n[SERIAL] Executing {len(tasks)} tasks sequentially")
        start_time = time.time()

        results = []
        for i, task in enumerate(tasks, 1):
            agent_name = self.select_agent(task)
            print(f"  [{i}/{len(tasks)}] ", end="")
            result = await self.execute_task(task, agent_name)
            results.append(result)

        total_time = time.time() - start_time

        return ExecutionResult(
            mode=ExecutionMode.SERIAL,
            total_time=total_time,
            task_count=len(tasks),
            results=results
        )

    async def execute_with_dependencies(self, tasks: List[Task]) -> ExecutionResult:
        """
        Execute tasks with dependencies (hybrid mode)

        Args:
            tasks: Task list

        Returns:
            Execution result
        """
        print(f"\n🔀 [HYBRID MODE] Executing in batches based on dependencies")
        start_time = time.time()

        # Topological sort to get execution batches
        batches = self.topological_sort(tasks)

        all_results = []
        for batch_idx, batch in enumerate(batches, 1):
            print(f"\n  Batch {batch_idx}/{len(batches)}: {len(batch)} tasks")

            # Log batch start
            if self.logger:
                self.logger.start_batch(batch_idx, [task.id for task in batch])

            # Execute tasks within each batch in parallel
            batch_start = time.time()
            batch_results = await asyncio.gather(*[
                self.execute_task(task, self.select_agent(task), batch=batch_idx)
                for task in batch
            ])
            batch_time = time.time() - batch_start

            # Log batch end
            if self.logger:
                self.logger.end_batch()
                print(f"\n  Batch {batch_idx} completed in {batch_time:.2f}s")

            all_results.extend(batch_results)

        total_time = time.time() - start_time

        return ExecutionResult(
            mode=ExecutionMode.AUTO,
            total_time=total_time,
            task_count=len(tasks),
            results=all_results
        )

    async def schedule(self, tasks: List[Task], mode: ExecutionMode = ExecutionMode.AUTO) -> ExecutionResult:
        """
        Intelligently schedule tasks

        Args:
            tasks: Task list
            mode: Execution mode (AUTO for automatic decision, PARALLEL for forced parallel, SERIAL for forced serial)

        Returns:
            Execution result
        """
        if not tasks:
            raise ValueError("No tasks to execute")

        # If AUTO mode, automatically decide execution strategy
        if mode == ExecutionMode.AUTO:
            can_parallelize = self.analyze_dependencies(tasks)

            if can_parallelize:
                # No dependencies, execute in parallel
                result = await self.execute_parallel(tasks)
            else:
                # Has dependencies, execute in hybrid mode (by batches)
                result = await self.execute_with_dependencies(tasks)

        elif mode == ExecutionMode.PARALLEL:
            result = await self.execute_parallel(tasks)

        elif mode == ExecutionMode.SERIAL:
            result = await self.execute_serial(tasks)

        else:
            raise ValueError(f"Unknown execution mode: {mode}")

        # Save to execution history
        self.execution_history.append(result)

        return result

    async def compare_performance(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Compare performance between parallel vs serial execution

        Args:
            tasks: Task list

        Returns:
            Comparison result dictionary
        """
        print("\n" + "=" * 60)
        print("Performance Comparison Test: Serial vs Parallel")
        print("=" * 60)

        # Serial execution
        serial_result = await self.execute_serial(tasks)

        # Wait a bit to avoid API rate limits
        await asyncio.sleep(1)

        # Parallel execution
        parallel_result = await self.execute_parallel(tasks)

        # Calculate performance gain
        time_saved = serial_result.total_time - parallel_result.total_time
        performance_gain = (time_saved / serial_result.total_time) * 100 if serial_result.total_time > 0 else 0

        comparison = {
            "serial_time": serial_result.total_time,
            "parallel_time": parallel_result.total_time,
            "time_saved": time_saved,
            "performance_gain_percent": performance_gain,
            "task_count": len(tasks)
        }

        return comparison

    def print_summary(self, result: ExecutionResult) -> None:
        """Print execution summary"""
        print("\n" + "=" * 60)
        print(f"[OK] Execution Complete!")
        print("=" * 60)
        print(f"Execution mode: {result.mode.value}")
        print(f"Total time: {result.total_time:.2f} seconds")
        print(f"Task count: {result.task_count}")

        # Count success/failure
        success_count = sum(1 for r in result.results if r.get('success', False))
        print(f"Success/Total: {success_count}/{result.task_count}")

        # Count agent usage
        agent_usage = {}
        for r in result.results:
            agent = r.get('agent', 'unknown')
            agent_usage[agent] = agent_usage.get(agent, 0) + 1

        print(f"\nAgent usage:")
        for agent, count in agent_usage.items():
            print(f"  - {agent}: {count} times")

        # Display total token consumption
        total_tokens = sum(r.get('tokens', 0) for r in result.results)
        print(f"\nTotal tokens consumed: {total_tokens}")

        if result.performance_gain:
            print(f"\n⚡ Performance gain: {result.performance_gain:.1f}%")

    def print_detailed_results(
        self,
        result: ExecutionResult,
        max_length: int = 150
    ) -> None:
        """Print detailed results"""
        print("\n" + "-" * 60)
        print("📝 Detailed Task Results")
        print("-" * 60)

        for i, r in enumerate(result.results, 1):
            task_id = r.get('task_id', f'Task {i}')
            agent = r.get('agent', 'Unknown')
            success = r.get('success', False)
            latency = r.get('latency', 0)
            result_text = r.get('result', '')

            status = "✓" if success else "✗"
            print(f"\n[{i}] {task_id} ({agent}) {status}")
            print(f"    Latency: {latency:.2f}s")

            # Truncate long text
            if len(result_text) > max_length:
                result_text = result_text[:max_length] + "..."

            print(f"    Result: {result_text}")

    def _analyze_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """
        Analyze workspace state for agent context

        Args:
            workspace_path: Path to workspace directory

        Returns:
            Dictionary with workspace statistics:
            - total_files: Total file count
            - files_by_type: Dict of {extension: count}
            - directory_structure: List of subdirectories
            - completed_tasks: List of completed task IDs
        """
        from pathlib import Path
        import os

        workspace = Path(workspace_path)
        
        if not workspace.exists():
            return {
                'total_files': 0,
                'files_by_type': {},
                'directory_structure': [],
                'completed_tasks': []
            }
        
        # Count files by type
        total_files = 0
        files_by_type = {}
        
        for file_path in workspace.rglob('*'):
            if file_path.is_file():
                total_files += 1
                ext = file_path.suffix or 'no_extension'
                files_by_type[ext] = files_by_type.get(ext, 0) + 1
        
        # Get directory structure (top level only)
        directory_structure = [
            d.name for d in workspace.iterdir() 
            if d.is_dir() and not d.name.startswith('.')
        ]
        
        # Get completed tasks from logger if available
        completed_tasks = []
        if self.logger:
            completed_tasks = [
                task_id for task_id, log in self.logger.task_logs.items()
                if log.get('success', False)
            ]
        
        return {
            'total_files': total_files,
            'files_by_type': files_by_type,
            'directory_structure': directory_structure,
            'completed_tasks': completed_tasks
        }
