"""Tests for procedural task generators."""

import random

from src.generators import (
    StringRewritingGenerator,
    ModularArithmeticGenerator,
    ArtificialGrammarGenerator,
    SHOT_COUNTS,
    DIFFICULTIES,
    TASK_FAMILIES,
    GENERATORS,
)
from src.generators.string_rewriting import _apply_rule
from src.generators.artificial_grammar import _enumerate_valid
from src.benchmark import _extract_answer, _check_answer


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_determinism():
    """Same seed always produces same output."""
    for name, Gen in GENERATORS.items():
        g = Gen()
        for diff in DIFFICULTIES:
            r1 = g.generate(seed=42, difficulty=diff)
            r2 = g.generate(seed=42, difficulty=diff)
            assert r1["expected"] == r2["expected"], f"{name}/{diff}: expected mismatch"
            assert r1["prompt"] == r2["prompt"], f"{name}/{diff}: prompt mismatch"


def test_different_seeds_differ():
    """Different seeds produce different rules."""
    for name, Gen in GENERATORS.items():
        g = Gen()
        r1 = g.generate(seed=0, difficulty="easy")
        r2 = g.generate(seed=1, difficulty="easy")
        # At minimum, the rule should differ (prompts may still look similar)
        assert r1["expected"] != r2["expected"] or r1["prompt"] != r2["prompt"], \
            f"{name}: seeds 0 and 1 produced identical output"


# ---------------------------------------------------------------------------
# String rewriting
# ---------------------------------------------------------------------------

def test_string_rewriting_answer_correctness():
    """All generated answers match rule application."""
    gen = StringRewritingGenerator()
    for diff in DIFFICULTIES:
        for seed in range(20):
            result = gen.generate(seed=seed, difficulty=diff)
            rule = gen.generate_rule(seed, diff)
            expected = _apply_rule(rule, result["query_input"])
            assert expected == result["expected"], \
                f"seed={seed}, diff={diff}: {expected} != {result['expected']}"


def test_string_rewriting_examples_show_rule():
    """Every example string contains at least one source character."""
    gen = StringRewritingGenerator()
    for diff in DIFFICULTIES:
        for seed in range(20):
            rule = gen.generate_rule(seed, diff)
            examples = gen.generate_examples(rule, 8, seed + 1000)
            for inp, out in examples:
                has_source = any(c in inp for c in rule.substitutions)
                assert has_source, f"No source char in '{inp}' for {rule.substitutions}"


def test_string_rewriting_difficulty_scaling():
    """Higher difficulty means more substitution rules."""
    gen = StringRewritingGenerator()
    for seed in range(10):
        easy = gen.generate_rule(seed, "easy")
        medium = gen.generate_rule(seed, "medium")
        hard = gen.generate_rule(seed, "hard")
        assert len(easy.substitutions) == 1
        assert len(medium.substitutions) == 2
        assert len(hard.substitutions) == 3
        assert hard.transform is not None


# ---------------------------------------------------------------------------
# Modular arithmetic
# ---------------------------------------------------------------------------

def test_modular_arithmetic_answer_correctness():
    """All generated answers are correct."""
    gen = ModularArithmeticGenerator()
    for diff in DIFFICULTIES:
        for seed in range(20):
            result = gen.generate(seed=seed, difficulty=diff)
            rule = gen.generate_rule(seed, diff)
            expr, answer = gen.generate_query(rule, seed + 2000)
            assert str(answer) == result["expected"], \
                f"seed={seed}, diff={diff}: {answer} != {result['expected']}"


def test_modular_arithmetic_difficulty_scaling():
    """Higher difficulty means more operators."""
    gen = ModularArithmeticGenerator()
    for seed in range(10):
        easy = gen.generate_rule(seed, "easy")
        medium = gen.generate_rule(seed, "medium")
        hard = gen.generate_rule(seed, "hard")
        assert len(easy.operators) == 1
        assert len(medium.operators) == 2
        assert len(hard.operators) == 3
        assert hard.precedence is not None


