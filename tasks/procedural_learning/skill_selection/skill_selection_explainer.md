# Skill Selection — Similarity Modes Explained

## What the task tests

Given a registry of tools (each with a name, description, and capabilities list), the model must pick the correct tool for a user request. The **similarity** axis controls how hard it is to tell tools apart.

## The three modes

### Distinct

Each tool's **name, description, and capabilities all point to the same thing**. There's no ambiguity.

**Example:**
> **flux_bridge**
> *Description:* Routes incoming signals to designated endpoints based on protocol headers and priority flags.
> *Capabilities:* route packets to endpoints, apply priority-based ordering, configure failover paths

A request like *"Direct incoming API calls to the correct backend service"* clearly maps to this tool. The name suggests bridging/routing, the description says routing, the capabilities say routing. Easy.

**Result:** All models score 100%. This is the baseline anchor — if a model can't do this, something is fundamentally broken.

### Confusable

Tool descriptions use **generic, overlapping vocabulary** that makes multiple tools *seem* relevant. The capabilities still differ, but you have to read them carefully.

**Example — two tools that sound similar:**
> **flux_bridge** (domain: signal_routing)
> *Description:* Processes incoming data flows and manages their distribution across system components.
>
> **prism_forge** (domain: format_conversion)
> *Description:* Processes incoming data structures and transforms them into target-compatible formats.

Both "process incoming data" — but one routes and the other converts formats. The model must look past the surface similarity to the actual capabilities list to choose correctly.

**Result:** All three tested models still score 100%. Frontier models handle this level of ambiguity fine.

### Adversarial

Tool descriptions **deliberately suggest a different domain** than what the tool actually does. The name and description are misleading — only the capabilities list reveals the truth.

**Example:**
> **flux_bridge** (actual domain: signal_routing)
> *Description:* Synthesizes composite data templates from fragmented input sources.

The description says "synthesizes templates" (sounds like pattern_synthesis), but the capabilities still say routing. The model must ignore the misleading description and trust the capabilities.

Meanwhile, the *actual* pattern_synthesis tool might be described as "validates structural compliance" — making it sound like schema_validation.

This creates a shell game where every tool's description points to a *different* tool's actual function.

**Result:** This is where models diverge:
- **gemma-3-4b: 44%** — mostly fooled by misleading descriptions
- **gemini-2.5-flash: 89%** — usually catches it, occasional mistakes
- **gemini-2.5-pro: 100%** — reads capabilities carefully every time

## Why this matters

This directly mirrors real-world tool-use failures. When an LLM has 30+ tools loaded with overlapping or misleading descriptions (like Claude choosing "upload to Colab" instead of "run on Kaggle"), it needs to look past surface-level name/description matching and reason about actual capabilities.

The adversarial condition isolates this specific skill — and shows it scales with model capability.

## Results summary

| Model | Distinct | Confusable | Adversarial |
|---|---|---|---|
| gemma-3-4b | 100% | 100% | **44%** |
| gemini-2.5-flash | 100% | 100% | **89%** |
| gemini-2.5-pro | 100% | 100% | **100%** |
