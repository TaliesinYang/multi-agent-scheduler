# Multi-Agent Intelligent Scheduler

> CSCI-6650 Advanced Topics in Operating Systems - Term Project
>
> An intelligent DAG-based task scheduling system for multiple AI agents with automatic dependency analysis and parallel execution optimization

---

## 📊 Key Results (Day 7 Evaluation)

Our end-to-end evaluation demonstrates the effectiveness of DAG-based scheduling:

| Test Group | Tasks | Structure | Speedup | Performance |
|------------|-------|-----------|---------|-------------|
| db_product_sales | 2 | Linear | 0.70× | Overhead dominates |
| os_user_analysis | 3 | Linear | **1.57×** | Sweet spot |
| os_system_health_fanout | 8 | Fan-out | 0.997× | Minimal benefit |
| web_scraping_fanout | 12 | Fan-out | **1.31×** | Clear advantage |
| data_pipeline_mixed | 16 | Mixed DAG | **1.32×** | Best savings |

**Critical Finding**: DAG scheduling shows clear advantage for tasks with **≥12 subtasks** and complex dependency structures.

📄 **Full Report**: [results/end_to_end/EXPERIMENT_REPORT.md](results/end_to_end/EXPERIMENT_REPORT.md)

---

## Project Overview

Current AI agent systems primarily use serial execution mode, where one task must complete before the next can begin. This project implements a **DAG-based Multi-Agent Scheduler** that:

- ✅ **Atomic Task Decomposition**: AI automatically breaks complex tasks into parallelizable subtasks
- ✅ **DAG Scheduling**: Kahn's topological sort algorithm for dependency-aware execution
- ✅ **Smart Parallel Execution**: Automatically identifies independent tasks for concurrent execution
- ✅ **CLI Integration**: Support for Claude and Gemini CLI tools
- ✅ **AgentBench Integration**: Standardized OS and Database interaction tasks
- ✅ **Performance Optimization**: Achieves up to 1.57× speedup on suitable workloads

---

## 🏗️ Project Structure

### Core Code (src/)
```
src/
├── scheduler.py                    # Base task scheduling framework
├── meta_agent_simple.py            # Task decomposition engine
│
└── orchestration/                  # 🔥 DAG Scheduling Core (Day 6-7)
    ├── dag_scheduler.py            # DAG scheduling (Kahn's algorithm)
    ├── cli_executor.py             # CLI subprocess execution (600s timeout)
    ├── meta_agent.py               # Advanced task decomposition
    ├── complexity_analyzer.py      # Task complexity analysis
    ├── dependency_injector.py      # Dependency injection framework
    └── agentbench_loader.py        # AgentBench task loader
```

### Experiments and Evaluation
```
experiments/
├── day7_evaluation/                # End-to-end evaluation
│   ├── run_end_to_end_test.py     # Main evaluation script
│   ├── generate_report.py         # Report generation
│   └── generate_tables.py         # Table generation
│
└── temp_tests/                     # Temporary test scripts
    └── test_*.py                   # Various integration tests
```

### Results and Documentation
```
results/
├── end_to_end/                     # Day 7 evaluation results
│   ├── EXPERIMENT_REPORT.md        # Complete evaluation report
│   ├── tables/                     # Publication-ready tables
│   └── raw_data/                   # JSON + CSV data
│
└── paper_data/                     # Paper data and analysis
    ├── mock/                       # Mock benchmark results
    ├── real/                       # Real experiment data
    ├── comparison/                 # Comparison analyses
    └── cli_performance/            # CLI performance data

docs/
├── NEXT_SESSION_PLAN.md            # Development roadmap
├── COMPLETE_CLEANUP_PLAN.md        # Complete cleanup plan
└── templates/                      # Paper section templates
    └── section_4_template.md       # Section 4 template
```

### Archived Components
```
archived/                           # Experimental features (not in git)
├── demos/                          # Demo scripts
├── monitoring/                     # Prometheus/Grafana configs
└── web_ui/                         # Flask web interface
```

### Official Tests
```
tests/                              # Unit and integration tests
├── test_basic.py
├── test_workflow.py
└── benchmark/                      # Performance benchmarks
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Claude CLI or Gemini CLI installed
- AgentBench dependency tasks dataset

### Installation
```bash
git clone https://github.com/yourusername/multi-agent-scheduler.git
cd multi-agent-scheduler
pip install -r requirements.txt
```

### Run Day 7 Evaluation
```bash
# From project root
python experiments/day7_evaluation/run_end_to_end_test.py
```

### Basic Usage
```python
from src.orchestration.dag_scheduler import DAGScheduler
from src.orchestration.cli_executor import CLIExecutor
from src.scheduler import Task

# Create tasks
tasks = [
    Task(id="task1", description="Analyze database", dependencies=[]),
    Task(id="task2", description="Generate report", dependencies=["task1"]),
]

