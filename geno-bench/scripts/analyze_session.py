#!/usr/bin/env python3
"""Deep-dive analysis of a single Claude Code session.

Extracts: error patterns, thrashing details, tool distribution,
error streaks. Output is plain text ready to paste into a mining
note (or pipe into a markdown file).

Usage:
    python3 analyze_session.py <session_id_prefix>
    python3 analyze_session.py 17446aea
    python3 analyze_session.py /path/to/session.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _parser import discover_sessions, parse_session, thrashing_score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Session ID prefix or full path to .jsonl")
    parser.add_argument(
        "--base",
        type=str,
        default="",
        help="Override base dir (default: ~/.claude/projects)",
    )
    parser.add_argument("--streak-min", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    # Resolve target to a path
    target_path: Path | None = None
    tp = Path(args.target)
    if tp.suffix == ".jsonl" and tp.exists():
        target_path = tp
    else:
        for p in discover_sessions(args.base or None):
            if args.target in p.name:
                target_path = p
                break

    if target_path is None:
        print(f"No session found matching '{args.target}'", file=sys.stderr)
        return 1

    session = parse_session(target_path)
    score, thrash_details = thrashing_score(session)

    print(f"# Session Analysis: {session.session_id[:8]}")
    print()
    print(f"- **Session ID:** {session.session_id}")
    print(f"- **Project:** {_short_project(session.project)}")
    print(f"- **Start:** {session.start_time}")
    print(f"- **End:** {session.end_time}")
    print(f"- **Turns:** {session.total_turns} | **Tool calls:** {len(session.tool_calls)} | **Errors:** {session.error_count}")
    print(f"- **Thrashing score:** {score:.2f}")
    print()

    _print_error_patterns(session, args.top_n)
    _print_thrashing(thrash_details, args.top_n)
    _print_tool_freq(session)
    _print_error_streaks(session, args.streak_min, args.top_n // 2)

    return 0


def _print_error_patterns(session, top_n):
    patterns: dict[str, int] = {}
    for tc in session.tool_calls:
        result = tc.result or ""
        if tc.is_error or any(k in result.lower() for k in ("error", "traceback", "failed")):
            err_lines = [l.strip() for l in result.split("\n") if any(k in l.lower() for k in ("error", "traceback", "failed"))]
            summary = err_lines[0][:90] if err_lines else "unknown"
            key = f"{tc.tool_name} | {summary}"
            patterns[key] = patterns.get(key, 0) + 1

    if not patterns:
        print("## Error Patterns\n\nNone detected.\n")
        return

    print(f"## Error Patterns ({len(patterns)} unique)\n")
    print("| Count | Tool + Error |")
    print("|---|---|")
    for k, v in sorted(patterns.items(), key=lambda x: -x[1])[:top_n]:
        # Escape pipe chars for markdown
        k_safe = k.replace("|", "\\|")
        print(f"| {v} | {k_safe} |")
    print()


def _print_thrashing(details, top_n):
    if not details:
        print("## Thrashing\n\nNo resources accessed 3+ times.\n")
        return

    print("## Thrashing Details\n")
    print("| Hits | Resource |")
    print("|---|---|")
    for r, c in sorted(details.items(), key=lambda x: -x[1])[:top_n]:
        r_safe = r.replace("|", "\\|")
        print(f"| {c} | `{r_safe[:90]}` |")
    print()


def _print_tool_freq(session):
    freq: dict[str, int] = {}
    for tc in session.tool_calls:
        freq[tc.tool_name] = freq.get(tc.tool_name, 0) + 1

    print("## Tool Distribution\n")
    print("| Tool | Count |")
    print("|---|---|")
    for k, v in sorted(freq.items(), key=lambda x: -x[1]):
        print(f"| {k} | {v} |")
    print()


def _print_error_streaks(session, min_len, max_show):
    streaks: list[list] = []
    current: list = []
    for tc in session.tool_calls:
        result = tc.result or ""
        is_err = tc.is_error or any(k in result.lower() for k in ("error", "traceback", "failed"))
        if is_err:
            current.append(tc)
        else:
            if len(current) >= min_len:
                streaks.append(current)
            current = []
    if len(current) >= min_len:
        streaks.append(current)

    print(f"## Error Streaks ({len(streaks)} streaks of {min_len}+ consecutive)\n")
    if not streaks:
        print("None.\n")
        return

    for i, streak in enumerate(streaks[:max_show]):
        print(f"### Streak {i + 1}: {len(streak)} errors\n")
        for tc in streak[:5]:
            err = (tc.result or "")[:150]
            last_err_line = ""
            for l in reversed([l.strip() for l in err.split("\n") if l.strip()]):
                last_err_line = l[:90]
                break
            print(f"- `{tc.tool_name}` — {last_err_line}")
        if len(streak) > 5:
            print(f"- ... +{len(streak) - 5} more")
        print()


def _short_project(project: str) -> str:
    s = project.replace("-Users-", "").replace("-", "/").lstrip("/")
    if s.startswith("euge/"):
        s = s[len("euge/") :]
    return s


if __name__ == "__main__":
    raise SystemExit(main())
