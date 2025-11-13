# Fork + Isolation Strategy: Multi-Agent Gemini CLI

**Date**: 2025-11-05
**Decision**: Fork Gemini CLI with Architectural Isolation Layer
**Goal**: Customize UI/UX + Replace scheduling logic while keeping upstream updates easy

---

## 问题分析

你的核心需求：

1. ✅ **完全控制UI/UX** - 修改启动动画、交互页面、设计风格
2. ✅ **原生体验** - 不通过MCP中转，直接内部集成
3. ✅ **使用我们的调度逻辑** - Meta Agent分解 + Scheduler并行执行
4. ✅ **方便同步更新** - 官方更新时不会太痛苦

**为什么MCP方案不够**：
- ❌ 无法修改UI/UX（启动动画、交互页面等）
- ❌ 交互通过中转，不是原生体验
- ❌ 受MCP协议限制

**为什么直接Fork也有问题**：
- ❌ 如果到处修改代码 → 每次upstream更新都是merge地狱

---

## 解决方案：Fork + 六边形架构隔离

### 核心思想

```
┌─────────────────────────────────────────────────────────────┐
│                    Gemini CLI (Fork)                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  UI/UX Layer (packages/cli/src/ui) ✏️ 可修改       │  │
│  │  - AppContainer.tsx                                 │  │
│  │  - 启动动画                                         │  │
│  │  - 交互页面                                         │  │
│  │  - 主题、颜色                                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Core Layer (packages/core/src)                     │  │
│  │                                                      │  │
│  │  📌 关键修改点：                                    │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │ TaskSchedulerPort (接口 - 新增)               │ │  │
│  │  │                                                │ │  │
│  │  │ interface TaskSchedulerPort {                 │ │  │
│  │  │   decompose(task): TaskPlan                   │ │  │
│  │  │   execute(plan): Results                      │ │  │
│  │  │ }                                              │ │  │
│  │  └────────────────┬───────────────────────────────┘ │  │
│  │                   │                                  │  │
│  │  ┌────────────────▼───────────────────────────────┐ │  │
│  │  │ AgentExecutor (修改)                           │ │  │
│  │  │                                                │ │  │
│  │  │ // 原来：直接调用Gemini API                    │ │  │
│  │  │ - const response = await geminiChat.send()    │ │  │
│  │  │                                                │ │  │
│  │  │ // 现在：通过Port调用                         │ │  │
│  │  │ + const scheduler = getScheduler()            │ │  │
│  │  │ + const plan = await scheduler.decompose()    │ │  │
│  │  │ + const results = await scheduler.execute()   │ │  │
│  │  └────────────────┬───────────────────────────────┘ │  │
│  │                   │                                  │  │
│  └───────────────────┼──────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      │ 注入依赖
                      │
┌─────────────────────▼──────────────────────────────────────┐
│  TaskScheduler Adapter (新增模块 - 独立文件)               │
│  packages/core/src/schedulers/multi-agent-scheduler.ts     │
│                                                             │
│  export class MultiAgentScheduler implements               │
│         TaskSchedulerPort {                                 │
│                                                             │
│    async decompose(task: string): Promise<TaskPlan> {      │
│      // 调用我们的Meta Agent（Python or ported to TS）    │
│      return await this.metaAgent.decompose(task);          │
│    }                                                        │
│                                                             │
│    async execute(plan: TaskPlan): Promise<Results> {       │
│      // 调用我们的Scheduler                                │
│      return await this.scheduler.execute(plan.tasks);      │
│    }                                                        │
│  }                                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ 内部调用
                      │
┌─────────────────────▼───────────────────────────────────────┐
│      我们的核心逻辑（独立包）                                │
│      packages/multi-agent-core/ (新增package)               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Meta Agent (ported to TypeScript)                    │ │
│  │  - 任务分解                                            │ │
│  │  - 代理选择                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Scheduler                                             │ │
│  │  - 并行执行                                            │ │
│  │  - 依赖解析                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Sub Agents                                            │ │
│  │  - Claude Agent                                        │ │
│  │  - OpenAI Agent                                        │ │
│  │  - Gemini Agent (使用Gemini CLI的现有实现)            │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 关键设计：修改隔离策略

### 修改层级（从容易到困难）

#### Level 1: UI/UX 修改 ✏️ 自由修改
**位置**: `packages/cli/src/ui/`
**内容**:
- 启动动画
- 交互页面
- 主题、颜色
- React组件

**Upstream冲突风险**: ⚠️ 中等
**策略**:
- 使用git merge策略（详见下文）
- 优先保留我们的UI定制

#### Level 2: 调度器接口 🔌 一次性修改
**位置**: `packages/core/src/schedulers/` (新建目录)
**新增文件**:
```
packages/core/src/schedulers/
├── port.ts                      # TaskSchedulerPort 接口定义
├── multi-agent-scheduler.ts     # 我们的实现
└── default-scheduler.ts         # 原Gemini逻辑（fallback）
```

**修改点**:
```typescript
// packages/core/src/agents/executor.ts (唯一需要修改的现有文件)

