# Failure-Grounded Task Catalog

Each task below is abstracted from real failure modes observed in session mining. The goal: synthetic stimuli that reproduce the cognitive failure without leaking any actual session data. Every task fits the pre/study/post paradigm.

## Mapping Summary

| Task | Sub-Ability | Source Failures | Stimulus Type |
|---|---|---|---|
| Error Severity Triage | Concept Formation | warning-vs-error, retryable-vs-terminal | error log classification |
| Error → Remediation | Associative Learning | hallucinated CLI flags, error taxonomy | error message to fix mapping |
| Stale State Recovery | Procedural Learning | stale refs, state amnesia | tool call trace with recovery step |
| Tool Precondition Sequences | Procedural Learning | read-before-edit, snapshot-before-click | ordered operation requirement |
| Strategy Pivot Timing | Reinforcement Learning | combinatorial cycling, over-commitment | failed attempt history |
| Batch Error Diagnosis | Observational Learning | build-fix loops, piecemeal editing | multi-error traces |
| Precondition Checking | Procedural Learning | "already exists", 403 Forbidden | state-dependent actions |
| Cascade vs Root Cause | Concept Formation | sibling cascades, false positive errors | error dependency graphs |
| Resource Lock Protocol | Procedural Learning | browser lock, process singleton | contention traces |
| Granularity Selection | Observational Learning | full rewrites for one-line changes | edit scope decisions |

---

## Concept Formation Tasks (Classification)

### 1. Error Severity Triage
**Source failures:** warning-vs-error confusion (38444d75), "TeX Live 2025 is frozen" treated as retryable (e7b0c083), phantom errors from keyword false positives (2fa2fb99)

**Task:** Given an output line (stdout/stderr), classify severity: `INFO` / `WARNING` / `RETRYABLE_ERROR` / `TERMINAL_ERROR`.

**Pre:** Classify a single line without context.
**Study:** Given a mixed output with labels, articulate the classification rule (what distinguishes retryable from terminal, warning from error).
**Post:** Apply to new lines.

**Example stimulus:**
```
[INFO]     Loading dataset v2.0.0
[WARN]     Deprecated flag --old-mode, use --new-mode instead
[ERROR]    connection timeout, retry 1/3
[FATAL]    disk full: no space left on device
```
**Expected answer:** one of 4 labels per line.

---

### 2. Cascade vs Root Cause
**Source failures:** sibling tool call cascades (b908c7e6, 2fa2fb99), parallel execution failure propagation

**Task:** Given a failure graph (N operations with their error messages and dependencies), identify which failures are primary (root causes) and which are cascaded (consequences).

**Pre:** Pick the root cause from a small graph.
**Study:** Articulate rules for distinguishing primary vs cascaded failures.
**Post:** Apply to a larger graph.

**Example stimulus:** JSON describing 5 operations A-E with edges A→B→C, A→D, E standalone. All failed. Task: list only the root causes.

---

## Associative Learning Tasks (Mapping)

### 3. Error → Remediation Mapping
**Source failures:** hallucinated CLI flags `--libgs`, `--no-turbopack` (e7b0c083, b5fa9f59); error taxonomy confusion (slug 404 vs kernel ERROR status)

**Task:** Given novel (invented) CLI tool error messages and their correct remediation pairs, learn the mapping and apply to held-out errors.

**Pre:** Guess remediation for a new error cold.
**Study:** Study 6-10 error→fix pairs from an invented tool's manual.
**Post:** Apply to new errors using the same rules.

**Example stimulus:** Invented tool `kgl` with errors like `E2101: kernel slug mismatch` → `refresh slug from API before retry`. Test on unseen error codes that follow the same structural rules.

---

## Procedural Learning Tasks (Execution)

### 4. Stale State Recovery
**Source failures:** stale refs in browser automation (17446aea), state amnesia re-reading edited files (5297e436, e4e5baf1)

**Task:** Given a sequence of operations where intermediate state becomes invalid, determine when and how to re-acquire state.

**Pre:** Given a trace, identify at which step state invalidation occurred.
**Study:** Study worked examples showing invalidation triggers and correct re-acquisition.
**Post:** Apply the "invalidate-then-refresh" protocol to a new trace.

**Example stimulus:** Abstract world with `snapshot→act→act→mutate→act`. After `mutate`, refs from the first snapshot are stale. Correct answer: insert `snapshot` before the post-mutate `act`.

---

### 5. Tool Precondition Sequences
**Source failures:** edit-before-read violations (b908c7e6), snapshot-before-click violations (17446aea)

