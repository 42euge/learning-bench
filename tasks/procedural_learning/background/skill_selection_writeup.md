# Skill Selection Under Context Pollution

## Team

Eugenio

## Problem Statement

Modern LLMs are increasingly deployed as tool-using agents with access to dozens of skills, APIs, and functions. As the number of available tools grows, the context window fills with tool descriptions — and models start selecting the wrong tool. This is not a hypothetical failure: it happens in production systems where 30+ tools are loaded simultaneously, and a model picks a superficially similar tool instead of the correct one.

No existing benchmark measures this capability in isolation. Standard tool-use benchmarks test whether a model can *use* a tool correctly, but not whether it can *select* the right tool from a crowded, ambiguous, or deliberately misleading registry. We call this failure mode **context pollution** — performance degrades not because the task is harder, but because irrelevant or confusing context interferes with selection.

The **Skill Selection** benchmark tests whether models can learn to navigate a growing tool registry, especially when tool names and descriptions are misleading. It directly measures a cognitive ability within the Learning track: can the model acquire and apply tool-selection strategies from practice examples?

## Task & Benchmark Construction

The benchmark uses a fictional enterprise automation platform ("Nexara Platform") with invented tool names (e.g., `flux_bridge`, `glyph_weaver`) to prevent any pretrained knowledge from leaking in. Each tool belongs to one of 15 capability domains (signal routing, schema validation, graph traversal, etc.) and has a name, description, and capabilities list.

The model sees a tool registry and a user request, then must select the single correct tool. We measure performance in a **pre/post learning framework**:

1. **Pre-learning**: The model selects a tool cold — no practice, no hints.
2. **Study phase**: The model analyzes practice examples showing correct tool selections with explanations, and writes notes about selection strategies.
3. **Post-learning**: The model selects a tool again, now with access to its own study notes.

### Difficulty Axes

**Tool count** (5, 15, 30): More tools mean more context to parse and more distractors.

**Similarity mode** — the key discriminator:
- **Distinct**: Tool names, descriptions, and capabilities all align clearly. Baseline — every model should succeed here.
- **Confusable**: Descriptions use generic, overlapping language across tools (e.g., "processes incoming data flows" for both a router and a converter). The model must read capabilities carefully to distinguish.
- **Adversarial**: Tool descriptions deliberately suggest a *different* domain than the tool's actual capability. The name says "synthesizer" but the capabilities say "router." The model must ignore surface-level cues and trust the capabilities list.

Three random seeds per condition yield **27 evaluation items** (3 tool counts × 3 similarity modes × 3 seeds).

## Dataset

- **27 items**, each with a unique tool registry, user request, correct tool, and study examples
- **All synthetic** — invented tool names, domains, and descriptions. Zero pretrained knowledge contamination.
- **Verifiably correct**: Each request maps to exactly one domain, and each registry has exactly one tool per domain. No ambiguity.
- **Deterministic**: Fixed random seeds produce identical datasets across runs.
- **Hosted on Kaggle**: `eugenio0/skill-selection-benchmark`
- **Generation script**: `datasets/skill_selection/generate.py` (standalone, reproducible)

## Technical Details

### Answer Format

Models respond with the tool name (e.g., `flux_bridge`), not a letter or number. This avoids position bias and mirrors real tool-use scenarios. Extraction uses fuzzy matching against valid tool names in the registry.

### Study Material

The study phase provides 4–8 practice examples (scaling with registry size) showing (task, correct tool, explanation). For adversarial conditions, explanations explicitly call out misleading names: *"Despite its name suggesting synthesis, flux_bridge is correct because its CAPABILITIES list (route signals, apply priority dispatch) directly match the task."*

### Metrics

- **Pre-learning accuracy**: Baseline tool selection without study
- **Post-learning accuracy**: Selection after studying practice examples
- **Learning gain**: Post − Pre accuracy
- **Learning efficiency**: Gain / (1 − Pre), measuring how much of the available improvement room is captured

## Results, Insights, and Conclusions

We evaluated across a scaling ladder from a 1B parameter model to frontier:

| Model | Pre | Post | Gain | Distinct | Confusable | Adversarial |
|---|---|---|---|---|---|---|
| gemma-3-1b | 14.8% | 14.8% | +0.0% | 33% | 11% | 0% |
| gemma-3-4b | 85.2% | 81.5% | −3.7% | 100% | 100% | 56% |
| gemini-2.5-flash | 88.9% | 96.3% | +7.4% | 100% | 100% | 67% |
| gemini-2.5-pro | 100% | 100% | +0.0% | 100% | 100% | 100% |

### Key Findings

**1. Adversarial similarity is the pure discriminator.** Distinct and confusable conditions hit ceiling (100%) for all models above 1B. But adversarial — where descriptions deliberately mismatch capabilities — produces a clean gradient: 0% → 56% → 67% → 100%. This isolates the specific skill of reading past surface cues.

**2. Small models can't even follow the format.** gemma-3-1b scores 33% on *distinct* (the easiest condition) and 0% at 15+ tools. It cannot reliably parse a tool registry and extract the right name, regardless of difficulty.

**3. Tool count compounds the difficulty.** gemma-3-1b drops from 44% (5 tools) to 0% (30 tools). Even gemma-3-4b drops from 100% to 56–89%. Context length and distractor density are separate but interacting difficulty axes.

**4. Learning gain requires sufficient baseline capability.** gemma-3-1b and gemma-3-4b show zero or negative learning gain — their study notes either don't help or actively confuse them. Only gemini-2.5-flash shows meaningful positive gain (+7.4%), reaching near-ceiling post-learning. This suggests a capability threshold below which self-generated study notes are noise.

**5. Negative learning gain is real.** gemma-3-4b's post-learning accuracy is *lower* than pre-learning (−3.7%). The model's own study notes introduced confusion. This mirrors a known phenomenon in human learning where elaboration can hurt when the learner lacks sufficient base understanding.

### What This Reveals

The Skill Selection benchmark answers: *"What can this benchmark tell us about model behavior that we could not see before?"*

It reveals that **tool selection under context pollution is a distinct cognitive skill that scales with model capability** — separate from tool use, instruction following, or general reasoning. Models that excel at standard benchmarks can still fail catastrophically when tool descriptions are misleading, and this failure mode has a clear scaling signature. The benchmark also shows that **in-context learning from practice examples** only helps models above a capability threshold, challenging the assumption that more examples always help.

## Organizational Affiliations

Independent

## References & Citations

1. Morris et al. (2024). "Measuring progress toward AGI: A cognitive framework." Google DeepMind.
2. Schick et al. (2023). "Toolformer: Language Models Can Teach Themselves to Use Tools." NeurIPS.
3. Qin et al. (2024). "Tool Learning with Large Language Models: A Survey." arXiv:2405.17935.
4. Patil et al. (2023). "Gorilla: Large Language Model Connected with Massive APIs." arXiv:2305.15334.
