# Analogy Completion

**Sub-ability:** Associative Learning (relational mapping)
**Difficulty grid:** 3 complexity × 3 evidence × 3 seeds = 27 items

## What it tests

Can the model induce a mathematical transformation rule from input→output examples and apply it to a new input? This tests relational abstraction — going beyond surface pattern matching to discover the underlying function.

## Three-phase framework

1. **Pre-test:** The model sees examples of number tuples being transformed (e.g., `(2,3,5) -> (4,6,10)`) and must apply the same rule to a new input. No analysis time.
2. **Study:** The model analyzes the examples to derive the exact formula for each output position, checking for cross-element interactions and verifying against every example.
3. **Post-test:** The model receives its own analysis notes plus the original examples, and must apply the rule to the same test input.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Complexity** | simple, moderate, complex | Simple: uniform operation (add k, multiply by k, swap positions). Moderate: different operation per position. Complex: cross-element dependencies (e.g., output[0] = input[0] + input[1]). |
| **Evidence** | few (3), mid (5), many (8) | Number of input→output examples provided. More examples = easier to verify hypotheses. |
| **Seeds** | 0, 1, 2 | Independent random generations. |

## Dataset generation

Transformation rules are procedurally generated with controlled complexity. Simple rules apply the same arithmetic to each position. Moderate rules use different ops per position. Complex rules involve pairwise sums/differences with added constants. All rules are deterministic and unambiguous given the examples.

## Scoring

- **Metric:** Post-learning accuracy (exact tuple match).
- **Extraction:** Last `(a, b, c)` pattern found in the response.
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **Simple/many:** Easy ceiling — most models get uniform operations right with 8 examples.
- **Complex/few:** Hard floor — cross-element dependencies with only 3 examples require genuine algebraic reasoning, not pattern guessing.
- **Study quality:** Models that write explicit per-position formulas and verify them perform dramatically better than those that guess-and-check.