# Schedule and execute
scheduler = DAGScheduler(tasks, executor=CLIExecutor(timeout=600))
results = await scheduler.execute()
```

---

## 🎯 Key Features

### 1. DAG Scheduling Algorithm
- **Kahn's Topological Sort**: Ensures correct dependency ordering
- **Parallel Execution**: Identifies independent tasks for concurrent execution
- **Cycle Detection**: Prevents invalid dependency graphs

### 2. CLI Integration
- **Claude CLI**: Anthropic's Claude models via subprocess
- **Gemini CLI**: Google's Gemini models via subprocess
- **Timeout Management**: 600s default timeout with graceful handling

### 3. AgentBench Integration
- **Standardized Tasks**: OS interaction and Database operations
- **Dependency Groups**: Pre-defined task sets with complex dependencies
- **Evaluation Framework**: Consistent benchmarking across experiments

### 4. Performance Optimization
- **12-Task Threshold**: Minimum task count for DAG scheduling benefit
- **Overhead Analysis**: ~27-30s DAG scheduling overhead
- **Success Rate**: 100% with 600s timeout (vs 85.4% with 60s)

---

## 📖 Documentation

- **Architecture**: See system architecture diagram in original README (below)
- **Evaluation Report**: [results/end_to_end/EXPERIMENT_REPORT.md](results/end_to_end/EXPERIMENT_REPORT.md)
- **Usage Guides**: [docs/](docs/) directory
- **API Documentation**: Inline docstrings in source code

---

## 🔬 Evaluation Methodology

Our Day 7 evaluation tested 5 dependency groups (41 tasks total):

1. **Linear Dependencies**: Sequential task chains (2-3 tasks)
2. **Fan-out Dependencies**: Parallel analysis tasks (8-12 tasks)
3. **Mixed DAG**: Complex dependency graphs (16 tasks)

**Modes Compared**:
- **Sequential**: Baseline (one task at a time)
- **Hybrid**: DAG scheduling with parallel execution

**Key Metrics**:
- Total execution time
- Success rate
- Speedup ratio
- Task completion status

---

## 🎓 Academic Context

**Course**: CSCI-6650 Advanced Topics in Operating Systems
**Institution**: Fairleigh Dickinson University, Vancouver Campus
**Term**: Fall 2025
**Topic**: Multi-Agent Task Scheduling and Parallel Execution

**Research Questions**:
1. When does DAG scheduling outperform sequential execution?
2. What is the minimum task count threshold for benefits?
3. How do different dependency structures affect performance?

---

## 🤝 Contributing

This is an academic project. For collaboration:
1. Check [docs/PROJECT_CLEANUP_PLAN.md](docs/PROJECT_CLEANUP_PLAN.md) for project structure
2. Follow existing code style (type hints, docstrings)
3. Add tests for new features
4. Run evaluation suite before submitting changes

---

## 📄 License

See LICENSE file for details.

---

## System Architecture

The system implements a 4-layer architecture that clearly separates orchestration logic from execution details:

```
┌─────────────────────────────────────────────────┐
│           User Input Layer                      │
│  - Natural language task descriptions           │
│  - CLI commands (multi_agent_cli.py)            │
│  - AgentBench task definitions                  │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│           Meta-Agent Layer                      │
│  - Task decomposition (meta_agent.py)           │
│  - Complexity analysis (complexity_analyzer.py) │
│  - Prompt template generation                   │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│        Orchestration Layer                      │
│  - DAG scheduling (dag_scheduler.py)            │
│  - Dependency management & topological sort     │
│  - Batch parallelization strategy               │
│  - Result aggregation (DAGResult)               │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│          Execution Layer                        │
│  - CLI tool invocation (cli_executor.py)        │
│  - Subprocess management (asyncio)              │
│  - Output parsing & success detection           │
│  - Timeout handling (600s default)              │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│            Agent Layer                          │
│  - Claude CLI Agent (claude)                    │
│  - Gemini Agent (gemini)                        │
│  - Codex Agent (codex)                          │
│  - OpenAI API Agent (optional)                  │
│  File: src/agents.py                            │
└─────────────────────────────────────────────────┘
```

### Layer Responsibilities & Code Mapping

| Layer | Core Responsibilities | Key Files | OS Concepts |
|-------|----------------------|-----------|-------------|
| **User Input** | Interface abstraction | `multi_agent_cli.py` | User space |
| **Meta-Agent** | Task analysis & decomposition | `src/orchestration/meta_agent.py`<br>`src/orchestration/complexity_analyzer.py` | Process creation |
| **Orchestration** | Scheduling & dependency management | `src/orchestration/dag_scheduler.py`<br>`src/orchestration/dependency_injector.py` | Process scheduling |
| **Execution** | Resource allocation & tool invocation | `src/orchestration/cli_executor.py`<br>`src/orchestration/executor.py` | Process management |
| **Agent** | Task execution & result generation | `src/agents.py` | Process/Thread execution |

### Data Flow

```
Task Definition (User)
    → Task Analysis (Meta-Agent)
    → Dependency Graph (Orchestration)
    → Batch Execution (Execution)
    → Agent Calls (Agent)
    → TaskResult Collection
    → DAGResult Aggregation
    → User Output
```

**Key Data Structures:**
- `Task`: Task definition with dependencies
- `TaskResult`: Individual task execution result
- `DAGResult`: Complete execution summary with statistics

---

**Last Updated**: 2025-11-17
**Project Status**: ✅ Day 7 Evaluation Complete
