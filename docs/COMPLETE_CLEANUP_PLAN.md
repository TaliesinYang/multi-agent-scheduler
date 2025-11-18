# 完整项目清理方案 - 根目录整理

**日期**: 2025-11-17
**目标**: 彻底清理根目录，只保留必要的核心文件和目录

---

## 📊 当前状态分析

### 根目录统计
- **总项目数**: ~100个
- **目录数**: 35个
- **文件数**: 40个配置/文档/脚本文件
- **问题**: 严重混乱，难以找到核心内容

---

## 🗂️ 目录分类与处理方案

### ✅ 必须保留的核心目录（8个）
```
src/                    # 核心源代码
tests/                  # 官方单元测试
experiments/            # 实验代码（已整理）
results/                # 评估结果
docs/                   # 文档（已整理）
data/                   # 数据文件（已整理）
scripts/                # 工具脚本
AgentBench/             # AgentBench子模块
```

### ⚠️ 功能性目录 - 需要评估（9个）

#### 1. 开发环境目录
```
venv/                   # Python虚拟环境
  → 决策: 保留（开发需要）
  → 已在.gitignore中

__pycache__/            # Python缓存
  → 决策: 保留但清空（.gitignore已覆盖）
```

#### 2. 配置和缓存目录
```
.benchmarks/            # Pytest基准测试缓存
  → 决策: 保留（.gitignore已覆盖）

.checkpoints/           # 检查点数据
  → 决策: 保留（可能包含重要检查点）

.pytest_cache/          # Pytest缓存
  → 决策: 保留（.gitignore已覆盖）

config/                 # 配置文件目录
  → 决策: 检查内容，可能合并到根目录或删除
  → 行动: 需要先检查内容
```

#### 3. 项目特定目录
```
demos/                  # 演示代码
  → 决策: 保留（如果有演示需求）
  → 或: 移到 examples/demos/

examples/               # 示例代码
  → 决策: 保留（团队参考用）

monitoring/             # 监控仪表板
  → 决策: 保留（如果在使用）
  → 或: 移到 tools/monitoring/

web_ui/                 # Web UI
  → 决策: 保留（如果在使用）
  → 或: 移到 tools/web_ui/

prototypes/             # 原型代码
  → 决策: 检查内容，可能移到 experiments/prototypes/
```

#### 4. 外部工具目录
```
gemini-cli-fork/        # Gemini CLI fork
  → 决策: 移到 external/gemini-cli-fork/
  → 或: 删除（如果不再使用）

multi_agent_scheduler.egg-info/  # 构建产物
  → 决策: 删除（.gitignore应覆盖）
```

### 🗑️ 临时/测试数据目录 - 建议清理（7个）

```
analysis/               # 分析结果（0 bytes - 空目录）
  → 决策: 检查内容，空则删除
  → 或: 移到 results/analysis/

paper_data/             # 论文数据（16KB）
  → 决策: 移到 results/paper_data/
  → 或: 保留在根目录（如果频繁使用）

paper_templates/        # 论文模板（12KB）
  → 决策: 移到 docs/paper_templates/

processed_data/         # 处理后的数据（0 bytes）
  → 决策: 检查内容，可能删除或移到 results/

raw_data/               # 原始数据（0 bytes）
  → 决策: 检查内容，可能删除或移到 results/

reports/                # 报告（4KB）
  → 决策: 移到 results/reports/

scrape_results/         # 爬虫结果（0 bytes）
  → 决策: 检查内容，可能删除或移到 results/

benchmark_results/      # 基准测试结果
  → 决策: 移到 results/benchmarks/
```

### 🔧 工具/开发目录（5个）
```
.claude/                # Claude CLI配置
  → 决策: 保留（项目配置）

.gemini/                # Gemini CLI配置
  → 决策: 保留（项目配置）

.git/                   # Git仓库
  → 决策: 保留（必须）

.github/                # GitHub配置
  → 决策: 保留（CI/CD等）

logs/                   # 日志文件
  → 决策: 清空内容（保留目录）
  → 已在.gitignore中

workspaces/             # 工作空间
  → 决策: 清空内容（保留目录）
  → 已在.gitignore中
```

---

## 📄 文件分类与处理方案

### ✅ 必须保留的核心文件（4个）
```
README.md               # 主项目README（已更新）
LICENSE                 # 许可证
requirements.txt        # Python依赖
setup.py                # 包配置
```

### 📋 文档文件 - 需要归档（26个MD）

#### 移到 docs/archived/（20个状态报告）
```
ACADEMIC_BENCHMARKS.md
ENHANCEMENT_PROPOSAL_SUMMARY.md
FINAL_100_PERCENT_STATUS.md
FINAL_STATUS.md
NEXT_STEPS_ROADMAP.md
OPTIMIZATION_COMPLETED.md
PERFORMANCE_BENCHMARK_RESULTS.md
PHASE_2_COMPLETION_REPORT.md
PRODUCTION_READY_CHECKLIST.md
PROJECT_STATUS_ANALYSIS.md
SECURITY_AUDIT_REPORT.md
UNIT_TEST_ANALYSIS_AND_NEXT_STEPS.md
WEEK1_DELIVERABLES.md
CLAUDE_CODE_调研总结.md
安全审计报告.md
```

