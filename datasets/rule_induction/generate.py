#!/usr/bin/env python3
"""Generate the rule induction benchmark dataset.

Usage:
    python datasets/rule_induction/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/rule_induction/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Rule engine: composable string transformations ===

def op_caesar(s, k):
    return ''.join(chr((ord(c) - 97 + k) % 26 + 97) if c.isalpha() else c for c in s)

def op_reverse(s, _):
    return s[::-1]

def op_swap_pairs(s, _):
    r = list(s)
    for i in range(0, len(r) - 1, 2):
        r[i], r[i + 1] = r[i + 1], r[i]
    return ''.join(r)

def op_vowel_shift(s, _):
    m = {'a': 'e', 'e': 'i', 'i': 'o', 'o': 'u', 'u': 'a'}
    return ''.join(m.get(c, c) for c in s)

def op_rotate_half(s, _):
    mid = len(s) // 2
    return s[mid:] + s[:mid]

def op_consonant_shift(s, k):
    cons = 'bcdfghjklmnpqrstvwxyz'
    return ''.join(cons[(cons.index(c) + k) % len(cons)] if c in cons else c for c in s)


OPERATIONS = [
    ('caesar', op_caesar), ('reverse', op_reverse), ('swap_pairs', op_swap_pairs),
    ('vowel_shift', op_vowel_shift), ('rotate_half', op_rotate_half),
    ('consonant_shift', op_consonant_shift),
]

WORDS = [
    'planet', 'bridge', 'castle', 'forest', 'garden', 'hunter', 'jungle', 'knight',
    'lemon', 'market', 'orange', 'purple', 'silver', 'tunnel', 'winter', 'broken',
    'candle', 'desert', 'falcon', 'gentle', 'harbor', 'insect', 'jumble', 'kitten',
    'luster', 'mangle', 'nickel', 'oyster', 'pencil', 'quiver', 'rattle', 'simple',
    'temple', 'velvet', 'wander', 'basket', 'coffee', 'donkey',
]


def gen_rule(seed, n_ops):
    rng = random.Random(seed)
    chosen = rng.sample(OPERATIONS, n_ops)
    params = [rng.randint(1, 5) for _ in range(n_ops)]
    return [(n, f, p) for (n, f), p in zip(chosen, params)]


def apply_rule(word, rule):
    r = word.lower()
    for _, fn, p in rule:
        r = fn(r, p)
    return r


def rule_desc(rule):
    return ' -> '.join(f'{n}({p})' for n, _, p in rule)


# === Dataset: complexity x evidence x seeds ===
COMPLEXITY = [1, 2, 3]
EVIDENCE = [2, 4, 8]
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for n_ops in COMPLEXITY:
        for n_ex in EVIDENCE:
            for seed in range(SEEDS):
                rule = gen_rule(seed * 100 + n_ops * 10 + n_ex, n_ops)
                rng = random.Random(seed * 7 + n_ops * 3 + n_ex)
                words = rng.sample(WORDS, n_ex + 1)
                ex_words, tw = words[:n_ex], words[n_ex]
                material = '\n'.join(f'"{w}" -> "{apply_rule(w, rule)}"' for w in ex_words)
                expected = apply_rule(tw, rule)
                label = f'{n_ops}op_{n_ex}ex'
                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': f'{n_ops}_ops',
                    'evidence': f'{n_ex}_examples',
                    'difficulty_label': label,
                    'material': material,
                    'test_input': tw,
                    'expected': expected,
                    'item_desc': rule_desc(rule),
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'rule_induction_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
