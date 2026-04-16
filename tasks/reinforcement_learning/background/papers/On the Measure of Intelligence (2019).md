# On the Measure of Intelligence (2019)

#paper #literature #learning

**Authors:** Francois Chollet
**Source:** arXiv:1911.01547

## Key Contribution
Proposes a formal definition of intelligence as skill-acquisition efficiency (not skill itself), grounded in Algorithmic Information Theory, and introduces the Abstraction and Reasoning Corpus (ARC) as a benchmark for human-like general fluid intelligence.

## Problem Addressed
AI benchmarking conflates task-specific skill with intelligence. Measuring skill at specific tasks (e.g., board games, video games) is heavily modulated by prior knowledge and experience, making it a poor proxy for general intelligence. No formal, actionable definition of intelligence existed that could guide benchmark design.

## Method
- Surveys and critically assesses definitions of intelligence from psychology and AI, identifying two historical conceptions (task-specific skill vs. general cognitive ability).
- Formalizes intelligence as skill-acquisition efficiency over a scope of tasks, weighted by priors, generalization difficulty, and experience.
- Introduces Core Knowledge priors (objectness, numerosity, basic geometry, agentness) drawn from developmental psychology as the assumed shared priors for fair comparison.
- Designs ARC: a set of novel visual reasoning tasks requiring abstraction and analogy, resistant to brute-force memorization.
- Each ARC task provides a few input-output grid demonstrations; the solver must infer the transformation rule and apply it to a new input.

## Key Results
- ARC tasks are solvable by most humans but extremely difficult for ML systems, demonstrating a large gap between human fluid intelligence and current AI.
- Highlights that high performance on narrow benchmarks (e.g., ImageNet, Go) does not imply progress toward general intelligence.
- ARC has since become the foundation of the ARC-AGI challenge, a major open benchmark for measuring general reasoning.

## Limitations
- ARC relies on visual grid puzzles, which may not capture all dimensions of intelligence (e.g., linguistic, social).
- The Core Knowledge priors are assumed rather than empirically validated as the minimal shared priors between humans and machines.
- Does not address how to train systems that perform well on ARC-style tasks.

## Relevance to Our Research
Foundational paper for the Learning track. ARC-AGI defines the gold standard for measuring whether models can acquire new skills from minimal examples rather than relying on memorized patterns. Our benchmark design should follow Chollet's principle: measure generalization efficiency, not memorized skill.

## Links
- Related: [[MIR-Bench (2025)]], [[SCAN (2018)]], [[MTOB (2023)]]
