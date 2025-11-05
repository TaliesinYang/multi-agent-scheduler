# 合法实施策略：构建多 Agent 版 Claude Code

**目标**: 在不侵犯 Claude Code 版权的前提下，构建类似但更强大的多 Agent 编码助手

---

## 一、三种合法路径对比

### 路径 1: Claude Code 插件（最快）

**时间**: 1-2 周
**难度**: ⭐
**功能完整度**: ⭐⭐
**推荐用途**: 快速验证概念

```bash
# 项目结构
claude-multi-agent-plugin/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── orchestrator.md
│   ├── parallel-executor.md
│   └── cost-optimizer.md
├── commands/
│   ├── parallel.md
│   ├── batch.md
│   └── optimize.md
└── README.md
```

**优点**:
- ✅ 利用 Claude Code 现有 UI
- ✅ 快速上手，1-2 周完成
- ✅ 无需重复造轮子

**缺点**:
- ❌ 功能受限于插件 API
- ❌ 依赖 Claude Code
- ❌ 难以实现真正的并行执行

**适用场景**: 技术验证、用户调研

---

### 路径 2: MCP Server（平衡）

**时间**: 2-4 周
**难度**: ⭐⭐
**功能完整度**: ⭐⭐⭐
**推荐用途**: 与 Claude Code 互补

```python
# multi_agent_scheduler/mcp_server.py
class MultiAgentMCPServer:
    """
    将多 Agent 系统暴露为 MCP 服务器
    Claude Code 可以通过 MCP 协议调用
    """

    def __init__(self):
        self.meta_agent = MetaAgent()
        self.scheduler = Scheduler()

    async def handle_tool_call(self, tool, params):
        if tool == 'decompose_task':
            return await self.meta_agent.decompose(
                params['task'],
                params.get('context', {})
            )

        elif tool == 'execute_parallel':
            return await self.scheduler.schedule(
                params['tasks'],
                parallel=True
            )

        elif tool == 'optimize_cost':
            return await self.optimize_agent_selection(
                params['tasks']
            )
```

**使用方式**:
```bash
# 1. 启动 MCP Server
python -m multi_agent_scheduler mcp-serve

# 2. Claude Code 配置
# .claude/mcp.json
{
  "mcpServers": {
    "multi-agent": {
      "command": "python",
      "args": ["-m", "multi_agent_scheduler", "mcp-serve"]
    }
  }
}

# 3. 在 Claude Code 中使用
$ claude
> Use multi-agent to build a blog with parallel execution

[Claude Code] Calling multi-agent MCP server...
[Multi-Agent] Task decomposed into 4 parallel tasks
[Multi-Agent] Executing...
✅ Done in 3.2s
```

**优点**:
- ✅ 充分利用现有代码
- ✅ 保持 Claude Code 的优秀 UI
- ✅ 真正的并行执行
- ✅ 与 Claude Code 互补

**缺点**:
- ⚠️ 需要实现 MCP 协议
- ⚠️ 交互体验受 Claude Code 限制

**适用场景**: 与 Claude Code 集成，提供高级功能

---

### 路径 3: 独立构建（推荐）⭐⭐⭐⭐⭐

**时间**: 6-8 周 MVP
**难度**: ⭐⭐⭐
**功能完整度**: ⭐⭐⭐⭐⭐
**推荐用途**: 长期产品

**完整的独立产品，参考 Claude Code 设计但代码独立**

```bash
# 项目结构
multi-agent-code/
├── src/
│   ├── cli/
│   │   ├── repl.py              # 交互式 REPL
│   │   ├── modes.py             # Plan/Execute 模式
│   │   ├── display.py           # 终端 UI
│   │   └── streaming.py         # 流式输出
│   ├── orchestration/
│   │   ├── meta_agent.py        # 任务分解
│   │   ├── scheduler.py         # 并行调度
│   │   └── optimizer.py         # 成本优化
│   ├── agents/
│   │   ├── claude.py
│   │   ├── openai.py
│   │   └── custom.py
│   ├── plugins/
│   │   ├── manager.py           # 插件管理
│   │   └── loader.py            # 插件加载
│   └── mcp/
│       ├── server.py            # MCP Server
│       └── client.py            # MCP Client
├── docs/
├── tests/
└── setup.py
```

