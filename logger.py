"""
Execution Logger for Multi-Agent Scheduler

Records detailed execution logs for task decomposition and execution,
enabling post-execution analysis and performance review.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ExecutionLogger:
    """
    Logger for recording multi-agent scheduler execution details

    Features:
    - Records task start/completion with timestamps
    - Tracks agent assignment and execution time
    - Logs batch execution information
    - Saves structured data to JSON file
    - Supports post-execution analysis
    """

    def __init__(self, session_id: Optional[str] = None, workspace_path: Optional[str] = None):
        """
        Initialize execution logger

        Args:
            session_id: Unique session identifier (default: timestamp)
            workspace_path: Path to workspace directory
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        self.log_file = self.log_dir / f"execution_{self.session_id}.log"

        # Execution data
        self.start_time = datetime.now()
        self.end_time = None
        self.user_task = None
        self.workspace_path = workspace_path  # Store workspace path
        self.tasks = []
        self.batches = []
        self.current_batch = None

        print(f"📝 Logging to: {self.log_file}")

    def set_user_task(self, task_description: str):
        """Set the original user task description"""
        self.user_task = task_description

    def log_decomposition(self, num_tasks: int, duration: float):
        """
        Log task decomposition results

        Args:
            num_tasks: Number of subtasks created
            duration: Time taken for decomposition
        """
        self.decomposition = {
            "num_tasks": num_tasks,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }

    def start_batch(self, batch_id: int, task_ids: List[str]):
        """
        Start logging a new batch

        Args:
            batch_id: Batch number
            task_ids: List of task IDs in this batch
        """
        self.current_batch = {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "start_time": datetime.now().isoformat(),
            "start_timestamp": datetime.now().timestamp()
        }

    def end_batch(self):
        """End current batch logging"""
        if self.current_batch:
            end_time = datetime.now()
            self.current_batch["end_time"] = end_time.isoformat()
            duration = end_time.timestamp() - self.current_batch["start_timestamp"]
            self.current_batch["duration"] = round(duration, 2)
            del self.current_batch["start_timestamp"]
            self.batches.append(self.current_batch)
            self.current_batch = None

    def log_task_start(self, task_id: str, prompt: str, agent_name: str, batch: int, rationale: Optional[Dict] = None):
        """
        Log task execution start

        Args:
            task_id: Task identifier
            prompt: Task prompt
            agent_name: Agent executing the task
            batch: Batch number
            rationale: Optional selection rationale dictionary
        """
        task_log = {
            "task_id": task_id,
            "prompt": prompt,
            "agent": agent_name,
            "batch": batch,
            "start_time": datetime.now().isoformat(),
            "start_timestamp": datetime.now().timestamp(),
            "end_time": None,
            "duration": None,
            "success": None,
            "error": None,
            "selection_rationale": rationale  # NEW: Store selection rationale
        }
        self.tasks.append(task_log)

        # Real-time display
        print(f"   ⏳ {task_id}: {prompt[:50]}{'...' if len(prompt) > 50 else ''} [Agent: {agent_name}]")

    def log_task_complete(
        self,
        task_id: str,
        success: bool,
        duration: float,
        error: Optional[str] = None,
        result: Optional[str] = None
    ):
        """
        Log task execution completion

        Args:
            task_id: Task identifier
            success: Whether task succeeded
            duration: Execution time in seconds
            error: Error message if failed
            result: Task output/result (full content)
        """
        # Find task log
        task_log = next((t for t in self.tasks if t["task_id"] == task_id), None)

        if task_log:
            task_log["end_time"] = datetime.now().isoformat()
            task_log["duration"] = round(duration, 2)
            task_log["success"] = success
            task_log["error"] = error
            task_log["result"] = result  # Save full task output
            del task_log["start_timestamp"]

            # Real-time display
            status = '✅' if success else '❌'
            print(f"   {status} {task_id} completed in {duration:.2f}s")

    def finalize(self, total_time: float, success_count: int, total_count: int):
        """
        Finalize logging and prepare summary

        Args:
            total_time: Total execution time
            success_count: Number of successful tasks
            total_count: Total number of tasks
        """
        self.end_time = datetime.now()
        self.total_time = total_time
        self.summary = {
            "total_tasks": total_count,
            "successful": success_count,
            "failed": total_count - success_count,
            "success_rate": round((success_count / total_count * 100) if total_count > 0 else 0, 1)
        }

    def save_to_file(self):
        """Save execution log to JSON file"""
        log_data = {
            "session_id": self.session_id,
            "user_task": self.user_task,
            "workspace_path": self.workspace_path,  # Save workspace path
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_time": round(self.total_time, 2) if hasattr(self, 'total_time') else None,
            "decomposition": self.decomposition if hasattr(self, 'decomposition') else None,
            "batches": self.batches,
            "tasks": self.tasks,
            "summary": self.summary if hasattr(self, 'summary') else None
        }

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Execution log saved to: {self.log_file}")

    def get_log_path(self) -> str:
        """Get the log file path"""
        return str(self.log_file)


def analyze_log(log_file: str):
    """
    Analyze execution log file

    Args:
        log_file: Path to log file

    Example:
        analyze_log("logs/execution_20251103_142530.log")
    """
    with open(log_file, 'r', encoding='utf-8') as f:
        log = json.load(f)

    print(f"\n{'='*60}")
    print("📊 Execution Log Analysis")
    print(f"{'='*60}")

    print(f"\n📋 Session: {log['session_id']}")
    print(f"🎯 Task: {log['user_task']}")
    print(f"⏱️  Total Time: {log['total_time']:.2f}s")

    if log.get('decomposition'):
        print(f"\n🧠 Decomposition:")
        print(f"   Tasks created: {log['decomposition']['num_tasks']}")
        print(f"   Time taken: {log['decomposition']['duration']:.2f}s")

    if log.get('summary'):
        summary = log['summary']
        print(f"\n✅ Summary:")
        print(f"   Success rate: {summary['success_rate']}%")
        print(f"   Successful: {summary['successful']}/{summary['total_tasks']}")
        print(f"   Failed: {summary['failed']}/{summary['total_tasks']}")

    print(f"\n📦 Batch Execution:")
    for batch in log['batches']:
        print(f"   Batch {batch['batch_id']}: {len(batch['task_ids'])} tasks, {batch['duration']:.2f}s")

    # Find slowest task
    if log['tasks']:
        tasks_with_duration = [t for t in log['tasks'] if t['duration'] is not None]
        if tasks_with_duration:
            slowest = max(tasks_with_duration, key=lambda t: t['duration'])
            print(f"\n🐌 Slowest Task:")
            print(f"   {slowest['task_id']}: {slowest['duration']:.2f}s")
            print(f"   Agent: {slowest['agent']}")

    # Show failed tasks
    failed = [t for t in log['tasks'] if not t.get('success')]
    if failed:
        print(f"\n❌ Failed Tasks ({len(failed)}):")
        for task in failed:
            print(f"   {task['task_id']}: {task.get('error', 'Unknown error')}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        # Analyze specified log file
        analyze_log(sys.argv[1])
    else:
        print("Usage: python logger.py <log_file>")
        print("Example: python logger.py logs/execution_20251103_142530.log")