#### 移到 docs/guides/（6个使用指南）
```
CLI_USAGE.md
DAY3_TESTING_GUIDE.md
FORK_SETUP_GUIDE.md
QUICK_CLI_SETUP.md
QUICK_START.md
USAGE_GUIDE.md
```

### 🐍 Python脚本（7个）

```
✅ setup.py                    保留（包配置）
⚠️ multi_agent_cli.py          决策待定（重要CLI库）
   → 选项1: 保留根目录（常用工具）
   → 选项2: 移到 src/cli_client.py
   → 选项3: 移到 tools/multi_agent_cli.py

❌ analyze_db_dep_1a.py        移到 experiments/temp_tests/
❌ query_items.py              移到 experiments/temp_tests/
❌ query_orders.py             移到 experiments/temp_tests/
❌ query_products.py           移到 experiments/temp_tests/
❌ run_academic_benchmark.py   移到 experiments/benchmarks/
```

### 🔧 Shell脚本（4个）

```
⚠️ setup_cli.sh                保留（安装脚本）
⚠️ quick_start.sh              移到 scripts/quick_start.sh
❌ test_db_query.sh            移到 experiments/temp_tests/
❌ test_gemini_config.sh       移到 experiments/temp_tests/
```

### 📦 数据文件（8个）

```
🗑️ benchmark_level2.json       删除（空文件）
🗑️ benchmark_results.json      删除（旧数据或空）
🗑️ config.txt                  删除（临时配置）
🗑️ health_check.txt            删除（临时文件）
🗑️ urls.txt                    删除（临时文件）
🗑️ test_data.csv               删除（测试数据）
```

### ⚙️ 配置文件
```
✅ .gitignore                  保留（已更新）
✅ requirements.txt            保留（依赖列表）
```

---

## 🎯 推荐的清理方案

### 方案1：激进清理（最干净，推荐）

**目标**: 根目录只保留8-10个必要项

#### 执行步骤

**阶段1：移动文档（5分钟）**
```bash
# 状态报告
mv ACADEMIC_BENCHMARKS.md ENHANCEMENT_PROPOSAL_SUMMARY.md FINAL_*.md \
   NEXT_STEPS_ROADMAP.md OPTIMIZATION_COMPLETED.md PERFORMANCE_BENCHMARK_RESULTS.md \
   PHASE_2_COMPLETION_REPORT.md PRODUCTION_READY_CHECKLIST.md \
   PROJECT_STATUS_ANALYSIS.md SECURITY_AUDIT_REPORT.md \
   UNIT_TEST_ANALYSIS_AND_NEXT_STEPS.md WEEK1_DELIVERABLES.md \
   CLAUDE_CODE_调研总结.md 安全审计报告.md \
   docs/archived/

# 使用指南
mv CLI_USAGE.md DAY3_TESTING_GUIDE.md FORK_SETUP_GUIDE.md \
   QUICK_CLI_SETUP.md QUICK_START.md USAGE_GUIDE.md \
   docs/guides/
```

**阶段2：移动Python脚本（3分钟）**
```bash
# 临时测试脚本
mv analyze_db_dep_1a.py query_*.py experiments/temp_tests/

# 基准测试
mv run_academic_benchmark.py experiments/benchmarks/

# 决策：multi_agent_cli.py
# 选项A: 保留在根目录
# 选项B: mv multi_agent_cli.py src/cli_client.py
# 选项C: mv multi_agent_cli.py tools/
```

**阶段3：移动Shell脚本（2分钟）**
```bash
mkdir -p scripts
mv quick_start.sh scripts/
mv test_db_query.sh test_gemini_config.sh experiments/temp_tests/
```

**阶段4：移动数据目录（5分钟）**
```bash
# 移动论文相关
mv paper_data/ results/
mv paper_templates/ docs/

# 移动结果目录
mv benchmark_results/ results/benchmarks_old/

# 检查并移动/删除空目录
# analysis/, processed_data/, raw_data/, scrape_results/
# 如果为空或无用，删除
```

**阶段5：删除临时文件（1分钟）**
```bash
rm -f benchmark_level2.json benchmark_results.json
rm -f config.txt health_check.txt urls.txt test_data.csv
```

**阶段6：清理/移动功能目录（5分钟）**
```bash
# 选项A: 移动不常用目录到 archived/ 或 tools/
mkdir -p archived
mv prototypes/ archived/
mv gemini-cli-fork/ external/

# 选项B: 删除构建产物
rm -rf multi_agent_scheduler.egg-info/

# 清空日志和工作空间（保留目录）
rm -rf logs/* workspaces/*
```

