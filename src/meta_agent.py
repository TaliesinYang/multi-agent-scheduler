"""
Meta-Agent: Intelligent Task Decomposition

Uses AI to automatically break down complex tasks into subtasks with dependencies.
"""

import asyncio
import json
from typing import List, Dict, Optional
from anthropic import AsyncAnthropic
from src.scheduler import Task


class MetaAgent:
    """
    Meta-Agent that uses AI to decompose complex tasks

    Example:
        meta = MetaAgent(api_key="sk-...")
        tasks = await meta.decompose_task("Build a todo app with database")
        # Returns: [Design DB schema, Build API, Create frontend, Write tests]
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Meta-Agent with Claude API

        Args:
            api_key: Anthropic API key
            model: Claude model to use for task decomposition
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def decompose_task(self, user_input: str, min_tasks: int = 15, max_tasks: int = 20) -> List[Task]:
        """
        Decompose user's complex task into structured subtasks

        Args:
            user_input: User's task description (e.g., "Build a website")
            min_tasks: Minimum number of subtasks to generate (default: 15)
            max_tasks: Maximum number of subtasks to generate (default: 20)

        Returns:
            List of Task objects with dependencies

        Example:
            >>> tasks = await meta.decompose_task("Develop a REST API")
            >>> for task in tasks:
            ...     print(f"{task.id}: {task.prompt}")
            task1: Design database schema
            task2: Implement CRUD operations
            task3: Add authentication
            task4: Write API tests
        """
        prompt = self._build_decomposition_prompt(user_input, min_tasks, max_tasks)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse AI response into structured tasks
            response_text = response.content[0].text
            tasks = self._parse_tasks_from_response(response_text)

            return tasks

        except Exception as e:
            print(f"❌ Task decomposition failed: {e}")
            # Fallback: Return single task if decomposition fails
            return [Task(
                id="task1",
                prompt=user_input,
                task_type="general",
                priority=1
            )]

    def _build_decomposition_prompt(self, user_input: str, min_tasks: int, max_tasks: int) -> str:
        """Build the prompt for task decomposition with atomic granularity"""
        return f"""You are a project planning expert. Break down this task into ATOMIC, executable subtasks.

User Task: {user_input}

CRITICAL Requirements:
1. Generate {min_tasks} to {max_tasks} SMALL, ATOMIC subtasks (prefer 15-20 tasks, favor MORE smaller tasks over fewer large tasks)
2. Each subtask MUST be completable in < 5 minutes
3. Each subtask should modify 1-3 files maximum
4. Break down by individual files, endpoints, or components - NOT by phases
5. Identify dependencies between tasks precisely
6. Classify task type: coding, analysis, simple, or general
7. Assign priority (1=highest, 5=lowest)
8. Estimate execution time in minutes

Granularity Guidelines:
❌ BAD (too broad):
   - "Implement frontend-backend integration"
   - "Add validation to all API endpoints"
   - "Set up complete authentication system"
   - "Build entire user interface"

✅ GOOD (atomic):
   - "Create API client helper in src/api/client.js"
   - "Add Authorization header to API client requests"
   - "Update TasksPage.jsx to use API client for fetching tasks"
   - "Add email validation helper function in utils/validation.js"
   - "Apply email validation to /api/register endpoint"

Return ONLY a valid JSON array in this exact format:
[
  {{
    "id": "task1",
    "prompt": "Design database schema with users table (3 fields: id, email, password_hash)",
    "task_type": "analysis",
    "priority": 1,
    "depends_on": [],
    "estimated_minutes": 3
  }},
  {{
    "id": "task2",
    "prompt": "Create schema.sql file with users table definition",
    "task_type": "coding",
    "priority": 1,
    "depends_on": ["task1"],
    "estimated_minutes": 2
  }},
  {{
    "id": "task3",
    "prompt": "Add tasks table to schema.sql with user_id foreign key",
    "task_type": "coding",
    "priority": 2,
    "depends_on": ["task2"],
    "estimated_minutes": 3
  }}
]

Task Types:
- coding: Writing/modifying code files
- analysis: Research, design, planning (no code)
- simple: Documentation, configs, < 2 min tasks
- general: Everything else

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the raw JSON array starting with '[' and ending with ']'
- Do NOT include any explanations, Chinese text, English descriptions, or markdown
- Do NOT wrap the JSON in code blocks (no ```json or ```)
- Do NOT ask questions or request clarification
- Start your response immediately with '[' character
- If unsure, make reasonable assumptions and provide the JSON array

