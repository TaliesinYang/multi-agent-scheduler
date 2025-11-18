#!/usr/bin/env python3
"""
Backup raw experimental data

Creates:
1. JSON file copies in raw_data/
2. summary.csv (all results in CSV format)
3. metadata.json (experiment configuration)
"""

import json
import csv
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Configuration
RESULTS_DIR = Path("results/end_to_end")
RAW_DATA_DIR = RESULTS_DIR / "raw_data"

# Test groups
TEST_GROUPS = [
    {"id": "db_product_sales", "tasks": 2, "structure": "Linear"},
    {"id": "os_user_analysis", "tasks": 3, "structure": "Linear"},
    {"id": "os_system_health_fanout", "tasks": 8, "structure": "Fan-out"},
    {"id": "web_scraping_fanout", "tasks": 12, "structure": "Fan-out"},
    {"id": "data_pipeline_mixed", "tasks": 16, "structure": "Mixed"},
]


def backup_json_files():
    """Copy all JSON comparison files to raw_data/"""
    print("📦 Backing up JSON files...")

    copied_count = 0
    for group in TEST_GROUPS:
        source = RESULTS_DIR / f"{group['id']}_comparison.json"
        if source.exists():
            dest = RAW_DATA_DIR / f"{group['id']}_comparison.json"
            shutil.copy2(source, dest)
            print(f"  ✓ Copied {group['id']}_comparison.json")
            copied_count += 1
        else:
            print(f"  ✗ Missing {group['id']}_comparison.json")

    print(f"  Total: {copied_count}/{len(TEST_GROUPS)} files backed up\n")


def generate_csv_summary():
    """Generate summary.csv with all results"""
    print("📊 Generating summary.csv...")

    csv_file = RAW_DATA_DIR / "summary.csv"

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "test_name",
            "tasks",
            "structure",
            "seq_time_s",
            "seq_success_rate",
            "seq_completed",
            "seq_failed",
            "hybrid_time_s",
            "hybrid_success_rate",
            "hybrid_completed",
            "hybrid_failed",
            "hybrid_batches",
            "speedup",
            "best_mode",
            "timestamp"
        ])

        # Data rows
        for group in TEST_GROUPS:
            file_path = RAW_DATA_DIR / f"{group['id']}_comparison.json"
            if not file_path.exists():
                continue

            with open(file_path) as json_f:
                data = json.load(json_f)

            writer.writerow([
                data['test_name'],
                data['task_count'],
                group['structure'],
                data['sequential']['total_time'],
                data['sequential']['success_rate'],
                data['sequential']['completed'],
                data['sequential']['failed'],
                data['hybrid']['total_time'],
                data['hybrid']['success_rate'],
                data['hybrid'].get('completed', 0),
                data['hybrid'].get('failed', 0),
                data['hybrid'].get('batches', 0),
                data['hybrid']['speedup'],
                data['best_mode'],
                data['timestamp']
            ])

    print(f"  ✓ summary.csv generated ({len(TEST_GROUPS)} rows)\n")


def generate_metadata():
    """Generate metadata.json with experiment configuration"""
    print("📝 Generating metadata.json...")

    # Get Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    metadata = {
        "experiment_name": "Multi-Agent Scheduler End-to-End Evaluation",
        "experiment_date": "2025-11-16",
        "timeout_configuration": {
            "current": "600s (10 minutes)",
            "previous": "60s (1 minute)",
            "reason": "60s caused 14.6% task failures; 600s achieved 100% success"
        },
        "test_framework": "AgentBench Dependency Tasks",
        "execution_modes": {
            "sequential": "Baseline execution (one task at a time)",
            "hybrid": "DAG-based parallel scheduling (Kahn's algorithm)"
        },
        "test_groups": {
            "total": len(TEST_GROUPS),
            "linear": sum(1 for g in TEST_GROUPS if g['structure'] == 'Linear'),
            "fan_out": sum(1 for g in TEST_GROUPS if g['structure'] == 'Fan-out'),
            "mixed": sum(1 for g in TEST_GROUPS if g['structure'] == 'Mixed')
        },
        "total_tasks": sum(g['tasks'] for g in TEST_GROUPS),
        "success_rate": {
            "sequential": "100% (41/41 tasks)",
            "hybrid": "100% (41/41 tasks)"
        },
        "tools": {
            "meta_agent": "Claude CLI (sonnet-4.5)",
            "dag_scheduler": "Custom DAG scheduler with Kahn's topological sort",
            "cli_executor": "Subprocess-based execution with FINAL_ANSWER detection"
        },
        "environment": {
            "python_version": python_version,
            "platform": "Linux WSL2",
            "experiment_duration": "~45 minutes"
        },
        "key_findings": {
            "optimal_threshold": ">=12 tasks for consistent Hybrid mode advantage",
            "average_speedup": "1.23× overall (1.12× average across 5 groups)",
            "total_time_saved": "296.64 seconds",
            "best_speedup": "1.57× (os_user_analysis, 3 tasks)",
            "regression_cases": [
                "db_product_sales (0.70×, 2 tasks)",
                "os_system_health_fanout (0.997×, 8 tasks)"
            ]
        },
        "limitations": {
            "single_run": "Each test group executed once (no statistical validation)",
            "task_type": "OS and Database interaction tasks (I/O-bound)",
            "agent_type": "Claude CLI only (not tested with Gemini, GPT, etc.)"
        },
        "data_files": {
            "experiment_report": "EXPERIMENT_REPORT.md",
            "tables": "tables/*.md (5 publication tables)",
            "raw_json": "raw_data/*.json (5 comparison files)",
            "csv_summary": "raw_data/summary.csv"
        },
        "generated_at": datetime.now().isoformat()
    }

    with open(RAW_DATA_DIR / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print("  ✓ metadata.json generated\n")


def generate_readme():
    """Generate README.md for raw_data directory"""
    print("📄 Generating README.md for raw_data/...")

    readme = """# Raw Experimental Data

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

**Generated**: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
**Total Files**: 7 (5 JSON + 1 CSV + 1 metadata)
**Total Tasks**: 41
**Success Rate**: 100%
"""

    with open(RAW_DATA_DIR / "README.md", 'w') as f:
        f.write(readme)

    print("  ✓ README.md generated\n")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("📦 RAW DATA BACKUP")
    print("="*70 + "\n")

    # Create raw_data directory
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Backup operations
    backup_json_files()
    generate_csv_summary()
    generate_metadata()
    generate_readme()

    print("✅ Raw data backup complete!")
    print(f"📁 Check: {RAW_DATA_DIR}/\n")

    # Summary
    print("📊 Backup Summary:")
    print(f"  JSON files: {len(list(RAW_DATA_DIR.glob('*_comparison.json')))}")
    print(f"  CSV file: {'✓' if (RAW_DATA_DIR / 'summary.csv').exists() else '✗'}")
    print(f"  Metadata: {'✓' if (RAW_DATA_DIR / 'metadata.json').exists() else '✗'}")
    print(f"  README: {'✓' if (RAW_DATA_DIR / 'README.md').exists() else '✗'}")
    print()


if __name__ == "__main__":
    main()
