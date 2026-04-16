#!/usr/bin/env python3
"""Generate the strategy pivot benchmark dataset.

Goal: Given a history of attempts at solving a problem, decide whether to
    (a) CONTINUE the current strategy,
    (b) ADJUST_PARAMS (keep strategy, vary parameters), or
    (c) PIVOT to a different strategy.

Pivot-trigger rules encoded in the training material:
  - Same strategy failed 3+ times with identical error -> PIVOT
  - Failures show progress (different errors, state changing) -> ADJUST_PARAMS
  - First failure or clear progress -> CONTINUE
  - Known alternative strategies available + current is blocked -> PIVOT

Usage:
    python datasets/strategy_pivot/generate.py

Upload to Kaggle:
    kaggle datasets version -p datasets/strategy_pivot/ -m "Regenerated"
"""

import os
import random

import pandas as pd


# ---------------------------------------------------------------------------
# Domain vocabulary for generating plausible attempt histories
# ---------------------------------------------------------------------------

TASKS = [
    ('T-117', 'extract tabular data from a scanned PDF'),
    ('T-204', 'parse nested JSON from an HTTP endpoint'),
    ('T-331', 'install a native build toolchain'),
    ('T-458', 'scrape a JavaScript-rendered site'),
    ('T-502', 'convert a LaTeX document to HTML'),
    ('T-618', 'query a legacy SQL schema'),
    ('T-729', 'authenticate to a rate-limited API'),
    ('T-810', 'transcode a corrupted video file'),
    ('T-902', 'decompress an unknown archive format'),
    ('T-1011', 'fetch data through a corporate proxy'),
]

# (strategy_name -> list of plausible action templates)
STRATEGY_ACTIONS = {
    'regex_parse': ['re.search(p{n})', 'regex_match(pattern_v{n})', 'findall(expr={n})'],
    'ast_parse':   ['ast.parse(file_v{n})', 'parse_tree(version={n})', 'walk_ast(depth={n})'],
    'llm_extract': ['llm.extract(k={n})', 'prompt_extract(temp=0.{n})', 'few_shot(k={n})'],
    'ocr_pipeline':['ocr.run(dpi={n}00)', 'tesseract(psm={n})', 'easyocr(lang_set={n})'],
    'http_fetch':  ['requests.get(t={n}0)', 'urllib.open(retry={n})', 'httpx.get(timeout={n})'],
    'selenium':    ['driver.get(wait={n})', 'selenium.click(sel_v{n})', 'webdriver.load({n}s)'],
    'playwright':  ['page.goto(t={n}000)', 'pw.click(locator_v{n})', 'pw.wait_for({n}s)'],
    'js_inject':   ['page.evaluate(script_v{n})', 'exec_js(snippet_{n})', 'inject_hook({n})'],
    'tex_compile': ['pdflatex(run_{n})', 'xelatex(pass_{n})', 'lualatex(v={n})'],
    'pandoc':      ['pandoc(--to=html{n})', 'pandoc(filter_v{n})', 'pandoc(opts_{n})'],
    'manual_spec': ['spec_parse(v{n})', 'hand_grammar(r={n})', 'peg_parser(v{n})'],
    'subprocess':  ['subprocess.run(cmd_{n})', 'shell_exec(script_{n})', 'popen(arg={n})'],
    'api_client':  ['client.call(v{n})', 'sdk.invoke(retry={n})', 'rest.post(body_{n})'],
    'db_direct':   ['cursor.execute(q{n})', 'conn.fetch(stmt_{n})', 'sqlalchemy(q={n})'],
    'ffmpeg':      ['ffmpeg(-c:v v{n})', 'ffmpeg(-preset p{n})', 'ffmpeg(-crf {n})'],
    'vlc_headless':['vlc.convert(v{n})', 'cvlc(out_{n})', 'vlc.transcode({n})'],
}