Example of CORRECT output format (start immediately with '['):
[
  {{"id": "task1", "prompt": "...", "task_type": "coding", "priority": 1, "depends_on": [], "estimated_minutes": 3}}
]"""

    def _parse_tasks_from_response(self, response_text: str) -> List[Task]:
        """
        Parse AI response into Task objects

        Handles both clean JSON and markdown-wrapped JSON responses
        """
        try:
            # Clean up response text
            text = response_text.strip()

            # First, try to extract from Claude CLI wrapper format
            # Claude CLI with --output-format json returns: {"type":"result","result":"..."}
            try:
                wrapper = json.loads(text)
                if isinstance(wrapper, dict) and 'result' in wrapper:
                    text = wrapper['result']
            except:
                pass  # Not a wrapper format, continue with original text

            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            task_data = json.loads(text)

            # Convert to Task objects
            tasks = []
            for item in task_data:
                # Store estimated_minutes in metadata if provided
                metadata = {}
                if "estimated_minutes" in item:
                    metadata["estimated_minutes"] = item["estimated_minutes"]

                task = Task(
                    id=item.get("id", f"task{len(tasks)+1}"),
                    prompt=item.get("prompt", ""),
                    task_type=item.get("task_type", "general"),
                    priority=item.get("priority", 3),
                    depends_on=item.get("depends_on", []),
                    metadata=metadata if metadata else None
                )
                tasks.append(task)

            print(f"✓ Decomposed into {len(tasks)} subtasks")
            return tasks

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Response: {response_text[:200]}...")

            # Fallback: Create a simple task list from text
            return self._fallback_parsing(response_text)

    def _fallback_parsing(self, text: str) -> List[Task]:
        """
        Fallback parser when JSON parsing fails

        Extracts task-like lines from free-form text
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        tasks = []
        for i, line in enumerate(lines[:5]):  # Max 5 tasks
            # Skip JSON artifacts and empty lines
            if line.startswith('{') or line.startswith('[') or len(line) < 10:
                continue

            # Remove common prefixes
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*', '•']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()

            if line:
                tasks.append(Task(
                    id=f"task{i+1}",
                    prompt=line,
                    task_type="general",
                    priority=i+1
                ))

        if not tasks:
            # Ultimate fallback
            tasks = [Task(
                id="task1",
                prompt="Complete the requested task",
                task_type="general",
                priority=1
            )]

        print(f"[WARN] Used fallback parser: {len(tasks)} tasks extracted")
        return tasks

    async def analyze_complexity(self, user_input: str) -> Dict:
        """
        Analyze task complexity to decide if decomposition is needed

        Args:
            user_input: User's task description

        Returns:
            Dict with complexity analysis:
            - complexity: low/medium/high
            - should_decompose: bool
            - estimated_subtasks: int
            - reasoning: str
        """
        prompt = f"""Analyze this task's complexity:

Task: {user_input}

Return a JSON object:
{{
  "complexity": "low|medium|high",
  "should_decompose": true|false,
  "estimated_subtasks": <number>,
  "reasoning": "<brief explanation>"
}}

Guidelines:
- low: Single-step task, <5 min
- medium: Multi-step, 15-60 min
- high: Complex, multiple dependencies, >1 hour

Only return the JSON object."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text.strip()

            # Clean and parse
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(text)
            return analysis

        except Exception as e:
            # Default to decomposition on error
            return {
                "complexity": "medium",
                "should_decompose": True,
                "estimated_subtasks": 3,
                "reasoning": f"Analysis failed: {e}"
            }

    def print_task_tree(self, tasks: List[Task]):
        """
        Print task list with dependencies in a tree structure

        Example output:
        📋 Task Breakdown:
        ├─ task1: Design database schema
        ├─ task2: Implement API [depends on: task1]
        └─ task3: Write tests [depends on: task2]
        """
        print("\n" + "="*60)
        print("📋 Task Breakdown:")
        print("="*60)

        for i, task in enumerate(tasks):
            # Determine tree symbol
            if i == len(tasks) - 1:
                symbol = "└─"
            else:
                symbol = "├─"

            # Format dependencies
            deps_str = ""
            if task.depends_on:
                deps_str = f" [depends on: {', '.join(task.depends_on)}]"

            # Format task type and priority
            meta_str = f"[{task.task_type}, priority={task.priority}]"

            print(f"{symbol} {task.id}: {task.prompt}")
            print(f"   {meta_str}{deps_str}")

        print("="*60)


# Example usage
if __name__ == "__main__":
    async def main():
        """Test the Meta-Agent"""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ Please set ANTHROPIC_API_KEY environment variable")
            return

        meta = MetaAgent(api_key=api_key)

        # Test 1: Complexity analysis
        print("\n🔍 Test 1: Complexity Analysis")
        test_input = "Build a todo list web application with user authentication"
        analysis = await meta.analyze_complexity(test_input)
        print(f"Complexity: {analysis['complexity']}")
        print(f"Should decompose: {analysis['should_decompose']}")
        print(f"Reasoning: {analysis['reasoning']}")

        # Test 2: Task decomposition
        print("\n🔍 Test 2: Task Decomposition")
        tasks = await meta.decompose_task(test_input)
        meta.print_task_tree(tasks)

        print("\n✓ Meta-Agent test completed")

    asyncio.run(main())


# ============================================================================
# MetaAgentCLI - CLI-based Meta-Agent (No API Key Required)
# ============================================================================


class MetaAgentCLI:
    """
    Meta-Agent using Claude CLI for task decomposition

    Uses claude command directly instead of API.
    No API key required - only needs Claude CLI subscription.

    Example:
        meta = MetaAgentCLI()
        tasks = await meta.decompose_task("Build a web app")
    """

    def __init__(self):
        """Initialize Meta-Agent with Claude CLI"""
        # Lazy import to avoid circular dependency
        from src.agents import ClaudeCLIAgent
        self.cli_agent = ClaudeCLIAgent()

    async def decompose_task(
        self,
        user_input: str,
        min_tasks: int = 15,
        max_tasks: int = 20
    ) -> List[Task]:
        """
        Decompose user's complex task using Claude CLI

        Args:
            user_input: User's task description
            min_tasks: Minimum number of subtasks (default: 15)
            max_tasks: Maximum number of subtasks (default: 20)

        Returns:
            List of Task objects with dependencies
        """
        print("[Meta-Agent] analyzing task via CLI...")

        # Build decomposition prompt
        prompt = self._build_decomposition_prompt(user_input, min_tasks, max_tasks)

        try:
            # Call claude CLI with longer timeout for complex decomposition
            result = await self.cli_agent.call(prompt, timeout=60)

            if result['success']:
                response_text = result['result']

                # Claude CLI returns wrapped JSON: {"type":"result", "result":"actual content"}
                # We need to extract the actual content from the nested structure
                try:
                    # Try to parse as JSON to unwrap the response
                    response_json = json.loads(response_text)

                    # Extract the 'result' field which contains the actual task list
                    if 'result' in response_json and isinstance(response_json['result'], str):
                        actual_content = response_json['result']
                    else:
                        # If no nested result, use the whole response
                        actual_content = response_text

                    # Parse the actual task list JSON
                    tasks = self._parse_tasks_from_response(actual_content)
                    return tasks

                except json.JSONDecodeError:
                    # If outer JSON parsing fails, try parsing the raw text directly
                    tasks = self._parse_tasks_from_response(response_text)
                    return tasks
            else:
                error = result.get('error', 'Unknown error')
                print(f"[WARN] CLI decomposition failed: {error}")
                print("[WARN] Using fallback: single task")
                return self._create_fallback_task(user_input)

        except Exception as e:
            print(f"[WARN] Meta-Agent CLI error: {e}")
            print(f"[WARN] Error details: {type(e).__name__}")
            print("[WARN] Using fallback: single task")
            return self._create_fallback_task(user_input)

    def _build_decomposition_prompt(self, user_input: str, min_tasks: int, max_tasks: int) -> str:
        """
        Build the prompt for task decomposition with atomic granularity

        Uses same enhanced prompt as API-based Meta-Agent
        """
        return f"""You are a project planning expert. Break down this task into ATOMIC, executable subtasks.

