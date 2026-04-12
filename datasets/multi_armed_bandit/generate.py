#!/usr/bin/env python3
"""Generate the multi-armed bandit benchmark dataset.

Usage:
    python datasets/multi_armed_bandit/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/multi_armed_bandit/ -m "Regenerated"
"""

import os
import random

import pandas as pd


ARM_LABELS = ['A', 'B', 'C', 'D']


def generate_bandit_history(rng, num_arms, clarity, num_plays):
    """Generate a bandit scenario with controlled reward probabilities and a play history."""
    arms = ARM_LABELS[:num_arms]

    if clarity == 'clear':
        best_idx = rng.randint(0, num_arms - 1)
        probs = {}
        for i, arm in enumerate(arms):
            if i == best_idx:
                probs[arm] = rng.uniform(0.75, 0.90)
            else:
                probs[arm] = rng.uniform(0.10, 0.30)
    elif clarity == 'moderate':
        best_idx = rng.randint(0, num_arms - 1)
        probs = {}
        for i, arm in enumerate(arms):
            if i == best_idx:
                probs[arm] = rng.uniform(0.60, 0.75)
            else:
                probs[arm] = rng.uniform(0.25, 0.45)
    else:  # ambiguous
        base = rng.uniform(0.40, 0.55)
        best_idx = rng.randint(0, num_arms - 1)
        probs = {}
        for i, arm in enumerate(arms):
            if i == best_idx:
                probs[arm] = base + rng.uniform(0.05, 0.10)
            else:
                probs[arm] = base + rng.uniform(-0.05, 0.02)

    history = []
    for _ in range(num_plays):
        arm = rng.choice(arms)
        reward = 1 if rng.random() < probs[arm] else 0
        history.append((arm, reward))

    arm_rewards = {a: [] for a in arms}
    for arm, reward in history:
        arm_rewards[arm].append(reward)

    empirical_rates = {}
    for arm in arms:
        if arm_rewards[arm]:
            empirical_rates[arm] = sum(arm_rewards[arm]) / len(arm_rewards[arm])
        else:
            empirical_rates[arm] = 0.0

    best_arm = max(arms, key=lambda a: empirical_rates[a])

    return arms, probs, history, empirical_rates, best_arm


def format_history(arms, history):
    """Format play history as a readable string."""
    lines = []
    for i, (arm, reward) in enumerate(history, 1):
        outcome = 'WIN (reward 1)' if reward == 1 else 'LOSS (reward 0)'
        lines.append(f'  Round {i}: Chose {arm} -> {outcome}')
    return '\n'.join(lines)


NUM_ARMS = [2, 3, 4]
CLARITIES = ['clear', 'moderate', 'ambiguous']
HISTORY_LENGTHS = {2: 20, 3: 30, 4: 40}
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for num_arms in NUM_ARMS:
        for clarity in CLARITIES:
            for seed in range(SEEDS):
                rng = random.Random(seed * 100 + num_arms * 10)
                num_plays = HISTORY_LENGTHS[num_arms]
                arms, probs, history, empirical_rates, best_arm = generate_bandit_history(
                    rng, num_arms, clarity, num_plays)

                history_text = format_history(arms, history)
                arm_list = ', '.join(arms)
                difficulty_label = f'{num_arms}arms_{clarity}'

                material = (
                    f'You are playing a {num_arms}-armed bandit game with arms: {arm_list}.\n'
                    f'Each arm gives a reward of 1 (win) or 0 (loss) when pulled.\n'
                    f'Here is the history of {num_plays} plays:\n\n'
                    f'{history_text}\n'
                )

                prob_str = ', '.join(f'{a}={probs[a]:.2f}' for a in arms)
                emp_str = ', '.join(f'{a}={empirical_rates[a]:.2f}' for a in arms)

                rows.append({
                    'task_id': tid, 'seed': seed, 'num_arms': num_arms,
                    'clarity': clarity, 'difficulty_label': difficulty_label,
                    'material': material, 'test_input': material,
                    'expected': best_arm, 'item_desc': f'{num_arms}arms_{clarity}_s{seed}',
                    'true_probs': prob_str, 'empirical_rates': emp_str,
                    'num_plays': num_plays, 'arms': arm_list,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'multi_armed_bandit_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'item_desc']].to_string(index=False))
