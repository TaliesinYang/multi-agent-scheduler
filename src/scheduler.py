"""
Multi-Agent Intelligent Scheduler
Core scheduler implementing parallel vs serial intelligent scheduling decisions
"""

import asyncio
import time
from typing import List, Dict, Optional, Set, Any, TYPE_CHECKING, Union, AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from src.agents import BaseAgent
    from src.logger import ExecutionLogger
    from src.config import AgentConfig
    from src.agent_selector import SmartAgentSelector
    from src.dependency_injection import SchedulerDependencies
    from src.workflow_graph import WorkflowGraph, WorkflowState
    from src.checkpoint import CheckpointManager


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
        dependencies: Optional[Union['SchedulerDependencies', Dict[str, 'BaseAgent']]] = None,
        agents: Optional[Dict[str, 'BaseAgent']] = None,
        logger: Optional['ExecutionLogger'] = None,
        config_path: Optional[str] = None,
        checkpoint_manager: Optional['CheckpointManager'] = None,
        enable_checkpoints: bool = False
    ) -> None:
        """
        Initialize scheduler with dependency injection support

        Args:
            dependencies: SchedulerDependencies object with all dependencies
                         OR legacy Dict of agents (for backward compatibility)
            agents: Agent dictionary (legacy, use dependencies instead)
            logger: ExecutionLogger instance (legacy, use dependencies instead)
            config_path: Path to agent configuration YAML (legacy)

        Example (new way - dependency injection):
            >>> from src.dependency_injection import SchedulerDependencies
            >>> deps = SchedulerDependencies(
            ...     agents={'claude': ClaudeAgent()},
            ...     logger=logger,
            ...     config=config
            ... )
            >>> scheduler = MultiAgentScheduler(deps)

        Example (legacy way - still supported):
            >>> scheduler = MultiAgentScheduler(
            ...     agents={'claude': ClaudeAgent()},
            ...     logger=logger
            ... )
        """
        self.execution_history = []

        # Handle dependency injection
        if dependencies is not None:
            # Check if it's a SchedulerDependencies object
            if hasattr(dependencies, 'agents') and hasattr(dependencies, 'get_config'):
                # New way: SchedulerDependencies object
                self._deps = dependencies
                self.agents = dependencies.agents
                self.logger = dependencies.get_logger()
                self.config = dependencies.get_config()
                self.agent_selector = dependencies.get_agent_selector()
            else:
                # Legacy way: Dict of agents passed as first argument
                self.agents = dependencies  # type: ignore
                self.logger = logger
                self._deps = None

                # Load configuration the old way
                from src.config import AgentConfig
                from src.agent_selector import SmartAgentSelector

                self.config = AgentConfig.load(config_path)
                self.agent_selector = SmartAgentSelector(self.config)
        else:
            # Legacy way: separate parameters
            if agents is None:
                raise ValueError("Either 'dependencies' or 'agents' must be provided")

            self.agents = agents
            self.logger = logger
            self._deps = None

            # Load configuration the old way
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

        # Optional services from DI container
        self.metrics = self._deps.get_metrics() if self._deps else None
        self.event_bus = self._deps.get_event_bus() if self._deps else None
        self.cache = self._deps.get_cache() if self._deps else None

        # Checkpoint support
        self.checkpoint_manager = checkpoint_manager
        self.enable_checkpoints = enable_checkpoints
        if self.enable_checkpoints and not self.checkpoint_manager:
            # Auto-create checkpoint manager if enabled
            from src.checkpoint import CheckpointManager
            self.checkpoint_manager = CheckpointManager()

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
        Execute a single task with metrics and event support

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

        # Emit task start event
        if self.event_bus:
            await self.event_bus.emit('task.started', {
                'task_id': task.id,
                'agent': agent_name,
                'batch': batch
            }, source='scheduler')

        # Increment metrics
        if self.metrics:
            self.metrics.inc('tasks.started')
            self.metrics.inc(f'tasks.{task.task_type}.started')

        # Log task start
        if self.logger:
            self.logger.log_task_start(task.id, task.prompt, agent.name, batch, rationale)
        else:
            print(f"  ⚡ [{agent_name}] Executing task: {task.id}")

        # Execute with timing
        if self.metrics:
            with self.metrics.time('task.execution'):
                result = await agent.call(task.prompt)
        else:
            result = await agent.call(task.prompt)

        result['task_id'] = task.id
        result['task_type'] = task.task_type
        result['agent_selected'] = agent_name

        # Track success/failure metrics
        if self.metrics:
            if result.get('success', False):
                self.metrics.inc('tasks.completed')
                self.metrics.inc(f'tasks.{task.task_type}.completed')
            else:
                self.metrics.inc('tasks.failed')
                self.metrics.inc(f'tasks.{task.task_type}.failed')

        # Emit task complete event
        if self.event_bus:
            await self.event_bus.emit('task.completed', {
                'task_id': task.id,
                'agent': agent_name,
                'success': result.get('success', False),
                'latency': result.get('latency', 0)
            }, source='scheduler')

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

    async def execute_task_stream(
        self,
        task: Task,
        agent_name: str,
        batch: int = 0
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a single task with streaming response

        Args:
            task: Task object
            agent_name: Agent name to use
            batch: Batch number (for logging)

        Yields:
            Stream chunks as dictionaries:
            - {'task_id': str, 'chunk': str, 'done': False} - intermediate chunks
            - {'task_id': str, 'result': str, 'done': True, 'success': bool} - final result

        Example:
            >>> async for chunk_data in scheduler.execute_task_stream(task, 'claude'):
            ...     if not chunk_data['done']:
            ...         print(chunk_data['chunk'], end='', flush=True)
            ...     else:
            ...         print(f"\\nCompleted: {chunk_data['success']}")
        """
        agent = self.agents[agent_name]

        # Get selection rationale if available
        rationale: Optional[Dict[str, Any]] = None
        if hasattr(self, 'agent_selector') and self.config.should_log_rationale():
            rationale = self.agent_selector.get_last_selection_rationale()

        # Emit task start event
        if self.event_bus:
            await self.event_bus.emit('task.stream_started', {
                'task_id': task.id,
                'agent': agent_name,
                'batch': batch
            }, source='scheduler')

        # Increment metrics
        if self.metrics:
            self.metrics.inc('tasks.stream_started')
            self.metrics.inc(f'tasks.{task.task_type}.stream_started')

        # Log task start
        if self.logger:
            self.logger.log_task_start(task.id, task.prompt, agent.name, batch, rationale)
        else:
            print(f"  🌊 [{agent_name}] Streaming task: {task.id}")

        # Stream execution
        start_time = time.time()
        full_text = ""
        success = True
        error_msg = None

        try:
            async for chunk in agent.call_stream(task.prompt):
                full_text += chunk
                yield {
                    'task_id': task.id,
                    'chunk': chunk,
                    'done': False
                }

            # Final result
            end_time = time.time()
            latency = end_time - start_time

        except Exception as e:
            success = False
            error_msg = str(e)
            end_time = time.time()
            latency = end_time - start_time
            print(f"❌ Stream error for task {task.id}: {error_msg}")

        # Track success/failure metrics
        if self.metrics:
            if success:
                self.metrics.inc('tasks.stream_completed')
                self.metrics.inc(f'tasks.{task.task_type}.stream_completed')
            else:
                self.metrics.inc('tasks.stream_failed')
                self.metrics.inc(f'tasks.{task.task_type}.stream_failed')

        # Emit task complete event
        if self.event_bus:
            await self.event_bus.emit('task.stream_completed', {
                'task_id': task.id,
                'agent': agent_name,
                'success': success,
                'latency': latency
            }, source='scheduler')

        # Log task complete
        if self.logger:
            self.logger.log_task_complete(
                task.id,
                success,
                latency,
                error_msg,
                full_text if success else None
            )

        # Yield final result
        yield {
            'task_id': task.id,
            'task_type': task.task_type,
            'agent_selected': agent_name,
            'result': full_text,
            'latency': latency,
            'done': True,
            'success': success,
            'error': error_msg
        }

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

    async def execute_workflow(
        self,
        workflow: 'WorkflowGraph',
        initial_state: Optional['WorkflowState'] = None,
        timeout: Optional[float] = None,
        execution_id: Optional[str] = None,
        enable_checkpoints: Optional[bool] = None
    ) -> 'WorkflowState':
        """
        Execute a workflow graph with scheduler integration

        Args:
            workflow: WorkflowGraph to execute
            initial_state: Initial workflow state
            timeout: Execution timeout in seconds
            execution_id: Unique execution ID for checkpointing
            enable_checkpoints: Override global checkpoint setting

        Returns:
            Final workflow state

        Example:
            >>> from src.workflow_graph import WorkflowGraph, WorkflowNode, NodeType
            >>> graph = WorkflowGraph()
            >>> graph.add_node(WorkflowNode("start", NodeType.START))
            >>> # ... add more nodes
            >>> result = await scheduler.execute_workflow(graph)
        """
        # Import here to avoid circular dependency
        from src.workflow_graph import WorkflowState
        from src.checkpoint import CheckpointStatus

        # Determine if checkpointing is enabled
        checkpointing = enable_checkpoints if enable_checkpoints is not None else self.enable_checkpoints

        # Generate execution ID if checkpointing
        if checkpointing and not execution_id:
            import uuid
            execution_id = f"workflow_{workflow.graph_id}_{uuid.uuid4().hex[:8]}"

        # Emit workflow start event
        if self.event_bus:
            await self.event_bus.emit('workflow.started', {
                'graph_id': workflow.graph_id,
                'execution_id': execution_id,
                'node_count': len(workflow.nodes),
                'edge_count': len(workflow.edges)
            }, source='scheduler')

        # Increment metrics
        if self.metrics:
            self.metrics.inc('workflows.started')

        # Validate workflow
        issues = workflow.validate()
        if issues:
            print(f"⚠️  Workflow validation warnings:")
            for issue in issues:
                print(f"    - {issue}")

        print(f"\n🔀 [WORKFLOW] Executing graph '{workflow.graph_id}'")
        if execution_id:
            print(f"   Execution ID: {execution_id}")
        print(f"   Nodes: {len(workflow.nodes)}, Edges: {len(workflow.edges)}")
        if checkpointing:
            print(f"   Checkpointing: enabled")

        # Create initial checkpoint if enabled
        if checkpointing and self.checkpoint_manager:
            await self.checkpoint_manager.create_checkpoint(
                execution_id=execution_id,
                status=CheckpointStatus.RUNNING,
                workflow_state=initial_state.data if initial_state else {},
                metadata={'graph_id': workflow.graph_id}
            )

        # Execute workflow
        start_time = time.time()
        try:
            if self.metrics:
                with self.metrics.time('workflow.execution'):
                    final_state = await workflow.execute(
                        initial_state,
                        timeout=timeout,
                        checkpoint_manager=self.checkpoint_manager if checkpointing else None,
                        execution_id=execution_id
                    )
            else:
                final_state = await workflow.execute(
                    initial_state,
                    timeout=timeout,
                    checkpoint_manager=self.checkpoint_manager if checkpointing else None,
                    execution_id=execution_id
                )

            success = not final_state.get('error')

        except Exception as e:
            success = False
            print(f"❌ Workflow execution failed: {e}")

            # Create error state
            from src.workflow_graph import WorkflowState
            final_state = initial_state or WorkflowState()
            final_state.set('error', str(e))
            final_state.metadata['end_time'] = time.time()
            final_state.metadata['duration'] = time.time() - start_time

            # Save failure checkpoint
            if checkpointing and self.checkpoint_manager:
                await self.checkpoint_manager.create_checkpoint(
                    execution_id=execution_id,
                    status=CheckpointStatus.FAILED,
                    workflow_state=final_state.data,
                    error=str(e),
                    metadata={'graph_id': workflow.graph_id}
                )

        # Save completion checkpoint
        if checkpointing and self.checkpoint_manager and success:
            await self.checkpoint_manager.create_checkpoint(
                execution_id=execution_id,
                status=CheckpointStatus.COMPLETED,
                workflow_state=final_state.data,
                completed_nodes=final_state.history,
                metadata={'graph_id': workflow.graph_id}
            )

        # Track metrics
        if self.metrics:
            if success:
                self.metrics.inc('workflows.completed')
            else:
                self.metrics.inc('workflows.failed')

        # Emit workflow complete event
        if self.event_bus:
            await self.event_bus.emit('workflow.completed', {
                'graph_id': workflow.graph_id,
                'execution_id': execution_id,
                'success': success,
                'duration': final_state.metadata.get('duration', 0),
                'node_count': len(final_state.history)
            }, source='scheduler')

        # Print execution summary
        duration = final_state.metadata.get('duration', 0)
        path = ' → '.join(final_state.history) if final_state.history else 'none'
        print(f"\n✅ Workflow completed in {duration:.2f}s")
        print(f"   Execution path: {path}")

        return final_state

    async def resume_workflow(
        self,
        execution_id: str,
        workflow: 'WorkflowGraph',
        timeout: Optional[float] = None
    ) -> 'WorkflowState':
        """
        Resume workflow execution from last checkpoint

        Args:
            execution_id: Execution ID to resume
            workflow: WorkflowGraph (must match original)
            timeout: Execution timeout

        Returns:
            Final workflow state

        Raises:
            ValueError: If cannot resume (no checkpoint or wrong status)
        """
        from src.workflow_graph import WorkflowState
        from src.checkpoint import CheckpointStatus

        if not self.checkpoint_manager:
            raise ValueError("Checkpoint manager not configured")

        # Load latest checkpoint
        checkpoint = await self.checkpoint_manager.load_latest_checkpoint(execution_id)

        if not checkpoint:
            raise ValueError(f"No checkpoint found for execution {execution_id}")

        if checkpoint.status not in [CheckpointStatus.RUNNING, CheckpointStatus.PAUSED]:
            raise ValueError(f"Cannot resume from status: {checkpoint.status.value}")

        print(f"\n🔄 [RESUME] Resuming workflow '{workflow.graph_id}'")
        print(f"   Execution ID: {execution_id}")
        print(f"   From checkpoint: {checkpoint.checkpoint_id}")
        print(f"   Completed nodes: {len(checkpoint.completed_nodes)}")

        # Restore state
        initial_state = WorkflowState(
            data=checkpoint.workflow_state,
            history=checkpoint.completed_nodes,
            metadata=checkpoint.metadata
        )

        # Resume execution
        return await self.execute_workflow(
            workflow,
            initial_state=initial_state,
            timeout=timeout,
            execution_id=execution_id,
            enable_checkpoints=True
        )

    def create_task_workflow(
        self,
        tasks: List[Task],
        workflow_type: str = "sequential"
    ) -> 'WorkflowGraph':
        """
        Create a workflow graph from a list of tasks

        Args:
            tasks: List of tasks to convert
            workflow_type: Type of workflow ("sequential", "parallel", or "dependency")

        Returns:
            WorkflowGraph configured for the tasks

        Example:
            >>> tasks = [
            ...     Task(id="task1", prompt="Write a function", task_type="coding"),
            ...     Task(id="task2", prompt="Write tests", task_type="coding"),
            ... ]
            >>> graph = scheduler.create_task_workflow(tasks, "sequential")
            >>> result = await scheduler.execute_workflow(graph)
        """
        from src.workflow_graph import WorkflowGraph, WorkflowNode, WorkflowEdge, NodeType, EdgeType

        graph = WorkflowGraph(graph_id=f"{workflow_type}_workflow")

        # Add start and end nodes
        graph.add_node(WorkflowNode("start", NodeType.START))
        graph.add_node(WorkflowNode("end", NodeType.END))

        # Create task handlers (with proper closure)
        def make_handler(t: Task) -> Callable:
            """Create handler for task execution"""
            async def handler(state: 'WorkflowState') -> Dict[str, Any]:
                # Select agent
                agent_name = self.select_agent(t)

                # Execute task
                result = await self.execute_task(t, agent_name)

                # Store result in state
                return {
                    f"task_{t.id}_result": result.get('result'),
                    f"task_{t.id}_success": result.get('success'),
                    f"task_{t.id}_latency": result.get('latency')
                }

            return handler

        task_handlers = {task.id: make_handler(task) for task in tasks}

        # Build workflow based on type
        if workflow_type == "sequential":
            # Sequential workflow: start -> task1 -> task2 -> ... -> end
            prev = "start"
            for task in tasks:
                node = WorkflowNode(
                    node_id=task.id,
                    node_type=NodeType.TASK,
                    handler=task_handlers[task.id],
                    config={'task_type': task.task_type}
                )
                graph.add_node(node)
                graph.add_edge(WorkflowEdge(prev, task.id))
                prev = task.id

            graph.add_edge(WorkflowEdge(prev, "end"))

        elif workflow_type == "parallel":
            # Parallel workflow: start -> [task1, task2, ...] -> end
            task_ids = []
            for task in tasks:
                node = WorkflowNode(
                    node_id=task.id,
                    node_type=NodeType.TASK,
                    handler=task_handlers[task.id],
                    config={'task_type': task.task_type}
                )
                graph.add_node(node)
                task_ids.append(task.id)

            # Add parallel branches
            graph.add_parallel_branches("start", task_ids, "end")

        elif workflow_type == "dependency":
            # Dependency-based workflow: respect task dependencies
            for task in tasks:
                node = WorkflowNode(
                    node_id=task.id,
                    node_type=NodeType.TASK,
                    handler=task_handlers[task.id],
                    config={'task_type': task.task_type}
                )
                graph.add_node(node)

            # Connect based on dependencies
            for task in tasks:
                if not task.depends_on:
                    # No dependencies, connect to start
                    graph.add_edge(WorkflowEdge("start", task.id))
                else:
                    # Has dependencies, connect from dependency tasks
                    for dep_id in task.depends_on:
                        graph.add_edge(WorkflowEdge(dep_id, task.id))

            # Connect leaf tasks to end
            leaf_tasks = [
                task.id for task in tasks
                if not any(task.id in t.depends_on for t in tasks if t.depends_on)
            ]
            for leaf_id in leaf_tasks:
                graph.add_edge(WorkflowEdge(leaf_id, "end"))

        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        return graph

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
