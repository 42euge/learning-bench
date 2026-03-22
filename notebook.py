# %% [markdown]
# # Learning Curve Profiler
#
# **Track:** Learning — Can the model acquire and apply new knowledge?
#
# This benchmark measures the *shape* of a model's in-context learning curve
# across procedurally generated rule-learning tasks. It reveals how accuracy
# changes as more demonstrations are provided — a signal no existing benchmark captures.

# %% Environment setup
import os
import sys
import subprocess

# Detect environment
ON_KAGGLE = os.environ.get("KAGGLE_KERNEL_RUN_TYPE") is not None
ON_COLAB = "google.colab" in sys.modules or os.path.exists("/content")

if ON_COLAB:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q",
        "kaggle-benchmarks @ git+https://github.com/Kaggle/kaggle-benchmarks.git",
        "matplotlib",
    ])
elif not ON_KAGGLE:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "matplotlib"])

print(f"Environment: {'Kaggle' if ON_KAGGLE else 'Colab' if ON_COLAB else 'Local'}")

# %% Imports
import re
import random
import string
import json
from dataclasses import dataclass

import kaggle_benchmarks as kbench
import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not available — plotting will be skipped")

# %% [markdown]
# ## Task Generators
#
# Three procedurally generated task families, each at three difficulty tiers.
# All tasks are seed-deterministic and have unambiguous correct answers.

# %% Constants
SHOT_COUNTS = [1, 2, 4, 8, 16, 32, 64]
DIFFICULTIES = ["easy", "medium", "hard"]
TASK_FAMILIES = ["string_rewriting", "modular_arithmetic", "artificial_grammar"]
SEEDS_PER_CONDITION = 30

# %% String Rewriting Generator

@dataclass
class StringRewritingRule:
    substitutions: dict[str, str]
    transform: str | None

def _apply_sr_rule(rule: StringRewritingRule, s: str) -> str:
    result = [rule.substitutions.get(ch, ch) for ch in s]
    out = "".join(result)
    if rule.transform is None:
        return out
    if rule.transform == "reverse":
        return out[::-1]
    if rule.transform.startswith("shift_"):
        n = int(rule.transform.split("_")[1]) % len(out) if out else 0
        return out[n:] + out[:n]
    return out

class StringRewritingGenerator:
    @staticmethod
    def generate_rule(seed, difficulty):
        rng = random.Random(seed)
        alphabet = list(string.ascii_lowercase)
        rng.shuffle(alphabet)
        if difficulty == "easy":
            n_subs, transform = 1, None
        elif difficulty == "medium":
            n_subs, transform = 2, None
        else:
            n_subs = 3
            transform = rng.choice(["reverse", f"shift_{rng.randint(1, 3)}"])
        sources = alphabet[:n_subs]
        remaining = [c for c in alphabet if c not in sources]
        targets = remaining[:n_subs]
        return StringRewritingRule(dict(zip(sources, targets)), transform)

    @staticmethod
    def _make_input(rule, rng):
        length = rng.randint(4, 8)
        source_chars = list(rule.substitutions.keys())
        inp = list(rng.choices(string.ascii_lowercase, k=length))
        inject_pos = rng.randint(0, length - 1)
        inp[inject_pos] = rng.choice(source_chars)
        return "".join(inp)

    def generate(self, seed, difficulty, n_examples=4):
        rule = self.generate_rule(seed, difficulty)
        rng_ex = random.Random(seed + 1000)
        examples = []
        for _ in range(n_examples):
            inp = self._make_input(rule, rng_ex)
            examples.append((inp, _apply_sr_rule(rule, inp)))
        rng_q = random.Random(seed + 2000)
        query_input = self._make_input(rule, rng_q)
        expected = _apply_sr_rule(rule, query_input)

        lines = ["Here are some examples of a string transformation rule:\n"]
        for inp, out in examples:
            lines += [f"Input: {inp}", f"Output: {out}", ""]
        lines += ["Now apply the same rule:", f"Input: {query_input}", "Output:"]
        return {"prompt": "\n".join(lines), "expected": expected, "family": "string_rewriting"}


# %% Modular Arithmetic Generator

