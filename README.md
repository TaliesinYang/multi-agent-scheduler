# Multi-Agent Intelligent Scheduler

> CSCI-6650 Advanced Topics in Operating Systems - Term Project
>
> An intelligent system for scheduling multiple AI agents with support for parallel/serial execution, task dependency analysis, and cost optimization

---

## Project Overview

Current AI agent systems primarily use serial execution mode, where one task must complete before the next can begin. This approach is inefficient when handling parallelizable tasks, such as simultaneously generating multiple design proposals or concurrently developing multiple functional modules.

This project implements a **Multi-Agent Intelligent Scheduler** capable of:

- **Atomic Task Decomposition**: AI automatically breaks tasks into 15-20 atomic subtasks (<5min each)
- **Real-time Topology Visualization**: Live dependency graph with progress tracking
- **Workspace Isolation**: File operations in dedicated workspaces with session continuity
- **Smart Scheduling**: Automatically analyzes task dependencies to determine parallel or serial execution
- **Cost Optimization**: Selects the most suitable AI based on task type (simple tasks use free Gemini, complex tasks use Claude)
- **Performance Improvement**: Achieves 40-60% latency reduction through parallel execution
- **Personal Use Scenarios**: Designed for individual users without requiring enterprise-level deployment

---

## System Architecture

```
       User Input: "Build a website"
              │
              ▼
   ┌──────────────────────────────┐
   │    Meta-Agent (NEW!)         │ ◄── AI-powered task decomposition
   │    - Complexity analysis      │
   │    - Task decomposition       │
   └──────────────┬───────────────┘
                  │ [Subtasks: DB, API, Frontend, Tests]
                  ▼
   ┌─────────────────────────────────────────────┐
   │         Multi-Agent Scheduler               │
   ├─────────────────────────────────────────────┤
   │                                             │
   │   ┌─────────────────────────────────┐      │
   │   │   Scheduler                      │      │
   │   │   - Task dependency analysis     │      │
   │   │   - Parallel/serial decisions    │      │
   │   │   - Intelligent agent selection  │      │
   │   └─────────┬───────────────────────┘      │
   │             │                               │
   │   ┌─────────┴──────────┬──────────┐       │
   │   │                    │          │        │
   │   ▼                    ▼          ▼        │
   │ ┌──────┐          ┌────────┐  ┌────────┐  │
   │ │Claude│          │ OpenAI │  │ Gemini │  │
   │ │API/CLI│          │  API   │  │  CLI   │  │
   │ └──────┘          └────────┘  └────────┘  │
   │                                             │
   └─────────────────────────────────────────────┘
              │
              ▼
      Aggregated Results
```

### Core Components

1. **Meta-Agent** (`meta_agent.py`)
   - AI-driven task decomposition
   - Automatic dependency analysis
   - Task complexity assessment
   - Structured output (JSON)

2. **Agent Manager** (`agents.py`)
   - Unified AI agent interface
   - Support for Claude, OpenAI, Gemini (both API and CLI)
   - CLI agents with timeout handling and process cleanup
   - Asynchronous calls and concurrency control
   - Performance statistics and monitoring

3. **Task Visualizer** (`task_visualizer.py`)
   - Real-time ASCII topology display
   - Dependency-aware batch grouping
   - Status tracking (pending/in_progress/completed/failed)
   - Progress bar with completion percentage
   - Support for dynamic subtask insertion

4. **Scheduler** (`scheduler.py`)
   - Task dependency analysis (DAG construction)
   - Topological sorting and batch division
   - Parallel/serial/hybrid execution
   - Intelligent agent selection strategies

5. **Workspace Manager** (`workspace_manager.py`)
   - Isolated workspace directories
   - Session-based continuous development
   - Metadata tracking and state management

6. **Smart Demo** (`smart_demo.py`, `demo_cli_full.py`)
   - Complete intelligent workflow
   - Automatic task decomposition + parallel scheduling
   - 100% CLI-based execution (no API keys required)
   - Three execution modes: API, CLI, Mock
   - Interactive and preset modes
   - Performance analysis and reporting

5. **Basic Demo** (`demo.py`)
   - 5 basic demonstration scenarios
   - Performance comparison tests
   - Interactive menu

---

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) API keys: Claude, OpenAI
- (Optional) CLI tools for subscription-based usage:
  - Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
  - Gemini CLI: `npm install -g @google/gemini-cli`

### Installation

```bash
# 1. Clone/download the project
cd multi-agent-scheduler

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys (optional, not needed for Mock mode)
cp config.py.example config.py
# Edit config.py to add your API keys
```

### Quick Run (Mock Mode)

```bash
# No API keys needed, run immediately
python demo.py
# Select "2. Use Mock Agents"
```

### Using Real APIs

