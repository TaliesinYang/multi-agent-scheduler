# 统计验证实验 - 快速启动

## ✅ 已完成的准备工作

1. **✓** 输出目录结构已创建 (`results/statistical_validation/`)
2. **✓** 主实验脚本已创建 (`run_statistical_validation.py`)
3. **✓** 统计分析脚本已创建 (`analyze_statistical_results.py`)
4. **✓** 使用指南已创建 (`STATISTICAL_VALIDATION_GUIDE.md`)
5. **✓** 语法检查通过（两个脚本都验证无误）
6. **✓** Python依赖已安装 (numpy, scipy, pandas)

## 🚀 立即启动（3步）

### 步骤 1: 确认AgentBench数据

```bash
# 检查AgentBench任务文件是否存在
ls AgentBench/dependency_tasks.json

# 如果不存在，检查archived目录
ls archived/AgentBench/dependency_tasks.json
```

**如果文件不存在**：
- 该文件包含实验所需的任务定义
- 根据README，之前的Day 7评估使用了这个文件
- 可能需要从备份或其他位置恢复

**如果文件存在**：继续步骤2

### 步骤 2: 启动实验

```bash
# 推荐方式：使用tmux（可断开SSH）
cd experiments/day7_evaluation
tmux new -s stats "python3 run_statistical_validation.py"

# 分离tmux会话：按 Ctrl+B，然后按 D
# 重新连接：tmux attach -t stats
```

**或者使用nohup（后台运行）：**

```bash
cd experiments/day7_evaluation
nohup python3 run_statistical_validation.py > ../../results/statistical_validation/run.log 2>&1 &

# 记录进程ID
echo $! > ../../results/statistical_validation/pid.txt
```

### 步骤 3: 监控进度

```bash
# 实时查看主日志
tail -f ../../results/statistical_validation/master.log

# 查看完成的运行次数
ls ../../results/statistical_validation/raw_runs/ | wc -l

# 查看实时统计（每完成一次运行后更新）
cat ../../results/statistical_validation/statistics_live.json
```

---

## 📊 实验规模

- **总运行次数**: 90次 (3组 × 30次重复)
- **任务执行总数**: ~1,860次
- **预计时间**: ~19小时
- **输出大小**: ~1-2 MB

### 选定的任务组

| 组ID | 任务数 | 依赖结构 | Day 7加速比 |
|------|--------|----------|-------------|
| os_user_analysis | 3 | Linear | 1.57× |
| web_scraping_fanout | 12 | Fan-out | 1.31× |
| data_pipeline_mixed | 16 | Mixed | 1.32× |

---

## 🔍 监控命令速查

```bash
# 查看进度（自动刷新）
watch -n 10 'echo "完成: $(ls results/statistical_validation/raw_runs/ 2>/dev/null | wc -l)/90"'

# 查看最后10行日志
tail -n 10 results/statistical_validation/master.log

# 检查是否有错误
cat results/statistical_validation/errors.log

# 查看实时统计（格式化输出）
python3 -m json.tool results/statistical_validation/statistics_live.json
```

---

## ⚠️ 重要注意事项

### 中断恢复

实验具有崩溃恢复功能：
- 如果中断，直接重新运行脚本即可
- 已完成的运行会自动跳过
- 从断点继续执行

### 磁盘空间

- 需要约100 MB空闲空间
- 检查：`df -h .`

### 超时设置

- 每个任务超时：600秒（10分钟）
- 基于Day 7数据，这个设置可达到100%成功率

---

## 📈 完成后的分析

等实验完成（~19小时后）：

```bash
# 运行统计分析
cd experiments/day7_evaluation
python3 analyze_statistical_results.py
```

**生成的输出**：
- `publication_tables/table_statistical_validation.tex` - LaTeX表格（论文用）
- `publication_tables/table_statistical_validation.md` - Markdown表格（文档用）
- `figures/fig1_execution_time_comparison.png` - 执行时间对比图
- `figures/fig2_speedup_confidence_intervals.png` - 加速比置信区间图
- `complete_analysis.json` - 完整统计分析结果

---

## 🎯 预期结果

基于Day 7探索性数据，预期：

| 指标 | os_user_analysis | web_scraping_fanout | data_pipeline_mixed |
|------|------------------|---------------------|---------------------|
| 加速比（均值） | ~1.55× ± 0.1 | ~1.30× ± 0.15 | ~1.32× ± 0.12 |
| 统计显著性 | p < 0.001 | p < 0.01 | p < 0.01 |
| 效应量 | Large (d>0.8) | Large (d>0.8) | Large (d>0.8) |

---

## 🆘 故障排除

### 问题：找不到AgentBench任务文件

**解决方案**：
1. 检查`AgentBench/dependency_tasks.json`
2. 检查`archived/AgentBench/dependency_tasks.json`
3. 如果都不存在，可能需要：
   - 从备份恢复
   - 检查之前的Day 7评估是如何获取数据的
   - 联系项目维护者获取数据文件

### 问题：实验卡住不动

**症状**：超过10分钟没有进度

**解决方案**：
- 600秒超时应该会自动杀死卡住的任务
- 检查`master.log`查看当前任务
- 如果确实卡住，Ctrl+C中断，然后重启（会自动恢复）

### 问题：高失败率

**检查**：
```bash
# 测试Claude CLI
claude -p "Test. Say FINAL_ANSWER: OK" --tools Bash --dangerously-skip-permissions

# 查看失败原因
cat results/statistical_validation/errors.log
```

---

## 📝 检查清单

在启动实验前：

- [ ] 确认AgentBench数据文件存在
- [ ] 确认有~19小时不间断运行时间
- [ ] 确认有100+ MB磁盘空闲空间
- [ ] 测试Claude CLI工具正常工作
- [ ] 阅读完整使用指南（STATISTICAL_VALIDATION_GUIDE.md）

准备就绪后：

- [ ] 使用tmux或nohup启动实验
- [ ] 验证日志文件正在更新
- [ ] 设置提醒（19小时后检查结果）
- [ ] 断开SSH前确认tmux会话已分离

---

## 📚 完整文档

详细信息请参阅：
- **STATISTICAL_VALIDATION_GUIDE.md** - 完整使用指南（推荐阅读）
- **run_statistical_validation.py** - 主实验脚本（有详细注释）
- **analyze_statistical_results.py** - 分析脚本（有详细注释）

---

**祝实验顺利！** 🚀

预计完成时间：启动后约19小时
