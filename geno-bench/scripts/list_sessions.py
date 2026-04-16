#!/usr/bin/env python3
"""List Claude Code sessions with failure signals.

Scans ~/.claude/projects/**.jsonl and surfaces sessions with evidence
of agent trouble: high thrashing score, many errors, or long tool
loops. Output is sorted by a rough "interestingness" score.

Usage:
    python3 list_sessions.py
    python3 list_sessions.py --min-thrash 0.3 --min-errors 10
    python3 list_sessions.py --project-filter learning
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _parser import discover_sessions, parse_session, thrashing_score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-thrash", type=float, default=0.0)
    parser.add_argument("--min-errors", type=int, default=0)
    parser.add_argument("--min-tools", type=int, default=10)
    parser.add_argument("--project-filter", type=str, default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--base",
        type=str,
        default="",
        help="Override base dir (default: ~/.claude/projects)",
    )
    args = parser.parse_args()

    paths = discover_sessions(args.base or None)
    if not paths:
        print("No sessions found. Is Claude Code installed?", file=sys.stderr)
        return 1

    rows = []
    for path in paths:
        try:
            session = parse_session(path)
        except Exception as e:
            print(f"[warn] failed to parse {path.name}: {e}", file=sys.stderr)
            continue

        if args.project_filter and args.project_filter.lower() not in session.project.lower():
            continue

        score, _ = thrashing_score(session)
        errors = session.error_count
        n_tools = len(session.tool_calls)
        turns = session.total_turns

        if n_tools < args.min_tools:
            continue
        if score < args.min_thrash and errors < args.min_errors:
            continue

        interest = score + errors / 100
        rows.append(
            {
                "interest": interest,
                "sid": session.session_id[:8],
                "thrash": score,
                "errors": errors,
                "turns": turns,
                "tools": n_tools,
                "project": _short_project(session.project),
            }
        )

    rows.sort(key=lambda r: -r["interest"])
    rows = rows[: args.limit]

    if not rows:
        print("No sessions match the filters.")
        return 0

    print(f"{'sid':10s}  {'thrash':>6s}  {'errors':>6s}  {'turns':>5s}  {'tools':>5s}  project")
    print("-" * 90)
    for r in rows:
        print(
            f"{r['sid']:10s}  "
            f"{r['thrash']:6.2f}  "
            f"{r['errors']:6d}  "
            f"{r['turns']:5d}  "
            f"{r['tools']:5d}  "
            f"{r['project'][:55]}"
        )
    print(f"\n{len(rows)} sessions shown.")
    return 0


def _short_project(project: str) -> str:
    """Shorten the project dir name."""
    # Claude projects encode paths as -Users-euge-code-foo
    s = project.replace("-Users-", "").replace("-", "/").lstrip("/")
    # Collapse leading user segment
    if s.startswith("euge/"):
        s = s[len("euge/") :]
    return s


if __name__ == "__main__":
    raise SystemExit(main())