# Errors are keyed by strategy to feel domain-consistent.
STRATEGY_ERRORS = {
    'regex_parse': [
        'no match for pattern',
        'catastrophic backtracking: regex timeout',
        'IndexError: group not found',
    ],
    'ast_parse': [
        'SyntaxError at line 1',
        'unsupported node type MatchStmt',
        'encoding error: non-utf8 bytes',
    ],
    'llm_extract': [
        'JSONDecodeError in model output',
        'schema mismatch: missing field "id"',
        'rate_limit: 429 from provider',
    ],
    'ocr_pipeline': [
        'empty output region',
        'low-confidence glyphs <0.2',
        'TesseractError: exit code 1',
    ],
    'http_fetch': [
        'ConnectionError: refused',
        'HTTP 403 Forbidden',
        'HTTP 429 rate limited',
        'ReadTimeout after 30s',
    ],
    'selenium': [
        'ElementNotInteractable',
        'TimeoutException waiting for selector',
        'StaleElementReferenceException',
    ],
    'playwright': [
        'TimeoutError: locator not found',
        'page closed before action',
        'net::ERR_ABORTED',
    ],
    'js_inject': [
        'ReferenceError: window.app undefined',
        'evaluation suppressed by CSP',
        'script returned null',
    ],
    'tex_compile': [
        '! Undefined control sequence \\begin{tabularx}',
        '! Package inputenc Error: unicode',
        '! Missing $ inserted',
    ],
    'pandoc': [
        'pandoc: unknown reader "tex+raw"',
        'YAML parse error in metadata',
        'filter returned non-zero',
    ],
    'manual_spec': [
        'grammar ambiguity at token <EQ>',
        'unexpected EOF in production',
        'left-recursion detected',
    ],
    'subprocess': [
        'exit code 127: command not found',
        'exit code 1: permission denied',
        'exit code 134: aborted (SIGABRT)',
    ],
    'api_client': [
        '401 Unauthorized',
        '500 Internal Server Error',
        'SSL handshake failure',
    ],
    'db_direct': [
        'ORA-00942: table or view does not exist',
        'connection reset by peer',
        'ambiguous column reference',
    ],
    'ffmpeg': [
        'moov atom not found',
        'Invalid data found when processing input',
        'Unknown encoder libx265',
    ],
    'vlc_headless': [
        'main libvlc error: stale plugins cache',
        'stream error: cannot demux',
        'access error: file not readable',
    ],
}

STRATEGY_FAMILIES = [
    # Each family provides a pool of >=3 plausible strategies that can coexist.
    ['regex_parse', 'ast_parse', 'llm_extract', 'manual_spec'],
    ['ocr_pipeline', 'llm_extract', 'regex_parse'],
    ['http_fetch', 'selenium', 'playwright', 'js_inject'],
    ['tex_compile', 'pandoc', 'manual_spec'],
    ['subprocess', 'api_client', 'db_direct'],
    ['ffmpeg', 'vlc_headless', 'subprocess'],
    ['http_fetch', 'api_client', 'playwright'],
]


def pick_family(rng):
    return list(rng.choice(STRATEGY_FAMILIES))


def fmt_action(strategy, n):
    tmpl = random.choice(STRATEGY_ACTIONS[strategy])  # non-seeded variety OK
    return tmpl.format(n=n)


# ---------------------------------------------------------------------------
# Attempt construction primitives
# ---------------------------------------------------------------------------

def attempt_line(i, strategy, action, outcome, error=None, state_changed=False):
    if outcome == 'SUCCESS':
        result = 'Result=SUCCESS'
    else:
        result = f'Result=ERROR "{error}"'
    sc = 'state_changed=yes' if state_changed else 'state_changed=no'
    return f'Attempt {i}: Strategy={strategy}, Action={action}, {result}, {sc}'


def build_stuck_history(rng, num_attempts, strategies):
    """All attempts use the same strategy, identical error, no state change.

    Expected answer: PIVOT.
    """
    strat = strategies[0]
    err = rng.choice(STRATEGY_ERRORS[strat])
    lines = []
    for i in range(1, num_attempts + 1):
        # Action templates vary but error is identical -> clear "stuck" signal
        act = fmt_action(strat, rng.randint(1, 9))
        lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=False))
    return lines, 'PIVOT'


def build_progress_history(rng, num_attempts, strategies):
    """Same strategy, different errors each time, state changing -> ADJUST_PARAMS."""
    strat = strategies[0]
    # Need distinct errors to show progress
    pool = list(STRATEGY_ERRORS[strat])
    rng.shuffle(pool)
    errs = [pool[i % len(pool)] for i in range(num_attempts)]
    # Force they are not all identical
    if len(set(errs)) == 1 and len(pool) > 1:
        errs[-1] = pool[1] if pool[1] != errs[0] else pool[-1]
    lines = []
    for i in range(1, num_attempts + 1):
        act = fmt_action(strat, i)
        lines.append(attempt_line(i, strat, act, 'FAILURE', error=errs[i - 1], state_changed=True))
    return lines, 'ADJUST_PARAMS'


