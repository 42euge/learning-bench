# Lab Notes

## 2026-03-21

**Repo setup complete.** Added:
- `requirements.txt` — kaggle-benchmarks SDK (from GitHub), pandas, numpy, matplotlib, python-dotenv
- `.env.example` — template for Kaggle Model Proxy config (API key, model defaults, caching)
- `src/benchmark.py` — scaffold with example `@kbench.task` showing the decorator pattern, llm.prompt(), and assertions
- Updated `.gitignore` (venv dirs) and `README.md` (setup instructions)

Key finding: kaggle-benchmarks uses `@kbench.task(name=...)` decorator, `llm.prompt()` for model interaction, and `kbench.assertions` for validation. Local dev requires MODEL_PROXY_API_KEY from Kaggle.

---

## 2026-03-21 — Benchmark concept selection

**Decision: Learning Curve Profiler**

Reviewed all 5 benchmark ideas from track research. Selected **Learning Curve Profiler** — it measures the *shape* of how models learn from in-context examples, which no existing benchmark does.

### Hypothesis

The shape of a model's learning curve (how accuracy improves with more demonstrations) reveals fundamental differences in learning ability that single-point accuracy measurements miss.

### Novel signal

- **Learning rate** — how quickly accuracy improves per additional example
- **Saturation point** — when adding more examples stops helping
- **Asymptotic ceiling** — maximum achievable accuracy
- **Curve shape** — linear? logarithmic? sigmoid? step-function?

This answers the key question: *"What can this benchmark tell us about model behavior that we could not see before?"*

### Why not the others

