### Project Name

GenoBench-learning


### Your Team

Eugenio Rivera Ramos


### Problem Statement

Do frontier models learn, or just recall? Jagged intelligence is a frequent complaint about coding models but is difficult to articulate precisely — models excel at some tasks and fail at structurally similar ones, especially when the problem is genuinely new. Can we measure that gap in a practical way?

Agentic harness systems are multi-step pipelines where the critical failure mode isn't typically lack of knowledge, but the inability to effectively use and manipulate context to discover proper solutions. A model must do two things: externalize its understanding into a context (notes, observations, intermediate reasoning), and then effectively use that context to solve a downstream problem. These are separable skills, and current benchmarks measure neither.

### Task & benchmark construction

GenoBench-Learning isolates both parts of this context-learning problem. The benchmark decomposes learning into two scored sub-problems: how well can a model construct a useful learned context from novel stimuli, and how well can it apply that context to solve a new instance? Each is measured independently and baselined against a one-shot approach.

Tasks span five cognitive sub-abilities using a pre/post study paradigm on stimuli designed to fall outside training data. The model is scored before and after a structured self-study phase in which it must articulate the underlying rule in its own words. Learning gain — the delta between pre- and post-study accuracy — is the primary signal.

| Sub-Ability | Tasks |
|---|---|
| Associative Learning | Analogy Completion, Sequence Extrapolation, Paired Associate |
| Concept Formation | Category Learning, Prototype Extraction, Rule Induction |
| Language Learning | Novel Grammar Induction |
| Observational Learning | Trace-Based Imitation |
| Reinforcement Learning | Belief Revision, Multi-Armed Bandit, Skill Selection |


### Dataset


### Technical details


### Results, insights, and conclusions
The benchmark reveals what standard evaluations cannot: not just whether a model knows things, but whether it can learn new things on demand, and whether explicit self-generated reasoning aids that learning.



### Organizational affiliations

Blue Origin; University of Washington. All work was completed using personal resources only, with no institutional support or resources.


### References & citations
