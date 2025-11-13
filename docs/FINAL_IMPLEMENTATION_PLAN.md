# Final Implementation Plan: Multi-Agent Scheduler as Gemini CLI Extension

**Date**: 2025-11-05
**Decision**: Use **MCP Server Extension** instead of Fork
**Rationale**: Avoid upstream sync conflicts, 100% reuse existing Python code, maintain Gemini CLI native updates

---

## Executive Summary

After deep research, we found the **optimal solution**: Build a **FastMCP-based MCP Server** that extends Gemini CLI without forking. This approach:

✅ **Solves upstream conflict problem**: Gemini CLI updates independently, no merge conflicts
✅ **Preserves our architecture**: Gemini is just the REPL frontend, not the executor
✅ **100% Python**: Reuse all existing Meta Agent + Scheduler code
✅ **Simple installation**: `fastmcp install gemini-cli multi-agent-server.py`
✅ **Native experience**: Users interact with official Gemini CLI + our multi-agent tools

---

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Gemini CLI (Official)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  REPL Interface                                      │   │
│  │  - Interactive prompt                                │   │
│  │  - Session management                                │   │
│  │  - Context files (GEMINI.md)                         │   │
│  │  - Streaming output                                  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐   │
│  │  MCP Client                                          │   │
│  │  - Discovers MCP servers from settings.json         │   │
│  │  - Registers tools from all servers                 │   │
│  │  - Routes tool calls via MCP protocol               │   │
│  └───────────────────┬─────────────────────────────────┘   │
└────────────────────┬─┴─────────────────────────────────────┘
                     │
                     │ MCP Protocol (JSON-RPC)
                     │
┌────────────────────▼──────────────────────────────────────┐
│        Multi-Agent Scheduler MCP Server (Our Code)        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  FastMCP Server (Python)                           │   │
│  │                                                     │   │
│  │  Registered Tools:                                 │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ @mcp.tool()                                  │  │   │
│  │  │ def decompose_task(task: str) -> TaskPlan   │  │   │
│  │  │   """Use Meta Agent to decompose task"""    │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ @mcp.tool()                                  │  │   │
│  │  │ def execute_parallel(plan: TaskPlan) ->     │  │   │
│  │  │   """Execute tasks in parallel via agents"""│  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ @mcp.tool()                                  │  │   │
│  │  │ def multi_agent_workflow(task: str) ->      │  │   │
│  │  │   """One-shot: decompose + execute"""       │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └────────────────────┬───────────────────────────────┘   │
└─────────────────────┬─┴───────────────────────────────────┘
                      │
                      │ Internal Python calls
                      │
┌─────────────────────▼─────────────────────────────────────┐
│         Existing Multi-Agent Scheduler (No Changes)       │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Meta Agent                                        │   │
│  │  - Task decomposition                              │   │
│  │  - Agent selection                                 │   │
│  │  - Dependency analysis                             │   │
│  └────────────────────┬───────────────────────────────┘   │
│                       │                                    │
│  ┌────────────────────▼───────────────────────────────┐   │
│  │  Scheduler                                         │   │
│  │  - Parallel execution                              │   │
│  │  - DAG-based scheduling                            │   │
│  │  - Progress tracking                               │   │
│  └────────────────────┬───────────────────────────────┘   │
│                       │                                    │
│  ┌────────────────────▼───────────────────────────────┐   │
│  │  Sub Agents (Existing)                             │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────┐ │   │
│  │  │ Claude   │ OpenAI   │ Gemini   │ Codex CLI... │ │   │
│  │  │ Agent    │ Agent    │ Agent    │ Agent        │ │   │
│  │  └──────────┴──────────┴──────────┴──────────────┘ │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

#### 1. **Gemini CLI = Frontend Only** ✅ (Addresses your concern)

- Gemini CLI只负责：
  - REPL交互界面
  - 会话管理
  - MCP客户端
  - 输出展示

- **Gemini NOT used for task execution**
- All task decomposition → Meta Agent
- All task execution → Our Scheduler + Sub Agents

#### 2. **MCP Server = Integration Layer**

