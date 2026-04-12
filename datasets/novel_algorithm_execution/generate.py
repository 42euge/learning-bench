#!/usr/bin/env python3
"""Generate the novel algorithm execution benchmark dataset.

Usage:
    python datasets/novel_algorithm_execution/generate.py

Output:
    datasets/novel_algorithm_execution/novel_algorithm_execution_dataset.csv

Upload to Kaggle:
    kaggle datasets version -p datasets/novel_algorithm_execution/ -m "Regenerated"
"""

import os
import random

import pandas as pd

# === Novel Algorithm Implementations ===
# Each algorithm: (name, function, spec_verbose, spec_standard, spec_terse)
# All are deterministic, operate on a list of integers, and return a single integer.


def crinkle_sum(lst):
    """Simple: swap adjacent pairs if both odd, then sum even-indexed elements."""
    arr = list(lst)
    for i in range(len(arr) - 1):
        if arr[i] % 2 == 1 and arr[i+1] % 2 == 1:
            arr[i], arr[i+1] = arr[i+1], arr[i]
    return sum(arr[i] for i in range(0, len(arr), 2))


CRINKLE_VERBOSE = """Algorithm: Crinkle Sum
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Conditional Adjacent Swap Pass: Go through the list from left to right, examining each
           consecutive pair (index 0&1, then 1&2, then 2&3, ...). For each pair, check if BOTH
           elements are odd numbers. If yes, swap them in place. If not, leave them. Process each
           pair exactly once, left to right. Note: the swaps happen in-place, so a swap at position
           i affects what is seen at position i+1.
  Step 2 — Even-Index Summation: After all swaps are done, take every element at an even index
           (0, 2, 4, ...) and add them together. That sum is the final answer.
Example: [3, 7, 4, 5] -> Step 1: pair(0,1)=[3,7] both odd, swap -> [7,3,4,5]; pair(1,2)=[3,4]
         not both odd, skip; pair(2,3)=[4,5] not both odd, skip. Step 2: arr[0]+arr[2]=7+4=11.
Output: A single integer."""

CRINKLE_STANDARD = """Algorithm: Crinkle Sum
Input: A list of integers.
Step 1: Iterate left to right through consecutive pairs. If both elements in a pair are odd, swap them.
Step 2: Sum all elements at even indices (0, 2, 4, ...).
Output: The sum (a single integer)."""

CRINKLE_TERSE = """Crinkle Sum: For each adjacent pair L-to-R, swap if both odd. Return sum of even-indexed elements."""


def zigzag_product(lst):
    """Simple: alternately add/subtract from accumulator, return abs value."""
    acc = 0
    for i, x in enumerate(lst):
        if i % 2 == 0:
            acc += x
        else:
            acc -= x
    return abs(acc)


ZIGZAG_VERBOSE = """Algorithm: Zigzag Product
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Initialize: Set an accumulator variable to 0.
  Step 2 — Alternating pass: Go through each element by index. If the index is even (0, 2, 4, ...),
           ADD the element to the accumulator. If the index is odd (1, 3, 5, ...), SUBTRACT the
           element from the accumulator.
  Step 3 — Absolute value: Take the absolute value of the accumulator. This is the final answer.
Example: [10, 3, 5, 8] -> acc starts at 0. Index 0 (even): 0+10=10. Index 1 (odd): 10-3=7.
         Index 2 (even): 7+5=12. Index 3 (odd): 12-8=4. abs(4)=4. Answer: 4.
Output: A single non-negative integer."""

ZIGZAG_STANDARD = """Algorithm: Zigzag Product
Input: A list of integers.
Step 1: Start accumulator at 0.
Step 2: For each element — add it if its index is even, subtract it if its index is odd.
Step 3: Return the absolute value of the accumulator.
Output: A single integer."""

ZIGZAG_TERSE = """Zigzag Product: acc=0; even-indexed elements add, odd-indexed subtract; return |acc|."""


