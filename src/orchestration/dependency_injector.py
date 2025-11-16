"""
Dependency Injection Module

Enables task output → input passing for complex workflows.
Supports path expressions like "task_a.users[0]" to extract data from upstream tasks.

Features:
- JSONPath-style data extraction from upstream task outputs
- Automatic prompt enhancement with dependency context
- Type-safe data passing with validation
- Support for nested structures and array indexing

Example:
    >>> from orchestration import DependencyInjector
    >>> from orchestration.executor import TaskResult
    >>>
    >>> # Upstream task result
    >>> task_a_result = TaskResult(
    ...     task_id="task_a",
    ...     success=True,
    ...     output="Found 5 users",
    ...     parsed_data={"users": ["alice", "bob", "charlie"], "count": 3}
    ... )
    >>>
    >>> # Inject into downstream task
    >>> injector = DependencyInjector()
    >>> enhanced_prompt = injector.inject_dependencies(
    ...     task=task_b,
    ...     upstream_results={"task_a": task_a_result},
    ...     input_mapping={
    ...         "target_user": "task_a.users[0]",
    ...         "total_count": "task_a.count"
    ...     }
    ... )
    >>> # Result: Prompt includes target_user="alice", total_count=3
"""

import re
import json
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from scheduler import Task

# Use absolute import for compatibility
try:
    from .executor import TaskResult
except ImportError:
    from executor import TaskResult


class DependencyInjectionError(Exception):
    """Raised when dependency injection fails"""
    pass


