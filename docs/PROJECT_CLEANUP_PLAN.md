# Project Cleanup and Reorganization Plan

**Date**: 2025-11-17
**Goal**: Reorganize project structure for team collaboration and clarity

---

## Current Issues

### 1. Root Directory Overload
- ❌ 20+ status/report MD files in root
- ❌ Hard to find main README.md
- ❌ No clear entry point for new team members

### 2. Test Files Scattered
- ❌ 15+ test_*.py files in root directory
- ❌ Mix of unit tests, integration tests, and temp scripts
- ❌ Unclear which tests are current vs deprecated

### 3. Experimental Data Unorganized
- ❌ benchmark_*.json scattered in root
- ❌ Multiple results/ subdirectories
- ❌ scrape_results/, analysis/, processed_data/ unclear purpose

### 4. Utility Scripts Mixed with Core Code
- ❌ generate_*.py, backup_*.py in root
- ❌ Confusion about what's core vs tooling

---

## Target Structure

```
multi-agent-scheduler/
│
├── README.md                          ← Clean, focused main README
├── CONTRIBUTING.md                    ← Team collaboration guide
├── LICENSE
├── requirements.txt
├── setup.py
├── .gitignore                         ← Updated to ignore temp files
│
├── src/                               ← Core source code (KEEP)
│   ├── __init__.py
│   ├── scheduler.py
│   ├── meta_agent_simple.py
│   ├── orchestration/                 ← DAG scheduling core
│   │   ├── dag_scheduler.py
│   │   ├── cli_executor.py
│   │   ├── meta_agent.py
│   │   └── ...
│   └── adapters/                      ← Agent adapters
│
├── tests/                             ← Official test suite (KEEP)
│   ├── __init__.py
│   ├── test_basic.py
│   ├── test_dag_dependency_integration.py
│   └── benchmark/
│
├── experiments/                       ← NEW: All experimental code
│   ├── README.md                      ← Explains experiment structure
│   ├── day7_evaluation/               ← Day 7 end-to-end tests
│   │   ├── run_end_to_end_test.py
│   │   ├── generate_report.py
│   │   ├── generate_tables.py
│   │   └── backup_raw_data.py
│   ├── temp_tests/                    ← Temporary test scripts
│   │   ├── test_agentbench_simple.py
│   │   ├── cli_parallel_test.py
│   │   └── ... (all test_*.py from root)
│   └── benchmarks/                    ← Benchmark tests
│       └── run_academic_benchmark.py
│
├── results/                           ← NEW: Consolidated results
│   ├── README.md                      ← Explains result structure
│   ├── day7_evaluation/               ← Day 7 evaluation results
│   │   ├── EXPERIMENT_REPORT.md
│   │   ├── tables/
│   │   ├── raw_data/
│   │   └── Multi_Agent_Scheduler_Evaluation_Results.zip
│   ├── benchmarks/                    ← Benchmark results
│   │   ├── benchmark_level1.json
│   │   ├── benchmark_level2.json
│   │   └── hybrid_test_results.json
│   └── archived/                      ← Old experiment data
│       ├── scrape_results/
│       ├── analysis/
│       └── processed_data/
│
├── docs/                              ← Documentation (KEEP but organize)
│   ├── README.md                      ← Docs index
│   ├── architecture/                  ← Architecture docs
│   │   ├── ARCHITECTURE.md
│   │   └── IMPLEMENTATION_ROADMAP.md
│   ├── guides/                        ← User guides
│   │   ├── QUICK_START.md
│   │   ├── USAGE_GUIDE.md
│   │   └── CLI_USAGE.md
│   ├── development/                   ← Dev docs
│   │   ├── CONTRIBUTING.md
│   │   └── DEPLOYMENT.md
│   └── archived/                      ← OLD: Status reports
│       ├── FINAL_STATUS.md
│       ├── PHASE_2_COMPLETION_REPORT.md
│       └── ... (all status MD files)
│
├── scripts/                           ← NEW: Utility scripts
│   ├── README.md
│   ├── cleanup/                       ← Cleanup utilities
│   │   └── organize_project.py
│   └── analysis/                      ← Analysis scripts
│       ├── calculate_avg_rating.py
│       └── example_extract_headers.py
│
├── AgentBench/                        ← AgentBench integration (KEEP)
├── demos/                             ← Demo scripts (KEEP)
├── examples/                          ← Example code (KEEP)
├── web_ui/                            ← Web UI (KEEP if used)
├── monitoring/                        ← Monitoring dashboards (KEEP if used)
│
└── temp/                              ← NEW: Temporary workspace
    ├── .gitkeep
    └── (all temp files go here)
```