def mirror_count(lst):
    """Simple: count pairs from outside in where left > right, return that count."""
    count = 0
    n = len(lst)
    for i in range(n // 2):
        if lst[i] > lst[n - 1 - i]:
            count += 1
    return count


MIRROR_VERBOSE = """Algorithm: Mirror Count
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Initialize a counter to 0.
  Step 2 — Pair elements from outside inward: pair the first element with the last, the second
           with the second-to-last, and so on. If the list has odd length, the middle element
           has no pair and is ignored.
  Step 3 — For each pair, if the LEFT element is strictly greater than the RIGHT element,
           increment the counter by 1.
  Step 4 — The counter value is the final answer.
Example: [8, 2, 5, 3, 6] -> pairs: (8,6), (2,3). Middle element 5 ignored.
         8>6? yes, count=1. 2>3? no. Answer: 1.
Output: A single non-negative integer."""

MIRROR_STANDARD = """Algorithm: Mirror Count
Input: A list of integers.
Step 1: Counter = 0.
Step 2: Pair elements from ends inward (first+last, second+second-to-last, ...). Skip middle if odd length.
Step 3: For each pair, if left > right, increment counter.
Output: The counter (a single integer)."""

MIRROR_TERSE = """Mirror Count: Pair elements outside-in; count how many pairs have left > right."""


def vortex_reduce(lst):
    """Medium: chunk into 3s, rotate within chunk based on sum, take max of each chunk, multiply all."""
    chunks = []
    for i in range(0, len(lst), 3):
        chunks.append(list(lst[i:i+3]))
    maxes = []
    for chunk in chunks:
        if len(chunk) < 2:
            maxes.append(max(chunk))
            continue
        s = sum(chunk)
        if s > 10:
            chunk = chunk[1:] + chunk[:1]
        else:
            chunk = chunk[-1:] + chunk[:-1]
        maxes.append(max(chunk))
    result = 1
    for m in maxes:
        result *= m
    return result


VORTEX_VERBOSE = """Algorithm: Vortex Reduce
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Partition into chunks of 3: Split the list into consecutive chunks of 3 elements each.
           If the last chunk has fewer than 3 elements, keep it as-is.
  Step 2 — Conditional rotation: For each chunk with 2 or more elements, compute the sum of the
           chunk. If the sum is strictly greater than 10, rotate the chunk LEFT by 1 position
           (first element moves to end: [a,b,c]->[b,c,a]). Otherwise (sum <= 10), rotate RIGHT
           by 1 position (last element moves to front: [a,b,c]->[c,a,b]). Chunks with only 1
           element stay unchanged.
  Step 3 — Extract maximums: From each (possibly rotated) chunk, take the maximum value.
  Step 4 — Multiply all: Multiply all the maximum values together. This product is the answer.
Example: [2, 5, 4, 1, 3, 8] -> Chunks: [2,5,4], [1,3,8]. Chunk 1 sum=11>10, rotate left:
         [5,4,2], max=5. Chunk 2 sum=12>10, rotate left: [3,8,1], max=8. Product: 5*8=40.
Output: A single integer."""

VORTEX_STANDARD = """Algorithm: Vortex Reduce
Input: A list of integers.
Step 1: Split into consecutive chunks of 3 (last chunk may be smaller).
Step 2: Per chunk (2+ elements): if chunk sum > 10, rotate left by 1; else rotate right by 1.
Step 3: Take the max of each chunk.
Step 4: Multiply all the maxes together.
Output: A single integer."""

VORTEX_TERSE = """Vortex Reduce: Chunk by 3; rotate left if sum>10 else right; take chunk maxes; multiply them all."""


def cascade_filter(lst):
    """Medium: multi-pass filter — remove multiples of 3, then square survivors, then sum only those < 100."""
    stage1 = [x for x in lst if x % 3 != 0]
    stage2 = [x * x for x in stage1]
    return sum(x for x in stage2 if x < 100)


CASCADE_VERBOSE = """Algorithm: Cascade Filter
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Remove multiples of 3: Go through the list and discard every element that is a multiple
           of 3 (i.e., element % 3 == 0). Zero is a multiple of 3. Keep all other elements in
           their original order.
  Step 2 — Square the survivors: Take each remaining element and replace it with its square
           (element * element).
  Step 3 — Threshold sum: From the squared values, sum ONLY those that are strictly less than 100.
           Ignore any squared value that is 100 or greater. This sum is the final answer.
Example: [6, 4, 7, 9, 2] -> Step 1: remove 6,9 (multiples of 3) -> [4,7,2]. Step 2: square ->
         [16, 49, 4]. Step 3: all < 100, so sum = 16+49+4 = 69. Answer: 69.
Output: A single integer."""

CASCADE_STANDARD = """Algorithm: Cascade Filter
Input: A list of integers.
Step 1: Remove all elements that are multiples of 3.
Step 2: Square each remaining element.
Step 3: Sum only the squared values that are strictly less than 100.
Output: A single integer."""

CASCADE_TERSE = """Cascade Filter: Drop multiples of 3; square rest; sum those squares < 100."""


def ripple_hash(lst):
    """Medium: XOR running pairs, then alternating sum of results."""
    if len(lst) < 2:
        return lst[0] if lst else 0
    xored = []
    for i in range(len(lst) - 1):
        xored.append(lst[i] ^ lst[i+1])
    acc = 0
    for i, v in enumerate(xored):
        if i % 2 == 0:
            acc += v
        else:
            acc -= v
    return abs(acc)


RIPPLE_VERBOSE = """Algorithm: Ripple Hash
Input: A list of integers (all non-negative).
Procedure (follow these steps in order):
  Step 1 — Pairwise XOR: Create a new list by XOR-ing each consecutive pair of elements. For a
           list of length n, this produces n-1 values. Element i of the new list = original[i] XOR
           original[i+1]. (XOR is the bitwise exclusive-or operation.)
  Step 2 — Alternating sum: Starting with accumulator = 0, go through the XOR list. At even indices
           (0, 2, 4, ...) ADD the value; at odd indices (1, 3, 5, ...) SUBTRACT it.
  Step 3 — Return the absolute value of the accumulator.
Example: [5, 3, 6] -> Step 1: [5^3, 3^6] = [6, 5]. Step 2: acc=0, idx 0 (even): 0+6=6,
         idx 1 (odd): 6-5=1. Step 3: |1|=1. Answer: 1.
Output: A single non-negative integer."""

RIPPLE_STANDARD = """Algorithm: Ripple Hash
Input: A list of non-negative integers.
Step 1: XOR each consecutive pair -> new list of length n-1.
Step 2: Alternating sum of the XOR list (add at even indices, subtract at odd).
Step 3: Return absolute value of the result.
Output: A single integer."""

RIPPLE_TERSE = """Ripple Hash: XOR consecutive pairs; alternating +/- sum of results; return absolute value."""


def nexus_fold(lst):
    """Complex: stateful accumulator with conditional ops, threshold reset, and parity-gated final transform."""
    acc = 0
    for x in lst:
        if acc % 2 == 0:
            acc += x
        else:
            acc -= x
        if acc > 20:
            acc = x
        if acc < -20:
            acc = -x
    if acc < 0:
        acc = acc * -1
    return acc


NEXUS_VERBOSE = """Algorithm: Nexus Fold
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Initialize: Set accumulator = 0.
  Step 2 — Process each element left to right. For each element x:
    Rule A (parity gate): Check if the accumulator is currently EVEN. If even, ADD x to the
           accumulator. If odd, SUBTRACT x from the accumulator.
    Rule B (upper overflow): After applying Rule A, if the accumulator is now strictly greater
           than 20, RESET the accumulator to x (the current element's value, not the accumulated
           value).
    Rule C (lower overflow): After applying Rule B, if the accumulator is now strictly less than
           -20, RESET the accumulator to -x (negative of the current element).
    Important: Apply Rules A, B, C in that exact order for each element before moving to the next.
  Step 3 — Final transform: After processing all elements, if the accumulator is negative, negate
           it (multiply by -1). Return the final accumulator value.
Example: [10, 7, 3, 15, 4] -> acc=0 (even).
  x=10: even, acc=0+10=10. 10<=20, no reset. 10>=-20, no reset. acc=10.
  x=7: even, acc=10+7=17. 17<=20, ok. acc=17.
  x=3: odd, acc=17-3=14. 14<=20, ok. acc=14.
  x=15: even, acc=14+15=29. 29>20, reset to x=15. acc=15.
  x=4: odd, acc=15-4=11. 11<=20, ok. acc=11.
  Final: 11>=0, no negate. Answer: 11.
Output: A single non-negative integer."""

NEXUS_STANDARD = """Algorithm: Nexus Fold
Input: A list of integers.
Step 1: accumulator = 0.
Step 2: For each element x (left to right):
  - If acc is even: acc += x. If acc is odd: acc -= x.
  - If acc > 20: acc = x (reset to current element).
  - If acc < -20: acc = -x (reset to negated current element).
Step 3: If acc < 0, negate it.
Output: A single integer."""

NEXUS_TERSE = """Nexus Fold: acc=0; per element: add if acc even, subtract if odd; reset to x if >20, -x if <-20; final: |acc|."""


def helix_weave(lst):
    """Complex: interleave from both ends, apply conditional transforms, running weighted sum."""
    n = len(lst)
    interleaved = []
    left, right = 0, n - 1
    while left <= right:
        interleaved.append(lst[left])
        if left != right:
            interleaved.append(lst[right])
        left += 1
        right -= 1

    acc = 0
    for i, v in enumerate(interleaved):
        if v % 2 == 0:
            contrib = v // 2
        else:
            contrib = v * 2
        if i % 3 == 0:
            acc += contrib * 3
        elif i % 3 == 1:
            acc += contrib * 2
        else:
            acc -= contrib
    return abs(acc)


HELIX_VERBOSE = """Algorithm: Helix Weave
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Interleave from ends: Build a new list by alternately taking elements from the start
           and end. Take first, then last, then second, then second-to-last, and so on. If the
           list has odd length, the middle element appears once at the end.
           Example: [a,b,c,d,e] -> [a,e,b,d,c].
  Step 2 — Conditional transform: For each element in the interleaved list, apply:
           - If the element is EVEN: replace it with element // 2 (integer division by 2).
           - If the element is ODD: replace it with element * 2.
           Call this the "contribution" for that position.
  Step 3 — Weighted accumulation: Starting with acc = 0, for each position i in the transformed list:
           - If i mod 3 == 0: acc += contribution * 3
           - If i mod 3 == 1: acc += contribution * 2
           - If i mod 3 == 2: acc -= contribution
  Step 4 — Return the absolute value of acc.
Example: [4, 7, 2] -> Step 1: interleave -> [4, 2, 7]. Step 2: 4 is even -> 2; 2 is even -> 1;
         7 is odd -> 14. Step 3: i=0 (mod3=0): acc=0+2*3=6. i=1 (mod3=1): acc=6+1*2=8.
         i=2 (mod3=2): acc=8-14=-6. Step 4: |-6|=6. Answer: 6.
Output: A single non-negative integer."""

HELIX_STANDARD = """Algorithm: Helix Weave
Input: A list of integers.
Step 1: Interleave from ends: take first, last, second, second-to-last, etc.
Step 2: Transform each value — even: v//2, odd: v*2.
Step 3: Weighted sum — at position i: if i%3==0, add val*3; if i%3==1, add val*2; if i%3==2, subtract val.
Step 4: Return absolute value of the sum.
Output: A single integer."""

HELIX_TERSE = """Helix Weave: Interleave from ends; even->halve, odd->double; weighted sum (x3,x2,-1 by i%3); return |result|."""


def prism_stack(lst):
    """Complex: multi-stack algorithm with push/pop rules based on value properties."""
    stack_a = []  # evens
    stack_b = []  # odds
    for x in lst:
        if x % 2 == 0:
            stack_a.append(x)
            if len(stack_a) >= 3:
                top3 = stack_a[-3:]
                stack_a = stack_a[:-3]
                stack_a.append(sum(top3))
        else:
            stack_b.append(x)
            if len(stack_b) >= 2:
                top2 = stack_b[-2:]
                stack_b = stack_b[:-2]
                stack_b.append(top2[0] * top2[1])

    total_a = sum(stack_a) if stack_a else 0
    total_b = sum(stack_b) if stack_b else 0
    return abs(total_a - total_b)


PRISM_VERBOSE = """Algorithm: Prism Stack
Input: A list of integers.
Procedure (follow these steps in order):
  Step 1 — Initialize two empty stacks: Stack-A (for even numbers) and Stack-B (for odd numbers).
  Step 2 — Process each element left to right:
    Rule A: If the element is EVEN, push it onto Stack-A. Then check: if Stack-A now has 3 or more
            elements, pop the top 3, compute their sum, and push that sum back onto Stack-A.
            (This collapses the top 3 into one element.)
    Rule B: If the element is ODD, push it onto Stack-B. Then check: if Stack-B now has 2 or more
            elements, pop the top 2, compute their product, and push that product back onto Stack-B.
            (This collapses the top 2 into one element.)
  Step 3 — After processing all elements:
    - Sum all elements remaining in Stack-A -> total_A
    - Sum all elements remaining in Stack-B -> total_B
    - Return |total_A - total_B| (absolute difference).
Example: [4, 3, 6, 5, 2] ->
  x=4 (even): A=[4], len<3 ok. B=[].
  x=3 (odd): A=[4]. B=[3], len<2 ok.
  x=6 (even): A=[4,6], len<3 ok. B=[3].
  x=5 (odd): B=[3,5], len>=2 -> pop 3,5 -> 3*5=15 -> B=[15]. A=[4,6].
  x=2 (even): A=[4,6,2], len>=3 -> pop 4,6,2 -> 4+6+2=12 -> A=[12]. B=[15].
  total_A=12, total_B=15. |12-15|=3. Answer: 3.
Output: A single non-negative integer."""

PRISM_STANDARD = """Algorithm: Prism Stack
Input: A list of integers.
Step 1: Two empty stacks: A (evens) and B (odds).
Step 2: For each element:
  - Even -> push to A. If A has 3+ elements, pop top 3 and push their sum.
  - Odd -> push to B. If B has 2+ elements, pop top 2 and push their product.
Step 3: Return |sum(A) - sum(B)|.
Output: A single integer."""

PRISM_TERSE = """Prism Stack: Evens to stack A (collapse top-3 by summing), odds to stack B (collapse top-2 by multiplying); return |sum(A)-sum(B)|."""


# === Algorithm registry ===
ALGORITHMS = {
    'simple': [
        ('Crinkle Sum', crinkle_sum, CRINKLE_VERBOSE, CRINKLE_STANDARD, CRINKLE_TERSE),
        ('Zigzag Product', zigzag_product, ZIGZAG_VERBOSE, ZIGZAG_STANDARD, ZIGZAG_TERSE),
        ('Mirror Count', mirror_count, MIRROR_VERBOSE, MIRROR_STANDARD, MIRROR_TERSE),
    ],
    'medium': [
        ('Vortex Reduce', vortex_reduce, VORTEX_VERBOSE, VORTEX_STANDARD, VORTEX_TERSE),
        ('Cascade Filter', cascade_filter, CASCADE_VERBOSE, CASCADE_STANDARD, CASCADE_TERSE),
        ('Ripple Hash', ripple_hash, RIPPLE_VERBOSE, RIPPLE_STANDARD, RIPPLE_TERSE),
    ],
    'complex': [
        ('Nexus Fold', nexus_fold, NEXUS_VERBOSE, NEXUS_STANDARD, NEXUS_TERSE),
        ('Helix Weave', helix_weave, HELIX_VERBOSE, HELIX_STANDARD, HELIX_TERSE),
        ('Prism Stack', prism_stack, PRISM_VERBOSE, PRISM_STANDARD, PRISM_TERSE),
    ],
}

CLARITY_MAP = {'verbose': 2, 'standard': 3, 'terse': 4}  # index into tuple

# === Deterministic seed mapping (NO hash()) ===
COMPLEXITY_SEED = {'simple': 0, 'medium': 1, 'complex': 2}
CLARITY_SEED = {'verbose': 0, 'standard': 1, 'terse': 2}

# === Generation constants ===
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0

    for complexity, algos in ALGORITHMS.items():
        for clarity, spec_idx in CLARITY_MAP.items():
            for seed in range(SEEDS):
                rng = random.Random(
                    seed * 1000 + COMPLEXITY_SEED[complexity] * 100 + CLARITY_SEED[clarity]
                )
                # Pick one algorithm per (complexity, seed) combo — cycle through the 3
                algo_tuple = algos[seed % len(algos)]
                name, fn = algo_tuple[0], algo_tuple[1]
                spec = algo_tuple[spec_idx]

                # Generate a random test input (6-8 integers, 1-20 range)
                list_len = rng.randint(6, 8)
                test_input = [rng.randint(1, 20) for _ in range(list_len)]
                expected = fn(test_input)

                label = f'{complexity}_{clarity}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'clarity': clarity, 'difficulty_label': label,
                    'algo_name': name, 'spec': spec.strip(),
                    'test_input': str(test_input),
                    'expected': str(expected),
                })
                tid += 1

    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'novel_algorithm_execution_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'algo_name', 'test_input', 'expected']].to_string(index=False))
    print(f'\nExpected answer range: {dataset["expected"].astype(int).min()} to {dataset["expected"].astype(int).max()}')
