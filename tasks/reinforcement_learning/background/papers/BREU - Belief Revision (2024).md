# Belief Revision: The Adaptability of Large Language Models Reasoning (2024)

#paper #literature #learning #metacognition

**Authors:** Bryan Wilie et al.
**Source:** arXiv:2406.19764 (EMNLP 2024)

## Key Contribution
Introduces Belief-R, a diagnostic dataset for evaluating belief revision in LLMs, and proposes the BREU (Belief Revision Evaluation Understudy) metric that measures both the ability to update beliefs given new evidence and the ability to maintain beliefs when updates are unwarranted.

## Problem Addressed
Humans routinely revise beliefs when confronted with new evidence (e.g., suppressing prior inferences). No systematic benchmark existed to test whether LLMs can perform this kind of adaptive reasoning -- updating when they should and maintaining when they should not.

## Method
- Constructs Belief-R dataset (~2K entries) within a delta reasoning (deltaR) framework, where models must decide whether new evidence warrants updating a prior belief.
- BREU metric averages BU-Acc (Belief Update Accuracy) and BM-Acc (Belief Maintain Accuracy), capturing the critical trade-off between over-updating and under-updating.
- Evaluates ~30 LLMs across diverse prompting strategies including chain-of-thought (CoT).
- Tests whether reasoning elicitation (CoT) improves belief revision ability.

## Key Results
- Larger LLMs tend to achieve higher BREU scores, but performance remains far below basic logical inference baselines.
- Models that are good at updating beliefs tend to underperform in scenarios where beliefs should be maintained, revealing a fundamental trade-off.
- Chain-of-thought prompting provides only ~1% BREU improvement, suggesting belief revision ability is not easily elicited through reasoning steps.
- The ability to revise beliefs appears to be a distinct capability from general reasoning.

## Limitations
- Dataset size (~2K) is relatively small; larger-scale evaluation may reveal different patterns.
- Focuses on propositional/logical belief revision; does not test revision of world knowledge or commonsense beliefs.
- Does not evaluate whether models can explain why they revised or maintained beliefs.

## Relevance to Our Research
Bridges the Learning and Metacognition tracks. Belief revision is central to adaptive learning (updating knowledge) and metacognition (knowing when your current beliefs are wrong). The BREU metric's dual measurement of update vs. maintain accuracy is a strong design pattern for our benchmark. The finding that CoT barely helps suggests we need novel evaluation approaches.

## Links
- Related: [[AbstentionBench (2025)]], [[LLMs Increase Confidence Despite Contradictions (2025)]]
