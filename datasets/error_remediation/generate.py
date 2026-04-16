#!/usr/bin/env python3
"""Generate the error remediation benchmark dataset.

Task: Given error messages from an invented CLI tool `zkl`, learn the mapping
from error patterns to correct remediation actions. The failure mode we're
testing: hallucinated CLI flags / wrong remediation. Models must learn the
ACTUAL documented remediation, not guess.

Invented tool:
    zkl — a fictional package-and-deployment CLI.
    Error codes:
        E1xxx = network / registry
        E2xxx = filesystem / cache
        E3xxx = auth / credentials

Complexity levels:
    direct_lookup  -> exact code -> fixed remediation (1:1 lookup)
    pattern_match  -> code prefix + keyword in message -> remediation family
    multi_factor   -> code family AND context keyword jointly select remediation

Evidence levels:
    few  = 5 pairs
    mid  = 7 pairs
    many = 10 pairs

3 seeds x 3 complexity x 3 evidence = 27 items.

Usage:
    python datasets/error_remediation/generate.py
"""

import os
import random

import pandas as pd


# === Invented CLI vocabulary ===

TOOL = 'zkl'

# Specific error codes used in direct_lookup mapping. Remediation commands are
# invented but deterministic: model must LEARN them from the examples.
DIRECT_CODES = {
    'E1001': 'zkl registry refresh --scope global',
    'E1007': 'zkl registry refresh --scope user',
    'E1014': 'zkl net retry --backoff 5s',
    'E1022': 'zkl net retry --backoff 30s',
    'E1031': 'zkl proxy reset',
    'E2003': 'zkl cache purge --deep',
    'E2011': 'zkl cache purge --shallow',
    'E2018': 'zkl fs relink --force',
    'E2024': 'zkl fs repair --index',
    'E2040': 'zkl fs repair --manifest',
    'E3002': 'zkl auth rotate --keyring',
    'E3008': 'zkl auth rotate --token',
    'E3015': 'zkl auth login --provider sso',
    'E3019': 'zkl auth trust --renew',
    'E3027': 'zkl auth login --provider oauth',
}

# For pattern_match: the remediation depends on the code family (E1/E2/E3) AND
# a keyword in the message body (not on the exact code).
# Family verb + keyword suffix determines the action.
FAMILY_VERBS = {
    'E1': 'refresh',  # network family -> refresh something
    'E2': 'purge',    # filesystem -> purge something
    'E3': 'rotate',   # auth -> rotate something
}

# Keyword -> target noun that gets plugged into the remediation
PATTERN_KEYWORDS = {
    'E1': {
        'mirror': 'mirror',
        'upstream': 'registry',
        'dns': 'resolver',
        'cert': 'ca-bundle',
        'tunnel': 'proxy',
    },
    'E2': {
        'inode': 'index',
        'manifest': 'manifest',
        'shard': 'shard-cache',
        'vault': 'blob-store',
        'lock': 'lockfile',
    },
    'E3': {
        'keyring': 'keyring',
        'token': 'token',
        'session': 'session',
        'device': 'device-trust',
        'scope': 'scope-map',
    },
}

# For multi_factor: remediation depends on code family AND one of two context
# qualifiers in the message (cold-start vs hot-path, or first-run vs retry).
# The combination picks a specific flag.
MULTI_QUALIFIERS = ['cold-start', 'hot-path']
MULTI_TABLE = {
    # (family, qualifier) -> (verb, target, flag)
    ('E1', 'cold-start'): ('bootstrap', 'registry', '--seed'),
    ('E1', 'hot-path'):   ('reconnect', 'registry', '--keepalive'),
    ('E2', 'cold-start'): ('rebuild',   'cache',    '--from-manifest'),
    ('E2', 'hot-path'):   ('compact',   'cache',    '--online'),
    ('E3', 'cold-start'): ('provision', 'credentials', '--enroll'),
    ('E3', 'hot-path'):   ('refresh',   'credentials', '--silent'),
}


# === Message generators ===

DIRECT_TEMPLATES = [
    '{code}: operation failed during {ctx}.',
    '[{code}] {ctx} did not complete.',
    'error {code} raised by {ctx}.',
    '{code} reported while handling {ctx}.',
]

DIRECT_CTX = {
    'E1': ['package sync', 'registry handshake', 'index download', 'dependency fetch'],
    'E2': ['workspace open', 'layer extraction', 'snapshot write', 'object commit'],
    'E3': ['session bootstrap', 'credential load', 'identity attach', 'grant verify'],
}

PATTERN_TEMPLATES = [
    '{code}: {keyword} check failed for target "{target}".',
    '[{code}] {keyword} subsystem reports invalid state at "{target}".',
    'error {code} while validating {keyword} for "{target}".',
    '{code} raised by {keyword} reconciler on "{target}".',
]

