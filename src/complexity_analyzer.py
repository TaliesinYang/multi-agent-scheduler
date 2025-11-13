"""
Dynamic Complexity Analyzer

Analyzes task complexity to optimize decomposition parameters.
"""

import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ComplexityScore:
    """
    Complexity analysis result

    Attributes:
        score: Numerical complexity score (1-100)
        level: Complexity level (low/medium/high/very_high)
        recommended_subtasks: Recommended number of subtasks
        reasoning: Human-readable explanation
    """
    score: int
    level: str
    recommended_subtasks: int
    reasoning: str

    def should_decompose(self) -> bool:
        """Check if task should be decomposed"""
        return self.level in ['medium', 'high', 'very_high']


class ComplexityAnalyzer:
    """
    Analyzes task complexity using heuristics

    Features:
    - Keyword-based scoring
    - Size estimation
    - Component counting
    - Technology stack analysis

    Example:
        >>> analyzer = ComplexityAnalyzer()
        >>> score = analyzer.analyze("Build a REST API with authentication")
        >>> print(f"Complexity: {score.level}, Subtasks: {score.recommended_subtasks}")
        Complexity: high, Subtasks: 18
    """

    def __init__(self):
        """Initialize complexity analyzer with scoring rules"""

        # Keywords indicating complexity (keyword: score_weight)
        self.complexity_keywords = {
            # Architecture patterns
            'microservice': 15, 'distributed': 15, 'cloud': 10,
            'architecture': 10, 'system': 8, 'infrastructure': 12,

            # Database operations
            'database': 10, 'schema': 8, 'migration': 8,
            'sql': 6, 'nosql': 8, 'orm': 6,

            # Authentication & Security
            'authentication': 12, 'authorization': 10, 'security': 10,
            'oauth': 12, 'jwt': 8, 'encryption': 10,

            # Frontend complexity
            'frontend': 8, 'ui': 6, 'dashboard': 10,
            'responsive': 6, 'animation': 5, 'interface': 6,

            # Backend complexity
            'backend': 8, 'api': 8, 'rest': 6,
            'graphql': 10, 'websocket': 8, 'realtime': 10,

            # Testing & Quality
            'test': 5, 'testing': 5, 'integration': 6,
            'e2e': 8, 'ci/cd': 10, 'deployment': 8,

            # Advanced features
            'machine learning': 20, 'ai': 15, 'analytics': 10,
            'optimization': 8, 'performance': 6, 'caching': 6,

            # Complexity indicators
            'full-stack': 15, 'complete': 8, 'entire': 8,
            'comprehensive': 10, 'complex': 10, 'advanced': 8,
        }

        # Simple task indicators (negative score)
        self.simplicity_keywords = {
            'simple': -5, 'basic': -5, 'quick': -3,
            'small': -4, 'minor': -3, 'fix': -5,
            'update': -3, 'change': -3, 'modify': -3,
        }

        # Technology/component patterns (each counts as +5)
        self.component_patterns = [
            r'\b(?:react|vue|angular|svelte)\b',  # Frontend frameworks
            r'\b(?:node|express|django|flask|fastapi)\b',  # Backend frameworks
            r'\b(?:postgres|mysql|mongodb|redis)\b',  # Databases
            r'\b(?:docker|kubernetes|aws|gcp|azure)\b',  # Infrastructure
            r'\b(?:typescript|javascript|python|go|rust)\b',  # Languages
        ]

    def analyze(self, task_description: str) -> ComplexityScore:
        """
        Analyze task complexity

        Args:
            task_description: Task description to analyze

        Returns:
            ComplexityScore with analysis results
        """
        text_lower = task_description.lower()

        # Calculate base score
        score = 0
        reasoning_parts = []

        # 1. Keyword scoring
        keyword_score = 0
        matched_keywords = []

        for keyword, weight in self.complexity_keywords.items():
            if keyword in text_lower:
                keyword_score += weight
                matched_keywords.append(keyword)

        for keyword, weight in self.simplicity_keywords.items():
            if keyword in text_lower:
                keyword_score += weight
                matched_keywords.append(f"-{keyword}")

        score += keyword_score
        if matched_keywords:
            reasoning_parts.append(f"Keywords: {', '.join(matched_keywords[:5])}")

        # 2. Component counting
        component_count = 0
        for pattern in self.component_patterns:
            matches = re.findall(pattern, text_lower)
            component_count += len(set(matches))

        component_score = component_count * 5
        score += component_score
        if component_count > 0:
            reasoning_parts.append(f"{component_count} technologies")

        # 3. Text length analysis
        word_count = len(task_description.split())
        if word_count > 50:
            length_score = 10
            reasoning_parts.append("detailed description")
        elif word_count > 20:
            length_score = 5
        elif word_count < 5:
            length_score = -10
            reasoning_parts.append("brief description")
        else:
            length_score = 0

        score += length_score

        # 4. Multi-part detection (and, with, including, etc.)
        conjunction_patterns = [
            r'\band\b', r'\bwith\b', r'\bincluding\b',
            r'\bplus\b', r'\balso\b', r',\s*'
        ]
        part_count = 0
        for pattern in conjunction_patterns:
            part_count += len(re.findall(pattern, text_lower))

        if part_count >= 5:
            conjunction_score = 15
            reasoning_parts.append("many components")
        elif part_count >= 3:
            conjunction_score = 10
            reasoning_parts.append("multiple parts")
        else:
            conjunction_score = 0

        score += conjunction_score

        # 5. Scope detection
        scope_indicators = {
            'full': 10, 'complete': 10, 'entire': 10,
            'end-to-end': 15, 'full-stack': 15,
            'production': 10, 'enterprise': 15,
        }

        scope_score = 0
        for indicator, weight in scope_indicators.items():
            if indicator in text_lower:
                scope_score += weight
                reasoning_parts.append(f"{indicator} scope")
                break

        score += scope_score

        # Normalize score to 1-100 range
        score = max(1, min(100, score))

        # Determine complexity level and recommended subtasks
        level, min_tasks, max_tasks = self._score_to_level(score)
        recommended_subtasks = min_tasks + (max_tasks - min_tasks) // 2

        # Build reasoning
        reasoning = f"Score: {score}/100. " + "; ".join(reasoning_parts) if reasoning_parts else "Basic task"

        return ComplexityScore(
            score=score,
            level=level,
            recommended_subtasks=recommended_subtasks,
            reasoning=reasoning
        )

    def _score_to_level(self, score: int) -> Tuple[str, int, int]:
        """
        Convert numerical score to complexity level

        Args:
            score: Numerical score (1-100)

        Returns:
            Tuple of (level, min_tasks, max_tasks)
        """
        if score >= 70:
            return ('very_high', 25, 35)
        elif score >= 45:
            return ('high', 18, 25)
        elif score >= 25:
            return ('medium', 12, 18)
        elif score >= 10:
            return ('low', 5, 10)
        else:
            return ('trivial', 1, 3)

    def get_task_range(self, task_description: str) -> Tuple[int, int]:
        """
        Get recommended task count range

        Args:
            task_description: Task description

        Returns:
            Tuple of (min_tasks, max_tasks)
        """
        score = self.analyze(task_description)
        _, min_tasks, max_tasks = self._score_to_level(score.score)
        return min_tasks, max_tasks

    def print_analysis(self, task_description: str) -> None:
        """
        Print detailed complexity analysis

        Args:
            task_description: Task to analyze
        """
        score = self.analyze(task_description)

        print("\n" + "="*60)
        print("🔍 Complexity Analysis")
        print("="*60)
        print(f"Task: {task_description[:80]}...")
        print(f"\nComplexity Level: {score.level.upper()}")
        print(f"Numerical Score: {score.score}/100")
        print(f"Recommended Subtasks: {score.recommended_subtasks}")
        print(f"Should Decompose: {'Yes' if score.should_decompose() else 'No'}")
        print(f"\nReasoning: {score.reasoning}")
        print("="*60)


