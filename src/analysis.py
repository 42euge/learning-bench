"""Analysis utilities for the Learning Curve Profiler benchmark.

Computes learning curve metrics: AULC, learning rate, saturation point,
asymptotic accuracy, and curve shape classification.
"""

import numpy as np
import pandas as pd

from src.generators import SHOT_COUNTS


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def compute_accuracy_at_k(results_df: pd.DataFrame) -> pd.DataFrame:
    """Compute accuracy at each shot count, grouped by family and difficulty.

    Args:
        results_df: DataFrame with columns [family, difficulty, shot_count, result]
                    where result is bool (True=correct).

    Returns:
        DataFrame with columns [family, difficulty, shot_count, accuracy, n_tasks]
    """
    grouped = results_df.groupby(["family", "difficulty", "shot_count"])
    acc = grouped["result"].agg(["mean", "count"]).reset_index()
    acc.columns = ["family", "difficulty", "shot_count", "accuracy", "n_tasks"]
    return acc


def compute_aulc(accuracy_series: pd.Series, shot_counts: list[int] | None = None) -> float:
    """Compute Area Under Learning Curve using trapezoidal rule on log2(k).

    Uses log2-spaced x-axis since shot counts double (1,2,4,8,...).
    Normalizes to [0, 1] range.

    Args:
        accuracy_series: Series indexed by shot_count with accuracy values.
        shot_counts: The shot counts used (default: SHOT_COUNTS).

    Returns:
        AULC score in [0, 1].
    """
    if shot_counts is None:
        shot_counts = SHOT_COUNTS

    # Sort by shot count
    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    log_k = [np.log2(k) for k in shot_counts]

    # Trapezoidal integration
    area = np.trapezoid(acc_values, log_k)

    # Normalize: max area = 1.0 * (log2(64) - log2(1)) = 6.0
    max_area = 1.0 * (log_k[-1] - log_k[0])
    if max_area == 0:
        return 0.0
    return area / max_area


def compute_learning_rate(accuracy_series: pd.Series, shot_counts: list[int] | None = None) -> list[float]:
    """Compute learning rate as accuracy gain per doubling of examples.

    Returns a list of rates between consecutive shot counts.
    """
    if shot_counts is None:
        shot_counts = SHOT_COUNTS

    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    rates = []
    for i in range(1, len(acc_values)):
        rates.append(acc_values[i] - acc_values[i - 1])
    return rates


def compute_saturation_point(
    accuracy_series: pd.Series,
    shot_counts: list[int] | None = None,
    threshold: float = 0.02,
) -> int | None:
    """Find the first shot count where accuracy gain drops below threshold.

    Returns the shot count, or None if never saturates.
    """
    if shot_counts is None:
        shot_counts = SHOT_COUNTS

    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    for i in range(1, len(acc_values)):
        gain = acc_values[i] - acc_values[i - 1]
        if gain < threshold:
            return shot_counts[i]
    return None


def compute_asymptotic_accuracy(accuracy_series: pd.Series, shot_counts: list[int] | None = None) -> float:
    """Return accuracy at the highest shot count."""
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    return accuracy_series.get(shot_counts[-1], 0.0)


def classify_curve_shape(
    accuracy_series: pd.Series,
    shot_counts: list[int] | None = None,
) -> str:
    """Classify the learning curve shape.

    Categories:
      - "flat": near-zero improvement across all shot counts
      - "linear": roughly constant improvement rate
      - "logarithmic": fast early, tapering late
      - "sigmoid": slow start, rapid middle, tapering end
      - "step": sudden jump at one point
    """
    if shot_counts is None:
        shot_counts = SHOT_COUNTS

    rates = compute_learning_rate(accuracy_series, shot_counts)
    if not rates:
        return "flat"

    total_gain = sum(rates)
    max_rate = max(rates)

    # Flat: total improvement < 5%
    if total_gain < 0.05:
        return "flat"

    # Step: one rate accounts for >70% of total gain
    if max_rate > 0.7 * total_gain:
        return "step"

    # Compare first half vs second half rates
    mid = len(rates) // 2
    first_half = sum(rates[:mid])
    second_half = sum(rates[mid:])

    if first_half < 0.001:
        ratio = float("inf")
    else:
        ratio = second_half / first_half

    # Sigmoid: slow start then acceleration
    if ratio > 2.0:
        return "sigmoid"

    # Logarithmic: fast start then tapering
    if first_half > 1.5 * second_half:
        return "logarithmic"

    # Linear: roughly equal rates
    return "linear"