OPERATOR_SYMBOLS = ["⊕", "⊗", "⊖", "⊘", "⊞", "⊠", "⊡", "⊛", "⊜", "⊝"]
OPERATIONS = [
    ("add", lambda a, b, m: (a + b) % m),
    ("mul", lambda a, b, m: (a * b) % m),
    ("add_scaled", lambda a, b, m: (2 * a + b) % m),
    ("diff_abs", lambda a, b, m: abs(a - b) % m),
    ("sum_sq", lambda a, b, m: (a * a + b) % m),
    ("add_plus1", lambda a, b, m: (a + b + 1) % m),
]

@dataclass
class Operator:
    symbol: str
    op_name: str
    op_fn: object
    modulus: int

@dataclass
class ArithmeticRule:
    operators: list
    precedence: list | None

def _eval_expression(rule, tokens):
    values = [t for i, t in enumerate(tokens) if i % 2 == 0]
    ops = [t for i, t in enumerate(tokens) if i % 2 == 1]
    if rule.precedence:
        for sym in rule.precedence:
            i = 0
            while i < len(ops):
                if ops[i] == sym:
                    op = next(o for o in rule.operators if o.symbol == sym)
                    values[i] = op.op_fn(values[i], values[i + 1], op.modulus)
                    values.pop(i + 1)
                    ops.pop(i)
                else:
                    i += 1
    else:
        while ops:
            sym = ops.pop(0)
            op = next(o for o in rule.operators if o.symbol == sym)
            a, b = values.pop(0), values.pop(0)
            values.insert(0, op.op_fn(a, b, op.modulus))
    return values[0]

class ModularArithmeticGenerator:
    @staticmethod
    def generate_rule(seed, difficulty):
        rng = random.Random(seed)
        n_ops = {"easy": 1, "medium": 2, "hard": 3}[difficulty]
        symbols = rng.sample(OPERATOR_SYMBOLS, n_ops)
        ops_pool = list(OPERATIONS)
        rng.shuffle(ops_pool)
        moduli_choices = [5, 7, 11, 13]
        operators = []
        for i in range(n_ops):
            mod = rng.choice(moduli_choices)
            op_name, op_fn = ops_pool[i]
            operators.append(Operator(symbols[i], op_name, op_fn, mod))
        precedence = None
        if difficulty == "hard":
            prec = [o.symbol for o in operators]
            rng.shuffle(prec)
            precedence = prec
        return ArithmeticRule(operators, precedence)

    @staticmethod
    def _make_expression(rule, rng):
        n_expr_ops = len(rule.operators)
        max_mod = max(o.modulus for o in rule.operators)
        values = [rng.randint(0, max_mod - 1) for _ in range(n_expr_ops + 1)]
        if n_expr_ops == 1:
            expr_ops = [rule.operators[0].symbol]
        else:
            expr_ops = [o.symbol for o in rule.operators]
            rng.shuffle(expr_ops)
            expr_ops = expr_ops[:n_expr_ops]
        tokens = []
        for i, v in enumerate(values):
            tokens.append(v)
            if i < len(expr_ops):
                tokens.append(expr_ops[i])
        expr_str = " ".join(str(t) for t in tokens)
        return tokens, expr_str, _eval_expression(rule, list(tokens))

    def generate(self, seed, difficulty, n_examples=4):
        rule = self.generate_rule(seed, difficulty)
        rng_ex = random.Random(seed + 1000)
        examples = []
        for _ in range(n_examples):
            _, expr_str, result = self._make_expression(rule, rng_ex)
            examples.append((expr_str, result))
        rng_q = random.Random(seed + 2000)
        _, query_expr, expected = self._make_expression(rule, rng_q)

        op_list = ", ".join(o.symbol for o in rule.operators)
        lines = [
            f"The following expressions use novel operator(s): {op_list}",
            "Each operator performs a specific arithmetic operation.",
            "Study the examples to figure out what each operator does, then evaluate the final expression.\n",
        ]
        for expr, result in examples:
            lines.append(f"{expr} = {result}")
        lines.append("")
        if rule.precedence:
            lines.append(f"Operator precedence (highest first): {' > '.join(rule.precedence)}")
            lines.append("")
        lines.append(f"{query_expr} =")
        return {"prompt": "\n".join(lines), "expected": str(expected), "family": "modular_arithmetic"}


# %% Artificial Grammar Generator

@dataclass
class Grammar:
    productions: dict
    start: str
    terminals: set
    nonterminals: set
    max_depth: int

