#!/usr/bin/env python3
"""Generate the sequence extrapolation benchmark dataset.

Usage:
    python datasets/sequence_extrapolation/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/sequence_extrapolation/ -m "Regenerated"
"""

import os
import random

import pandas as pd

# === Sequence generators ===

COMPLEXITY_SEED = {'simple': 0, 'moderate': 1, 'complex': 2}  # deterministic, no hash()


def seq_linear(seed, n):
    rng = random.Random(seed)
    a = rng.randint(2, 9)
    b = rng.randint(-5, 15)
    return [a * i + b for i in range(n)], f'{a}*i+{b}'


def seq_alternating(seed, n):
    rng = random.Random(seed)
    start = rng.randint(1, 10)
    a = rng.randint(2, 7)
    b = rng.randint(2, 7)
    while b == a:
        b = rng.randint(2, 7)
    seq = [start]
    for i in range(1, n):
        seq.append(seq[-1] + (a if i % 2 == 0 else b))
    return seq, f'alt +{a}/+{b}'


def seq_quadratic(seed, n):
    rng = random.Random(seed)
    a = rng.randint(1, 4)
    b = rng.randint(-3, 5)
    c = rng.randint(0, 10)
    return [a * i * i + b * i + c for i in range(n)], f'{a}i^2+{b}i+{c}'


def seq_fibonacci(seed, n):
    rng = random.Random(seed)
    a, b = rng.randint(1, 5), rng.randint(1, 5)
    c = rng.randint(0, 3)
    seq = [a, b]
    for _ in range(n - 2):
        seq.append(seq[-1] + seq[-2] + c)
    return seq, f'fib+{c}({a},{b})'


def seq_geometric(seed, n):
    rng = random.Random(seed)
    start = rng.randint(1, 5)
    r = rng.choice([2, 3])
    d = rng.randint(-3, 5)
    seq = [start]
    for _ in range(n - 1):
        seq.append(seq[-1] * r + d)
    return seq, f'f(i)=f(i-1)*{r}+{d}'


def seq_conditional(seed, n):
    rng = random.Random(seed)
    start = rng.randint(1, 8)
    a = rng.randint(3, 7)
    b = rng.randint(1, 4)
    seq = [start]
    for _ in range(n - 1):
        if seq[-1] % 2 == 0:
            seq.append(seq[-1] + a)
        else:
            seq.append(seq[-1] * 2 - b)
    return seq, f'even:+{a},odd:*2-{b}'


FAMILIES = {
    'simple': [seq_linear, seq_alternating],
    'moderate': [seq_quadratic, seq_fibonacci],
    'complex': [seq_geometric, seq_conditional],
}

TERMS_SHOWN = {'low': 5, 'mid': 7, 'high': 10}
TOTAL = 12
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity, fns in FAMILIES.items():
        for ev_label, n_shown in TERMS_SHOWN.items():
            for seed in range(SEEDS):
                fn = fns[seed % len(fns)]
                seq, desc = fn(seed * 100 + COMPLEXITY_SEED[complexity], TOTAL)
                shown = seq[:n_shown]
                target = seq[n_shown]
                material = ', '.join(str(x) for x in shown)
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'evidence': ev_label, 'difficulty_label': label,
                    'material': material, 'test_input': f'next after [{material}]',
                    'expected': str(target), 'item_desc': desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'sequence_extrapolation_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'item_desc']].to_string(index=False))
