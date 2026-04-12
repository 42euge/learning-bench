# Learning Sub-Abilities: Task Design

**Last updated:** 2026-04-09 — Task brainstorm + dataset search

## Overview

6 sub-abilities from the Learning track, 3-4 tasks each. All tasks use the pre/post learning framework (pre-learning → study → post-learning). Synthetic data preferred to prevent pretrained knowledge leakage.

---

## 1. Concept Formation

*Abstracting key features of objects, events, and ideas to form categories and schemas.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Category Learning** | Learn hidden classification rules from labeled objects | ✅ Built | Synthetic |
| 2 | **Rule Induction** | Discover composed string transformation rules from I/O examples | ✅ Built | Synthetic |
| 3 | **Prototype Extraction** | Given examples of novel "species" with varying features, identify the prototype/central tendency | New | Synthetic: generate feature vectors with cluster structure |
| 4 | **Exception Learning** | Learn a rule, then learn exceptions to it | New | Synthetic: rule + exceptions pattern |

## 2. Associative Learning

*Learning relationships between events, objects, or stimuli that appear together.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Analogy Completion** | Learn relational mappings between novel domains | ✅ Built | Synthetic |
| 2 | **Paired Associate Learning** | Learn arbitrary pairings (novel word → novel symbol/meaning), then recall | New | Synthetic: invented vocabulary mappings |
| 3 | **Contextual Association** | Learn that X predicts Y in context A but Z in context B | New | Synthetic: context-dependent mappings |
| 4 | **Sequence Extrapolation** | Identify mathematical patterns, predict next term | ✅ Built | Synthetic |

## 3. Reinforcement Learning

*Learning based on the consequences (rewards and punishments) of actions.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Multi-Armed Bandit** | Choose between options, get reward feedback, learn optimal strategy | New | Synthetic: reward distributions |
| 2 | **Reward Reversal** | Learn which action is rewarded, then reward switches — can model adapt? | New | Synthetic: reward schedules with reversals |
| 3 | **Delayed Gratification** | Choose between immediate small reward vs. sequence of actions for larger reward | New | Synthetic: decision trees with payoffs |
| 4 | **Belief Revision** | Update answers when given contradicting evidence | ✅ Built | Synthetic |

## 4. Observational Learning

*Learning by watching others perform a skill or task.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Trace-Based Imitation** | Given step-by-step worked examples of a novel procedure, apply it to new inputs | New | Synthetic: invented algorithms with traces |
| 2 | **Error Observation** | Watch someone solve a problem with mistakes, identify what went wrong and solve correctly | New | Synthetic: solutions with deliberate errors |
| 3 | **Strategy Extraction** | Observe multiple agents solving same problem differently, identify which strategy works best | New | Synthetic: game/puzzle solution traces |
| 4 | **Demonstration Generalization** | See a skill demonstrated in one domain, transfer to analogous domain | New | Synthetic: cross-domain procedure mapping |

## 5. Procedural Learning

*Learning skills, action patterns, or tasks through performance or practice.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Novel Algorithm Execution** | Learn a made-up algorithm from description, execute it step by step | New | Synthetic: invented algorithms |
| 2 | **Multi-Step Procedure** | Learn a multi-step procedure (like a recipe), apply it with variations | New | Synthetic: procedural recipes with substitutions |
| 3 | **Debugging by Practice** | Given buggy code in a novel language, learn syntax rules from examples, then fix bugs | New | Synthetic: invented programming language |
| 4 | **Rule Composition** | Learn individual rules, then compose them in correct order | New | Synthetic: transformation chains |
| 5 | **Skill Selection** | Learn to select the correct tool from a growing registry as context gets noisier | ✅ Built | Synthetic |

## 6. Language Learning

*Acquiring new language-related information, such as syntax, vocabulary, and coding languages.*

