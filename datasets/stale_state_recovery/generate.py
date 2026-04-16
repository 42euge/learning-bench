#!/usr/bin/env python3
"""Generate the stale state recovery benchmark dataset.

Usage:
    python datasets/stale_state_recovery/generate.py

Output:
    datasets/stale_state_recovery/stale_state_recovery_dataset.csv

Task:
    Given a sequence of operations where intermediate state becomes invalid
    after certain actions, identify where state becomes stale and what recovery
    step must be inserted.

    Operations:
      - snapshot(): returns a ref token (e.g. s1) capturing current world state
      - act(ref.item_X): acts using a ref, fails if ref is stale
      - mutate(): changes world state, invalidates ALL prior refs
      - refresh(ref): re-snapshots, making ref valid again

    In the "implicit_mutation" variant, some named operations secretly mutate
    state (e.g. write_file, navigate). The rules for which operations invalidate
    refs are given in the worked examples — the model must learn them from the
    material.

Upload to Kaggle:
    kaggle datasets version -p datasets/stale_state_recovery/ -m "Regenerated"
"""

import os
import random
import pandas as pd


# ======================================================================
# Core vocabulary
# ======================================================================

ITEMS = ['item_A', 'item_B', 'item_C', 'item_D', 'item_E', 'item_F', 'item_G']

# Named actions used for "implicit_mutation" variant. Some mutate, some don't.
IMPLICIT_MUTATING = ['write_file', 'navigate', 'commit', 'deploy']
IMPLICIT_PURE = ['read_file', 'inspect', 'log', 'ping', 'hash']


# ======================================================================
# World model used to render worked examples (ground truth semantics)
# ======================================================================

def is_mutating(op_name, complexity):
    """Return True if this operation invalidates existing refs."""
    if complexity == 'implicit_mutation':
        return op_name in IMPLICIT_MUTATING or op_name == 'mutate'
    return op_name == 'mutate'


# ======================================================================
# Sequence building
# ======================================================================

def _fmt_op(op):
    """Render one op dict to a single text line (no step numbers)."""
    kind = op['kind']
    if kind == 'snapshot':
        return f"{op['ref']} = snapshot()"
    if kind == 'act':
        return f"act({op['ref']}.{op['item']})"
    if kind == 'mutate':
        return "mutate()"
    if kind == 'refresh':
        return f"{op['ref']} = snapshot()  # re-snapshot after mutation"
    if kind == 'named':
        return f"{op['name']}()"
    raise ValueError(kind)


def _render_sequence(ops, annotate=False):
    """Render a list of ops as a numbered sequence. If annotate, append OK/FAIL
    comments based on simulated validity of refs at each step."""
    live_refs = set()
    lines = []
    for i, op in enumerate(ops, start=1):
        text = _fmt_op(op)
        if annotate:
            if op['kind'] == 'snapshot':
                live_refs.add(op['ref'])
                text = f"{text}  # captures current state"
            elif op['kind'] == 'refresh':
                live_refs.add(op['ref'])
                # comment already present from _fmt_op
                pass
            elif op['kind'] == 'act':
                ok = op['ref'] in live_refs
                tag = 'OK' if ok else 'FAIL: stale ref'
                # Only add tag if not already a comment line
                text = f"{text}  # {tag}"
            elif op['kind'] == 'mutate':
                live_refs.clear()
                text = f"{text}  # invalidates all prior refs"
            elif op['kind'] == 'named':
                if op['mutating']:
                    live_refs.clear()
                    text = f"{text}  # MUTATING: invalidates all prior refs"
                else:
                    text = f"{text}  # pure: refs remain valid"
        lines.append(f"{i}. {text}")
    return '\n'.join(lines)


def _plain_sequence(ops):
    """Render without annotations — used for test inputs."""
    lines = []
    for i, op in enumerate(ops, start=1):
        text = _fmt_op(op)
        # Strip the built-in refresh comment for the buggy test input only;
        # the buggy input shouldn't contain a refresh anyway.
        lines.append(f"{i}. {text}")
    return '\n'.join(lines)


