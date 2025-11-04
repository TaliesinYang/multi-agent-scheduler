"""
Task Topology Visualizer
Real-time dependency graph and execution status display
"""

from typing import List, Dict, Optional, Set
from scheduler import Task
from dataclasses import dataclass


@dataclass
class TaskStatus:
    """Task execution status"""
    task_id: str
    status: str  # pending, in_progress, completed, failed, decomposed
    duration: float = 0.0
    agent: str = ""


class TaskVisualizer:
    """
    Visualize task dependency graph and execution progress

    Features:
    - ASCII tree-style topology display
    - Batch grouping
    - Real-time status updates
    - Progress bar
    - Dependency visualization

    Example output:

    📋 Task Topology (20 tasks, 6 batches)

    Batch 1 (2 tasks) ━━━━━━━━━━━━━━━━━━━━━━━━
      ├─ task1: Design DB schema    [analysis] ✅ 35.5s
      └─ task2: Setup Flask         [coding]   ✅ 136.3s

    Batch 2 (3 tasks) ━━━━━━━━━━━━━━━━━━━━━━━━
      ├─ task3: User model          [coding]   ⏳ 45.2s
      ├─ task4: Task model          [coding]   ⏸️
      └─ task5: Project model       [coding]   ⏸️

    Progress: ████████░░░░░░ 40% (8/20)
    """

    def __init__(self, tasks: List[Task]):
        """
        Initialize visualizer with task list

        Args:
            tasks: List of Task objects to visualize
        """
        self.tasks = tasks
        self.status_map: Dict[str, TaskStatus] = {}

        # Initialize all tasks as pending
        for task in tasks:
            self.status_map[task.id] = TaskStatus(
                task_id=task.id,
                status="pending"
            )

        # Build batch structure
        self.batches = self._build_batches()

    def _build_batches(self) -> List[List[Task]]:
        """
        Build batch groups based on dependencies

        Returns:
            List of batches, each batch is a list of tasks
        """
        batches = []
        completed_ids: Set[str] = set()
        remaining_tasks = self.tasks.copy()

        while remaining_tasks:
            # Find tasks with satisfied dependencies
            batch = []
            for task in remaining_tasks:
                deps_satisfied = all(dep in completed_ids for dep in task.depends_on)
                if deps_satisfied:
                    batch.append(task)

            if not batch:
                # Circular dependency or error - add remaining tasks
                batch = remaining_tasks.copy()

            batches.append(batch)

            # Mark these tasks as completed (for dependency checking)
            for task in batch:
                completed_ids.add(task.id)
                remaining_tasks.remove(task)

        return batches

    def update_status(self, task_id: str, status: str, duration: float = 0.0, agent: str = ""):
        """
        Update task status

        Args:
            task_id: Task ID to update
            status: New status (pending, in_progress, completed, failed, decomposed)
            duration: Execution duration in seconds (optional)
            agent: Agent name (optional)
        """
        if task_id in self.status_map:
            self.status_map[task_id].status = status
            if duration > 0:
                self.status_map[task_id].duration = duration
            if agent:
                self.status_map[task_id].agent = agent

    def _get_status_emoji(self, status: str) -> str:
        """Get status symbol"""
        emoji_map = {
            "pending": "[ - ]",
            "in_progress": "[RUN]",
            "completed": "[OK] ",
            "failed": "[FAIL]",
            "decomposed": "[...] "
        }
        return emoji_map.get(status, "[?]  ")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return ""
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds / 60)
            secs = seconds % 60
            return f"{minutes}m{secs:.0f}s"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def build_tree(self, show_progress: bool = True) -> str:
        """
        Build ASCII tree-style visualization

        Args:
            show_progress: Whether to show progress bar at bottom

        Returns:
            Multi-line string with tree visualization
        """
        lines = []

        # Header
        total_tasks = len(self.tasks)
        batch_count = len(self.batches)
        lines.append("")
        lines.append(f"Task Topology: {total_tasks} tasks, {batch_count} batches")
        lines.append("")

        # Render each batch
        for batch_num, batch in enumerate(self.batches, 1):
            task_count = len(batch)
            lines.append(f"Batch {batch_num}/{batch_count} ({task_count} tasks) " + "━" * 30)

            for i, task in enumerate(batch):
                # Get status
                status = self.status_map[task.id]
                emoji = self._get_status_emoji(status.status)

                # Tree symbol
                if i == len(batch) - 1:
                    symbol = "└─"
                else:
                    symbol = "├─"

                # Format prompt (truncate if too long)
                prompt = self._truncate_text(task.prompt, 50)

                # Format task type
                task_type_str = f"[{task.task_type}]"

                # Format duration
                duration_str = self._format_duration(status.duration)

                # Format agent (if available)
                agent_str = f"[{status.agent}]" if status.agent else ""

                # Build line
                line = f"  {symbol} {task.id}: {prompt}"
                meta_line = f"     {task_type_str} {emoji} {duration_str} {agent_str}"

                lines.append(line)
                lines.append(meta_line)

            lines.append("")  # Empty line between batches

        # Progress bar
        if show_progress:
            lines.append(self._build_progress_bar())
            lines.append("")

        return "\n".join(lines)

    def _build_progress_bar(self) -> str:
        """
        Build progress bar showing completion status

        Returns:
            Progress bar string like: Progress: ████████░░░░░░ 40% (8/20)
        """
        total = len(self.tasks)
        completed = sum(1 for s in self.status_map.values() if s.status == "completed")
        failed = sum(1 for s in self.status_map.values() if s.status == "failed")
        in_progress = sum(1 for s in self.status_map.values() if s.status == "in_progress")

        # Calculate percentage
        percentage = (completed + failed) / total * 100 if total > 0 else 0

        # Build bar (20 characters)
        bar_length = 20
        filled_length = int(bar_length * (completed + failed) / total) if total > 0 else 0

        filled_bar = "█" * filled_length
        empty_bar = "░" * (bar_length - filled_length)

        # Status summary
        status_str = f"Progress: {filled_bar}{empty_bar} {percentage:.0f}% ({completed+failed}/{total})"

        # Add counts
        details = []
        if completed > 0:
            details.append(f"✅ {completed}")
        if failed > 0:
            details.append(f"❌ {failed}")
        if in_progress > 0:
            details.append(f"⏳ {in_progress}")

        if details:
            status_str += " | " + " ".join(details)

        return status_str

    def build_compact_view(self) -> str:
        """
        Build compact progress view (no tree structure)

        Returns:
            Compact multi-line status display
        """
        lines = []

        # Header
        total = len(self.tasks)
        lines.append("")
        lines.append(f"📊 Execution Progress ({total} tasks)")
        lines.append("")

        # Progress bar
        lines.append(self._build_progress_bar())
        lines.append("")

        # Group by status
        pending = [t for t in self.tasks if self.status_map[t.id].status == "pending"]
        in_progress = [t for t in self.tasks if self.status_map[t.id].status == "in_progress"]
        completed = [t for t in self.tasks if self.status_map[t.id].status == "completed"]
        failed = [t for t in self.tasks if self.status_map[t.id].status == "failed"]

        # Show in-progress
        if in_progress:
            lines.append(f"⏳ In Progress ({len(in_progress)}):")
            for task in in_progress[:3]:  # Show max 3
                status = self.status_map[task.id]
                duration_str = self._format_duration(status.duration)
                agent_str = f" [{status.agent}]" if status.agent else ""
                prompt = self._truncate_text(task.prompt, 60)
                lines.append(f"  • {task.id}: {prompt}{agent_str} {duration_str}")
            if len(in_progress) > 3:
                lines.append(f"  ... and {len(in_progress) - 3} more")
            lines.append("")

        # Show completed summary
        if completed:
            lines.append(f"✅ Completed ({len(completed)}): {', '.join(t.id for t in completed[:5])}")
            if len(completed) > 5:
                lines.append(f"   ... and {len(completed) - 5} more")
            lines.append("")

        # Show failed
        if failed:
            lines.append(f"❌ Failed ({len(failed)}): {', '.join(t.id for t in failed)}")
            lines.append("")

        # Show pending count
        if pending:
            lines.append(f"⏸️  Pending ({len(pending)})")
            lines.append("")

        return "\n".join(lines)

    def add_subtasks(self, parent_task_id: str, subtasks: List[Task]):
        """
        Add dynamically decomposed subtasks to visualization

        Args:
            parent_task_id: ID of parent task that was decomposed
            subtasks: List of new subtasks
        """
        # Mark parent as decomposed
        if parent_task_id in self.status_map:
            self.status_map[parent_task_id].status = "decomposed"

        # Add subtasks to task list
        self.tasks.extend(subtasks)

        # Initialize status for subtasks
        for task in subtasks:
            self.status_map[task.id] = TaskStatus(
                task_id=task.id,
                status="pending"
            )

        # Rebuild batches
        self.batches = self._build_batches()

    def get_summary(self) -> Dict:
        """
        Get summary statistics

        Returns:
            Dictionary with counts and percentages
        """
        total = len(self.tasks)
        statuses = [s.status for s in self.status_map.values()]

        return {
            "total": total,
            "completed": statuses.count("completed"),
            "failed": statuses.count("failed"),
            "in_progress": statuses.count("in_progress"),
            "pending": statuses.count("pending"),
            "decomposed": statuses.count("decomposed"),
            "success_rate": statuses.count("completed") / total * 100 if total > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    # Test visualization
    from scheduler import Task

    # Create sample tasks
    tasks = [
        Task(id="task1", prompt="Design database schema", task_type="analysis", priority=1),
        Task(id="task2", prompt="Setup Flask app structure", task_type="coding", priority=1),
        Task(id="task3", prompt="Implement User model", task_type="coding", priority=2, depends_on=["task1", "task2"]),
        Task(id="task4", prompt="Implement Task model", task_type="coding", priority=2, depends_on=["task1", "task2"]),
        Task(id="task5", prompt="Create REST API endpoints", task_type="coding", priority=3, depends_on=["task3", "task4"]),
    ]

    # Initialize visualizer
    viz = TaskVisualizer(tasks)

    # Show initial state
    print("=== Initial State ===")
    print(viz.build_tree())

    # Simulate execution
    viz.update_status("task1", "completed", duration=35.5, agent="Claude")
    viz.update_status("task2", "completed", duration=136.3, agent="Codex")
    viz.update_status("task3", "in_progress", duration=45.2, agent="Codex")

    # Show updated state
    print("\n=== After Some Tasks ===")
    print(viz.build_tree())

    # Show compact view
    print("\n=== Compact View ===")
    print(viz.build_compact_view())

    # Show summary
    print("\n=== Summary ===")
    summary = viz.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
