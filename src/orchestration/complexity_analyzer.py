"""
Task Complexity Analyzer

Analyzes task complexity using multiple criteria to determine
the appropriate prompt template.

Criteria (user-suggested):
1. Dependency count (has dependencies = complex)
2. Task type (database queries = complex)
3. Prompt length (>100 characters = complex)
4. Optional: AI-powered analysis for edge cases

Features:
- Rule-based scoring system
- Configurable complexity thresholds
- Detailed reasoning output

Example:
    >>> from complexity_analyzer import ComplexityAnalyzer
    >>> analyzer = ComplexityAnalyzer()
    >>> result = analyzer.analyze(task)
    >>> print(result["complexity"])  # "simple" or "complex"
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from scheduler import Task


@dataclass
class ComplexityAnalysis:
    """
    Result of complexity analysis

    Attributes:
        complexity: "simple" or "complex"
        score: Numeric complexity score (0-100)
        template_type: Recommended template ("simple", "complex", "summary")
        reasoning: Explanation of the decision
        criteria_breakdown: Individual criterion scores
    """
    complexity: str  # "simple" or "complex"
    score: int  # 0-100
    template_type: str  # "simple", "complex", or "summary"
    reasoning: str
    criteria_breakdown: Dict[str, Any]


class ComplexityAnalyzer:
    """
    Rule-based task complexity analyzer

    Uses multiple criteria to assess task complexity and recommend
    appropriate prompt template.

    Scoring system:
    - 0-30: Simple (use simple template)
    - 31-100: Complex (use complex template)
    """

    # Default weights for each criterion
    DEFAULT_WEIGHTS = {
        "dependency_count": 25,  # Has dependencies -> +25 points
        "task_type": 30,         # Database task -> +30 points
        "prompt_length": 20,     # >100 chars -> +20 points
        "keywords": 25           # Complex keywords -> +25 points
    }

    # Keywords indicating complexity
    COMPLEX_KEYWORDS = {
        "database", "SELECT", "INSERT", "UPDATE", "DELETE",
        "query", "transaction", "join", "aggregate",
        "analyze", "calculate", "process", "transform"
    }

    def __init__(
        self,
        threshold: int = 30,
        weights: Optional[Dict[str, int]] = None
    ):
        """
        Initialize complexity analyzer

        Args:
            threshold: Complexity threshold (default: 30)
                      Score >= threshold -> complex
            weights: Custom weights for criteria (optional)
        """
        self.threshold = threshold
        self.weights = weights or self.DEFAULT_WEIGHTS

    def analyze(self, task: 'Task') -> ComplexityAnalysis:
        """
        Analyze task complexity

        Args:
            task: Task to analyze

        Returns:
            ComplexityAnalysis with results

        Example:
            >>> task = Task(
            ...     id="task1",
            ...     prompt="SELECT * FROM users WHERE id = 1",
            ...     depends_on=["task0"],
            ...     type="database"
            ... )
            >>> result = analyzer.analyze(task)
            >>> print(result.complexity)  # "complex"
        """
        # Calculate individual criterion scores
        criteria = {}

        # Criterion 1: Dependency count
        dependency_score = self._score_dependencies(task)
        criteria["dependency_count"] = {
            "score": dependency_score,
            "has_dependencies": len(task.depends_on) > 0,
            "count": len(task.depends_on)
        }

        # Criterion 2: Task type
        task_type_score = self._score_task_type(task)
        criteria["task_type"] = {
            "score": task_type_score,
            "type": getattr(task, 'type', 'unknown'),
            "is_database": getattr(task, 'type', '') == 'database'
        }

        # Criterion 3: Prompt length
        prompt_length_score = self._score_prompt_length(task)
        criteria["prompt_length"] = {
            "score": prompt_length_score,
            "length": len(task.prompt),
            "exceeds_threshold": len(task.prompt) > 100
        }

        # Criterion 4: Complex keywords
        keyword_score = self._score_keywords(task)
        criteria["keywords"] = {
            "score": keyword_score,
            "found_keywords": self._find_complex_keywords(task.prompt)
        }

        # Calculate total score
        total_score = sum(c["score"] for c in criteria.values())

        # Determine complexity
        complexity = "complex" if total_score >= self.threshold else "simple"
        template_type = complexity

        # Generate reasoning
        reasoning = self._generate_reasoning(complexity, total_score, criteria)

        return ComplexityAnalysis(
            complexity=complexity,
            score=total_score,
            template_type=template_type,
            reasoning=reasoning,
            criteria_breakdown=criteria
        )

    def _score_dependencies(self, task: 'Task') -> int:
        """
        Score based on dependency count

        Logic:
        - Has dependencies -> full weight (complex)
        - No dependencies -> 0 (simple)
        """
        if task.depends_on and len(task.depends_on) > 0:
            return self.weights["dependency_count"]
        return 0

    def _score_task_type(self, task: 'Task') -> int:
        """
        Score based on task type

        Logic:
        - Database tasks -> full weight (complex)
        - OS tasks -> 0 (simple)
        """
        task_type = getattr(task, 'type', '').lower()

        if task_type == 'database':
            return self.weights["task_type"]

        return 0

    def _score_prompt_length(self, task: 'Task') -> int:
        """
        Score based on prompt length

        Logic:
        - >150 chars -> full weight
        - 100-150 chars -> half weight
        - <100 chars -> 0
        """
        length = len(task.prompt)

        if length > 150:
            return self.weights["prompt_length"]
        elif length > 100:
            return self.weights["prompt_length"] // 2

        return 0

    def _score_keywords(self, task: 'Task') -> int:
        """
        Score based on presence of complex keywords

        Logic:
        - Contains complex keywords -> full weight
        - No complex keywords -> 0
        """
        keywords = self._find_complex_keywords(task.prompt)

        if keywords:
            return self.weights["keywords"]

        return 0

    def _find_complex_keywords(self, text: str) -> list:
        """Find complex keywords in text"""
        text_lower = text.lower()
        found = []

        for keyword in self.COMPLEX_KEYWORDS:
            if keyword.lower() in text_lower:
                found.append(keyword)

        return found

    def _generate_reasoning(
        self,
        complexity: str,
        score: int,
        criteria: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable reasoning

        Args:
            complexity: Determined complexity level
            score: Total score
            criteria: Breakdown of criteria

        Returns:
            Reasoning string
        """
        reasons = []

        # Dependency analysis
        if criteria["dependency_count"]["has_dependencies"]:
            count = criteria["dependency_count"]["count"]
            reasons.append(f"has {count} dependencies")

        # Task type analysis
        if criteria["task_type"]["is_database"]:
            reasons.append("database query task")

        # Prompt length analysis
        if criteria["prompt_length"]["exceeds_threshold"]:
            length = criteria["prompt_length"]["length"]
            reasons.append(f"long prompt ({length} chars)")

        # Keyword analysis
        keywords = criteria["keywords"]["found_keywords"]
        if keywords:
            reasons.append(f"contains complex keywords: {', '.join(keywords[:3])}")

        if not reasons:
            reasons.append("simple task with no complexity indicators")

        reason_str = ", ".join(reasons)

        return (
            f"Classified as '{complexity}' (score: {score}/{100}). "
            f"Reasons: {reason_str}."
        )


