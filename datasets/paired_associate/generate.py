#!/usr/bin/env python3
"""Generate the paired associate benchmark dataset.

Usage:
    python datasets/paired_associate/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/paired_associate/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Novel vocabulary generation ===

ONSETS = ['bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 'pl', 'pr', 'sk', 'sl', 'sn',
          'sp', 'st', 'sw', 'tr', 'tw', 'wr',
          'b', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'z']
VOWELS = ['a', 'e', 'i', 'o', 'u', 'ai', 'ei', 'ou', 'au', 'oi']
CODAS = ['k', 'n', 'm', 'p', 't', 'l', 's', 'x', 'b', 'd', 'sh', 'ng', 'ff', 'll', 'rn', 'nt', 'mp']

OBJECTS = ['apple', 'hammer', 'river', 'cloud', 'feather', 'crystal', 'lantern', 'rope',
           'wheel', 'mirror', 'basket', 'candle', 'anchor', 'pebble', 'arrow', 'drum']
COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'silver', 'golden']
SIZES = ['tiny', 'small', 'large', 'enormous', 'thin', 'wide', 'tall', 'short']
ACTIONS = ['running', 'spinning', 'falling', 'glowing', 'melting', 'growing', 'floating', 'breaking']
MODIFIERS = ['very', 'not', 'slightly', 'extremely', 'almost', 'barely']


def gen_nonsense_word(rng, min_syl=2, max_syl=3):
    """Generate a pronounceable nonsense word."""
    n_syl = rng.randint(min_syl, max_syl)
    word = ''
    for i in range(n_syl):
        word += rng.choice(ONSETS) + rng.choice(VOWELS)
        if i == n_syl - 1 or rng.random() < 0.3:
            word += rng.choice(CODAS)
    return word


def gen_vocab_simple(seed, n_pairs):
    """Simple: word -> single concrete meaning (1:1 arbitrary mapping).

    The test pair IS included in the material — the task is recall, not generalization.
    We test a pair from the second half of the list to avoid primacy bias.
    """
    rng = random.Random(seed)
    meanings_pool = OBJECTS + COLORS + ACTIONS
    rng.shuffle(meanings_pool)
    words = []
    seen = set()
    while len(words) < n_pairs:
        w = gen_nonsense_word(rng)
        if w not in seen and len(w) >= 4:
            seen.add(w)
            words.append(w)
    meanings = meanings_pool[:n_pairs]
    vocab = list(zip(words, meanings))
    rng.shuffle(vocab)
    # Test a pair from the second half (avoids primacy/recency at edges)
    test_idx = n_pairs // 2 + rng.randint(0, n_pairs // 2 - 1)
    test_word, test_meaning = vocab[test_idx]
    study_pairs = list(vocab)  # all pairs shown in material
    return study_pairs, test_word, test_meaning, None, None, 'simple 1:1 mapping'


def gen_vocab_compound(seed, n_pairs):
    """Compound: word -> compound meaning (word = size + color).

    The test pair IS included in the material — the task is recall of a two-part meaning.
    """
    rng = random.Random(seed)
    words = []
    seen = set()
    while len(words) < n_pairs:
        w = gen_nonsense_word(rng)
        if w not in seen and len(w) >= 4:
            seen.add(w)
            words.append(w)
    colors_pool = list(COLORS); rng.shuffle(colors_pool)
    sizes_pool = list(SIZES); rng.shuffle(sizes_pool)
    meanings = []
    for i in range(n_pairs):
        meanings.append(f'{sizes_pool[i % len(sizes_pool)]} {colors_pool[i % len(colors_pool)]}')
    vocab = list(zip(words, meanings))
    rng.shuffle(vocab)
    # Test a pair from the second half
    test_idx = n_pairs // 2 + rng.randint(0, n_pairs // 2 - 1)
    test_word, test_meaning = vocab[test_idx]
    study_pairs = list(vocab)  # all pairs shown in material
    return study_pairs, test_word, test_meaning, None, None, 'compound (size+color)'


def gen_vocab_relational(seed, n_pairs):
    """Relational: modifier words change base-word meanings.

    The test is a novel composition (modifier-base) NOT shown in the material,
    but both the modifier and the base ARE shown so the model can derive the answer.
    We guarantee the test's components are always included.
    """
    rng = random.Random(seed)
    all_words = []
    seen = set()
    while len(all_words) < n_pairs + 4:
        w = gen_nonsense_word(rng)
        if w not in seen and len(w) >= 4:
            seen.add(w)
            all_words.append(w)
    n_base = max(3, n_pairs // 2)
    n_mod = max(2, n_pairs - n_base)
    base_words = all_words[:n_base]
    mod_words = all_words[n_base:n_base + n_mod]
    base_pool = list(COLORS[:n_base + 2]); rng.shuffle(base_pool)
    base_map = {w: base_pool[i] for i, w in enumerate(base_words)}
    mod_pool = list(MODIFIERS[:n_mod + 2]); rng.shuffle(mod_pool)
    mod_map = {w: mod_pool[i] for i, w in enumerate(mod_words)}

    # Generate all possible compositions and pick the test composition
    composed = []
    for mw in mod_words:
        for bw in base_words:
            composed.append((f'{mw}-{bw}', f'{mod_map[mw]} {base_map[bw]}', mw, bw))
    rng.shuffle(composed)
    test_word, test_meaning, test_mod, test_base = composed[0]

    # Build study pairs: MUST include the test's modifier and base definitions
    required = [
        (test_base, base_map[test_base]),        # base word definition
        (f'{test_mod}-', f'{mod_map[test_mod]} (modifier)'),  # modifier definition
    ]

    # Add other base and modifier definitions
    other_pairs = []
    for w, m in base_map.items():
        if w != test_base:
            other_pairs.append((w, m))
    for w, m in mod_map.items():
        if w != test_mod:
            other_pairs.append((f'{w}-', f'{m} (modifier)'))

    # Add some example compositions (not the test one) to show the pattern
    example_compositions = [(w, m) for w, m, _, _ in composed[1:]]
    other_pairs.extend(example_compositions[:3])
    rng.shuffle(other_pairs)

    # Fill remaining slots with other pairs
    study_pairs = list(required)
    remaining_slots = n_pairs - len(study_pairs)
    study_pairs.extend(other_pairs[:remaining_slots])
    rng.shuffle(study_pairs)

    desc = 'relational (modifier+base composition)'
    return study_pairs, test_word, test_meaning, None, None, desc


VOCAB_FNS = {'simple': gen_vocab_simple, 'compound': gen_vocab_compound, 'relational': gen_vocab_relational}
EVIDENCE = {'few': 4, 'mid': 8, 'many': 12}
# Deterministic integer mapping replacing hash(ev_label) % 50
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity, vocab_fn in VOCAB_FNS.items():
        for ev_label, n_pairs in EVIDENCE.items():
            for seed in range(SEEDS):
                study_pairs, test_word, test_meaning, rev_word, rev_meaning, desc = vocab_fn(
                    seed * 100 + EVIDENCE_SEED[ev_label], n_pairs)
                material = '\n'.join(f'  {w} = "{m}"' for w, m in study_pairs)
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'evidence': ev_label, 'difficulty_label': label,
                    'material': material, 'test_input': test_word,
                    'expected': test_meaning, 'item_desc': desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'paired_associate_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
