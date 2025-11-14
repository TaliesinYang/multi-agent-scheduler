# 🧪 真实API测试策略

**文档版本**: 1.0
**最后更新**: 2025-11-14
**目标**: 从Mock测试过渡到真实API生产环境测试

---

## 📋 目录

- [为什么需要真实API测试](#为什么需要真实api测试)
- [测试阶段规划](#测试阶段规划)
- [环境配置](#环境配置)
- [渐进式测试策略](#渐进式测试策略)
- [成本控制](#成本控制)
- [性能基准测试](#性能基准测试)
- [故障处理与容错](#故障处理与容错)
- [监控与日志](#监控与日志)

---

## 🎯 为什么需要真实API测试

### Mock测试的局限性

| 维度 | Mock测试 | 真实API测试 |
|------|---------|-----------|
| **响应时间** | 立即 (~1ms) | 2-10秒 (模型推理) |
| **网络延迟** | 无 | 100-500ms |
| **API限流** | 无限制 | 50-100 req/min |
| **失败场景** | 模拟 | 真实网络/API错误 |
| **成本** | 免费 | 每1K tokens $0.003-0.015 |
| **代表性** | ❌ 理论验证 | ✅ 实际部署性能 |

### 需要真实测试的场景

1. **性能验证**: 确认实际吞吐量和延迟
2. **成本估算**: 计算真实运行成本
3. **容错测试**: 验证网络中断、API限流的恢复能力
4. **生产部署前**: 最后一步质量保证

---

## 📅 测试阶段规划

### Phase 1: 小规模验证 (1-3天)

**目标**: 验证基本功能，估算成本

```bash
# 测试规模
- 任务数量: 5-10个任务
- 并发度: 2-3个并发
- 预计成本: $0.01-0.05
- 测试时间: 2-5分钟

# 验证内容
✅ API密钥配置正确
✅ Agent能正常调用API
✅ 任务调度逻辑正确
✅ 结果解析无误
✅ 初步成本估算
```

**执行命令**:
```bash
# 1. 配置API密钥
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# 2. 运行小规模测试
python tests/real_world/test_real_api_performance.py --tasks 5

# 3. 查看成本
# 输出示例: Total cost: $0.023 (5 tasks, avg $0.0046/task)
```

---

### Phase 2: 中等规模测试 (3-7天)

**目标**: 测试并发调度、错误恢复

```bash
# 测试规模
- 任务数量: 20-50个任务
- 并发度: 5-10个并发
- 预计成本: $0.10-0.50
- 测试时间: 5-15分钟

# 验证内容
✅ 并行调度性能
✅ 依赖关系正确处理
✅ 错误重试机制
✅ Checkpoint恢复
✅ 实际加速比测量
```

**执行命令**:
```bash
# 测试并行调度
python tests/real_world/test_real_api_performance.py \
    --tasks 30 \
    --test-type speedup

# 测试容错能力
python tests/real_world/test_real_api_performance.py \
    --tasks 20 \
    --test-type fault-tolerance
```

---

### Phase 3: 大规模压力测试 (7-14天)

**目标**: 验证生产环境性能

```bash
# 测试规模
- 任务数量: 100-500个任务
- 并发度: 20-50个并发
- 预计成本: $2-10
- 测试时间: 30-120分钟

# 验证内容
✅ API限流处理
✅ 长时间运行稳定性
✅ 内存/资源管理
✅ 大规模任务调度效率
✅ 真实世界性能基准
```

**执行命令**:
```bash
# 大规模测试
python tests/real_world/test_real_api_performance.py \
    --tasks 200 \
    --test-type large-scale \
    --max-cost 5.0  # 成本上限保护
```

---

## 🔧 环境配置

### 1. API密钥管理

**安全最佳实践**:

```bash
# 方式1: 环境变量 (推荐 - CI/CD)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export OPENAI_API_KEY="sk-proj-..."

# 方式2: .env文件 (推荐 - 本地开发)
cat > .env.production << EOF
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
OPENAI_MODEL=gpt-4-turbo
EOF

# 方式3: 密钥管理服务 (推荐 - 生产环境)
# AWS Secrets Manager, GCP Secret Manager, Azure Key Vault
```

**重要**:
- ❌ 不要将API密钥提交到Git
- ✅ 添加 `.env.production` 到 `.gitignore`
- ✅ 使用最小权限的API密钥
- ✅ 定期轮换密钥

---

### 2. 成本限额配置

创建 `config.production.yaml`:

```yaml
# 真实API配置
agents:
  claude:
    enabled: true
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 4000
    api_key_env: "ANTHROPIC_API_KEY"

  openai:
    enabled: true
    model: "gpt-4-turbo"
    max_tokens: 4000
    api_key_env: "OPENAI_API_KEY"

# 成本控制
cost_control:
  enabled: true
  max_cost_per_session: 10.0  # 美元
  max_cost_per_task: 0.5      # 美元
  alert_threshold: 5.0        # 成本警告阈值
  auto_stop_on_limit: true    # 超过限额自动停止

# 速率限制 (避免触发API限流)
rate_limiting:
  requests_per_minute: 50     # Claude: 50 req/min
  max_concurrent: 10          # 最大并发数
  retry_on_rate_limit: true   # 遇到限流自动重试
  backoff_strategy: "exponential"  # 重试退避策略

# 监控
monitoring:
  log_level: "INFO"
  enable_metrics: true
  export_results: true
  results_dir: "./results/production"
```

---

## 🚀 渐进式测试策略

### Step 1: 单任务验证

**目标**: 确保单个API调用正常工作

```python
# tests/real_world/test_single_task.py
import asyncio
from src.scheduler import MultiAgentScheduler, Task
from src.agents import ClaudeAgent
import os

async def test_single_task():
    """测试单个真实API调用"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 未设置 ANTHROPIC_API_KEY")
        return

    scheduler = MultiAgentScheduler(agents={
        "claude": ClaudeAgent(api_key=api_key)
    })

    task = Task(
        id="test1",
        prompt="用一句话解释什么是机器学习",
        task_type="general"
    )

    print("🚀 开始执行单个任务...")
    result = await scheduler.schedule([task])

    if result.success:
        print("✅ 任务执行成功!")
        print(f"结果: {result.task_results['test1'].result[:100]}...")
        print(f"耗时: {result.total_duration:.2f}秒")
    else:
        print(f"❌ 任务失败: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_single_task())
```

**执行**:
```bash
python tests/real_world/test_single_task.py
# 预期输出:
# 🚀 开始执行单个任务...
# ✅ 任务执行成功!
# 结果: 机器学习是一种让计算机从数据中学习规律...
# 耗时: 3.24秒
```

---

### Step 2: 并行任务测试

**目标**: 验证并行调度性能

```python
# tests/real_world/test_parallel_tasks.py
async def test_parallel_execution():
    """测试并行任务执行"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    scheduler = MultiAgentScheduler(agents={
        "claude": ClaudeAgent(api_key=api_key)
    })

    # 5个独立任务 (无依赖，可并行)
    tasks = [
        Task(id=f"task{i}",
             prompt=f"用一句话解释数字{i}的数学意义",
             task_type="general")
        for i in range(1, 6)
    ]

    # 串行执行基准
    print("📊 测试1: 串行执行 (禁用并行)...")
    start = time.time()
    # 这里需要实现串行模式，或者逐个执行
    serial_time = time.time() - start

    # 并行执行
    print("📊 测试2: 并行执行...")
    start = time.time()
    result = await scheduler.schedule(tasks)
    parallel_time = time.time() - start

    # 计算加速比
    speedup = serial_time / parallel_time
    print(f"\n🎯 性能对比:")
    print(f"  串行耗时: {serial_time:.2f}秒")
    print(f"  并行耗时: {parallel_time:.2f}秒")
    print(f"  加速比: {speedup:.2f}x")

    # 预期: 2.5-3.5x 加速比 (真实API)
    # Mock测试: 4.9x 加速比
```

---

### Step 3: 依赖关系测试

**目标**: 验证DAG调度正确性

```python
async def test_dependency_scheduling():
    """测试依赖关系调度"""

    tasks = [
        Task(id="analyze", prompt="分析需求", task_type="analysis"),
        Task(id="design", prompt="设计架构", task_type="design",
             depends_on=["analyze"]),
        Task(id="impl_a", prompt="实现模块A", task_type="coding",
             depends_on=["design"]),
        Task(id="impl_b", prompt="实现模块B", task_type="coding",
             depends_on=["design"]),
        Task(id="test", prompt="集成测试", task_type="testing",
             depends_on=["impl_a", "impl_b"]),
    ]

    result = await scheduler.schedule(tasks)

    # 验证执行顺序
    execution_order = [t for t in result.execution_history]
    assert execution_order[0] == "analyze"
    assert execution_order[1] == "design"
    assert "test" in execution_order[-2:]  # test应该在最后

    print("✅ 依赖关系调度正确!")
```

---

### Step 4: 容错测试

**目标**: 验证错误处理和恢复

```python
async def test_fault_tolerance():
    """测试容错能力"""

    # 创建包含可能失败任务的列表
    tasks = [
        Task(id="task1", prompt="正常任务", task_type="general"),
        Task(id="task2",
             prompt="这是一个超长prompt" + "x" * 100000,  # 可能超长
             task_type="general"),
        Task(id="task3", prompt="正常任务", task_type="general"),
    ]

    result = await scheduler.schedule(tasks)

    # 验证: 部分失败不影响其他任务
    successful = [tid for tid, res in result.task_results.items()
                  if res.success]
    print(f"✅ 成功任务: {len(successful)}/{len(tasks)}")
    print(f"成功率: {len(successful)/len(tasks)*100:.1f}%")
```

---

## 💰 成本控制

### 成本估算公式

```python
# Claude Sonnet 4.5 定价 (2025)
INPUT_COST_PER_1K = 0.003   # $0.003/1K tokens
OUTPUT_COST_PER_1K = 0.015  # $0.015/1K tokens

def estimate_cost(prompt: str, expected_output_tokens: int = 500):
    """估算单个任务成本"""
    # 估算输入tokens (粗略: 1 token ≈ 4 字符)
    input_tokens = len(prompt) / 4

    # 计算成本
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K
    output_cost = (expected_output_tokens / 1000) * OUTPUT_COST_PER_1K

    total_cost = input_cost + output_cost
    return total_cost

# 示例
prompt = "请详细分析量子计算的发展趋势，不少于1000字"
cost = estimate_cost(prompt, expected_output_tokens=1500)
print(f"预计成本: ${cost:.4f}")  # ~$0.0258
```

### 成本监控脚本

```python
# src/cost_monitor.py
class CostMonitor:
    def __init__(self, max_budget: float = 10.0):
        self.max_budget = max_budget
        self.current_cost = 0.0
        self.task_costs = {}

    def record_task_cost(self, task_id: str, cost: float):
        """记录任务成本"""
        self.task_costs[task_id] = cost
        self.current_cost += cost

        # 检查预算
        if self.current_cost > self.max_budget:
            raise BudgetExceededError(
                f"预算超限: ${self.current_cost:.2f} > ${self.max_budget:.2f}"
            )

        # 警告
        if self.current_cost > self.max_budget * 0.8:
            print(f"⚠️  预算警告: 已使用 {self.current_cost/self.max_budget*100:.1f}%")

    def get_report(self) -> dict:
        """生成成本报告"""
        return {
            "total_cost": self.current_cost,
            "budget": self.max_budget,
            "utilization": self.current_cost / self.max_budget * 100,
            "tasks_count": len(self.task_costs),
            "avg_cost_per_task": self.current_cost / len(self.task_costs),
            "most_expensive_task": max(self.task_costs.items(),
                                      key=lambda x: x[1])
        }
```

---

## 📊 性能基准测试

### 测试场景设计

#### Scenario 1: 独立任务并行

```python
# 10个独立任务，测试纯并行性能
tasks = [
    Task(id=f"task{i}",
         prompt=f"分析主题{i}的核心观点",
         task_type="analysis")
    for i in range(10)
]

# 预期性能 (真实API):
# - 串行: ~40秒 (每个任务4秒)
# - 并行 (10并发): ~12-15秒
# - 加速比: 2.7-3.3x
```

#### Scenario 2: 复杂DAG

```python
# 20个任务，多层依赖
#       task1
#      /  |  \
#   task2 task3 task4
#     |     |     |
#   task5 task6 task7
#      \   |   /
#       task8

# 预期性能:
# - 串行: ~80秒
# - 并行: ~28-35秒
# - 加速比: 2.3-2.9x
```

#### Scenario 3: 混合任务类型

```python
# 不同复杂度的任务
tasks = [
    # 简单任务 (预计200 tokens输出)
    Task(id="simple1", prompt="一句话总结X", ...),

    # 中等任务 (预计500 tokens输出)
    Task(id="medium1", prompt="分析X的优缺点", ...),

    # 复杂任务 (预计1000+ tokens输出)
    Task(id="complex1", prompt="详细设计X的实现方案", ...),
]

# 验证: 调度器是否优先执行复杂任务
```

---

## 🛠️ 故障处理与容错

### 常见故障场景

#### 1. API限流 (Rate Limit)

```python
# 症状
# anthropic.RateLimitError: 429 Too Many Requests

# 处理策略
retry_config = {
    "max_retries": 3,
    "backoff_strategy": "exponential",  # 1s, 2s, 4s
    "initial_delay": 1.0,
    "max_delay": 30.0
}

# 实现
async def call_with_retry(func, *args, **kwargs):
    for attempt in range(retry_config["max_retries"]):
        try:
            return await func(*args, **kwargs)
        except RateLimitError:
            if attempt == retry_config["max_retries"] - 1:
                raise

            delay = min(
                retry_config["initial_delay"] * (2 ** attempt),
                retry_config["max_delay"]
            )
            print(f"⏱️  Rate limit hit, retrying in {delay}s...")
            await asyncio.sleep(delay)
```

#### 2. 网络超时

```python
# 症状
# asyncio.TimeoutError

# 处理策略
timeout_config = {
    "request_timeout": 60.0,  # 单个请求超时
    "total_timeout": 600.0    # 总执行超时
}

# 实现
async with asyncio.timeout(timeout_config["request_timeout"]):
    result = await agent.execute(task)
```

#### 3. API错误响应

```python
# 症状
# anthropic.APIError: Invalid request

# 处理策略
def validate_task(task: Task) -> bool:
    """任务提交前验证"""
    # 检查prompt长度
    if len(task.prompt) > 100000:
        print(f"⚠️  Task {task.id}: Prompt too long")
        return False

    # 检查必填字段
    if not task.prompt or not task.task_type:
        return False

    return True

# 使用
valid_tasks = [t for t in tasks if validate_task(t)]
```

---

## 📈 监控与日志

### 实时监控指标

```python
# 关键指标
metrics = {
    # 性能指标
    "throughput": 0.0,        # tasks/sec
    "avg_latency": 0.0,       # seconds
    "p95_latency": 0.0,       # seconds
    "success_rate": 0.0,      # 0-100%

    # 资源指标
    "active_tasks": 0,        # 当前执行中任务数
    "queue_length": 0,        # 等待队列长度
    "api_calls_count": 0,     # API调用总数

    # 成本指标
    "total_cost": 0.0,        # USD
    "cost_per_task": 0.0,     # USD

    # 错误指标
    "error_count": 0,
    "rate_limit_hits": 0,
    "timeout_count": 0
}
```

### 日志配置

```python
# logging_config.py
import logging

def setup_production_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('production.log'),
            logging.StreamHandler()
        ]
    )

    # 详细的API调用日志
    api_logger = logging.getLogger('api_calls')
    api_logger.addHandler(
        logging.FileHandler('api_calls.log')
    )
```

### 执行报告生成

```python
# 自动生成测试报告
def generate_test_report(result, output_file="test_report.md"):
    """生成Markdown格式测试报告"""

    report = f"""
# 真实API测试报告

**测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**总任务数**: {len(result.task_results)}

## 📊 性能指标

- **总耗时**: {result.total_duration:.2f}秒
- **成功任务**: {result.successful_tasks}/{result.total_tasks}
- **成功率**: {result.success_rate:.1f}%
- **平均每任务**: {result.avg_duration:.2f}秒

## 💰 成本统计

- **总成本**: ${result.total_cost:.4f}
- **平均成本/任务**: ${result.cost_per_task:.4f}

## ❌ 失败任务

{chr(10).join(f"- {tid}: {tres.error}" for tid, tres in result.task_results.items() if not tres.success)}

## 📈 性能分析

...
    """

    with open(output_file, 'w') as f:
        f.write(report)
```

---

## ✅ 测试检查清单

### 测试前检查

- [ ] API密钥已配置且有效
- [ ] 已设置成本上限
- [ ] 已配置速率限制
- [ ] 日志系统正常工作
- [ ] 有足够的API配额

### 测试中监控

- [ ] 实时查看成本累计
- [ ] 监控错误率
- [ ] 观察响应延迟
- [ ] 检查任务成功率
- [ ] 验证并行度

### 测试后分析

- [ ] 对比Mock vs 真实性能
- [ ] 分析成本效益
- [ ] 识别性能瓶颈
- [ ] 记录优化建议
- [ ] 生成测试报告

---

## 🎯 成功标准

一次成功的真实API测试应该达到:

### 功能性
- ✅ 所有任务类型正常工作
- ✅ 依赖关系正确处理
- ✅ 错误能正确恢复

### 性能
- ✅ 加速比 ≥ 2.5x (对于并行任务)
- ✅ 成功率 ≥ 95%
- ✅ P95延迟 < 15秒

### 成本
- ✅ 成本在预算内
- ✅ 单任务成本 < $0.10 (一般场景)
- ✅ 无意外的高成本任务

---

## 📚 参考资源

- [Claude API文档](https://docs.anthropic.com/claude/reference)
- [OpenAI API文档](https://platform.openai.com/docs)
- [速率限制最佳实践](https://docs.anthropic.com/claude/reference/rate-limits)
- [成本优化指南](https://docs.anthropic.com/claude/docs/cost-optimization)

---

**下一步**:
1. 执行 Phase 1 小规模验证
2. 分析结果，调整配置
3. 逐步扩大测试规模
4. 生成生产环境性能报告