User Task: {user_input}

CRITICAL Requirements:
1. Generate {min_tasks} to {max_tasks} SMALL, ATOMIC subtasks (prefer 15-20 tasks, favor MORE smaller tasks over fewer large tasks)
2. Each subtask MUST be completable in < 5 minutes
3. Each subtask should modify 1-3 files maximum
4. Break down by individual files, endpoints, or components - NOT by phases
5. Identify dependencies between tasks precisely
6. Classify task type: coding, analysis, simple, or general
7. Assign priority (1=highest, 5=lowest)
8. Estimate execution time in minutes

Granularity Guidelines:
❌ BAD (too broad):
   - "Implement frontend-backend integration"
   - "Add validation to all API endpoints"
   - "Set up complete authentication system"
   - "Build entire user interface"

✅ GOOD (atomic):
   - "Create API client helper in src/api/client.js"
   - "Add Authorization header to API client requests"
   - "Update TasksPage.jsx to use API client for fetching tasks"
   - "Add email validation helper function in utils/validation.js"
   - "Apply email validation to /api/register endpoint"

Return ONLY a valid JSON array in this exact format:
[
  {{
    "id": "task1",
    "prompt": "Design database schema with users table (3 fields: id, email, password_hash)",
    "task_type": "analysis",
    "priority": 1,
    "depends_on": [],
    "estimated_minutes": 3
  }},
  {{
    "id": "task2",
    "prompt": "Create schema.sql file with users table definition",
    "task_type": "coding",
    "priority": 1,
    "depends_on": ["task1"],
    "estimated_minutes": 2
  }},
  {{
    "id": "task3",
    "prompt": "Add tasks table to schema.sql with user_id foreign key",
    "task_type": "coding",
    "priority": 2,
    "depends_on": ["task2"],
    "estimated_minutes": 3
  }}
]

