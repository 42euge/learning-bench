"""Procedural task generators for the Learning Curve Profiler benchmark."""

from src.generators.string_rewriting import StringRewritingGenerator
from src.generators.modular_arithmetic import ModularArithmeticGenerator
from src.generators.artificial_grammar import ArtificialGrammarGenerator

SHOT_COUNTS = [1, 2, 4, 8, 16, 32, 64]
DIFFICULTIES = ["easy", "medium", "hard"]
TASK_FAMILIES = ["string_rewriting", "modular_arithmetic", "artificial_grammar"]

GENERATORS = {
    "string_rewriting": StringRewritingGenerator,
    "modular_arithmetic": ModularArithmeticGenerator,
    "artificial_grammar": ArtificialGrammarGenerator,
}

__all__ = [
    "StringRewritingGenerator",
    "ModularArithmeticGenerator",
    "ArtificialGrammarGenerator",
    "SHOT_COUNTS",
    "DIFFICULTIES",
    "TASK_FAMILIES",
    "GENERATORS",
]
