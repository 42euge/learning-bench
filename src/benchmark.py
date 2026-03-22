"""Learning Curve Profiler benchmark using kaggle-benchmarks SDK.

Measures the shape of a model's in-context learning curve across
procedurally generated rule-learning tasks at varying shot counts.
"""

import json
import re
from pathlib import Path

import kaggle_benchmarks as kbench
import pandas as pd

from src.generators import GENERATORS, SHOT_COUNTS, DIFFICULTIES, TASK_FAMILIES


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@kbench.task(
    name="Learning Curve Profiler",
    description=(
        "Measures how model accuracy improves as more in-context examples are "
        "provided, across three procedurally generated task families "
        "(string rewriting, modular arithmetic, artificial grammar) "
        "at three difficulty tiers."
    ),
)
def learning_curve_profiler(
    llm,
    prompt: str,
    expected: str,
    family: str,
    difficulty: str,
    shot_count: int,
    seed: int,
) -> bool:
    """Evaluate a single task instance.

    Returns True if the model's response matches the expected answer.
    """
    response = llm.prompt(prompt)
    response_clean = _extract_answer(response, family)
    return _check_answer(response_clean, expected, family)


# ---------------------------------------------------------------------------
# Answer extraction and checking
# ---------------------------------------------------------------------------

def _extract_answer(response: str, family: str) -> str:
    """Extract the answer from the model's response."""
    text = response.strip()

    if family == "string_rewriting":
        # Look for the last line or the text after "Output:"
        match = re.search(r"(?:Output:\s*)?([a-z]+)\s*$", text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        # Fallback: take last word-like token
        tokens = re.findall(r"[a-z]+", text.lower())
        return tokens[-1] if tokens else text

    elif family == "modular_arithmetic":
        # Look for a number, preferring the last one or one after "="
        match = re.search(r"=\s*(\d+)", text)
        if match:
            return match.group(1)
        numbers = re.findall(r"\d+", text)
        return numbers[-1] if numbers else text

    elif family == "artificial_grammar":
        # Look for "valid" or "invalid"
        text_lower = text.lower()
        if "invalid" in text_lower:
            return "invalid"
        if "valid" in text_lower:
            return "valid"
        return text

    return text


def _check_answer(response: str, expected: str, family: str) -> bool:
    """Check if the extracted response matches the expected answer."""
    if family == "modular_arithmetic":
        # Numeric comparison
        try:
            return int(response) == int(expected)
        except ValueError:
            return response.strip() == expected.strip()
    else:
        return response.strip().lower() == expected.strip().lower()


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: Path | None = None) -> pd.DataFrame:
    """Load the benchmark dataset as a DataFrame."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "benchmark_dataset.json"
    with open(path) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def generate_dataset_inline(
    seeds_per_condition: int = 30,
    shot_counts: list[int] | None = None,
) -> pd.DataFrame:
    """Generate dataset on-the-fly without reading from disk."""
    if shot_counts is None:
        shot_counts = SHOT_COUNTS

    rows = []
    task_id = 0
    for family in TASK_FAMILIES:
        gen = GENERATORS[family]()
        for difficulty in DIFFICULTIES:
            for seed in range(seeds_per_condition):
                for sc in shot_counts:
                    result = gen.generate(seed=seed, difficulty=difficulty, n_examples=sc)
                    rows.append({
                        "task_id": task_id,
                        "family": family,
                        "difficulty": difficulty,
                        "shot_count": sc,
                        "seed": seed,
                        "prompt": result["prompt"],
                        "expected": result["expected"],
                    })
                    task_id += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Evaluation entry point
# ---------------------------------------------------------------------------

def run_evaluation(
    dataset: pd.DataFrame | None = None,
    n_jobs: int = 1,
    timeout: float = 60.0,
):
    """Run the benchmark evaluation across the full dataset."""
    if dataset is None:
        dataset = generate_dataset_inline()

    results = learning_curve_profiler.evaluate(
        evaluation_data=dataset.rename(columns={"task_id": "_id"}).set_index("_id"),
        n_jobs=n_jobs,
        timeout=timeout,
    )
    return results


if __name__ == "__main__":
    # Quick smoke test with a tiny subset
    df = generate_dataset_inline(seeds_per_condition=2, shot_counts=[2, 4])
    print(f"Generated {len(df)} tasks for smoke test")
    print(df[["family", "difficulty", "shot_count", "expected"]].head(20))
