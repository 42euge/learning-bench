# Tasks

## Active
- [ ] run remaining tasks on Kaggle (grammar induction running on e2cdd)
- [ ] finalize writeup with cross-task results
- [ ] create cover image & media
- [ ] submit on Kaggle

## Backlog
- [ ] run all 12 tasks across full model ladder via Kaggle "Add Models" UI

## Done

- [x] define benchmark hypothesis (what new signal does it reveal?) → formal hypothesis in notes.md
- [x] review track research notes and pick benchmark concept → **Learning Curve Profiler**
- [x] setup repo (requirements.txt, kaggle-benchmarks SDK, project skeleton)
- [x] design task types with difficulty scaling → generators in `src/generators/`
- [x] build dataset with verifiable answers → `src/dataset.py` (1890 tasks)
- [x] implement benchmark with kaggle-benchmarks SDK → `src/benchmark.py`, `src/analysis.py`, `src/run_benchmark.py`
- [x] write tests → `tests/test_generators.py` (15/15 pass)
- [x] draft writeup → `writeup.md`
- [x] create Kaggle notebook → `notebook.py`
- [x] build skill_selection benchmark task — strong discriminatory power confirmed
- [x] extract all 12 datasets into standalone generate.py scripts
- [x] upload all 12 datasets to Kaggle
- [x] run scaling tests: skill_selection (best), novel_algorithm, category_learning, multi_armed_bandit
- [x] draft writeup for Skill Selection Under Context Pollution