class DependencyInjector:
    """
    Dependency injection for task workflows

    Extracts data from upstream task outputs and injects them into
    downstream task prompts using path expressions.

    Path expression syntax:
        - "task_id.field" - Extract field from task's parsed_data
        - "task_id.nested.field" - Nested field access
        - "task_id.array[0]" - Array indexing
        - "task_id.array[*]" - All array elements (returns list)

    Example:
        upstream_results = {
            "task_a": TaskResult(
                parsed_data={"users": ["alice", "bob"], "count": 2}
            )
        }

        input_mapping = {
            "first_user": "task_a.users[0]",
            "user_count": "task_a.count"
        }

        # Injects: first_user="alice", user_count=2
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize dependency injector

        Args:
            verbose: Whether to print debug information
        """
        self.verbose = verbose

    def inject_dependencies(
        self,
        task: 'Task',
        upstream_results: Dict[str, TaskResult],
        input_mapping: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Inject dependencies into task prompt

        Args:
            task: Target task to inject dependencies into
            upstream_results: Dict mapping task_id -> TaskResult
            input_mapping: Dict mapping parameter_name -> path_expression
                          e.g., {"user": "task_a.users[0]", "count": "task_a.count"}

        Returns:
            Enhanced prompt with injected dependency context

        Raises:
            DependencyInjectionError: If injection fails

        Example:
            >>> enhanced_prompt = injector.inject_dependencies(
            ...     task=task_b,
            ...     upstream_results={"task_a": result_a},
            ...     input_mapping={"target_user": "task_a.users[0]"}
            ... )
        """
        if not input_mapping:
            # No dependencies to inject
            return task.prompt

        # Extract dependency values
        injected_values = {}

        for param_name, path_expr in input_mapping.items():
            try:
                value = self._extract_value(path_expr, upstream_results)
                injected_values[param_name] = value

                if self.verbose:
                    print(f"  [DI] {param_name} = {value} (from {path_expr})")

            except Exception as e:
                raise DependencyInjectionError(
                    f"Failed to extract '{param_name}' from '{path_expr}': {e}"
                )

        # Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            task.prompt,
            injected_values,
            upstream_results
        )

        return enhanced_prompt

    def _extract_value(
        self,
        path_expr: str,
        upstream_results: Dict[str, TaskResult]
    ) -> Any:
        """
        Extract value using path expression

        Path syntax:
            - "task_id.field" - Simple field access
            - "task_id.nested.field" - Nested field
            - "task_id.array[0]" - Array index
            - "task_id.array[*]" - All array elements

        Args:
            path_expr: Path expression (e.g., "task_a.users[0]")
            upstream_results: Upstream task results

        Returns:
            Extracted value

        Raises:
            DependencyInjectionError: If extraction fails
        """
        # Parse path expression: "task_id.path.to.field[index]"
        match = re.match(r'^([a-zA-Z0-9_-]+)\.(.+)$', path_expr)
        if not match:
            raise DependencyInjectionError(
                f"Invalid path expression: '{path_expr}'. "
                f"Expected format: 'task_id.field' or 'task_id.field[index]'"
            )

        task_id = match.group(1)
        field_path = match.group(2)

        # Get upstream task result
        if task_id not in upstream_results:
            raise DependencyInjectionError(
                f"Task '{task_id}' not found in upstream results. "
                f"Available: {list(upstream_results.keys())}"
            )

        task_result = upstream_results[task_id]

        # Check if task succeeded
        if not task_result.success:
            raise DependencyInjectionError(
                f"Cannot extract from failed task '{task_id}'. "
                f"Error: {task_result.error}"
            )

        # Get parsed_data
        if not task_result.parsed_data:
            raise DependencyInjectionError(
                f"Task '{task_id}' has no parsed_data. "
                f"Ensure executor extracts structured data."
            )

        data = task_result.parsed_data

        # Navigate field path with array indexing support
        return self._navigate_path(data, field_path, path_expr)

    def _navigate_path(
        self,
        data: Any,
        field_path: str,
        original_expr: str
    ) -> Any:
        """
        Navigate through nested fields and arrays

        Supports:
            - "field" - Direct field access
            - "field.nested" - Nested fields
            - "array[0]" - Array indexing
            - "array[*]" - All array elements

        Args:
            data: Current data object
            field_path: Remaining path to navigate
            original_expr: Original path expression (for error messages)

        Returns:
            Extracted value

        Raises:
            DependencyInjectionError: If navigation fails
        """
        current = data
        parts = field_path.split('.')

        for part in parts:
            # Check for array indexing: "field[0]" or "field[*]"
            array_match = re.match(r'^(\w+)\[([0-9*]+)\]$', part)

            if array_match:
                # Array access
                field_name = array_match.group(1)
                index_str = array_match.group(2)

                # Get array field
                if not isinstance(current, dict) or field_name not in current:
                    raise DependencyInjectionError(
                        f"Field '{field_name}' not found in '{original_expr}'"
                    )

                array_value = current[field_name]

                if not isinstance(array_value, list):
                    raise DependencyInjectionError(
                        f"Field '{field_name}' is not an array in '{original_expr}'"
                    )

                # Handle index
                if index_str == '*':
                    # Return all elements
                    current = array_value
                else:
                    # Return specific index
                    index = int(index_str)
                    if index < 0 or index >= len(array_value):
                        raise DependencyInjectionError(
                            f"Array index {index} out of range for '{field_name}' "
                            f"(length: {len(array_value)}) in '{original_expr}'"
                        )
                    current = array_value[index]

            else:
                # Simple field access
                if not isinstance(current, dict) or part not in current:
                    raise DependencyInjectionError(
                        f"Field '{part}' not found in '{original_expr}'"
                    )
                current = current[part]

        return current

    def _build_enhanced_prompt(
        self,
        original_prompt: str,
        injected_values: Dict[str, Any],
        upstream_results: Dict[str, TaskResult]
    ) -> str:
        """
        Build enhanced prompt with dependency context

        Adds a "Context from upstream tasks" section containing:
        1. Injected parameter values
        2. Summary of upstream task outputs

        Args:
            original_prompt: Original task prompt
            injected_values: Extracted dependency values
            upstream_results: Upstream task results (for context)

        Returns:
            Enhanced prompt string

        Example output:
            === TASK PROMPT ===
            Find files owned by the specified user.

            === CONTEXT FROM UPSTREAM TASKS ===
            Injected parameters:
            - target_user: "alice"
            - user_count: 5

            Upstream task outputs:
            - task_a: Found 5 users in /etc/passwd

            === INSTRUCTIONS ===
            Use the injected parameters above to complete the task.
        """
        sections = []

        # Section 1: Task prompt
        sections.append("=== TASK PROMPT ===")
        sections.append(original_prompt)
        sections.append("")

        # Section 2: Dependency context
        sections.append("=== CONTEXT FROM UPSTREAM TASKS ===")

        # Injected parameters
        if injected_values:
            sections.append("Injected parameters:")
            for param_name, value in injected_values.items():
                # Format value as JSON for clarity
                value_str = json.dumps(value) if not isinstance(value, str) else f'"{value}"'
                sections.append(f"  - {param_name}: {value_str}")
            sections.append("")

        # Upstream outputs summary
        if upstream_results:
            sections.append("Upstream task outputs:")
            for task_id, result in upstream_results.items():
                if result.success:
                    output_preview = result.output[:100] + "..." if len(result.output) > 100 else result.output
                    sections.append(f"  - {task_id}: {output_preview}")
            sections.append("")

        # Section 3: Instructions
        sections.append("=== INSTRUCTIONS ===")
        sections.append("Use the injected parameters and upstream context to complete the task.")
        sections.append("Provide your final answer after completing all operations.")

        return "\n".join(sections)


# Convenience functions

def inject_task_dependencies(
    task: 'Task',
    upstream_results: Dict[str, TaskResult],
    input_mapping: Optional[Dict[str, str]] = None,
    verbose: bool = False
) -> str:
    """
    Quick dependency injection (convenience function)

    Args:
        task: Target task
        upstream_results: Upstream task results
        input_mapping: Parameter -> path mapping
        verbose: Debug output

    Returns:
        Enhanced prompt

    Example:
        >>> prompt = inject_task_dependencies(
        ...     task=task_b,
        ...     upstream_results={"task_a": result_a},
        ...     input_mapping={"user": "task_a.users[0]"}
        ... )
    """
    injector = DependencyInjector(verbose=verbose)
    return injector.inject_dependencies(task, upstream_results, input_mapping)


# TODO: Day 5 - Add support for conditional injection (if upstream task failed)
# TODO: Day 5 - Add data type validation against output_schema
# TODO: Day 6 - Integration with DAGScheduler for automatic injection