- Thin adapter between Gemini CLI and our scheduler
- Registers tools that Gemini CLI can discover
- Translates MCP protocol to our internal APIs

#### 3. **Zero Changes to Existing Code** ✅

- `src/meta_agent.py` - No changes
- `src/scheduler.py` - No changes
- `src/agents.py` - No changes
- `src/task.py` - No changes

We only ADD a new file: `src/mcp_server.py`

---

## Why This Solves the Fork Conflict Problem

### ❌ Fork Approach (Original Plan 1):

```
Our Fork of Gemini CLI
    ↓
Modify internal code
    ↓
Gemini CLI updates → MERGE CONFLICTS 💥
    ↓
Manual resolution every time
```

**Problems**:
- Every Gemini CLI update = potential conflicts
- Need to understand Gemini's internal changes
- May break our modifications
- High maintenance burden

### ✅ MCP Extension Approach (New Plan):

```
Official Gemini CLI (updates independently)
    ↓ (stable MCP protocol interface)
Our MCP Server (independent codebase)
    ↓
Our scheduler (unchanged)
```

**Advantages**:
- ✅ Gemini CLI updates: `npm update @google/gemini-cli` (no conflicts)
- ✅ Our code updates: independent Python development
- ✅ Interface: MCP protocol is stable and versioned
- ✅ Zero maintenance burden from upstream

**Why It Works**:
- MCP is a **standard protocol** (like HTTP)
- Gemini CLI treats our server as **black box**
- We treat Gemini CLI as **black box**
- Only contract: MCP JSON-RPC messages

---

## Implementation Plan

### Phase 1: MCP Server Prototype (Week 1)

#### 1.1 Setup Development Environment

```bash
# Install Gemini CLI (official)
npm install -g @google/gemini-cli

# Install FastMCP
pip install fastmcp

# Create MCP server file
mkdir -p src/mcp
touch src/mcp/server.py
```

#### 1.2 Create Minimal MCP Server

**File**: `src/mcp/server.py` (v0.1 - proof of concept)

