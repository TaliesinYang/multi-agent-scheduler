# Multi-Agent Scheduler - Project Context

## Project Overview

**Course**: CSCI6650 - Advanced Topics in Operating Systems (Fall 2025)
**Institution**: Fairleigh Dickinson University, Vancouver Campus
**Type**: Academic Research Project - Group Assignment

This is a **Multi-Agent Task Scheduler** that demonstrates advanced OS concepts including:
- Concurrent task execution and scheduling
- Process management and inter-process communication
- Resource allocation and load balancing
- Distributed task execution across heterogeneous agents

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    User Task Input                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │    MetaAgentCLI      │ ◄─── Uses Claude/Codex/Gemini
          │ (Task Decomposition) │      for task breakdown
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   AgentSelector      │ ◄─── Smart agent selection
          │  (Capability-based)  │      based on task type
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  DependencyScheduler │ ◄─── Batching & parallelization
          │   (Batch Execution)  │      based on dependencies
          └──────────┬───────────┘
                     │
         ┌───────────┼────────────┐
         │           │            │
         ▼           ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Claude │  │ Codex  │  │ Gemini │
    │  CLI   │  │  CLI   │  │  CLI   │
    └────────┘  └────────┘  └────────┘
```

### File Structure

```
multi-agent-scheduler/
├── src/
│   ├── agents.py          # CLI agent implementations (subprocess execution)
│   ├── meta_agent.py      # Task decomposition logic
│   ├── scheduler.py       # Dependency-based task scheduler
│   ├── agent_selector.py  # Capability-based agent selection
│   ├── agent_config.yaml  # Agent capabilities and weights
│   ├── task_visualizer.py # Task execution visualization
│   ├── workspace_manager.py # Workspace isolation
│   └── config.py          # Configuration and API keys
├── demos/
│   ├── demo_cli_full.py   # Full system demonstration
│   ├── smart_demo.py      # Smart agent selection demo
│   └── demo.py            # Basic usage examples
├── tests/                 # Test suite
├── workspaces/            # Isolated agent execution environments
├── logs/                  # Execution logs with metrics
└── .claude/               # Claude CLI project configuration
└── .gemini/               # Gemini CLI project configuration
└── AGENTS.md             # This file (Codex context)
```

## Codex Agent Role

### Primary Responsibilities

As **Codex CLI**, your role in this system is:

1. **Code Implementation Tasks**
   - Implement functions and classes based on specifications
   - Generate boilerplate code and standard patterns
   - Create API endpoints and CRUD operations
   - Write unit tests and integration tests

2. **Code Refactoring**
   - Optimize existing code for performance
   - Apply design patterns
   - Improve code readability
   - Fix linting and type checking errors

3. **Documentation Generation**
   - Write docstrings for functions and classes
   - Generate API documentation
   - Create code examples

### NOT Responsible For

- System architecture design (Claude's role)
- Complex algorithm design (Claude's role)
- Simple documentation tasks (Gemini's role)
- Task decomposition (MetaAgent's role)

## Technical Stack

- **Language**: Python 3.8+
- **Concurrency**: asyncio (async/await paradigm)
- **Process Management**: subprocess for CLI execution
- **Configuration**: YAML (agent_config.yaml)
- **Logging**: JSON-formatted execution logs
- **Type Checking**: Python type hints throughout

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** (Google style) for all public functions/classes
- Prefer **pathlib** over os.path
- Use **async/await** for I/O operations
- Maximum line length: 88 characters (Black formatter)

### Example Function

```python
async def execute_task(
    task: Task,
    agent: BaseCLIAgent,
    workspace: Path,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Execute a single task using the specified agent.

    Args:
        task: Task object containing prompt and metadata
        agent: CLI agent instance to execute the task
        workspace: Workspace directory for execution
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary containing execution result and metrics

    Raises:
        TimeoutError: If execution exceeds timeout
        AgentExecutionError: If agent execution fails
    """
    # Implementation here
```

### Project-Specific Patterns

1. **Agent Execution**
   ```python
   # Always use async subprocess execution
   result = await agent.call(prompt=task.prompt, workspace=workspace)
   ```

2. **Error Handling**
   ```python
   # Use try-except with specific error types
   try:
       result = await execute_task(task, agent)
   except TimeoutError:
       logger.error(f"Task {task.task_id} timed out")
       # Retry logic
   ```

3. **Configuration Loading**
   ```python
   # Use pathlib for file paths
   config_path = Path(__file__).parent / "agent_config.yaml"
   with open(config_path, 'r') as f:
       config = yaml.safe_load(f)
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Structure

- Unit tests: `tests/test_*.py`
- Integration tests: `tests/integration/`
- Fixtures: `tests/conftest.py`

## Common Operations

### Execute Demo

```bash
cd /path/to/multi-agent-scheduler
python3 demos/demo_cli_full.py
```

### Check Types

```bash
mypy src/ --strict
```

### Linting

```bash
flake8 src/ --max-line-length=88
black src/ --check
```

## Agent Communication

All agents (including Codex) communicate via:
- **Input**: Task prompt as string
- **Output**: JSON response with result and metadata
- **Execution**: Isolated workspace directory
- **Logging**: Structured logs in `logs/` directory

## Current Development Status

- ✅ Core scheduler implementation
- ✅ CLI agent integration (Claude, Codex, Gemini)
- ✅ Smart agent selection
- ✅ Dependency-based batching
- ✅ Workspace isolation
- ✅ Execution logging and metrics
- 🔄 Project-level CLI configuration (in progress)
- ⏳ Performance optimization
- ⏳ Web UI dashboard

## Notes for Codex

- The project is fully async - always use `async def` and `await`
- All CLI calls are subprocess executions - use `RobustCLIAgent.call()`
- Workspace isolation is critical - never write outside workspace directories
- Configuration is centralized in `src/agent_config.yaml`
- Error handling should be defensive - agents may fail unpredictably
- Logging is JSON-formatted for metrics tracking

## Resources

- Project GitHub: (To be published)
- Course Materials: `/resource/Course Information/`
- Agent Config: `src/agent_config.yaml`
- Example Logs: `logs/execution_*.log`
