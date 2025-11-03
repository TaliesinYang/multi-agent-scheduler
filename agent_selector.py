"""
Smart Agent Selector for Multi-Agent Scheduler

Implements intelligent agent selection based on:
- Task type and complexity
- Agent capabilities and strengths
- Load balancing
- Fallback chains

Example:
    config = AgentConfig.load()
    selector = SmartAgentSelector(config)

    agent_name = selector.select(task, available_agents)
    rationale = selector.get_last_selection_rationale()
"""

from typing import Dict, List, Optional, Tuple
from config import AgentConfig
from scheduler import Task


class SmartAgentSelector:
    """
    Intelligent agent selection system

    Evaluates task complexity and matches with best-suited agent
    based on configuration rules.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize selector with configuration

        Args:
            config: AgentConfig instance
        """
        self.config = config
        self.last_selection_rationale = {}
        self.selection_history = []

    def select(
        self,
        task: Task,
        available_agents: Dict[str, 'BaseAgent']
    ) -> str:
        """
        Select best agent for task

        Args:
            task: Task object
            available_agents: Dictionary of available agent instances

        Returns:
            Selected agent name

        Raises:
            ValueError: If no suitable agent found
        """
        # Filter enabled agents that are available
        enabled_agents = [
            name for name in self.config.get_enabled_agents()
            if name in available_agents
        ]

        if not enabled_agents:
            raise ValueError("No enabled agents available")

        # Evaluate task complexity
        complexity_score = self.evaluate_complexity(task)
        complexity_level = self._get_complexity_level(complexity_score)

        # Get task type mapping
        task_type = task.task_type.lower()
        type_mapping = self.config.get_type_mapping(task_type)

        if type_mapping:
            # Use configured type mapping
            selected_agent = self._select_from_mapping(
                task,
                type_mapping,
                enabled_agents,
                complexity_score,
                complexity_level
            )
        else:
            # Fallback to weight-based selection
            selected_agent = self._select_by_weights(
                task,
                enabled_agents,
                complexity_score
            )

        # Record selection rationale
        self._record_selection_rationale(
            task,
            selected_agent,
            complexity_score,
            complexity_level
        )

        return selected_agent

    def evaluate_complexity(self, task: Task) -> float:
        """
        Evaluate task complexity score

        Args:
            task: Task object

        Returns:
            Complexity score (0-100+)
        """
        score = 0.0

        # 1. Prompt length contribution
        prompt_contribution = len(task.prompt) / 100
        score += prompt_contribution

        # 2. Dependencies contribution
        dependency_contribution = len(task.depends_on) * 10
        score += dependency_contribution

        # 3. Priority contribution
        priority_contribution = task.priority * 5
        score += priority_contribution

        # 4. Keyword-based complexity
        keywords = self.config.get_complexity_keywords()
        prompt_lower = task.prompt.lower()

        complex_keyword_matches = sum(
            1 for kw in keywords.get("complex", [])
            if kw.lower() in prompt_lower
        )
        simple_keyword_matches = sum(
            1 for kw in keywords.get("simple", [])
            if kw.lower() in prompt_lower
        )

        keyword_contribution = (complex_keyword_matches * 20) - (simple_keyword_matches * 10)
        score += keyword_contribution

        return max(0, score)  # Ensure non-negative

    def _get_complexity_level(self, complexity_score: float) -> str:
        """
        Convert complexity score to level

        Args:
            complexity_score: Numeric complexity score

        Returns:
            Complexity level string (simple, medium, complex)
        """
        levels = self.config.get_complexity_levels()

        for level_name, thresholds in levels.items():
            if thresholds["min"] <= complexity_score <= thresholds["max"]:
                return level_name

        return "complex"  # Default

    def _select_from_mapping(
        self,
        task: Task,
        type_mapping: Dict,
        enabled_agents: List[str],
        complexity_score: float,
        complexity_level: str
    ) -> str:
        """
        Select agent using type mapping configuration

        Args:
            task: Task object
            type_mapping: Type mapping configuration
            enabled_agents: List of enabled agent names
            complexity_score: Task complexity score
            complexity_level: Complexity level string

        Returns:
            Selected agent name
        """
        # Check for primary agent
        primary = type_mapping.get("primary")
        if primary and primary in enabled_agents:
            # Check if secondary should be used based on complexity
            complexity_threshold = type_mapping.get("complexity_threshold")
            secondary = type_mapping.get("secondary")

            if (
                complexity_threshold is not None
                and complexity_score > complexity_threshold
                and secondary
                and secondary in enabled_agents
            ):
                return secondary

            return primary

        # Try fallback chain
        fallback_chain = type_mapping.get("fallback", [])
        for agent_name in fallback_chain:
            if agent_name in enabled_agents:
                return agent_name

        # Last resort: first available
        return enabled_agents[0]

    def _select_by_weights(
        self,
        task: Task,
        enabled_agents: List[str],
        complexity_score: float
    ) -> str:
        """
        Select agent by task type weights

        Args:
            task: Task object
            enabled_agents: List of enabled agent names
            complexity_score: Task complexity score

        Returns:
            Selected agent name
        """
        task_type = task.task_type.lower()
        agent_scores = {}

        for agent_name in enabled_agents:
            weights = self.config.get_task_type_weights(agent_name)
            base_weight = weights.get(task_type, 50)  # Default 50

            # Apply load balancing if enabled
            if self.config.is_load_balancing_enabled():
                # Reduce score for agents with more recent selections
                recent_count = sum(
                    1 for selection in self.selection_history[-10:]
                    if selection == agent_name
                )
                load_penalty = recent_count * 5
                base_weight -= load_penalty

            agent_scores[agent_name] = base_weight

        # Select agent with highest score
        best_agent = max(agent_scores, key=agent_scores.get)
        return best_agent

    def _record_selection_rationale(
        self,
        task: Task,
        selected_agent: str,
        complexity_score: float,
        complexity_level: str
    ):
        """
        Record rationale for selection

        Args:
            task: Task object
            selected_agent: Selected agent name
            complexity_score: Complexity score
            complexity_level: Complexity level
        """
        # Get agent weights for comparison
        all_weights = {}
        enabled_agents = self.config.get_enabled_agents()
        task_type = task.task_type.lower()

        for agent_name in enabled_agents:
            weights = self.config.get_task_type_weights(agent_name)
            all_weights[agent_name] = weights.get(task_type, 0)

        # Build rationale
        self.last_selection_rationale = {
            "task_id": task.id,
            "task_type": task.task_type,
            "selected_agent": selected_agent,
            "complexity_score": round(complexity_score, 2),
            "complexity_level": complexity_level,
            "prompt_length": len(task.prompt),
            "dependencies_count": len(task.depends_on),
            "priority": task.priority,
            "agent_weights": all_weights,
            "reason": self._generate_reason(task, selected_agent, complexity_level)
        }

        # Add to history
        self.selection_history.append(selected_agent)

        # Keep history limited
        if len(self.selection_history) > 100:
            self.selection_history = self.selection_history[-100:]

    def _generate_reason(self, task: Task, selected_agent: str, complexity_level: str) -> str:
        """
        Generate human-readable selection reason

        Args:
            task: Task object
            selected_agent: Selected agent name
            complexity_level: Complexity level

        Returns:
            Reason string
        """
        task_type = task.task_type.lower()
        type_mapping = self.config.get_type_mapping(task_type)

        if type_mapping:
            if type_mapping.get("primary") == selected_agent:
                reason_text = type_mapping.get("reason", "Best match for task type")
                return f"{reason_text} ({complexity_level} complexity)"
            elif type_mapping.get("secondary") == selected_agent:
                return f"Secondary agent for complex {task_type} task"
            else:
                return f"Fallback agent for {task_type} task"
        else:
            return f"Weight-based selection for {task_type} ({complexity_level})"

    def get_last_selection_rationale(self) -> Dict:
        """
        Get rationale for last selection

        Returns:
            Dictionary with selection rationale details
        """
        return self.last_selection_rationale.copy()

    def get_selection_stats(self) -> Dict[str, int]:
        """
        Get statistics on agent selection history

        Returns:
            Dictionary of agent_name -> selection_count
        """
        stats = {}
        for agent_name in self.selection_history:
            stats[agent_name] = stats.get(agent_name, 0) + 1
        return stats

    def reset_history(self):
        """Clear selection history"""
        self.selection_history = []
        self.last_selection_rationale = {}