```python
"""
Multi-Agent Scheduler MCP Server
Extends Gemini CLI with multi-agent orchestration capabilities
"""

from fastmcp import FastMCP
from typing import Dict, List, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.meta_agent import MetaAgent
from src.scheduler import Scheduler
from src.agents import ClaudeAgent, OpenAIAgent, GeminiAgent

# Initialize FastMCP server
mcp = FastMCP("Multi-Agent Scheduler")

# Initialize our existing components (singleton pattern)
_meta_agent = None
_scheduler = None

def get_meta_agent() -> MetaAgent:
    """Lazy initialization of Meta Agent"""
    global _meta_agent
    if _meta_agent is None:
        _meta_agent = MetaAgent()
    return _meta_agent

def get_scheduler() -> Scheduler:
    """Lazy initialization of Scheduler"""
    global _scheduler
    if _scheduler is None:
        # Load config from environment or default
        agents = [
            ClaudeAgent(),
            OpenAIAgent(),
            GeminiAgent()
        ]
        _scheduler = Scheduler(agents=agents)
    return _scheduler


@mcp.tool()
def decompose_task(task: str) -> Dict[str, Any]:
    """
    Decompose a complex task into subtasks using Meta Agent

    Args:
        task: High-level task description from user

    Returns:
        Task plan with subtasks, assigned agents, and dependencies

    Example:
        task = "Build a REST API with tests"
        result = {
            "tasks": [
                {"id": 1, "description": "Design schema", "agent": "claude"},
                {"id": 2, "description": "Implement API", "agent": "openai"},
                {"id": 3, "description": "Write tests", "agent": "gemini"}
            ],
            "dependencies": {"2": [1], "3": [2]}
        }
    """
    meta_agent = get_meta_agent()
    plan = meta_agent.decompose(task)

    return {
        "status": "success",
        "plan": plan.to_dict(),
        "task_count": len(plan.tasks),
        "estimated_time": plan.estimate_time(),
        "estimated_cost": plan.estimate_cost()
    }


@mcp.tool()
def execute_parallel(plan_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a task plan in parallel using the Scheduler

    Args:
        plan_json: Task plan from decompose_task()

    Returns:
        Execution results from all agents

    Example:
        results = {
            "status": "success",
            "completed": 3,
            "failed": 0,
            "total_time": 4.3,
            "results": [...]
        }
    """
    scheduler = get_scheduler()

    # Convert JSON to TaskPlan object
    from src.task import TaskPlan
    plan = TaskPlan.from_dict(plan_json)

    # Execute with scheduler
    results = scheduler.schedule(plan.tasks)

    return {
        "status": "success",
        "completed": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "total_time": max([r.get("latency", 0) for r in results]),
        "results": results
    }


@mcp.tool()
def multi_agent_workflow(task: str, auto_execute: bool = False) -> Dict[str, Any]:
    """
    One-shot workflow: Decompose task AND execute in parallel

    This is the main tool users will interact with.
    It combines decompose_task() and execute_parallel().

    Args:
        task: High-level task description
        auto_execute: If False, return plan for approval. If True, execute immediately.

    Returns:
        If auto_execute=False: Task plan for user approval
        If auto_execute=True: Execution results

    Example usage in Gemini CLI:
        > Use multi_agent_workflow to build a todo app with tests

        (Gemini will call this tool, show plan, ask for approval, then execute)
    """
    # Step 1: Decompose
    decomposition = decompose_task(task)
    plan = decomposition["plan"]

    if not auto_execute:
        # Return plan for user approval
        return {
            "status": "awaiting_approval",
            "plan": plan,
            "message": "Review the plan. Set auto_execute=true to proceed."
        }

    # Step 2: Execute
    execution = execute_parallel(plan)

    return {
        "status": "completed",
        "plan": plan,
        "execution": execution,
        "summary": {
            "task_count": decomposition["task_count"],
            "completed": execution["completed"],
            "failed": execution["failed"],
            "total_time": execution["total_time"],
            "estimated_cost": decomposition["estimated_cost"]
        }
    }


@mcp.tool()
def list_available_agents() -> List[Dict[str, str]]:
    """
    List all configured agents and their capabilities

    Returns:
        List of agents with name, model, and capabilities
    """
    scheduler = get_scheduler()

    return [
        {
            "name": agent.name,
            "model": getattr(agent, "model", "unknown"),
            "type": type(agent).__name__,
            "capabilities": getattr(agent, "capabilities", [])
        }
        for agent in scheduler.agents
    ]


# Define prompts (accessible as slash commands in Gemini CLI)
@mcp.prompt()
def explain_multi_agent() -> str:
    """Explain how the multi-agent system works"""
    return """
# Multi-Agent Scheduler

This system extends Gemini CLI with multi-agent orchestration:

## How It Works

1. **Task Decomposition**: Your task is analyzed by a Meta Agent
2. **Agent Selection**: Subtasks are assigned to the best agent (Claude, GPT, Gemini)
3. **Parallel Execution**: Independent tasks run simultaneously
4. **Result Aggregation**: All results are combined

## Available Tools

- `multi_agent_workflow`: One-shot task execution (recommended)
- `decompose_task`: See task breakdown without executing
- `execute_parallel`: Execute a plan
- `list_available_agents`: See configured agents

## Example

> Build a REST API with authentication and tests

The system will:
1. Assign schema design to Claude (best for architecture)
2. Assign API implementation to GPT-4 (best for code)
3. Assign tests to Gemini (fast and cheap)
4. Run all in parallel (2-3x faster than sequential)
"""


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
```

#### 1.3 Install MCP Server to Gemini CLI

```bash
# Method 1: FastMCP auto-install (recommended)
cd /path/to/multi-agent-scheduler
fastmcp install gemini-cli src/mcp/server.py

# Method 2: Manual configuration
# Edit ~/.gemini/settings.json and add:
# {
#   "mcpServers": {
#     "multi-agent": {
#       "command": "python",
#       "args": ["/path/to/multi-agent-scheduler/src/mcp/server.py"],
#       "env": {
#         "ANTHROPIC_API_KEY": "$ANTHROPIC_API_KEY",
#         "OPENAI_API_KEY": "$OPENAI_API_KEY"
#       }
#     }
#   }
# }
```

