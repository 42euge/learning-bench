# Learning Benchmark — GenoBench

Kaggle benchmark for the **Learning** track of the Google DeepMind x Kaggle AGI Hackathon. Tests whether frontier LLMs can acquire and apply new knowledge in-context, not just recall from training data.

## Structure

- `datasets/` — one folder per task with `generate.py` (deterministic data generator) and `dataset-metadata.json` (Kaggle dataset config). Generated CSVs are gitignored.
- `tasks/` — Kaggle benchmark kernels organized by learning sub-ability (`associative_learning/`, `concept_formation/`, `language_learning/`, `observational_learning/`, `procedural_learning/`, `reinforcement_learning/`). Each sub-ability has a `kernel-metadata.json`; each task has its own `.ipynb`.
- `docs/` — GitHub Pages site describing the benchmark tasks.
- `writeup/writeup.md` — full hackathon writeup.
- `tests/` — sanity tests for dataset generators.
- `requirements.txt` — Python dependencies for local generation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in MODEL_PROXY_API_KEY if running evals locally
```

## Generating a dataset

```bash
python datasets/<task>/generate.py
```

See `writeup/writeup.md` for task design, evaluation methodology, and results.