import { getScheduler } from '../schedulers/port.js';

export class AgentExecutor {
  async execute(inputs: AgentInputs): Promise<OutputObject> {
    // 原来的代码：
    // const response = await this.geminiChat.send(...);

    // 新代码（注入点）：
    const scheduler = getScheduler(this.runtimeContext);

    if (scheduler.type === 'multi-agent') {
      // 使用我们的多代理调度器
      const plan = await scheduler.decompose(inputs.task);
      const results = await scheduler.execute(plan);
      return this.formatResults(results);
    } else {
      // Fallback到原Gemini逻辑
      const response = await this.geminiChat.send(...);
      return response;
    }
  }
}
```

**Upstream冲突风险**: ✅ 极低
**原因**:
- 只修改一个文件的一个方法
- 新增独立目录，不影响现有代码
- 如果upstream修改了`executor.ts`，只需重新应用这个patch

#### Level 3: 核心逻辑 🆕 完全独立
**位置**: `packages/multi-agent-core/` (新package)
**内容**: 我们的Meta Agent + Scheduler（完全独立）

**Upstream冲突风险**: ✅ 零（独立package）

---

## Git策略：优雅的Upstream同步

### Branch结构

```
main (我们的生产分支)
├── ui-customizations (UI修改)
├── scheduler-integration (调度器注入)
└── multi-agent-core (独立功能)

upstream/main (Google官方)
```

### 同步流程

#### Step 1: 定期从upstream拉取
```bash
# 每月或每个重要版本
git fetch upstream
git checkout -b sync-upstream-2025-12
git merge upstream/main

# 解决冲突（主要在UI层）
```

#### Step 2: 冲突处理策略
```bash
# UI冲突 → 优先保留我们的修改
git checkout --ours packages/cli/src/ui/AppContainer.tsx

# executor.ts冲突 → 手动merge，重新应用我们的patch
# (因为这个文件修改量小，容易处理)
```

#### Step 3: 测试和发布
```bash
npm run test:all
npm run build
# 发布到我们自己的npm registry
```

### Patch管理（更优雅的方案）

**使用patch-package保存我们的修改**：

```bash
# 安装patch-package
npm install -D patch-package

# 修改后生成patch
npx patch-package @google/gemini-cli-core

# 生成 patches/@google+gemini-cli-core+0.13.0.patch
```

**Upstream更新时**：
```bash
# 1. 更新依赖
npm update @google/gemini-cli

# 2. 自动应用我们的patch
npm install  # patch-package会自动运行

# 3. 如果patch失败，手动调整
npx patch-package @google/gemini-cli-core --reverse
# 手动修改代码
npx patch-package @google/gemini-cli-core
```

---

## 具体实现步骤

### Phase 1: 基础架构（Week 1）

#### 1.1 Fork Gemini CLI
```bash
# 在GitHub上fork https://github.com/google-gemini/gemini-cli
git clone https://github.com/YOUR_ORG/gemini-cli.git
cd gemini-cli

# 添加upstream remote
git remote add upstream https://github.com/google-gemini/gemini-cli.git
```

#### 1.2 创建调度器接口
**File**: `packages/core/src/schedulers/port.ts`
```typescript
/**
 * Port interface for task scheduling
 * Allows different scheduling implementations to be plugged in
 */

export interface TaskPlan {
  tasks: Task[];
  dependencies: Record<string, string[]>;
}