#### 1.4 Test Integration

```bash
# Start Gemini CLI
gemini

# In Gemini CLI prompt:
> List available tools

# Should see:
# - multi_agent_workflow
# - decompose_task
# - execute_parallel
# - list_available_agents

# Test basic workflow:
> Use multi_agent_workflow to write a Python function that calculates fibonacci

# Expected flow:
# 1. Gemini calls decompose_task via MCP
# 2. Meta Agent breaks down task
# 3. Gemini shows plan to user
# 4. User approves
# 5. Gemini calls execute_parallel via MCP
# 6. Scheduler executes with Claude/GPT/Gemini
# 7. Results shown in Gemini CLI
```

**Success Criteria**:
- ✅ MCP server starts without errors
- ✅ Tools registered in Gemini CLI
- ✅ Can call decompose_task and get valid plan
- ✅ Can execute plan and get results
- ✅ All existing agents (Claude, GPT, Gemini) work

---

### Phase 2: Enhanced Features (Week 2)

#### 2.1 Add Streaming Support

**Problem**: Current implementation returns results after all tasks complete. We want real-time progress.

**Solution**: Use MCP's progress notifications

```python
@mcp.tool()
async def execute_parallel_streaming(plan_json: Dict[str, Any]) -> Dict[str, Any]:
    """Execute with real-time progress updates"""
    scheduler = get_scheduler()
    plan = TaskPlan.from_dict(plan_json)

    # Use async generator for progress
    async for progress in scheduler.schedule_streaming(plan.tasks):
        # Send progress notification via MCP
        yield {
            "type": "progress",
            "task_id": progress["task_id"],
            "agent": progress["agent"],
            "status": progress["status"],  # "running" | "completed" | "failed"
            "message": progress.get("message", "")
        }

    # Final result
    yield {
        "type": "complete",
        "results": progress["final_results"]
    }
```

#### 2.2 Add Configuration Management

**File**: `src/mcp/config.py`

```python
"""Configuration management for MCP server"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

class MCPConfig:
    """Load configuration from multiple sources"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load from: env vars > config.yaml > defaults"""

        # Defaults
        config = {
            "agents": {
                "claude": {
                    "enabled": True,
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "model": "claude-sonnet-4-5-20250929",
                    "max_concurrent": 5
                },
                "openai": {
                    "enabled": True,
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": "gpt-4-turbo",
                    "max_concurrent": 3
                },
                "gemini": {
                    "enabled": True,
                    "api_key": os.getenv("GOOGLE_API_KEY"),
                    "model": "gemini-2.5-pro",
                    "max_concurrent": 5
                }
            },
            "meta_agent": {
                "model": "claude-sonnet-4-5-20250929",
                "provider": "claude"
            },
            "preferences": {
                "auto_execute": False,
                "parallel": True,
                "show_cost_estimate": True,
                "verbose": True
            }
        }

        # Override with config.yaml if exists
        config_file = Path(__file__).parent.parent.parent / "config" / "mcp_config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                user_config = yaml.safe_load(f)
                config.update(user_config)

        return config

    def get_enabled_agents(self) -> list:
        """Return list of enabled agent configs"""
        return [
            (name, cfg)
            for name, cfg in self.config["agents"].items()
            if cfg.get("enabled", True)
        ]
```

#### 2.3 Add Cost Tracking

```python
@mcp.tool()
def get_cost_report() -> Dict[str, Any]:
    """Get cost breakdown for recent tasks"""
    scheduler = get_scheduler()

    return {
        "total_cost_usd": scheduler.get_total_cost(),
        "cost_by_agent": scheduler.get_cost_breakdown(),
        "task_count": scheduler.get_task_count(),
        "avg_cost_per_task": scheduler.get_avg_cost()
    }
```

---

### Phase 3: Production Readiness (Week 3-4)

#### 3.1 Error Handling

