# geno-bench

Mine Claude Code session logs for failure patterns. Turn observed failures into benchmark tasks.

## Install as a Claude Code skill

```bash
npx skills add 42euge/geno-bench -g -a claude-code -y
```

This installs geno-bench into `~/.claude/skills/geno-bench/`. In any Claude Code session, ask:

> "Mine my recent Claude Code sessions for failure patterns."

Claude will activate the skill and walk through the workflow.

## What it does

Claude Code stores every session as JSONL at `~/.claude/projects/<project-slug>/<session-id>.jsonl`. Those logs contain every tool call, error, retry, and back-and-forth. geno-bench provides:

1. **Scripts** to scan sessions and surface ones with evidence of agent failure (high thrashing, many errors, long loops)
2. **Analysis** to extract per-session failure patterns (error streaks, repeated resource access, tool distribution)
3. **Templates** for turning mined patterns into benchmark task designs

## Manual usage (no skill)

Clone the repo and run the scripts directly:

```bash
git clone https://github.com/42euge/geno-bench.git
cd geno-bench

# List sessions with evidence of failure
python3 scripts/list_sessions.py --min-thrash 0.3 --min-errors 10

# Deep-dive on a specific session by ID prefix
python3 scripts/analyze_session.py 17446aea

# Or pipe output to a markdown note
python3 scripts/analyze_session.py 17446aea > session_notes/2026-04-15_my-project_17446aea.md
```

No third-party dependencies. Uses only the Python standard library.

## Repo structure

```
geno-bench/
├── SKILL.md                    # skill definition (for npx skills installer)
├── README.md                   # this file
├── LICENSE                     # MIT
├── scripts/
│   ├── list_sessions.py        # inventory sessions with failure signals
│   └── analyze_session.py      # extract patterns from one session
├── templates/
│   ├── session_note.md         # template for per-session mining notes
│   └── task_catalog.md         # template for failure-to-task catalog
└── examples/
    └── sample_session_note.md  # what a filled-out note looks like
```

## Philosophy

LLM benchmarks usually test knowledge recall on static datasets. This workflow is for building benchmarks that test whether models can **learn from observed failures** — specifically, the kinds of failures that actually occur in agentic harnesses.

The failure taxonomy that emerges tends to cluster around a handful of cognitive gaps:
- **Stale state recovery** — retrying with invalidated references
- **Retry without diagnosis** — hitting the same error repeatedly without updating strategy
- **Tool-task mismatch** — using a fragile approach when a stable one exists
- **Warning vs error confusion** — treating non-blocking output as blocking
- **Precondition blindness** — mutating without checking current state
- **Strategy over-commitment** — not pivoting when the current approach plateaus

These map naturally to cognitive sub-abilities from learning science (concept formation, associative learning, procedural learning, reinforcement learning) and can be instantiated as synthetic benchmark tasks with the pre/study/post paradigm.

## License

MIT
