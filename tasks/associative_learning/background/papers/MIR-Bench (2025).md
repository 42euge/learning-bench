# MIR-Bench (2025)

#paper #literature #learning

**Authors:** Kai Yan, Zhan Ling, Kang Liu, Yifan Yang, Ting-Han Fan, Lingfeng Shen, Zhengyin Du, Jiecao Chen
**Source:** arXiv:2502.09933 (NeurIPS 2025 Datasets & Benchmarks Track)

## Key Contribution
First benchmark specifically designed to evaluate many-shot in-context inductive reasoning in LLMs, testing whether models can recognize complicated patterns from hundreds to thousands of input-output examples without fine-tuning.

## Problem Addressed
Existing pattern-recognition benchmarks for LLMs focus on few-shot settings (typically <10 examples) and fail to evaluate the ability to aggregate information from long contexts. As LLM context windows grow, many-shot in-context learning (ICL) becomes a viable paradigm, but no benchmark systematically tested this capability for inductive reasoning.

## Method
- Constructs tasks where LLMs must predict outputs from underlying functions given many input-output demonstration pairs with diverse data formats.
- Studies scaling effects: how performance changes as the number of in-context examples increases.
- Evaluates robustness, inductive vs. transductive reasoning, RAG-based approaches, and coding-for-induction strategies.
- Tests cross-domain generalizability of pattern recognition abilities.
- Benchmarks multiple frontier LLMs across these dimensions.

## Key Results
- LLMs show meaningful scaling with more in-context examples but plateau well below perfect accuracy on complex patterns.
- Coding-based inductive reasoning (generating code that captures the pattern) can outperform direct prediction for some function types.
- Significant variation across models and pattern types, providing strong discriminatory power.
- Accepted at NeurIPS 2025 Datasets & Benchmarks.

## Limitations
- Patterns are generated from mathematical functions, which may not capture all forms of real-world inductive reasoning.
- Long-context performance is partially confounded by context window limitations and attention mechanisms.
- Does not test whether learned patterns transfer across sessions or tasks.

## Relevance to Our Research
Directly relevant to the Learning track. MIR-Bench demonstrates how to evaluate in-context learning at scale, a key dimension of whether models can acquire new knowledge. Its methodology for testing scaling effects and inductive vs. transductive reasoning provides a template for our benchmark design.

## Links
- Related: [[On the Measure of Intelligence (2019)]], [[SCAN (2018)]]
