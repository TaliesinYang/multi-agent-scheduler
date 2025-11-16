"""
MetaAgent - Dynamic Prompt Generation System

MetaAgent analyzes tasks and generates appropriate prompts for SubAgents.
Architecture:
- MetaAgent (fixed): Task analysis + Prompt generation
- SubAgents (dynamic): Execute tasks with generated prompts
- SummaryAgent (generated): Aggregate all results

Features:
- Automatic complexity analysis
- Template-based prompt generation
- Summary task creation
- Upstream context injection

Example:
    >>> from meta_agent import MetaAgent
    >>> meta = MetaAgent()
    >>> enhanced_tasks = meta.process_tasks(tasks)
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from scheduler import Task

# Use relative imports
try:
    from .complexity_analyzer import ComplexityAnalyzer, ComplexityAnalysis
    from .prompt_templates import PromptTemplateLibrary
except ImportError:
    from complexity_analyzer import ComplexityAnalyzer, ComplexityAnalysis
    from prompt_templates import PromptTemplateLibrary


@dataclass
class EnhancedTask:
    """
    Task with MetaAgent-generated prompt

    Attributes:
        original_task: Original task from loader
        generated_prompt: Dynamically generated prompt
        complexity: Complexity analysis result
        template_used: Template type used
    """
    original_task: 'Task'
    generated_prompt: str
    complexity: ComplexityAnalysis
    template_used: str


class MetaAgent:
    """
    Meta-level agent for task planning and prompt generation

    Responsibilities:
    1. Analyze task complexity
    2. Select appropriate prompt template
    3. Generate concrete prompts for SubAgents
    4. Create summary task for final aggregation

    Example:
        >>> meta = MetaAgent()
        >>> tasks = [task1, task2, task3]
        >>> enhanced_tasks = meta.process_tasks(tasks, input_mappings)
        >>> # Now execute enhanced_tasks with DAGScheduler
    """

    def __init__(
        self,
        analyzer: Optional[ComplexityAnalyzer] = None,
        template_library: Optional[PromptTemplateLibrary] = None,
        verbose: bool = True
    ):
        """
        Initialize MetaAgent

        Args:
            analyzer: Custom complexity analyzer (optional)
            template_library: Custom template library (optional)
            verbose: Print analysis details
        """
        self.analyzer = analyzer or ComplexityAnalyzer()
        self.template_library = template_library or PromptTemplateLibrary()
        self.verbose = verbose

    def process_tasks(
        self,
        tasks: List['Task'],
        input_mappings: Optional[Dict[str, Dict[str, str]]] = None,
        add_summary: bool = True
    ) -> List['Task']:
        """
        Process tasks with MetaAgent

        Main workflow:
        1. Analyze each task's complexity
        2. Select appropriate template
        3. Generate dynamic prompt
        4. Optionally add summary task

        Args:
            tasks: List of tasks to process
            input_mappings: Dependency injection mappings (optional)
            add_summary: Whether to add final summary task

        Returns:
            List of tasks with generated prompts

        Example:
            >>> tasks = loader.load_all_tasks()
            >>> enhanced_tasks = meta.process_tasks(tasks)
        """
        if self.verbose:
            print(f"\n🤖 [META AGENT] Processing {len(tasks)} tasks")

        enhanced_tasks = []

        for task in tasks:
            # Step 1: Analyze complexity
            complexity = self.analyzer.analyze(task)

            if self.verbose:
                print(f"  📊 {task.id}: {complexity.complexity} (score: {complexity.score})")
                print(f"      {complexity.reasoning}")

            # Step 2: Generate prompt
            generated_prompt = self._generate_prompt_for_task(
                task,
                complexity,
                input_mappings
            )

            # Step 3: Create enhanced task with new prompt
            # Update task's prompt in-place
            task.prompt = generated_prompt

            # Store metadata
            if not hasattr(task, 'metadata'):
                task.metadata = {}

            task.metadata.update({
                "meta_agent_processed": True,
                "complexity": complexity.complexity,
                "complexity_score": complexity.score,
                "template_used": complexity.template_type,
                "original_prompt": task.prompt if not hasattr(task, 'original_prompt') else task.original_prompt
            })

            enhanced_tasks.append(task)

        # Step 4: Optionally add summary task
        if add_summary and len(enhanced_tasks) > 1:
            summary_task = self._create_summary_task(enhanced_tasks)
            enhanced_tasks.append(summary_task)

            if self.verbose:
                print(f"\n  ➕ Added summary task: {summary_task.id}")

        if self.verbose:
            print(f"\n✅ Meta Agent processing complete: {len(enhanced_tasks)} tasks ready\n")

        return enhanced_tasks

    def _generate_prompt_for_task(
        self,
        task: 'Task',
        complexity: ComplexityAnalysis,
        input_mappings: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """
        Generate prompt for a single task

        Args:
            task: Task to generate prompt for
            complexity: Complexity analysis result
            input_mappings: Dependency mappings

        Returns:
            Generated prompt string
        """
        template_type = complexity.template_type

        # Prepare template variables
        template_vars = {
            "description": task.prompt
        }

        # For complex tasks, prepare upstream context placeholder
        if template_type == "complex" and task.depends_on:
            # Add placeholder for dependency injection
            # Actual injection happens in DependencyInjector
            upstream_context = self._prepare_upstream_context_placeholder(
                task,
                input_mappings
            )
            template_vars["upstream_context"] = upstream_context

        # Generate prompt from template
        prompt = self.template_library.generate_prompt(
            template_type,
            **template_vars
        )

        return prompt

    def _prepare_upstream_context_placeholder(
        self,
        task: 'Task',
        input_mappings: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """
        Prepare placeholder text for upstream context

        Note: Actual data injection happens later in DependencyInjector.
        This just provides the structure.

        Args:
            task: Task with dependencies
            input_mappings: Input mapping specifications

        Returns:
            Placeholder text for context section
        """
        if not input_mappings or task.id not in input_mappings:
            return "Dependencies: " + ", ".join(task.depends_on)

        # Show what data will be injected
        mapping = input_mappings[task.id]
        context_lines = []

        for param_name, path_expr in mapping.items():
            context_lines.append(f"- {param_name}: {{{param_name}}} (from {path_expr})")

        return "\n".join(context_lines)

    def _create_summary_task(self, tasks: List['Task']) -> 'Task':
        """
        Create summary task that aggregates all results

        Strategy:
        - Depends on all leaf tasks (tasks with no downstream dependencies)
        - Uses summary template
        - Aggregates results into final answer

        Args:
            tasks: List of all tasks

        Returns:
            Summary task
        """
        # Find leaf tasks (no other tasks depend on them)
        all_task_ids = {t.id for t in tasks}
        has_downstream = set()

        for task in tasks:
            has_downstream.update(task.depends_on)

        leaf_task_ids = all_task_ids - has_downstream

        # Create mock Task object for summary
        # Import Task class
        try:
            from scheduler import Task
        except ImportError:
            # Fallback: create simple dict-like object
            class Task:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)

        # Generate summary prompt
        summary_prompt = self.template_library.generate_prompt(
            "summary",
            all_task_results="[Results will be injected by DependencyInjector]"
        )

        summary_task = Task(
            id="final_summary",
            prompt=summary_prompt,
            depends_on=list(leaf_task_ids),
            type="summary",
            metadata={
                "is_summary": True,
                "meta_agent_generated": True,
                "template_used": "summary"
            }
        )

        return summary_task


# Convenience function
def enhance_tasks_with_meta_agent(
    tasks: List['Task'],
    input_mappings: Optional[Dict[str, Dict[str, str]]] = None,
    add_summary: bool = True,
    verbose: bool = True
) -> List['Task']:
    """
    Quick task enhancement with MetaAgent (convenience function)

    Args:
        tasks: Tasks to enhance
        input_mappings: Dependency mappings
        add_summary: Add summary task
        verbose: Print details

    Returns:
        Enhanced tasks

    Example:
        >>> enhanced_tasks = enhance_tasks_with_meta_agent(tasks)
    """
    meta = MetaAgent(verbose=verbose)
    return meta.process_tasks(tasks, input_mappings, add_summary)


# Example usage
if __name__ == "__main__":
    # Mock Task class for testing
    class MockTask:
        def __init__(self, id, prompt, depends_on=None, type="os"):
            self.id = id
            self.prompt = prompt
            self.depends_on = depends_on or []
            self.type = type
            self.metadata = {}

    # Create test tasks
    task1 = MockTask(
        id="task1",
        prompt="List all users in /etc/passwd",
        depends_on=[],
        type="os"
    )

    task2 = MockTask(
        id="task2",
        prompt="Count files in user's home directory",
        depends_on=["task1"],
        type="os"
    )

    task3 = MockTask(
        id="task3",
        prompt="SELECT product_id FROM products WHERE sales > 1000",
        depends_on=[],
        type="database"
    )

    tasks = [task1, task2, task3]

    # Process with MetaAgent
    meta = MetaAgent(verbose=True)
    enhanced_tasks = meta.process_tasks(tasks, add_summary=True)

    print("\n=== ENHANCED TASKS ===\n")
    for task in enhanced_tasks:
        print(f"Task: {task.id}")
        print(f"Complexity: {task.metadata.get('complexity', 'N/A')}")
        print(f"Template: {task.metadata.get('template_used', 'N/A')}")
        print(f"Prompt preview: {task.prompt[:100]}...\n")
