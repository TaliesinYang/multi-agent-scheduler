# Interactive CLI Prototype

This directory contains a working prototype of the enhanced Multi-Agent Code CLI.

## What is this?

A proof-of-concept implementation showing how to transform the multi-agent scheduler into an interactive CLI tool similar to Claude Code, but with multi-agent orchestration.

## Quick Start

### Run the Prototype

```bash
# From project root
python prototypes/interactive_cli_prototype.py
```

### Example Session

```
Multi-Agent Code v0.1.0 (Prototype)
Interactive AI Coding Assistant

Type '/help' for commands, '/exit' to quit

macode> /help
Available Commands:
  /help     - Show this help message
  /config   - Show current configuration
  /agents   - List available agents
  /history  - Show conversation history
  /clear    - Clear session context
  /exit     - Exit the CLI

macode> Build a REST API for user management

🧠 Meta-Agent: Decomposing task...

📋 Plan:
  1. [claude] Design database schema
  2. [openai] Implement backend API
  3. [claude] Create frontend interface
  4. [gemini] Write tests

Execute plan? [Y/n]: y

⚡ Executing tasks...

✅ [claude] Design database schema (2.3s)
✅ [openai] Implement backend API (3.1s)
✅ [claude] Create frontend interface (2.8s)
✅ [gemini] Write tests (1.5s)

✅ Completed 4 tasks

macode> /exit
Goodbye! 👋
```

## Features Demonstrated

### ✅ Core Features

1. **Interactive REPL**
   - Command prompt
   - Real-time input/output
   - Session management

2. **Command System**
   - `/help` - Show help
   - `/config` - Show configuration
   - `/agents` - List agents
   - `/history` - Show history
   - `/clear` - Clear session
   - `/exit` - Exit CLI

3. **Task Processing**
   - Automatic task decomposition
   - Intelligent agent selection
   - User confirmation
   - Parallel execution

4. **Multiple Modes**
   - **Mock mode**: No API keys needed (instant demo)
   - **API mode**: Real Claude/OpenAI integration

5. **User Experience**
   - Color-coded output
   - Progress indicators
   - Error handling
   - Keyboard shortcuts (Ctrl+C, Ctrl+D)

## Configuration

The prototype automatically detects API keys from environment:

```bash
# For real API mode
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-proj-..."

# Then run
python prototypes/interactive_cli_prototype.py
```

If no API keys are found, it runs in mock mode (perfect for demos).

## Architecture

```
InteractiveCLI (REPL)
    ↓
TaskProcessor (orchestrator)
    ↓
Meta-Agent (task decomposition)
    ↓
Scheduler (parallel execution)
    ↓
Agents (Claude, OpenAI, Gemini)
```

## Code Structure

```python
# Main components
InteractiveCLI      # REPL loop, command handling
TaskProcessor       # Task decomposition and execution
SessionContext      # Conversation history
Config              # Configuration management

# Supporting
Colors              # Terminal colors
print_*()           # Formatted output functions
```

## Extending the Prototype

### Add a New Command

```python
async def handle_command(self, command: str):
    # ... existing commands ...

    elif cmd == '/stats':
        # Your new command
        print("📊 Statistics:")
        print(f"  Tasks completed: {len(self.session.history)}")
```

### Add a New Agent

```python
def _create_agents(self) -> dict:
    agents = {}
    # ... existing agents ...

    agents['custom'] = MyCustomAgent(...)
    return agents
```

### Customize Task Decomposition

```python
def _mock_decomposition(self, user_input: str) -> List[Task]:
    # Add your own decomposition logic
    if 'your-keyword' in user_input:
        return [
            Task(...),
            Task(...),
        ]
```

## Next Steps

This prototype demonstrates the core concept. To build the full product:

1. **Week 1-2**: Enhanced REPL
   - Add `prompt-toolkit` for better input (history, completion)
   - Add `rich` for beautiful output
   - Implement multi-line input

2. **Week 3-4**: Real Integration
   - Integrate with real Meta-Agent API
   - Add streaming output
   - Improve agent selection logic

3. **Week 5-6**: Polish
   - Configuration file support
   - Workspace management
   - Better error handling
   - Package for distribution

See `docs/IMPLEMENTATION_ROADMAP.md` for detailed plan.

## Comparison with Final Product

| Feature | Prototype | Final Product |
|---------|-----------|---------------|
| **REPL** | ✅ Basic | ✅ Advanced (history, completion) |
| **Commands** | ✅ Core commands | ✅ Extensive commands |
| **Task Processing** | ✅ Works | ✅ Optimized |
| **Streaming** | ❌ Simulated | ✅ Real-time |
| **Config File** | ❌ No | ✅ YAML config |
| **Workspace** | ❌ No | ✅ Full workspace support |
| **Batch Mode** | ❌ No | ✅ Batch execution |
| **Workflows** | ❌ No | ✅ YAML workflows |
| **Plugins** | ❌ No | ✅ Plugin system |

## Try It Now!

```bash
# Run in mock mode (no setup needed)
python prototypes/interactive_cli_prototype.py

# Try these commands:
macode> /help
macode> /agents
macode> Build a todo app
macode> /history
macode> /exit
```

## Feedback

This is a prototype to validate the concept. Feedback welcome!

- What features are most important?
- What's missing?
- What should be simplified?

See `docs/PRODUCT_VISION.md` for the full product vision.