```python
@mcp.tool()
def multi_agent_workflow(task: str, auto_execute: bool = False) -> Dict[str, Any]:
    """Enhanced with error handling"""
    try:
        # Validate input
        if not task or len(task.strip()) == 0:
            return {
                "status": "error",
                "error": "Task description cannot be empty"
            }

        # Decompose
        decomposition = decompose_task(task)

        if decomposition["status"] != "success":
            return {
                "status": "error",
                "error": "Task decomposition failed",
                "details": decomposition
            }

        # ... rest of execution

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
```

#### 3.2 Testing

**File**: `tests/test_mcp_server.py`

```python
"""Test MCP server integration"""

import pytest
from src.mcp.server import decompose_task, execute_parallel, multi_agent_workflow

def test_decompose_task():
    """Test task decomposition"""
    result = decompose_task("Write a Python hello world function")

    assert result["status"] == "success"
    assert "plan" in result
    assert result["task_count"] >= 1

def test_multi_agent_workflow_no_execute():
    """Test workflow without execution"""
    result = multi_agent_workflow(
        "Build a simple calculator",
        auto_execute=False
    )

    assert result["status"] == "awaiting_approval"
    assert "plan" in result

@pytest.mark.integration
def test_full_workflow():
    """Test complete workflow (requires API keys)"""
    result = multi_agent_workflow(
        "Write a Python function to reverse a string",
        auto_execute=True
    )

    assert result["status"] == "completed"
    assert result["execution"]["completed"] > 0
```

#### 3.3 Documentation

**File**: `docs/MCP_SERVER_GUIDE.md`

```markdown
# Multi-Agent Scheduler MCP Server Guide

## Installation

### Prerequisites
- Python 3.8+
- Gemini CLI installed (`npm install -g @google/gemini-cli`)
- API keys: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY

### Quick Start

1. Install FastMCP:
   ```bash
   pip install fastmcp
   ```

2. Install MCP server to Gemini CLI:
   ```bash
   cd /path/to/multi-agent-scheduler
   fastmcp install gemini-cli src/mcp/server.py
   ```

3. Start Gemini CLI:
   ```bash
   gemini
   ```

4. Verify installation:
   ```
   > List available tools
   ```

## Usage Examples

### Example 1: Simple Task
```
> Use multi_agent_workflow to write a Python quicksort implementation
```

### Example 2: Complex Project
```
> Use multi_agent_workflow to build a REST API for user management with authentication, PostgreSQL database, unit tests, and API documentation
```

### Example 3: Manual Control
```
> Use decompose_task to plan a full-stack todo app
(Review plan)
> Use execute_parallel with the plan to execute
```

## Configuration

Edit `config/mcp_config.yaml`:

```yaml
agents:
  claude:
    enabled: true
    model: claude-sonnet-4-5-20250929
    max_concurrent: 5

  openai:
    enabled: true
    model: gpt-4-turbo
    max_concurrent: 3

meta_agent:
  model: claude-sonnet-4-5-20250929

preferences:
  auto_execute: false  # Ask before running
  parallel: true
  show_cost_estimate: true
```

## Troubleshooting

### MCP server not appearing
- Check `~/.gemini/settings.json` has `multi-agent` server configured
- Restart Gemini CLI
- Check server logs: `gemini mcp logs multi-agent`

### Tasks failing
- Verify API keys are set
- Check agent configuration in `mcp_config.yaml`
- Run tests: `pytest tests/test_mcp_server.py`
```

---

## Comparison: Fork vs MCP Extension

