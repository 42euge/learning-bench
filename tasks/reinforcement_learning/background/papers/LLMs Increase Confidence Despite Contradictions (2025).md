# When Two LLMs Debate, Both Think They'll Win (2025)

#paper #literature #learning #metacognition

**Authors:** Pradyumna Shyama Prasad, Minh Nhat Nguyen
**Source:** arXiv:2505.19184

## Key Contribution
Reveals that LLMs exhibit pathological confidence dynamics during adversarial debates: confidence escalates from 72.9% to 83.3% across rounds, both sides simultaneously claim >75% victory probability in 61.7% of debates, and this anti-Bayesian pattern persists even when models are told their odds are exactly 50%.

## Problem Addressed
As LLMs are deployed in multi-agent systems, debates, and advisory roles, understanding whether their confidence calibration is rational becomes critical. Rational Bayesian agents should moderate confidence when encountering strong counterarguments, but no systematic study had tested whether LLMs follow this principle during adversarial interactions.

## Method
- Sets up controlled debate experiments between LLMs on topics with verifiable outcomes.
- Tracks confidence ratings across opening, middle, and closing rounds of debates.
- Tests self-play conditions: identical LLMs debating each other, with and without information about opponent capability.
- Analyzes private scratchpad reasoning vs. public confidence statements for faithfulness.
- Tests intervention: explicitly informing models their odds are 50%.

## Key Results
- **Confidence escalation:** Average confidence rises from 72.9% (opening) to 83.3% (closing) -- directly contradicts Bayesian updating.
- **Mutual overestimation:** In 61.7% of debates, both sides simultaneously claim >=75% win probability -- a logical impossibility.
- **Persistent bias:** Even when debating identical models and told odds are 50%, confidence still rises from 50% to 57.1%.
- **Misaligned reasoning:** Private scratchpad thoughts sometimes differ from public confidence, raising faithfulness concerns.
- These patterns are consistent across multiple frontier models.

## Limitations
- Debate format is somewhat artificial; real-world deployment scenarios may differ.
- Confidence is self-reported, not derived from probability distributions over outputs.
- Limited to text-based debates; does not test confidence in other modalities.
- Does not propose a solution to the pathological confidence escalation.

## Relevance to Our Research
Bridges Learning and Metacognition tracks. Demonstrates that LLMs fail at a fundamental metacognitive task: calibrating confidence in response to new evidence. This is closely related to belief revision (BREU) but in a dynamic, adversarial setting. Provides strong motivation for benchmarks that test whether models can appropriately lower confidence when confronted with contradictory evidence.

## Links
- Related: [[BREU - Belief Revision (2024)]], [[AbstentionBench (2025)]], [[Self-Correction Bench (2025)]]