def build_continue_history(rng, num_attempts, strategies):
    """Either first failure or most attempts succeeded recently -> CONTINUE."""
    strat = strategies[0]
    lines = []
    # Majority successes and the most recent attempt(s) succeeded.
    # End with a success so CONTINUE is the right call.
    mode = rng.choice(['first_failure', 'mostly_success'])
    if mode == 'first_failure':
        # Only one failure and it's the last one, but state changed and it's attempt 1-of-many? Use: success, success, ..., single recent failure? That's ambiguous.
        # Cleaner: all successes except a mid-sequence minor hiccup, ending on success.
        for i in range(1, num_attempts + 1):
            act = fmt_action(strat, i)
            if i == max(2, num_attempts // 2):
                err = rng.choice(STRATEGY_ERRORS[strat])
                lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=True))
            else:
                lines.append(attempt_line(i, strat, act, 'SUCCESS', state_changed=True))
    else:
        for i in range(1, num_attempts + 1):
            act = fmt_action(strat, i)
            lines.append(attempt_line(i, strat, act, 'SUCCESS', state_changed=True))
    return lines, 'CONTINUE'


# ---------- subtle variants ----------

def build_subtle_pivot(rng, num_attempts, strategies):
    """Same error appears 3+ times in a row with only cosmetic action changes.

    The attempts may include an early unrelated success with a different
    strategy, but the *current* strategy is clearly stuck.
    """
    strat = strategies[0]
    err = rng.choice(STRATEGY_ERRORS[strat])
    lines = []
    stuck_count = 0
    for i in range(1, num_attempts + 1):
        if i == 1 and num_attempts >= 5 and len(strategies) > 1:
            # Unrelated early success with a different strategy -> distractor
            other = strategies[1]
            lines.append(attempt_line(i, other, fmt_action(other, 1), 'SUCCESS', state_changed=True))
        else:
            act = fmt_action(strat, rng.randint(1, 9))
            lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=False))
            stuck_count += 1
    # Guarantee >=3 stuck failures
    assert stuck_count >= 3
    return lines, 'PIVOT'


def build_subtle_adjust(rng, num_attempts, strategies):
    """Same strategy, errors that LOOK similar at first glance but are
    meaningfully different (different numbers, different exception types),
    and state IS changing. Correct answer: ADJUST_PARAMS.
    """
    strat = strategies[0]
    pool = list(STRATEGY_ERRORS[strat])
    lines = []
    for i in range(1, num_attempts + 1):
        act = fmt_action(strat, i)
        err = pool[(i - 1) % len(pool)]
        # Add a unique numeric suffix so each error is distinct even if pool small
        err_variant = f'{err} (v{i})'
        lines.append(attempt_line(i, strat, act, 'FAILURE', error=err_variant, state_changed=True))
    return lines, 'ADJUST_PARAMS'


def build_subtle_continue(rng, num_attempts, strategies):
    """One recent failure amid a string of successes; state is advancing -> CONTINUE."""
    strat = strategies[0]
    lines = []
    fail_idx = num_attempts - 1  # second-to-last is the failure, last is success again
    for i in range(1, num_attempts + 1):
        act = fmt_action(strat, i)
        if i == fail_idx:
            err = rng.choice(STRATEGY_ERRORS[strat])
            lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=True))
        else:
            lines.append(attempt_line(i, strat, act, 'SUCCESS', state_changed=True))
    return lines, 'CONTINUE'


# ---------- adversarial variants ----------

def build_adversarial_continue(rng, num_attempts, strategies):
    """Looks scary (multiple failures) but each failure is on a DIFFERENT
    strategy and the CURRENT strategy (last one chosen) is progressing.

    Correct: CONTINUE. Models that over-weight raw failure counts will PIVOT.
    """
    strat = strategies[0]
    lines = []
    # Early noise: failures on other strategies
    num_noise = min(len(strategies) - 1, max(1, num_attempts - 3))
    for i in range(1, num_noise + 1):
        other = strategies[i % len(strategies)]
        err = rng.choice(STRATEGY_ERRORS[other])
        lines.append(attempt_line(i, other, fmt_action(other, i), 'FAILURE', error=err, state_changed=False))
    # Then the current strategy makes real progress and ends on success.
    for j in range(num_noise + 1, num_attempts + 1):
        act = fmt_action(strat, j)
        if j == num_attempts:
            lines.append(attempt_line(j, strat, act, 'SUCCESS', state_changed=True))
        else:
            err = rng.choice(STRATEGY_ERRORS[strat])
            lines.append(attempt_line(j, strat, act, 'FAILURE', error=f'{err} (different cause)', state_changed=True))
    return lines, 'CONTINUE'