| Aspect | Fork Approach | MCP Extension Approach |
|--------|---------------|------------------------|
| **Upstream Updates** | ❌ Merge conflicts | ✅ Independent updates |
| **Maintenance Burden** | ❌ High (ongoing merges) | ✅ Low (stable interface) |
| **Code Reuse** | ⚠️ Need to port to TypeScript | ✅ 100% Python reuse |
| **Development Speed** | ⚠️ 4-6 weeks (porting) | ✅ 2-3 weeks (thin adapter) |
| **Architecture** | ❌ Gemini executes tasks | ✅ Gemini = frontend only |
| **Gemini Role** | ❌ Direct executor | ✅ REPL + tool router |
| **Our Scheduler** | ⚠️ Needs porting | ✅ No changes needed |
| **Installation** | ❌ Replace Gemini CLI | ✅ `fastmcp install` |
| **User Experience** | ⚠️ Custom CLI | ✅ Native Gemini CLI |
| **Conflict Risk** | ❌ Every update | ✅ None (protocol-based) |
| **Legal Status** | ✅ Apache 2.0 fork OK | ✅ Extension mechanism |

---

## Risk Assessment

### Technical Risks

#### Risk 1: MCP Protocol Changes
**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- MCP is a stable, versioned protocol
- Gemini CLI maintains backward compatibility
- We can version-lock if needed

#### Risk 2: Performance Overhead
**Likelihood**: Low
**Impact**: Low
**Mitigation**:
- MCP is JSON-RPC (lightweight)
- No network calls (STDIO transport)
- Negligible latency (<10ms)

#### Risk 3: Limited by MCP Capabilities
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- MCP supports all we need: tools, prompts, resources
- Can return rich content (text, images, structured data)
- Streaming supported via progress notifications

### Operational Risks

#### Risk 4: User Confusion (Two Components)
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- Clear installation guide
- One-command setup: `fastmcp install`
- Package as single distribution

#### Risk 5: Configuration Complexity
**Likelihood**: Low
**Impact**: Low
**Mitigation**:
- Sensible defaults
- Auto-detect API keys from environment
- Fallback to interactive setup

---

## Success Criteria

### Week 1 (Prototype)
- ✅ MCP server starts and registers tools
- ✅ Gemini CLI can call decompose_task
- ✅ Can execute simple task end-to-end
- ✅ All existing agents work (Claude, GPT, Gemini)

### Week 2 (Features)
- ✅ Streaming progress updates
- ✅ Configuration management
- ✅ Cost tracking
- ✅ Error handling

### Week 3 (Production)
- ✅ Comprehensive tests (unit + integration)
- ✅ Documentation complete
- ✅ Installation script
- ✅ Example workflows

### Week 4 (Beta Release)
- ✅ 10 beta users testing
- ✅ Bug fixes
- ✅ Performance optimization
- ✅ Published on PyPI (optional)

---

## Timeline

```
Week 1: MCP Server Prototype
├─ Day 1-2: Setup FastMCP, basic tools
├─ Day 3-4: Integration with existing scheduler
└─ Day 5-7: Testing and debugging

Week 2: Enhanced Features
├─ Day 8-9: Streaming support
├─ Day 10-11: Configuration management
└─ Day 12-14: Cost tracking, polish

Week 3: Production Readiness
├─ Day 15-17: Error handling, validation
├─ Day 18-19: Tests (unit, integration)
└─ Day 20-21: Documentation

Week 4: Beta & Release
├─ Day 22-24: Beta user testing
├─ Day 25-26: Bug fixes
└─ Day 27-28: Final polish, release
```

---

## Next Immediate Actions

### This Week
1. ✅ Complete research (DONE - this document)
2. [ ] Create `src/mcp/server.py` prototype
3. [ ] Test basic integration with Gemini CLI
4. [ ] Validate with simple task execution

### Next Week
1. [ ] Implement streaming support
2. [ ] Add configuration management
3. [ ] Create test suite
4. [ ] Write user guide

---

## Conclusion

The **MCP Extension approach is superior** to forking because:

1. **Solves the upstream conflict problem**: Gemini CLI updates don't affect our code
2. **Preserves our architecture**: Gemini is just the REPL, not the executor
3. **100% code reuse**: All Python code stays unchanged
4. **Faster development**: 2-3 weeks vs 4-6 weeks
5. **Better user experience**: Native Gemini CLI + our capabilities
6. **Lower maintenance**: Stable MCP protocol interface

**Recommendation**: Proceed with MCP Extension implementation.

**Next Step**: Create prototype `src/mcp/server.py` and validate integration.