---

## File Categorization

### ✅ KEEP in Root (6 files)
```
README.md           ← Main project README (rewrite)
CONTRIBUTING.md     ← New: Team collaboration guide
LICENSE
requirements.txt
setup.py
.gitignore          ← Update with comprehensive rules
```

### 📦 MOVE to docs/archived/
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

### 📦 MOVE to docs/guides/
```
QUICK_START.md
QUICK_CLI_SETUP.md
CLI_USAGE.md
USAGE_GUIDE.md
DAY3_TESTING_GUIDE.md
FORK_SETUP_GUIDE.md
```

### 📦 MOVE to experiments/temp_tests/
```
test_agentbench_simple.py
test_cli_agentbench.py
test_cli_performance.py
test_dag_executor.py
test_dag_quick.py
test_dependency_injection.py
test_env.py
test_import.py
test_multi_round.py
test_adapter_simple.py
cli_parallel_test.py
cli_real_test.py
simple_test.py
quick_test_multi_round.py
minimal_example.py
debug_cli_output.py
```

### 📦 MOVE to experiments/day7_evaluation/
```
run_end_to_end_test.py
generate_report.py
generate_tables.py
backup_raw_data.py
package_results.py
```

### 📦 MOVE to results/day7_evaluation/
```
results/end_to_end/  (entire directory)
Multi_Agent_Scheduler_Evaluation_Results.zip
```

### 📦 MOVE to results/benchmarks/
```
benchmark_level1.json
benchmark_level2.json
benchmark_tasks_10.json
benchmark_results.json
results/hybrid_test_results.json
```

### 📦 MOVE to results/archived/
```
scrape_results/
analysis/
processed_data/
paper_data/
paper_templates/
```

### 📦 MOVE to scripts/analysis/
```
analyze_db_dep_1a.py
calculate_avg_rating.py
example_extract_headers.py
generate_paper_data.py
query_items.py
query_orders.py
query_products.py
read_csv.py
read_csv_script.py
```

### 🗑️ DELETE (temp/build artifacts)
```
config.txt
health_check.txt
urls.txt
test_data.csv
*.egg-info/ (build artifacts)
.pytest_cache/
.benchmarks/
.checkpoints/
workspaces/ (if empty or temp)
```

---

## Implementation Steps

### Step 1: Create New Directory Structure
```bash
mkdir -p experiments/{day7_evaluation,temp_tests,benchmarks}
mkdir -p results/{day7_evaluation,benchmarks,archived}
mkdir -p docs/{architecture,guides,development,archived}
mkdir -p scripts/{cleanup,analysis}
mkdir -p temp
```

### Step 2: Move Files (automated script)
Run `scripts/cleanup/organize_project.py` to move files according to plan

### Step 3: Update .gitignore
Add comprehensive ignore rules for temp files, build artifacts, etc.

### Step 4: Create README files
- Root README.md (focused, clean)
- experiments/README.md (explains experiment structure)
- results/README.md (explains result organization)
- docs/README.md (documentation index)
- scripts/README.md (utility script guide)

### Step 5: Create CONTRIBUTING.md
Team collaboration guide with:
- How to run tests
- Where to add new experiments
- Code structure explanation
- Git workflow

### Step 6: Verify & Test
- Ensure imports still work
- Run core tests
- Verify documentation links

### Step 7: Git Commit
```bash
git add -A
git commit -m "refactor: Reorganize project structure for team collaboration

- Move status reports to docs/archived/
- Consolidate experiments in experiments/
- Organize results in results/
- Create clear README and CONTRIBUTING.md
- Update .gitignore for cleaner repo

BREAKING CHANGE: File paths reorganized. Update any hardcoded paths."
```

---

## Benefits

### For Team Members
✅ Clear entry point (README.md)
✅ Easy to find core code (src/)
✅ Easy to find experiments (experiments/)
✅ Easy to understand structure (CONTRIBUTING.md)

### For Development
✅ Separation of core vs experimental code
✅ Clear test organization
✅ Reusable utility scripts
✅ Clean git history

### For Documentation
✅ All guides in docs/
✅ Archived old status reports
✅ Clear documentation hierarchy

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Run cleanup script
3. ⏳ Create new README files
4. ⏳ Update .gitignore
5. ⏳ Test that everything still works
6. ⏳ Commit to Git

---

**Estimated Time**: 1-2 hours
**Risk**: Low (all files backed up, can revert if needed)
**Impact**: High (much easier for team to navigate)
