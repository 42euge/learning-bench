#!/usr/bin/env python3
"""Generate the analogy completion benchmark dataset.

Usage:
    python datasets/analogy_completion/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/analogy_completion/ -m "Regenerated"
"""

import os
import random

import pandas as pd

# === Analogy generators: number-tuple transformations ===


def analogy_simple(seed):
    """1-feature: single arithmetic op on each element."""
    rng = random.Random(seed)
    op = rng.choice(['add', 'mul', 'swap'])
    k = rng.randint(2, 7)
    if op == 'add':
        fn = lambda t: (t[0]+k, t[1]+k, t[2]+k)
        desc = f'add {k} to each'
    elif op == 'mul':
        fn = lambda t: (t[0]*k, t[1]*k, t[2]*k)
        desc = f'multiply each by {k}'
    else:
        fn = lambda t: (t[2], t[1], t[0])
        desc = 'reverse order'
    return fn, desc


def analogy_moderate(seed):
    """2-feature: different ops per position."""
    rng = random.Random(seed)
    a_op = rng.randint(1, 5)
    b_op = rng.randint(2, 4)
    fn = lambda t: (t[0] + a_op, t[1] * b_op, t[2] - a_op)
    desc = f'(+{a_op}, *{b_op}, -{a_op})'
    return fn, desc


def analogy_complex(seed):
    """3-feature: cross-element dependencies."""
    rng = random.Random(seed)
    k = rng.randint(1, 3)
    mode = rng.choice(['sum', 'diff', 'mix'])
    if mode == 'sum':
        fn = lambda t: (t[0]+t[1], t[1]+t[2], t[0]+t[2]+k)
        desc = f'pairwise sums +{k}'
    elif mode == 'diff':
        fn = lambda t: (abs(t[0]-t[1]), abs(t[1]-t[2]), t[0]+t[1]+t[2])
        desc = 'diffs + total'
    else:
        fn = lambda t: (t[1]*k, t[2]+t[0], t[0]*t[1]%10)
        desc = f'mixed cross-element k={k}'
    return fn, desc


ANALOGY_FNS = {'simple': analogy_simple, 'moderate': analogy_moderate, 'complex': analogy_complex}

EVIDENCE = {'few': 3, 'mid': 5, 'many': 8}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}  # deterministic, no hash()
SEEDS = 3


def tuple_str(t):
    return f'({t[0]}, {t[1]}, {t[2]})'


def gen_tuples(rng, n):
    return [tuple(rng.randint(1, 9) for _ in range(3)) for _ in range(n)]


def generate_dataset():
    rows = []
    tid = 0
    for complexity, afn in ANALOGY_FNS.items():
        for ev_label, n_pairs in EVIDENCE.items():
            for seed in range(SEEDS):
                fn, desc = afn(seed * 100)
                rng = random.Random(seed * 13 + EVIDENCE_SEED[ev_label])
                tuples = gen_tuples(rng, n_pairs + 1)
                ex_tuples, test_t = tuples[:n_pairs], tuples[n_pairs]
                material = '\n'.join(f'{tuple_str(t)} -> {tuple_str(fn(t))}' for t in ex_tuples)
                expected_result = fn(test_t)
                expected = tuple_str(expected_result)
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'evidence': ev_label, 'difficulty_label': label,
                    'material': material, 'test_input': tuple_str(test_t),
                    'expected': expected, 'item_desc': desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'analogy_completion_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
