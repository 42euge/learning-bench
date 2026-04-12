#!/usr/bin/env python3
"""Generate the trace-based imitation benchmark dataset.

Usage:
    python datasets/trace_based_imitation/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/trace_based_imitation/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Novel procedure definitions ===
# These are invented algorithms that do NOT correspond to any standard named algorithm.
# Each takes a list of integers and returns a single integer via deterministic steps.

# --- SIMPLE (1-step) procedures ---

def zigzag_sum(nums):
    """Add odd-indexed elements, subtract even-indexed elements, multiply by count."""
    total = 0
    for i, v in enumerate(nums):
        if i % 2 == 1:
            total += v
        else:
            total -= v
    result = total * len(nums)
    return result, [
        f"For each element: subtract if even-indexed, add if odd-indexed -> running total = {total}",
        f"Multiply by count of elements ({len(nums)}) -> {total} * {len(nums)} = {result}",
    ]


def mirror_diff(nums):
    """Pair first with last, second with second-to-last, etc. Sum absolute differences, add middle if odd length."""
    pairs = []
    total = 0
    n = len(nums)
    for i in range(n // 2):
        d = abs(nums[i] - nums[n - 1 - i])
        pairs.append(f"|{nums[i]} - {nums[n - 1 - i]}| = {d}")
        total += d
    middle_note = ""
    if n % 2 == 1:
        mid = nums[n // 2]
        total += mid
        middle_note = f", add middle element {mid}"
    result = total
    return result, [
        f"Pair from outside in and take absolute differences: {'; '.join(pairs)}",
        f"Sum of differences{middle_note} = {result}",
    ]


def triangle_count(nums):
    """Square each element, sum digits of each square, then take alternating sum of those digit-sums."""
    squares = [v * v for v in nums]
    digit_sums = [sum(int(d) for d in str(s)) for s in squares]
    alt_sum = 0
    for i, ds in enumerate(digit_sums):
        if i % 2 == 0:
            alt_sum += ds
        else:
            alt_sum -= ds
    return alt_sum, [
        f"Square each element: {nums} -> {squares}",
        f"Sum digits of each square: {squares} -> {digit_sums}",
        f"Alternating sum (+/-) of digit-sums: {' + '.join(str(ds) if i % 2 == 0 else f'(- {ds})' for i, ds in enumerate(digit_sums))} = {alt_sum}",
    ]


# --- MEDIUM (2-step) procedures ---

def spiral_crunch(nums):
    """Step 1: Reverse every other pair. Step 2: Cumulative sum, return last."""
    transformed = list(nums)
    for i in range(0, len(transformed) - 1, 4):
        transformed[i], transformed[i + 1] = transformed[i + 1], transformed[i]
    cumsum = []
    running = 0
    for v in transformed:
        running += v
        cumsum.append(running)
    result = cumsum[-1] if cumsum else 0
    return result, [
        f"Swap every other pair (positions 0-1, 4-5, ...): {list(nums)} -> {transformed}",
        f"Cumulative sum: {transformed} -> {cumsum}",
        f"Final value = {result}",
    ]


def wave_hash(nums):
    """Step 1: Sort, interleave min/max. Step 2: Multiply adjacent pairs, sum products."""
    s = sorted(nums)
    interleaved = []
    lo, hi = 0, len(s) - 1
    while lo <= hi:
        interleaved.append(s[lo])
        if lo != hi:
            interleaved.append(s[hi])
        lo += 1
        hi -= 1
    products = []
    for i in range(0, len(interleaved) - 1, 2):
        products.append(interleaved[i] * interleaved[i + 1])
    result = sum(products)
    return result, [
        f"Sort and interleave min/max: {list(nums)} -> sorted {s} -> interleaved {interleaved}",
        f"Multiply adjacent pairs: {[f'{interleaved[i]}*{interleaved[i + 1]}' for i in range(0, len(interleaved) - 1, 2)]} = {products}",
        f"Sum of products = {result}",
    ]


def cascade_mod(nums):
    """Step 1: Replace each element with (element * its 1-based position) mod 17.
       Step 2: XOR all results together, then multiply by count."""
    mod_vals = [(v * (i + 1)) % 17 for i, v in enumerate(nums)]
    xor_result = 0
    for v in mod_vals:
        xor_result ^= v
    result = xor_result * len(nums)
    return result, [
        f"Multiply each by its 1-based position, mod 17: {[f'{v}*{i + 1}%17={m}' for i, (v, m) in enumerate(zip(nums, mod_vals))]}",
        f"XOR all results: {' ^ '.join(str(v) for v in mod_vals)} = {xor_result}",
        f"Multiply by count ({len(nums)}): {xor_result} * {len(nums)} = {result}",
    ]


# --- COMPLEX (3-step with conditionals) procedures ---

def branch_fold(nums):
    """If first element > 5: fold left with multiply (capped at 999), else fold right with add.
       Then negate odd-positioned results. Finally, sum all."""
    if nums[0] > 5:
        branch = "left-multiply"
        acc = nums[0]
        intermediates = [acc]
        for v in nums[1:]:
            acc = (acc * v) % 999
            intermediates.append(acc)
    else:
        branch = "right-add"
        acc = nums[-1]
        intermediates = [0] * len(nums)
        intermediates[-1] = acc
        for i in range(len(nums) - 2, -1, -1):
            acc = acc + nums[i]
            intermediates[i] = acc
    negated = [(-v if i % 2 == 1 else v) for i, v in enumerate(intermediates)]
    result = sum(negated)
    return result, [
        f"First element = {nums[0]}, {'> 5' if nums[0] > 5 else '<= 5'} -> branch: {branch}",
        f"Fold to get intermediates: {intermediates}",
        f"Negate odd-indexed positions: {intermediates} -> {negated}",
        f"Sum all: {' + '.join(str(v) for v in negated)} = {result}",
    ]


def pivot_weave(nums):
    """Step 1: Find median. Split into above/below median.
       Step 2: Interleave below and above lists, padding shorter with 0.
       Step 3: If length is even, sum all; if odd, alternating sum."""
    s = sorted(nums)
    median = s[len(s) // 2]
    below = [x for x in nums if x < median]
    above = [x for x in nums if x > median]
    at_med = [x for x in nums if x == median]
    below = below + at_med
    woven = []
    for i in range(max(len(below), len(above))):
        if i < len(below):
            woven.append(below[i])
        else:
            woven.append(0)
        if i < len(above):
            woven.append(above[i])
        else:
            woven.append(0)
    if len(nums) % 2 == 0:
        result = sum(woven)
        step3 = f"Length {len(nums)} is even -> plain sum of woven: {result}"
    else:
        result = sum(v if i % 2 == 0 else -v for i, v in enumerate(woven))
        step3 = f"Length {len(nums)} is odd -> alternating sum of woven: {result}"
    return result, [
        f"Sort {list(nums)} -> {s}, median = {median}. Below/at median: {below}, above: {above}",
        f"Interleave (pad with 0): {woven}",
        step3,
    ]


def chain_gate(nums):
    """Step 1: Compute pairwise sums of consecutive elements.
       Step 2: For each pairwise sum, if > 10 keep it, else replace with 1.
       Step 3: Product of all gated values, mod 1000, then subtract first original element."""
    pair_sums = [nums[i] + nums[i + 1] for i in range(len(nums) - 1)]
    gated = [v if v > 10 else 1 for v in pair_sums]
    product = 1
    for v in gated:
        product *= v
    product_mod = product % 1000
    result = product_mod - nums[0]
    return result, [
        f"Pairwise sums of consecutive elements: {[f'{nums[i]}+{nums[i + 1]}={pair_sums[i]}' for i in range(len(pair_sums))]}",
        f"Gate: keep if >10, else replace with 1: {pair_sums} -> {gated}",
        f"Product mod 1000: {'*'.join(str(v) for v in gated)} = {product} mod 1000 = {product_mod}",
        f"Subtract first original element ({nums[0]}): {product_mod} - {nums[0]} = {result}",
    ]


# === Procedure registry ===
PROCEDURES = {
    'simple': [
        ('zigzag_sum', zigzag_sum, "Zigzag Sum: subtract even-indexed, add odd-indexed, multiply by count"),
        ('mirror_diff', mirror_diff, "Mirror Diff: pair outside-in, sum absolute differences, add middle if odd"),
        ('triangle_count', triangle_count, "Triangle Count: square each, digit-sum each square, alternating sum"),
    ],
    'medium': [
        ('spiral_crunch', spiral_crunch, "Spiral Crunch: swap every other pair, then cumulative sum"),
        ('wave_hash', wave_hash, "Wave Hash: sort-interleave min/max, multiply adjacent pairs, sum"),
        ('cascade_mod', cascade_mod, "Cascade Mod: multiply by position mod 17, XOR all, multiply by count"),
    ],
    'complex': [
        ('branch_fold', branch_fold, "Branch Fold: conditional fold direction, negate odd positions, sum"),
        ('pivot_weave', pivot_weave, "Pivot Weave: split by median, interleave, conditional sum"),
        ('chain_gate', chain_gate, "Chain Gate: pairwise sums, gate >10, product mod 1000, subtract first"),
    ],
}

# === Dataset parameters ===
COMPLEXITY_LEVELS = ['simple', 'medium', 'complex']
TRACE_COUNTS = [2, 3, 4]
SEEDS = 3


def generate_input(rng, length=5):
    """Generate a random list of integers for procedure input."""
    return [rng.randint(1, 9) for _ in range(length)]


def format_trace(inputs, fn):
    """Generate a full worked trace: input -> step1 -> step2 -> ... -> output."""
    result, steps = fn(inputs)
    trace = f"Input: {inputs}\n"
    for i, step in enumerate(steps, 1):
        trace += f"  Step {i}: {step}\n"
    trace += f"Output: {result}"
    return trace, result


def generate_dataset():
    rows = []
    tid = 0
    for complexity in COMPLEXITY_LEVELS:
        procs = PROCEDURES[complexity]
        for n_traces in TRACE_COUNTS:
            for seed in range(SEEDS):
                rng = random.Random(
                    seed * 1000
                    + TRACE_COUNTS.index(n_traces) * 100
                    + COMPLEXITY_LEVELS.index(complexity) * 10
                )
                proc_name, proc_fn, proc_desc = procs[seed % len(procs)]

                traces = []
                for t in range(n_traces):
                    ex_input = generate_input(rng)
                    trace_str, _ = format_trace(ex_input, proc_fn)
                    traces.append(trace_str)

                test_input = generate_input(rng)
                expected_result, expected_steps = proc_fn(test_input)

                material = "\n\n".join(f"Example {i + 1}:\n{tr}" for i, tr in enumerate(traces))
                label = f"{complexity}_{n_traces}traces"

                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': complexity,
                    'n_traces': n_traces,
                    'difficulty_label': label,
                    'procedure_name': proc_name,
                    'procedure_desc': proc_desc,
                    'material': material,
                    'test_input': str(test_input),
                    'expected': str(expected_result),
                    'expected_steps': '\n'.join(expected_steps),
                    'item_desc': f'{proc_name} ({complexity}, {n_traces} traces, seed {seed})',
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'trace_based_imitation_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'procedure_name', 'test_input', 'expected']].to_string(index=False))
