"""Dataset generator for the Learning Curve Profiler benchmark.

Generates all task instances across (family × difficulty × shot_count × seed)
and outputs them as a JSON file ready for benchmark evaluation.
"""

import json
import os
from pathlib import Path

from src.generators import (
    DIFFICULTIES,
    GENERATORS,
    SHOT_COUNTS,
    TASK_FAMILIES,
)

# Number of unique rule seeds per (family, difficulty) pair.
# Each seed generates a different rule; each rule is then prompted at each shot count.
SEEDS_PER_CONDITION = 30

# Output path
DATA_DIR = Path(__file__).parent.parent / "data"


def generate_dataset(
    seeds_per_condition: int = SEEDS_PER_CONDITION,
    shot_counts: list[int] = SHOT_COUNTS,
    output_path: Path | None = None,
) -> list[dict]:
    """Generate the full benchmark dataset.

    Returns a list of task instances, each a dict with:
      - task_id: unique identifier
      - family: task family name
      - difficulty: easy/medium/hard
      - shot_count: number of examples shown
      - seed: random seed for rule generation
      - prompt: the full prompt string
      - expected: the correct answer
      - metadata: rule details for debugging
    """
    dataset = []
    task_id = 0

    for family in TASK_FAMILIES:
        gen = GENERATORS[family]()
        for difficulty in DIFFICULTIES:
            for seed in range(seeds_per_condition):
                for shot_count in shot_counts:
                    result = gen.generate(
                        seed=seed,
                        difficulty=difficulty,
                        n_examples=shot_count,
                    )
                    task_instance = {
                        "task_id": task_id,
                        "family": family,
                        "difficulty": difficulty,
                        "shot_count": shot_count,
                        "seed": seed,
                        "prompt": result["prompt"],
                        "expected": result["expected"],
                    }
                    dataset.append(task_instance)
                    task_id += 1

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(dataset, f, indent=2)
        print(f"Generated {len(dataset)} tasks → {output_path}")

    return dataset


def print_stats(dataset: list[dict]) -> None:
    """Print dataset statistics."""
    from collections import Counter

    print(f"\nTotal tasks: {len(dataset)}")
    print(f"\nBy family:")
    for fam, count in sorted(Counter(d["family"] for d in dataset).items()):
        print(f"  {fam}: {count}")
    print(f"\nBy difficulty:")
    for diff, count in sorted(Counter(d["difficulty"] for d in dataset).items()):
        print(f"  {diff}: {count}")
    print(f"\nBy shot count:")
    for sc, count in sorted(Counter(d["shot_count"] for d in dataset).items()):
        print(f"  {sc}: {count}")
    print(f"\nConditions: {len(TASK_FAMILIES)} families × {len(DIFFICULTIES)} difficulties × {len(SHOT_COUNTS)} shot counts = {len(TASK_FAMILIES) * len(DIFFICULTIES) * len(SHOT_COUNTS)}")
    print(f"Seeds per condition: {SEEDS_PER_CONDITION}")


if __name__ == "__main__":
    output = DATA_DIR / "benchmark_dataset.json"
    dataset = generate_dataset(output_path=output)
    print_stats(dataset)
