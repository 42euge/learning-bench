#!/usr/bin/env python3
"""Generate the category learning benchmark dataset.

Usage:
    python datasets/category_learning/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/category_learning/ -m "Regenerated"
"""

import json
import os
import random

import pandas as pd

# === Feature-based classification ===

SHAPES = ['circle', 'square', 'triangle', 'diamond', 'hexagon', 'star']
COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
SIZES = ['tiny', 'small', 'medium', 'large', 'huge']
PATTERNS = ['solid', 'striped', 'dotted', 'checkered', 'plaid']

FEATURE_POOLS = {'shape': SHAPES, 'color': COLORS, 'size': SIZES, 'pattern': PATTERNS}


def make_item(rng):
    return {
        'shape': rng.choice(SHAPES),
        'color': rng.choice(COLORS),
        'size': rng.choice(SIZES),
        'pattern': rng.choice(PATTERNS),
    }


def item_str(it):
    return f"{it['size']} {it['color']} {it['pattern']} {it['shape']}"


def rule_single(seed):
    rng = random.Random(seed)
    feat = rng.choice(['shape', 'color', 'size', 'pattern'])
    pool = FEATURE_POOLS[feat]
    split = set(rng.sample(pool, len(pool) // 2))

    def clf(it):
        return 'A' if it[feat] in split else 'B'

    return clf, f'{feat} in {sorted(split)} -> A'


def rule_two(seed):
    rng = random.Random(seed)
    f1, f2 = rng.sample(['shape', 'color', 'size', 'pattern'], 2)
    p1 = FEATURE_POOLS[f1]
    p2 = FEATURE_POOLS[f2]
    v1 = set(rng.sample(p1, max(1, len(p1) // 2)))
    v2 = set(rng.sample(p2, max(1, len(p2) // 2)))

    def clf(it):
        c1, c2 = it[f1] in v1, it[f2] in v2
        if c1 and c2:
            return 'A'
        elif c1:
            return 'B'
        else:
            return 'C'

    return clf, f'{f1}+{f2} conjunction'


def rule_conditional(seed):
    rng = random.Random(seed)
    f1, f2, f3 = rng.sample(['shape', 'color', 'size', 'pattern'], 3)
    p1 = FEATURE_POOLS[f1]
    p2 = FEATURE_POOLS[f2]
    p3 = FEATURE_POOLS[f3]
    gate = set(rng.sample(p1, max(1, len(p1) // 2)))
    ba = set(rng.sample(p2, max(1, len(p2) // 2)))
    bb = set(rng.sample(p3, max(1, len(p3) // 2)))

    def clf(it):
        if it[f1] in gate:
            return 'A' if it[f2] in ba else 'B'
        else:
            return 'C' if it[f3] in bb else 'D'

    return clf, f'if {f1} in gate -> {f2}, else -> {f3}'


RULE_FNS = {'single': rule_single, 'two_feat': rule_two, 'conditional': rule_conditional}
EVIDENCE = {'few': 4, 'mid': 6, 'many': 10}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}  # deterministic, no hash()
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity, rule_fn in RULE_FNS.items():
        for ev_label, n_ex in EVIDENCE.items():
            for seed in range(SEEDS):
                clf, desc = rule_fn(seed * 100)
                rng = random.Random(seed * 11 + 7 + EVIDENCE_SEED[ev_label])
                items = [make_item(rng) for _ in range(200)]
                labeled = [(it, clf(it)) for it in items]
                examples = labeled[:n_ex]
                test_it, test_cat = labeled[n_ex]
                material = '\n'.join(
                    f'{item_str(it)} -> Category {cat}' for it, cat in examples
                )
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': complexity,
                    'evidence': ev_label,
                    'difficulty_label': label,
                    'material': material,
                    'test_input': item_str(test_it),
                    'expected': test_cat,
                    'item_desc': desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'category_learning_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
