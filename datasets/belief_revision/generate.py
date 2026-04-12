#!/usr/bin/env python3
"""Generate the belief revision benchmark dataset.

Usage:
    python datasets/belief_revision/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/belief_revision/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Belief revision: constraint satisfaction with updates ===

def gen_simple(seed, strength):
    """Simple: find X given numeric constraints."""
    rng = random.Random(seed)
    target_initial = rng.randint(10, 50)
    lo = target_initial - rng.randint(1, 3)
    hi = target_initial + rng.randint(1, 3)
    parity = 'even' if target_initial % 2 == 0 else 'odd'

    initial = f"Find X where: X > {lo}, X < {hi}, X is {parity}."

    if strength == 'weak':
        new_target = target_initial + (2 if target_initial % 2 == 0 else 2)
        update = f"Additional constraint: X > {target_initial}."
    elif strength == 'moderate':
        new_target = rng.randint(60, 90)
        new_parity = 'even' if new_target % 2 == 0 else 'odd'
        update = f"CORRECTION: The range was wrong. X > {new_target - 2}, X < {new_target + 2}, X is {new_parity}."
    else:  # strong
        new_target = rng.randint(60, 90)
        new_parity = 'even' if new_target % 2 == 0 else 'odd'
        update = f"DISREGARD previous constraints. New constraints: X > {new_target - 1}, X < {new_target + 1}, X is {new_parity}."

    return initial, update, str(target_initial), str(new_target), f'simple_{strength}'


def gen_chain(seed, strength):
    """Causal chain: A causes B causes C, then A changes."""
    rng = random.Random(seed)
    people = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank']
    p = rng.sample(people, 4)

    initial = f"{p[0]} gave a book to {p[1]}. {p[1]} always shares books with {p[2]}. Who has the book?"
    initial_answer = p[2]

    if strength == 'weak':
        update = f"Actually, {p[1]} kept the book this time."
        new_answer = p[1]
    elif strength == 'moderate':
        update = f"Correction: {p[0]} gave the book to {p[3]}, not {p[1]}. {p[3]} always shares with {p[2]}."
        new_answer = p[2]
    else:
        update = f"Correction: {p[0]} gave the book to {p[3]}, not {p[1]}. {p[3]} never shares books."
        new_answer = p[3]

    return initial, update, initial_answer, new_answer, f'chain_{strength}'


def gen_nested(seed, strength):
    """Nested reasoning: if-then chains that get overridden."""
    rng = random.Random(seed)
    colors = ['red', 'blue', 'green', 'yellow']
    c = rng.sample(colors, 4)

    initial = (f"Rule 1: If the light is {c[0]}, press button A. "
               f"Rule 2: If the light is {c[1]}, press button B. "
               f"Rule 3: If the light is {c[2]}, press button C. "
               f"The light is {c[0]}. What button do you press?")
    initial_answer = 'A'

    if strength == 'weak':
        update = f"Addendum: Rule 1 is suspended today. Default to button D."
        new_answer = 'D'
    elif strength == 'moderate':
        update = f"Correction: The light is actually {c[1]}, not {c[0]}."
        new_answer = 'B'
    else:
        update = f"OVERRIDE: The light is {c[2]}. Also, Rule 3 now maps to button A instead of C."
        new_answer = 'A'

    return initial, update, initial_answer, new_answer, f'nested_{strength}'


BELIEF_FNS = {'simple': gen_simple, 'chain': gen_chain, 'nested': gen_nested}
STRENGTHS = ['weak', 'moderate', 'strong']
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity, bfn in BELIEF_FNS.items():
        for strength in STRENGTHS:
            for seed in range(SEEDS):
                initial, update, old_answer, new_answer, desc = bfn(seed * 100, strength)
                material = f"INITIAL EVIDENCE:\n{initial}\n\nNEW EVIDENCE:\n{update}"
                label = f'{complexity}_{strength}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'evidence': strength, 'difficulty_label': label,
                    'material': material, 'test_input': initial,
                    'expected': new_answer.lower(), 'item_desc': desc,
                    'initial_evidence': initial, 'update_evidence': update,
                    'old_answer': old_answer,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'belief_revision_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'item_desc']].to_string(index=False))
