# Statistical Validation Experiment Guide

## Overview

This directory contains scripts for running a comprehensive **90-run statistical validation experiment** to validate DAG scheduling performance claims with proper statistical rigor.

**Experiment Scope:**
- **3 task groups** (Linear, Fan-out, Mixed DAG)
- **30 runs per group**
- **2 modes per run** (Sequential baseline + Hybrid DAG scheduling)
- **Total: 90 runs, 180 group executions, ~1,860 individual task executions**

**Estimated Runtime:** ~19 hours (overnight run)

---

## Quick Start

### 1. Launch Experiment (Recommended: tmux)

```bash
# Navigate to experiment directory
cd experiments/day7_evaluation

# Start in tmux (survives SSH disconnection)
tmux new -session -s stats "python3 run_statistical_validation.py"

# Detach from tmux: Press Ctrl+B, then D
# Reattach later: tmux attach -t stats
```

**Alternative: nohup (background process)**

```bash
nohup python3 run_statistical_validation.py > experiment.log 2>&1 &

# Get process ID
echo $!

# Monitor: tail -f experiment.log
```

### 2. Monitor Progress

```bash
# Real-time progress log
tail -f ../../results/statistical_validation/master.log

# View live statistics (updated after each run)
cat ../../results/statistical_validation/statistics_live.json

# Check how many runs completed
ls ../../results/statistical_validation/raw_runs/ | wc -l

# Check for errors
cat ../../results/statistical_validation/errors.log
```

### 3. After Completion (~19 hours later)

```bash
# Run statistical analysis
python3 analyze_statistical_results.py

# Check outputs
ls -la ../../results/statistical_validation/publication_tables/
ls -la ../../results/statistical_validation/figures/
```

---

## Experiment Configuration

### Selected Task Groups

| Group ID | Tasks | Structure | Day 7 Speedup | Why Selected |
|----------|-------|-----------|---------------|--------------|
| `os_user_analysis` | 3 | Linear chain | 1.57× | Best hybrid performance |
| `web_scraping_fanout` | 12 | Fan-out | 1.31× | Clear hybrid advantage |
| `data_pipeline_mixed` | 16 | Mixed DAG | 1.32× | Most complex scenario |

### Execution Parameters

- **Timeout:** 600s per task (proven 100% success rate)
- **Pause between runs:** 5 seconds (prevent overheating)
- **Crash recovery:** Automatic (resumes from last completed run)
- **Incremental saving:** Each run saved immediately

---

## Output Structure

```
results/statistical_validation/
├── raw_runs/                           # Individual run results (90 files)
│   ├── run_001_os_user_analysis.json
│   ├── run_002_os_user_analysis.json
│   └── ...
│
├── aggregated_data.csv                 # All runs in single CSV
├── statistics_live.json                # Real-time statistics (updated per run)
├── complete_analysis.json              # Full analysis results
│
├── publication_tables/                 # Publication-ready outputs
│   ├── table_statistical_validation.tex    # LaTeX table
│   ├── table_statistical_validation.md     # Markdown table
│   └── statistical_summary.csv             # CSV summary
│
├── figures/                            # Publication-quality figures
│   ├── fig1_execution_time_comparison.png
│   └── fig2_speedup_confidence_intervals.png
│
├── master.log                          # Experiment progress log
└── errors.log                          # Error tracking

```

---

## Crash Recovery

The experiment is **crash-safe**:

1. **Automatic Resume:** If interrupted, simply restart the script
   ```bash
   python3 run_statistical_validation.py
   ```

2. **Skip Completed:** Already-completed runs are automatically skipped
   - Check completed runs: `ls results/statistical_validation/raw_runs/ | wc -l`
   - Example: If 45/90 runs completed before crash, restart will continue from run 46

3. **Data Integrity:** Each run is saved immediately after completion
   - No data loss even if process is killed mid-experiment

---

## Monitoring Commands

### Basic Monitoring

```bash
# Watch progress in real-time
tail -f ../../results/statistical_validation/master.log

# Check completion status
echo "Completed: $(ls ../../results/statistical_validation/raw_runs/ 2>/dev/null | wc -l)/90 runs"

# Estimated time remaining (rough)
# If you know how many runs completed and started time, you can calculate
```

### Detailed Monitoring

```bash
# Check last 50 log lines
tail -n 50 ../../results/statistical_validation/master.log

# View current statistics
cat ../../results/statistical_validation/statistics_live.json | python3 -m json.tool

# Check system resource usage
htop  # or: top

# Check disk space
df -h .
```

### Error Checking

```bash
# Check if any errors occurred
cat ../../results/statistical_validation/errors.log

# Count failed runs (if any)
grep -c "❌" ../../results/statistical_validation/master.log || echo "No failures"
```

---

## Statistical Analysis

After experiment completion, run the analysis script:

```bash
python3 analyze_statistical_results.py
```

