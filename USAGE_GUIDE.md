# 使用指南 - 论文数据生成系统

**版本**: v1.0
**更新**: 2024-11-14

---

## 🎯 快速开始（< 5 分钟）

```bash
# 1. 运行 Mock benchmark (5 分钟)
source venv/bin/activate
python run_academic_benchmark.py --quick

# 2. 运行真实测试 (可选，约 2 分钟)
python cli_parallel_test.py

# 3. 生成论文数据 (< 10 秒)
python generate_paper_data.py

# 4. 查看结果
ls paper_data/
cat paper_data/README.md
cat paper_data/key_numbers.md
```

**输出**: `paper_data/` 目录，包含所有论文所需的数据和图表

---

## 📚 详细使用说明

### 场景 1: Mock + 真实测试（推荐）

```bash
# 步骤 1: Mock benchmark
python run_academic_benchmark.py --quick
# 输出: benchmark_level1.json, benchmark_level2.json

# 步骤 2: 真实 CLI 测试
python cli_parallel_test.py
# 输出: real_test_results.json
# 注意: 会调用真实 LLM (Gemini/Claude CLI)

# 步骤 3: 生成论文数据
python generate_paper_data.py
# 输出: paper_data/ 完整数据包
```

**优点**: 数据最完整，论文最有说服力
**时间**: 总共约 8 分钟
**成本**: $0 (Mock 免费, CLI 订阅制)

---

### 场景 2: 仅 Mock 测试（快速）

```bash
# 步骤 1: Mock benchmark
python run_academic_benchmark.py --quick

# 步骤 2: 生成数据（仅 Mock）
python generate_paper_data.py

# 查看结果
open paper_data/mock/results.csv
```

**优点**: 快速，可重现
**缺点**: 缺少真实环境验证
**时间**: < 6 分钟
**成本**: $0

---

### 场景 3: 仅真实测试

```bash
# 步骤 1: 真实测试
python cli_parallel_test.py

# 步骤 2: 生成数据（仅真实）
python generate_paper_data.py --real-only

# 查看结果
open paper_data/real/results.csv
```

**优点**: 真实性能数据
**缺点**: 缺少可重现 baseline
**时间**: ~2 分钟
**成本**: $0 (CLI 订阅)

---

## 📁 输出文件结构

```
paper_data/
├── README.md                     # 数据说明文档 ⭐
├── key_numbers.md                # 关键数字清单 ⭐
│
├── mock/                         # Mock 环境数据
│   ├── results.csv               # Excel 可打开
│   ├── table.tex                 # LaTeX 表格（复制到论文）
│   └── charts/
│       └── performance_chart.pdf # 性能图表 (300 DPI)
│
├── real/                         # 真实环境数据
│   ├── results.csv
│   ├── table.tex
│   └── charts/
│       └── serial_vs_parallel.pdf
│
└── comparison/                   # Mock vs Real 对比
    ├── mock_vs_real.csv
    ├── comparison_table.tex
    └── charts/
        └── speedup_comparison.pdf
```

**⭐ 必读文件**:
1. `README.md` - 了解数据来源和使用方法
2. `key_numbers.md` - 快速获取关键数字

---

## 📊 数据使用方法

### 步骤 1: 查看数据

```bash
# Excel 打开 CSV
open paper_data/mock/results.csv
open paper_data/real/results.csv

# 或使用命令行
cat paper_data/key_numbers.md
```

### 步骤 2: 复制表格到论文

```latex
% 在论文中添加：
\input{tables/mock_table.tex}

% 然后复制文件：
cp paper_data/mock/table.tex your_paper/tables/
```

### 步骤 3: 插入图表

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{figures/performance_chart.pdf}
\caption{Mock environment performance}
\label{fig:mock_perf}
\end{figure}

