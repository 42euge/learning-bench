# Skill Selection

**Sub-ability:** Procedural Learning
**Difficulty grid:** 3 registry sizes × 3 similarity levels × 3 seeds = 27 items

## What it tests

Can the model learn to select the correct tool from a growing registry of tools with potentially misleading names and descriptions? This tests procedural learning in a realistic scenario — navigating a complex tool ecosystem where surface-level cues (names, descriptions) can be deceptive and only deep capability analysis reveals the right choice.

## Three-phase framework

1. **Pre-test:** The model sees a tool registry (with names, descriptions, and capabilities) and a task description, and must select the correct tool. No study time.
2. **Study:** The model receives the registry plus practice examples (tasks with correct tool selections and explanations), and must analyze patterns, note misleading cases, and build a quick-reference guide.
3. **Post-test:** The model receives its own study notes plus the original registry and task, and must select the correct tool.

## Difficulty dimensions

| Dimension | Levels | What varies |
|-----------|--------|-------------|
| **Registry size** | 5, 15, 30 | Number of tools in the registry. Larger registries = more distractors. |
| **Similarity** | distinct, confusable, adversarial | Distinct: clear, accurate descriptions. Confusable: generic descriptions that overlap. Adversarial: deliberately misleading names/descriptions (capabilities are the ground truth). |
| **Seeds** | 0, 1, 2 | Independent random generations. |

Study examples scale with registry size: 4 examples for 5 tools, 6 for 15, 8 for 30.

## Dataset generation

Tools are generated with synthetic names (e.g., `flux_bridge`, `data_weaver`), descriptions, and capability lists across multiple domains (data processing, security, analytics, etc.). In adversarial mode, tool names and descriptions are swapped or made misleading while capabilities remain truthful. Practice examples are generated with explicit explanations of why the correct tool was chosen.

## Scoring

- **Metric:** Post-learning accuracy (exact tool name match).
- **Extraction:** Match against valid tool names list — tries exact match first, then substring on short lines.
- **Per-item assertion:** `kbench.assertions.assert_equal(post_extracted, expected)`

## What discriminates models

- **5/distinct:** Easy baseline — 5 clearly described tools, most models succeed.
- **30/adversarial:** The hardest setting. 30 tools with misleading names and descriptions. Only models that carefully read capabilities (not names) and learned from the practice examples will select correctly.
- **Study quality:** Models that build accurate quick-reference guides mapping each tool to its actual capabilities outperform those that just summarize descriptions.