# ======================================================================
# Worked-example generators
# ======================================================================

def make_worked_example(rng, complexity, idx):
    """Build one worked example showing valid use (with appropriate
    refresh/re-snapshot) and annotated OK/FAIL semantics.

    Returns (ops_list_valid, description).
    """
    ops = []
    # Start with a snapshot
    ops.append({'kind': 'snapshot', 'ref': 's1'})
    ref_counter = 1

    # Decide how many mutations
    if complexity == 'single_mutation':
        n_mutations = 1
    elif complexity == 'multiple_mutations':
        n_mutations = rng.randint(2, 3)
    else:  # implicit_mutation
        n_mutations = rng.randint(1, 2)

    # Act once or twice before first mutation
    n_pre_acts = rng.randint(1, 2)
    items_used = rng.sample(ITEMS, min(len(ITEMS), 4))
    pool = list(items_used)
    rng.shuffle(pool)

    for _ in range(n_pre_acts):
        if not pool:
            pool = list(items_used); rng.shuffle(pool)
        ops.append({'kind': 'act', 'ref': f's{ref_counter}', 'item': pool.pop()})

    # Interleave mutations + refreshes + more acts
    for _ in range(n_mutations):
        # Insert a mutating op
        if complexity == 'implicit_mutation':
            # Alternate between labeled mutate and a named-but-secretly-mutating op
            if rng.random() < 0.5:
                name = rng.choice(IMPLICIT_MUTATING)
                ops.append({'kind': 'named', 'name': name, 'mutating': True})
            else:
                ops.append({'kind': 'mutate'})
            # Sometimes sneak a pure named op in there too
            if rng.random() < 0.5:
                name = rng.choice(IMPLICIT_PURE)
                ops.append({'kind': 'named', 'name': name, 'mutating': False})
        else:
            ops.append({'kind': 'mutate'})

        # VALID example refreshes the ref
        ref_counter += 1
        ops.append({'kind': 'snapshot', 'ref': f's{ref_counter}'})

        # One or two acts with fresh ref
        n_post = rng.randint(1, 2)
        if not pool:
            pool = list(items_used); rng.shuffle(pool)
        for _ in range(n_post):
            if not pool:
                pool = list(items_used); rng.shuffle(pool)
            ops.append({'kind': 'act', 'ref': f's{ref_counter}', 'item': pool.pop()})

    return ops


def make_worked_example_text(rng, complexity, idx):
    """Build a worked example's display string (numbered + annotated)."""
    ops = make_worked_example(rng, complexity, idx)
    header = f"Worked Example {idx}:"
    body = _render_sequence(ops, annotate=True)
    return header + '\n' + body


# ======================================================================
# Test-input (buggy sequence) generator + corrected sequence
# ======================================================================

