"""
AgentBench Dependency Task Loader

Loads dependency task groups from AgentBench/dependency_tasks.json
and converts them to Task objects for DAG execution with dependency injection.

Features:
- Loads manually annotated dependency task groups
- Preserves input_mapping for dependency injection
- Supports group-based task execution
- Compatible with DAGScheduler + DependencyInjector

Example:
    >>> from orchestration import AgentBenchLoader
    >>>
    >>> loader = AgentBenchLoader("AgentBench/dependency_tasks.json")
    >>> groups = loader.load_all_groups()
    >>>
    >>> # Execute one group
    >>> group = groups[0]
    >>> tasks = loader.get_group_tasks("os_user_analysis")
    >>> input_mappings = loader.get_input_mappings("os_user_analysis")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Use absolute import for compatibility
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scheduler import Task
except ImportError:
    from scheduler import Task


@dataclass
class TaskGroup:
    """A group of dependent tasks"""
    group_id: str
    description: str
    tasks: List[Task]
    input_mappings: Dict[str, Dict[str, str]]  # task_id -> {param: path_expr}
    metadata: Dict[str, Any]


class AgentBenchLoader:
    """
    Loader for AgentBench dependency task groups

    Reads dependency_tasks.json and converts to Task objects with
    input_mapping preservation for dependency injection.

    Example:
        >>> loader = AgentBenchLoader()
        >>>
        >>> # Load all groups
        >>> groups = loader.load_all_groups()
        >>> print(f"Loaded {len(groups)} task groups")
        >>>
        >>> # Get specific group
        >>> tasks = loader.get_group_tasks("os_user_analysis")
        >>> mappings = loader.get_input_mappings("os_user_analysis")
        >>>
        >>> # Execute with DAGScheduler
        >>> from orchestration import DAGScheduler, CLIExecutor
        >>> scheduler = DAGScheduler(CLIExecutor())
        >>> result = await scheduler.execute_dag(
        ...     tasks=tasks,
        ...     input_mappings=mappings
        ... )
    """

    def __init__(self, json_path: Optional[str] = None):
        """
        Initialize AgentBench loader

        Args:
            json_path: Path to dependency_tasks.json
                      Defaults to "AgentBench/dependency_tasks.json"
        """
        if json_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            json_path = project_root / "AgentBench" / "dependency_tasks.json"

        self.json_path = Path(json_path)
        self.data = None
        self.groups = {}  # group_id -> TaskGroup

    def load(self) -> Dict[str, Any]:
        """
        Load JSON data from file

        Returns:
            Dictionary containing metadata and groups

        Raises:
            FileNotFoundError: If JSON file not found
            json.JSONDecodeError: If JSON is invalid
        """
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"Dependency tasks file not found: {self.json_path}\n"
                f"Expected location: AgentBench/dependency_tasks.json"
            )

        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        return self.data

    def load_all_groups(self) -> List[TaskGroup]:
        """
        Load all task groups from JSON

        Returns:
            List of TaskGroup objects

        Example:
            >>> loader = AgentBenchLoader()
            >>> groups = loader.load_all_groups()
            >>> for group in groups:
            ...     print(f"{group.group_id}: {len(group.tasks)} tasks")
        """
        if self.data is None:
            self.load()

        groups = []

        for group_data in self.data.get("groups", []):
            group = self._parse_group(group_data)
            self.groups[group.group_id] = group
            groups.append(group)

        return groups

    def _parse_group(self, group_data: Dict[str, Any]) -> TaskGroup:
        """
        Parse a single task group from JSON

        Args:
            group_data: Dictionary containing group data

        Returns:
            TaskGroup object
        """
        group_id = group_data["group_id"]
        description = group_data["description"]

        tasks = []
        input_mappings = {}

        for task_data in group_data.get("tasks", []):
            # Create Task object
            task = Task(
                id=task_data["id"],
                prompt=task_data["prompt"],
                depends_on=task_data.get("depends_on", []),
                metadata={
                    "description": task_data.get("description", ""),
                    "output_schema": task_data.get("output_schema", {}),
                    "type": task_data.get("type", "unknown")
                }
            )
            tasks.append(task)

            # Store input_mapping if present
            if "input_mapping" in task_data:
                input_mappings[task.id] = task_data["input_mapping"]

        return TaskGroup(
            group_id=group_id,
            description=description,
            tasks=tasks,
            input_mappings=input_mappings,
            metadata={
                "task_count": len(tasks),
                "dependency_count": sum(len(t.depends_on) for t in tasks)
            }
        )

    def get_group(self, group_id: str) -> Optional[TaskGroup]:
        """
        Get a specific task group by ID

        Args:
            group_id: Group identifier

        Returns:
            TaskGroup object or None if not found
        """
        if not self.groups:
            self.load_all_groups()

        return self.groups.get(group_id)

    def get_group_tasks(self, group_id: str) -> List[Task]:
        """
        Get tasks for a specific group

        Args:
            group_id: Group identifier

        Returns:
            List of Task objects

        Raises:
            KeyError: If group not found
        """
        group = self.get_group(group_id)
        if group is None:
            available = list(self.groups.keys())
            raise KeyError(
                f"Group '{group_id}' not found. "
                f"Available groups: {available}"
            )

        return group.tasks

    def get_input_mappings(self, group_id: str) -> Dict[str, Dict[str, str]]:
        """
        Get input mappings for a specific group

        Args:
            group_id: Group identifier

        Returns:
            Dictionary mapping task_id -> {param_name: path_expression}

        Example:
            >>> mappings = loader.get_input_mappings("os_user_analysis")
            >>> # mappings = {
            >>> #     "os_dep_1b": {"target_user": "os_dep_1a.users[0]"},
            >>> #     "os_dep_1c": {"file_count": "os_dep_1b.count"}
            >>> # }
        """
        group = self.get_group(group_id)
        if group is None:
            raise KeyError(f"Group '{group_id}' not found")

        return group.input_mappings

    def list_groups(self) -> List[Tuple[str, str, int]]:
        """
        List all available groups

        Returns:
            List of tuples (group_id, description, task_count)

        Example:
            >>> loader = AgentBenchLoader()
            >>> for group_id, desc, count in loader.list_groups():
            ...     print(f"{group_id}: {desc} ({count} tasks)")
        """
        if not self.groups:
            self.load_all_groups()

        return [
            (gid, group.description, len(group.tasks))
            for gid, group in self.groups.items()
        ]

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata from JSON file

        Returns:
            Dictionary containing version, description, totals, etc.
        """
        if self.data is None:
            self.load()

        return self.data.get("metadata", {})

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded task groups

        Returns:
            Dictionary with statistics:
            - total_groups: Number of groups
            - total_tasks: Total tasks across all groups
            - total_dependencies: Total dependency edges
            - avg_tasks_per_group: Average tasks per group
            - groups_by_type: Count of OS vs DB groups
        """
        if not self.groups:
            self.load_all_groups()

        total_tasks = sum(len(g.tasks) for g in self.groups.values())
        total_deps = sum(
            len(task.depends_on)
            for group in self.groups.values()
            for task in group.tasks
        )

        # Count by type
        type_counts = {}
        for group in self.groups.values():
            for task in group.tasks:
                task_type = task.metadata.get("type", "unknown")
                type_counts[task_type] = type_counts.get(task_type, 0) + 1

        return {
            "total_groups": len(self.groups),
            "total_tasks": total_tasks,
            "total_dependencies": total_deps,
            "avg_tasks_per_group": total_tasks / len(self.groups) if self.groups else 0,
            "tasks_by_type": type_counts,
            "avg_dependencies_per_task": total_deps / total_tasks if total_tasks > 0 else 0
        }


# Convenience function
def load_dependency_groups(json_path: Optional[str] = None) -> List[TaskGroup]:
    """
    Quick load all dependency task groups

    Args:
        json_path: Optional path to JSON file

    Returns:
        List of TaskGroup objects

    Example:
        >>> from orchestration import load_dependency_groups
        >>> groups = load_dependency_groups()
        >>> print(f"Loaded {len(groups)} groups")
    """
    loader = AgentBenchLoader(json_path)
    return loader.load_all_groups()


if __name__ == "__main__":
    # Test the loader
    print("Testing AgentBench Dependency Task Loader")
    print("=" * 60)

    try:
        loader = AgentBenchLoader()

        # Load all groups
        groups = loader.load_all_groups()
        print(f"\n✓ Loaded {len(groups)} task groups")

        # Show statistics
        stats = loader.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  Total dependencies: {stats['total_dependencies']}")
        print(f"  Avg tasks/group: {stats['avg_tasks_per_group']:.1f}")
        print(f"  Avg deps/task: {stats['avg_dependencies_per_task']:.1f}")
        print(f"  Tasks by type: {stats['tasks_by_type']}")

        # List groups
        print(f"\n📋 Available groups:")
        for group_id, desc, count in loader.list_groups():
            print(f"  - {group_id}: {desc} ({count} tasks)")

        # Test loading one group
        print(f"\n🧪 Testing first group:")
        first_group = groups[0]
        print(f"  Group: {first_group.group_id}")
        print(f"  Description: {first_group.description}")
        print(f"  Tasks: {len(first_group.tasks)}")

        for task in first_group.tasks:
            deps = f" (depends on: {', '.join(task.depends_on)})" if task.depends_on else ""
            print(f"    - {task.id}: {task.metadata.get('description', '')}{deps}")

        print(f"\n  Input mappings:")
        for task_id, mapping in first_group.input_mappings.items():
            print(f"    {task_id}:")
            for param, path in mapping.items():
                print(f"      {param} <- {path}")

        print("\n✅ Loader test successful!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
