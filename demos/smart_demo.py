"""
Smart Demo - Intelligent Multi-Agent Scheduler
Intelligent Demo: Automatic Task Decomposition + Parallel Scheduling

This demo showcases the complete intelligent workflow:
1. User inputs a complex task
2. Meta-Agent decomposes it into subtasks automatically
3. Scheduler executes subtasks in parallel with optimal agents
4. Results are aggregated and displayed
"""

import asyncio
import os
import time
from typing import Dict, List
from dotenv import load_dotenv

from src.meta_agent import MetaAgent
from src.scheduler import MultiAgentScheduler, Task, ExecutionMode
from src.agents import ClaudeAgent, ClaudeCLIAgent, OpenAIAgent, GeminiAgent, MockAgent


class SmartSchedulerDemo:
    """
    Intelligent Scheduler Demo with AI-powered task decomposition
    """

    def __init__(self, use_mock: bool = False, use_cli: bool = False):
        """
        Initialize the smart demo

        Args:
            use_mock: If True, use Mock agents (no API needed)
            use_cli: If True, use CLI agents instead of API (subscription-based, cost-effective)
        """
        self.use_mock = use_mock
        self.use_cli = use_cli
        self.meta_agent = None
        self.scheduler = None

    def setup_agents(self):
        """Setup AI agents based on configuration"""
        load_dotenv()

        if self.use_mock:
            print("🔧 Using Mock agents (no API required)")
            agents = {
                'claude': MockAgent(name="Claude", delay=0.8),
                'openai': MockAgent(name="OpenAI", delay=0.8),
                'gemini': MockAgent(name="Gemini", delay=0.5)
            }
            # Mock Meta-Agent won't be created (use fallback)
            self.meta_agent = None

        elif self.use_cli:
            print("🔧 Setting up CLI agents (100% CLI, no API keys required)")

            # Use CLI version of Meta-Agent (no API key needed)
            from meta_agent import MetaAgentCLI
            self.meta_agent = MetaAgentCLI()
            print("✓ Meta-Agent using Claude CLI for task decomposition")

            # Initialize CLI execution agents
            agents = {}

            # Add Claude CLI
            try:
                agents['claude'] = ClaudeCLIAgent()
                print("✓ Claude CLI agent added")
            except Exception as e:
                print(f"⚠️  Claude CLI not available: {e}")

            # Add Codex CLI
            try:
                from agents import CodexCLIAgent
                agents['codex'] = CodexCLIAgent()
                print("✓ Codex CLI agent added")
            except Exception as e:
                print(f"⚠️  Codex CLI not available: {e}")

            # Add Gemini CLI
            try:
                agents['gemini'] = GeminiAgent()
                print("✓ Gemini CLI agent added")
            except Exception as e:
                print(f"⚠️  Gemini CLI not available: {e}")

            if not agents:
                print("❌ No CLI agents available. Please ensure CLI tools are installed and authenticated:")
                print("   • Claude: claude auth login")
                print("   • Codex: codex auth login")
                print("   • Gemini: gemini auth login")
                raise ValueError("No CLI agents available")

        else:
            print("🔧 Setting up real API agents...")

            # Get API keys
            claude_key = os.getenv("ANTHROPIC_API_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")

            if not claude_key:
                print("❌ ANTHROPIC_API_KEY not found in environment")
                print("💡 Tip: Copy .env.example to .env and add your API key")
                raise ValueError("Missing API key")

            # Initialize Meta-Agent with Claude
            self.meta_agent = MetaAgent(api_key=claude_key)

            # Initialize execution agents
            agents = {
                'claude': ClaudeAgent(api_key=claude_key),
            }

            # Add OpenAI if available
            if openai_key:
                agents['openai'] = OpenAIAgent(api_key=openai_key)
            else:
                print("⚠️  OpenAI API key not found, using only Claude")

            # Add Gemini CLI (free, no API key needed)
            try:
                agents['gemini'] = GeminiAgent()
                print("✓ Gemini CLI agent added")
            except:
                print("⚠️  Gemini CLI not available")

        self.scheduler = MultiAgentScheduler(agents)
        print(f"✓ Initialized {len(agents)} agents: {list(agents.keys())}")

    async def run_smart_workflow(self, user_input: str):
        """
        Run the complete intelligent workflow

        Args:
            user_input: User's complex task description
        """
        print("\n" + "="*60)
        print("🚀 SMART WORKFLOW - Intelligent Task Decomposition")
        print("="*60)
        print(f"📝 User Input: {user_input}")
        print()

        # Step 1: Task Decomposition
        print("🧠 Step 1: Decomposing task with AI...")
        start_decompose = time.time()

        if self.meta_agent and not self.use_mock:
            # Use real Meta-Agent
            tasks = await self.meta_agent.decompose_task(user_input, max_tasks=6)
            self.meta_agent.print_task_tree(tasks)
        else:
            # Fallback: Manual decomposition for mock mode
            print("⚠️  Using manual decomposition (mock mode)")
            tasks = self._manual_decomposition(user_input)
            if self.meta_agent:
                self.meta_agent.print_task_tree(tasks)
            else:
                self._print_simple_task_list(tasks)

        decompose_time = time.time() - start_decompose
        print(f"⏱️  Decomposition time: {decompose_time:.2f}s")

        # Step 2: Parallel Execution
        print("\n⚡ Step 2: Executing subtasks in parallel...")
        start_execute = time.time()

        result = await self.scheduler.schedule(tasks, mode=ExecutionMode.AUTO)

        execute_time = time.time() - start_execute
        print(f"⏱️  Execution time: {execute_time:.2f}s")

        # Step 3: Display Results
        print("\n📊 Step 3: Results Summary")
        self._display_results(result)

        # Total time
        total_time = decompose_time + execute_time
        print(f"\n🎯 Total Workflow Time: {total_time:.2f}s")

        # Performance insight
        if len(tasks) > 1:
            estimated_serial_time = len(tasks) * 2.0  # Estimate 2s per task
            improvement = (estimated_serial_time - execute_time) / estimated_serial_time * 100
            print(f"💡 Performance Gain: {improvement:.1f}% faster than serial execution")

        return result

    def _manual_decomposition(self, user_input: str) -> List[Task]:
        """
        Fallback manual decomposition for mock mode

        Provides reasonable default decomposition based on common patterns
        """
        # Simple keyword-based decomposition
        lower_input = user_input.lower()

        if "website" in lower_input or "web app" in lower_input:
            return [
                Task(id="task1", prompt="Design database schema and data models",
                     task_type="coding", priority=1),
                Task(id="task2", prompt="Design user interface and page layouts",
                     task_type="coding", priority=1),
                Task(id="task3", prompt="Implement backend API endpoints",
                     task_type="coding", priority=2, depends_on=["task1"]),
                Task(id="task4", prompt="Implement frontend components",
                     task_type="coding", priority=2, depends_on=["task2"]),
                Task(id="task5", prompt="Write unit and integration tests",
                     task_type="coding", priority=3, depends_on=["task3", "task4"])
            ]

        elif "api" in lower_input:
            return [
                Task(id="task1", prompt="Design API endpoints and data models",
                     task_type="analysis", priority=1),
                Task(id="task2", prompt="Implement CRUD operations",
                     task_type="coding", priority=2, depends_on=["task1"]),
                Task(id="task3", prompt="Add authentication and authorization",
                     task_type="coding", priority=2, depends_on=["task1"]),
                Task(id="task4", prompt="Write API tests and documentation",
                     task_type="simple", priority=3, depends_on=["task2", "task3"])
            ]

        elif "research" in lower_input or "analyze" in lower_input:
            return [
                Task(id="task1", prompt="Literature review and background research",
                     task_type="analysis", priority=1),
                Task(id="task2", prompt="Data collection and organization",
                     task_type="simple", priority=2, depends_on=["task1"]),
                Task(id="task3", prompt="Analysis and findings",
                     task_type="analysis", priority=3, depends_on=["task2"]),
                Task(id="task4", prompt="Write summary report",
                     task_type="simple", priority=4, depends_on=["task3"])
            ]

        else:
            # Generic decomposition
            return [
                Task(id="task1", prompt=f"Research and plan: {user_input}",
                     task_type="analysis", priority=1),
                Task(id="task2", prompt="Implement core functionality",
                     task_type="coding", priority=2, depends_on=["task1"]),
                Task(id="task3", prompt="Testing and validation",
                     task_type="simple", priority=3, depends_on=["task2"])
            ]

    def _print_simple_task_list(self, tasks: List[Task]):
        """Print task list without MetaAgent"""
        print("\n" + "="*60)
        print("📋 Task Breakdown:")
        print("="*60)
        for i, task in enumerate(tasks):
            symbol = "└─" if i == len(tasks) - 1 else "├─"
            deps_str = f" [depends on: {', '.join(task.depends_on)}]" if task.depends_on else ""
            print(f"{symbol} {task.id}: {task.prompt}{deps_str}")
        print("="*60)

    def _display_results(self, result):
        """Display execution results in a formatted way"""
        print("="*60)

        # Success rate
        successful = sum(1 for r in result.results if r.get('success', False))
        success_rate = successful / len(result.results) * 100 if result.results else 0
        print(f"✅ Success Rate: {successful}/{len(result.results)} ({success_rate:.1f}%)")

        # Agent distribution
        agent_counts = {}
        for r in result.results:
            agent = r.get('agent_selected', 'unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        print(f"🤖 Agent Distribution: {agent_counts}")

        # Show first few results
        print(f"\n📄 Sample Results (showing first 3):")
        for i, r in enumerate(result.results[:3]):
            result_text = r.get('result', '')[:100]  # First 100 chars
            print(f"\n  Task {i+1} [{r.get('agent_selected', '?')}]:")
            print(f"  {result_text}...")

        print("="*60)


async def interactive_demo():
    """
    Interactive mode: User can input their own tasks
    """
    print("\n" + "🌟"*30)
    print("  SMART MULTI-AGENT SCHEDULER - Interactive Demo")
    print("🌟"*30)

    # Choose mode
    print("\n📋 Choose Demo Mode:")
    print("  1. Real API mode (pay-per-token)")
    print("  2. CLI mode (subscription-based, cost-effective) 🆕")
    print("  3. Mock mode (no API needed, instant results)")

    choice = input("\nYour choice (1/2/3): ").strip()
    use_mock = (choice == "3")
    use_cli = (choice == "2")

    # Initialize
    demo = SmartSchedulerDemo(use_mock=use_mock, use_cli=use_cli)
    try:
        demo.setup_agents()
    except ValueError as e:
        print(f"\n❌ Setup failed: {e}")
        return

    # Main loop
    while True:
        print("\n" + "-"*60)
        print("💬 Enter your task (or 'quit' to exit):")
        print("Examples:")
        print("  - Build a todo list web application")
        print("  - Create a REST API for user management")
        print("  - Research the benefits of microservices")

        user_input = input("\n> ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            print("❌ Please enter a task")
            continue

        # Run workflow
        await demo.run_smart_workflow(user_input)

        # Continue?
        cont = input("\n🔄 Try another task? (y/n): ").strip().lower()
        if cont != 'y':
            print("\n👋 Goodbye!")
            break


async def preset_demo():
    """
    Preset demo with example tasks (for presentation)
    """
    print("\n" + "🌟"*30)
    print("  SMART MULTI-AGENT SCHEDULER - Preset Demo")
    print("🌟"*30)

    # Choose mode
    print("\n📋 Choose Demo Mode:")
    print("  1. Real API mode (pay-per-token)")
    print("  2. CLI mode (subscription-based, cost-effective) 🆕")
    print("  3. Mock mode (recommended for quick demo)")

    choice = input("\nYour choice (1/2/3): ").strip()
    use_mock = (choice == "3")
    use_cli = (choice == "2")

    demo = SmartSchedulerDemo(use_mock=use_mock, use_cli=use_cli)
    try:
        demo.setup_agents()
    except ValueError as e:
        print(f"\n❌ Setup failed: {e}")
        print("💡 Switching to mock mode...")
        demo = SmartSchedulerDemo(use_mock=True)
        demo.setup_agents()

    # Preset examples
    examples = [
        "Build a todo list web application with user authentication",
        "Create a REST API for managing blog posts",
        "Research and compare microservices vs monolithic architectures",
        "Develop a command-line tool for file organization"
    ]

    print("\n📚 Available Examples:")
    for i, ex in enumerate(examples, 1):
        print(f"  {i}. {ex}")
    print(f"  {len(examples)+1}. Custom input")

    choice = input(f"\nSelect example (1-{len(examples)+1}): ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(examples):
            user_input = examples[idx]
        else:
            user_input = input("\n💬 Enter your task: ").strip()
    except:
        user_input = examples[0]  # Default

    # Run
    await demo.run_smart_workflow(user_input)


async def quick_test():
    """
    Quick test for validation (no user input needed)
    """
    print("\n" + "🧪"*30)
    print("  QUICK TEST - Validating Smart Scheduler")
    print("🧪"*30)

    demo = SmartSchedulerDemo(use_mock=True)
    demo.setup_agents()

    test_input = "Build a simple REST API for task management"
    print(f"\n🔍 Test Input: {test_input}")

    result = await demo.run_smart_workflow(test_input)

    # Validation
    assert result.task_count >= 3, "Should have at least 3 subtasks"
    assert result.total_time < 10, "Should complete in <10s (mock mode)"

    print("\n✅ Quick test PASSED")


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--test":
            await quick_test()
        elif mode == "--preset":
            await preset_demo()
        elif mode == "--interactive":
            await interactive_demo()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python smart_demo.py [--test|--preset|--interactive]")
    else:
        # Default: Preset demo
        await preset_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