MULTI_TEMPLATES = [
    '{code}: failure detected on {qualifier} pathway for "{target}".',
    '[{code}] {qualifier} run aborted while touching "{target}".',
    'error {code} observed on a {qualifier} attempt against "{target}".',
    '{code} emitted by the {qualifier} executor handling "{target}".',
]

TARGETS = [
    'acme-core', 'bluefin-utils', 'redline-sdk', 'north-star', 'pivot-tools',
    'glacier-net', 'quartz-runtime', 'ember-cli', 'nimbus-store', 'slate-auth',
    'opal-queue', 'verdant-lib', 'onyx-gate', 'fjord-sync', 'halo-index',
]


# === Builders ===

def _families():
    return ['E1', 'E2', 'E3']


def _random_code(rng, family):
    """Generate a random unseen code in the given family (not in DIRECT_CODES)."""
    used = set(DIRECT_CODES.keys())
    for _ in range(200):
        num = rng.randint(100, 999)
        code = f'{family}{num:03d}'[:5]  # E1 + 3 digits -> 5 chars total like E1123
        if len(code) == 5 and code not in used:
            return code
    # fallback
    return f'{family}{rng.randint(100,999):03d}'


def _fmt_pair(err_msg, remediation):
    return f'  ERROR: {err_msg}\n  FIX:   {remediation}'


# --- direct_lookup ---

def gen_direct(seed, n_pairs):
    """direct_lookup: exact error code -> exact remediation command.

    Study material: n_pairs (code, remediation) examples.
    Test: one of the studied codes wrapped in a new message template.
    """
    rng = random.Random(seed)
    codes = list(DIRECT_CODES.keys())
    rng.shuffle(codes)
    study_codes = codes[:n_pairs]

    pairs = []
    for code in study_codes:
        fam = code[:2]
        ctx = rng.choice(DIRECT_CTX[fam])
        tmpl = rng.choice(DIRECT_TEMPLATES)
        err = tmpl.format(code=code, ctx=ctx)
        pairs.append((err, DIRECT_CODES[code], code))

    # Test pair: pick a studied code from the second half (avoid primacy)
    test_idx = n_pairs // 2 + rng.randint(0, max(0, n_pairs // 2 - 1))
    test_code = study_codes[test_idx]
    fam = test_code[:2]
    # Use a DIFFERENT template / context than any shown, so recognition must
    # come from the code, not the sentence.
    ctx = rng.choice(DIRECT_CTX[fam])
    tmpl = rng.choice(DIRECT_TEMPLATES)
    test_err = tmpl.format(code=test_code, ctx=ctx)
    test_rem = DIRECT_CODES[test_code]

    rng.shuffle(pairs)
    material_pairs = [(p[0], p[1]) for p in pairs]
    desc = 'direct_lookup: exact code -> exact remediation'
    return material_pairs, test_err, test_rem, desc


# --- pattern_match ---

