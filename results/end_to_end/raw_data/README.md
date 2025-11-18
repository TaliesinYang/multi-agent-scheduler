# Raw Experimental Data

This directory contains the complete raw data from the Multi-Agent Scheduler evaluation experiment.

## Files

### JSON Comparison Files
- `db_product_sales_comparison.json` (2 tasks, Linear)
- `os_user_analysis_comparison.json` (3 tasks, Linear)
- `os_system_health_fanout_comparison.json` (8 tasks, Fan-out)
- `web_scraping_fanout_comparison.json` (12 tasks, Fan-out)
- `data_pipeline_mixed_comparison.json` (16 tasks, Mixed DAG)

Each JSON file contains:
- Test metadata (name, input, complexity)
- Sequential mode results (time, success rate, completed/failed tasks)
- Hybrid mode results (time, success rate, batches, speedup)
- Best mode recommendation
- Timestamp

### CSV Summary
- `summary.csv` - All 5 test results in CSV format for easy analysis in Excel/Python/R

Columns:
- test_name, tasks, structure
- seq_time_s, seq_success_rate, seq_completed, seq_failed
- hybrid_time_s, hybrid_success_rate, hybrid_completed, hybrid_failed
- hybrid_batches, speedup, best_mode, timestamp

### Metadata
- `metadata.json` - Experiment configuration and key findings

Contains:
- Timeout configuration (600s)
- Test framework details (AgentBench)
- Tool stack (Claude CLI, DAG Scheduler, CLI Executor)
- Environment info (Python version, platform)
- Key findings (optimal threshold, speedup metrics)
- Limitations (single-run, task types)

## Usage

### Load JSON in Python
```python
import json

with open('db_product_sales_comparison.json') as f:
    data = json.load(f)

print(f"Speedup: {data['hybrid']['speedup']:.2f}×")
```

### Load CSV in Python
```python
import pandas as pd

df = pd.read_csv('summary.csv')
print(df[['test_name', 'tasks', 'speedup']])
```

### Load CSV in R
```r
data <- read.csv('summary.csv')
summary(data$speedup)
```

## Reproducibility

To reproduce these results:
1. Install dependencies: `pip install -r requirements.txt`
2. Configure timeout: `CLIExecutor(timeout=600.0)`
3. Run experiment: `python3 run_end_to_end_test.py`
4. Results will be saved to `results/end_to_end/`

## Citation

If you use this data, please cite:
```
Multi-Agent Scheduler Day 7 Evaluation (2025-11-16)
AgentBench Dependency Tasks Framework
Timeout: 600s, Success Rate: 100%, Total Tasks: 41
```

## Related Files

- **Experiment Report**: `../EXPERIMENT_REPORT.md`
- **Publication Tables**: `../tables/*.md`
- **60s Timeout Backup**: `../backup_60s_timeout/`

---

**Generated**: 2025-11-17 11:16:11
**Total Files**: 7 (5 JSON + 1 CSV + 1 metadata)
**Total Tasks**: 41
**Success Rate**: 100%
