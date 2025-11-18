"""
Simple MetaAgent wrapper for end-to-end testing

Avoids complex dependency chains by importing only what's needed.
"""

import asyncio
import json
from typing import List, Optional
from src.scheduler import Task


class SimpleMetaAgentCLI:
    """
    Simplified MetaAgent using Claude CLI for task decomposition

    This version avoids complex dependencies for testing purposes.
    """

    def __init__(self, agent_type: str = 'claude'):
        """Initialize with CLI agent type"""
        self.agent_type = agent_type
        self.cli_command = agent_type
        print(f"[SimpleMetaAgent] Using {agent_type.upper()} CLI for decomposition")

    async def decompose_task(
        self,
        user_input: str,
        min_tasks: Optional[int] = None,
        max_tasks: Optional[int] = None,
        use_dynamic_complexity: bool = True
    ) -> List[Task]:
        """
        Decompose user task into subtasks using Claude CLI

        Args:
            user_input: User's complex task
            min_tasks: Minimum number of subtasks
            max_tasks: Maximum number of subtasks
            use_dynamic_complexity: Unused (for compatibility)

        Returns:
            List of Task objects
        """
        if min_tasks is None:
            min_tasks = 5
        if max_tasks is None:
            max_tasks = 20

        print(f"[Decomposition] Generating {min_tasks}-{max_tasks} subtasks...")

        # Build prompt for task decomposition
        prompt = f"""You are a project planning expert. Break down this task into ATOMIC, executable subtasks.

User Task: {user_input}

CRITICAL Requirements:
1. Generate {min_tasks} to {max_tasks} SMALL, ATOMIC subtasks
2. Each subtask MUST be completable in < 5 minutes
3. Each subtask should modify 1-3 files maximum
4. Identify dependencies between tasks precisely
5. Classify task type: coding, analysis, simple, or general
6. Assign priority (1=highest, 5=lowest)

Return ONLY a valid JSON array in this exact format:
[
  {{
    "id": "task1",
    "prompt": "Design database schema with users table",
    "task_type": "analysis",
    "priority": 1,
    "depends_on": []
  }},
  {{
    "id": "task2",
    "prompt": "Create schema.sql file",
    "task_type": "coding",
    "priority": 1,
    "depends_on": ["task1"]
  }}
]

Task Types:
- coding: Writing/modifying code files
- analysis: Research, design, planning (no code)
- simple: Documentation, configs, < 2 min tasks
- general: Everything else

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the raw JSON array starting with '[' and ending with ']'
- Do NOT include any explanations or markdown
- Do NOT wrap in code blocks
- Start your response immediately with '[' character
"""

        # Call Claude CLI
        import subprocess
        try:
            print(f"  🤖 Calling {self.cli_command} CLI...")

            result = subprocess.run(
                [self.cli_command, "-p", prompt, "--tools", "Bash", "--permission-mode", "bypassPermissions"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                print(f"  ❌ CLI failed: {result.stderr}")
                return self._fallback_decomposition(user_input, min_tasks)

            output = result.stdout.strip()
            print(f"  ✓ Got response ({len(output)} chars)")

            # Parse JSON
            tasks = self._parse_response(output)

            if not tasks:
                print(f"  ⚠️  Parsing failed, using fallback")
                return self._fallback_decomposition(user_input, min_tasks)

            print(f"  ✓ Parsed {len(tasks)} tasks")
            return tasks

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Timeout, using fallback")
            return self._fallback_decomposition(user_input, min_tasks)
        except Exception as e:
            print(f"  ❌ Error: {e}, using fallback")
            return self._fallback_decomposition(user_input, min_tasks)

    def _parse_response(self, output: str) -> List[Task]:
        """Parse CLI response into Task objects"""
        try:
            # Clean output
            text = output.strip()

            # Remove markdown if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Find JSON array
            start = text.find('[')
            end = text.rfind(']') + 1
            if start == -1 or end == 0:
                return []

            json_text = text[start:end]
            task_data = json.loads(json_text)

            if not isinstance(task_data, list):
                return []

            # Convert to Task objects
            tasks = []
            for item in task_data:
                if not isinstance(item, dict) or 'prompt' not in item:
                    continue

                task = Task(
                    id=item.get('id', f"task{len(tasks)+1}"),
                    prompt=item.get('prompt', ''),
                    task_type=item.get('task_type', 'general'),
                    priority=item.get('priority', 3),
                    depends_on=item.get('depends_on', [])
                )
                tasks.append(task)

            return tasks

        except Exception as e:
            print(f"  Parse error: {e}")
            return []

    def _fallback_decomposition(self, user_input: str, task_count: int) -> List[Task]:
        """Fallback: Create simple task list when AI decomposition fails"""
        print(f"  [Fallback] Creating {task_count} generic subtasks")

        tasks = []
        task_templates = [
            ("Analyze requirements", "analysis"),
            ("Design system architecture", "analysis"),
            ("Implement core functionality", "coding"),
            ("Add error handling", "coding"),
            ("Write unit tests", "coding"),
            ("Create documentation", "simple"),
            ("Perform integration testing", "general"),
            ("Optimize performance", "coding")
        ]

        for i in range(min(task_count, len(task_templates))):
            prompt_template, task_type = task_templates[i]
            tasks.append(Task(
                id=f"task{i+1}",
                prompt=f"{prompt_template} for: {user_input[:50]}",
                task_type=task_type,
                priority=i//2 + 1,
                depends_on=[f"task{i}"] if i > 0 else []
            ))

        return tasks

    def print_task_tree(self, tasks: List[Task]):
        """Print task tree for display"""
        print("\n📋 Task Decomposition Tree:")
        print("─" * 70)
        for i, task in enumerate(tasks):
            symbol = "└─" if i == len(tasks) - 1 else "├─"
            deps = f" [depends on: {', '.join(task.depends_on)}]" if task.depends_on else ""
            print(f"{symbol} {task.id}: {task.prompt[:60]}...{deps}")
        print("─" * 70)