def make_test_pair(rng, complexity):
    """Build a buggy sequence and its corrected version.

    Returns (buggy_ops, corrected_ops, stale_step_index_1based).
    """
    ops = []
    ops.append({'kind': 'snapshot', 'ref': 's1'})
    ref_counter = 1

    if complexity == 'single_mutation':
        n_mutations = 1
    elif complexity == 'multiple_mutations':
        n_mutations = rng.randint(2, 3)
    else:
        n_mutations = rng.randint(1, 2)

    items_pool = list(ITEMS)
    rng.shuffle(items_pool)

    # One act pre-mutation
    n_pre = rng.randint(1, 2)
    for _ in range(n_pre):
        if not items_pool:
            items_pool = list(ITEMS); rng.shuffle(items_pool)
        ops.append({'kind': 'act', 'ref': f's{ref_counter}', 'item': items_pool.pop()})

    # Track where to choose the "forgotten refresh" — pick one of the mutations
    # to have its refresh omitted. The others are fine.
    mutation_refresh_flags = []  # whether refresh is included after each mutation
    chosen_missing = rng.randrange(n_mutations)

    for m in range(n_mutations):
        # Insert mutation
        if complexity == 'implicit_mutation':
            if rng.random() < 0.5:
                name = rng.choice(IMPLICIT_MUTATING)
                ops.append({'kind': 'named', 'name': name, 'mutating': True})
            else:
                ops.append({'kind': 'mutate'})
            # Optional pure op before the act
            if rng.random() < 0.4:
                name = rng.choice(IMPLICIT_PURE)
                ops.append({'kind': 'named', 'name': name, 'mutating': False})
        else:
            ops.append({'kind': 'mutate'})

        if m == chosen_missing:
            # Forget the refresh — the next act(s) will use the stale ref
            mutation_refresh_flags.append(False)
        else:
            ref_counter += 1
            ops.append({'kind': 'snapshot', 'ref': f's{ref_counter}'})
            mutation_refresh_flags.append(True)

        # Append one act (this is where the stale ref bug manifests if missing)
        if not items_pool:
            items_pool = list(ITEMS); rng.shuffle(items_pool)
        ops.append({'kind': 'act', 'ref': f's{ref_counter}', 'item': items_pool.pop()})

    # Now build the corrected sequence: insert a refresh right after each
    # mutation whose refresh was missing — but ONLY if there's actually a
    # stale-ref act (and no subsequent snapshot before that act) to fix.
    #
    # Strategy: walk buggy ops in order, maintain a "current fresh ref". When
    # we see a mutation without a later snapshot-before-next-act, insert a
    # refresh and redirect subsequent acts to the new ref until the next
    # explicit snapshot.

    def _needs_refresh_after(buggy_ops_list, mut_index):
        """Given the index of a mutating op in buggy ops list, return True if
        the next act in the list (before any snapshot) uses a ref — i.e. a
        refresh is needed to keep that act valid."""
        for j in range(mut_index + 1, len(buggy_ops_list)):
            nk = buggy_ops_list[j]['kind']
            if nk == 'snapshot':
                return False  # an explicit snapshot comes before any act
            if nk == 'act':
                return True
        return False

    corrected_ops = []
    new_ref_counter = 1
    current_ref = f's{new_ref_counter}'
    corrected_ops.append({'kind': 'snapshot', 'ref': current_ref})

    for idx, op in enumerate(ops[1:], start=1):
        if op['kind'] == 'snapshot':
            new_ref_counter += 1
            current_ref = f's{new_ref_counter}'
            corrected_ops.append({'kind': 'snapshot', 'ref': current_ref})
        elif op['kind'] == 'mutate':
            corrected_ops.append({'kind': 'mutate'})
            if _needs_refresh_after(ops, idx):
                new_ref_counter += 1
                current_ref = f's{new_ref_counter}'
                corrected_ops.append({'kind': 'refresh', 'ref': current_ref})
        elif op['kind'] == 'named':
            corrected_ops.append(op)
            if op['mutating'] and _needs_refresh_after(ops, idx):
                new_ref_counter += 1
                current_ref = f's{new_ref_counter}'
                corrected_ops.append({'kind': 'refresh', 'ref': current_ref})
        elif op['kind'] == 'act':
            corrected_ops.append({'kind': 'act', 'ref': current_ref, 'item': op['item']})
        else:
            corrected_ops.append(op)

    # Figure out the 1-based step index in the buggy sequence where staleness
    # first manifests: first act after the "chosen_missing" mutation without
    # refresh. We can reconstruct this by re-walking buggy ops tracking live.
    live_refs = set()
    stale_step = None
    for i, op in enumerate(ops, start=1):
        if op['kind'] == 'snapshot':
            live_refs.add(op['ref'])
        elif op['kind'] == 'mutate':
            live_refs.clear()
        elif op['kind'] == 'named' and op.get('mutating'):
            live_refs.clear()
        elif op['kind'] == 'act':
            if op['ref'] not in live_refs:
                stale_step = i
                break

    return ops, corrected_ops, stale_step


