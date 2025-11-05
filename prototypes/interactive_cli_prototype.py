#!/usr/bin/env python3
"""
Interactive CLI Prototype for Multi-Agent Code

This is a minimal prototype to demonstrate the core concept.
Run with: python prototypes/interactive_cli_prototype.py

Features demonstrated:
- Interactive REPL with prompt
- Command handling (/help, /config, etc.)
- Task processing with Meta-Agent
- Streaming output simulation
- Session context management
"""

import asyncio
import sys
import os
from typing import Optional, List
from dataclasses import dataclass

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.meta_agent import MetaAgent, MetaAgentCLI
from src.scheduler import Scheduler
from src.agents import MockAgent, ClaudeAgent, OpenAIAgent
from src.task import Task


# ============================================================================
# CLI Display & Formatting
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a header with formatting"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def print_agent_output(agent_name: str, text: str):
    """Print agent output with color coding"""
    colors = {
        'claude': Colors.MAGENTA,
        'openai': Colors.GREEN,
        'gemini': Colors.CYAN,
        'mock': Colors.YELLOW,
    }
    color = colors.get(agent_name.lower(), Colors.END)
    print(f"{color}[{agent_name}]{Colors.END} {text}")


# ============================================================================
# Session Management
# ============================================================================

@dataclass
class SessionContext:
    """Stores conversation context and history"""
    history: List[dict]
    workspace_files: List[str]

    def __init__(self):
        self.history = []
        self.workspace_files = []

    def add_interaction(self, user_input: str, result: dict):
        """Add user interaction to history"""
        self.history.append({
            'input': user_input,
            'result': result,
        })

    def get_context_summary(self) -> str:
        """Get a summary of recent context"""
        if not self.history:
            return "No previous interactions"

        recent = self.history[-3:]  # Last 3 interactions
        summary = []
        for item in recent:
            summary.append(f"  - {item['input']}")
        return "\n".join(summary)


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration for the CLI"""

    def __init__(self):
        # Load from environment or config file
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # Preferences
        self.auto_execute = False  # Ask before executing
        self.use_mock = not (self.anthropic_key or self.openai_key)
        self.parallel = True
        self.verbose = True

    def display(self):
        """Display current configuration"""
        print("\n⚙️  Configuration:")
        print(f"  Auto-execute: {self.auto_execute}")
        print(f"  Parallel execution: {self.parallel}")
        print(f"  Mock mode: {self.use_mock}")
        print(f"  Verbose: {self.verbose}")
        print(f"\n🤖 Available Agents:")
        if self.anthropic_key:
            print(f"  ✓ Claude (API key found)")
        else:
            print(f"  ✗ Claude (no API key)")

        if self.openai_key:
            print(f"  ✓ OpenAI (API key found)")
        else:
            print(f"  ✗ OpenAI (no API key)")

        if self.use_mock:
            print(f"  ✓ Mock agents (enabled)")


# ============================================================================
# Task Processor
# ============================================================================

class TaskProcessor:
    """Processes user tasks through Meta-Agent and Scheduler"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize Meta-Agent
        if config.use_mock:
            print_info("Using Mock mode (no API keys)")
            self.meta_agent = None  # Will use simple decomposition
        elif config.anthropic_key:
            self.meta_agent = MetaAgent(api_key=config.anthropic_key)
        else:
            self.meta_agent = None

        # Initialize execution agents
        self.agents = self._create_agents()

        # Initialize scheduler
        self.scheduler = Scheduler(self.agents)

    def _create_agents(self) -> dict:
        """Create available agents based on config"""
        agents = {}

        if self.config.use_mock:
            # Use mock agents for demo
            agents['claude'] = MockAgent('Claude', latency=2.0)
            agents['openai'] = MockAgent('OpenAI', latency=1.5)
            agents['gemini'] = MockAgent('Gemini', latency=1.0)
        else:
            # Use real agents
            if self.config.anthropic_key:
                agents['claude'] = ClaudeAgent(
                    api_key=self.config.anthropic_key,
                    max_concurrent=5
                )

            if self.config.openai_key:
                agents['openai'] = OpenAIAgent(
                    api_key=self.config.openai_key,
                    max_concurrent=3
                )

        return agents

    async def process(self, user_input: str, context: SessionContext) -> dict:
        """Process user task"""

        # Step 1: Decompose task
        print(f"\n{Colors.BOLD}🧠 Meta-Agent: Decomposing task...{Colors.END}")

        if self.meta_agent:
            # Use real Meta-Agent
            tasks = await self.meta_agent.decompose_task(user_input)
        else:
            # Simple mock decomposition
            tasks = self._mock_decomposition(user_input)

        # Step 2: Display plan
        print(f"\n{Colors.BOLD}📋 Plan:{Colors.END}")
        for i, task in enumerate(tasks, 1):
            agent_name = task.assigned_agent if hasattr(task, 'assigned_agent') else 'claude'
            print(f"  {i}. [{agent_name}] {task.description}")

        # Step 3: Ask for confirmation
        if not self.config.auto_execute:
            response = input(f"\n{Colors.BOLD}Execute plan? [Y/n]: {Colors.END}").strip().lower()
            if response and response != 'y':
                print_info("Execution cancelled")
                return {'status': 'cancelled'}

        # Step 4: Execute
        print(f"\n{Colors.BOLD}⚡ Executing tasks...{Colors.END}")
        results = await self.scheduler.schedule(tasks)

        # Step 5: Display results
        print()
        for task, result in zip(tasks, results):
            agent_name = task.assigned_agent if hasattr(task, 'assigned_agent') else 'unknown'
            if result.get('success'):
                print_success(f"[{agent_name}] {task.description} ({result.get('time', 0):.1f}s)")
            else:
                print_error(f"[{agent_name}] {task.description} failed")

        return {
            'status': 'completed',
            'tasks': len(tasks),
            'results': results
        }

    def _mock_decomposition(self, user_input: str) -> List[Task]:
        """Simple mock task decomposition"""

        # Analyze input to create reasonable decomposition
        user_lower = user_input.lower()

        if 'web' in user_lower or 'website' in user_lower or 'app' in user_lower:
            # Web development task
            return [
                Task(
                    id="1",
                    description="Design database schema",
                    prompt=f"Design database schema for: {user_input}",
                    assigned_agent='claude'
                ),
                Task(
                    id="2",
                    description="Implement backend API",
                    prompt=f"Implement backend API for: {user_input}",
                    assigned_agent='openai',
                    dependencies=['1']
                ),
                Task(
                    id="3",
                    description="Create frontend interface",
                    prompt=f"Create frontend for: {user_input}",
                    assigned_agent='claude',
                    dependencies=['2']
                ),
                Task(
                    id="4",
                    description="Write tests",
                    prompt=f"Write tests for: {user_input}",
                    assigned_agent='gemini',
                    dependencies=['2', '3']
                ),
            ]
        elif 'refactor' in user_lower:
            # Refactoring task
            return [
                Task(
                    id="1",
                    description="Analyze code structure",
                    prompt=f"Analyze code for: {user_input}",
                    assigned_agent='claude'
                ),
                Task(
                    id="2",
                    description="Apply refactoring",
                    prompt=f"Refactor: {user_input}",
                    assigned_agent='claude',
                    dependencies=['1']
                ),
                Task(
                    id="3",
                    description="Update tests",
                    prompt=f"Update tests for: {user_input}",
                    assigned_agent='gemini',
                    dependencies=['2']
                ),
            ]
        else:
            # Generic task
            return [
                Task(
                    id="1",
                    description="Analyze requirements",
                    prompt=f"Analyze: {user_input}",
                    assigned_agent='claude'
                ),
                Task(
                    id="2",
                    description="Implement solution",
                    prompt=f"Implement: {user_input}",
                    assigned_agent='openai',
                    dependencies=['1']
                ),
                Task(
                    id="3",
                    description="Verify and test",
                    prompt=f"Test: {user_input}",
                    assigned_agent='gemini',
                    dependencies=['2']
                ),
            ]


