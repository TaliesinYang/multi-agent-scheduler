# 🚀 快速开始指南

本指南帮助您在 **5分钟内** 运行 Multi-Agent Scheduler！

---

## 📦 第一步：安装（2分钟）

```bash
# 1. 进入项目目录
cd multi-agent-scheduler

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "import anthropic; print('✅ 安装成功')"
```

---

## ⚡ 第二步：运行第一个示例（1分钟）

### 方式1: 最简示例（推荐新手）

```bash
# 无需任何配置，立即运行
python minimal_example.py
```

**输出示例**:
```
🚀 Multi-Agent Scheduler - 最简示例

📦 初始化调度器...
📝 定义任务...

⚡ 开始执行（自动并行）...

✅ 执行完成！3个任务在1秒内完成
```

### 方式2: 交互式 Demo

```bash
python demo.py
# 选择: 2. Use Mock Agents
# 然后选择任何示例场景
```

---

## 🔑 第三步：配置真实 API（可选）

如果要使用真实的 AI 模型，需要配置 API 密钥：

### 快速配置（环境变量）

```bash
# 设置 Claude API 密钥
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# 验证
python -c "from anthropic import Anthropic; Anthropic(); print('✅ API配置成功')"

# 运行真实 API 测试
python demo.py
# 选择: 1. Use Real API
```

### 详细配置（配置文件）

```bash
# 1. 复制配置模板
cp config.yaml.example config.yaml

# 2. 编辑配置
nano config.yaml

# 3. 启用需要的 Agent
agents:
  claude:
    enabled: true
    model: "claude-sonnet-4-5-20250929"
```

---

## 📝 第四步：编写你的第一个调度程序（2分钟）

创建 `my_first_scheduler.py`:

```python
import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import MockAgent

async def main():
    # 1. 创建调度器
    scheduler = MultiAgentScheduler(agents={"mock": MockAgent()})

    # 2. 定义你的任务
    tasks = [
        Task(id="t1", prompt="你的第一个任务", task_type="general"),
        Task(id="t2", prompt="你的第二个任务", task_type="general"),
        Task(id="t3", prompt="你的第三个任务", task_type="general"),
    ]

    # 3. 执行调度
    result = await scheduler.schedule(tasks)

    # 4. 查看结果
    scheduler.print_summary(result)

asyncio.run(main())
```

运行：
```bash
python my_first_scheduler.py
```

---

## 🎯 常见使用场景

### 场景1: 并行执行独立任务

```python
tasks = [
    Task(id="design1", prompt="设计方案A", task_type="general"),
    Task(id="design2", prompt="设计方案B", task_type="general"),
    Task(id="design3", prompt="设计方案C", task_type="general"),
]
# 3个任务会自动并行执行，节省时间！
```

### 场景2: 有依赖的任务链

```python
tasks = [
    Task(id="需求", prompt="分析需求", task_type="general"),
    Task(id="设计", prompt="设计架构", task_type="general", depends_on=["需求"]),
    Task(id="开发", prompt="编写代码", task_type="general", depends_on=["设计"]),
    Task(id="测试", prompt="编写测试", task_type="general", depends_on=["开发"]),
]
# 调度器会自动按依赖顺序执行
```

### 场景3: 使用真实 AI

```python
from src.agents import ClaudeAgent, GeminiCLIAgent

# 真实 AI Agent
scheduler = MultiAgentScheduler(agents={
    'claude': ClaudeAgent(api_key="your-key"),
    'gemini': GeminiCLIAgent()  # CLI 模式，更省钱
})

tasks = [
    Task(id="code", prompt="写一个排序算法", task_type="coding"),
    Task(id="docs", prompt="生成API文档", task_type="general"),
]

result = await scheduler.schedule(tasks)
```

---

## ⚙️ 性能优化（进阶）

### 调整并发数

```yaml
# config.yaml
scheduler:
  max_concurrent_tasks: 15  # 增加并发（默认10）
```

### 成本优化

```yaml
# 使用免费的 Gemini CLI
agents:
  gemini:
    enabled: true
    use_cli: true  # 免费！

  claude:
    enabled: true
    only_for_types: ["coding"]  # 仅用于代码任务
```

### 内存优化（大量任务）

```python
# 分批处理
async def process_many_tasks(all_tasks, batch_size=50):
    for i in range(0, len(all_tasks), batch_size):
        batch = all_tasks[i:i+batch_size]
        result = await scheduler.schedule(batch)
        # 处理结果
```

---

## 🐛 遇到问题？

### 问题1: 导入错误

```bash
# 解决: 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题2: API密钥无效

```bash
# 检查密钥格式
echo $ANTHROPIC_API_KEY  # 应该以 sk-ant- 开头

# 重新设置
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### 问题3: 任务执行慢

```python
# 检查是否有依赖（导致串行执行）
tasks = [
    Task(id="t1", prompt="...", depends_on=[]),  # ✅ 无依赖
    Task(id="t2", prompt="...", depends_on=[]),  # ✅ 无依赖
]
# 无依赖的任务会自动并行！
```

---

## 📚 下一步学习

1. **查看完整示例**
   ```bash
   python demo.py  # 5个示例场景
   ```

2. **阅读文档**
   - `README.md` - 完整文档
   - `PERFORMANCE_BENCHMARK_RESULTS.md` - 性能报告
   - `docs/` - 详细指南

3. **运行性能测试**
   ```bash
   python -m pytest tests/ -v  # 213个单元测试
   python -m pytest tests/benchmark/ --benchmark-only  # 性能测试
   ```

4. **启动 Web UI**（如果已实现）
   ```bash
   python web_ui/app.py
   # 访问 http://localhost:8080
   ```

5. **查看监控**
   ```bash
   # 启动健康检查服务
   python -c "from src.health import app; import uvicorn; uvicorn.run(app, port=8000)"

   # 访问
   # http://localhost:8000/health
   # http://localhost:8000/metrics
   ```

---

## 🎉 成功运行！

如果你看到了任务执行结果，恭喜！你已经成功运行了 Multi-Agent Scheduler。

**接下来可以**:
- ✅ 尝试不同的任务类型
- ✅ 配置真实 API
- ✅ 优化并发设置
- ✅ 探索更多高级功能

**需要帮助？**
- 查看 `README.md` 的"常见问题"部分
- 查看 `docs/` 目录中的详细文档
- 运行示例: `python demo.py`

---

**最后更新**: 2025-11-14
**用时**: ⚡ 5分钟从零到运行