**Analysis Outputs:**

1. **Descriptive Statistics**
   - Mean ± Standard Deviation
   - Min, Max, Median, Quartiles
   - 95% Confidence Intervals
   - Coefficient of Variation (stability measure)

2. **Inferential Statistics**
   - Paired t-tests (Sequential vs Hybrid, within-group)
   - p-values (statistical significance)
   - Cohen's d effect sizes
   - Degrees of freedom

3. **Publication Outputs**
   - LaTeX table (for paper Section 8)
   - Markdown table (for README/documentation)
   - CSV summary (for Excel/data analysis)
   - High-resolution figures (300 DPI PNG)

---

## Troubleshooting

### Problem: Experiment hangs on a task

**Symptoms:** No progress for >10 minutes

**Solution:**
- Check `master.log` to see which task is running
- The 600s timeout should kill stuck tasks automatically
- If truly hung, restart (crash recovery will resume)

### Problem: High failure rate

**Symptoms:** Many "✗" marks in logs, low success rates

**Possible causes:**
1. CLI tool (claude) not configured properly
2. Network issues (if CLI requires internet)
3. System resource exhaustion (memory/CPU)

**Solution:**
```bash
# Check CLI tool
claude -p "Test. Say FINAL_ANSWER: OK" --tools Bash --dangerously-skip-permissions

# Check system resources
free -h  # Memory
top      # CPU usage

# Review errors
cat ../../results/statistical_validation/errors.log
```

### Problem: Disk full

**Symptoms:** Write errors in logs

**Solution:**
```bash
# Check disk space
df -h .

# Calculate expected disk usage:
# 90 runs × ~10 KB/run = ~1 MB total (very small)
# You need at least 100 MB free to be safe
```

### Problem: Want to stop experiment early

**Approach 1: Graceful stop**
- Press `Ctrl+C` in tmux session
- Experiment will save current progress and exit

**Approach 2: Kill process**
```bash
# Find process ID
ps aux | grep run_statistical_validation

# Kill it
kill <PID>

# Data is safe (incremental saving)
# Resume anytime by restarting script
```

---

## Expected Results

Based on Day 7 exploratory data (n=1 per group):

| Group | Expected Speedup | Expected Significance |
|-------|------------------|----------------------|
| `os_user_analysis` | ~1.55× ± 0.1× | p < 0.001 (highly significant) |
| `web_scraping_fanout` | ~1.30× ± 0.15× | p < 0.01 (significant) |
| `data_pipeline_mixed` | ~1.32× ± 0.12× | p < 0.01 (significant) |

**Key Hypotheses to Test:**

1. **H1:** Hybrid DAG scheduling is significantly faster than sequential for all 3 groups (p < 0.05)
2. **H2:** Speedup is stable (CV < 15%) across repeated runs
3. **H3:** Effect sizes are large (Cohen's d > 0.8)

---

## Integration with Paper

After analysis completes, use these outputs for the paper:

**Section 8 (Results):**
- Include `table_statistical_validation.tex` in LaTeX source
- Reference `fig1_execution_time_comparison.png` and `fig2_speedup_confidence_intervals.png`
- Report p-values, confidence intervals, and effect sizes

**Section 9 (Discussion):**
- Interpret statistical significance
- Discuss practical significance (speedup magnitude)
- Address variance/stability (coefficient of variation)
- Compare with Day 7 exploratory results (validate consistency)

**Example Text:**

> Statistical validation across 30 runs per task group confirmed the performance advantages of DAG-based scheduling. For the `os_user_analysis` group (3 tasks, linear chain), hybrid scheduling achieved a mean speedup of 1.55× (95% CI: [1.48, 1.62], t(29) = 42.3, p < 0.001, d = 2.8). This large effect size indicates not only statistical significance but also strong practical significance...

---

## Files in This Directory

| File | Purpose | When to Use |
|------|---------|-------------|
| `run_statistical_validation.py` | Main experiment script | Run once to execute 90 trials |
| `analyze_statistical_results.py` | Statistical analysis | Run after experiment completes |
| `run_end_to_end_test.py` | Original evaluation script | Reference (infrastructure reused) |
| `STATISTICAL_VALIDATION_GUIDE.md` | This file | Read before starting experiment |

---

## Questions?

**Before starting:**
- Review this entire guide
- Ensure ~20 hours of uninterrupted runtime available
- Verify disk space (need ~100 MB free)
- Test CLI tool: `claude -p "Test" --tools Bash -y`

**During experiment:**
- Monitor via `tail -f master.log`
- Check `statistics_live.json` for interim results
- Don't restart unless truly stuck (wait for 600s timeout)

**After completion:**
- Run `analyze_statistical_results.py` immediately
- Review all tables and figures
- Validate against expected results (see above)

---

**Good luck with the overnight run! 🚀**

*Estimated completion time: Current time + 19 hours*