**优点**:
- ✅ 完全掌控代码
- ✅ 可以实现任何功能
- ✅ 不依赖第三方
- ✅ 可以商业化

**缺点**:
- ⚠️ 开发周期长
- ⚠️ 需要自己实现 UI

**适用场景**: 长期产品开发

---

## 二、推荐的分阶段策略

### 阶段 1: 快速验证（Week 1-2）

**目标**: 验证多 Agent 概念是否受用户欢迎

**方案**: 创建 Claude Code 插件

**步骤**:

```bash
# 1. 创建插件结构
mkdir claude-multi-agent-plugin
cd claude-multi-agent-plugin

# 2. 创建 plugin.json
mkdir -p .claude-plugin
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "multi-agent",
  "version": "0.1.0",
  "description": "Multi-agent parallel execution for Claude Code",
  "author": "Your Name",
  "commands": ["parallel", "batch", "optimize"],
  "agents": ["orchestrator"]
}
EOF

# 3. 创建 /parallel 命令
mkdir commands
cat > commands/parallel.md << 'EOF'
---
name: parallel
description: Execute tasks in parallel using multiple agents
---

# Parallel Execution

Break down the user's request into parallel tasks and execute simultaneously.

## Steps:
1. Analyze task dependencies
2. Group independent tasks
3. Assign to different agents (Claude, GPT-4, Gemini)
4. Execute in parallel
5. Merge results

## Example:
User: Build a REST API with frontend
→ Task 1 (Claude): Backend API
→ Task 2 (GPT-4): Frontend (runs parallel)
→ Task 3 (Gemini): Tests (waits for 1,2)
EOF

# 4. 创建 orchestrator agent
mkdir agents
cat > agents/orchestrator.md << 'EOF'
---
name: orchestrator
description: Coordinates multiple AI agents for parallel execution
---

# Orchestrator Agent

Expert in breaking down complex tasks and coordinating multiple AI agents.

## Capabilities:
- Task dependency analysis
- Optimal agent selection
- Parallel execution planning
- Result merging

## Decision Logic:
- Simple tasks → Gemini (fast, cheap)
- Complex code → Claude (quality)
- API/Backend → GPT-4 (specialized)
EOF

# 5. 本地测试
# 在 Claude Code 中
> /plugin add ./claude-multi-agent-plugin
> /parallel Build a todo app
```

**验证指标**:
- ✅ 能否通过插件实现基本功能？
- ✅ 用户是否喜欢多 Agent 概念？
- ✅ 性能提升是否明显？

**决策点**: 如果反馈好 → 进入阶段 2

---

### 阶段 2: MCP 集成（Week 3-4）

**目标**: 实现真正的并行执行

**方案**: 将现有多 Agent 系统作为 MCP Server

**实现**:

