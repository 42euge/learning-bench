# Failure-Grounded Task Catalog

Each task below is abstracted from real failure modes observed during session mining. The goal: synthetic stimuli that reproduce the cognitive failure without leaking any actual session data. Every task fits the pre/study/post paradigm.

## Mapping Summary

| Task | Sub-Ability | Source Failure | Stimulus Type |
|---|---|---|---|
| {name} | {concept_formation / associative / procedural / observational / reinforcement} | {which mined session(s) surfaced this} | {error log / trace / history / etc.} |

---

## {Sub-Ability} Tasks

### 1. {Task Name}
**Source failures:** which session(s) this came from, with one-sentence summary of the observed failure.

**Task:** One paragraph describing what the model is asked to do.

**Pre:** What the model does without any study phase.
**Study:** What the model is asked to analyze / articulate about the examples.
**Post:** What the model does after studying, conditioned on its own notes.

**Example stimulus:**
```
An actual minimal example of what the model sees. Make it novel / synthetic — must not overlap with training data.
```
**Expected answer:** {exact form of the correct response}

---

## Pre/Study/Post Paradigm

All tasks should share this structure:

1. **Pre-phase:** Ask the question without any guidance. Measures baseline (what the model knows cold).
2. **Study phase:** Present labeled examples and ask the model to articulate the underlying rule / pattern / protocol in its own words.
3. **Post-phase:** Ask the original question again, now conditioned on the model's own study notes.

Score = post-phase accuracy. Learning gain = post − pre.

## Difficulty Grid

Each task should have a 3×3×3 grid:
- **Complexity** (3 levels): easy / medium / hard variants of the underlying rule
- **Evidence** (3 levels): few / mid / many study examples
- **Seed** (3 seeds): for statistical stability

= 27 items per task.

## Cognitive Sub-Ability Mapping (reference)

From the learning sciences literature — useful for organizing which sub-abilities your failures hit:

- **Associative Learning** — mapping from X to Y (e.g., error code → remediation)
- **Concept Formation** — classification / categorization (e.g., warning vs error)
- **Language Learning** — inducing rules of a novel formal system
- **Observational Learning** — learning from worked examples / execution traces
- **Procedural Learning** — executing novel multi-step procedures correctly
- **Reinforcement Learning** — learning from outcomes / reward signals (e.g., when to pivot strategy)
