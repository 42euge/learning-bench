# Belief Revision

**Sub-ability:** Reinforcement Learning (evidence integration)
**Difficulty grid:** 3 complexity × 3 contradiction strength × 3 seeds = 27 items

## What it tests

Can the model update its answer when presented with new evidence that contradicts or modifies initial evidence? This tests belief revision — the ability to overcome anchoring bias and integrate corrections, a core component of learning from feedback.

## Three-phase framework

1. **Pre-test:** The model sees all evidence (initial + correction) at once and must give the correct answer considering everything. No analysis time.
2. **Study:** The model explicitly analyzes what changed — what the initial evidence suggested, what the new evidence changes, and how it affects the conclusion.
3. **Post-test:** The model receives its own analysis plus all evidence and must answer again.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Complexity** | simple, chain, nested | Simple: numeric constraints with corrections. Chain: causal chains (A→B→C) where an intermediate link changes. Nested: if-then rules where an override at one level cascades through nested conditions. |
| **Contradiction** | weak, moderate, strong | Weak: minor addendum that adjusts details. Moderate: correction to a specific fact. Strong: complete override that reverses the conclusion. |
| **Seeds** | 0, 1, 2 | Independent random generations. |

## Dataset generation

Evidence scenarios are generated with an initial evidence block and an update/correction block. The initial evidence leads to one answer (`old_answer`), but the correction changes the correct answer (`expected`). The material presents both blocks together, testing whether the model properly integrates the update rather than anchoring on the initial evidence.

**Example scenario types:**
- Simple: "The total is 15" → "CORRECTION: The total is actually 12"
- Chain: "A causes B, B causes C" → "UPDATE: A no longer causes B"
- Nested: "IF condition1 THEN X, ELSE Y" → "CORRECTION: condition1 is false"

## Scoring

- **Metric:** Post-learning accuracy (exact answer match, case-insensitive).
- **Extraction:** Last short line (≤30 chars) from the response, lowercased and stripped.
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **Simple/weak:** Most models handle basic corrections — easy baseline.
- **Nested/strong:** Complete overrides in nested rule systems require tracking cascading changes through multiple levels. Many models anchor on the initial evidence and fail to propagate the override.
- **Pre vs. post insight:** The pre-test already shows all evidence. Models that fail pre but succeed post demonstrate that explicit analysis (study phase) helps overcome anchoring. Models that fail both reveal a fundamental limitation in evidence integration.
