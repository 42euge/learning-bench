#!/usr/bin/env python3
"""Generate the batch error diagnosis benchmark dataset.

Task: Given a multi-error build/test output, identify ALL distinct root causes
in one pass — not just the first one. The failure mode (observed in real agent
runs) is fixing one error, re-running, seeing the next, fixing it, re-running...
doing N cycles instead of 1.

Three complexity dimensions:
    - independent_errors: errors don't affect each other
    - chained_errors: fixing one would expose another (careful ordering needed)
    - redundant_errors: multiple symptoms of the same root cause (don't over-count)

Usage:
    python datasets/batch_error_diagnosis/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/batch_error_diagnosis/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Error template pools ===
#
# Each error template produces a single build-output line. The template is
# paired with a "root cause" key so we can tell whether multiple lines point
# to the SAME underlying issue (redundant) or DIFFERENT ones (independent).

FILES = [
    'src/auth/session.ts', 'src/auth/login.ts', 'src/api/users.ts',
    'src/api/orders.ts', 'src/models/user.ts', 'src/models/order.ts',
    'src/utils/format.ts', 'src/utils/parse.ts', 'src/pages/dashboard.tsx',
    'src/pages/settings.tsx', 'src/hooks/useAuth.ts', 'src/store/reducer.ts',
    'src/lib/client.ts', 'src/lib/validator.ts', 'test/api.test.ts',
    'test/auth.test.ts',
]

IDENTIFIERS = [
    'UserProfile', 'OrderItem', 'sessionToken', 'formatDate', 'parseAmount',
    'validateEmail', 'AuthContext', 'useSettings', 'fetchOrders', 'StoreState',
    'ApiClient', 'normalizeInput', 'RequestHeaders', 'ResponsePayload',
]

MODULES = [
    '@/utils/logger', 'lodash', '@/lib/config', 'react-query', '@/models/base',
    'date-fns', '@/store/actions', 'zod',
]


# Each generator returns (line_text, root_cause_key).
# root_cause_key is what determines distinctness.

def err_type_mismatch(rng, cause_id):
    """TS2345 type mismatch; same cause_id across lines => same root cause."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    ident = IDENTIFIERS[cause_id % len(IDENTIFIERS)]
    return (f"{f}:{ln}:{col} - error TS2345: Argument of type 'string' is not "
            f"assignable to parameter of type '{ident}'."), f"type:{ident}"


def err_missing_import(rng, cause_id):
    """TS2304 cannot find name; each distinct cause_id => distinct missing import."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    mod = MODULES[cause_id % len(MODULES)]
    name = mod.split('/')[-1]
    return (f"{f}:{ln}:{col} - error TS2304: Cannot find name '{name}'. "
            f"Did you forget to import from '{mod}'?"), f"import:{mod}"


def err_null_access(rng, cause_id):
    """TS18047 possibly null; cause_id maps to the variable being accessed."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    ident = IDENTIFIERS[(cause_id + 3) % len(IDENTIFIERS)]
    return (f"{f}:{ln}:{col} - error TS18047: '{ident}' is possibly 'null'."
            ), f"null:{ident}"


def err_missing_prop(rng, cause_id):
    """TS2741 missing required property."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    ident = IDENTIFIERS[(cause_id + 5) % len(IDENTIFIERS)]
    prop = ['id', 'createdAt', 'status', 'token', 'email'][cause_id % 5]
    return (f"{f}:{ln}:{col} - error TS2741: Property '{prop}' is missing in "
            f"type but required in '{ident}'."), f"prop:{ident}.{prop}"


def err_unused_var(rng, cause_id):
    """TS6133 declared but never used."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    ident = IDENTIFIERS[(cause_id + 7) % len(IDENTIFIERS)]
    return (f"{f}:{ln}:{col} - error TS6133: '{ident}' is declared but its "
            f"value is never read."), f"unused:{ident}"


def err_no_overload(rng, cause_id):
    """TS2769 no overload matches; downstream of a type change => same root cause."""
    f = rng.choice(FILES)
    ln = rng.randint(5, 180)
    col = rng.randint(1, 40)
    ident = IDENTIFIERS[cause_id % len(IDENTIFIERS)]
    return (f"{f}:{ln}:{col} - error TS2769: No overload matches this call. "
            f"Overload 1 expected '{ident}' but got 'string'."), f"type:{ident}"


def err_test_failure(rng, cause_id):
    """Jest/vitest test failure; cause_id maps to the assertion contract."""
    suites = ['AuthFlow', 'OrderApi', 'UserModel', 'ValidatorUtil', 'DashboardPage']
    suite = suites[cause_id % len(suites)]
    case = ['returns 200 on success', 'rejects invalid input',
            'handles empty list', 'persists across refresh'][cause_id % 4]
    return (f"FAIL test/{suite.lower()}.test.ts > {suite} > {case}\n"
            f"  Expected: 200  Received: 500"), f"test:{suite}:{case}"


INDEPENDENT_POOL = [
    err_type_mismatch, err_missing_import, err_null_access,
    err_missing_prop, err_unused_var, err_test_failure,
]


def build_independent(rng, n_errors):
    """n_errors distinct root causes, no relationship between them."""
    chosen = rng.sample(INDEPENDENT_POOL, min(n_errors, len(INDEPENDENT_POOL)))
    # If we need more than pool size, pad by reusing generators but with new cause ids.
    while len(chosen) < n_errors:
        chosen.append(rng.choice(INDEPENDENT_POOL))
    lines = []
    causes = set()
    for i, gen in enumerate(chosen):
        line, cause = gen(rng, i * 11 + rng.randint(0, 3))
        # Ensure unique cause
        attempts = 0
        while cause in causes and attempts < 5:
            line, cause = gen(rng, i * 11 + rng.randint(0, 100))
            attempts += 1
        causes.add(cause)
        lines.append(line)
    return lines, causes