export interface Task {
  id: string;
  description: string;
  agent: string;
  prompt: string;
}

export interface TaskResult {
  taskId: string;
  agent: string;
  result: string;
  success: boolean;
  latency: number;
}

export interface TaskSchedulerPort {
  /**
   * Decompose a high-level task into subtasks
   */
  decompose(task: string, context?: any): Promise<TaskPlan>;

  /**
   * Execute a task plan
   */
  execute(plan: TaskPlan): Promise<TaskResult[]>;

  /**
   * Get scheduler type for conditional logic
   */
  readonly type: 'default' | 'multi-agent';
}

/**
 * Get the configured scheduler
 */
export function getScheduler(config: Config): TaskSchedulerPort {
  const schedulerType = config.get('scheduler.type');

  if (schedulerType === 'multi-agent') {
    return new MultiAgentScheduler(config);
  } else {
    return new DefaultScheduler(config);
  }
}
```

#### 1.3 实现Default Scheduler（保留原逻辑）
**File**: `packages/core/src/schedulers/default-scheduler.ts`
```typescript
/**
 * Default scheduler - wraps original Gemini CLI behavior
 * This is a fallback that preserves original functionality
 */

import { TaskSchedulerPort, TaskPlan, TaskResult } from './port.js';
import { GeminiChat } from '../core/geminiChat.js';

export class DefaultScheduler implements TaskSchedulerPort {
  readonly type = 'default' as const;

  constructor(private config: Config) {}

  async decompose(task: string): Promise<TaskPlan> {
    // Original Gemini logic: no decomposition, execute as single task
    return {
      tasks: [{
        id: 'task-1',
        description: task,
        agent: 'gemini',
        prompt: task
      }],
      dependencies: {}
    };
  }

  async execute(plan: TaskPlan): Promise<TaskResult[]> {
    // Execute using original Gemini chat
    const geminiChat = new GeminiChat(this.config);
    const response = await geminiChat.send(plan.tasks[0].prompt);

    return [{
      taskId: plan.tasks[0].id,
      agent: 'gemini',
      result: response.text,
      success: true,
      latency: response.latency || 0
    }];
  }
}
```

#### 1.4 实现Multi-Agent Scheduler（我们的逻辑）
**File**: `packages/core/src/schedulers/multi-agent-scheduler.ts`
```typescript
/**
 * Multi-Agent Scheduler - uses Meta Agent + parallel execution
 * This is our custom implementation
 */

import { TaskSchedulerPort, TaskPlan, TaskResult } from './port.js';
import { MetaAgent } from '../../multi-agent-core/meta-agent.js';
import { Scheduler } from '../../multi-agent-core/scheduler.js';

export class MultiAgentScheduler implements TaskSchedulerPort {
  readonly type = 'multi-agent' as const;

  private metaAgent: MetaAgent;
  private scheduler: Scheduler;

  constructor(private config: Config) {
    this.metaAgent = new MetaAgent(config);
    this.scheduler = new Scheduler(config);
  }

  async decompose(task: string, context?: any): Promise<TaskPlan> {
    // Use our Meta Agent for decomposition
    const plan = await this.metaAgent.decompose(task, context);

    return {
      tasks: plan.tasks.map(t => ({
        id: t.id,
        description: t.description,
        agent: t.assigned_agent,
        prompt: t.prompt
      })),
      dependencies: plan.dependencies
    };
  }

  async execute(plan: TaskPlan): Promise<TaskResult[]> {
    // Use our Scheduler for parallel execution
    const results = await this.scheduler.schedule(plan.tasks);

    return results.map(r => ({
      taskId: r.task_id,
      agent: r.agent,
      result: r.result,
      success: r.success,
      latency: r.latency
    }));
  }
}
```

#### 1.5 修改AgentExecutor（唯一需要改的现有文件）
**File**: `packages/core/src/agents/executor.ts`

```typescript
// 在文件顶部添加import
import { getScheduler } from '../schedulers/port.js';

