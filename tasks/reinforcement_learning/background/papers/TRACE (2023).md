# TRACE: A Comprehensive Benchmark for Continual Learning in Large Language Models (2023)

#paper #literature #learning

**Authors:** Xiao Wang, Yuan Zhang, Tianze Chen, Songyang Gao, Senjie Jin, Xianjun Yang, Zhiheng Xi, Rui Zheng, Yicheng Zou, Tao Gui, Qi Zhang, Xuanjing Huang
**Source:** arXiv:2310.06762

## Key Contribution
Introduces TRACE, a comprehensive continual learning benchmark for LLMs comprising 8 distinct datasets across domain-specific tasks, multilingual capabilities, code generation, and mathematical reasoning. Also proposes Reasoning-augmented Continual Learning (RCL) to mitigate catastrophic forgetting.

## Problem Addressed
LLMs need to continuously acquire new knowledge without forgetting previously learned capabilities. While continual learning is well-studied in traditional ML, no comprehensive benchmark existed to evaluate it specifically for LLMs across diverse task types, measuring both forward transfer and catastrophic forgetting.

## Method
- Constructs 8 diverse datasets spanning domain-specific knowledge, multilingual tasks, code generation, and math reasoning.
- Measures both task-specific performance gains and degradation of general abilities after continual training.
- Compares full-parameter training vs. LoRA training approaches.
- Evaluates impact on instruction-following capabilities.
- Proposes RCL: integrates task-specific cues with meta-rationales to reduce catastrophic forgetting while maintaining learning on new tasks.

## Key Results
- Nearly all models exhibit significant decline in general abilities after continual learning, especially in math/reasoning (e.g., llama2-chat 13B accuracy on GSM8K dropped from 28.8% to 2%).
- Multilingual abilities are the exception: they generally improve with continual training (e.g., TydiQA F1 score improved from 23.47 to 33.23).
- Full-parameter training fits target tasks better but causes more severe forgetting than LoRA.
- Instruction-following capabilities suffer significant reduction after continual learning.
- RCL approach reduces catastrophic forgetting while expediting convergence on new tasks.

## Limitations
- Focuses on fine-tuning-based continual learning; does not evaluate in-context continual learning.
- Limited to open-source models; does not test proprietary frontier models.
- Does not measure whether models can selectively retain vs. update knowledge.

## Relevance to Our Research
Directly relevant to the Learning track. TRACE demonstrates how to measure whether models can acquire new knowledge without losing old knowledge -- a fundamental challenge for genuine learning. The finding that different capability types (math vs. multilingual) respond differently to continual learning provides important design considerations for our benchmark tasks.

## Links
- Related: [[On the Measure of Intelligence (2019)]], [[BREU - Belief Revision (2024)]]
