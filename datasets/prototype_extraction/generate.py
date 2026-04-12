#!/usr/bin/env python3
"""Generate the prototype extraction benchmark dataset.

Usage:
    python datasets/prototype_extraction/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/prototype_extraction/ -m "Regenerated"
"""

import json
import os
import random

import pandas as pd


FEATURE_NAMES = ['horn_length', 'wing_span', 'tail_length', 'spots', 'weight']
CATEGORY_NAMES = ['Zorplings', 'Minkles', 'Quibbles']

PROTOTYPES = {
    'Zorplings': {'horn_length': 8, 'wing_span': 9, 'tail_length': 3, 'spots': 2, 'weight': 7},
    'Minkles':   {'horn_length': 3, 'wing_span': 2, 'tail_length': 8, 'spots': 9, 'weight': 4},
    'Quibbles':  {'horn_length': 5, 'wing_span': 5, 'tail_length': 5, 'spots': 5, 'weight': 5},
}

OVERLAP_NOISE = {'low': 1, 'medium': 2, 'high': 3}


def generate_creature(prototype, noise, rng):
    """Generate a creature by adding noise to a prototype."""
    creature = {}
    for feat in FEATURE_NAMES:
        val = prototype[feat] + rng.randint(-noise, noise)
        creature[feat] = max(1, min(10, val))
    return creature


def creature_str(creature):
    """Format creature features as a readable string."""
    parts = [f'{feat}={creature[feat]}' for feat in FEATURE_NAMES]
    return ', '.join(parts)


def euclidean_dist(a, b):
    """Euclidean distance between two creatures in feature space."""
    return sum((a[f] - b[f]) ** 2 for f in FEATURE_NAMES) ** 0.5


def classify_by_prototype(creature):
    """Classify a creature by nearest prototype (ground truth)."""
    best_cat = None
    best_dist = float('inf')
    for cat, proto in PROTOTYPES.items():
        d = euclidean_dist(creature, proto)
        if d < best_dist:
            best_dist = d
            best_cat = cat
    return best_cat


def generate_test_creature(target_cat, noise, rng):
    """Generate a test creature that is unambiguously closest to target_cat prototype."""
    for _ in range(100):
        creature = generate_creature(PROTOTYPES[target_cat], noise, rng)
        if classify_by_prototype(creature) == target_cat:
            return creature
    return dict(PROTOTYPES[target_cat])


EVIDENCE = {'few': 4, 'mid': 8, 'many': 12}
# Deterministic integer mappings replacing hash()
OVERLAP_SEED = {'low': 0, 'medium': 1, 'high': 2}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for overlap_label, noise in OVERLAP_NOISE.items():
        for ev_label, n_ex_per_cat in EVIDENCE.items():
            for seed in range(SEEDS):
                rng = random.Random(seed * 1000 + OVERLAP_SEED[overlap_label] * 500 + EVIDENCE_SEED[ev_label] * 200)

                examples = []
                for cat in CATEGORY_NAMES:
                    proto = PROTOTYPES[cat]
                    for _ in range(n_ex_per_cat):
                        creature = generate_creature(proto, noise, rng)
                        examples.append((creature, cat))

                rng.shuffle(examples)

                target_cat = CATEGORY_NAMES[seed % len(CATEGORY_NAMES)]
                test_creature = generate_test_creature(target_cat, noise, rng)
                expected = classify_by_prototype(test_creature)

                material_lines = []
                for creature, cat in examples:
                    material_lines.append(f'{creature_str(creature)} -> {cat}')
                material = '\n'.join(material_lines)

                n_total = n_ex_per_cat * len(CATEGORY_NAMES)
                label = f'{overlap_label}_{ev_label}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'overlap': overlap_label,
                    'evidence': ev_label, 'difficulty_label': label,
                    'n_examples': n_total, 'noise': noise,
                    'material': material, 'test_input': creature_str(test_creature),
                    'expected': expected,
                    'categories': json.dumps(CATEGORY_NAMES),
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'prototype_extraction_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