```bash
# 1. Configure keys
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-proj-..."

# 2. Install Gemini CLI (optional)
npm install -g @google/gemini-cli
gemini auth login

# 3. Run Demo
python demo.py
# Select "1. Use Real API"
```

### Using CLI Agents (Cost-Effective)

CLI mode uses subscription-based services instead of pay-per-token APIs, significantly reducing costs (~$10/month vs $30-50/month).

```bash
# 1. Install CLI tools
npm install -g @anthropic-ai/claude-code
npm install -g @google/gemini-cli

# 2. (Optional) Set up API key for Meta-Agent task decomposition
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# 3. Run Smart Demo with CLI mode
python smart_demo.py
# Select "2. CLI mode"
# Tasks will be executed using CLI agents instead of APIs

# Benefits:
# - Lower cost: ~$10/month subscription vs pay-per-token
# - Same quality: Uses the same models as API
# - Faster setup: No API key management for execution agents
```

**Cost Comparison:**

| Mode | Meta-Agent | Execution | Monthly Cost | Best For |
|------|-----------|-----------|-------------|----------|
| **Mock** | Fallback | Simulated | Free | Testing, demos |
| **CLI** | API | CLI tools | ~$10 | Regular use, cost-sensitive |
| **API** | API | API | ~$30-50 | Heavy usage, enterprise |

### Smart Demo (Recommended)

Intelligent demo with AI-powered automatic task decomposition:

```bash
# Mock mode (no API needed, suitable for demonstrations)
python smart_demo.py
# Select "3. Mock mode"
# Then input a complex task, e.g.: "Build a todo list web application"

# CLI mode (subscription-based, cost-effective)
export ANTHROPIC_API_KEY="sk-ant-api03-..."  # For Meta-Agent
python smart_demo.py
# Select "2. CLI mode"
# Tasks will be executed using CLI agents

# Real API mode (pay-per-token)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
python smart_demo.py
# Select "1. Real API mode"
# Then input a task, Meta-Agent will automatically decompose and schedule execution

# Quick test (verify functionality)
python smart_demo.py --test

# Preset scenario demonstration
python smart_demo.py --preset

# Interactive mode
python smart_demo.py --interactive
```

**Smart Demo Workflow**:
1. User inputs a complex task (e.g., "Develop a website")
2. Meta-Agent uses AI to analyze and automatically break down into subtasks
3. Scheduler schedules parallel execution based on dependencies
4. Display aggregated results and performance report

---

## Usage Examples

### Basic Parallel Scheduling

```python
import asyncio
from agents import ClaudeAgent, OpenAIAgent, GeminiAgent
from scheduler import MultiAgentScheduler, Task

async def main():
    # Initialize agents
    agents = {
        'claude': ClaudeAgent(api_key="your-key"),
        'openai': OpenAIAgent(api_key="your-key"),
        'gemini': GeminiAgent()
    }

    # Create scheduler
    scheduler = MultiAgentScheduler(agents)

    # Define tasks
    tasks = [
        Task(id="task1", prompt="Explain quantum computing", task_type="simple"),
        Task(id="task2", prompt="Write a sorting algorithm", task_type="coding"),
        Task(id="task3", prompt="Analyze cloud computing advantages", task_type="analysis")
    ]

    # Execute scheduling (automatically decides parallel/serial)
    result = await scheduler.schedule(tasks)

    # Print results
    scheduler.print_summary(result)

asyncio.run(main())
```

### Performance Comparison

```python
# Compare parallel vs serial performance
comparison = await scheduler.compare_performance(tasks)

print(f"Performance improvement: {comparison['performance_gain_percent']:.1f}%")
# Output: Performance improvement: 58.3%
```

### Dependency Scheduling

```python
# Define tasks with dependencies
tasks = [
    Task(id="design", prompt="Design API", task_type="coding"),
    Task(id="implement", prompt="Implement API", depends_on=["design"]),
    Task(id="test", prompt="Write tests", depends_on=["implement"])
]

# Automatic batch execution (hybrid mode)
result = await scheduler.schedule(tasks)
# Batch 1: [design] (parallel)
# Batch 2: [implement]
# Batch 3: [test]
```

---

## Demo Scenarios

After running `python demo.py`, you can choose from the following demonstrations:

1. **Basic Parallel Scheduling** - Demonstrates parallel execution of multiple independent tasks
2. **Performance Comparison** - Compares serial vs parallel execution time
3. **Dependency Scheduling** - Demonstrates intelligent batching of dependent tasks
4. **Smart Agent Selection** - Shows how to select AI based on task type
5. **Mock Agent Testing** - Quick testing without API requirements

---

## Operating System Concept Mapping

This project directly implements and demonstrates core OS concepts:

### 1. Process Scheduling
- **Concept**: How CPU allocates time among multiple processes
- **Implementation**: AI tasks mapped as processes, scheduler determines execution order
- **Strategies**: Priority scheduling (priority), Round-robin (batch execution)

