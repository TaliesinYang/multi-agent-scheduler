# 🚀 Multi-Agent Scheduler 运行模式说明

**最后更新**: 2025-11-14

---

## 📋 目录

- [运行模式总览](#运行模式总览)
- [模式1: Mock模式（推荐测试）](#模式1-mock模式推荐测试)
- [模式2: API模式（真实AI）](#模式2-api模式真实ai)
- [模式3: CLI客户端模式](#模式3-cli客户端模式)
- [单元测试使用哪种模式](#单元测试使用哪种模式)
- [如何切换模式](#如何切换模式)
- [模式对比](#模式对比)

---

## 🎯 运行模式总览

本项目支持 **3种运行模式**，您可以根据需求选择：

```
┌──────────────────────────────────────────────────────────┐
│                   运行模式选择                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1️⃣  Mock模式     - 模拟AI（免费、快速、测试用）          │
│  2️⃣  API模式      - 真实AI（需API密钥、收费）             │
│  3️⃣  CLI客户端模式 - 本地客户端（如Codex、Claude CLI）     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 模式1: Mock模式（推荐测试）

### ✅ 适用场景
- **单元测试** ⭐ 最常用
- **算法验证** - 验证调度逻辑是否正确
- **快速演示** - 向他人展示系统功能
- **开发调试** - 调试代码时不想花费API成本
- **CI/CD** - 自动化测试

### 特点
```
✅ 完全免费 - 无需任何API密钥
✅ 立即响应 - 延迟可配置（默认1秒）
✅ 100%可靠 - 不会有网络错误
✅ 可控模拟 - 可以模拟各种延迟场景
❌ 非真实AI - 返回模拟数据
```

### 使用方法

#### 方式1: 最简单的方式
```python
from src.scheduler import MultiAgentScheduler, Task
from src.agents import MockAgent

# 创建Mock Agent（无需API密钥）
scheduler = MultiAgentScheduler(agents={
    "mock": MockAgent()
})

# 定义任务
tasks = [
    Task(id="task1", prompt="分析量子计算", task_type="general"),
    Task(id="task2", prompt="实现排序算法", task_type="general")
]

# 执行（返回模拟结果）
result = await scheduler.schedule(tasks)
```

#### 方式2: 配置不同延迟
```python
# 模拟不同速度的Agent
agents = {
    'fast': MockAgent(name="Fast-Mock", delay=0.5),    # 快速响应
    'medium': MockAgent(name="Medium-Mock", delay=1.0), # 中等速度
    'slow': MockAgent(name="Slow-Mock", delay=2.0)     # 慢速响应
}

scheduler = MultiAgentScheduler(agents)
```

#### 方式3: 运行demo
```bash
# 直接运行，无需配置
python minimal_example.py

# 或者运行完整demo，选择Mock模式
python demos/demo.py
# 选择: "2. Use Mock agents"
```

### Mock Agent实现原理
```python
# src/agents.py
class MockAgent(BaseAgent):
    """Mock Agent - 不调用真实API"""

    async def call(self, prompt: str):
        # 模拟网络延迟
        await asyncio.sleep(self.delay)  # 默认1秒

        # 返回模拟响应
        return {
            "agent": "Mock",
            "result": f"Mock response for: {prompt[:50]}...",
            "latency": self.delay,
            "tokens": len(prompt.split()) * 2,
            "success": True
        }
```

---

## 模式2: API模式（真实AI）

### ✅ 适用场景
- **生产部署** - 实际使用AI能力
- **真实测试** - 验证真实性能
- **论文实验** - 获取真实数据
- **产品开发** - 正式功能开发

### 特点
```
✅ 真实AI响应 - 实际调用Claude/GPT等
✅ 高质量输出 - 真实的AI推理能力
❌ 需要API密钥 - 需要注册并付费
❌ 有成本 - 每次调用收费（~$0.003-0.015/1K tokens）
❌ 有延迟 - 网络延迟 + 模型推理（2-10秒）
❌ 可能失败 - 网络错误、限流等
```

### 支持的AI服务

#### 1. Claude API（推荐）
```python
from src.agents import ClaudeAgent

# 需要API密钥
agent = ClaudeAgent(
    api_key="sk-ant-api03-...",
    model="claude-sonnet-4-5-20250929",
    max_concurrent=20
)

scheduler = MultiAgentScheduler(agents={"claude": agent})
```

**获取API密钥**:
1. 访问 https://console.anthropic.com/
2. 注册账号并充值
3. 创建API密钥

**定价**:
- Claude Sonnet 4.5: $0.003/1K input, $0.015/1K output
- Claude Haiku 3.5: $0.00025/1K input, $0.00125/1K output

#### 2. OpenAI API
```python
from src.agents import OpenAIAgent

agent = OpenAIAgent(
    api_key="sk-proj-...",
    model="gpt-4-turbo",
    max_concurrent=20
)

scheduler = MultiAgentScheduler(agents={"openai": agent})
```

**获取API密钥**:
1. 访问 https://platform.openai.com/
2. 注册并添加付款方式
3. 创建API密钥

**定价**:
- GPT-4 Turbo: $0.01/1K input, $0.03/1K output
- GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output

#### 3. 混合使用（成本优化）
```python
# 智能选择：简单任务用便宜的，复杂任务用强大的
agents = {
    "haiku": ClaudeAgent(api_key=key1, model="claude-haiku-3.5"),   # 便宜
    "sonnet": ClaudeAgent(api_key=key2, model="claude-sonnet-4-5"), # 强大
}

scheduler = MultiAgentScheduler(agents)

# 配置路由策略
scheduler.agent_selection_strategy = {
    "simple": "haiku",    # 简单任务 → Haiku (成本↓90%)
    "complex": "sonnet"   # 复杂任务 → Sonnet (质量↑)
}
```

### 配置API密钥

#### 方式1: 环境变量（推荐 - CI/CD）
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-proj-..."
```

然后在代码中：
```python
import os

claude = ClaudeAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai = OpenAIAgent(api_key=os.getenv("OPENAI_API_KEY"))
```

#### 方式2: .env文件（推荐 - 本地开发）
```bash
# 创建 .env 文件
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
EOF

# 代码中加载
from dotenv import load_dotenv
load_dotenv()

claude = ClaudeAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

#### 方式3: 配置文件
```python
# src/config.py
ANTHROPIC_API_KEY = "sk-ant-api03-..."
OPENAI_API_KEY = "sk-proj-..."

# 使用
from src.config import ANTHROPIC_API_KEY
claude = ClaudeAgent(api_key=ANTHROPIC_API_KEY)
```

⚠️ **安全提示**:
- 不要将API密钥提交到Git
- 添加 `.env` 和 `config.py` 到 `.gitignore`
- 使用最小权限的API密钥

---

## 模式3: CLI客户端模式

### ✅ 适用场景
- 已有 **GitHub Copilot** 订阅
- 使用 **Claude Code CLI**
- 使用其他本地AI客户端
- **不想使用API**，但想要真实AI能力

### 特点
```
✅ 无需API密钥 - 使用本地客户端
✅ 可能免费 - 如果已有订阅
✅ 真实AI - 真实的AI推理能力
❌ 需要安装客户端 - codex、claude等命令行工具
❌ 配置复杂 - 需要正确配置客户端
```

### 支持的CLI客户端

#### 1. Codex CLI（GitHub Copilot）
```python
from src.agents import CodexExecAgent

# 需要安装 codex CLI 并登录 GitHub Copilot
agent = CodexExecAgent(
    workspace="/path/to/project",
    max_concurrent=5
)

scheduler = MultiAgentScheduler(agents={"codex": agent})
```

**前置要求**:
```bash
# 1. 安装 GitHub Copilot CLI
npm install -g @githubnext/github-copilot-cli

# 2. 登录
gh copilot auth

# 3. 验证
codex --version
```

**使用示例**:
```python
# 执行代码生成任务
task = Task(
    id="gen_code",
    prompt="Write a Python function to sort a list",
    task_type="coding"
)

result = await scheduler.schedule([task])
# → 使用Codex生成真实代码！
```

#### 2. Claude CLI
```python
from src.agents import ClaudeCLIAgent

# 需要安装 claude CLI
agent = ClaudeCLIAgent(max_concurrent=5)

scheduler = MultiAgentScheduler(agents={"claude_cli": agent})
```

**前置要求**:
```bash
# 安装 claude CLI (示例)
npm install -g @anthropic-ai/claude-cli
# 或
pip install claude-cli

# 配置
claude configure

# 验证
claude --version
```

#### 3. 自定义CLI Agent
```python
from src.agents import RobustCLIAgent

class CustomCLIAgent(RobustCLIAgent):
    def __init__(self):
        super().__init__(
            name="CustomAI",
            cli_command="my-ai-cli",  # 您的CLI命令
            max_concurrent=10
        )

agent = CustomCLIAgent()
scheduler = MultiAgentScheduler(agents={"custom": agent})
```

---

## 单元测试使用哪种模式？

### ✅ 推荐：Mock模式

**原因**:
1. **免费** - 不消耗API配额
2. **快速** - 立即响应，测试套件运行快
3. **可靠** - 100%成功率，无网络问题
4. **独立** - 无需外部依赖，CI/CD友好
5. **可控** - 可以精确控制延迟和响应

### 当前项目的单元测试

```bash
# 运行所有单元测试（使用Mock Agent）
pytest tests/

# 结果: 213个测试全部通过
===== 213 passed in 16.09s =====
```

**测试配置**:
```python
# tests/test_scheduler.py
import pytest
from src.agents import MockAgent

@pytest.fixture
def scheduler():
    """所有测试使用Mock Agent"""
    return MultiAgentScheduler(agents={
        "mock": MockAgent(delay=0.1)  # 快速Mock
    })

def test_parallel_scheduling(scheduler):
    """测试并行调度逻辑"""
    tasks = [
        Task(id=f"task{i}", prompt="test", task_type="general")
        for i in range(10)
    ]

    result = await scheduler.schedule(tasks)

    # 验证算法正确性（不关心AI输出质量）
    assert result.success
    assert len(result.task_results) == 10
```

### 真实API测试（可选）

对于**生产环境验证**，可以单独运行真实API测试：

```bash
# 真实API测试（需要API密钥）
export ANTHROPIC_API_KEY="sk-ant-..."
python tests/real_world/test_real_api_performance.py --tasks 5

# 或者使用pytest标记
pytest tests/real_world/ -m "real_api" --run-real-api
```

**区分测试类型**:
```python
# tests/real_world/test_real_api.py
import pytest

@pytest.mark.real_api
@pytest.mark.skip(reason="Requires API key and costs money")
async def test_real_claude_performance():
    """真实Claude API性能测试（手动运行）"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("No API key configured")

    agent = ClaudeAgent(api_key=api_key)
    # 真实测试...
```

---

## 如何切换模式？

### 方法1: 代码中直接切换

```python
import os
from src.scheduler import MultiAgentScheduler
from src.agents import MockAgent, ClaudeAgent, CodexExecAgent

# 根据环境变量决定模式
mode = os.getenv("AGENT_MODE", "mock")  # 默认mock

if mode == "mock":
    # Mock模式 - 测试/开发
    agents = {"mock": MockAgent()}

elif mode == "api":
    # API模式 - 生产环境
    api_key = os.getenv("ANTHROPIC_API_KEY")
    agents = {"claude": ClaudeAgent(api_key=api_key)}

elif mode == "cli":
    # CLI模式 - 本地客户端
    agents = {"codex": CodexExecAgent()}

scheduler = MultiAgentScheduler(agents)
```

### 方法2: 配置文件切换

```yaml
# config.yaml
mode: "mock"  # mock | api | cli

agents:
  mock:
    enabled: true
    delay: 1.0

  api:
    claude:
      enabled: false
      api_key_env: "ANTHROPIC_API_KEY"
      model: "claude-sonnet-4-5-20250929"

  cli:
    codex:
      enabled: false
      workspace: "/path/to/project"
```

### 方法3: 运行时选择（Demo方式）

```bash
python demos/demo.py

# 输出:
# Please select running mode:
# 1. Use real APIs (requires API keys)
# 2. Use Mock agents (quick testing, recommended)
#
# Please select (1/2) [default: 2]:
```

---

## 模式对比

| 特性 | Mock模式 | API模式 | CLI模式 |
|------|---------|---------|---------|
| **是否需要API密钥** | ❌ 不需要 | ✅ 需要 | ❌ 不需要 |
| **是否收费** | ✅ 免费 | ❌ 收费 | ⚠️ 可能免费 |
| **响应速度** | ⚡ 极快 (1s) | 🐌 慢 (3-10s) | 🚀 较快 (2-5s) |
| **AI质量** | ❌ 模拟数据 | ✅ 真实AI | ✅ 真实AI |
| **可靠性** | ✅ 100% | ⚠️ 95-98% | ⚠️ 95-98% |
| **适用场景** | 测试、开发、演示 | 生产、论文实验 | 有订阅用户 |
| **CI/CD友好** | ✅ 非常友好 | ❌ 不友好 | ⚠️ 一般 |
| **网络依赖** | ❌ 无依赖 | ✅ 需要网络 | ⚠️ 可能需要 |
| **配置复杂度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 |

---

## 实际使用建议

### 开发阶段
```
1️⃣ 本地开发 → Mock模式（快速迭代）
2️⃣ 功能验证 → Mock模式（算法测试）
3️⃣ 单元测试 → Mock模式（CI/CD）
```

### 测试阶段
```
4️⃣ 集成测试 → Mock模式（稳定性测试）
5️⃣ 性能验证 → API模式（小规模，5-10任务）
6️⃣ 压力测试 → API模式（中等规模，20-50任务）
```

### 生产阶段
```
7️⃣ 生产部署 → API模式（真实用户）
8️⃣ 成本优化 → 混合模式（Haiku + Sonnet）
9️⃣ 监控报警 → API模式 + 实时监控
```

### 学术研究
```
🔟 算法验证 → Mock模式（MARBLE benchmark）
1️⃣1️⃣ 性能测试 → API模式（真实数据）
1️⃣2️⃣ 论文图表 → Mock + API对比
```

---

## 快速开始

### 1分钟体验（Mock模式）
```bash
# 克隆项目
git clone https://github.com/your-repo/multi-agent-scheduler
cd multi-agent-scheduler

# 立即运行（无需配置）
python minimal_example.py

# 输出示例:
# 🚀 Multi-Agent Scheduler - 最简示例
# ✅ 执行成功!
# ⚡ 并行加速: 2.5x
```

### 5分钟配置（API模式）
```bash
# 1. 设置API密钥
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# 2. 运行真实API测试
python tests/real_world/test_real_api_performance.py --tasks 5

# 3. 查看成本
# Total cost: $0.023 (5 tasks)
```

### 完整体验（所有模式）
```bash
# 运行交互式demo
python demos/demo.py

# 选择不同模式体验所有功能
```

---

## FAQ

### Q1: 单元测试一定要用Mock吗？
**A**: 推荐使用Mock，原因：
- 免费、快速、可靠
- 验证的是**算法逻辑**，不是AI输出质量
- CI/CD友好
- 真实API可以单独测试（`tests/real_world/`）

### Q2: Mock模式能测试什么？
**A**: Mock模式可以测试：
- ✅ 调度算法正确性
- ✅ 依赖关系处理
- ✅ 并行执行逻辑
- ✅ 错误处理机制
- ✅ 性能优化效果（理论值）
- ❌ **不能测试**：真实AI输出质量、实际网络性能

### Q3: 如何使用Codex而不是API？
**A**: 使用CLI模式：
```python
from src.agents import CodexExecAgent

agent = CodexExecAgent(workspace="/your/project")
scheduler = MultiAgentScheduler(agents={"codex": agent})
```
前提：已安装并登录GitHub Copilot CLI

### Q4: 能混合使用多种模式吗？
**A**: 可以！
```python
agents = {
    "mock": MockAgent(),           # 简单任务用Mock（免费）
    "claude": ClaudeAgent(key),    # 重要任务用真实AI
    "codex": CodexExecAgent()      # 代码生成用Codex
}
```

### Q5: 生产环境推荐哪种模式？
**A**:
- **小型项目/预算有限**: CLI模式（如果有Copilot订阅）
- **中型项目**: API模式（Claude Haiku为主，省钱）
- **大型项目**: 混合模式（智能路由，成本优化）

---

## 相关文档

- [真实API测试策略](REAL_API_TESTING_STRATEGY.md) - 如何测试真实API
- [成本优化指南](OPTIMIZATION_ROADMAP.md) - 如何降低API成本
- [快速开始](../QUICK_START.md) - 5分钟上手指南
- [API文档](../README.md) - 完整API说明

---

**最后更新**: 2025-11-14
**维护者**: Multi-Agent Scheduler Team