# Global analyzer instance
_global_analyzer: Optional[ComplexityAnalyzer] = None


def get_analyzer() -> ComplexityAnalyzer:
    """Get global ComplexityAnalyzer instance"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = ComplexityAnalyzer()
    return _global_analyzer


# Example usage
if __name__ == "__main__":
    analyzer = ComplexityAnalyzer()

    # Test cases
    test_cases = [
        "Fix typo in README",
        "Add logging to API endpoint",
        "Build a todo list web application",
        "Build a full-stack e-commerce platform with React, Node.js, PostgreSQL, and Stripe integration",
        "Create microservices architecture with authentication, API gateway, database, caching, and deployment",
        "Implement machine learning model for image classification with training pipeline and REST API",
    ]

    print("\n🧪 Testing Complexity Analyzer\n")

    for i, task in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}")
        print(f"{'='*60}")

        score = analyzer.analyze(task)

        print(f"Task: {task}")
        print(f"\nComplexity: {score.level.upper()}")
        print(f"Score: {score.score}/100")
        print(f"Recommended subtasks: {score.recommended_subtasks}")
        print(f"Reasoning: {score.reasoning}")

        if score.should_decompose():
            min_tasks, max_tasks = analyzer.get_task_range(task)
            print(f"Task range: {min_tasks}-{max_tasks} subtasks")

    print("\n✓ Complexity analyzer test completed\n")