def build_chained(rng, n_errors):
    """n_errors distinct root causes but ordered: the earlier one, if fixed,
    would eliminate the later ones' symptoms. Diagnosing all still requires
    counting n_errors distinct root causes — this tests that the model doesn't
    collapse a chain into 'just the first one'."""
    # Seed with an initial type-level error then ripple downstream errors.
    base_id = rng.randint(0, 20)
    lines = []
    causes = set()

    # Root 1: renamed identifier or type
    l1, c1 = err_type_mismatch(rng, base_id)
    lines.append(l1); causes.add(c1)

    # Root 2: downstream null because the changed shape nullifies field
    l2, c2 = err_null_access(rng, base_id + 31)
    lines.append(l2); causes.add(c2)

    if n_errors >= 3:
        # Root 3: test suite breaks because both of the above leaked
        l3, c3 = err_test_failure(rng, base_id + 53)
        lines.append(l3); causes.add(c3)

    if n_errors >= 4:
        l4, c4 = err_missing_prop(rng, base_id + 71)
        lines.append(l4); causes.add(c4)

    if n_errors >= 5:
        l5, c5 = err_missing_import(rng, base_id + 89)
        lines.append(l5); causes.add(c5)

    return lines[:n_errors], causes


def build_redundant(rng, n_errors_actual):
    """n_errors_actual VISIBLE error LINES, but fewer distinct root causes.
    Model must not over-count. Strategy: duplicate one root cause across
    multiple files/lines."""
    # Pick 2 or 3 actual root causes (always fewer than line count) and scatter
    # them across n_errors_actual lines. Stratify so the count varies.
    if n_errors_actual <= 3:
        n_distinct = 2
    elif n_errors_actual == 4:
        n_distinct = rng.choice([2, 3])
    else:  # 5
        n_distinct = rng.choice([2, 3])
    generators = rng.sample([err_type_mismatch, err_no_overload, err_null_access,
                             err_missing_import, err_missing_prop], n_distinct)
    # Assign cause IDs per root cause
    cause_ids = [rng.randint(0, 20) for _ in range(n_distinct)]

    lines = []
    causes = set()
    for i in range(n_errors_actual):
        cidx = i % n_distinct
        gen = generators[cidx]
        # For the first occurrence of each root cause use its id; reuse the SAME id
        # for subsequent occurrences so cause keys collide.
        line, cause = gen(rng, cause_ids[cidx])
        # For type_mismatch + no_overload we intentionally chose generators whose
        # keys collide ("type:IDENT"), so repeat occurrences resolve to same cause.
        lines.append(line)
        causes.add(cause)
    rng.shuffle(lines)
    return lines, causes


# === Worked example generation ===
#
# Each study example shows:
#   1. A multi-error build output
#   2. The full enumeration of distinct root causes
#   3. The count
#
# The pattern being taught: ALWAYS enumerate every distinct error before
# proposing fixes, then collapse duplicates (same root cause) to get the count.

def _mk_example_output(rng, mode):
    """Return (output_text, distinct_count, enumeration_text)."""
    if mode == 'independent_errors':
        n = rng.randint(2, 4)
        lines, causes = build_independent(rng, n)
    elif mode == 'chained_errors':
        n = rng.randint(2, 4)
        lines, causes = build_chained(rng, n)
    else:  # redundant_errors
        n_visible = rng.randint(3, 5)
        lines, causes = build_redundant(rng, n_visible)

    header = "BUILD OUTPUT:\n"
    body = "\n".join(lines)
    output = header + body

    enum_lines = [f"  {i+1}. {c}" for i, c in enumerate(sorted(causes))]
    enumeration = ("Distinct root causes:\n" + "\n".join(enum_lines)
                   + f"\nCount of distinct root causes: {len(causes)}")
    return output, len(causes), enumeration


def format_example(rng, mode, idx):
    output, count, enumeration = _mk_example_output(rng, mode)
    text = (f"Example {idx}:\n{output}\n\nDiagnosis:\n{enumeration}")
    return text


def format_test_stimulus(rng, mode):
    output, count, _enum = _mk_example_output(rng, mode)
    stim = output + "\n\nHow many distinct root causes are there?"
    return stim, count


# === Dataset assembly ===

COMPLEXITY_LEVELS = ['independent_errors', 'chained_errors', 'redundant_errors']
EVIDENCE_LEVELS = [('few', 3), ('mid', 4), ('many', 5)]
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity in COMPLEXITY_LEVELS:
        for evidence_label, n_examples in EVIDENCE_LEVELS:
            for seed in range(SEEDS):
                # Deterministic seeding
                rng = random.Random(
                    seed * 10_000
                    + COMPLEXITY_LEVELS.index(complexity) * 100
                    + n_examples
                )

                # Build n_examples worked examples in the SAME complexity mode.
                examples = []
                for i in range(n_examples):
                    examples.append(format_example(rng, complexity, i + 1))
                material = "\n\n".join(examples)

                # Test stimulus — same complexity mode, new instance
                test_input, expected_count = format_test_stimulus(rng, complexity)

                difficulty_label = f"{complexity}_{evidence_label}"
                item_desc = (f"{complexity} ({evidence_label}={n_examples} "
                             f"examples, seed {seed})")

                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': complexity,
                    'evidence': evidence_label,
                    'n_examples': n_examples,
                    'difficulty_label': difficulty_label,
                    'material': material,
                    'test_input': test_input,
                    'expected': str(expected_count),
                    'item_desc': item_desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'batch_error_diagnosis_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'n_examples',
                   'expected', 'item_desc']].to_string(index=False))
