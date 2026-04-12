#!/usr/bin/env python3
"""Generate the novel grammar induction benchmark dataset.

Usage:
    python datasets/novel_grammar_induction/generate.py

Output:
    datasets/novel_grammar_induction/novel_grammar_induction_dataset.csv

Upload to Kaggle:
    kaggle datasets version -p datasets/novel_grammar_induction/ -m "Regenerated"
"""

import os
import random

import pandas as pd

# === Word classes with nonsense words ===
NOUNS = ['wug', 'blick', 'dax']
VERBS = ['fep', 'tup', 'niz']
ADJS  = ['ral', 'gom']
DETS  = ['sib', 'vex']

# === Difficulty grid constants ===
COMPLEXITY = ['simple', 'medium', 'complex']
EVIDENCE = [4, 8, 12]   # few, mid, many example sentences
SEEDS = 3

# Deterministic integer mapping for seeds (no hash())
COMPLEXITY_SEED = {'simple': 0, 'medium': 1, 'complex': 2}
EVIDENCE_SEED = {4: 0, 8: 1, 12: 2}


# === Helper ===

def starts_with_vowel(w):
    return w[0] in 'aeiou'


# === Simple grammar: DET NOUN VERB (fixed word order, no agreement) ===

def gen_simple_sentences(rng, n):
    """Generate n valid sentences: DET NOUN VERB."""
    max_unique = len(DETS) * len(NOUNS) * len(VERBS)  # 18
    n = min(n, max_unique)
    sents = set()
    while len(sents) < n:
        sents.add((rng.choice(DETS), rng.choice(NOUNS), rng.choice(VERBS)))
    return [' '.join(s) for s in sents]


def gen_simple_violations(rng, valid_sents):
    """Generate violations: wrong word order."""
    tests = []
    # Valid test sentence
    s = (rng.choice(DETS), rng.choice(NOUNS), rng.choice(VERBS))
    tests.append((' '.join(s), 'yes'))
    # NOUN DET VERB (swap det/noun)
    s2 = (rng.choice(NOUNS), rng.choice(DETS), rng.choice(VERBS))
    tests.append((' '.join(s2), 'no'))
    # VERB NOUN DET (reversed)
    s3 = (rng.choice(VERBS), rng.choice(NOUNS), rng.choice(DETS))
    tests.append((' '.join(s3), 'no'))
    # DET VERB NOUN (verb before noun)
    s4 = (rng.choice(DETS), rng.choice(VERBS), rng.choice(NOUNS))
    tests.append((' '.join(s4), 'no'))
    return tests


# === Medium grammar: DET NOUN VERB with agreement ===
# Rule: "sib" pairs with consonant-initial nouns, "vex" with vowel-initial
# Verb agreement: if det is "sib", verb takes suffix "-a"; if "vex", verb takes suffix "-o"

def medium_det_for_noun(noun):
    return 'vex' if starts_with_vowel(noun) else 'sib'


def medium_verb_form(verb, det):
    return verb + 'a' if det == 'sib' else verb + 'o'


def gen_medium_sentences(rng, n):
    """Generate n valid sentences: DET NOUN VERB+suffix with agreement."""
    max_unique = len(NOUNS) * len(VERBS)  # 9 (det is determined by noun)
    n = min(n, max_unique)
    sents = set()
    while len(sents) < n:
        noun = rng.choice(NOUNS)
        det = medium_det_for_noun(noun)
        verb = rng.choice(VERBS)
        vf = medium_verb_form(verb, det)
        sents.add((det, noun, vf))
    return [' '.join(s) for s in sents]


def gen_medium_violations(rng, valid_sents):
    """Generate violations: agreement errors."""
    tests = []
    # Valid
    noun = rng.choice(NOUNS)
    det = medium_det_for_noun(noun)
    verb = rng.choice(VERBS)
    vf = medium_verb_form(verb, det)
    tests.append((f'{det} {noun} {vf}', 'yes'))
    # Wrong determiner (use opposite)
    noun2 = rng.choice(NOUNS)
    wrong_det = 'vex' if medium_det_for_noun(noun2) == 'sib' else 'sib'
    verb2 = rng.choice(VERBS)
    vf2 = medium_verb_form(verb2, wrong_det)  # verb agrees with wrong det
    tests.append((f'{wrong_det} {noun2} {vf2}', 'no'))
    # Wrong verb suffix (det is correct but verb suffix mismatches)
    noun3 = rng.choice(NOUNS)
    det3 = medium_det_for_noun(noun3)
    verb3 = rng.choice(VERBS)
    wrong_suffix = 'o' if det3 == 'sib' else 'a'
    tests.append((f'{det3} {noun3} {verb3}{wrong_suffix}', 'no'))
    # Wrong word order
    noun4 = rng.choice(NOUNS)
    det4 = medium_det_for_noun(noun4)
    verb4 = rng.choice(VERBS)
    vf4 = medium_verb_form(verb4, det4)
    tests.append((f'{noun4} {det4} {vf4}', 'no'))
    return tests