```python
# multi_agent_scheduler/mcp_server.py

import asyncio
import json
from typing import Dict, List, Any
from .meta_agent import MetaAgent
from .scheduler import Scheduler
from .agents import ClaudeAgent, OpenAIAgent, GeminiAgent

class MultiAgentMCPServer:
    """
    MCP Server exposing multi-agent capabilities

    Tools:
    - decompose_task: Break down task into subtasks
    - execute_parallel: Execute tasks in parallel
    - optimize_cost: Choose best agents for cost optimization
    """

    def __init__(self):
        self.meta_agent = MetaAgent()
        self.agents = self._init_agents()
        self.scheduler = Scheduler(self.agents)

    def _init_agents(self) -> Dict[str, Any]:
        """Initialize available agents"""
        import os
        agents = {}

        if api_key := os.getenv('ANTHROPIC_API_KEY'):
            agents['claude'] = ClaudeAgent(api_key=api_key)

        if api_key := os.getenv('OPENAI_API_KEY'):
            agents['openai'] = OpenAIAgent(api_key=api_key)

        agents['gemini'] = GeminiAgent()  # Free tier

        return agents

    async def handle_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle MCP tool calls"""

        if tool_name == 'decompose_task':
            # Break down task
            task = params['task']
            context = params.get('context', {})

            tasks = await self.meta_agent.decompose_task(task)

            return {
                'success': True,
                'tasks': [
                    {
                        'id': t.id,
                        'description': t.description,
                        'agent': t.assigned_agent,
                        'dependencies': t.dependencies
                    }
                    for t in tasks
                ]
            }

        elif tool_name == 'execute_parallel':
            # Execute tasks in parallel
            tasks = params['tasks']

            results = await self.scheduler.schedule(tasks)

            return {
                'success': True,
                'results': results,
                'total_time': sum(r['time'] for r in results),
                'cost': sum(r.get('cost', 0) for r in results)
            }

        elif tool_name == 'optimize_cost':
            # Optimize agent selection for cost
            tasks = params['tasks']

            optimized = await self._optimize_agent_selection(tasks)

            return {
                'success': True,
                'optimized_tasks': optimized,
                'estimated_savings': self._calculate_savings(
                    tasks, optimized
                )
            }

        else:
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}'
            }

    async def _optimize_agent_selection(
        self,
        tasks: List[Dict]
    ) -> List[Dict]:
        """Optimize agent selection for cost"""
        # Simple heuristic: use cheaper agents for simpler tasks
        optimized = []

        for task in tasks:
            complexity = self._estimate_complexity(task['description'])

            if complexity < 3:
                agent = 'gemini'  # Cheapest
            elif complexity < 7:
                agent = 'openai'  # Mid-tier
            else:
                agent = 'claude'  # Most capable

            optimized.append({
                **task,
                'agent': agent,
                'estimated_cost': self._estimate_cost(agent, complexity)
            })

        return optimized

    def _estimate_complexity(self, description: str) -> int:
        """Estimate task complexity (1-10)"""
        # Simple heuristic based on keywords
        keywords = {
            'simple': 2,
            'basic': 2,
            'refactor': 5,
            'design': 7,
            'architecture': 9,
            'distributed': 10
        }

        desc_lower = description.lower()
        scores = [v for k, v in keywords.items() if k in desc_lower]

        return max(scores) if scores else 5

    def _estimate_cost(self, agent: str, complexity: int) -> float:
        """Estimate cost in USD"""
        rates = {
            'gemini': 0.001,
            'openai': 0.01,
            'claude': 0.03
        }

        return rates.get(agent, 0.01) * complexity

    def _calculate_savings(
        self,
        original: List[Dict],
        optimized: List[Dict]
    ) -> float:
        """Calculate cost savings"""
        original_cost = sum(
            self._estimate_cost('claude', 5)  # Assume all Claude
            for _ in original
        )

        optimized_cost = sum(
            t['estimated_cost'] for t in optimized
        )

        return original_cost - optimized_cost

    async def serve(self, host='localhost', port=3000):
        """Start MCP server"""
        # Implement MCP protocol server
        # (simplified, actual implementation needs full MCP spec)
        print(f"🚀 Multi-Agent MCP Server running on {host}:{port}")
        print(f"📦 Available tools:")
        print(f"  - decompose_task")
        print(f"  - execute_parallel")
        print(f"  - optimize_cost")

        # Server loop
        while True:
            await asyncio.sleep(1)

# CLI entry point
async def main():
    server = MultiAgentMCPServer()
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
```

**配置 Claude Code**:

```json
// .claude/mcp.json
{
  "mcpServers": {
    "multi-agent": {
      "command": "python",
      "args": ["-m", "multi_agent_scheduler.mcp_server"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

**使用示例**:

```bash
$ claude

> Use multi-agent server to build a blog website with cost optimization

[Claude Code] Connecting to multi-agent MCP server...
[Multi-Agent] Decomposing task...

Tasks:
  1. Database design (Claude) - $0.15
  2. Backend API (OpenAI) - $0.10
  3. Frontend (Gemini) - $0.05
  4. Tests (Gemini) - $0.03

Total estimated cost: $0.33 (vs $0.60 single-agent)
Savings: 45%

Execute? [Y/n]: y

[Multi-Agent] Executing in parallel...
✅ All tasks completed in 3.8s
💰 Actual cost: $0.31
```

---

### 阶段 3: 独立产品（Week 5-12）

**目标**: 构建完整的独立产品

**方案**: 参考 Claude Code 设计，独立实现

**核心特性**:

#### 1. Plan Mode / Execute Mode

```python
# src/cli/modes.py

from enum import Enum
from typing import Optional

class Mode(Enum):
    PLAN = "plan"
    EXECUTE = "execute"

class ModeManager:
    """Manage Plan/Execute modes"""

    def __init__(self):
        self.current_mode = Mode.PLAN
        self.plan: Optional[TaskPlan] = None

    def toggle_mode(self):
        """Toggle between plan and execute"""
        if self.current_mode == Mode.PLAN:
            self.current_mode = Mode.EXECUTE
        else:
            self.current_mode = Mode.PLAN

    async def handle_input(self, user_input: str):
        """Handle user input based on current mode"""

        if self.current_mode == Mode.PLAN:
            return await self._handle_plan_mode(user_input)
        else:
            return await self._handle_execute_mode(user_input)

    async def _handle_plan_mode(self, user_input: str):
        """
        Plan mode: Analyze and plan, don't execute
        """
        print("🧠 Plan Mode (analyzing only, no changes)")

        # Use Meta-Agent to analyze
        self.plan = await self.meta_agent.decompose(user_input)

        # Display plan
        self.display_plan(self.plan)

        # Ask for approval
        if await self.confirm("Switch to Execute Mode?"):
            self.current_mode = Mode.EXECUTE
            return await self._handle_execute_mode(user_input)

    async def _handle_execute_mode(self, user_input: str):
        """
        Execute mode: Actually make changes
        """
        print("⚡ Execute Mode (making changes)")

        if not self.plan:
            # Create plan first
            self.plan = await self.meta_agent.decompose(user_input)

        # Execute
        results = await self.scheduler.execute(self.plan)

        return results
```

**用户体验**:

```bash
$ macode

Multi-Agent Code v1.0
Press Shift+Tab twice for Plan Mode

macode> Refactor authentication module

🧠 Plan Mode (Shift+Tab+Tab activated)

Analyzing authentication module...

📋 Proposed Changes:
  1. Extract token validation → utils/auth.py
  2. Simplify error handling → middleware/errors.py
  3. Add rate limiting → middleware/rate_limit.py
  4. Update tests → tests/test_auth.py

Estimated impact:
  - Files changed: 4
  - Lines added: ~150
  - Lines removed: ~80
  - Estimated time: 5-7 minutes

⚠️ Plan Mode: No changes will be made

Switch to Execute Mode? [Y/n]: y

⚡ Execute Mode

[claude] Extracting token validation... ✓ (2.1s)
[openai] Simplifying error handling... ✓ (1.8s)
[claude] Adding rate limiting... ✓ (2.3s)
[gemini] Updating tests... ✓ (1.5s)

✅ Refactoring complete (7.7s total)
📊 Changes:
  - 4 files modified
  - 156 lines added
  - 82 lines removed
  - All tests passing ✓

macode>
```

#### 2. 插件系统（独立实现）

```python
# src/plugins/manager.py

