#!/usr/bin/env python3
"""Generate the error severity triage benchmark dataset.

Task: classify a log line from an invented CLI tool into one of four severity
classes: INFO / WARNING / RETRYABLE_ERROR / TERMINAL_ERROR.

The classification rules are NOT universal — they come from the invented tool's
conventions that the model must infer from a batch of labeled examples. The
goal is to test whether models can override their "error == blocking" prior
and use the evidence to distinguish retryable from terminal errors.

Difficulty grid:
  - complexity: single_tag | tag_plus_code | contextual
  - evidence:   few (5) | mid (8) | many (12)
  - seeds:      3

Usage:
    python datasets/error_severity_triage/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/error_severity_triage/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# === Invented tool names (feel novel to the model) ===

TOOL_NAMES = [
    'prismd', 'orbix', 'quarkctl', 'zephyrq', 'vantaloop',
    'glintd', 'helixsync', 'nimboforge', 'tessera', 'lumenrun',
]

# === Action words (tool actions) ===

ACTIONS = [
    'fetch', 'resolve', 'compile', 'flush', 'index', 'unpack', 'validate',
    'stream', 'bind', 'migrate', 'snapshot', 'replicate', 'drain', 'warm',
]

# === Target nouns ===

TARGETS = [
    'shard', 'manifest', 'pipeline', 'segment', 'ledger', 'cache-ring',
    'buffer-pool', 'task-queue', 'bundle', 'artifact', 'keyring', 'vault',
]


def _mk_objects(rng, n):
    """Generate n unique action/target pairs."""
    pool = [f'{a} {t}' for a in ACTIONS for t in TARGETS]
    rng.shuffle(pool)
    return pool[:n]


# ---------------------------------------------------------------------------
# Complexity: SINGLE_TAG
# Each line is prefixed with a unique tool-specific tag token that maps 1:1
# to a severity class. The model must infer the tag -> class mapping.
# ---------------------------------------------------------------------------

SINGLE_TAG_SCHEMES = [
    # (tool_name, {tag: severity})
    ('prismd',   {'[.]': 'INFO', '[~]': 'WARNING', '[*]': 'RETRYABLE_ERROR', '[!]': 'TERMINAL_ERROR'}),
    ('orbix',    {'::note::': 'INFO', '::soft::': 'WARNING', '::retry::': 'RETRYABLE_ERROR', '::halt::': 'TERMINAL_ERROR'}),
    ('zephyrq',  {'@ok':  'INFO', '@mild': 'WARNING', '@redo': 'RETRYABLE_ERROR', '@dead': 'TERMINAL_ERROR'}),
    ('quarkctl', {'<I>': 'INFO', '<W>': 'WARNING', '<Er>': 'RETRYABLE_ERROR', '<Ef>': 'TERMINAL_ERROR'}),
    ('glintd',   {'++': 'INFO', '~~': 'WARNING', '^^': 'RETRYABLE_ERROR', 'xx': 'TERMINAL_ERROR'}),
    ('tessera',  {'#info': 'INFO', '#warn': 'WARNING', '#again': 'RETRYABLE_ERROR', '#stop': 'TERMINAL_ERROR'}),
]


def _single_tag_line(rng, tag, phrase):
    return f'{tag} {phrase}'


def gen_single_tag(seed, n_examples, forced_test_class=None):
    rng = random.Random(seed)
    tool, scheme = rng.choice(SINGLE_TAG_SCHEMES)
    tags = list(scheme.keys())
    # Reverse map: severity class -> tag
    class_to_tag = {v: k for k, v in scheme.items()}
    # Generate unique action/target phrases for all lines (examples + test)
    phrases = _mk_objects(rng, n_examples + 1)

    # Distribute severities as evenly as possible across examples
    severities_order = []
    for i in range(n_examples):
        severities_order.append(tags[i % 4])
    rng.shuffle(severities_order)

    # Build example block
    example_lines = []
    for i in range(n_examples):
        tag = severities_order[i]
        phrase = phrases[i]
        raw = _single_tag_line(rng, tag, phrase)
        example_lines.append(f'  {raw}    -> {scheme[tag]}')
    material = '\n'.join(example_lines)

    # Pick a test tag
    if forced_test_class is not None:
        test_tag = class_to_tag[forced_test_class]
    else:
        test_tag = rng.choice(tags)
    test_phrase = phrases[-1]
    test_input = _single_tag_line(rng, test_tag, test_phrase)
    expected = scheme[test_tag]
    desc = f'single_tag / tool={tool}'
    return material, test_input, expected, desc


# ---------------------------------------------------------------------------
# Complexity: TAG_PLUS_CODE
# Lines have a generic severity bucket tag (ERR, OK, WARN) plus a tool-specific
# error code. The tag alone is insufficient for ERR lines — the model must use
# the code prefix or numeric range to distinguish retryable vs terminal.
# ---------------------------------------------------------------------------

TAG_PLUS_CODE_SCHEMES = [
    # Rule: "OK" => INFO, "WARN" => WARNING, "ERR-<range>":
    #   codes 1xx-3xx = RETRYABLE, 4xx-9xx = TERMINAL
    (
        'nimboforge',
        {
            'info_tag': 'OK',
            'warn_tag': 'WARN',
            'err_tag':  'ERR',
            'retryable_codes': [101, 133, 204, 240, 310, 355],
            'terminal_codes':  [402, 455, 501, 577, 812, 903],
            'code_fmt': 'E-{code}',
        },
    ),
    # Rule: "NOTE" => INFO, "CAUTION" => WARNING, "FAULT" codes starting with
    #   T- or N- are retryable (transient/network); D- or F- are terminal.
    (
        'vantaloop',
        {
            'info_tag': 'NOTE',
            'warn_tag': 'CAUTION',
            'err_tag':  'FAULT',
            'retryable_codes': ['T-011', 'T-028', 'N-104', 'N-217', 'T-331', 'N-408'],
            'terminal_codes':  ['D-002', 'D-117', 'F-240', 'F-315', 'D-406', 'F-509'],
            'code_fmt': '{code}',
        },
    ),
    # Rule: "LOG" => INFO, "SOFT" => WARNING, "HARD" codes with even last digit
    #   are retryable; odd last digit = terminal.
    (
        'helixsync',
        {
            'info_tag': 'LOG',
            'warn_tag': 'SOFT',
            'err_tag':  'HARD',
            'retryable_codes': [1002, 1024, 2008, 2040, 3006, 4002],
            'terminal_codes':  [1001, 1013, 2005, 2031, 3007, 4009],
            'code_fmt': 'H{code}',
        },
    ),
    # Rule: "TRACE" => INFO, "HINT" => WARNING, "BREAK" codes prefixed "rt-" are
    #   retryable; "tm-" are terminal.
    (
        'lumenrun',
        {
            'info_tag': 'TRACE',
            'warn_tag': 'HINT',
            'err_tag':  'BREAK',
            'retryable_codes': ['rt-17', 'rt-23', 'rt-44', 'rt-58', 'rt-61', 'rt-79'],
            'terminal_codes':  ['tm-04', 'tm-12', 'tm-30', 'tm-45', 'tm-66', 'tm-88'],
            'code_fmt': '{code}',
        },
    ),
]


def _tpc_line(rng, tag, phrase, code=None, code_fmt=None):
    if code is None:
        return f'{tag} :: {phrase}'
    cc = code_fmt.format(code=code)
    return f'{tag} :: {phrase} [{cc}]'


def gen_tag_plus_code(seed, n_examples, forced_test_class=None):
    rng = random.Random(seed)
    tool, scheme = rng.choice(TAG_PLUS_CODE_SCHEMES)
    phrases = _mk_objects(rng, n_examples + 1)

    # Severity class assignment per example (cycle through all 4 classes)
    # Order is [INFO, WARNING, RETRYABLE, TERMINAL] repeated, then shuffled.
    class_cycle = ['INFO', 'WARNING', 'RETRYABLE_ERROR', 'TERMINAL_ERROR']
    chosen = [class_cycle[i % 4] for i in range(n_examples)]
    rng.shuffle(chosen)

    # Track which retryable/terminal codes are used so test can pick a novel one
    retry_pool = list(scheme['retryable_codes'])
    term_pool = list(scheme['terminal_codes'])
    rng.shuffle(retry_pool)
    rng.shuffle(term_pool)
    retry_idx, term_idx = 0, 0

    example_lines = []
    for i, cls in enumerate(chosen):
        phrase = phrases[i]
        if cls == 'INFO':
            raw = _tpc_line(rng, scheme['info_tag'], phrase)
        elif cls == 'WARNING':
            raw = _tpc_line(rng, scheme['warn_tag'], phrase)
        elif cls == 'RETRYABLE_ERROR':
            code = retry_pool[retry_idx % len(retry_pool)]
            retry_idx += 1
            raw = _tpc_line(rng, scheme['err_tag'], phrase, code=code, code_fmt=scheme['code_fmt'])
        else:  # TERMINAL_ERROR
            code = term_pool[term_idx % len(term_pool)]
            term_idx += 1
            raw = _tpc_line(rng, scheme['err_tag'], phrase, code=code, code_fmt=scheme['code_fmt'])
        example_lines.append(f'  {raw}    -> {cls}')
    material = '\n'.join(example_lines)

    # Build a test line — choose any of the 4 classes uniformly (or use forced class)
    test_cls = forced_test_class if forced_test_class is not None else rng.choice(class_cycle)
    test_phrase = phrases[-1]
    if test_cls == 'INFO':
        test_input = _tpc_line(rng, scheme['info_tag'], test_phrase)
    elif test_cls == 'WARNING':
        test_input = _tpc_line(rng, scheme['warn_tag'], test_phrase)
    elif test_cls == 'RETRYABLE_ERROR':
        # Pick an UNUSED retryable code if available (novel composition)
        unused = [c for c in scheme['retryable_codes'] if c not in retry_pool[:retry_idx]]
        if not unused:
            unused = scheme['retryable_codes']
        code = rng.choice(unused)
        test_input = _tpc_line(rng, scheme['err_tag'], test_phrase, code=code, code_fmt=scheme['code_fmt'])
    else:  # TERMINAL_ERROR
        unused = [c for c in scheme['terminal_codes'] if c not in term_pool[:term_idx]]
        if not unused:
            unused = scheme['terminal_codes']
        code = rng.choice(unused)
        test_input = _tpc_line(rng, scheme['err_tag'], test_phrase, code=code, code_fmt=scheme['code_fmt'])

    expected = test_cls
    desc = f'tag_plus_code / tool={tool}'
    return material, test_input, expected, desc


# ---------------------------------------------------------------------------
# Complexity: CONTEXTUAL
# Severity depends on keywords in the message body. All lines share the same
# generic tag (e.g., "STATUS:"), so the model has to learn which body keywords
# push a line from WARNING to RETRYABLE_ERROR or TERMINAL_ERROR. The classic
# trick: "timeout" / "throttled" / "transient" => retryable, but
# "no space left" / "corrupt" / "unauthorized" / "quota permanently exceeded"
# => terminal.
# ---------------------------------------------------------------------------

CONTEXTUAL_SCHEMES = [
    {
        'tool': 'orbix',
        'tag': 'STATUS:',
        # body template -> severity
        'info_bodies': [
            'started {action} on {target}',
            '{action} {target} completed',
            '{target} warmed up',
            'handshake ok with {target}',
            'checkpoint saved for {target}',
            'heartbeat from {target}',
        ],
        'warning_bodies': [
            'slow {action} on {target} ({lat}ms)',
            '{target} approaching capacity',
            '{action} {target} retried once and succeeded',
            'stale {target} detected, refreshing',
            '{target} latency above baseline',
        ],
        'retryable_keywords': [
            'connection timeout reaching {target}',
            'throttled by {target} (try again)',
            '{target} returned transient 503',
            'temporarily unreachable: {target}',
            'lock contention on {target}',
            'rate limit hit on {action} {target}',
        ],
        'terminal_keywords': [
            'disk full: no space left while writing {target}',
            '{target} manifest is corrupt',
            'unauthorized: credentials rejected for {target}',
            'schema mismatch: {target} incompatible',
            'quota permanently exceeded for {target}',
            '{target} not found and cannot be recreated',
        ],
    },
    {
        'tool': 'tessera',
        'tag': '>>',
        'info_bodies': [
            '{action} {target} done',
            'loaded {target} index',
            'opened handle to {target}',
            'replica of {target} in sync',
            'warm start of {target}',
        ],
        'warning_bodies': [
            'degraded {action} on {target}',
            '{target} fragmentation rising',
            'deprecated call during {action} {target}',
            'retry succeeded for {target} after 1 attempt',
            '{target} size approaching limit',
        ],
        'retryable_keywords': [
            'network timeout on {target}',
            'temporary DNS failure for {target}',
            'upstream busy: {target} try later',
            'socket reset while streaming {target}',
            'transient checksum mismatch on {target}',
            'lease lost on {target}, can reacquire',
        ],
        'terminal_keywords': [
            'permanent authentication failure for {target}',
            '{target} file corrupt beyond repair',
            'out of disk writing {target}',
            'license for {target} has expired',
            'incompatible format version for {target}',
            'hardware fault on device backing {target}',
        ],
    },
]


def _fmt_body(rng, body, action, target):
    return body.format(action=action, target=target, lat=rng.choice([150, 240, 380, 610, 980]))


def gen_contextual(seed, n_examples, forced_test_class=None):
    rng = random.Random(seed)
    scheme = rng.choice(CONTEXTUAL_SCHEMES)
    tag = scheme['tag']

    # Sample distinct action/target pairs
    pairs = _mk_objects(rng, n_examples + 1)

    # Choose which bodies to use per severity
    pools = {
        'INFO': list(scheme['info_bodies']),
        'WARNING': list(scheme['warning_bodies']),
        'RETRYABLE_ERROR': list(scheme['retryable_keywords']),
        'TERMINAL_ERROR': list(scheme['terminal_keywords']),
    }
    for k in pools:
        rng.shuffle(pools[k])

    class_cycle = ['INFO', 'WARNING', 'RETRYABLE_ERROR', 'TERMINAL_ERROR']
    chosen = [class_cycle[i % 4] for i in range(n_examples)]
    rng.shuffle(chosen)

    # Track used bodies so test gets a fresh one
    used_idx = {k: 0 for k in pools}
    example_lines = []
    for i, cls in enumerate(chosen):
        action, target = pairs[i].split(' ', 1)
        body_tmpl = pools[cls][used_idx[cls] % len(pools[cls])]
        used_idx[cls] += 1
        body = _fmt_body(rng, body_tmpl, action, target)
        raw = f'{tag} {body}'
        example_lines.append(f'  {raw}    -> {cls}')
    material = '\n'.join(example_lines)

    # Build test line
    test_cls = forced_test_class if forced_test_class is not None else rng.choice(class_cycle)
    action, target = pairs[-1].split(' ', 1)
    # Prefer an unused body for the test class
    unused = pools[test_cls][used_idx[test_cls]:] or pools[test_cls]
    body_tmpl = rng.choice(unused)
    body = _fmt_body(rng, body_tmpl, action, target)
    test_input = f'{tag} {body}'
    expected = test_cls
    desc = f'contextual / tool={scheme["tool"]}'
    return material, test_input, expected, desc


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

COMPLEXITY_FNS = {
    'single_tag': gen_single_tag,
    'tag_plus_code': gen_tag_plus_code,
    'contextual': gen_contextual,
}
EVIDENCE = {'few': 5, 'mid': 8, 'many': 12}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}
# Deterministic per-complexity salt (avoids Python's salted string hash())
COMPLEXITY_SEED = {'single_tag': 11, 'tag_plus_code': 29, 'contextual': 53}
SEEDS = 3


def generate_dataset():
    """Generate 27 rows (3 complexities x 3 evidence levels x 3 seeds).

    Test classes are stratified across the 9 items per complexity to keep
    class balance reasonable and to force each complexity to probe all four
    severities, with extra emphasis on the RETRYABLE vs TERMINAL distinction
    (the core failure mode this benchmark is designed to surface).

    Per complexity (9 items): INFO x2, WARNING x2, RETRYABLE_ERROR x3, TERMINAL_ERROR x2.
    """
    test_class_pattern = [
        'INFO', 'WARNING', 'RETRYABLE_ERROR',
        'TERMINAL_ERROR', 'RETRYABLE_ERROR', 'INFO',
        'WARNING', 'TERMINAL_ERROR', 'RETRYABLE_ERROR',
    ]
    rows = []
    tid = 0
    for complexity, fn in COMPLEXITY_FNS.items():
        pos = 0
        for ev_label, n_examples in EVIDENCE.items():
            for seed in range(SEEDS):
                s = seed * 1000 + EVIDENCE_SEED[ev_label] * 7 + COMPLEXITY_SEED[complexity]
                forced = test_class_pattern[pos]
                material, test_input, expected, desc = fn(s, n_examples, forced_test_class=forced)
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid, 'seed': seed, 'complexity': complexity,
                    'evidence': ev_label, 'difficulty_label': label,
                    'material': material, 'test_input': test_input,
                    'expected': expected, 'item_desc': desc,
                })
                tid += 1
                pos += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'error_severity_triage_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'item_desc']].to_string(index=False))
