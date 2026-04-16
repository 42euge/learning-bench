# Paired Associate Learning

**Sub-ability:** Associative Learning
**Difficulty grid:** 3 complexity × 3 evidence × 3 seeds = 27 items

## What it tests

Can the model memorize and recall arbitrary word-meaning pairs from a novel vocabulary? This isolates rote associative binding — the ability to form new arbitrary mappings during a conversation — rather than relying on prior knowledge.

## Three-phase framework

1. **Pre-test:** The model sees a vocabulary list of nonsense words mapped to English meanings, and is asked what a held-out word means. No study time.
2. **Study:** The model is given the same vocabulary and asked to create a systematic study guide — grouping related words, identifying patterns, building mnemonics, and summarizing all pairs.
3. **Post-test:** The model receives its own study notes plus the original vocabulary, and must answer the same lookup question.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Complexity** | simple, compound, relational | Simple: 1:1 word→object mappings. Compound: word→"size color" pairs. Relational: modifier words that compose with base words (e.g., "mako-" = "very", "trel" = "blue" → "mako-trel" = "very blue"). |
| **Evidence** | few (4), mid (8), many (12) | Number of word-meaning pairs to memorize. More pairs = harder recall. |
| **Seeds** | 0, 1, 2 | Independent random generations for statistical robustness. |

## Dataset generation

Nonsense words are built from pronounceable syllable templates (onset + vowel + optional coda). Meanings are drawn from pools of concrete nouns, colors, sizes, actions, and modifiers. For simple and compound conditions, the test pair is included in the material — the task is pure recall from a list. For relational conditions, the test is a novel composition whose modifier and base are both shown in the material, so the model must derive the answer by composing known parts.

## Scoring

- **Metric:** Post-learning accuracy (fraction of items where the model's post-study answer exactly matches the expected meaning).
- **Extraction:** Last short line (≤60 chars) from the response, lowercased and stripped of quotes/punctuation.
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **Simple/few:** Most models can handle 4 arbitrary 1:1 mappings — this is a baseline.
- **Relational/many:** Requires compositional understanding (modifier + base) across 12 pairs. Models that truly "learn" the modifier system will generalize; those that memorize surface patterns will fail on novel compositions.
- **Study quality matters:** Models that produce organized, complete study notes (with every pair listed) perform better than those that produce vague summaries.