# Convenience function
def analyze_task(task: 'Task') -> ComplexityAnalysis:
    """
    Quick task complexity analysis (convenience function)

    Args:
        task: Task to analyze

    Returns:
        ComplexityAnalysis result

    Example:
        >>> result = analyze_task(my_task)
        >>> print(result.template_type)
    """
    analyzer = ComplexityAnalyzer()
    return analyzer.analyze(task)


# Example usage
if __name__ == "__main__":
    # Mock Task class for testing
    class MockTask:
        def __init__(self, id, prompt, depends_on=None, type="os"):
            self.id = id
            self.prompt = prompt
            self.depends_on = depends_on or []
            self.type = type

    analyzer = ComplexityAnalyzer()

    # Example 1: Simple task
    simple_task = MockTask(
        id="task1",
        prompt="List all users",
        depends_on=[],
        type="os"
    )
    result1 = analyzer.analyze(simple_task)
    print(f"Task 1: {result1.complexity} (score: {result1.score})")
    print(f"  Reasoning: {result1.reasoning}\n")

    # Example 2: Complex task (has dependencies)
    complex_task1 = MockTask(
        id="task2",
        prompt="Count files in user's home directory",
        depends_on=["task1"],
        type="os"
    )
    result2 = analyzer.analyze(complex_task1)
    print(f"Task 2: {result2.complexity} (score: {result2.score})")
    print(f"  Reasoning: {result2.reasoning}\n")

    # Example 3: Complex task (database)
    complex_task2 = MockTask(
        id="task3",
        prompt="SELECT product_id, product_name FROM products WHERE sales > 1000. Return the list of product IDs.",
        depends_on=[],
        type="database"
    )
    result3 = analyzer.analyze(complex_task2)
    print(f"Task 3: {result3.complexity} (score: {result3.score})")
    print(f"  Reasoning: {result3.reasoning}\n")

    # Example 4: Very complex task (all factors)
    very_complex_task = MockTask(
        id="task4",
        prompt="SELECT AVG(rating) as avg_rating FROM reviews WHERE product_id IN ({product_ids}). Calculate the average rating for all products with high sales.",
        depends_on=["task3"],
        type="database"
    )
    result4 = analyzer.analyze(very_complex_task)
    print(f"Task 4: {result4.complexity} (score: {result4.score})")
    print(f"  Reasoning: {result4.reasoning}")
