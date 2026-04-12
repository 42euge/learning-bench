# Tasks

## Active
- [ ] run against multiple frontier models (needs MODEL_PROXY_API_KEY in .env)
- [ ] build skill_selection benchmark task — can a model learn to pick the right tool as options grow and context gets noisy

## Backlog
- [ ] analyze results & discriminatory power (automated in `src/analysis.py`, needs model results)
- [ ] finalize writeup with actual results (draft in `writeup.md`)
- [ ] create cover image & media
- [ ] submit on Kaggle

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