// 在AgentExecutor类的execute方法中修改
export class AgentExecutor<TOutput extends z.ZodTypeAny> {
  async execute(inputs: AgentInputs): Promise<OutputObject<TOutput>> {
    // 🔌 注入点：使用可插拔的调度器
    const scheduler = getScheduler(this.runtimeContext);

    // Log which scheduler is being used
    debugLogger.log(`Using scheduler: ${scheduler.type}`);

    if (scheduler.type === 'multi-agent') {
      // ========== 多代理调度路径 ==========

      // 1. 用Meta Agent分解任务
      const plan = await scheduler.decompose(inputs.task, inputs.context);

      // 2. 显示计划给用户（通过UI）
      if (this.onActivity) {
        this.onActivity({
          type: 'plan_generated',
          plan: plan
        });
      }

      // 3. 并行执行
      const results = await scheduler.execute(plan);

      // 4. 格式化结果
      return this.formatMultiAgentResults(results);

    } else {
      // ========== 原Gemini逻辑（fallback） ==========

      // Original code (unchanged)
      const history: Content[] = [];
      // ... rest of original logic
    }
  }

  private formatMultiAgentResults(results: TaskResult[]): OutputObject {
    // Convert our results to Gemini CLI expected format
    return {
      output: results.map(r => r.result).join('\n\n'),
      metadata: {
        totalTasks: results.length,
        successfulTasks: results.filter(r => r.success).length,
        totalTime: Math.max(...results.map(r => r.latency))
      }
    };
  }
}
```

**这个修改非常小巧**：
- 只在一个方法中添加条件分支
- 不破坏原有逻辑（fallback仍然工作）
- 容易应用patch

#### 1.6 配置文件
**File**: `.gemini/settings.json` (用户级配置)
```json
{
  "scheduler": {
    "type": "multi-agent",  // "default" or "multi-agent"
    "agents": {
      "claude": {
        "enabled": true,
        "apiKey": "${ANTHROPIC_API_KEY}",
        "model": "claude-sonnet-4-5-20250929"
      },
      "openai": {
        "enabled": true,
        "apiKey": "${OPENAI_API_KEY}",
        "model": "gpt-4-turbo"
      }
    }
  }
}
```

---

### Phase 2: 核心逻辑实现（Week 2）

#### 2.1 创建独立package
```bash
# 在monorepo中添加新package
mkdir -p packages/multi-agent-core/src
```

**File**: `packages/multi-agent-core/package.json`
```json
{
  "name": "@gemini-cli/multi-agent-core",
  "version": "1.0.0",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "vitest"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.30.0",
    "openai": "^4.70.0"
  }
}
```

#### 2.2 移植Meta Agent到TypeScript
**File**: `packages/multi-agent-core/src/meta-agent.ts`

```typescript
/**
 * Meta Agent - Task decomposition and agent selection
 * Ported from Python implementation
 */

import Anthropic from '@anthropic-ai/sdk';

export class MetaAgent {
  private client: Anthropic;

  constructor(private config: Config) {
    this.client = new Anthropic({
      apiKey: config.get('anthropicApiKey')
    });
  }

  async decompose(task: string, context?: any): Promise<TaskPlan> {
    const prompt = this.buildDecompositionPrompt(task, context);

    const response = await this.client.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 4096,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    // Parse JSON response
    const planJson = JSON.parse(response.content[0].text);

    return {
      tasks: planJson.tasks,
      dependencies: planJson.dependencies
    };
  }

  private buildDecompositionPrompt(task: string, context?: any): string {
    return `
You are a Meta-Agent that decomposes complex tasks into subtasks.

Task: ${task}

Available agents:
- claude: Best for complex reasoning, system design, architecture
- openai: Best for code generation, APIs, implementation
- gemini: Best for simple tasks, testing, fast execution

Decompose the task into subtasks and assign each to the best agent.
Consider parallelization opportunities.

Return JSON:
{
  "tasks": [
    {
      "id": "task-1",
      "description": "...",
      "assigned_agent": "claude",
      "prompt": "..."
    }
  ],
  "dependencies": {
    "task-2": ["task-1"]
  }
}
`;
  }
}
```

#### 2.3 移植Scheduler到TypeScript
**File**: `packages/multi-agent-core/src/scheduler.ts`

```typescript
/**
 * Scheduler - Parallel task execution with dependency resolution
 * Ported from Python implementation
 */

import { ClaudeAgent, OpenAIAgent, GeminiAgent } from './agents.js';