def _enumerate_valid(grammar, max_len=15):
    valid = set()
    def _expand(symbol, depth):
        if depth > grammar.max_depth:
            return []
        if symbol in grammar.terminals:
            return [symbol]
        if symbol not in grammar.productions:
            return []
        results = []
        for alt in grammar.productions[symbol]:
            partial = [""]
            for s in alt:
                expanded = _expand(s, depth + 1)
                if not expanded:
                    partial = []
                    break
                new_partial = []
                for prefix in partial:
                    for suffix in expanded:
                        candidate = prefix + suffix
                        if len(candidate) <= max_len:
                            new_partial.append(candidate)
                partial = new_partial
            results.extend(partial)
        return results
    valid.update(_expand(grammar.start, 0))
    return valid

def _generate_invalid(grammar, rng, valid_strings):
    terminals = sorted(grammar.terminals)
    if not valid_strings:
        return "".join(rng.choices(terminals, k=rng.randint(2, 6)))
    base = rng.choice(sorted(valid_strings))
    for strategy in rng.sample(["swap", "insert", "delete", "replace"], 4):
        candidate = None
        if strategy == "swap" and len(base) >= 2:
            i = rng.randint(0, len(base) - 2)
            candidate = base[:i] + base[i + 1] + base[i] + base[i + 2:]
        elif strategy == "insert":
            i = rng.randint(0, len(base))
            candidate = base[:i] + rng.choice(terminals) + base[i:]
        elif strategy == "delete" and len(base) >= 2:
            i = rng.randint(0, len(base) - 1)
            candidate = base[:i] + base[i + 1:]
        elif strategy == "replace" and len(base) >= 1:
            i = rng.randint(0, len(base) - 1)
            candidate = base[:i] + rng.choice(terminals) + base[i + 1:]
        if candidate and candidate not in valid_strings:
            return candidate
    for _ in range(20):
        candidate = "".join(rng.choices(terminals, k=rng.randint(2, 6)))
        if candidate not in valid_strings:
            return candidate
    return "".join(rng.choices(terminals, k=7))

class ArtificialGrammarGenerator:
    @staticmethod
    def generate_rule(seed, difficulty):
        rng = random.Random(seed)
        pool = list("abcdefghkmnpqrstuvwxyz")
        rng.shuffle(pool)
        if difficulty == "easy":
            t = pool[:4]
            productions = {"S": [[t[0], "X", t[1]]], "X": [[t[2]], [t[3]]]}
            terminals, max_depth = set(t[:4]), 4
        elif difficulty == "medium":
            t = pool[:5]
            productions = {"S": [[t[0], "X", t[1]]], "X": [[t[2], "X", t[3]], [t[4]]]}
            terminals, max_depth = set(t[:5]), 5
        else:
            t = pool[:10]
            productions = {
                "S": [[t[0], "X", t[1]], [t[2], "Y", t[3]]],
                "X": [[t[4], "X", t[5]], [t[6]]],
                "Y": [[t[7], "Y", t[4]], [t[8]]],
            }
            terminals, max_depth = set(t[:10]), 6
        nonterminals = set(productions.keys())
        return Grammar(productions, "S", terminals, nonterminals, max_depth)

    def generate(self, seed, difficulty, n_examples=4):
        rule = self.generate_rule(seed, difficulty)
        valid_strings = _enumerate_valid(rule)
        valid_list = sorted(valid_strings)

        # Generate examples (balanced valid/invalid)
        rng = random.Random(seed + 1000)
        examples = []
        n_valid = (n_examples + 1) // 2
        if valid_list:
            for _ in range(n_valid):
                examples.append((valid_list[rng.randint(0, len(valid_list) - 1)], "valid"))
        for _ in range(n_examples - len(examples)):
            examples.append((_generate_invalid(rule, rng, valid_strings), "invalid"))
        rng.shuffle(examples)

        # Generate query
        rng_q = random.Random(seed + 2000)
        if rng_q.random() < 0.5 and valid_list:
            query = valid_list[rng_q.randint(0, len(valid_list) - 1)]
            expected = "valid"
        else:
            query = _generate_invalid(rule, rng_q, valid_strings)
            expected = "invalid"

        lines = [
            'The following strings are classified as either "valid" or "invalid"',
            "according to a hidden rule. Study the examples and classify the final string.\n",
        ]
        for s, label in examples:
            lines.append(f'"{s}" → {label}')
        lines += ["", f'"{query}" →']
        return {"prompt": "\n".join(lines), "expected": expected, "family": "artificial_grammar"}


