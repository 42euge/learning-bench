### Project Name

GenoBench-learning


### Your Team

Eugenio Rivera Ramos


### Problem Statement

Do frontier models learn, or just recall? Jagged intelligence is a frequent complaint about coding models but is difficult to articulate precisely — models excel at some tasks and fail at structurally similar ones, especially when the problem is genuinely new. Can we measure that gap in a practical way?

Agentic harness systems are multi-step pipelines where the critical failure mode isn't typically lack of knowledge, but the inability to effectively use and manipulate context to discover proper solutions. A model must do two things: externalize its understanding into a context (notes, observations, intermediate reasoning), and then effectively use that context to solve a downstream problem. These are separable skills, and current benchmarks measure neither.

### Task & benchmark construction

GenoBench-Learning isolates both parts of this context-learning problem. The benchmark decomposes learning into two scored sub-problems: how well can a model construct a useful learned context from novel stimuli, and how well can it apply that context to solve a new instance? Each is measured independently and baselined against a one-shot approach.

Tasks span six cognitive sub-abilities using a pre/post study paradigm on stimuli designed to fall outside training data. The model is scored before and after a structured self-study phase in which it must articulate the underlying rule in its own words. Learning gain — the delta between pre- and post-study accuracy — is the primary signal.

| Sub-Ability | Task | Source |
|---|---|---|
| Associative Learning | Paired Associate | procedural generation |
| Associative Learning | Error Remediation | session mining |
| Concept Formation | Rule Induction | procedural generation |
| Concept Formation | Error Severity Triage | session mining |
| Language Learning | Novel Grammar Induction | procedural generation |
| Observational Learning | Trace-Based Imitation | procedural generation |
| Observational Learning | Batch Error Diagnosis | session mining |
| Procedural Learning | Skill Selection, Novel Algorithm Execution | procedural generation |
| Procedural Learning | Stale State Recovery | session mining |
| Reinforcement Learning | Multi-Armed Bandit | procedural generation |
| Reinforcement Learning | Strategy Pivot | session mining |

### Dataset

Stimuli come from two sources, both designed to fall outside training data:

**Procedural generation.** Six tasks use algorithmically generated stimuli — novel vocabularies, artificial grammars, invented classification rules, and synthetic execution traces. Each task produces a 3x3x3 difficulty grid (complexity × evidence × seed = 27 items) to ensure statistical stability and scaling visibility.

**Session mining.** Five tasks are grounded in real failure patterns mined from 620 Claude Code session logs across 46 projects using geno-bench (`geno-bench/`). We scanned for sessions with high thrashing scores (repeated resource access) and error streaks (3+ consecutive failures), then abstracted the failure shapes — stale state recovery, error severity confusion, strategy over-commitment, error-to-remediation mapping, and batch diagnosis failures — into synthetic stimuli. No raw session data appears in the benchmark; only the structural failure patterns are preserved.

### Technical details

**Pre/post study paradigm.** Every task follows an identical three-phase protocol: (1) pre-test — the model answers cold, measuring baseline capability; (2) study — the model analyzes worked examples and articulates the underlying rule in its own words; (3) post-test — the model answers the same question conditioned on its own study notes. Learning gain (post − pre accuracy) is the primary metric.

**Session mining pipeline (geno-bench).** We built an open-source tool (`geno-bench/`) that parses Claude Code JSONL session logs from `~/.claude/projects/`. For each session it computes: error patterns (tool + error type, grouped by frequency), thrashing score (fraction of tool calls targeting resources accessed 3+ times), error streaks (consecutive failures indicating no-progress loops), and tool distribution. Sessions are ranked by a composite "interestingness" signal (thrashing + error density). Analysts then write structured mining notes that categorize failures and propose benchmark abstractions. The tool is installable as a Claude Code skill: `npx skills add 42euge/geno-bench -g -a claude-code -y`.

**Evaluation.** Tasks run on the Kaggle Benchmarks platform using the `kaggle_benchmarks` SDK. Each task is a self-contained notebook with a `@kbench.task` decorated function. Models are evaluated via the Kaggle LLM proxy, enabling head-to-head comparison across providers without local inference.


### Results, insights, and conclusions

The benchmark reveals what standard evaluations cannot: not just whether a model knows things, but whether it can learn new things on demand, and whether explicit self-generated reasoning aids that learning.

A key methodological insight is that benchmark tasks can be systematically derived from observed agentic failures rather than invented from scratch. By mining 620 real Claude Code sessions across 46 projects, we identified 15 recurring failure categories (stale state, retry without diagnosis, tool-task mismatch, warning-as-error confusion, strategy over-commitment, etc.) and abstracted five of them into benchmark tasks. This grounding in real failures ensures the benchmark tests abilities that actually matter in deployed systems — the stimuli are synthetic, but the cognitive gaps they target are empirically observed.



### Organizational affiliations

Blue Origin; University of Washington. All work was completed using personal resources only, with no institutional support or resources.


### References & citations

- geno-bench: session mining tool for Claude Code. https://github.com/42euge/geno-bench
- Kaggle Benchmarks SDK (kaggle-benchmarks). https://github.com/Kaggle/kaggle-benchmarks
- Morris et al. "Measuring Progress Toward AGI: A Cognitive Framework." Google DeepMind, 2026.
- vercel-labs/skills: open agent skills ecosystem. https://github.com/vercel-labs/skills
