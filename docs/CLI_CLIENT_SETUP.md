# 🖥️ CLI客户端模式设置指南

**适用于**: 使用GitHub Copilot、Claude CLI等本地客户端的用户
**优势**: 无需API密钥、可能免费、使用真实AI

---

## 📋 目录

- [支持的CLI客户端](#支持的cli客户端)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [常见问题](#常见问题)

---

## 🎯 支持的CLI客户端

### 1. GitHub Copilot Codex ⭐ 推荐

**适用场景**: 代码生成、调试、测试、重构
**要求**: GitHub Copilot订阅（$10/月或$100/年）

### 2. Claude CLI

**适用场景**: 分析、设计、文档、通用任务
**要求**: Anthropic账号

### 3. 自定义CLI工具

**适用场景**: 任何支持命令行调用的AI工具
**要求**: 可执行的CLI命令

---

## 🔧 前置要求

### 选项1: GitHub Copilot Codex（推荐）

#### 步骤1: 确认Copilot订阅

```bash
# 检查GitHub Copilot状态
gh copilot --version

# 如果未安装，需要先订阅
# 访问: https://github.com/settings/copilot
```

#### 步骤2: 安装Copilot CLI

```bash
# 方式1: 使用GitHub CLI扩展（推荐）
gh extension install github/gh-copilot

# 方式2: 直接安装
npm install -g @githubnext/github-copilot-cli

# 验证安装
gh copilot --version
```

#### 步骤3: 认证

```bash
# 登录GitHub
gh auth login

# 启用Copilot
gh copilot auth

# 验证Copilot可用
gh copilot suggest "write a python function"
```

#### 步骤4: 设置Codex命令

```bash
# 创建codex命令别名（如果不存在）
# 添加到 ~/.bashrc 或 ~/.zshrc

alias codex='gh copilot suggest'

# 或者如果安装了copilot-cli
# codex 命令应该已经可用
which codex  # 检查是否存在

# 如果不存在，可以创建包装脚本
cat > ~/bin/codex << 'EOF'
#!/bin/bash
gh copilot suggest "$@"
EOF
chmod +x ~/bin/codex

# 验证
codex --help
```

---

### 选项2: Claude CLI（可选）

#### 步骤1: 安装Claude CLI

```bash
# 方式1: 使用pip
pip install claude-cli

# 方式2: 使用npm（如果有npm版本）
npm install -g @anthropic-ai/claude-cli

# 验证安装
claude --version
```

#### 步骤2: 配置Claude CLI

```bash
# 配置API密钥（需要Anthropic账号）
claude configure

# 或设置环境变量
export ANTHROPIC_API_KEY="your-key"

# 测试
claude "Hello, how are you?"
```

---

## ⚡ 快速开始

### 步骤1: 复制配置文件

```bash
# 复制CLI配置模板
cp config.cli.yaml config.yaml

# 或者如果您想保留原配置
ln -s config.cli.yaml config.yaml
```

### 步骤2: 编辑配置（可选）

```bash
# 编辑配置文件
vim config.yaml

# 主要配置项:
# - agents.codex.enabled: true/false
# - agents.codex.workspace: 工作目录路径
# - scheduler.agent_selection_strategy: 任务分配策略
```

### 步骤3: 验证CLI可用性

```bash
# 运行验证脚本
python scripts/verify_cli_setup.py

# 或手动验证
python -c "
import subprocess
result = subprocess.run(['codex', '--help'], capture_output=True)
print('✅ Codex可用' if result.returncode == 0 else '❌ Codex不可用')
"
```

### 步骤4: 运行第一个示例

```python
# test_cli.py
import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import CodexExecAgent

async def main():
    # 创建Codex Agent
    agent = CodexExecAgent(
        workspace="./workspace",
        max_concurrent=3
    )

    scheduler = MultiAgentScheduler(agents={
        "codex": agent
    })

    # 定义任务
    tasks = [
        Task(
            id="task1",
            prompt="Write a Python function to calculate factorial",
            task_type="coding"
        )
    ]

    # 执行
    print("🚀 执行中...")
    result = await scheduler.schedule(tasks)

    # 查看结果
    if result.success:
        print("✅ 成功!")
        print(f"结果: {result.task_results['task1'].result}")
    else:
        print("❌ 失败:", result.error)

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```bash
python test_cli.py
```

---

## 📝 详细配置

### 配置文件结构

```yaml
# config.yaml (或 config.cli.yaml)

agents:
  codex:
    enabled: true                    # 启用Codex
    cli_command: "codex"             # CLI命令名
    workspace: "./workspace"         # 工作目录
    max_concurrent: 5                # 并发数
    timeout: 600                     # 超时（秒）

scheduler:
  agent_selection_strategy:
    coding: "codex"                  # 代码任务用Codex
    general: "codex"                 # 默认用Codex
```

### 任务类型映射

```yaml
scheduler:
  agent_selection_strategy:
    # 代码相关
    coding: "codex"           # 代码生成
    debugging: "codex"        # 调试
    testing: "codex"          # 测试
    refactoring: "codex"      # 重构

    # 文档/分析
    analysis: "claude_cli"    # 分析
    documentation: "codex"    # 文档
    design: "claude_cli"      # 设计

    # 默认
    general: "codex"          # 通用任务
```

### 高级配置

#### 1. 多个CLI Agent

```yaml
agents:
  codex_coding:
    enabled: true
    cli_command: "codex"
    workspace: "./workspace/code"

  codex_testing:
    enabled: true
    cli_command: "codex"
    workspace: "./workspace/tests"

  claude_analysis:
    enabled: true
    cli_command: "claude"

scheduler:
  agent_selection_strategy:
    coding: "codex_coding"
    testing: "codex_testing"
    analysis: "claude_analysis"
```

#### 2. 自定义CLI Agent

```yaml
agents:
  my_custom_ai:
    enabled: true
    cli_command: "my-ai-cli"
    max_concurrent: 3
    timeout: 300
    # 自定义参数
    custom_args:
      - "--model"
      - "best"
      - "--format"
      - "json"
```

在代码中使用:
```python
from src.agents import RobustCLIAgent

class MyCustomAgent(RobustCLIAgent):
    def __init__(self):
        super().__init__(
            name="CustomAI",
            cli_command="my-ai-cli",
            max_concurrent=3
        )

agent = MyCustomAgent()
```

---

## 🔍 验证设置

### 自动验证脚本

创建 `scripts/verify_cli_setup.py`:

```python
#!/usr/bin/env python3
"""验证CLI客户端设置"""

import subprocess
import sys

def check_command(cmd, name):
    """检查命令是否可用"""
    try:
        result = subprocess.run(
            [cmd, '--help'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {name} 可用")
            return True
        else:
            print(f"❌ {name} 不可用 (返回码: {result.returncode})")
            return False
    except FileNotFoundError:
        print(f"❌ {name} 未安装 (命令: {cmd})")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠️  {name} 超时")
        return False
    except Exception as e:
        print(f"❌ {name} 错误: {e}")
        return False

def main():
    print("🔍 验证CLI客户端设置\n")

    results = {}

    # 检查Codex
    print("检查 GitHub Copilot Codex...")
    results['gh'] = check_command('gh', 'GitHub CLI')
    results['codex'] = check_command('codex', 'Codex')

    # 检查Claude CLI
    print("\n检查 Claude CLI...")
    results['claude'] = check_command('claude', 'Claude CLI')

    # 总结
    print("\n" + "="*50)
    print("总结:")
    print("="*50)

    available = [k for k, v in results.items() if v]
    if available:
        print(f"✅ 可用的CLI: {', '.join(available)}")
        print("\n推荐配置:")
        if 'codex' in available:
            print("  agents.codex.enabled: true")
        if 'claude' in available:
            print("  agents.claude_cli.enabled: true")
        return 0
    else:
        print("❌ 没有可用的CLI客户端")
        print("\n请安装:")
        print("  • GitHub Copilot: gh extension install github/gh-copilot")
        print("  • Claude CLI: pip install claude-cli")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

运行验证:
```bash
chmod +x scripts/verify_cli_setup.py
python scripts/verify_cli_setup.py
```

---

## 🚀 使用示例

### 示例1: 代码生成

```python
from src.scheduler import MultiAgentScheduler, Task
from src.agents import CodexExecAgent

async def generate_code():
    agent = CodexExecAgent(workspace="./code_output")
    scheduler = MultiAgentScheduler(agents={"codex": agent})

    tasks = [
        Task(id="sort", prompt="Write a quicksort function in Python", task_type="coding"),
        Task(id="search", prompt="Write a binary search function", task_type="coding"),
        Task(id="test", prompt="Write unit tests for quicksort", task_type="testing", depends_on=["sort"])
    ]

    result = await scheduler.schedule(tasks)
    return result
```

### 示例2: 项目重构

```python
async def refactor_project():
    agent = CodexExecAgent(workspace="./my_project")
    scheduler = MultiAgentScheduler(agents={"codex": agent})

    tasks = [
        Task(id="analyze", prompt="Analyze code structure and identify refactoring opportunities", task_type="analysis"),
        Task(id="refactor1", prompt="Refactor utils.py to use modern Python syntax", task_type="refactoring", depends_on=["analyze"]),
        Task(id="refactor2", prompt="Add type hints to all functions", task_type="refactoring", depends_on=["analyze"]),
        Task(id="test", prompt="Update tests after refactoring", task_type="testing", depends_on=["refactor1", "refactor2"])
    ]

    result = await scheduler.schedule(tasks)
    return result
```

### 示例3: 使用配置文件

```python
import yaml
from src.scheduler import MultiAgentScheduler
from src.agents import CodexExecAgent

# 加载配置
with open('config.cli.yaml') as f:
    config = yaml.safe_load(f)

# 根据配置创建Agent
agents = {}
if config['agents']['codex']['enabled']:
    agents['codex'] = CodexExecAgent(
        workspace=config['agents']['codex']['workspace'],
        max_concurrent=config['agents']['codex']['max_concurrent']
    )

# 创建调度器
scheduler = MultiAgentScheduler(agents)

# 使用...
```

---

## ❓ 常见问题

### Q1: Codex命令找不到

**问题**: `codex: command not found`

**解决**:
```bash
# 检查GitHub CLI是否安装
gh --version

# 检查Copilot扩展
gh extension list | grep copilot

# 重新安装
gh extension install github/gh-copilot

# 创建别名
alias codex='gh copilot suggest'
```

### Q2: Codex返回"未订阅"错误

**问题**: `Error: You don't have access to GitHub Copilot`

**解决**:
1. 访问 https://github.com/settings/copilot
2. 订阅GitHub Copilot ($10/月)
3. 重新认证: `gh copilot auth`

### Q3: CLI超时

**问题**: CLI命令执行超时

**解决**:
```yaml
# 增加超时时间
agents:
  codex:
    timeout: 1200  # 增加到20分钟
```

### Q4: 工作区权限问题

**问题**: `Permission denied: ./workspace`

**解决**:
```bash
# 创建并设置权限
mkdir -p ./workspace
chmod 755 ./workspace

# 或在配置中使用绝对路径
agents:
  codex:
    workspace: "/home/user/my_workspace"
```

### Q5: 如何查看CLI命令输出

**解决**:
```yaml
# 启用CLI日志
logging:
  log_cli_commands: true
  log_cli_responses: true
  level: "DEBUG"

# 查看日志
tail -f scheduler_cli.log
```

### Q6: 能否混用CLI和API模式

**可以**!
```yaml
agents:
  codex:
    enabled: true
    # CLI模式（免费）

  claude_api:
    enabled: true
    api_key_env: "ANTHROPIC_API_KEY"
    # API模式（按需付费）

scheduler:
  agent_selection_strategy:
    coding: "codex"       # 代码用免费CLI
    analysis: "claude_api"  # 分析用付费API（质量更高）
```

---

## 📊 性能对比

| 模式 | 成本 | 速度 | 质量 | 并发 |
|------|------|------|------|------|
| **CLI (Codex)** | $10/月固定 | 快 (2-5s) | 高 | 中 (5并发) |
| **API (Claude)** | 按使用 ($0.003+) | 中 (3-10s) | 很高 | 高 (20并发) |
| **Mock** | 免费 | 极快 (1s) | 模拟 | 无限 |

---

## 🎯 推荐配置

### 个人开发者（有Copilot订阅）
```yaml
agents:
  codex:
    enabled: true
  mock:
    enabled: true  # 测试时使用

scheduler:
  agent_selection_strategy:
    coding: "codex"
    testing: "codex"
    simple: "mock"
```

### 团队开发（混合模式）
```yaml
agents:
  codex:
    enabled: true    # 代码生成（固定费用）
  claude_api:
    enabled: true    # 复杂分析（按需付费）
  mock:
    enabled: true    # CI/CD测试

scheduler:
  agent_selection_strategy:
    coding: "codex"
    testing: "codex"
    analysis: "claude_api"
    design: "claude_api"
    simple: "mock"
```

---

## 🔗 相关资源

- [GitHub Copilot文档](https://docs.github.com/en/copilot)
- [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli)
- [运行模式说明](RUNNING_MODES.md)
- [项目README](../README.md)

---

**最后更新**: 2025-11-14
**需要帮助?** 提交Issue或查看完整文档