# ---------------------------------------------------------------------------
# Aggregate analysis
# ---------------------------------------------------------------------------

def compute_all_metrics(results_df: pd.DataFrame) -> pd.DataFrame:
    """Compute all learning curve metrics for each (family, difficulty) condition.

    Args:
        results_df: DataFrame with [family, difficulty, shot_count, result].

    Returns:
        DataFrame with one row per (family, difficulty) with columns:
        [family, difficulty, aulc, learning_rates, saturation_point,
         asymptotic_accuracy, curve_shape, accuracy_by_k]
    """
    acc_df = compute_accuracy_at_k(results_df)

    rows = []
    for (family, difficulty), group in acc_df.groupby(["family", "difficulty"]):
        acc_series = group.set_index("shot_count")["accuracy"]

        aulc = compute_aulc(acc_series)
        rates = compute_learning_rate(acc_series)
        sat = compute_saturation_point(acc_series)
        asymp = compute_asymptotic_accuracy(acc_series)
        shape = classify_curve_shape(acc_series)
        acc_by_k = {int(k): round(float(v), 4) for k, v in acc_series.items()}

        rows.append({
            "family": family,
            "difficulty": difficulty,
            "aulc": round(aulc, 4),
            "learning_rates": [round(r, 4) for r in rates],
            "saturation_point": sat,
            "asymptotic_accuracy": round(asymp, 4),
            "curve_shape": shape,
            "accuracy_by_k": acc_by_k,
        })

    return pd.DataFrame(rows)


def compute_overall_aulc(results_df: pd.DataFrame) -> float:
    """Compute the overall AULC across all conditions (the primary benchmark score)."""
    acc_df = compute_accuracy_at_k(results_df)
    overall_acc = acc_df.groupby("shot_count")["accuracy"].mean()
    return compute_aulc(overall_acc)


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_learning_curves(
    results_df: pd.DataFrame,
    output_path: str | None = None,
    title: str = "Learning Curves",
):
    """Plot learning curves for each (family, difficulty) condition.

    Returns the matplotlib figure.
    """
    import matplotlib.pyplot as plt

    acc_df = compute_accuracy_at_k(results_df)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    families = sorted(acc_df["family"].unique())
    colors = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}

    for ax, family in zip(axes, families):
        for difficulty in ["easy", "medium", "hard"]:
            subset = acc_df[
                (acc_df["family"] == family) & (acc_df["difficulty"] == difficulty)
            ].sort_values("shot_count")
            if subset.empty:
                continue
            ax.plot(
                subset["shot_count"],
                subset["accuracy"],
                marker="o",
                label=difficulty,
                color=colors[difficulty],
                linewidth=2,
            )

        ax.set_xscale("log", base=2)
        ax.set_xlabel("Number of examples (k)")
        ax.set_title(family.replace("_", " ").title())
        ax.set_ylim(-0.05, 1.05)
        ax.legend()
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Accuracy")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


if __name__ == "__main__":
    # Demo with synthetic results
    import random

    rng = random.Random(42)
    rows = []
    for family in ["string_rewriting", "modular_arithmetic", "artificial_grammar"]:
        for difficulty in ["easy", "medium", "hard"]:
            base = {"easy": 0.3, "medium": 0.15, "hard": 0.05}[difficulty]
            rate = {"easy": 0.12, "medium": 0.08, "hard": 0.04}[difficulty]
            for k in SHOT_COUNTS:
                acc = min(1.0, base + rate * np.log2(k))
                for _ in range(30):
                    rows.append({
                        "family": family,
                        "difficulty": difficulty,
                        "shot_count": k,
                        "result": rng.random() < acc,
                    })

    df = pd.DataFrame(rows)
    metrics = compute_all_metrics(df)
    print(metrics.to_string(index=False))
    print(f"\nOverall AULC: {compute_overall_aulc(df):.4f}")
