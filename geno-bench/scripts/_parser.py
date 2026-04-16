"""Minimal JSONL parser for Claude Code session logs.

Self-contained — no dependencies beyond the Python standard library.
Parses ~/.claude/projects/<slug>/<session-id>.jsonl into structured
tool-call records suitable for failure-pattern mining.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolCall:
    tool_name: str
    tool_id: str = ""
    input: Any = None
    result: str = ""
    is_error: bool = False
    duration_ms: float | None = None


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    timestamp: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class Session:
    session_id: str
    project: str
    path: Path
    start_time: str = ""
    end_time: str = ""
    turns: list[Turn] = field(default_factory=list)

    @property
    def total_turns(self) -> int:
        return len(self.turns)

    @property
    def tool_calls(self) -> list[ToolCall]:
        return [tc for t in self.turns for tc in t.tool_calls]

    @property
    def error_count(self) -> int:
        n = 0
        for tc in self.tool_calls:
            r = (tc.result or "").lower()
            if tc.is_error or "error" in r or "traceback" in r or "failed" in r:
                n += 1
        return n


def _extract_tool_calls(content_blocks: list[dict]) -> list[ToolCall]:
    calls: list[ToolCall] = []
    for block in content_blocks or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use":
            calls.append(
                ToolCall(
                    tool_name=block.get("name", "unknown"),
                    tool_id=block.get("id", ""),
                    input=block.get("input"),
                )
            )
    return calls


def _link_tool_results(turns: list[Turn]) -> None:
    """Walk turns and link tool_result blocks back to their tool_use parents."""
    id_to_call: dict[str, ToolCall] = {}
    for t in turns:
        for tc in t.tool_calls:
            if tc.tool_id:
                id_to_call[tc.tool_id] = tc

    # tool_result blocks appear in subsequent user turns
    # We need to re-scan the raw data for them, so this is a second pass
    # caller must supply raw records; handled in parse_session instead


def parse_session(path: str | os.PathLike) -> Session:
    """Parse a Claude Code JSONL session file."""
    path = Path(path)
    session_id = path.stem
    project = path.parent.name

    turns: list[Turn] = []
    id_to_call: dict[str, ToolCall] = {}
    start = ""
    end = ""

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = rec.get("timestamp", "")
            if ts and not start:
                start = ts
            if ts:
                end = ts

            msg = rec.get("message", {})
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content")

            # Normalize content to list
            blocks: list[dict] = []
            if isinstance(content, list):
                blocks = [b for b in content if isinstance(b, dict)]
            elif isinstance(content, str):
                blocks = [{"type": "text", "text": content}]

            # Tool results in user turns
            if role == "user":
                for b in blocks:
                    if b.get("type") == "tool_result":
                        tc = id_to_call.get(b.get("tool_use_id", ""))
                        if tc is not None:
                            result_content = b.get("content", "")
                            if isinstance(result_content, list):
                                # Content can be list of {type: text, text: ...}
                                parts = []
                                for p in result_content:
                                    if isinstance(p, dict) and p.get("type") == "text":
                                        parts.append(p.get("text", ""))
                                tc.result = "\n".join(parts)
                            else:
                                tc.result = str(result_content)
                            tc.is_error = bool(b.get("is_error", False))

            # Tool uses in assistant turns
            tool_calls = _extract_tool_calls(blocks) if role == "assistant" else []
            for tc in tool_calls:
                if tc.tool_id:
                    id_to_call[tc.tool_id] = tc

            turns.append(Turn(role=role, timestamp=ts, tool_calls=tool_calls))

    return Session(
        session_id=session_id,
        project=project,
        path=path,
        start_time=start,
        end_time=end,
        turns=turns,
    )


def discover_sessions(base: str | os.PathLike | None = None) -> list[Path]:
    """Find all JSONL session files under the Claude projects dir."""
    if base is None:
        base = os.path.expanduser("~/.claude/projects")
    base = Path(base)
    if not base.exists():
        return []
    paths: list[Path] = []
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".jsonl"):
                paths.append(Path(root) / f)
    return paths


def thrashing_score(session: Session) -> tuple[float, dict[str, int]]:
    """Compute thrashing = fraction of tool calls targeting a resource 3+ times.

    Returns (score, {resource: count}).
    """
    resource_counts: dict[str, int] = {}
    total = 0
    for tc in session.tool_calls:
        resource = _resource_key(tc)
        if resource is None:
            continue
        total += 1
        resource_counts[resource] = resource_counts.get(resource, 0) + 1
    if total == 0:
        return 0.0, {}
    thrashing = sum(c for c in resource_counts.values() if c >= 3)
    details = {r: c for r, c in resource_counts.items() if c >= 3}
    return thrashing / total, details


def _resource_key(tc: ToolCall) -> str | None:
    """Extract a stable resource identifier from a tool call."""
    if not isinstance(tc.input, dict):
        return None
    if tc.tool_name == "Bash":
        cmd = tc.input.get("command", "")
        return f"bash:{cmd[:80]}" if cmd else None
    for key in ("file_path", "notebook_path", "path"):
        if key in tc.input:
            return str(tc.input[key])
    return None