# ---------------------------------------------------------------------------
# Artificial grammar
# ---------------------------------------------------------------------------

def test_artificial_grammar_answer_correctness():
    """All generated labels match grammar membership."""
    gen = ArtificialGrammarGenerator()
    for diff in DIFFICULTIES:
        for seed in range(20):
            result = gen.generate(seed=seed, difficulty=diff)
            rule = gen.generate_rule(seed, diff)
            valid_set = _enumerate_valid(rule)
            expected_label = "valid" if result["query_string"] in valid_set else "invalid"
            assert expected_label == result["expected"], \
                f"seed={seed}, diff={diff}: {expected_label} != {result['expected']}"


def test_artificial_grammar_examples_balanced():
    """Examples contain both valid and invalid strings."""
    gen = ArtificialGrammarGenerator()
    for seed in range(10):
        rule = gen.generate_rule(seed, "easy")
        examples = gen.generate_examples(rule, 8, seed + 1000)
        labels = [label for _, label in examples]
        assert "valid" in labels, f"seed={seed}: no valid examples"
        assert "invalid" in labels, f"seed={seed}: no invalid examples"


# ---------------------------------------------------------------------------
# Answer extraction
# ---------------------------------------------------------------------------

def test_extract_answer_string_rewriting():
    assert _extract_answer("abc", "string_rewriting") == "abc"
    assert _extract_answer("Output: xyz", "string_rewriting") == "xyz"
    assert _extract_answer("I think the answer is\nOutput: abc", "string_rewriting") == "abc"


def test_extract_answer_modular_arithmetic():
    assert _extract_answer("5", "modular_arithmetic") == "5"
    assert _extract_answer("= 12", "modular_arithmetic") == "12"
    assert _extract_answer("The answer is 7.", "modular_arithmetic") == "7"


def test_extract_answer_artificial_grammar():
    assert _extract_answer("valid", "artificial_grammar") == "valid"
    assert _extract_answer("invalid", "artificial_grammar") == "invalid"
    assert _extract_answer("The string is invalid.", "artificial_grammar") == "invalid"
    # "invalid" contains "valid" but should match "invalid" first
    assert _extract_answer("invalid", "artificial_grammar") == "invalid"


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

def test_dataset_size():
    """Dataset has expected number of tasks."""
    from src.dataset import generate_dataset
    dataset = generate_dataset(seeds_per_condition=2, shot_counts=[2, 4])
    expected = 3 * 3 * 2 * 2  # families × difficulties × seeds × shot_counts
    assert len(dataset) == expected, f"Expected {expected}, got {len(dataset)}"


def test_dataset_unique_ids():
    """All task IDs are unique."""
    from src.dataset import generate_dataset
    dataset = generate_dataset(seeds_per_condition=2, shot_counts=[2, 4])
    ids = [d["task_id"] for d in dataset]
    assert len(ids) == len(set(ids)), "Duplicate task IDs found"


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def test_analysis_metrics():
    """Analysis computes valid metrics from synthetic data."""
    import pandas as pd
    from src.analysis import compute_all_metrics, compute_overall_aulc

    rng = random.Random(42)
    rows = []
    for family in TASK_FAMILIES:
        for difficulty in DIFFICULTIES:
            for k in SHOT_COUNTS:
                for _ in range(10):
                    rows.append({
                        "family": family,
                        "difficulty": difficulty,
                        "shot_count": k,
                        "result": rng.random() < 0.5,
                    })

    df = pd.DataFrame(rows)
    metrics = compute_all_metrics(df)
    assert len(metrics) == 9  # 3 families × 3 difficulties
    assert all(0 <= m <= 1 for m in metrics["aulc"])
    assert all(0 <= m <= 1 for m in metrics["asymptotic_accuracy"])

    aulc = compute_overall_aulc(df)
    assert 0 <= aulc <= 1


if __name__ == "__main__":
    import sys
    # Run all test functions
    passed = 0
    failed = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