import json
from pathlib import Path
from typing import Dict, List, Any

class PluginManager:
    """
    Plugin system (inspired by Claude Code, but独立实现)
    """

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        self.commands: Dict[str, Command] = {}
        self.agents: Dict[str, Agent] = {}

    def load_plugin(self, plugin_path: Path):
        """Load a plugin from directory"""

        # Read manifest
        manifest_path = plugin_path / '.macode-plugin' / 'plugin.json'
        manifest = json.loads(manifest_path.read_text())

        plugin = Plugin(
            name=manifest['name'],
            version=manifest['version'],
            description=manifest.get('description', ''),
            author=manifest.get('author', '')
        )

        # Load commands
        commands_dir = plugin_path / 'commands'
        if commands_dir.exists():
            for cmd_file in commands_dir.glob('*.md'):
                command = self._load_command(cmd_file)
                self.commands[command.name] = command
                plugin.commands.append(command)

        # Load agents
        agents_dir = plugin_path / 'agents'
        if agents_dir.exists():
            for agent_file in agents_dir.glob('*.md'):
                agent = self._load_agent(agent_file)
                self.agents[agent.name] = agent
                plugin.agents.append(agent)

        # Load hooks
        hooks_file = plugin_path / 'hooks' / 'hooks.json'
        if hooks_file.exists():
            hooks = json.loads(hooks_file.read_text())
            plugin.hooks = hooks

        self.plugins[plugin.name] = plugin
        return plugin

    def _load_command(self, cmd_file: Path) -> Command:
        """Load a command from markdown file"""
        content = cmd_file.read_text()

        # Parse frontmatter
        frontmatter, description = self._parse_markdown(content)

        return Command(
            name=frontmatter.get('name', cmd_file.stem),
            description=frontmatter.get('description', ''),
            prompt=description
        )

    def _load_agent(self, agent_file: Path) -> Agent:
        """Load an agent from markdown file"""
        content = agent_file.read_text()

        # Parse frontmatter
        frontmatter, system_prompt = self._parse_markdown(content)

        return Agent(
            name=frontmatter.get('name', agent_file.stem),
            description=frontmatter.get('description', ''),
            system_prompt=system_prompt,
            model=frontmatter.get('model', 'claude-sonnet-4-5')
        )
```

**插件结构**（类似 Claude Code 但用自己的命名）:

```
.macode-plugin/              # 注意: 不是 .claude-plugin
├── plugin.json
commands/
├── parallel.md
└── optimize.md
agents/
├── reviewer.md
└── optimizer.md
```

#### 3. 流式输出

```python
# src/cli/streaming.py

import asyncio
from typing import AsyncIterator

class StreamingDisplay:
    """Real-time streaming output display"""

    def __init__(self):
        self.active_agents = {}

    async def stream_agent_output(
        self,
        agent_name: str,
        output_stream: AsyncIterator[str]
    ):
        """Display streaming output from an agent"""

        print(f"\n[{agent_name}] Starting...")

        buffer = ""
        async for chunk in output_stream:
            buffer += chunk

            # Display in real-time
            print(chunk, end='', flush=True)

        print(f"\n[{agent_name}] ✓ Complete")
        return buffer

    async def stream_parallel(
        self,
        agent_streams: Dict[str, AsyncIterator[str]]
    ):
        """Display multiple agents working in parallel"""

        tasks = [
            self.stream_agent_output(name, stream)
            for name, stream in agent_streams.items()
        ]

        results = await asyncio.gather(*tasks)

        return dict(zip(agent_streams.keys(), results))