# === Complex grammar: DET ADJ NOUN VERB (DET NOUN) -- nested object clause ===
# Same det-noun agreement as medium, plus:
# - ADJ must precede NOUN
# - Object clause: (DET NOUN) with its own agreement
# - Verb suffix: "-a"/"-o" based on SUBJECT det (not object det)

def gen_complex_sentence(rng):
    """Generate one valid complex sentence: DET ADJ NOUN VERB(suffix) DET NOUN."""
    subj_noun = rng.choice(NOUNS)
    subj_det = medium_det_for_noun(subj_noun)
    adj = rng.choice(ADJS)
    verb = rng.choice(VERBS)
    vf = medium_verb_form(verb, subj_det)
    obj_noun = rng.choice(NOUNS)
    obj_det = medium_det_for_noun(obj_noun)
    return (subj_det, adj, subj_noun, vf, obj_det, obj_noun)


def complex_to_str(parts):
    return ' '.join(parts)


def gen_complex_sentences(rng, n):
    """Generate n valid complex sentences."""
    max_unique = len(NOUNS) * len(ADJS) * len(VERBS) * len(NOUNS)  # 54
    n = min(n, max_unique)
    sents = set()
    while len(sents) < n:
        sents.add(gen_complex_sentence(rng))
    return [complex_to_str(s) for s in sents]


def gen_complex_violations(rng, valid_sents):
    """Generate violations: agreement, order, nesting errors."""
    tests = []
    # Valid
    s = gen_complex_sentence(rng)
    tests.append((complex_to_str(s), 'yes'))
    # Wrong subject det-noun agreement
    s2 = list(gen_complex_sentence(rng))
    s2[0] = 'vex' if s2[0] == 'sib' else 'sib'  # flip subject det
    tests.append((complex_to_str(s2), 'no'))
    # Wrong object det-noun agreement
    s3 = list(gen_complex_sentence(rng))
    s3[4] = 'vex' if s3[4] == 'sib' else 'sib'  # flip object det
    tests.append((complex_to_str(s3), 'no'))
    # Missing adjective (DET NOUN VERB DET NOUN -- wrong structure)
    s4 = gen_complex_sentence(rng)
    tests.append((f'{s4[0]} {s4[2]} {s4[3]} {s4[4]} {s4[5]}', 'no'))
    return tests


# === Dataset generation ===

GEN_FUNCS = {
    'simple':  (gen_simple_sentences, gen_simple_violations),
    'medium':  (gen_medium_sentences, gen_medium_violations),
    'complex': (gen_complex_sentences, gen_complex_violations),
}


def generate_dataset():
    rows = []
    tid = 0

    for complexity in COMPLEXITY:
        gen_sents, gen_viols = GEN_FUNCS[complexity]
        for n_ex in EVIDENCE:
            for seed in range(SEEDS):
                rng = random.Random(
                    seed * 100 + EVIDENCE_SEED[n_ex] * 10 + COMPLEXITY_SEED[complexity]
                )
                valid_examples = gen_sents(rng, n_ex)
                test_items = gen_viols(rng, valid_examples)
                material = '\n'.join(f'  {s}' for s in valid_examples)
                label = f'{complexity}_{n_ex}ex'

                for test_sent, expected_ans in test_items:
                    rows.append({
                        'task_id': tid,
                        'seed': seed,
                        'complexity': complexity,
                        'evidence': f'{n_ex}_examples',
                        'difficulty_label': label,
                        'material': material,
                        'test_sentence': test_sent,
                        'expected': expected_ans,
                        'item_desc': f'{complexity} grammar, {n_ex} examples, seed {seed}',
                    })
                    tid += 1

    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'novel_grammar_induction_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(f'Complexity levels: {COMPLEXITY}')
    print(f'Evidence levels: {EVIDENCE}')
    print()
    for _, row in dataset.iterrows():
        print(f'  [{row["difficulty_label"]:12s}] test="{row["test_sentence"]}"  expected={row["expected"]}')
