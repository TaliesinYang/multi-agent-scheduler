"""
Graph-Based Workflow Engine

Implements a directed graph workflow system with conditional branching,
parallel execution, loops, and state management.

Inspired by LangGraph but optimized for multi-agent task orchestration.
"""

import asyncio
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict
import time


class NodeType(Enum):
    """Node types in workflow graph"""
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    SUBGRAPH = "subgraph"


class EdgeType(Enum):
    """Edge types in workflow graph"""
    NORMAL = "normal"
    CONDITIONAL = "conditional"
    LOOP_BACK = "loop_back"


@dataclass
class WorkflowState:
    """
    Workflow state that flows through nodes

    Attributes:
        data: Key-value state data
        history: Execution history
        loop_counts: Loop iteration counters
        metadata: Additional metadata
    """
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    loop_counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy(self) -> 'WorkflowState':
        """Create a copy of state"""
        return WorkflowState(
            data=self.data.copy(),
            history=self.history.copy(),
            loop_counts=self.loop_counts.copy(),
            metadata=self.metadata.copy()
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in state"""
        self.data[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """Update state with multiple values"""
        self.data.update(updates)


@dataclass
class WorkflowNode:
    """
    Workflow node

    Attributes:
        node_id: Unique node identifier
        node_type: Type of node
        handler: Async function to execute (optional)
        config: Node configuration
    """
    node_id: str
    node_type: NodeType
    handler: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute node logic

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        # Record execution in history
        state.history.append(self.node_id)

        # Execute handler if exists
        if self.handler:
            try:
                result = await self.handler(state)
                if result is not None:
                    if isinstance(result, dict):
                        state.update(result)
                    elif isinstance(result, WorkflowState):
                        state = result
            except Exception as e:
                state.set('error', str(e))
                state.set('failed_node', self.node_id)
                raise

        return state


@dataclass
class WorkflowEdge:
    """
    Workflow edge

    Attributes:
        from_node: Source node ID
        to_node: Target node ID
        edge_type: Type of edge
        condition: Condition function for conditional edges
        label: Edge label for visualization
    """
    from_node: str
    to_node: str
    edge_type: EdgeType = EdgeType.NORMAL
    condition: Optional[Callable[[WorkflowState], bool]] = None
    label: Optional[str] = None

    def should_traverse(self, state: WorkflowState) -> bool:
        """
        Check if edge should be traversed

        Args:
            state: Current workflow state

        Returns:
            True if edge should be traversed
        """
        if self.edge_type == EdgeType.NORMAL:
            return True

        if self.edge_type == EdgeType.CONDITIONAL and self.condition:
            return self.condition(state)

        if self.edge_type == EdgeType.LOOP_BACK:
            # Check loop count
            loop_id = f"{self.from_node}->{self.to_node}"
            max_iterations = state.metadata.get('max_loop_iterations', 100)
            current_count = state.loop_counts.get(loop_id, 0)
            return current_count < max_iterations

        return False


class WorkflowGraph:
    """
    Graph-based workflow engine

    Supports:
    - Conditional branching (if/else)
    - Parallel execution
    - Loops
    - Subgraphs
    - State management

    Example:
        >>> graph = WorkflowGraph()
        >>> graph.add_node(WorkflowNode("start", NodeType.START))
        >>> graph.add_node(WorkflowNode("task1", NodeType.TASK, handler=my_task))
        >>> graph.add_edge(WorkflowEdge("start", "task1"))
        >>> result = await graph.execute(WorkflowState())
    """

    def __init__(self, graph_id: str = "main"):
        """
        Initialize workflow graph

        Args:
            graph_id: Graph identifier
        """
        self.graph_id = graph_id
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.start_node: Optional[str] = None
        self.end_nodes: Set[str] = set()

    def add_node(self, node: WorkflowNode) -> 'WorkflowGraph':
        """
        Add node to graph

        Args:
            node: WorkflowNode to add

        Returns:
            Self for chaining
        """
        self.nodes[node.node_id] = node

        # Track special nodes
        if node.node_type == NodeType.START:
            self.start_node = node.node_id
        elif node.node_type == NodeType.END:
            self.end_nodes.add(node.node_id)

        return self

    def add_edge(self, edge: WorkflowEdge) -> 'WorkflowGraph':
        """
        Add edge to graph

        Args:
            edge: WorkflowEdge to add

        Returns:
            Self for chaining
        """
        # Validate nodes exist
        if edge.from_node not in self.nodes:
            raise ValueError(f"Source node '{edge.from_node}' not found")
        if edge.to_node not in self.nodes:
            raise ValueError(f"Target node '{edge.to_node}' not found")

        self.edges.append(edge)
        return self

    def add_conditional_edges(
        self,
        from_node: str,
        conditions: Dict[str, Union[str, Callable[[WorkflowState], bool]]],
        default: Optional[str] = None
    ) -> 'WorkflowGraph':
        """
        Add conditional edges from a node

        Args:
            from_node: Source node ID
            conditions: Dict of {label: condition} or {label: target_node}
                       If value is string, uses it as simple equality check
                       If value is callable, uses it as condition function
            default: Default target node if no conditions match

        Returns:
            Self for chaining

        Example:
            >>> graph.add_conditional_edges(
            ...     "analyze",
            ...     {
            ...         "success": lambda state: state.get('status') == 'ok',
            ...         "failure": lambda state: state.get('status') == 'error'
            ...     },
            ...     default="fallback"
            ... )
        """
        for label, condition_or_target in conditions.items():
            if isinstance(condition_or_target, str):
                # Simple string target
                target = condition_or_target
                condition_func = lambda s, l=label: s.get('route') == l
            else:
                # Condition function provided
                # Extract target from label or use label as target
                target = label if label in self.nodes else f"path_{label}"
                condition_func = condition_or_target

            edge = WorkflowEdge(
                from_node=from_node,
                to_node=target,
                edge_type=EdgeType.CONDITIONAL,
                condition=condition_func,
                label=label
            )
            self.add_edge(edge)

        # Add default edge if provided
        if default:
            edge = WorkflowEdge(
                from_node=from_node,
                to_node=default,
                edge_type=EdgeType.CONDITIONAL,
                condition=lambda s: True,  # Always true (fallback)
                label="default"
            )
            self.add_edge(edge)

        return self

    def add_parallel_branches(
        self,
        from_node: str,
        branches: List[str],
        join_node: str
    ) -> 'WorkflowGraph':
        """
        Add parallel execution branches

        Args:
            from_node: Source node that splits
            branches: List of node IDs to execute in parallel
            join_node: Node that waits for all branches

        Returns:
            Self for chaining

        Example:
            >>> graph.add_parallel_branches(
            ...     "start",
            ...     ["branch_a", "branch_b", "branch_c"],
            ...     "join"
            ... )
        """
        # Add edges from source to all branches
        for branch in branches:
            self.add_edge(WorkflowEdge(from_node, branch))

        # Add edges from all branches to join
        for branch in branches:
            self.add_edge(WorkflowEdge(branch, join_node))

        return self

    def add_loop(
        self,
        loop_node: str,
        condition: Callable[[WorkflowState], bool],
        max_iterations: int = 100
    ) -> 'WorkflowGraph':
        """
        Add loop back to a node

        Args:
            loop_node: Node ID to loop back to
            condition: Condition to continue looping
            max_iterations: Maximum loop iterations

        Returns:
            Self for chaining

        Example:
            >>> graph.add_loop(
            ...     "process",
            ...     condition=lambda state: state.get('count', 0) < 10
            ... )
        """
        edge = WorkflowEdge(
            from_node=loop_node,
            to_node=loop_node,
            edge_type=EdgeType.LOOP_BACK,
            condition=condition,
            label="loop"
        )
        self.add_edge(edge)

        return self

    def _find_next_nodes(
        self,
        current_node: str,
        state: WorkflowState
    ) -> List[str]:
        """
        Find next nodes to execute based on current state

        Args:
            current_node: Current node ID
            state: Current workflow state

        Returns:
            List of next node IDs
        """
        next_nodes = []

        for edge in self.edges:
            if edge.from_node == current_node:
                if edge.should_traverse(state):
                    # Track loop iterations
                    if edge.edge_type == EdgeType.LOOP_BACK:
                        loop_id = f"{edge.from_node}->{edge.to_node}"
                        state.loop_counts[loop_id] = state.loop_counts.get(loop_id, 0) + 1

                    next_nodes.append(edge.to_node)

        return next_nodes

    def _is_parallel_split(self, node_id: str) -> bool:
        """
        Check if node splits into parallel branches

        Args:
            node_id: Node ID to check

        Returns:
            True if node has multiple outgoing normal edges
        """
        normal_edges = [
            e for e in self.edges
            if e.from_node == node_id and e.edge_type == EdgeType.NORMAL
        ]
        return len(normal_edges) > 1

    async def execute(
        self,
        initial_state: Optional[WorkflowState] = None,
        start_node: Optional[str] = None,
        timeout: Optional[float] = None,
        checkpoint_manager: Optional[Any] = None,
        execution_id: Optional[str] = None
    ) -> WorkflowState:
        """
        Execute workflow graph

        Args:
            initial_state: Initial workflow state
            start_node: Override start node
            timeout: Execution timeout in seconds
            checkpoint_manager: CheckpointManager for saving state
            execution_id: Unique execution ID for checkpointing

        Returns:
            Final workflow state

        Raises:
            ValueError: If start node not found
            asyncio.TimeoutError: If execution exceeds timeout
        """
        # Initialize
        state = initial_state or WorkflowState()
        current = start_node or self.start_node

        if not current:
            raise ValueError("No start node defined")

        if current not in self.nodes:
            raise ValueError(f"Start node '{current}' not found")

        # Set metadata
        state.metadata['graph_id'] = self.graph_id
        state.metadata['start_time'] = time.time()

        # Execute with optional timeout
        async def _execute():
            nonlocal current, state

            # Import here to avoid circular dependency
            if checkpoint_manager:
                from src.checkpoint import CheckpointStatus

            while current not in self.end_nodes:
                # Execute current node
                node = self.nodes[current]
                state = await node.execute(state)

                # Check for errors
                if state.get('error'):
                    print(f"❌ Error in node '{current}': {state.get('error')}")
                    break

                # Save checkpoint after each node if enabled
                if checkpoint_manager and execution_id:
                    # Check if should checkpoint based on interval
                    if await checkpoint_manager.should_checkpoint(execution_id):
                        # Find pending nodes (remaining nodes in graph)
                        pending = [
                            nid for nid in self.nodes.keys()
                            if nid not in state.history and nid not in self.end_nodes
                        ]

                        await checkpoint_manager.create_checkpoint(
                            execution_id=execution_id,
                            status=CheckpointStatus.RUNNING,
                            current_node=current,
                            completed_nodes=state.history.copy(),
                            pending_nodes=pending,
                            workflow_state=state.data.copy(),
                            metadata={'graph_id': self.graph_id}
                        )

                # Find next nodes
                next_nodes = self._find_next_nodes(current, state)

                if not next_nodes:
                    print(f"⚠️  No next nodes from '{current}', ending workflow")
                    break

                # Handle parallel execution
                if len(next_nodes) > 1:
                    # Execute all branches in parallel
                    branch_states = await asyncio.gather(*[
                        self._execute_branch(node_id, state.copy())
                        for node_id in next_nodes
                    ])

                    # Merge results (simple merge - last write wins)
                    for branch_state in branch_states:
                        state.update(branch_state.data)

                    # Continue from first branch's end point
                    # (This is simplified - in production you'd handle joins properly)
                    break

                # Single next node
                current = next_nodes[0]

            # Record end time
            state.metadata['end_time'] = time.time()
            state.metadata['duration'] = state.metadata['end_time'] - state.metadata['start_time']

            return state

        if timeout:
            return await asyncio.wait_for(_execute(), timeout=timeout)
        else:
            return await _execute()

    async def _execute_branch(
        self,
        start_node: str,
        state: WorkflowState
    ) -> WorkflowState:
        """
        Execute a branch starting from a node

        Args:
            start_node: Node to start from
            state: Branch state

        Returns:
            Final branch state
        """
        current = start_node

        while current not in self.end_nodes:
            # Execute node
            node = self.nodes[current]
            state = await node.execute(state)

            # Find next
            next_nodes = self._find_next_nodes(current, state)

            if not next_nodes or len(next_nodes) > 1:
                break  # End branch or nested parallel

            current = next_nodes[0]

        return state

    def visualize(self) -> str:
        """
        Generate Graphviz DOT representation

        Returns:
            DOT format string
        """
        dot = [f'digraph {self.graph_id} {{']
        dot.append('  rankdir=TB;')
        dot.append('  node [shape=box, style=rounded];')

        # Add nodes
        for node_id, node in self.nodes.items():
            shape = "ellipse" if node.node_type in [NodeType.START, NodeType.END] else "box"
            color = "green" if node.node_type == NodeType.START else "red" if node.node_type == NodeType.END else "lightblue"
            dot.append(f'  "{node_id}" [shape={shape}, fillcolor={color}, style=filled];')

        # Add edges
        for edge in self.edges:
            label = edge.label or ""
            style = "dashed" if edge.edge_type == EdgeType.CONDITIONAL else "solid"
            style = "dotted" if edge.edge_type == EdgeType.LOOP_BACK else style
            dot.append(f'  "{edge.from_node}" -> "{edge.to_node}" [label="{label}", style={style}];')

        dot.append('}')
        return '\n'.join(dot)

    def get_execution_path(self, state: WorkflowState) -> List[str]:
        """
        Get execution path from state history

        Args:
            state: Workflow state with history

        Returns:
            List of node IDs in execution order
        """
        return state.history.copy()

    def validate(self) -> List[str]:
        """
        Validate graph structure

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check for start node
        if not self.start_node:
            issues.append("No START node defined")

        # Check for end nodes
        if not self.end_nodes:
            issues.append("No END nodes defined")

        # Check for unreachable nodes
        reachable = self._find_reachable_nodes()
        unreachable = set(self.nodes.keys()) - reachable
        if unreachable:
            issues.append(f"Unreachable nodes: {unreachable}")

        # Check for dead ends (nodes with no outgoing edges, except END)
        for node_id in self.nodes:
            if node_id not in self.end_nodes:
                outgoing = [e for e in self.edges if e.from_node == node_id]
                if not outgoing:
                    issues.append(f"Dead end node: {node_id}")

        return issues

    def _find_reachable_nodes(self) -> Set[str]:
        """Find all reachable nodes from start"""
        if not self.start_node:
            return set()

        reachable = set()
        queue = [self.start_node]

        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue

            reachable.add(current)

            # Add neighbors
            for edge in self.edges:
                if edge.from_node == current and edge.to_node not in reachable:
                    queue.append(edge.to_node)

        return reachable


# Utility functions

def create_simple_workflow(
    tasks: List[Callable],
    task_ids: Optional[List[str]] = None
) -> WorkflowGraph:
    """
    Create a simple sequential workflow from tasks

    Args:
        tasks: List of async task functions
        task_ids: Optional custom task IDs

    Returns:
        WorkflowGraph with linear execution

    Example:
        >>> graph = create_simple_workflow([task1, task2, task3])
    """
    graph = WorkflowGraph()

    # Add start and end
    graph.add_node(WorkflowNode("start", NodeType.START))
    graph.add_node(WorkflowNode("end", NodeType.END))

    # Add tasks
    if not task_ids:
        task_ids = [f"task{i+1}" for i in range(len(tasks))]

    for task_id, task_func in zip(task_ids, tasks):
        graph.add_node(WorkflowNode(task_id, NodeType.TASK, handler=task_func))

    # Chain tasks
    prev = "start"
    for task_id in task_ids:
        graph.add_edge(WorkflowEdge(prev, task_id))
        prev = task_id

    graph.add_edge(WorkflowEdge(prev, "end"))

    return graph