```

---

## 三、法律合规检查清单

### ✅ 必须做到

- [ ] **代码完全独立编写** - 不复制任何 Claude Code 代码
- [ ] **独立命名** - 不使用 "Claude Code" 品牌
- [ ] **明确说明** - 标注"受 Claude Code 启发"
- [ ] **开源许可** - 使用 MIT/Apache 等宽松许可
- [ ] **不混淆品牌** - 清晰区分你的产品和 Claude Code

### ❌ 不能做

- [ ] Fork Claude Code 仓库后修改
- [ ] 复制粘贴 Claude Code 的代码
- [ ] 声称是 "Claude Code 的修改版"
- [ ] 使用 Anthropic 或 Claude Code 商标
- [ ] 反向工程其专有算法

---

## 四、推荐的命名和品牌

### 产品名称建议

**好的命名**:
- ✅ Multi-Agent Code (macode)
- ✅ ParallelAI Code
- ✅ Team Code (tcode)
- ✅ Conductor Code
- ✅ OrchestraAI

**避免的命名**:
- ❌ Claude Code Plus
- ❌ Claude Code Multi
- ❌ Super Claude Code
- ❌ 任何包含 "Claude" 的名字

### 项目描述模板

**正确的描述**:
```
Multi-Agent Code: An AI coding assistant that coordinates
multiple AI agents for parallel execution. Inspired by
Claude Code's excellent UX, but with multi-agent orchestration
for 2-3x speed improvement.
```

**错误的描述**:
```
❌ "A fork of Claude Code with multi-agent support"
❌ "Modified version of Claude Code"
❌ "Claude Code but better"
```

---

## 五、快速启动模板

### 最小可行插件（1 天完成）

```bash
#!/bin/bash
# quick-start-plugin.sh

# Create plugin structure
mkdir -p claude-multi-agent-plugin/{.claude-plugin,commands,agents}
cd claude-multi-agent-plugin

# Plugin manifest
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "multi-agent-preview",
  "version": "0.1.0",
  "description": "Multi-agent parallel execution preview",
  "author": "Your Name"
}
EOF

# Parallel command
cat > commands/parallel.md << 'EOF'
---
name: parallel
description: Execute tasks in parallel
---

# Parallel Execution

Analyze the task and identify components that can be executed in parallel.

Example:
User: "Build a blog with frontend and backend"

Parallel strategy:
1. Backend API (Agent A) - can start immediately
2. Frontend (Agent B) - can start in parallel
3. Tests (Agent C) - waits for 1 and 2
EOF

# Orchestrator agent
cat > agents/orchestrator.md << 'EOF'
---
name: orchestrator
description: Multi-agent task coordinator
---

# Orchestrator

Coordinates multiple tasks across different AI agents for optimal execution.

Skills:
- Dependency analysis
- Agent selection
- Parallel planning
EOF

# README
cat > README.md << 'EOF'
# Multi-Agent Preview Plugin

A Claude Code plugin that demonstrates multi-agent parallel execution.

## Installation

```bash
# In Claude Code
/plugin add ./claude-multi-agent-plugin
```

## Usage

```bash
/parallel Build a todo app
```
EOF

echo "✅ Plugin created! Test with:"
echo "  claude"
echo "  > /plugin add $(pwd)"
echo "  > /parallel Build a REST API"
```

---

## 六、总结

### 推荐路径

**第 1-2 周**: Claude Code 插件
- 快速验证概念
- 收集用户反馈
- 决定是否继续

**第 3-4 周**: MCP Server
- 实现真正的并行执行
- 与 Claude Code 互补
- 建立技术优势

**第 5-12 周**: 独立产品
- 完整的独立工具
- 参考但不复制
- 长期产品基础

### 成功关键

1. **合法性第一** - 绝不直接魔改
2. **快速验证** - 先做插件测试
3. **独立代码** - 所有代码自己写
4. **差异化** - 强调多 Agent 优势
5. **开源友好** - 建立社区信任

### 最终目标

打造一个**合法的、独立的、比 Claude Code 更强大**的多 Agent 编码助手！

---

**创建时间**: 2025-11-05
**适用场景**: 合法地实现类似 Claude Code 的多 Agent 工具
