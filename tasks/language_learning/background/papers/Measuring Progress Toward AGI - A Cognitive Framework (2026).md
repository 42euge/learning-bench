# Measuring Progress Toward AGI: A Cognitive Framework (2026)

#paper #literature #foundational

**Authors:** Ryan Burnell, Yumeya Yamamori, Orhan Firat, Kate Olszewska, Steph Hughes-Fitt, Oran Kelly, Isaac R. Galatzer-Levy, Meredith Ringel Morris, Allan Dafoe, Alison M. Snyder, Noah D. Goodman, Matthew Botvinick, Shane Legg
**Source:** Google DeepMind (March 2026) / https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/measuring-progress-toward-agi/measuring-progress-toward-agi-a-cognitive-framework.pdf

## Key Contribution
A comprehensive cognitive taxonomy that deconstructs general intelligence into 10 key cognitive faculties, drawing from psychology, neuroscience, and cognitive science, with a three-stage evaluation protocol for benchmarking AI systems against human performance distributions.

## Problem Addressed
Existing approaches to measuring AI progress toward AGI lack a principled, scientifically grounded framework rooted in the cognitive sciences. There was no systematic way to evaluate AI systems across the full breadth of cognitive abilities relative to human baselines.

## Method
- Defines 10 cognitive faculties: Perception, Generation, Attention, Learning, Memory, Reasoning, Metacognition, Executive Functions, Problem-Solving, and Social Cognition.
- Proposes a three-stage evaluation protocol:
  1. Evaluate AI across a broad suite of cognitive tasks covering each ability, using held-out test sets.
  2. Collect human baselines from a demographically representative sample of adults.
  3. Map AI performance relative to the distribution of human performance per ability.
- Identifies five abilities with the largest evaluation gaps: Learning, Metacognition, Attention, Executive Functions, and Social Cognition.
- Launched the Kaggle hackathon to crowdsource benchmark creation for under-evaluated abilities.

## Key Results
- Establishes that current AI evaluation has significant blind spots in key cognitive areas.
- The five under-evaluated abilities (Learning, Metacognition, Attention, Executive Functions, Social Cognition) are precisely the tracks of the associated Kaggle hackathon.
- Provides the theoretical foundation for the entire competition.

## Limitations
- Framework is descriptive/taxonomic rather than providing ready-made evaluation tools.
- Human baselines are resource-intensive to collect at scale.
- Some cognitive faculties (e.g., perception, memory) may require modality-specific evaluations beyond text.

## Relevance to Our Research
This is THE foundational paper for the hackathon. Our benchmark must align with this framework's definition of Social Cognition and its evaluation protocol. The three-stage protocol (AI tasks, human baselines, comparative mapping) should guide our methodology. Understanding how Social Cognition is defined here -- understanding and navigating social situations -- sets the scope for our benchmark design.

## Links
- Related: [[Triangulating LLM Progress (2025)]], [[GINC (2021)]]
- Blog: https://blog.google/innovation-and-ai/models-and-research/google-deepmind/measuring-agi-cognitive-framework/
- Kaggle competition: https://www.kaggle.com/competitions/kaggle-measuring-agi
