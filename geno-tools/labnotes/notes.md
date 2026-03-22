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