GENERATORS = {
    "string_rewriting": StringRewritingGenerator,
    "modular_arithmetic": ModularArithmeticGenerator,
    "artificial_grammar": ArtificialGrammarGenerator,
}


# %% [markdown]
# ## Answer Extraction & Checking

# %% Answer parsing
def extract_answer(response: str, family: str) -> str:
    text = response.strip()
    if family == "string_rewriting":
        match = re.search(r"(?:Output:\s*)?([a-z]+)\s*$", text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        tokens = re.findall(r"[a-z]+", text.lower())
        return tokens[-1] if tokens else text
    elif family == "modular_arithmetic":
        match = re.search(r"=\s*(\d+)", text)
        if match:
            return match.group(1)
        numbers = re.findall(r"\d+", text)
        return numbers[-1] if numbers else text
    elif family == "artificial_grammar":
        text_lower = text.lower()
        if "invalid" in text_lower:
            return "invalid"
        if "valid" in text_lower:
            return "valid"
        return text
    return text

def check_answer(response: str, expected: str, family: str) -> bool:
    if family == "modular_arithmetic":
        try:
            return int(response) == int(expected)
        except ValueError:
            return response.strip() == expected.strip()
    return response.strip().lower() == expected.strip().lower()


# %% [markdown]
# ## Benchmark Task Definition

# %% Task
@kbench.task(
    name="Learning Curve Profiler",
    description=(
        "Measures how model accuracy improves as more in-context examples are "
        "provided, across three procedurally generated task families "
        "(string rewriting, modular arithmetic, artificial grammar) "
        "at three difficulty tiers."
    ),
)
def learning_curve_profiler(
    llm,
    prompt: str,
    expected: str,
    family: str,
    difficulty: str,
    shot_count: int,
    seed: int,
) -> bool:
    """Evaluate a single task instance. Returns True if correct."""
    response = llm.prompt(prompt)
    response_clean = extract_answer(response, family)
    return check_answer(response_clean, expected, family)


# %% [markdown]
# ## Analysis Utilities

# %% Metrics
def compute_accuracy_at_k(results_df):
    grouped = results_df.groupby(["family", "difficulty", "shot_count"])
    acc = grouped["result"].agg(["mean", "count"]).reset_index()
    acc.columns = ["family", "difficulty", "shot_count", "accuracy", "n_tasks"]
    return acc

def compute_aulc(accuracy_series, shot_counts=None):
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    log_k = [np.log2(k) for k in shot_counts]
    area = np.trapezoid(acc_values, log_k)
    max_area = 1.0 * (log_k[-1] - log_k[0])
    return area / max_area if max_area > 0 else 0.0

def compute_learning_rate(accuracy_series, shot_counts=None):
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    return [acc_values[i] - acc_values[i - 1] for i in range(1, len(acc_values))]

def compute_saturation_point(accuracy_series, shot_counts=None, threshold=0.02):
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    acc_values = [accuracy_series.get(k, 0.0) for k in shot_counts]
    for i in range(1, len(acc_values)):
        if acc_values[i] - acc_values[i - 1] < threshold:
            return shot_counts[i]
    return None

def classify_curve_shape(accuracy_series, shot_counts=None):
    if shot_counts is None:
        shot_counts = SHOT_COUNTS
    rates = compute_learning_rate(accuracy_series, shot_counts)
    if not rates:
        return "flat"
    total_gain = sum(rates)
    if total_gain < 0.05:
        return "flat"
    if max(rates) > 0.7 * total_gain:
        return "step"
    mid = len(rates) // 2
    first_half, second_half = sum(rates[:mid]), sum(rates[mid:])
    ratio = second_half / first_half if first_half > 0.001 else float("inf")
    if ratio > 2.0:
        return "sigmoid"
    if first_half > 1.5 * second_half:
        return "logarithmic"
    return "linear"

def compute_all_metrics(results_df):
    acc_df = compute_accuracy_at_k(results_df)
    rows = []
    for (family, difficulty), group in acc_df.groupby(["family", "difficulty"]):
        acc_series = group.set_index("shot_count")["accuracy"]
        rows.append({
            "family": family, "difficulty": difficulty,
            "aulc": round(compute_aulc(acc_series), 4),
            "learning_rates": [round(r, 4) for r in compute_learning_rate(acc_series)],
            "saturation_point": compute_saturation_point(acc_series),
            "asymptotic_accuracy": round(acc_series.get(SHOT_COUNTS[-1], 0.0), 4),
            "curve_shape": classify_curve_shape(acc_series),
            "accuracy_by_k": {int(k): round(float(v), 4) for k, v in acc_series.items()},
        })
    return pd.DataFrame(rows)

def compute_overall_aulc(results_df):
    acc_df = compute_accuracy_at_k(results_df)
    overall_acc = acc_df.groupby("shot_count")["accuracy"].mean()
    return compute_aulc(overall_acc)


# %% Visualization
def plot_learning_curves(results_df, title="Learning Curves"):
    acc_df = compute_accuracy_at_k(results_df)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    families = sorted(acc_df["family"].unique())
    colors = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}
    for ax, family in zip(axes, families):
        for diff in ["easy", "medium", "hard"]:
            subset = acc_df[(acc_df["family"] == family) & (acc_df["difficulty"] == diff)].sort_values("shot_count")
            if not subset.empty:
                ax.plot(subset["shot_count"], subset["accuracy"], marker="o",
                        label=diff, color=colors[diff], linewidth=2)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("Number of examples (k)")
        ax.set_title(family.replace("_", " ").title())
        ax.set_ylim(-0.05, 1.05)
        ax.legend()
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Accuracy")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


