# CLI Client Usage Guide

## Quick Start

### 1. Run Performance Test

```bash
# Quick test (1 iteration, simple case only)
python test_cli_performance.py --mode quick --tests simple

# Full test (3 iterations, all cases)
python test_cli_performance.py --mode full
```

### 2. Generate Paper Data

```bash
# Integrate all data sources (Mock + Real + CLI)
python generate_paper_data.py
```

### 3. Use CLI Client Directly

```bash
# Interactive mode
python multi_agent_cli.py

# Batch mode
python multi_agent_cli.py --task "Build a REST API" --agents claude,gemini

# Export results
python multi_agent_cli.py --task "..." --output results.json
```

## File Structure

```
paper_data/
├── mock/                    # Mock benchmark data
│   ├── results.csv
│   └── table.tex
├── real/                    # Real test data (cli_parallel_test.py)
│   ├── results.csv
│   └── table.tex
├── cli_performance/         # CLI performance benchmarks (NEW)
│   ├── results.json
│   ├── summary.csv
│   ├── table.tex
│   └── README.md
└── comparison/              # Mock vs Real comparison
    └── ...
```

## Test Cases

- **Simple**: 3 independent Q&A tasks
- **Medium**: 5-8 tasks with dependencies (web application)
- **Complex**: 10-15 tasks with dependencies (microservices)

## Output Files

### JSON (results.json)
- Raw benchmark data with all metrics
- Use for programmatic analysis

### CSV (summary.csv)
- Excel-compatible summary table
- Use for data visualization

### LaTeX (table.tex)
- Ready-to-use table for paper
- Include with: `\input{paper_data/cli_performance/table.tex}`

## For Paper Writing

### Section 4.2 (CLI Performance)

```latex
\subsection{Real-World CLI Performance}

We evaluated the system using real CLI tools (Claude, Gemini, Codex)
across three complexity levels. Results are shown in Table~\ref{tab:cli_performance}.

\input{paper_data/cli_performance/table.tex}

The results demonstrate that our scheduler achieves X.XXx average speedup
in real-world conditions...
```

## Troubleshooting

### "No CLI agents available"
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code
claude auth login
```

### Test timeout
```bash
# Use quick mode
python test_cli_performance.py --mode quick
```

### Missing data
```bash
# Check what data exists
ls -la paper_data/*/

# Regenerate specific data
python run_academic_benchmark.py --quick    # Mock
python cli_parallel_test.py                 # Real
python test_cli_performance.py              # CLI
```
