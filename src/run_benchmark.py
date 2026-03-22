"""Run the Learning Curve Profiler benchmark end-to-end.

Usage:
    python -m src.run_benchmark                    # Full run (1890 tasks)
    python -m src.run_benchmark --quick            # Quick test (54 tasks)
    python -m src.run_benchmark --seeds 5          # Custom seed count
    python -m src.run_benchmark --jobs 4           # Parallel execution
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.benchmark import learning_curve_profiler, generate_dataset_inline
from src.analysis import compute_all_metrics, compute_overall_aulc, plot_learning_curves
from src.generators import SHOT_COUNTS


RESULTS_DIR = Path(__file__).parent.parent / "results"


def run(
    seeds_per_condition: int = 30,
    shot_counts: list[int] | None = None,
    n_jobs: int = 1,
    timeout: float = 60.0,
    output_dir: Path | None = None,
):
    """Run the full benchmark pipeline."""
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    if output_dir is None:
        output_dir = RESULTS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate dataset
    print(f"Generating dataset: {seeds_per_condition} seeds × 3 families × 3 difficulties × {len(shot_counts)} shot counts")
    dataset = generate_dataset_inline(seeds_per_condition, shot_counts)
    print(f"Total tasks: {len(dataset)}")

    # 2. Run evaluation
    print(f"\nRunning evaluation (n_jobs={n_jobs}, timeout={timeout}s)...")
    eval_df = dataset.copy()
    eval_df.index.name = "_id"

    results = learning_curve_profiler.evaluate(
        evaluation_data=eval_df,
        n_jobs=n_jobs,
        timeout=timeout,
    )

    # 3. Extract results
    results_df = results.as_dataframe()
    print(f"Completed: {len(results_df)} / {len(dataset)} tasks")

    # Merge back metadata
    merged = dataset.copy()
    merged["result"] = False  # default
    for _, row in results_df.iterrows():
        idx = row.get("id", row.name)
        if idx in merged.index:
            merged.loc[idx, "result"] = bool(row["result"])

    # 4. Compute metrics
    metrics = compute_all_metrics(merged)
    overall_aulc = compute_overall_aulc(merged)

    print(f"\n{'='*60}")
    print(f"OVERALL AULC: {overall_aulc:.4f}")
    print(f"{'='*60}\n")
    print(metrics[["family", "difficulty", "aulc", "asymptotic_accuracy", "curve_shape"]].to_string(index=False))

    # 5. Save results
    merged.to_csv(output_dir / "raw_results.csv", index=False)
    metrics.to_json(output_dir / "metrics.json", orient="records", indent=2)
    with open(output_dir / "summary.json", "w") as f:
        json.dump({"overall_aulc": overall_aulc}, f, indent=2)

    # 6. Plot
    try:
        fig = plot_learning_curves(merged, output_path=str(output_dir / "learning_curves.png"))
        print(f"\nPlot saved to {output_dir / 'learning_curves.png'}")
    except Exception as e:
        print(f"Plotting skipped: {e}")

    return merged, metrics, overall_aulc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Learning Curve Profiler benchmark")
    parser.add_argument("--seeds", type=int, default=30, help="Seeds per condition")
    parser.add_argument("--quick", action="store_true", help="Quick test with 3 seeds, 3 shot counts")
    parser.add_argument("--jobs", type=int, default=1, help="Parallel jobs")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout per task (seconds)")
    args = parser.parse_args()

    if args.quick:
        run(seeds_per_condition=3, shot_counts=[2, 8, 32], n_jobs=args.jobs, timeout=args.timeout)
    else:
        run(seeds_per_condition=args.seeds, n_jobs=args.jobs, timeout=args.timeout)