Task Types:
- coding: Writing/modifying code files
- analysis: Research, design, planning (no code)
- simple: Documentation, configs, < 2 min tasks
- general: Everything else

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the raw JSON array starting with '[' and ending with ']'
- Do NOT include any explanations, Chinese text, English descriptions, or markdown
- Do NOT wrap the JSON in code blocks (no ```json or ```)
- Do NOT ask questions or request clarification
- Start your response immediately with '[' character
- If unsure, make reasonable assumptions and provide the JSON array

Example of CORRECT output format (start immediately with '['):
[
  {{"id": "task1", "prompt": "...", "task_type": "coding", "priority": 1, "depends_on": [], "estimated_minutes": 3}}
]"""

    def _parse_tasks_from_response(self, response_text: str) -> List[Task]:
        """
        Parse AI response into Task objects

        Handles both clean JSON and markdown-wrapped JSON responses
        """
        try:
            # Clean up response text
            text = response_text.strip()

            # First, try to extract from Claude CLI wrapper format
            # Claude CLI with --output-format json returns: {"type":"result","result":"..."}
            try:
                wrapper = json.loads(text)
                if isinstance(wrapper, dict) and 'result' in wrapper:
                    text = wrapper['result']
            except:
                pass  # Not a wrapper format, continue with original text

            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            task_data = json.loads(text)

            # Convert to Task objects
            tasks = []
            for item in task_data:
                # Store estimated_minutes in metadata if provided
                metadata = {}
                if "estimated_minutes" in item:
                    metadata["estimated_minutes"] = item["estimated_minutes"]

                task = Task(
                    id=item.get("id", f"task{len(tasks)+1}"),
                    prompt=item.get("prompt", ""),
                    task_type=item.get("task_type", "general"),
                    priority=item.get("priority", 3),
                    depends_on=item.get("depends_on", []),
                    metadata=metadata if metadata else None
                )
                tasks.append(task)

            print(f"✓ Decomposed into {len(tasks)} subtasks")
            return tasks

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Response: {response_text[:200]}...")

            # Fallback: Create a simple task list from text
            return self._fallback_parsing(response_text)

    def _fallback_parsing(self, text: str) -> List[Task]:
        """
        Fallback parser when JSON parsing fails

        Extracts task-like lines from free-form text
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        tasks = []
        for i, line in enumerate(lines[:5]):  # Max 5 tasks
            # Skip JSON artifacts and empty lines
            if line.startswith('{') or line.startswith('[') or len(line) < 10:
                continue

            # Remove common prefixes
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*', '•']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()

            if line:
                task = Task(
                    id=f"task{i+1}",
                    prompt=line[:200],  # Limit length
                    task_type="general",
                    priority=3,
                    depends_on=[]
                )
                tasks.append(task)

        if not tasks:
            # Last resort: single task
            print("[WARN] Fallback parsing failed, creating single task")
            return self._create_fallback_task(text[:200])

        print(f"[WARN] Used fallback parsing, extracted {len(tasks)} tasks")
        return tasks

    def _create_fallback_task(self, user_input: str) -> List[Task]:
        """
        Create a single fallback task when decomposition fails

        Args:
            user_input: Original user input

        Returns:
            List with single Task object
        """
        return [
            Task(
                id="task1",
                prompt=user_input,
                task_type="general",
                priority=1,
                depends_on=[]
            )
        ]

    def print_task_tree(self, tasks: List[Task]):
        """
        Print task dependency tree

        Reuses format from API-based Meta-Agent
        """
        print("\n📋 Task Breakdown:")
        for task in tasks:
            deps = f" [depends on: {', '.join(task.depends_on)}]" if task.depends_on else ""
            priority_str = "⭐" * task.priority
            print(f"├─ {task.id}: {task.prompt[:60]}...{deps}")
            print(f"│  Type: {task.task_type} | Priority: {priority_str}")
        print()


# Test MetaAgentCLI when run directly
if __name__ == "__main__" and False:  # Disabled by default
    async def test_cli():
        print("🧪 Testing MetaAgentCLI...")

        meta = MetaAgentCLI()

        # Test task decomposition via CLI
        print("\n🔍 Test: CLI-based Task Decomposition")
        test_input = "Build a todo list web application with user authentication"
        tasks = await meta.decompose_task(test_input)
        meta.print_task_tree(tasks)

        print("\n✓ MetaAgentCLI test completed")

    asyncio.run(test_cli())
