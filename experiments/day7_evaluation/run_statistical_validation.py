#!/usr/bin/env python3
"""
Statistical Validation Experiment - 90 Runs

Provides rigorous statistical validation of DAG scheduling performance:
- 3 task groups (Linear, Fan-out, Mixed)
- 30 runs per group
- 2 modes per run (Sequential + Hybrid)
- Total: 90 runs, 180 group executions

This enables:
- Mean and standard deviation calculation
- 95% confidence intervals
- Paired t-tests for statistical significance
- Publication-quality results with proper statistical rigor

Estimated runtime: ~19 hours (overnight run)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime
import gc

# Import from existing evaluation script
from run_end_to_end_test import (
    EndToEndEvaluator,
    load_agentbench_tasks,
    convert_agentbench_to_tasks
)

# Configuration
SELECTED_GROUPS = [
    "os_user_analysis",      # 3 tasks, Linear chain, 1.57× speedup
    "web_scraping_fanout",   # 12 tasks, Fan-out, 1.31× speedup
    "data_pipeline_mixed"    # 16 tasks, Mixed DAG, 1.32× speedup
]

N_RUNS_PER_GROUP = 30
TOTAL_RUNS = len(SELECTED_GROUPS) * N_RUNS_PER_GROUP  # 90
PAUSE_BETWEEN_RUNS = 5  # seconds (prevent overheating)

# Output directory
OUTPUT_DIR = project_root / "results" / "statistical_validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "master.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_completed_runs() -> set:
    """
    Check which runs have already been completed (crash recovery)

    Returns:
        Set of completed run IDs (e.g., {"run_001_os_user_analysis", ...})
    """
    completed = set()
    raw_runs_dir = OUTPUT_DIR / "raw_runs"

    if not raw_runs_dir.exists():
        return completed

    for file in raw_runs_dir.glob("*.json"):
        # Extract run ID from filename (e.g., "run_001_os_user_analysis.json")
        run_id = file.stem
        completed.add(run_id)

    return completed


def save_incremental_result(result: Dict[str, Any]):
    """
    Save individual run result immediately (crash recovery)

    Args:
        result: Run result dictionary with all metrics
    """
    raw_runs_dir = OUTPUT_DIR / "raw_runs"
    raw_runs_dir.mkdir(parents=True, exist_ok=True)

    filename = raw_runs_dir / f"{result['run_id']}.json"

    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"✓ Saved: {filename.name}")


def append_to_csv(result: Dict[str, Any]):
    """
    Append run result to aggregated CSV file

    Args:
        result: Run result dictionary
    """
    csv_file = OUTPUT_DIR / "aggregated_data.csv"

    # Create CSV with headers if it doesn't exist
    if not csv_file.exists():
        with open(csv_file, 'w') as f:
            headers = [
                "run_id", "group_id", "run_number",
                "seq_time_s", "seq_completed", "seq_failed", "seq_success_rate",
                "hybrid_time_s", "hybrid_completed", "hybrid_failed",
                "hybrid_success_rate", "hybrid_batches",
                "speedup", "timestamp"
            ]
            f.write(",".join(headers) + "\n")

    # Append data row
    with open(csv_file, 'a') as f:
        row = [
            result['run_id'],
            result['group_id'],
            str(result['run_number']),
            f"{result['sequential']['total_time']:.2f}",
            str(result['sequential']['completed']),
            str(result['sequential']['failed']),
            f"{result['sequential']['success_rate']:.1f}",
            f"{result['hybrid']['total_time']:.2f}",
            str(result['hybrid']['completed']),
            str(result['hybrid']['failed']),
            f"{result['hybrid']['success_rate']:.1f}",
            str(result['hybrid'].get('batch_count', 0)),
            f"{result['speedup']:.4f}",
            result['timestamp_start']
        ]
        f.write(",".join(row) + "\n")


def update_live_statistics():
    """
    Update real-time statistics summary (for monitoring)

    Reads all completed runs and calculates current statistics
    """
    raw_runs_dir = OUTPUT_DIR / "raw_runs"

    if not raw_runs_dir.exists():
        return

    # Group results by group_id
    results_by_group = {group: [] for group in SELECTED_GROUPS}

    for file in raw_runs_dir.glob("*.json"):
        with open(file, 'r') as f:
            result = json.load(f)

        group_id = result['group_id']
        if group_id in results_by_group:
            results_by_group[group_id].append(result)

    # Calculate statistics for each group
    stats = {}
    for group_id, results in results_by_group.items():
        if not results:
            stats[group_id] = {"n_runs": 0}
            continue

        seq_times = [r['sequential']['total_time'] for r in results]
        hyb_times = [r['hybrid']['total_time'] for r in results]
        speedups = [r['speedup'] for r in results]

        import numpy as np

        stats[group_id] = {
            "n_runs": len(results),
            "sequential": {
                "mean": float(np.mean(seq_times)),
                "std": float(np.std(seq_times, ddof=1)) if len(seq_times) > 1 else 0.0,
                "min": float(np.min(seq_times)),
                "max": float(np.max(seq_times))
            },
            "hybrid": {
                "mean": float(np.mean(hyb_times)),
                "std": float(np.std(hyb_times, ddof=1)) if len(hyb_times) > 1 else 0.0,
                "min": float(np.min(hyb_times)),
                "max": float(np.max(hyb_times))
            },
            "speedup": {
                "mean": float(np.mean(speedups)),
                "std": float(np.std(speedups, ddof=1)) if len(speedups) > 1 else 0.0,
                "min": float(np.min(speedups)),
                "max": float(np.max(speedups))
            }
        }

    # Save live statistics
    stats_file = OUTPUT_DIR / "statistics_live.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)


async def run_single_trial(
    evaluator: EndToEndEvaluator,
    group_id: str,
    run_number: int,
    total_progress: int
) -> Dict[str, Any]:
    """
    Execute one complete trial (sequential + hybrid) for a task group

    Args:
        evaluator: Initialized EndToEndEvaluator instance
        group_id: AgentBench group ID to test
        run_number: Run number (1-30)
        total_progress: Overall progress counter (1-90)

    Returns:
        Complete result dictionary with metrics for both modes
    """
    run_id = f"run_{run_number:03d}_{group_id}"

    logger.info(f"\n{'='*70}")
    logger.info(f"[{total_progress}/{TOTAL_RUNS}] Starting: {run_id}")
    logger.info(f"{'='*70}")

    timestamp_start = datetime.now().isoformat()

    # Load task group
    all_groups = load_agentbench_tasks()
    group = next((g for g in all_groups if g["group_id"] == group_id), None)

    if not group:
        raise ValueError(f"Group '{group_id}' not found in AgentBench")

    tasks = convert_agentbench_to_tasks(group)
    logger.info(f"Loaded {len(tasks)} tasks from group '{group_id}'")

    # Execute Sequential Mode
    logger.info("\n▶️  Running SEQUENTIAL mode...")
    try:
        seq_result = await evaluator.run_sequential(tasks.copy())
        logger.info(f"✓ Sequential: {seq_result['total_time']:.2f}s, "
                   f"success rate: {seq_result['success_rate']:.1f}%")
    except Exception as e:
        logger.error(f"✗ Sequential mode failed: {e}")
        seq_result = {
            "total_time": 0.0,
            "completed": 0,
            "failed": len(tasks),
            "success_rate": 0.0,
            "error": str(e)
        }

    # Pause before hybrid mode
    await asyncio.sleep(2)

    # Execute Hybrid Mode
    logger.info("\n▶️  Running HYBRID mode...")
    try:
        hyb_result = await evaluator.run_hybrid(tasks.copy())
        logger.info(f"✓ Hybrid: {hyb_result['total_time']:.2f}s, "
                   f"success rate: {hyb_result['success_rate']:.1f}%, "
                   f"batches: {hyb_result.get('batch_count', 0)}")
    except Exception as e:
        logger.error(f"✗ Hybrid mode failed: {e}")
        hyb_result = {
            "total_time": 0.0,
            "completed": 0,
            "failed": len(tasks),
            "success_rate": 0.0,
            "batch_count": 0,
            "error": str(e)
        }

    # Calculate speedup
    if seq_result['total_time'] > 0 and hyb_result['total_time'] > 0:
        speedup = seq_result['total_time'] / hyb_result['total_time']
    else:
        speedup = 0.0

    timestamp_end = datetime.now().isoformat()

    # Build result dictionary
    result = {
        "run_id": run_id,
        "group_id": group_id,
        "run_number": run_number,
        "total_progress": total_progress,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "task_count": len(tasks),
        "sequential": seq_result,
        "hybrid": hyb_result,
        "speedup": speedup
    }

    logger.info(f"\n📊 Run {run_number} Results:")
    logger.info(f"  Sequential: {seq_result['total_time']:.2f}s")
    logger.info(f"  Hybrid: {hyb_result['total_time']:.2f}s")
    logger.info(f"  Speedup: {speedup:.4f}×")

    return result


async def cleanup_after_run(evaluator: EndToEndEvaluator):
    """
    Cleanup resources after each run to prevent memory leaks

    Args:
        evaluator: EndToEndEvaluator instance
    """
    # Force garbage collection
    gc.collect()

    # Note: We don't reinitialize the executor between runs
    # to avoid unnecessary overhead. The executor should handle
    # cleanup internally.


async def main():
    """
    Main experiment loop - 90 runs total

    Execution plan:
    1. Initialize evaluator (once)
    2. For each task group (3 groups):
       a. Run 30 trials
       b. Save each trial immediately
       c. Update live statistics
    3. Generate final summary
    """
    logger.info("\n" + "="*70)
    logger.info("🔬 STATISTICAL VALIDATION EXPERIMENT - 90 RUNS")
    logger.info("="*70)
    logger.info(f"\nConfiguration:")
    logger.info(f"  Task groups: {len(SELECTED_GROUPS)}")
    logger.info(f"  Runs per group: {N_RUNS_PER_GROUP}")
    logger.info(f"  Total runs: {TOTAL_RUNS}")
    logger.info(f"  Estimated time: ~19 hours")
    logger.info(f"\nSelected groups:")
    for group in SELECTED_GROUPS:
        logger.info(f"  - {group}")
    logger.info(f"\nOutput directory: {OUTPUT_DIR}")
    logger.info("")

    # Check for previous runs (crash recovery)
    completed_runs = get_completed_runs()
    if completed_runs:
        logger.info(f"📂 Found {len(completed_runs)} completed runs (resuming)")
        logger.info(f"   Will skip these runs to avoid duplicates\n")

    # Initialize evaluator
    logger.info("🔧 Initializing evaluator...")
    evaluator = EndToEndEvaluator()
    await evaluator.cli_executor.initialize()
    logger.info("✅ Evaluator ready\n")

    # Track overall progress
    total_progress = 0
    experiment_start = time.time()

    # Main experiment loop
    for group_id in SELECTED_GROUPS:
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 GROUP: {group_id}")
        logger.info(f"   Running {N_RUNS_PER_GROUP} trials")
        logger.info(f"{'='*70}\n")

        group_start = time.time()

        for run_num in range(1, N_RUNS_PER_GROUP + 1):
            total_progress += 1
            run_id = f"run_{run_num:03d}_{group_id}"

            # Skip if already completed (crash recovery)
            if run_id in completed_runs:
                logger.info(f"⏭️  [{total_progress}/{TOTAL_RUNS}] Skipping {run_id} (already completed)")
                continue

            try:
                # Run trial
                result = await run_single_trial(
                    evaluator=evaluator,
                    group_id=group_id,
                    run_number=run_num,
                    total_progress=total_progress
                )

                # Save immediately (crash recovery)
                save_incremental_result(result)
                append_to_csv(result)

                # Update live statistics
                update_live_statistics()

                # Cleanup
                await cleanup_after_run(evaluator)

                logger.info(f"✅ [{total_progress}/{TOTAL_RUNS}] Completed: {run_id}\n")

                # Pause between runs (prevent overheating)
                if run_num < N_RUNS_PER_GROUP:
                    logger.info(f"⏸️  Pausing {PAUSE_BETWEEN_RUNS}s before next run...\n")
                    await asyncio.sleep(PAUSE_BETWEEN_RUNS)

            except Exception as e:
                logger.error(f"❌ [{total_progress}/{TOTAL_RUNS}] Failed: {run_id}")
                logger.error(f"   Error: {e}")
                logger.error(f"   Continuing with next run...\n")

                # Log error to separate file
                error_log = OUTPUT_DIR / "errors.log"
                with open(error_log, 'a') as f:
                    f.write(f"[{datetime.now().isoformat()}] {run_id}: {e}\n")

        group_time = time.time() - group_start
        logger.info(f"\n✅ Group '{group_id}' completed in {group_time/60:.1f} minutes\n")

    # Experiment complete
    total_time = time.time() - experiment_start

    logger.info(f"\n{'='*70}")
    logger.info("🎉 EXPERIMENT COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"\nStatistics:")
    logger.info(f"  Total runs: {TOTAL_RUNS}")
    logger.info(f"  Completed: {len(get_completed_runs())}")
    logger.info(f"  Total time: {total_time/3600:.2f} hours")
    logger.info(f"\nResults saved to: {OUTPUT_DIR}")
    logger.info(f"  Raw runs: {OUTPUT_DIR / 'raw_runs'}")
    logger.info(f"  Aggregated CSV: {OUTPUT_DIR / 'aggregated_data.csv'}")
    logger.info(f"  Live statistics: {OUTPUT_DIR / 'statistics_live.json'}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Run statistical analysis: python analyze_statistical_results.py")
    logger.info(f"  2. Generate publication tables and figures")
    logger.info(f"  3. Include results in paper Section 8\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Experiment interrupted by user")
        logger.info("   Progress has been saved. Resume by running this script again.")
        logger.info("   Completed runs will be skipped automatically.\n")
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        logger.error("   Check master.log and errors.log for details\n")
        raise