**Task:** Given a set of tools with hidden preconditions, learn the ordering rules from examples and apply to new tool sequences.

**Pre:** Given a sequence of tool calls, predict which will succeed/fail.
**Study:** Study worked traces showing precondition violations and corrected sequences.
**Post:** Validate a new sequence and insert missing preconditions.

**Example stimulus:** Tools `{A, B, C, D}` where `B` requires prior `A`, `D` requires prior `C`. Given `[A, D, B]`, the correct answer is the fixed sequence `[A, B, C, D]` or similar.

---

### 6. Precondition Checking for State-Dependent Actions
**Source failures:** "Category already exists" (38444d75), 403 Forbidden without auth check

**Task:** Given an action and the current world state, determine if preconditions are satisfied before attempting.

**Pre:** Directly attempt actions, score on success.
**Study:** Study action schemas with precondition specifications.
**Post:** For each proposed action, check preconditions first; only attempt if satisfied.

---

### 7. Resource Lock Protocol
**Source failures:** "Browser is already in use" (b908c7e6), ProcessSingleton failures

**Task:** Given a shared-resource scenario with contention, determine the correct acquire/wait/retry/release protocol.

**Pre:** Given a resource conflict, propose a recovery action.
**Study:** Study examples of correct lock handling (backoff, wait-and-retry, handoff signals).
**Post:** Apply protocol to new contention scenarios.

---

## Observational Learning Tasks (Learning from Traces)

### 8. Batch Error Diagnosis
**Source failures:** build-fix loops with 4 sequential build errors (b5fa9f59), 18 deploy cycles for single-feature changes (e4e5baf1), piecemeal editing (7 streaks of 3-9 single-line edits)

**Task:** Given a build/test output with multiple errors, identify ALL errors that need fixing (not just the first one).

**Pre:** Given build output with 5 errors, propose a fix for the first one only.
**Study:** Study worked examples showing complete-diagnosis-before-edit pattern.
**Post:** For new build output, list all required fixes and propose a single combined edit.

**Example stimulus:** Pseudo-TypeScript build output with 4 different error types (type mismatch, import missing, null check, syntax). Correct answer enumerates all 4 and proposes targeted fixes for each.

---

### 9. Granularity Selection
**Source failures:** Full file rewrites for single-line changes (721b7df5), Write-then-Read before Edit (5297e436)

**Task:** Given a before/after diff, classify the minimal operation needed: `edit` (targeted), `rewrite` (full file), `insert` (new cell/section), `delete` (removal).

**Pre:** Choose operation type without rules.
**Study:** Study examples showing when each operation type is appropriate (character-level % changed, structural disruption, etc.).
**Post:** Classify new diffs.

---

## Reinforcement Learning Tasks (Outcome-Based Learning)

### 10. Strategy Pivot Timing
**Source failures:** 133 run_code calls in one session (38444d75), 50 of 84 tool calls fighting TeX env (e7b0c083), over-commitment to broken approaches

**Task:** Given a history of failed attempts with the same strategy, decide whether to continue or pivot to alternative.

**Pre:** Given 3 failures, propose next action.
**Study:** Study worked examples showing pivot-trigger signals (same error N times, no state change across attempts, alternative available).
**Post:** Given new failure histories, decide: continue current strategy, adjust parameters, or pivot entirely.

**Example stimulus:** Synthetic history `[approach_A: fail, approach_A: fail, approach_A: fail]` with tool alternatives listed. Correct answer names an alternative strategy.

---

## Notes on Coverage vs Existing Benchmark

Current tasks in the benchmark (post-trim):
- Paired Associate ✓ (Associative)
- Rule Induction ✓ (Concept Formation)
- Novel Grammar Induction ✓ (Language Learning)
- Trace-Based Imitation ✓ (Observational)
- Skill Selection, Novel Algorithm Execution ✓ (Procedural)
- Multi-Armed Bandit ✓ (Reinforcement)

The failure-grounded tasks above would replace or supplement the weak tasks we trimmed. Strongest candidates to add:

1. **Error Severity Triage** → new Concept Formation task (groundedin real failures, not arithmetic pattern-matching)
2. **Error → Remediation Mapping** → replaces Analogy Completion as Associative Learning task
3. **Stale State Recovery** → new Procedural Learning task with clear learning signal
4. **Strategy Pivot Timing** → replaces Belief Revision as Reinforcement Learning task (actually tests RL-like outcome-based learning)
5. **Batch Error Diagnosis** → supplements Trace-Based Imitation in Observational Learning

## Language Learning Gap

No failure type maps naturally to Language Learning (grammar induction of a novel formal language). This sub-ability will keep its current task.
