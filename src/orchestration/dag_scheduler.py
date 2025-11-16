"""
DAG Scheduler Implementation

Schedules tasks with dependencies using topological sort (Kahn's algorithm).
Uses ToolExecutor interface for execution (CLI or API mode).

Features:
- Dependency resolution with topological sort
- Batch-based parallel execution
- Circular dependency detection
- Supports both CLI and API executors

Example:
    >>> from orchestration import DAGScheduler, CLIExecutor
    >>> from scheduler import Task
    >>>
    >>> executor = CLIExecutor()
    >>> await executor.initialize()
    >>>
    >>> scheduler = DAGScheduler(executor, default_agent="claude")
    >>>
    >>> tasks = [
    ...     Task(id="task1", prompt="Install nginx", depends_on=[]),
    ...     Task(id="task2", prompt="Configure nginx", depends_on=["task1"]),
    ...     Task(id="task3", prompt="Start nginx", depends_on=["task2"])
    ... ]
    >>>
    >>> result = await scheduler.execute_dag(tasks)
    >>> print(f"Completed {result.task_count} tasks in {result.total_time:.2f}s")
"""

import asyncio
import time
from typing import List, Dict, Set, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from scheduler import Task

# Use absolute import for compatibility
try:
    from .executor import ToolExecutor, TaskResult
except ImportError:
    from executor import ToolExecutor, TaskResult


