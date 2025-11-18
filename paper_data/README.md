# Paper Data Package

**Generated**: 2025-11-14 20:05:06

## Data Sources

### Mock Environment ✅
- **Type**: Simulated agents (MockAgent)
- **Purpose**: Algorithm validation, reproducible baseline
- **Advantages**: Fast, reproducible, no cost
- **Limitations**: Does not reflect real-world network latency or API limits

## Directory Structure

```
paper_data/
├── mock/                    # Mock environment data
│   ├── results.csv          # Excel-compatible
│   ├── table.tex            # LaTeX table (copy to paper)
│   └── charts/              # PDF charts (300 DPI)
└── README.md               # This file
```

## Key Numbers

### Mock Environment
- **Parallel Speedup**: ~4.9x
- **Framework Overhead**: < 10%
- **Memory Usage**: < 50MB (100 tasks)
- **Throughput**: ~200 tasks/s

## Usage Guide (For Teammates)

### Step 1: Review Data
1. Open `results.csv` in Excel
2. Check the numbers
3. Identify key findings

### Step 2: Insert Tables
1. Open `table.tex`
2. Copy to your paper (Section 4)
3. Compile and check formatting

### Step 3: Insert Charts
1. Copy PDF files from `charts/` to your paper's `figures/`
2. Reference in paper: `\includegraphics{figures/performance_chart.pdf}`

### Step 4: Write Analysis
- Explain what the data shows
- Compare with MARBLE/AgentBench
- Discuss limitations (especially Mock vs Real differences)

## Academic Writing Tips

### Mock Data (Section 4.1)
- ✅ Use for: Algorithm correctness, reproducible baseline
- ⚠️ Clearly state: "controlled environment", "simulated agents"
- ❌ Don't claim: Real-world performance without qualification

### Real Data (Section 4.2)
- ✅ Use for: Feasibility, real-world validation
- ✅ Discuss: Network impact, API limits
- ✅ Explain: Why real speedup < mock speedup

### Comparison (Section 4.3)
- ✅ Explain the gap between Mock and Real
- ✅ Identify bottlenecks (network, API)
- ✅ Suggest improvements (caching, batching)

## Citation Guidelines

When comparing with academic benchmarks:

- **MARBLE (ACL'25)**: Use for multi-agent collaboration baseline
- **AgentBench (ICLR'24)**: Use for task success rate
- Always note environment differences

## Questions?

If you need clarification on any data:
1. Check `key_numbers.md` for quick reference
2. Review section templates in `../paper_templates/`
3. Ask the person who ran the tests

---

**Remember**: Academic honesty is paramount. Always clearly distinguish Mock from Real data.