# ============================================================================
# Interactive REPL
# ============================================================================

class InteractiveCLI:
    """Main interactive command-line interface"""

    VERSION = "0.1.0 (Prototype)"

    def __init__(self):
        self.config = Config()
        self.session = SessionContext()
        self.processor = TaskProcessor(self.config)
        self.running = True

    def show_welcome(self):
        """Display welcome message"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("=" * 60)
        print(f"  Multi-Agent Code v{self.VERSION}")
        print("  Interactive AI Coding Assistant")
        print("=" * 60)
        print(f"{Colors.END}")
        print("\nType '/help' for commands, '/exit' to quit")
        print(f"{Colors.CYAN}💡 Tip: Try 'Build a todo app' or 'Refactor auth.py'{Colors.END}")

    def show_help(self):
        """Display help message"""
        print(f"\n{Colors.BOLD}Available Commands:{Colors.END}")
        print("  /help     - Show this help message")
        print("  /config   - Show current configuration")
        print("  /agents   - List available agents")
        print("  /history  - Show conversation history")
        print("  /clear    - Clear session context")
        print("  /exit     - Exit the CLI")
        print(f"\n{Colors.BOLD}Usage:{Colors.END}")
        print("  Just type what you want to do, and the AI will help!")
        print(f"\n{Colors.BOLD}Examples:{Colors.END}")
        print("  • Build a REST API for user management")
        print("  • Refactor this code to use async/await")
        print("  • Write tests for the authentication module")
        print("  • Explain the repository pattern")

    async def handle_command(self, command: str):
        """Handle special commands (starting with /)"""

        cmd = command.lower().strip()

        if cmd == '/help':
            self.show_help()

        elif cmd == '/config':
            self.config.display()

        elif cmd == '/agents':
            print(f"\n{Colors.BOLD}🤖 Available Agents:{Colors.END}")
            for name, agent in self.processor.agents.items():
                status = "✓" if agent else "✗"
                print(f"  {status} {name.capitalize()} - {agent.name}")

        elif cmd == '/history':
            print(f"\n{Colors.BOLD}📜 Session History:{Colors.END}")
            if self.session.history:
                for i, item in enumerate(self.session.history, 1):
                    print(f"\n{i}. {item['input']}")
                    print(f"   Status: {item['result'].get('status', 'unknown')}")
            else:
                print("  (empty)")

        elif cmd == '/clear':
            self.session = SessionContext()
            print_success("Session cleared")

        elif cmd == '/exit' or cmd == '/quit':
            print_info("Goodbye! 👋")
            self.running = False

        else:
            print_error(f"Unknown command: {command}")
            print("Type '/help' for available commands")

    async def process_task(self, user_input: str):
        """Process user task"""

        try:
            result = await self.processor.process(user_input, self.session)
            self.session.add_interaction(user_input, result)

            # Show summary
            if result['status'] == 'completed':
                print_success(f"\nCompleted {result['tasks']} tasks")

        except KeyboardInterrupt:
            print_info("\nTask cancelled by user")

        except Exception as e:
            print_error(f"Error: {str(e)}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()

    async def repl(self):
        """Main REPL loop"""

        self.show_welcome()

        while self.running:
            try:
                # Display prompt
                user_input = input(f"\n{Colors.BOLD}{Colors.CYAN}macode>{Colors.END} ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # Process as AI task
                    await self.process_task(user_input)

            except KeyboardInterrupt:
                print()  # New line
                response = input("Exit? [y/N]: ").strip().lower()
                if response == 'y':
                    self.running = False
                    print_info("Goodbye! 👋")

            except EOFError:
                # Ctrl+D pressed
                self.running = False
                print_info("\nGoodbye! 👋")

            except Exception as e:
                print_error(f"Unexpected error: {str(e)}")
                if self.config.verbose:
                    import traceback
                    traceback.print_exc()

    def run(self):
        """Start the CLI"""
        try:
            asyncio.run(self.repl())
        except KeyboardInterrupt:
            print_info("\nGoodbye! 👋")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    cli = InteractiveCLI()
    cli.run()


if __name__ == '__main__':
    main()