export class Scheduler {
  private agents: Map<string, Agent>;

  constructor(private config: Config) {
    this.agents = new Map([
      ['claude', new ClaudeAgent(config)],
      ['openai', new OpenAIAgent(config)],
      ['gemini', new GeminiAgent(config)]
    ]);
  }

  async schedule(tasks: Task[]): Promise<TaskResult[]> {
    // Build dependency graph
    const graph = this.buildDependencyGraph(tasks);

    // Topological sort
    const batches = this.resolveDependencies(graph);

    // Execute batches in parallel
    const results: TaskResult[] = [];
    for (const batch of batches) {
      const batchResults = await Promise.all(
        batch.map(task => this.executeTask(task))
      );
      results.push(...batchResults);
    }

    return results;
  }

  private async executeTask(task: Task): Promise<TaskResult> {
    const agent = this.agents.get(task.agent);
    if (!agent) {
      throw new Error(`Unknown agent: ${task.agent}`);
    }

    const startTime = Date.now();
    try {
      const result = await agent.call(task.prompt);
      const latency = Date.now() - startTime;

      return {
        taskId: task.id,
        agent: task.agent,
        result: result,
        success: true,
        latency: latency
      };
    } catch (error) {
      return {
        taskId: task.id,
        agent: task.agent,
        result: error.message,
        success: false,
        latency: Date.now() - startTime
      };
    }
  }

  private buildDependencyGraph(tasks: Task[]): DependencyGraph {
    // Same logic as Python version
    // ...
  }

  private resolveDependencies(graph: DependencyGraph): Task[][] {
    // Topological sort
    // Same logic as Python version
    // ...
  }
}
```

---

### Phase 3: UI定制（Week 3）

#### 3.1 修改启动动画
**File**: `packages/cli/src/ui/components/StartupAnimation.tsx` (新建)

```typescript
import React, { useEffect, useState } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';

export const StartupAnimation: React.FC = () => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(s => (s + 1) % 4);
    }, 500);
    return () => clearInterval(timer);
  }, []);

  const messages = [
    '🚀 Initializing Multi-Agent System...',
    '🤖 Loading Claude, GPT-4, Gemini...',
    '⚡ Ready for parallel execution!',
    '✨ Multi-Agent Gemini CLI'
  ];

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="cyan">
          <Spinner type="dots" />
        </Text>
        <Text> {messages[step]}</Text>
      </Box>
    </Box>
  );
};
```

#### 3.2 修改主界面
**File**: `packages/cli/src/ui/AppContainer.tsx` (修改)

```typescript
// 在现有AppContainer.tsx中添加

import { StartupAnimation } from './components/StartupAnimation.js';
import { MultiAgentPlanView } from './components/MultiAgentPlanView.js';

// 在render中添加条件渲染
{showPlan && <MultiAgentPlanView plan={plan} />}
```

#### 3.3 创建Plan展示组件
**File**: `packages/cli/src/ui/components/MultiAgentPlanView.tsx` (新建)

```typescript
import React from 'react';
import { Box, Text } from 'ink';

export const MultiAgentPlanView: React.FC<{ plan: TaskPlan }> = ({ plan }) => {
  return (
    <Box flexDirection="column" paddingX={2}>
      <Text bold color="yellow">📋 Task Plan:</Text>
      {plan.tasks.map((task, i) => (
        <Box key={task.id} paddingLeft={2}>
          <Text>{i + 1}. </Text>
          <Text color="cyan">[{task.agent}]</Text>
          <Text> {task.description}</Text>
        </Box>
      ))}
      <Box paddingTop={1}>
        <Text color="gray">Execute? [Y/n]: </Text>
      </Box>
    </Box>
  );
};
```

---

## Upstream同步流程示例

### 场景：Google发布了Gemini CLI v0.14.0

```bash
# Step 1: Fetch upstream changes
git fetch upstream
git checkout main
git checkout -b sync-v0.14.0

# Step 2: Merge upstream
git merge upstream/main

# 预期冲突：
# - packages/cli/src/ui/AppContainer.tsx (UI修改)
# - packages/core/src/agents/executor.ts (我们的注入点)