% 复制图表文件：
cp paper_data/mock/charts/*.pdf your_paper/figures/
```

### 步骤 4: 使用关键数字

打开 `key_numbers.md`，找到需要的数字，直接复制到论文：

```markdown
"Our scheduler achieved a 4.9x parallel speedup..."
```

---

## 🎓 给队友的数据包

### 创建数据包

```bash
# 打包所有数据
zip -r paper_data_package.zip paper_data/

# 或使用 tar
tar -czf paper_data_package.tar.gz paper_data/
```

### 数据包内容

```
paper_data_package.zip
├── README.md          # 先看这个！
├── key_numbers.md     # 关键数字（直接用于写作）
├── mock/              # Mock 数据
├── real/              # 真实数据
└── comparison/        # 对比数据
```

### 队友工作流

1. **解压**: `unzip paper_data_package.zip`
2. **阅读**: `cat paper_data/README.md`
3. **查看数据**: 打开 CSV 文件
4. **写作**: 参考 `key_numbers.md` 和 `paper_templates/section_4_template.md`
5. **插入**: 复制 LaTeX 表格和 PDF 图表

---

## 🛠️ 故障排查

### 问题 1: 找不到 Mock 数据

```
❌ 未找到 Mock benchmark 数据
```

**解决**:
```bash
# 运行 Mock benchmark
python run_academic_benchmark.py --quick
```

---

### 问题 2: 找不到真实数据

```
❌ 未找到真实测试数据: real_test_results.json
```

**解决**:
```bash
# 运行真实测试
python cli_parallel_test.py

# 或只处理 Mock 数据
python generate_paper_data.py  # 会自动跳过 Real
```

---

### 问题 3: matplotlib 未安装

```
⚠️ matplotlib 未安装，将跳过图表生成
```

**解决**:
```bash
pip install matplotlib numpy
```

**影响**: 不会生成 PDF 图表，但 CSV 和 LaTeX 表格仍然正常

---

### 问题 4: CLI 测试失败

```
❌ Gemini CLI 加载失败
```

**解决**:
```bash
# 确认 CLI 工具已安装和认证
gemini auth login
claude auth login

# 或只运行 Mock 测试
python run_academic_benchmark.py --quick
python generate_paper_data.py
```

---

## 📝 论文写作建议

### ✅ 正确做法

```markdown
✅ "In controlled benchmarks, our scheduler achieved 4.9x speedup..."
✅ "Real-world validation with CLI demonstrates feasibility..."
✅ "The gap between mock (4.9x) and real (2.4x) reveals network bottleneck..."
```

### ❌ 错误做法

```markdown
❌ "Our scheduler achieves 4.9x speedup" (没说是 Mock)
❌ "Outperforms MARBLE by 19%" (MARBLE 是真实环境，你是 Mock，不可比)
❌ 只展示 Mock 数据，不提真实环境
```

### 💡 写作模板

参考 `paper_templates/section_4_template.md`:
- Section 4.1: Mock Benchmarks
- Section 4.2: Real Validation
- Section 4.3: Comparison
- Section 4.4: Discussion

---

## 🔧 高级用法

### 自定义输出目录

```bash
python generate_paper_data.py --output custom_dir/
```

### 仅处理真实数据

```bash
python generate_paper_data.py --real-only
```

### 重新生成图表

```bash
# 删除旧图表
rm -rf paper_data/*/charts/

# 重新生成
python generate_paper_data.py
```

---

## 📞 获取帮助

### 查看帮助信息

```bash
python generate_paper_data.py --help
python run_academic_benchmark.py --help
```

### 检查数据完整性

```bash
# 查看生成了哪些文件
find paper_data -type f

# 查看数据统计
cat paper_data/key_numbers.md
```

### 常见问题

1. **数据不完整?** → 检查是否运行了所有测试
2. **图表质量差?** → 确保安装了 matplotlib
3. **LaTeX 编译错误?** → 检查表格格式
4. **数字对不上?** → 重新运行测试

---

## 📚 相关文档

- **论文模板**: `paper_templates/section_4_template.md`
- **数据说明**: `paper_data/README.md`
- **关键数字**: `paper_data/key_numbers.md`
- **项目文档**: `README.md`

---

## ✅ 检查清单

### 数据生成

- [ ] 已运行 Mock benchmark
- [ ] 已运行真实测试（可选）
- [ ] 已生成论文数据
- [ ] 已查看 README.md
- [ ] 已查看 key_numbers.md

### 论文写作

- [ ] 已复制 LaTeX 表格
- [ ] 已插入 PDF 图表
- [ ] 已参考论文模板
- [ ] 已明确区分 Mock vs Real
- [ ] 已解释性能差距

### 数据包准备

- [ ] 已打包数据文件
- [ ] 已包含 README
- [ ] 已测试队友能否打开
- [ ] 已提供使用说明

---

## 🎉 完成！

你现在拥有：
- ✅ 完整的论文数据
- ✅ LaTeX 表格和 PDF 图表
- ✅ 数据说明文档
- ✅ 论文写作模板
- ✅ 可以打包给队友的数据包

**下一步**:
1. 查看 `paper_data/key_numbers.md` 了解关键数字
2. 参考 `paper_templates/section_4_template.md` 写论文
3. 将数据包发给队友

**祝论文写作顺利！** 🚀
