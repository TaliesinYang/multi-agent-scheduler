"""
Prompt Template Library for MetaAgent

Provides different prompt templates for tasks of varying complexity.
MetaAgent selects appropriate template based on task analysis.

Features:
- SIMPLE: For straightforward tasks without dependencies
- COMPLEX: For tasks with upstream dependencies or database operations
- SUMMARY: For final result aggregation task

Example:
    >>> from prompt_templates import PromptTemplateLibrary
    >>> library = PromptTemplateLibrary()
    >>> template = library.get_template("simple")
    >>> prompt = template.format(description="List all users")
"""

from typing import Dict, Any
from string import Template


class PromptTemplateLibrary:
    """
    Library of prompt templates for different task complexity levels

    Templates use Python string.Template for safe substitution.
    """

    # Simple template for root tasks without dependencies
    SIMPLE_TEMPLATE = """$description

CRITICAL INSTRUCTIONS:
1. Execute this task directly using available tools (Bash, file operations, etc.)
2. Do NOT ask clarifying questions - this is an automated task
3. Do NOT analyze or explain - just execute and provide the answer
4. You MUST end your response with exactly: FINAL_ANSWER: [your answer]

Example response format:
[execution steps if needed]
FINAL_ANSWER: your_answer_here
"""

    # Complex template for tasks with dependencies
    COMPLEX_TEMPLATE = """$description

CONTEXT FROM UPSTREAM TASKS:
$upstream_context

CRITICAL INSTRUCTIONS:
1. Use the provided context data from upstream tasks
2. Execute this task directly using available tools
3. Do NOT ask questions - all necessary data is provided above
4. Do NOT analyze or explain unnecessarily
5. You MUST end your response with exactly: FINAL_ANSWER: [your answer]

Example response format:
[execution steps if needed]
FINAL_ANSWER: your_answer_here
"""

    # Summary template for final aggregation
    SUMMARY_TEMPLATE = """You are the Summary Agent responsible for aggregating all task results.

TASK RESULTS TO SUMMARIZE:
$all_task_results

YOUR TASK:
Provide a comprehensive summary that includes:
1. Key findings from each task group
2. Important data points and statistics
3. Overall insights and conclusions

CRITICAL INSTRUCTIONS:
- Aggregate all results into a coherent summary
- Do NOT execute any new tasks
- You MUST end your response with exactly: FINAL_ANSWER: [your summary]

Example response format:
Summary of all tasks:
- Task group 1: ...
- Task group 2: ...
- Insights: ...

FINAL_ANSWER: [comprehensive summary of all results]
"""

    def __init__(self):
        """Initialize template library"""
        self.templates = {
            "simple": Template(self.SIMPLE_TEMPLATE),
            "complex": Template(self.COMPLEX_TEMPLATE),
            "summary": Template(self.SUMMARY_TEMPLATE)
        }

    def get_template(self, template_type: str) -> Template:
        """
        Get template by type

        Args:
            template_type: One of "simple", "complex", "summary"

        Returns:
            Template object

        Raises:
            ValueError: If template_type not found
        """
        if template_type not in self.templates:
            raise ValueError(
                f"Unknown template type: {template_type}. "
                f"Available: {list(self.templates.keys())}"
            )

        return self.templates[template_type]

    def generate_prompt(
        self,
        template_type: str,
        **kwargs
    ) -> str:
        """
        Generate prompt from template

        Args:
            template_type: Type of template to use
            **kwargs: Template variables (description, upstream_context, etc.)

        Returns:
            Generated prompt string

        Example:
            >>> library = PromptTemplateLibrary()
            >>> prompt = library.generate_prompt(
            ...     "simple",
            ...     description="List all users in /etc/passwd"
            ... )
        """
        template = self.get_template(template_type)

        # Provide defaults for optional parameters
        defaults = {
            "description": "",
            "upstream_context": "No upstream context available",
            "all_task_results": "No results available"
        }

        # Merge provided kwargs with defaults
        template_vars = {**defaults, **kwargs}

        try:
            return template.substitute(**template_vars)
        except KeyError as e:
            raise ValueError(
                f"Missing required template variable: {e}. "
                f"Template '{template_type}' requires: {template_vars.keys()}"
            )

    def list_templates(self) -> Dict[str, str]:
        """
        List all available templates with descriptions

        Returns:
            Dictionary of template_type -> description
        """
        return {
            "simple": "For straightforward tasks without dependencies",
            "complex": "For tasks with upstream dependencies or complex operations",
            "summary": "For final result aggregation across all tasks"
        }


# Convenience function
def generate_prompt(template_type: str, **kwargs) -> str:
    """
    Quick prompt generation (convenience function)

    Args:
        template_type: Template to use ("simple", "complex", "summary")
        **kwargs: Template variables

    Returns:
        Generated prompt

    Example:
        >>> prompt = generate_prompt("simple", description="Count files")
    """
    library = PromptTemplateLibrary()
    return library.generate_prompt(template_type, **kwargs)


# Example usage
if __name__ == "__main__":
    library = PromptTemplateLibrary()

    # Example 1: Simple task
    simple_prompt = library.generate_prompt(
        "simple",
        description="Read /etc/passwd and extract all usernames"
    )
    print("=== SIMPLE TEMPLATE ===")
    print(simple_prompt)
    print()

    # Example 2: Complex task
    complex_prompt = library.generate_prompt(
        "complex",
        description="Count files in user's home directory",
        upstream_context="target_user: root (from task os_dep_1a)"
    )
    print("=== COMPLEX TEMPLATE ===")
    print(complex_prompt)
    print()

    # Example 3: Summary task
    summary_prompt = library.generate_prompt(
        "summary",
        all_task_results="""
Task os_dep_1a: Found 5 users
Task os_dep_1b: 42 files in /home/alex
Task os_dep_1c: Exceeds threshold
"""
    )
    print("=== SUMMARY TEMPLATE ===")
    print(summary_prompt)