# Step 3: 解决UI冲突（保留我们的定制）
git checkout --ours packages/cli/src/ui/AppContainer.tsx
git checkout --ours packages/cli/src/ui/components/StartupAnimation.tsx

# Step 4: 手动处理executor.ts（重新应用patch）
# 如果我们用了patch-package：
npx patch-package @google/gemini-cli-core --reverse
# 手动调整代码以适应新版本
npx patch-package @google/gemini-cli-core

# Step 5: 测试
npm run test:all
npm run build
npm run start

# Step 6: 提交merge
git add .
git commit -m "chore: sync with upstream v0.14.0"
git push origin main
```

**预期工作量**：
- ✅ 大部分自动merge
- ⚠️ UI冲突：10-30分钟（选择保留我们的）
- ⚠️ executor.ts：30-60分钟（重新应用patch）
- ✅ 我们的packages/multi-agent-core：零冲突（独立）

**总计**：1-2小时 vs 纯fork的1-2天 ✅

---

## 最小修改原则

### 只修改这些文件：

#### 核心层（最小侵入）
```
packages/core/src/
├── schedulers/                    # 🆕 新目录（零冲突）
│   ├── port.ts
│   ├── default-scheduler.ts
│   └── multi-agent-scheduler.ts
└── agents/
    └── executor.ts                # ✏️ 修改（一个方法，~20行）
```

#### UI层（自由修改）
```
packages/cli/src/ui/
├── components/
│   ├── StartupAnimation.tsx       # 🆕 新文件
│   └── MultiAgentPlanView.tsx     # 🆕 新文件
└── AppContainer.tsx               # ✏️ 修改（添加组件引用）
```

#### 独立逻辑（零冲突）
```
packages/multi-agent-core/         # 🆕 完全独立的package
├── src/
│   ├── meta-agent.ts
│   ├── scheduler.ts
│   └── agents.ts
└── package.json
```

**修改文件数**：
- 新增：7个文件（独立，零冲突）
- 修改：2个文件（AppContainer.tsx, executor.ts）

**对比**：
- ❌ 如果到处修改：可能涉及50+文件
- ✅ 我们的方案：只修改2个文件

---

## 成功标准

### Week 1: 架构就位
- ✅ Fork成功，upstream remote配置
- ✅ Scheduler接口定义
- ✅ AgentExecutor注入点修改
- ✅ 可以在default和multi-agent模式间切换

### Week 2: 功能完整
- ✅ Meta Agent工作（任务分解）
- ✅ Scheduler工作（并行执行）
- ✅ 所有agents集成（Claude, GPT, Gemini）
- ✅ 端到端测试通过

### Week 3: UI完善
- ✅ 启动动画自定义
- ✅ Plan展示界面
- ✅ 主题定制
- ✅ 用户体验优化

### Week 4: 生产就绪
- ✅ Upstream sync测试（模拟v0.14.0合并）
- ✅ Patch文件生成（patch-package）
- ✅ 文档完善
- ✅ Beta用户测试

---

## 总结

### 这个方案解决了你的所有问题：

1. ✅ **完全控制UI/UX** - Fork后可以随意修改
2. ✅ **原生体验** - 直接内部集成，不通过MCP
3. ✅ **使用我们的调度** - Meta Agent + Scheduler完整集成
4. ✅ **方便同步更新** - 最小化修改，清晰的patch策略

### 对比MCP方案：

| 维度 | MCP方案 | Fork+隔离方案 |
|------|---------|--------------|
| UI定制 | ❌ 不能 | ✅ 完全自由 |
| 启动动画 | ❌ 不能 | ✅ 可定制 |
| 交互体验 | ⚠️ 中转 | ✅ 原生 |
| 调度逻辑 | ✅ 完全控制 | ✅ 完全控制 |
| Upstream冲突 | ✅ 零 | ⚠️ 少量（2文件）|
| 开发周期 | 2-3周 | 3-4周 |
| 维护成本 | ✅ 低 | ⚠️ 中等 |

### 推荐：

**Fork + 隔离层方案是最优解** ⭐⭐⭐⭐⭐

因为你需要：
- 完全的UI/UX控制 ← MCP做不到
- 原生体验 ← MCP做不到
- 合理的维护成本 ← 隔离架构解决