def build_adversarial_adjust(rng, num_attempts, strategies):
    """Failures share a superficially similar message but they are clearly
    different underlying issues (different numeric codes, different line
    numbers) and state IS changing. Correct: ADJUST_PARAMS.

    Models that pattern-match on "same error string prefix" will PIVOT.
    """
    strat = strategies[0]
    base_err = rng.choice(STRATEGY_ERRORS[strat])
    lines = []
    for i in range(1, num_attempts + 1):
        act = fmt_action(strat, i)
        # Each error has a DIFFERENT numeric/line suffix -> progress
        err = f'{base_err} [code={100 + i * 7}, line={20 + i * 3}]'
        lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=True))
    return lines, 'ADJUST_PARAMS'


def build_adversarial_pivot(rng, num_attempts, strategies):
    """The strategy is truly stuck (same error, no state change) AND an
    alternative strategy was tried ONCE early and succeeded partially before
    being abandoned. This should trigger PIVOT (back to the known-working
    alternative).

    Models that assume "the latest strategy must be right" will CONTINUE.
    """
    strat = strategies[0]
    other = strategies[1] if len(strategies) > 1 else strategies[0]
    err = rng.choice(STRATEGY_ERRORS[strat])
    lines = []
    # One early partial success with the alternative
    lines.append(attempt_line(1, other, fmt_action(other, 1), 'SUCCESS', state_changed=True))
    # Then stuck loop on current strategy
    for i in range(2, num_attempts + 1):
        act = fmt_action(strat, rng.randint(1, 9))
        lines.append(attempt_line(i, strat, act, 'FAILURE', error=err, state_changed=False))
    return lines, 'PIVOT'


# ---------------------------------------------------------------------------
# Worked-example material (shared across items)
# ---------------------------------------------------------------------------

WORKED_EXAMPLES = """Here are worked examples that illustrate when to CONTINUE, ADJUST_PARAMS, or PIVOT.

Rules you should follow:
  1. If the same strategy has failed 3+ times with the SAME error and
     state_changed=no, choose PIVOT. The approach is stuck.
  2. If the same strategy is failing but the errors are DIFFERENT each time
     and state_changed=yes, choose ADJUST_PARAMS. Progress is being made.
  3. If the most recent attempt succeeded, or failures are limited to a
     single hiccup in an otherwise successful run, choose CONTINUE.
  4. A strategy that has not yet failed 3+ times on an identical error is
     not yet "stuck"; avoid pivoting prematurely.
  5. When evaluating the CURRENT strategy, ignore attempts that used a
     different strategy. Focus on the recent trajectory of the current one.

EXAMPLE 1 — PIVOT (same error 3x, no state change)
HISTORY for task DEMO-A:
Attempt 1: Strategy=selenium, Action=driver.get(wait=5), Result=ERROR "TimeoutException waiting for selector", state_changed=no
Attempt 2: Strategy=selenium, Action=driver.get(wait=10), Result=ERROR "TimeoutException waiting for selector", state_changed=no
Attempt 3: Strategy=selenium, Action=driver.get(wait=20), Result=ERROR "TimeoutException waiting for selector", state_changed=no
Available strategies: selenium, playwright, http_fetch
Next? -> PIVOT

EXAMPLE 2 — ADJUST_PARAMS (different errors, state changing)
HISTORY for task DEMO-B:
Attempt 1: Strategy=tex_compile, Action=pdflatex(run_1), Result=ERROR "! Undefined control sequence \\begin{tabularx}", state_changed=yes
Attempt 2: Strategy=tex_compile, Action=pdflatex(run_2), Result=ERROR "! Package inputenc Error: unicode", state_changed=yes
Attempt 3: Strategy=tex_compile, Action=pdflatex(run_3), Result=ERROR "! Missing $ inserted", state_changed=yes
Available strategies: tex_compile, pandoc, manual_spec
Next? -> ADJUST_PARAMS

EXAMPLE 3 — CONTINUE (mostly successful)
HISTORY for task DEMO-C:
Attempt 1: Strategy=http_fetch, Action=requests.get(t=30), Result=SUCCESS, state_changed=yes
Attempt 2: Strategy=http_fetch, Action=requests.get(t=40), Result=SUCCESS, state_changed=yes
Attempt 3: Strategy=http_fetch, Action=requests.get(t=50), Result=ERROR "HTTP 429 rate limited", state_changed=yes
Attempt 4: Strategy=http_fetch, Action=requests.get(t=60), Result=SUCCESS, state_changed=yes
Available strategies: http_fetch, api_client, playwright
Next? -> CONTINUE

EXAMPLE 4 — PIVOT (alternative available, current blocked)
HISTORY for task DEMO-D:
Attempt 1: Strategy=pandoc, Action=pandoc(--to=html1), Result=SUCCESS, state_changed=yes
Attempt 2: Strategy=tex_compile, Action=pdflatex(run_1), Result=ERROR "! Missing $ inserted", state_changed=no
Attempt 3: Strategy=tex_compile, Action=pdflatex(run_2), Result=ERROR "! Missing $ inserted", state_changed=no
Attempt 4: Strategy=tex_compile, Action=pdflatex(run_3), Result=ERROR "! Missing $ inserted", state_changed=no
Available strategies: tex_compile, pandoc, manual_spec
Next? -> PIVOT
"""