# %% [markdown]
# ## Generate Dataset

# %% Dataset generation
print("Generating benchmark dataset...")
rows = []
task_id = 0
for family in TASK_FAMILIES:
    gen = GENERATORS[family]()
    for difficulty in DIFFICULTIES:
        for seed in range(SEEDS_PER_CONDITION):
            for shot_count in SHOT_COUNTS:
                result = gen.generate(seed=seed, difficulty=difficulty, n_examples=shot_count)
                rows.append({
                    "task_id": task_id,
                    "family": family,
                    "difficulty": difficulty,
                    "shot_count": shot_count,
                    "seed": seed,
                    "prompt": result["prompt"],
                    "expected": result["expected"],
                })
                task_id += 1

dataset = pd.DataFrame(rows)
print(f"Generated {len(dataset)} tasks")
print(f"  {len(TASK_FAMILIES)} families × {len(DIFFICULTIES)} difficulties × {len(SHOT_COUNTS)} shot counts × {SEEDS_PER_CONDITION} seeds")

# %% [markdown]
# ## Run Evaluation

# %% Evaluate
print("\nRunning benchmark evaluation...")

results = learning_curve_profiler.evaluate(
    evaluation_data=dataset.set_index("task_id"),
    n_jobs=1,
    timeout=120.0,
)

# %% Process results
results_df = results.as_dataframe()
print(f"Completed: {len(results_df)} / {len(dataset)} tasks")

# Merge results back with metadata
merged = dataset.set_index("task_id").copy()
merged["result"] = False
for _, row in results_df.iterrows():
    idx = row.get("id")
    if idx is not None and idx in merged.index:
        merged.loc[idx, "result"] = bool(row["result"])
merged = merged.reset_index()

# %% [markdown]
# ## Results

# %% Compute metrics
metrics = compute_all_metrics(merged)
overall_aulc = compute_overall_aulc(merged)

print(f"\n{'='*60}")
print(f"OVERALL AULC: {overall_aulc:.4f}")
print(f"{'='*60}\n")
print(metrics[["family", "difficulty", "aulc", "asymptotic_accuracy", "curve_shape"]].to_string(index=False))

# %% Plot
if HAS_MATPLOTLIB:
    fig = plot_learning_curves(merged, title="Learning Curve Profiler")
    plt.show()
else:
    print("Plotting skipped (matplotlib not available)")

# %% [markdown]
# ## Detailed Results by Condition

# %% Detailed table
for _, row in metrics.iterrows():
    print(f"\n{row['family']} / {row['difficulty']}:")
    print(f"  AULC: {row['aulc']}")
    print(f"  Curve shape: {row['curve_shape']}")
    print(f"  Saturation: k={row['saturation_point']}")
    print(f"  Accuracy by k: {row['accuracy_by_k']}")

# %% Choose main task for leaderboard
# %choose learning_curve_profiler
