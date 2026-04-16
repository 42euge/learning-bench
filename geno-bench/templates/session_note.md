# Session Mining: {session_id_prefix}

- **Session ID:** {full_session_id}
- **Project:** {short_project_name}
- **Turns:** {total_turns} | **Tool calls:** {tool_calls_total} | **Errors:** {error_count}
- **Thrashing score:** {thrash_score}

## Top Error Patterns ({n_unique} unique)

| Count | Tool | Error |
|---|---|---|
| N | ToolName | First line of error message |

## Thrashing Details

| Hits | Resource |
|---|---|
| N | path or command that was re-accessed 3+ times |

## Error Streaks (N streaks of 3+ consecutive)

### Streak Pattern 1: {short_name}
Describe the pattern. Example: "Agent gets stale DOM ref, page changes, ref becomes invalid, agent retries with stale ref instead of re-snapshotting."

- Key error: `{example error line}`
- **Failure type:** {abstract category, e.g. "Not updating internal state after environment change"}

### Streak Pattern 2: {short_name}
...

## Tool Distribution

| Tool | Count |
|---|---|
| Bash | N |
| ToolX | N |

## Key Failure Types

Abstract the concrete failures above into categories:

1. **{Category}** — {one-sentence description}
2. **{Category}** — ...

## Potential Benchmark Abstractions

Each failure type below could become a synthetic task that tests whether a model can learn the correct response from examples:

1. **{Sub-ability} — {Task name}:** {one-sentence description of the pre/study/post paradigm applied to this failure}
2. ...

---

Notes:
- Be specific about what was NOVEL about this session's failures vs previous sessions.
- Don't restate failure types already catalogued elsewhere — just note their recurrence.
- If a high thrashing score was driven by user-directed iteration (not agent confusion), call that out explicitly.