#### 最终根目录结构（方案1）
```
multi-agent-scheduler/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── setup_cli.sh
├── .gitignore
│
├── .git/
├── .github/
├── .claude/
├── .gemini/
│
├── src/                    # 核心代码
├── tests/                  # 测试
├── experiments/            # 实验
├── results/                # 结果
├── docs/                   # 文档
├── data/                   # 数据
├── scripts/                # 脚本
├── AgentBench/             # 子模块
│
├── demos/                  # 演示（可选保留）
├── examples/               # 示例（可选保留）
├── monitoring/             # 监控（可选保留）
├── web_ui/                 # UI（可选保留）
│
├── venv/                   # 虚拟环境（.gitignore）
├── logs/                   # 日志（清空）
└── workspaces/             # 工作空间（清空）
```

**优点**：
- ✅ 根目录清晰专业
- ✅ 只有6-10个关键文件
- ✅ 所有历史文件归档保留
- ✅ 团队协作友好

**缺点**：
- ⚠️ 改动较大（需要仔细测试）
- ⚠️ 可能需要更新一些脚本路径

---

### 方案2：保守清理（稳妥，适合时间紧张）

**目标**: 只移动明确的临时文件，保留其他

#### 执行步骤（10分钟）

```bash
# 1. 移动状态报告MD（最明确的归档）
mv FINAL_*.md WEEK1_DELIVERABLES.md PROJECT_STATUS_ANALYSIS.md docs/archived/

# 2. 移动明确的临时脚本
mv query_*.py analyze_db_dep_1a.py experiments/temp_tests/

# 3. 删除空文件
rm -f benchmark_level2.json config.txt urls.txt

# 4. 清空日志
rm -rf logs/*

# 完成
```

**优点**：
- ✅ 快速（10分钟）
- ✅ 低风险
- ✅ 改善可见

**缺点**：
- ⚠️ 根目录仍然较乱
- ⚠️ 改善有限（~30%）

---

## 📋 详细执行检查清单

### 移动前检查
- [ ] 确认所有Git更改已提交
- [ ] 确认目标目录已创建
- [ ] 备份重要文件（可选）

### 移动文档
- [ ] 移动20个状态报告MD → docs/archived/
- [ ] 移动6个使用指南MD → docs/guides/
- [ ] 创建docs/archived/README.md说明归档内容

### 移动脚本
- [ ] 移动query_*.py等 → experiments/temp_tests/
- [ ] 移动run_academic_benchmark.py → experiments/benchmarks/
- [ ] 移动test_*.sh → experiments/temp_tests/
- [ ] 移动quick_start.sh → scripts/

### 移动数据
- [ ] 移动paper_data/ → results/paper_data/
- [ ] 移动paper_templates/ → docs/paper_templates/
- [ ] 检查analysis/, raw_data/等空目录
- [ ] 移动benchmark_results/ → results/

### 删除临时文件
- [ ] 删除benchmark_level2.json
- [ ] 删除config.txt, urls.txt等临时文件
- [ ] 清空logs/内容
- [ ] 清空workspaces/内容

### 清理目录
- [ ] 删除multi_agent_scheduler.egg-info/
- [ ] 考虑移动prototypes/到archived/
- [ ] 考虑移动gemini-cli-fork/到external/

### 验证
- [ ] 运行核心导入测试
- [ ] 运行pytest测试套件
- [ ] 检查experiments/day7_evaluation/脚本
- [ ] 确认README中的路径正确

### Git提交
- [ ] git add -A
- [ ] git status检查
- [ ] git commit -m "refactor: Complete root directory cleanup"
- [ ] git push origin master

---

## ⏱️ 时间估算

### 方案1（激进清理）
- 准备和检查：5分钟
- 移动文档：5分钟
- 移动脚本：3分钟
- 移动目录：8分钟
- 删除文件：2分钟
- 验证测试：5分钟
- Git提交：3分钟
- **总计**: 约30-35分钟

### 方案2（保守清理）
- 移动明确文件：7分钟
- 删除临时文件：2分钟
- Git提交：2分钟
- **总计**: 约10-12分钟

---

## 🎯 建议

**推荐方案1（激进清理）**，理由：
1. 项目已经做了一半清理，不如一次性完成
2. 时间成本可接受（30分钟）
3. Git可以完全回滚，风险可控
4. 最终效果专业，团队协作友好

**执行顺序**：
1. 下次session开始时先git status确认干净
2. 按阶段执行（每阶段后验证）
3. 遇到问题立即停止，使用git reset回滚
4. 全部完成后运行完整测试套件

---

## 📝 待决策的问题

1. **multi_agent_cli.py位置**？
   - 保留根目录
   - 移到src/cli_client.py
   - 移到tools/

2. **demos/, examples/, monitoring/, web_ui/目录**？
   - 保留（如果团队使用）
   - 移到archived/或tools/
   - 需要确认是否在使用

3. **paper_data/和paper_templates/**？
   - 移到results/和docs/
   - 保留根目录（如果频繁使用）

4. **空数据目录（analysis/, raw_data/等）**？
   - 删除空目录
   - 保留目录结构

---

**文档创建时间**: 2025-11-17
**下次执行时参考**: 此文档 + 深度分析报告