| Concept | Reason for passing |
|---|---|
| Xenolinguistics | High quality but significantly more complex to build; good candidate for future iteration |
| Fragile Knowledge | Overlaps with Attention track (focus on relevant info, ignore distractions) |
| Corrective Cascade | Overlaps with Metacognition track (knowing what you know/don't know) |
| Concept Transfer | Medium discrimination, less compelling framing |

---

## 2026-03-21 — Formal benchmark hypothesis

### Hypothesis statement

The shape of a model's in-context learning curve — measured across procedurally generated rule-learning tasks at shot counts 1, 2, 4, 8, 16, 32, 64 — reveals fundamental differences in learning ability that single-point accuracy measurements miss. Specifically, models differ in learning rate, saturation point, asymptotic ceiling, and curve shape (linear/logarithmic/sigmoid/step), and these differences are consistent within model families but discriminating across them.

### Novel signals (what this reveals that we couldn't see before)

1. **Learning rate** — slope of accuracy improvement per doubling of examples
2. **Saturation point** — first k where accuracy gain < 2%
3. **Asymptotic ceiling** — max accuracy at k=64
4. **Curve shape classification** — linear / logarithmic / sigmoid / step-function
5. **Cross-task consistency** — do models have a characteristic "learning signature"?

No existing benchmark captures the *shape* of in-context learning. Current benchmarks report accuracy at a fixed shot count (typically 0 or 5). This benchmark treats the learning curve itself as the measurement.

### Task families (3 types, procedurally generated for contamination resistance)

1. **String rewriting** — character substitution rules (e.g., "every vowel becomes the next consonant")
2. **Modular arithmetic with invented notation** — novel operator symbols with defined semantics (e.g., "a ⊕ b = (2a + b) mod 7")
3. **Artificial grammar classification** — strings that follow/violate procedurally generated grammars

All tasks are procedurally generated with random seeds, making memorization from training data ineffective.

### Complexity tiers

| Tier | Rules | Example |
|---|---|---|
| Easy | 1 rule | Single substitution: a→x |
| Medium | 2-rule composition | Substitute then reverse |
| Hard | 3+ rule chains | Substitute, reverse, then apply positional shift |

### Metrics

**Primary metric:** AULC (Area Under Learning Curve) — captures overall learning ability in a single number, analogous to AUC-ROC for classifiers.

**Secondary metrics:**
- Accuracy@k (accuracy at each shot count)
- Learning rate (slope between consecutive shot counts)
- Saturation point (first k where Δaccuracy < 2%)
- Asymptotic accuracy (accuracy at k=64)

### Expected discrimination patterns

| Model class | Expected curve shape | Learning rate | Ceiling |
|---|---|---|---|
| Small models (≤7B) | Linear / flat | Low | Low |
| Large models (70B+) | Logarithmic | High early, tapering | High |
| Reasoning models (o-series, thinking) | Sigmoid | Slow start, then rapid | High |
| Fine-tuned/distilled | Variable | Task-dependent | Medium |

This should produce a meaningful gradient across frontier models — not all 0% or all 100%. Easy tasks ensure even small models score above zero; hard tasks with few shots ensure even frontier models don't saturate.

### What this means for the build

The next step is to design the three task families with difficulty scaling, implement the procedural generation, and verify that tasks have unambiguous correct answers.

---

## 2026-03-21 — Task type generators implemented

Built procedural generators for all three task families in `src/generators/`:

### Generators

1. **StringRewritingGenerator** — Character substitution rules with guaranteed source-char presence in all examples. Easy (1 rule), medium (2 rules), hard (3 rules + reverse/shift transform).

2. **ModularArithmeticGenerator** — Novel operator symbols (⊕, ⊗, etc.) with modular arithmetic semantics. Easy (1 op), medium (2 ops), hard (3 ops with explicit precedence rules). Operands drawn from range [0, modulus-1], moduli are small primes (5, 7, 11, 13).

3. **ArtificialGrammarGenerator** — Context-free grammars with valid/invalid string classification. Easy (2-3 non-recursive productions), medium (recursive grammar), hard (multiple recursive nonterminals with distractor patterns). Uses exhaustive enumeration for verification.

### Verification

- All generators are deterministic (same seed → same output)
- All answers verified correct across 10 seeds × 3 difficulties per family
- String rewriting examples guaranteed to demonstrate the rule (at least one source char in every input)
- Shared constants: `SHOT_COUNTS = [1, 2, 4, 8, 16, 32, 64]`, `DIFFICULTIES`, `TASK_FAMILIES`

### Next step

Build the full dataset: for each (family × difficulty × seed × shot_count), generate a task instance and store as the benchmark dataset.

---

## 2026-03-21 — Dataset + benchmark implementation

### Dataset (`src/dataset.py`)

Generated 1,890 task instances: 3 families × 3 difficulties × 7 shot counts × 30 seeds. Output as JSON in `data/benchmark_dataset.json`. Can also generate inline without disk I/O.

### Benchmark (`src/benchmark.py`)

Single `@kbench.task` decorated function `learning_curve_profiler` that:
- Takes prompt, expected answer, and metadata (family, difficulty, shot_count, seed)
- Sends prompt to LLM via `llm.prompt()`
- Extracts answer with family-specific parsing (regex for strings, numbers, valid/invalid)
- Returns `bool` (pass/fail)

Answer extraction handles common model response patterns:
- String rewriting: captures last lowercase word, or text after "Output:"
- Modular arithmetic: captures number after "=" or last number
- Artificial grammar: detects "valid"/"invalid" anywhere in response

### Analysis (`src/analysis.py`)

Computes all learning curve metrics:
- **AULC** — trapezoidal integration over log2-spaced shot counts, normalized to [0,1]
- **Learning rate** — accuracy gain per doubling
- **Saturation point** — first k where gain < 2%
- **Asymptotic accuracy** — accuracy at k=64
- **Curve shape classification** — flat/linear/logarithmic/sigmoid/step

Includes `plot_learning_curves()` for visualization (3-panel plot by family).

### Runner (`src/run_benchmark.py`)

End-to-end CLI: `python -m src.run_benchmark [--quick] [--seeds N] [--jobs N]`
Generates dataset, runs evaluation, computes metrics, saves results + plots.

### Next step

Run against frontier models via Kaggle Model Proxy.

---

## 2026-04-09 — Multi-Armed Bandit: first run (Gemini 2.5 Flash)

- **Task**: `eugenio0/new-benchmark-task-e2cdd` (v2)
- **Status**: COMPLETE
- **Model**: google/gemini-2.5-flash
- **Results**: Pre=96.3%, Post=96.3%, Gain=+0.0%
- **Verdict**: CEILING EFFECT — task is too easy. Flash computes win rates trivially. Only 1 failure (4arms_moderate where empirical rates were close). Zero learning gain because baseline is already near-perfect.
- **Next**: Need to make the task harder — reduce history length, add non-stationarity, or use continuous rewards to require real statistical reasoning.
- **Output**: `results/bandit_v1/`

---

## 2026-04-09 — Skill Selection benchmark built

- **Path**: `tasks/procedural_learning/skill_selection.ipynb`
- **Design**: Can a model learn to select the correct tool from a growing registry as context gets noisier?
- **Difficulty grid**: 3 num_tools (5/15/30) × 3 similarity (distinct/confusable/adversarial) × 3 seeds = 27 items
- **Platform**: Fictional "Nexara Platform" with invented tool names (flux_bridge, glyph_weaver, etc.)
- **Key feature**: Adversarial mode uses tool names/descriptions that deliberately mismatch actual capabilities
- **Status**: Built, compatibility checks pass, ready to push to Kaggle
- **Motivation**: Directly inspired by real failure — Claude picked wrong tool (Colab upload vs Kaggle benchmarks) from 30+ loaded skills

---

## 2026-04-09 — Skill Selection: first multi-model run (v3, extraction bug)

- **Task**: `eugenio0/new-benchmark-task-e2cdd` (v3)
- **Status**: COMPLETE but extraction bug (underscore removal broke tool name matching)
- **Models**: gemma-3-4b, gemini-2.5-flash, gemini-2.5-pro
- **Re-scored locally with fixed extraction:**
  - gemma-3-4b:      pre=70.4%  post=70.4%  gain=+0.0%
  - gemini-2.5-flash: pre=96.3%  post=100%   gain=+3.7%
  - gemini-2.5-pro:   pre=92.6%  post=100%   gain=+7.4%
- **Adversarial is the discriminator**: gemma-3-4b=22%, flash=89%, pro=78%
- **Distinct is at ceiling**: 100% for all models (good baseline anchor)
- **Learning gain**: Flash and pro both reach 100% post-learning; gemma-3-4b gains nothing
- **Bug fix**: `re.sub(r'[`*_]', '', text)` was removing underscores from tool names → 0% extraction. Fixed to `re.sub(r'[`*]', '', text)`.
- **v5 pushed** with fix, awaiting results
- **Output**: `results/skill_selection_v1/`

---

## 2026-04-09 — Skill Selection: official results (v5, extraction fixed)

- **Task**: `eugenio0/new-benchmark-task-e2cdd` (v5)
- **Status**: COMPLETE — clean results, 0 extraction failures
- **Models**: gemma-3-4b, gemini-2.5-flash, gemini-2.5-pro
- **Results:**
  - gemma-3-4b:      pre=81.5%  post=81.5%  gain=+0.0%
  - gemini-2.5-flash: pre=96.3%  post=100%   gain=+3.7%
  - gemini-2.5-pro:   pre=100%   post=100%   gain=+0.0%
- **Adversarial is the discriminator**: 4b=44%, flash=89%, pro=100%
- **Tool count scales for weak models**: 4b drops 100%→67% at 30 tools
- **Distinct & confusable at ceiling** for all — good anchors
- **Verdict**: STRONG discriminatory power. Adversarial similarity is the key axis. Task works.
- **Output**: `results/skill_selection_v2_fixed/`

---

## 2026-04-12 — Dataset extraction complete (all 12 tasks)

All 12 task notebooks now have:
- `datasets/<task>/generate.py` — standalone, deterministic seeds (no hash())
- `datasets/<task>/dataset-metadata.json` — Kaggle upload metadata
- Kaggle datasets uploaded (all 12)
- Notebooks slimmed: generation code removed, load from Kaggle CSV
- Multi-model eval added (gemma-3-1b, gemma-3-4b, gemini-2.5-flash)

| Task | Kaggle Dataset | Rows |
|------|---------------|------|
| skill_selection | eugenio0/skill-selection-benchmark | 27 |
| novel_algorithm_execution | eugenio0/novel-algorithm-execution-benchmark | 27 |
| novel_grammar_induction | eugenio0/novel-grammar-induction-benchmark | 108 |
| category_learning | eugenio0/category-learning-benchmark | 27 |
| analogy_completion | eugenio0/analogy-completion-benchmark | 27 |
| sequence_extrapolation | eugenio0/sequence-extrapolation-benchmark | 27 |
| rule_induction | eugenio0/rule-induction-benchmark | 27 |
| belief_revision | eugenio0/belief-revision-benchmark | 27 |
| multi_armed_bandit | eugenio0/multi-armed-bandit-benchmark | 27 |
| paired_associate | eugenio0/paired-associate-benchmark | 27 |
| prototype_extraction | eugenio0/prototype-extraction-benchmark | 27 |
| trace_based_imitation | eugenio0/trace-based-imitation-benchmark | 27 |

**Next**: Run each task on Kaggle with scaling ladder to find which show discriminatory power.
**Blocker**: Single benchmark slug (e2cdd) serializes all runs.