### 2. Concurrency Control
- **Concept**: Managing concurrent execution of multiple processes
- **Implementation**: Using `asyncio.Semaphore` to limit concurrency
- **Mechanisms**: Semaphore, Mutex

### 3. Inter-Process Communication (IPC)
- **Concept**: Data exchange between processes
- **Implementation**: Task dependency passing (DAG), result aggregation
- **Methods**: Message Passing

### 4. Resource Allocation
- **Concept**: Allocation and management of limited resources
- **Implementation**: API quotas as resources, dynamically allocated to tasks
- **Strategies**: Starvation avoidance, deadlock prevention

### 5. Deadlock Prevention
- **Concept**: Avoiding circular waiting for resources among processes
- **Implementation**: DAG ensures acyclic dependencies, topological sorting

---

## Performance Evaluation

### Test Scenario: 4 Independent Tasks

| Execution Mode | Total Time | Performance Gain |
|----------------|------------|------------------|
| Serial Execution | 8.2s | - |
| Parallel Execution | 3.1s | **62%** |

### Resource Utilization

| Metric | Serial | Parallel | Improvement |
|--------|--------|----------|-------------|
| CPU Idle Time | 75% | 10% | ↓ 87% |
| Total Token Consumption | 5000 | 5000 | Same |
| API Call Count | 4 | 4 | Same |

**Conclusion**: Parallel execution significantly reduces latency without increasing costs.

---

## Project Structure

```
multi-agent-scheduler/
├── agents.py              # AI agent wrapper (150 lines)
│   ├── BaseAgent         # Base agent class
│   ├── ClaudeAgent       # Claude API
│   ├── OpenAIAgent       # OpenAI API
│   ├── GeminiAgent       # Gemini CLI
│   └── MockAgent         # Mock for testing
│
├── scheduler.py           # Core scheduler (200 lines)
│   ├── Task              # Task definition
│   ├── ExecutionResult   # Result wrapper
│   └── MultiAgentScheduler  # Main scheduler class
│       ├── analyze_dependencies()
│       ├── select_agent()
│       ├── execute_parallel()
│       ├── execute_serial()
│       └── execute_with_dependencies()
│
├── demo.py               # Demo program (150 lines)
│   ├── demo_basic_parallel()
│   ├── demo_performance_comparison()
│   ├── demo_dependency_scheduling()
│   ├── demo_agent_selection()
│   └── demo_mock_agents()
│
├── config.py.example     # Configuration template
├── requirements.txt      # Dependency list
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore file
└── README.md            # This document
```

**Total Lines of Code**: ~500 lines (excluding comments)

---

## Presentation Script (15 minutes)

### 1. Problem Introduction (2 minutes)

"Existing AI systems execute tasks serially. But many scenarios can be parallelized, such as:
- Simultaneously generating 3 design proposals
- Concurrent development of frontend and backend
- Simultaneously analyzing multiple datasets

Our scheduler addresses this pain point."

### 2. Core Innovation (3 minutes)

"Three major innovations:
1. **Intelligent Scheduling**: Automatically analyzes task dependencies, decides parallel/serial execution
2. **Cost Optimization**: Simple tasks use free Gemini, complex tasks use Claude
3. **Personal Use**: Desktop application, no enterprise deployment needed"

### 3. Code Demonstration (5 minutes)

```bash
python demo.py
# Select: 2. Performance Comparison
# Display: Parallel is 60% faster than serial
```

### 4. OS Concept Mapping (5 minutes)

"This project directly implements core OS concepts:
- **Process Scheduling**: Tasks=processes, scheduler=CPU scheduler
- **Concurrency Control**: Semaphore controls concurrency
- **Resource Management**: API quotas=CPU time slices
- **IPC**: Task dependency passing"

---

## Future Extensions

- [ ] Web UI (Streamlit/Gradio)
- [ ] DAG visualization (D3.js)
- [ ] Cost tracking dashboard
- [ ] Support for more AI models (Llama, Mistral)
- [ ] Task history and replay
- [ ] Configuration file system
- [ ] Docker containerized deployment
- [ ] Distributed scheduling (multi-machine)

---

## Contributing

This is an academic project, and discussions and suggestions are welcome.

---

## License

This project is for educational purposes and follows the MIT License.

---

## Team

CSCI-6650 Operating Systems - Group Project

---

## References

1. Tran, K.-T., et al. (2025). Multi-Agent Collaboration Mechanisms: A Survey of LLMs. arXiv:2501.06322.
2. Rasal, S., & Maheshwary, G. (2024). Orchestrated Problem Solving with Multi-Agent LLMs. arXiv:2402.16713.
3. Microsoft Research. (2025). Optimizing Sequential Multi-Step Tasks with Parallel LLM Agents. arXiv:2507.08944.

---

**Last Updated**: January 2025

**Demo Readiness Status**: Ready to run immediately
