---
name: geno-bench
description: Mine Claude Code session logs for failure patterns and abstract them into evaluation tasks. Use when the user asks to analyze their Claude Code sessions for recurring bugs, thrashing, error loops, or wants to build benchmarks grounded in real agent failures.
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# geno-bench

A workflow for mining failure patterns from Claude Code session logs and turning them into synthetic benchmark tasks.

## When to use

Activate this skill when the user asks to:
- Analyze their Claude Code sessions for failure patterns
- Find recurring bugs or thrashing in agent transcripts
- Identify where agents get stuck, retry without diagnosis, or loop
- Build benchmarks grounded in real agent failures (not invented scenarios)
- Turn observed failures into learnable evaluation tasks

## What it does

Session mining extracts five signals from Claude Code JSONL logs:
1. **Error patterns** — tool calls with failing results, grouped by type
2. **Error streaks** — 3+ consecutive failures (evidence of no-progress loops)
3. **Thrashing** — same resource accessed 3+ times (stuck state)
4. **Tool distribution** — which tools dominate, which barely used
5. **Strategy commitment** — over-commitment to single approach

These become inputs for categorizing failures (stale state, retry without diagnosis, wrong tool, warning-as-error, etc.) and ultimately for synthesizing benchmark tasks that test whether models can learn from these failure modes.

## Instructions

When the user asks to mine their sessions:

### Step 1: Inventory
Run `scripts/list_sessions.py` to see all sessions with their thrashing/error metrics. Filter to the most interesting ones (thrash > 0.3 OR errors > 10 AND tools > 20).

```bash
python3 scripts/list_sessions.py --min-thrash 0.3 --min-errors 10
```

### Step 2: Deep-dive on high-signal sessions
For each interesting session, run `scripts/analyze_session.py <session_id>` to extract:
- Error pattern counts
- Thrashing details (what file/command was re-accessed)
- Tool frequency
- Error streaks (3+ consecutive failures)

```bash
python3 scripts/analyze_session.py <session_id_prefix>
```

### Step 3: Write up findings
For each analyzed session, write a markdown note in `session_mining/` using the template at `templates/session_note.md`. Name it `{YYYY-MM-DD}_{project-slug}_{session_id_prefix}.md`.

Each note should cover:
- Session metadata (id, project, turns, tools, errors, thrashing)
- Top error patterns table
- Thrashing details
- Tool distribution
- Error streaks with brief descriptions of what went wrong
- Key failure types (abstract categories, e.g. "retry without diagnosis")
- Potential benchmark abstractions (how this could become a learnable task)

**Critical:** Focus on failure TYPES that are novel. Once you've seen stale-ref thrashing in one session, note its recurrence but don't re-explain it in every subsequent note.

### Step 4: Build a task catalog (optional)
Once you've mined 5+ sessions across different projects, use `templates/task_catalog.md` to organize the failure types into benchmark task designs. Each task should:
- Name the failure it targets
- Map to a cognitive sub-ability (concept formation, associative learning, etc.)
- Describe a synthetic pre/study/post paradigm that tests whether models can learn from examples of the failure

### Important guardrails

- **Privacy:** Session logs contain user prompts, file paths, and potentially sensitive content. Never commit raw session data to public repos. Notes are abstractions — they should reference session IDs and counts, not raw content.
- **False positives:** The error detection heuristic flags any result containing "error" or "failed". Many will be false positives (source code mentioning error handling, rubric text). Confirm real errors before pattern-matching.
- **Thrashing ≠ failure:** A high thrashing score can reflect user-driven iteration (many edits to the same file because the user keeps asking for tweaks), not agent confusion. Cross-check against the narrative.

## Output format

A typical mining session produces:
1. `session_mining/*.md` — one note per analyzed session
2. `TASK_CATALOG.md` — synthesized failure taxonomy and task designs (if the user wants a benchmark)

Do not generate code for the benchmark tasks themselves unless explicitly asked — the catalog is the deliverable.