# ======================================================================
# Material builder (worked examples)
# ======================================================================

def build_material(rng, complexity, n_examples):
    """Build the `material` string with n_examples worked examples plus a
    brief vocabulary note."""
    intro_lines = [
        "World model: `snapshot()` captures the current world and returns a",
        "ref token. `act(ref.item_X)` uses a ref to perform an action. A ref",
        "becomes STALE once the world state it captured is mutated — any",
        "further `act(ref.*)` with that stale ref FAILS. To recover, you must",
        "re-snapshot to get a fresh ref before acting again.",
    ]
    if complexity == 'implicit_mutation':
        intro_lines += [
            "",
            "Some named operations (e.g. `write_file()`, `navigate()`,",
            "`commit()`, `deploy()`) mutate the world as a side-effect — they",
            "invalidate refs just like `mutate()` does. Others (e.g.",
            "`read_file()`, `inspect()`, `log()`, `ping()`, `hash()`) are pure",
            "and do NOT invalidate refs. The worked examples below demonstrate",
            "which is which.",
        ]
    intro = '\n'.join(intro_lines)

    examples = []
    for i in range(1, n_examples + 1):
        examples.append(make_worked_example_text(rng, complexity, i))

    return intro + '\n\n' + '\n\n'.join(examples)


# ======================================================================
# CSV row builder
# ======================================================================

COMPLEXITY_ORDER = ['single_mutation', 'multiple_mutations', 'implicit_mutation']
EVIDENCE_ORDER = ['few', 'mid', 'many']
EVIDENCE_COUNTS = {'few': 3, 'mid': 5, 'many': 6}
SEEDS = 3

COMPLEXITY_SEED = {'single_mutation': 0, 'multiple_mutations': 1, 'implicit_mutation': 2}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}


def corrected_sequence_to_string(corrected_ops):
    """Render corrected ops as a numbered sequence string — used for the
    `expected` column and for model answer comparison."""
    lines = []
    for i, op in enumerate(corrected_ops, start=1):
        lines.append(f"{i}. {_fmt_op(op)}")
    return '\n'.join(lines)


def generate_dataset():
    rows = []
    task_id = 0
    for complexity in COMPLEXITY_ORDER:
        for evidence in EVIDENCE_ORDER:
            n_examples = EVIDENCE_COUNTS[evidence]
            for seed in range(SEEDS):
                rng = random.Random(
                    seed * 1000
                    + COMPLEXITY_SEED[complexity] * 100
                    + EVIDENCE_SEED[evidence] * 10
                )
                material = build_material(rng, complexity, n_examples)
                buggy_ops, corrected_ops, stale_step = make_test_pair(rng, complexity)
                test_input = "OPS:\n" + _plain_sequence(buggy_ops)
                expected = corrected_sequence_to_string(corrected_ops)
                label = f'{complexity}_{evidence}'
                item_desc = (
                    f'complexity={complexity}, evidence={evidence}({n_examples}ex), '
                    f'seed={seed}, stale_step={stale_step}, len={len(buggy_ops)}'
                )
                rows.append({
                    'task_id': task_id,
                    'material': material,
                    'test_input': test_input,
                    'expected': expected,
                    'complexity': complexity,
                    'evidence': evidence,
                    'difficulty_label': label,
                    'seed': seed,
                    'item_desc': item_desc,
                    'stale_step': stale_step,
                })
                task_id += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'stale_state_recovery_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'seed', 'stale_step', 'item_desc']].to_string(index=False))
    print()
    print('Sample material (row 0):')
    print('-' * 60)
    print(dataset.iloc[0]['material'])
    print()
    print('Sample test_input (row 0):')
    print('-' * 60)
    print(dataset.iloc[0]['test_input'])
    print()
    print('Sample expected (row 0):')
    print('-' * 60)
    print(dataset.iloc[0]['expected'])
