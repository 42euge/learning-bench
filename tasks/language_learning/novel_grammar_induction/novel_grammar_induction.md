# Novel Grammar Induction

**Sub-ability:** Language Learning
**Difficulty grid:** 3 complexity × 3 evidence levels × 3 seeds × 4 test items = 108 items

## What it tests

Can the model induce the grammar rules of a completely novel language from example sentences, then judge whether new sentences are grammatical? This is the most linguistically grounded task in the benchmark — it tests the fundamental human ability to acquire language structure from exposure.

## Three-phase framework

1. **Pre-test:** The model sees valid sentences in a novel language and must judge whether a test sentence is grammatical (YES/NO). No analysis time.
2. **Study:** The model analyzes the example sentences to identify word classes, word order rules, agreement patterns, and embedding structures. Must verify the grammar against every example.
3. **Post-test:** The model receives its own grammar notes plus the original examples, and must judge the same test sentence.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Complexity** | simple, medium, complex | Simple: DET NOUN VERB, fixed word order, no agreement. Medium: DET NOUN VERB with determiner-noun and determiner-verb agreement. Complex: DET ADJ NOUN VERB DET NOUN with nested structure and cross-element agreement. |
| **Evidence** | 4, 8, 12 examples | Number of valid example sentences. More examples expose more of the grammar. |
| **Seeds** | 0, 1, 2 | Independent vocabulary and rule generations. |

Each seed generates 4 test items: 1 valid sentence + 3 violations (word order, agreement, vocabulary).

## Dataset generation

Languages are procedurally generated with:
- **Vocabulary:** Novel words for determiners, nouns, verbs, adjectives — drawn from phonotactically plausible nonsense
- **Agreement system:** Determiners agree with nouns (and optionally verbs) via class markers
- **Word order:** Fixed constituent order that varies between generated languages
- **Violations:** Test sentences include specific error types — wrong word order, agreement mismatches, or out-of-vocabulary words

## Scoring

- **Metric:** Post-learning accuracy (exact YES/NO match).
- **Extraction:** Finds "yes" or "no" in the response (case-insensitive).
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **Simple/12 examples:** Basic word order with many examples — most models detect violations.
- **Complex/4 examples:** Nested agreement with minimal data. Models must induce cross-element agreement rules from just 4 sentences. This is where models separate: good grammar induction vs. surface-level pattern matching.
- **False positives vs. false negatives:** Some models are biased toward "YES" (accepting everything) or "NO" (rejecting everything). The 1:3 ratio of valid:invalid test items helps expose this.
- **Study quality:** Models that write complete, formal grammar rules (with explicit agreement tables) dramatically outperform those that write vague linguistic descriptions.