@dataclass
class DAGResult:
    """
    DAG execution result

    Attributes:
        total_time: Total execution time in seconds
        task_count: Number of tasks executed
        batch_count: Number of batches executed
        results: List of TaskResult objects
        success_count: Number of successful tasks
        failed_count: Number of failed tasks
        metadata: Additional execution metadata
    """
    total_time: float
    task_count: int
    batch_count: int
    results: List[TaskResult]
    success_count: int = 0
    failed_count: int = 0
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate success/failure counts"""
        self.success_count = sum(1 for r in self.results if r.success)
        self.failed_count = self.task_count - self.success_count

        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()


class DAGScheduler:
    """
    DAG-based task scheduler using topological sort

    Schedules tasks with dependencies ensuring:
    - Tasks execute only after their dependencies complete
    - Tasks within the same batch execute in parallel
    - Circular dependencies are detected

    Uses ToolExecutor interface for execution, supporting both CLI and API modes.

    Example:
        >>> executor = CLIExecutor()
        >>> await executor.initialize()
        >>> scheduler = DAGScheduler(executor, default_agent="claude")
        >>>
        >>> tasks = [...]  # Tasks with depends_on relationships
        >>> result = await scheduler.execute_dag(tasks)
    """

    def __init__(
        self,
        executor: ToolExecutor,
        default_agent: str = "claude",
        verbose: bool = True
    ):
        """
        Initialize DAG scheduler

        Args:
            executor: ToolExecutor instance (CLI or API)
            default_agent: Default agent name for tasks
            verbose: Whether to print execution progress
        """
        self.executor = executor
        self.default_agent = default_agent
        self.verbose = verbose

    def build_dependency_graph(self, tasks: List['Task']) -> Dict[str, List[str]]:
        """
        Build task dependency graph (adjacency list)

        Args:
            tasks: List of tasks

        Returns:
            Graph mapping task_id -> list of dependent task IDs

        Example:
            tasks = [
                Task(id="A", depends_on=[]),
                Task(id="B", depends_on=["A"]),
                Task(id="C", depends_on=["A"])
            ]
            => {"A": ["B", "C"], "B": [], "C": []}
        """
        graph: Dict[str, List[str]] = {task.id: [] for task in tasks}
        task_map: Dict[str, 'Task'] = {task.id: task for task in tasks}

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in graph:
                    graph[dep_id].append(task.id)

        return graph

    def topological_sort(self, tasks: List['Task']) -> List[List['Task']]:
        """
        Topologically sort tasks into executable batches using Kahn's algorithm

        Returns:
            List of batches, where tasks in each batch can execute in parallel

        Raises:
            ValueError: If circular dependency detected

        Algorithm:
            1. Calculate in-degree for each task (number of dependencies)
            2. Find all tasks with in-degree 0 (ready to execute)
            3. Execute these tasks as a batch
            4. Decrease in-degree of dependent tasks
            5. Repeat until all tasks processed

        Example:
            tasks = [A, B(→A), C(→A), D(→B,C)]
            => [[A], [B, C], [D]]  # 3 batches
        """
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: len(task.depends_on) for task in tasks}

        batches = []
        processed = set()

        while len(processed) < len(tasks):
            # Find all tasks with in-degree 0 (currently executable)
            current_batch = []
            for task in tasks:
                if task.id not in processed and in_degree[task.id] == 0:
                    current_batch.append(task)

            if not current_batch:
                # No tasks can be executed but not all tasks processed
                remaining = [t.id for t in tasks if t.id not in processed]
                raise ValueError(
                    f"Circular dependency detected! Cannot resolve tasks: {remaining}"
                )

            batches.append(current_batch)

            # Update in-degrees for next iteration
            for task in current_batch:
                processed.add(task.id)

                # Find tasks that depend on the current task
                for other_task in tasks:
                    if task.id in other_task.depends_on:
                        in_degree[other_task.id] -= 1

        return batches

    async def execute_dag(
        self,
        tasks: List['Task'],
        agent_mapping: Optional[Dict[str, str]] = None
    ) -> DAGResult:
        """
        Execute tasks with dependencies using DAG scheduling

        Args:
            tasks: List of tasks with depends_on relationships
            agent_mapping: Optional task_id -> agent_name mapping
                          Falls back to default_agent if not specified

        Returns:
            DAGResult with execution details

        Example:
            >>> tasks = [
            ...     Task(id="install_pkg", prompt="Install nginx", depends_on=[]),
            ...     Task(id="config_pkg", prompt="Configure nginx", depends_on=["install_pkg"]),
            ...     Task(id="start_pkg", prompt="Start nginx", depends_on=["config_pkg"])
            ... ]
            >>> result = await scheduler.execute_dag(tasks)
            >>> # Executes in 3 batches: install -> config -> start
        """
        if not tasks:
            raise ValueError("No tasks provided")

        if self.verbose:
            print(f"\n🔀 [DAG SCHEDULER] Executing {len(tasks)} tasks with dependencies")

        start_time = time.time()

        # Perform topological sort
        try:
            batches = self.topological_sort(tasks)
        except ValueError as e:
            # Circular dependency detected
            if self.verbose:
                print(f"\n❌ {e}")
            return DAGResult(
                total_time=time.time() - start_time,
                task_count=len(tasks),
                batch_count=0,
                results=[],
                metadata={"error": str(e)}
            )

        if self.verbose:
            print(f"  📊 Scheduled into {len(batches)} batches")
            for i, batch in enumerate(batches, 1):
                task_ids = ", ".join([t.id for t in batch])
                print(f"    Batch {i}: [{task_ids}]")

        # Execute batches sequentially, tasks within batch in parallel
        all_results: List[TaskResult] = []

        for batch_idx, batch in enumerate(batches, 1):
            if self.verbose:
                print(f"\n  ⚡ Batch {batch_idx}/{len(batches)}: Executing {len(batch)} tasks in parallel")

            batch_start = time.time()

            # Execute tasks in parallel using asyncio.gather
            batch_results = await asyncio.gather(*[
                self._execute_single_task(task, agent_mapping, batch_idx)
                for task in batch
            ])

            batch_time = time.time() - batch_start
            all_results.extend(batch_results)

            # Print batch results
            if self.verbose:
                success_count = sum(1 for r in batch_results if r.success)
                print(f"    ✓ Batch {batch_idx} completed in {batch_time:.2f}s "
                      f"({success_count}/{len(batch)} successful)")

        total_time = time.time() - start_time

        result = DAGResult(
            total_time=total_time,
            task_count=len(tasks),
            batch_count=len(batches),
            results=all_results
        )

        if self.verbose:
            print(f"\n  📈 DAG Execution Complete:")
            print(f"    Total time: {result.total_time:.2f}s")
            print(f"    Success rate: {result.success_count}/{result.task_count} "
                  f"({result.success_count/result.task_count*100:.1f}%)")

        return result

    async def _execute_single_task(
        self,
        task: 'Task',
        agent_mapping: Optional[Dict[str, str]],
        batch: int
    ) -> TaskResult:
        """
        Execute a single task using the executor

        Args:
            task: Task to execute
            agent_mapping: Optional task_id -> agent_name mapping
            batch: Batch number (for logging)

        Returns:
            TaskResult from executor
        """
        # Determine agent for this task
        agent_name = self.default_agent
        if agent_mapping and task.id in agent_mapping:
            agent_name = agent_mapping[task.id]

        if self.verbose:
            print(f"      [{agent_name}] {task.id}: {task.prompt[:50]}...")

        # Execute via executor
        try:
            result = await self.executor.execute(
                task_prompt=task.prompt,
                agent_name=agent_name,
                task_id=task.id
            )

            if self.verbose:
                status = "✓" if result.success else "✗"
                print(f"      {status} {task.id} completed in {result.latency:.2f}s")

            return result

        except Exception as e:
            if self.verbose:
                print(f"      ✗ {task.id} failed: {e}")

            return TaskResult(
                task_id=task.id,
                success=False,
                output="",
                latency=0.0,
                agent=agent_name,
                error=f"Execution error: {str(e)}",
                metadata={"exception": type(e).__name__, "batch": batch}
            )


# Convenience functions
async def execute_dag_with_executor(
    tasks: List['Task'],
    executor: ToolExecutor,
    agent: str = "claude"
) -> DAGResult:
    """
    Quick DAG execution (convenience function)

    Args:
        tasks: Tasks with dependencies
        executor: Initialized executor
        agent: Agent name

    Returns:
        DAGResult

    Example:
        >>> executor = CLIExecutor()
        >>> await executor.initialize()
        >>> result = await execute_dag_with_executor(tasks, executor)
    """
    scheduler = DAGScheduler(executor, default_agent=agent)
    return await scheduler.execute_dag(tasks)


# TODO: Day 5 - Add dependency injection support (pass task outputs to inputs)
# TODO: Day 5 - Support agent selection based on task type
# TODO: Day 6 - Add AgentBench task adapter
