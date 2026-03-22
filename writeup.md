# Learning Curve Profiler

## Team

[Your name / team here]

## Problem Statement

Current LLM benchmarks measure what models *know* — accuracy at a fixed number of examples (typically zero-shot or 5-shot). But they miss a fundamental question: **how do models *learn*?**

Two models might both score 70% at 5-shot, yet differ dramatically in *how* they got there. One might jump from 20% to 70% between 1 and 2 examples (step-function learner), while another climbs steadily from 40% to 70% across all shot counts (linear learner). These learning dynamics are invisible to single-point measurements.

The **Learning Curve Profiler** measures the *shape* of a model's in-context learning curve — how accuracy changes as more demonstrations are provided — revealing fundamental differences in learning ability that no existing benchmark captures.

## Task & Benchmark Construction

We evaluate models across **three procedurally generated task families**, each at **three difficulty tiers**, measured at **seven shot counts** (1, 2, 4, 8, 16, 32, 64 examples).

### Task Families

**String Rewriting.** Models observe input→output string pairs governed by character substitution rules, then apply the same rule to a new input. Easy tasks use 1 rule (e.g., `a→x`), medium use 2 sequential rules, and hard use 3 rules plus a structural transform (reverse or shift).

**Modular Arithmetic.** Models learn novel operator symbols (⊕, ⊗, etc.) defined as modular arithmetic operations. Easy tasks have 1 operator, medium have 2, and hard have 3 with explicit precedence rules.

**Artificial Grammar Classification.** Models observe strings labeled "valid" or "invalid" according to a hidden context-free grammar, then classify new strings. Easy grammars have no recursion, medium add recursive productions, hard add multiple recursive nonterminals.

### Why These Tasks?

All three families share critical properties: (1) **procedurally generated** from random seeds, making training-data memorization ineffective; (2) **deterministic verification** — correct answers are computed algorithmically; (3) **difficulty scaling** via compositionality, not just problem size.

### Prompt Format

Each task presents k examples in the family's natural format, followed by a query. For example (string rewriting, 2-shot):

```
Here are some examples of a string transformation rule:
Input: rcjmnod → Output: rcjmnad
Input: rzrjuo → Output: rzrjua

Now apply the same rule:
Input: boyvtws → Output:
```

## Dataset

- **1,890 task instances**: 3 families × 3 difficulties × 7 shot counts × 30 seeds
- **Procedurally generated** using Python's `random.Random` with deterministic seeds
- **Verification**: all 1,890 answers independently verified correct via rule application
- **No ambiguity**: every task has exactly one correct answer
- String rewriting inputs are guaranteed to contain at least one character affected by the rule, ensuring every example demonstrates the transformation

## Technical Details

### Primary Metric: AULC (Area Under Learning Curve)

We compute accuracy at each shot count k ∈ {1, 2, 4, 8, 16, 32, 64}, then integrate using the trapezoidal rule over a log₂-spaced x-axis (since shot counts double). The result is normalized to [0, 1], where 1.0 means perfect accuracy at all shot counts.

AULC captures overall learning ability in a single number — analogous to AUC-ROC for classifiers. A model that learns quickly and plateaus high gets a high AULC; one that stays flat gets a low AULC regardless of where.

### Secondary Metrics

- **Learning rate**: accuracy gain per doubling of examples
- **Saturation point**: first k where accuracy gain drops below 2%
- **Asymptotic accuracy**: accuracy at k=64
- **Curve shape**: classified as flat, linear, logarithmic, sigmoid, or step-function

### Answer Extraction

Model responses are parsed with family-specific extractors: last lowercase word for string rewriting, last number (or number after "=") for modular arithmetic, and presence of "valid"/"invalid" keywords for grammar classification. Comparison is case-insensitive for strings and exact for numbers.

## Results, Insights, and Conclusions

[To be filled after model evaluation]

### Expected Discrimination Patterns

Based on the benchmark design, we expect:

| Model class | Expected curve shape | Learning rate | Ceiling |
|---|---|---|---|
| Small models (≤7B) | Linear / flat | Low | Low |
| Large models (70B+) | Logarithmic | High early, tapering | High |
| Reasoning models | Sigmoid | Slow start, then rapid | High |

Easy tasks ensure even small models score above zero; hard tasks with few shots ensure frontier models don't saturate — producing a meaningful performance gradient.

### What This Reveals

The Learning Curve Profiler answers: *"What can this benchmark tell us about model behavior that we could not see before?"*

It reveals the **learning signature** of each model — not just how well it performs, but *how it learns*. This is the difference between knowing a student's test score and understanding how they study.

## Organizational Affiliations

[Your affiliations]

## References & Citations

1. Morris et al. (2024). "Measuring progress toward AGI: A cognitive framework." Google DeepMind.
2. Brown et al. (2020). "Language Models are Few-Shot Learners." NeurIPS.
3. Min et al. (2022). "Rethinking the Role of Demonstrations." EMNLP.