| # | Task | Description | Status | Dataset |
|---|------|-------------|--------|---------|
| 1 | **Novel Grammar Induction** | Learn the grammar of an invented language from examples, then generate/judge sentences | New | Synthetic: constructed grammar |
| 2 | **Vocabulary Mapping** | Learn translations between English and an invented language, translate new sentences | New | Synthetic: invented lexicon + rules |
| 3 | **Code in Novel Language** | Learn a new (invented) programming language from examples, write/predict output | New | Synthetic: invented language spec + examples |
| 4 | **Morphological Rule Learning** | Learn how words change form (plurals, tenses) in a novel system | New | Synthetic: invented morphology rules |

---

## Dataset Search Results

**Overall finding:** No existing datasets directly usable for any task. Synthetic generation is the correct approach — this is actually a strength since it guarantees zero pretrained knowledge contamination.

### Useful references & inspiration by sub-ability

#### Concept Formation
- **Posner & Keele (1968)** dot-pattern distortion paradigm — gold standard for prototype extraction experiments
- **RULEX model** (Nosofsky et al. 1994) — canonical rule-plus-exception paradigm
- **GPICL Benchmark** (arXiv:2405.17234) — general-purpose in-context learning with minimal transferable knowledge
- `sklearn.datasets.make_classification` — useful for generating clustered feature vectors

#### Associative Learning
- **Wuggy** (github.com/WuggyCode/wuggy) — Python lib for generating phonotactically valid pseudowords
- **CL-bench** (tencent/CL-bench on HF) — 500 contexts, 1,899 tasks requiring learning from context
- **MIR-Bench** (kaiyan289/MIR-Bench on HF) — many-shot in-context inductive reasoning
- **"ICL Learns Label Relationships"** (arXiv:2307.12375) — key paper on LLMs learning arbitrary mappings

#### Reinforcement Learning
- **"LLMs Are In-Context Bandit RL"** (arXiv:2410.05362, COLM 2025) — directly tests LLMs on bandit tasks, validates approach
- **OpenAI Gym bandit environments** — reference for distribution design
- **Iowa Gambling Task** — structural inspiration for delayed gratification
- **UC Davis CNTRACS probabilistic reversal learning** — standard reversal learning paradigm (80/20 → 20/80)

#### Observational Learning
- **ProcessBench** (Qwen/ProcessBench on HF) — 3,400 step-by-step math solutions with annotated errors
- **PRM800K** (trl-lib/prm800k on HF) — 800K step-level correctness labels
- **Codeforces-cots** (open-r1/codeforces-cots on HF) — 5 different reasoning traces per problem
- Contamination risk: use these as format templates but generate novel problems

#### Procedural Learning
- **SCAN** (scan on HF) — compositional commands → action sequences. Use structure but invent new primitives
- **COGS** (github.com/najoungkim/COGS) — compositional generalization (24K examples)
- **CLUTRR** (CLUTRR/v1 on HF) — rule composition via family relationships
- **Reasoning Gym** (github.com/open-thought/reasoning-gym) — 100+ procedural generators, NeurIPS 2025

#### Language Learning
- **AGSuite** (R package, github.com/cookm346/AGSuite) — generates artificial grammar learning stimuli
- **UniMorph 4.0** (unimorph.github.io) — 169 languages, 14.8M morphological triplets as templates
- **SIGMORPHON Shared Tasks** — annual morphological inflection challenges
- **"Implicit ICL"** (arXiv:2503.24190) — adapted AGL experiments for GPT-4o/o3-mini
- **Wug test papers** (ACL 2024, EMNLP 2023) — tested LLMs on novel word inflection

---

## Summary

- **Total tasks:** 25 (6 built + 19 new)
- **Sub-abilities covered:** 6/6
- **Dataset strategy:** All synthetic — guarantees zero pretrained knowledge contamination
- **Key references:** arXiv:2410.05362 (bandit RL), arXiv:2503.24190 (implicit ICL), SCAN, UniMorph, ProcessBench
