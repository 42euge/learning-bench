# Session Mining: abc12345 (example — fabricated, not real)

- **Session ID:** abc12345-0000-0000-0000-000000000000
- **Project:** example/web-scraper
- **Turns:** 412 | **Tool calls:** 138 | **Errors:** 27
- **Thrashing score:** 0.41

## Top Error Patterns (12 unique)

| Count | Tool | Error |
|---|---|---|
| 8 | browser_click | Ref e803 not found in the current page snapshot |
| 6 | Bash | HTTPError 429: Too Many Requests |
| 4 | browser_navigate | Navigation timeout after 30000ms |
| 3 | Edit | File has been modified since read |
| 2 | Bash | unknown option '--no-verify' |

## Thrashing Details

| Hits | Resource |
|---|---|
| 14 | `https://example.com/products` |
| 9 | `bash:curl -s https://api.example.com/v2/list` |
| 6 | `scraper/parser.py` |

## Error Streaks (5 streaks of 3+ consecutive)

### Streak Pattern 1: Stale DOM ref thrashing
Agent captures a page snapshot, clicks an element (uses ref `e803`), page state updates, agent tries to click a second element still using refs from the old snapshot. 8 consecutive failures before it eventually re-snapshots.

- Key error: `Ref e803 not found in the current page snapshot`
- **Failure type:** No protocol for re-acquiring state after environment change

### Streak Pattern 2: Rate limit without backoff
Agent gets 429 from an API, retries immediately 6 times with no delay.

- Key error: `HTTPError 429: Too Many Requests`
- **Failure type:** Missing exponential backoff; treating transient errors as permanent

### Streak Pattern 3: Hallucinated CLI flag
Agent invents `--no-verify` on a tool that doesn't support it, gets `unknown option`, retries the same invalid flag once before giving up.

- Key error: `unknown option '--no-verify'`
- **Failure type:** Fabricating tool capabilities instead of consulting `--help`

## Tool Distribution

| Tool | Count |
|---|---|
| Bash | 71 |
| browser_snapshot | 22 |
| browser_click | 18 |
| Read | 11 |
| Edit | 9 |
| browser_navigate | 7 |

## Key Failure Types

1. **Stale state thrashing** — agent doesn't re-snapshot after environment-mutating actions
2. **Transient vs permanent error confusion** — 429s and timeouts should trigger backoff, not retry
3. **CLI hallucination** — agent fabricates flags instead of checking docs
4. **Read-before-edit violations** — external tools modify files between agent reads, edits fail

## Potential Benchmark Abstractions

Each failure type could become a synthetic task:

1. **Procedural Learning — Stale State Recovery:** given a sequence of operations where one is environment-mutating, identify where to insert a re-snapshot. Pre/study/post paradigm with worked examples of invalidation triggers.

2. **Concept Formation — Error Severity Triage:** given a mixed log with labeled examples (INFO/WARN/RETRYABLE/TERMINAL), classify new lines. Tests whether model can distinguish "429 rate limit" (retryable) from "403 forbidden" (often terminal).

3. **Associative Learning — Error to Remediation Mapping:** invented CLI tool with novel error codes. Study 6-10 (error, fix) pairs, apply to held-out errors. Prevents cold-guessing.

4. **Procedural Learning — Tool Precondition Sequences:** novel tools with hidden ordering constraints (X must precede Y). Study worked examples of valid/invalid orderings, apply to new sequences.

---

**Notes on novelty vs prior sessions:**
- Stale DOM ref thrashing is common across sessions (previously seen in session `xyz67890`)
- Rate-limit-without-backoff is new for this session
- CLI hallucination was also observed in session `def45678`