# ---------------------------------------------------------------------------
# Item generation dispatch
# ---------------------------------------------------------------------------

# For each complexity, we want to cover all three decisions across the 3 seeds
# so every cell in the grid has a mix of answers (avoids label-frequency shortcuts).
#
# 3 complexities x 3 evidence-levels x 3 seeds = 27 items.
# We cycle CONTINUE / ADJUST_PARAMS / PIVOT across the 3 seeds of each
# (complexity, evidence) cell so each cell contains one of each.

COMPLEXITIES = ['clear_signal', 'subtle_signal', 'adversarial']
EVIDENCE_LEVELS = [('few', 4), ('mid', 6), ('many', 8)]
SEEDS = 3

DECISIONS_PER_CELL = ['CONTINUE', 'ADJUST_PARAMS', 'PIVOT']

BUILDERS = {
    ('clear_signal',   'CONTINUE'):      build_continue_history,
    ('clear_signal',   'ADJUST_PARAMS'): build_progress_history,
    ('clear_signal',   'PIVOT'):         build_stuck_history,
    ('subtle_signal',  'CONTINUE'):      build_subtle_continue,
    ('subtle_signal',  'ADJUST_PARAMS'): build_subtle_adjust,
    ('subtle_signal',  'PIVOT'):         build_subtle_pivot,
    ('adversarial',    'CONTINUE'):      build_adversarial_continue,
    ('adversarial',    'ADJUST_PARAMS'): build_adversarial_adjust,
    ('adversarial',    'PIVOT'):         build_adversarial_pivot,
}


def build_test_input(rng, num_attempts, decision, complexity):
    task_id, task_desc = rng.choice(TASKS)
    strategies = pick_family(rng)
    # Ensure we have enough strategies listed
    if len(strategies) < 3:
        strategies = strategies + ['manual_spec', 'subprocess'][: 3 - len(strategies)]
    builder = BUILDERS[(complexity, decision)]
    lines, expected = builder(rng, num_attempts, strategies)
    assert expected == decision, f'builder mismatch: {complexity}/{decision} -> {expected}'
    body = '\n'.join(lines)
    prompt = (
        f'HISTORY for task {task_id} ({task_desc}):\n'
        f'{body}\n'
        f'Available strategies: {", ".join(strategies)}\n'
        f'Next?'
    )
    return prompt, expected


def generate_dataset():
    rows = []
    tid = 0
    for complexity in COMPLEXITIES:
        for ev_label, num_attempts in EVIDENCE_LEVELS:
            for seed in range(SEEDS):
                # Cycle decisions across seeds so each cell has one of each.
                decision = DECISIONS_PER_CELL[seed % 3]
                # Deterministic seeding: mix everything that varies the item.
                seed_value = (
                    seed * 1000
                    + COMPLEXITIES.index(complexity) * 137
                    + [e[0] for e in EVIDENCE_LEVELS].index(ev_label) * 29
                    + DECISIONS_PER_CELL.index(decision) * 7
                )
                rng = random.Random(seed_value)
                # Also seed the module random for action-template variety
                random.seed(seed_value)

                test_input, expected = build_test_input(rng, num_attempts, decision, complexity)

                difficulty_label = f'{complexity}_{ev_label}'
                item_desc = f'{complexity}_{ev_label}_s{seed}_{decision}'

                rows.append({
                    'task_id': tid,
                    'seed': seed,
                    'complexity': complexity,
                    'evidence': ev_label,
                    'num_attempts': num_attempts,
                    'difficulty_label': difficulty_label,
                    'material': WORKED_EXAMPLES,
                    'test_input': test_input,
                    'expected': expected,
                    'item_desc': item_desc,
                })
                tid += 1
    return pd.DataFrame(rows)


if __name__ == '__main__':
    dataset = generate_dataset()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'strategy_pivot_dataset.csv')
    dataset.to_csv(out_path, index=False)
    print(f'Generated {len(dataset)} rows -> {out_path}')
    print(dataset[['task_id', 'difficulty_label', 'expected', 'item_desc']].to_string(index=False))
    print('\nLabel distribution:')
    print(dataset['expected'].value_counts().to_string())
    print('\nBy complexity:')
    print(dataset.groupby(['complexity', 'expected']).size().to_string())