def gen_pattern(seed, n_pairs):
    """pattern_match: family prefix + keyword -> remediation pattern.

    Remediation shape: `zkl <verb> <noun>` where verb = FAMILY_VERBS[family]
    and noun = PATTERN_KEYWORDS[family][keyword]. The test is a NEW code in a
    studied family with a studied keyword in a new target — the model must
    apply the rule, not look up an exact code.
    """
    rng = random.Random(seed + 1000)
    pairs = []
    used_keys = set()

    # Generate n_pairs distinct (family, keyword) examples, covering all
    # families at least once if possible.
    families = _families()
    # Build a pool with at least 2 from each family when n_pairs allows
    pool = []
    for fam in families:
        kws = list(PATTERN_KEYWORDS[fam].keys())
        rng.shuffle(kws)
        for kw in kws:
            pool.append((fam, kw))
    rng.shuffle(pool)

    # ensure we choose a set that covers 3 families
    chosen = []
    fam_counts = {f: 0 for f in families}
    for fam, kw in pool:
        if len(chosen) >= n_pairs:
            break
        if fam_counts[fam] < (n_pairs // 3 + 1):
            chosen.append((fam, kw))
            fam_counts[fam] += 1
    # top up if short
    for fam, kw in pool:
        if len(chosen) >= n_pairs:
            break
        if (fam, kw) not in chosen:
            chosen.append((fam, kw))

    for fam, kw in chosen[:n_pairs]:
        code = _random_code(rng, fam)
        target = rng.choice(TARGETS)
        tmpl = rng.choice(PATTERN_TEMPLATES)
        err = tmpl.format(code=code, keyword=kw, target=target)
        verb = FAMILY_VERBS[fam]
        noun = PATTERN_KEYWORDS[fam][kw]
        rem = f'{TOOL} {verb} {noun}'
        pairs.append((err, rem))
        used_keys.add((fam, kw))

    # Test: pick a (family, keyword) pair that was SHOWN (so rule applies),
    # but with a NEW code and NEW target.
    test_fam, test_kw = rng.choice(list(used_keys))
    test_code = _random_code(rng, test_fam)
    test_target = rng.choice(TARGETS)
    test_err = rng.choice(PATTERN_TEMPLATES).format(
        code=test_code, keyword=test_kw, target=test_target)
    verb = FAMILY_VERBS[test_fam]
    noun = PATTERN_KEYWORDS[test_fam][test_kw]
    test_rem = f'{TOOL} {verb} {noun}'

    rng.shuffle(pairs)
    desc = 'pattern_match: family prefix + keyword -> verb+noun remediation'
    return pairs, test_err, test_rem, desc


# --- multi_factor ---

def gen_multi(seed, n_pairs):
    """multi_factor: (family, qualifier) jointly determine remediation.

    Remediation: `zkl <verb> <target> <flag>`.
    Both family and qualifier (cold-start vs hot-path) are needed. If a model
    uses only one factor, it will be wrong on the disambiguating test.
    """
    rng = random.Random(seed + 2000)
    pairs = []
    combos_shown = set()

    combos = list(MULTI_TABLE.keys())
    rng.shuffle(combos)

    # Cycle through combos so each is shown at least once when n_pairs >= 6
    i = 0
    while len(pairs) < n_pairs:
        fam, qual = combos[i % len(combos)]
        code = _random_code(rng, fam)
        target = rng.choice(TARGETS)
        verb, tgt_noun, flag = MULTI_TABLE[(fam, qual)]
        tmpl = rng.choice(MULTI_TEMPLATES)
        err = tmpl.format(code=code, qualifier=qual, target=target)
        rem = f'{TOOL} {verb} {tgt_noun} {flag}'
        pairs.append((err, rem))
        combos_shown.add((fam, qual))
        i += 1

    # Test must be a combo that was shown (so answer is derivable) but with
    # NEW code and NEW target. Prefer a combo where BOTH the same-family-
    # different-qualifier and same-qualifier-different-family were also
    # shown, so the model can only answer correctly by using BOTH factors.
    # Start with any shown combo from the second half of the study list.
    candidates = []
    for combo in combos_shown:
        fam, qual = combo
        # sibling combos (disambiguators)
        same_fam_other_q = (fam, 'hot-path' if qual == 'cold-start' else 'cold-start')
        other_fam_same_q = None
        for f in _families():
            if f != fam and (f, qual) in combos_shown:
                other_fam_same_q = (f, qual)
                break
        if same_fam_other_q in combos_shown and other_fam_same_q is not None:
            candidates.append(combo)
    if not candidates:
        candidates = list(combos_shown)

    test_fam, test_qual = rng.choice(candidates)
    test_code = _random_code(rng, test_fam)
    test_target = rng.choice(TARGETS)
    test_err = rng.choice(MULTI_TEMPLATES).format(
        code=test_code, qualifier=test_qual, target=test_target)
    verb, tgt_noun, flag = MULTI_TABLE[(test_fam, test_qual)]
    test_rem = f'{TOOL} {verb} {tgt_noun} {flag}'

    rng.shuffle(pairs)
    desc = 'multi_factor: (family, qualifier) -> verb+target+flag remediation'
    return pairs, test_err, test_rem, desc


COMPLEXITY_FNS = {
    'direct_lookup': gen_direct,
    'pattern_match': gen_pattern,
    'multi_factor': gen_multi,
}
EVIDENCE = {'few': 5, 'mid': 7, 'many': 10}
EVIDENCE_SEED = {'few': 0, 'mid': 1, 'many': 2}
SEEDS = 3


def generate_dataset():
    rows = []
    tid = 0
    for complexity, fn in COMPLEXITY_FNS.items():
        for ev_label, n_pairs in EVIDENCE.items():
            for seed in range(SEEDS):
                pairs, test_err, test_rem, desc = fn(
                    seed * 100 + EVIDENCE_SEED[ev_label], n_pairs)
                material = '\n'.join(_fmt_pair(e, r) for e, r in pairs)
                label = f'{complexity}_{ev_label}'
                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': complexity,
                    'evidence': ev_label,
                    'difficulty_label': label,
                    'material': material,
                    'test_input': test_err,
                    'expected': test_rem,
                    'item_desc': desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'error_remediation_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'test_input', 'expected']].to_string(index=False))
