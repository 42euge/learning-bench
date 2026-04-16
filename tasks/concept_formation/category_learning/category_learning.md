# Category Learning

**Sub-ability:** Concept Formation
**Difficulty grid:** 3 complexity × 3 evidence × 3 seeds = 27 items

## What it tests

Can the model discover a hidden classification rule from labeled examples and apply it to a novel object? This isolates concept formation — the ability to identify which features are relevant for categorization and form an explicit rule.

## Three-phase framework

1. **Pre-test:** The model sees objects (described by size, color, pattern, shape) labeled with categories (A–D), and must classify a new unlabeled object. No analysis time.
2. **Study:** The model analyzes the examples to identify which features determine category membership, writes the exact classification rule, and verifies it against every example.
3. **Post-test:** The model receives its own rule analysis plus the original examples, and must classify the same test object.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Complexity** | single, two_feat, conditional | Single: one feature determines category (e.g., shape ∈ {circle, square} → A). Two-feature: conjunction of two features (e.g., large AND red → B). Conditional: if-then chains with overrides (e.g., IF striped THEN C, ELSE IF large THEN A). |
| **Evidence** | few (4), mid (6), many (10) | Number of labeled examples. Fewer examples = harder to disambiguate which features matter. |
| **Seeds** | 0, 1, 2 | Independent random generations. |

## Dataset generation

Objects are described by four features (size, color, pattern, shape) drawn from fixed pools. Classification rules are generated at three complexity levels. Training examples are sampled to be consistent with the rule, and the test object is guaranteed to be unambiguous under the true rule. Feature values in examples are varied to avoid spurious correlations.

## Scoring

- **Metric:** Post-learning accuracy (exact category letter match).
- **Extraction:** Last category letter (A–D) found in the response, checked via reverse line scan.
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **Single/many:** Easy baseline — one feature, lots of examples, most models succeed.
- **Conditional/few:** Requires identifying multi-step rules from minimal data. Models must handle "ELSE IF" logic rather than simple feature matching.
- **Feature distraction:** All four features are always present, but only 1–2 are actually relevant. Models that latch onto irrelevant features (confirmation bias) will fail.
