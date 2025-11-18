# 🚀 CLI客户端模式 - 快速设置指南

**目标**: 配置项目使用GitHub Copilot或Claude CLI，不需要API密钥

---

## ✅ 已为您准备的文件

我已经创建了完整的CLI配置：

```
✅ config.cli.yaml          - CLI客户端专用配置
✅ docs/CLI_CLIENT_SETUP.md - 详细设置文档
✅ scripts/verify_cli_setup.py - 验证脚本
✅ workspace/               - 工作目录（已创建）
✅ checkpoints_cli/         - 检查点目录（已创建）
```

---

## 🎯 3步快速开始

### 步骤1: 安装CLI客户端

#### 选项A: GitHub Copilot（推荐）

```bash
# 1. 确保已订阅GitHub Copilot ($10/月)
#    访问: https://github.com/settings/copilot

# 2. 安装GitHub CLI
# macOS
brew install gh

# Linux (Debian/Ubuntu)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 3. 安装Copilot扩展
gh extension install github/gh-copilot

# 4. 登录
gh auth login
gh copilot auth

# 5. 验证
gh copilot --help
```

#### 选项B: Claude CLI

```bash
# 安装
pip install claude-cli

# 配置（需要Anthropic API密钥）
claude configure

# 验证
claude --version
```

---

### 步骤2: 激活配置

```bash
# 复制CLI配置为主配置
cp config.cli.yaml config.yaml

# 或者创建符号链接
ln -s config.cli.yaml config.yaml
```

---

### 步骤3: 验证设置

```bash
# 运行验证脚本
python scripts/verify_cli_setup.py

# 应该看到:
# ✅ GitHub CLI 可用
# ✅ Copilot扩展 已安装
# ✅ config.yaml 存在
```

---

## 🧪 测试运行

### 测试1: 最简单的示例

创建 `test_cli.py`:

```python
import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import CodexExecAgent

async def main():
    # 使用Codex（无需API密钥）
    agent = CodexExecAgent(workspace="./workspace")

    scheduler = MultiAgentScheduler(agents={
        "codex": agent
    })

    # 简单任务
    task = Task(
        id="hello",
        prompt="Write a Python function that prints 'Hello, World!'",
        task_type="coding"
    )

    # 执行
    print("🚀 正在使用Codex...")
    result = await scheduler.schedule([task])

    # 结果
    if result.success:
        print("✅ 成功!")
        print(result.task_results['hello'].result)
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

### 测试2: 使用配置文件

```python
import asyncio
import yaml
from src.scheduler import MultiAgentScheduler, Task
from src.agents import CodexExecAgent

async def main():
    # 加载配置
    with open('config.yaml') as f:
        config = yaml.safe_load(f)

    # 根据配置创建Agent
    agents = {}
    if config['agents']['codex']['enabled']:
        agents['codex'] = CodexExecAgent(
            workspace=config['agents']['codex']['workspace'],
            max_concurrent=config['agents']['codex']['max_concurrent']
        )

    scheduler = MultiAgentScheduler(agents)

    # 定义多个任务
    tasks = [
        Task(id="t1", prompt="Write a sorting function", task_type="coding"),
        Task(id="t2", prompt="Write a search function", task_type="coding"),
        Task(id="t3", prompt="Write tests", task_type="testing", depends_on=["t1", "t2"])
    ]

    result = await scheduler.schedule(tasks)
    scheduler.print_summary(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📝 配置说明

### config.cli.yaml 核心配置

```yaml
# 启用的Agent
agents:
  codex:
    enabled: true              # 使用Codex
    cli_command: "gh copilot suggest"  # 或 "codex"
    workspace: "./workspace"
    max_concurrent: 5

  mock:
    enabled: true              # 保留Mock用于测试

# 任务路由
scheduler:
  agent_selection_strategy:
    coding: "codex"            # 代码任务 → Codex
    testing: "codex"           # 测试任务 → Codex
    simple: "mock"             # 简单任务 → Mock
    general: "codex"           # 默认 → Codex
```

### 自定义配置

如果需要修改，编辑 `config.yaml`:

```yaml
agents:
  codex:
    # 调整并发数（根据机器性能）
    max_concurrent: 3  # 降低并发

    # 调整超时
    timeout: 900       # 增加到15分钟

    # 更改工作目录
    workspace: "/path/to/your/workspace"
```

---

## ❓ 常见问题

### Q: 我没有GitHub Copilot订阅怎么办？

**A**: 有3个选择：
1. **订阅Copilot** ($10/月) - 推荐，物超所值
2. **使用Mock模式** - 免费，用于测试
3. **使用API模式** - 按使用付费，参考 `docs/RUNNING_MODES.md`

---

### Q: 如何在Mock和CLI模式间切换？

**A**: 修改配置文件：

```yaml
# CLI模式
agents:
  codex:
    enabled: true
  mock:
    enabled: false

# Mock模式（测试）
agents:
  codex:
    enabled: false
  mock:
    enabled: true
```

或使用环境变量：
```bash
export AGENT_MODE=cli    # CLI模式
export AGENT_MODE=mock   # Mock模式
```

---

### Q: Codex命令找不到？

**A**: 使用 `gh copilot suggest` 代替：

```yaml
agents:
  codex:
    cli_command: "gh copilot suggest"  # 而不是 "codex"
```

---

### Q: 能否同时使用多个CLI客户端？

**A**: 可以！

```yaml
agents:
  codex:
    enabled: true
    cli_command: "gh copilot suggest"

  claude_cli:
    enabled: true
    cli_command: "claude"

scheduler:
  agent_selection_strategy:
    coding: "codex"       # 代码用Codex
    analysis: "claude_cli"  # 分析用Claude
```

---

## 📚 完整文档

详细信息请查看：

- **详细设置**: `docs/CLI_CLIENT_SETUP.md`
- **运行模式对比**: `docs/RUNNING_MODES.md`
- **配置示例**: `config.cli.yaml`

---

## 🎯 下一步

1. ✅ 安装CLI客户端（GitHub Copilot或Claude CLI）
2. ✅ 激活配置: `cp config.cli.yaml config.yaml`
3. ✅ 验证设置: `python scripts/verify_cli_setup.py`
4. ✅ 运行示例: `python test_cli.py`
5. 🚀 开始使用您的项目！

---

**需要帮助？**
- 查看完整文档: `docs/CLI_CLIENT_SETUP.md`
- 提交Issue: GitHub Issues
- 查看示例: `examples/` 目录

**祝您使用愉快！** 🎉
