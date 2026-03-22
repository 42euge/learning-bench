"""String rewriting task generator.

Tasks present character substitution rules via examples. The model must infer
the rule(s) from input→output pairs and apply them to a new input.

Difficulty tiers:
- easy:   1 substitution rule
- medium: 2 substitution rules applied in sequence
- hard:   3 substitution rules + a structural transform (reverse or shift)
"""

import random
import string
from dataclasses import dataclass


@dataclass
class StringRewritingRule:
    """A set of character substitution rules plus an optional structural transform."""
    substitutions: dict[str, str]  # char → char mappings
    transform: str | None  # None, "reverse", or "shift_N"


def _apply_rule(rule: StringRewritingRule, s: str) -> str:
    """Apply substitution rules then structural transform to a string."""
    # Apply substitutions left-to-right (all at once, not cascading)
    result = []
    for ch in s:
        result.append(rule.substitutions.get(ch, ch))
    out = "".join(result)

    # Apply structural transform
    if rule.transform is None:
        return out
    if rule.transform == "reverse":
        return out[::-1]
    if rule.transform.startswith("shift_"):
        n = int(rule.transform.split("_")[1])
        if not out:
            return out
        n = n % len(out)
        return out[n:] + out[:n]
    return out


class StringRewritingGenerator:
    """Generates string rewriting tasks with seed-based determinism."""

    @staticmethod
    def generate_rule(seed: int, difficulty: str) -> StringRewritingRule:
        """Generate a rewriting rule based on seed and difficulty."""
        rng = random.Random(seed)

        # Pick source and target characters for substitutions
        alphabet = list(string.ascii_lowercase)
        rng.shuffle(alphabet)

        if difficulty == "easy":
            n_subs = 1
            transform = None
        elif difficulty == "medium":
            n_subs = 2
            transform = None
        else:  # hard
            n_subs = 3
            transform = rng.choice(["reverse", f"shift_{rng.randint(1, 3)}"])

        # Build substitution map: pick n_subs source chars, each maps to a
        # different char. Ensure no overlap between sources and targets.
        sources = alphabet[:n_subs]
        # Targets come from remaining chars to avoid identity mappings
        remaining = [c for c in alphabet if c not in sources]
        targets = remaining[:n_subs]

        substitutions = dict(zip(sources, targets))
        return StringRewritingRule(substitutions=substitutions, transform=transform)

    @staticmethod
    def _make_input(rule: StringRewritingRule, rng: random.Random) -> str:
        """Generate an input string guaranteed to contain at least one source char."""
        length = rng.randint(4, 8)
        source_chars = list(rule.substitutions.keys())
        # Place at least one source char, fill rest randomly
        inp = list(rng.choices(string.ascii_lowercase, k=length))
        inject_pos = rng.randint(0, length - 1)
        inp[inject_pos] = rng.choice(source_chars)
        return "".join(inp)

    @staticmethod
    def generate_examples(rule: StringRewritingRule, n: int, seed: int) -> list[tuple[str, str]]:
        """Generate n (input, output) example pairs."""
        rng = random.Random(seed)
        examples = []
        for _ in range(n):
            inp = StringRewritingGenerator._make_input(rule, rng)
            out = _apply_rule(rule, inp)
            examples.append((inp, out))
        return examples

    @staticmethod
    def generate_query(rule: StringRewritingRule, seed: int) -> tuple[str, str]:
        """Generate a single (input, expected_output) query pair."""
        rng = random.Random(seed)
        inp = StringRewritingGenerator._make_input(rule, rng)
        expected = _apply_rule(rule, inp)
        return inp, expected

    @staticmethod
    def format_prompt(examples: list[tuple[str, str]], query_input: str) -> str:
        """Format examples and query into a prompt string."""
        lines = ["Here are some examples of a string transformation rule:\n"]
        for inp, out in examples:
            lines.append(f"Input: {inp}")
            lines.append(f"Output: {out}")
            lines.append("")
        lines.append("Now apply the same rule:")
        lines.append(f"Input: {query_input}")
        lines.append("Output:")
        return "\n".join(lines)

    def generate(self, seed: int, difficulty: str, n_examples: int = 4) -> dict:
        """Full generation pipeline: returns prompt, expected answer, and metadata."""
        rule = self.generate_rule(seed, difficulty)
        examples = self.generate_examples(rule, n_examples, seed=seed + 1000)
        query_input, expected = self.generate_query(rule, seed=seed + 2000)
        prompt = self.format_prompt(examples, query_input)
        return {
            "prompt": prompt,
            "expected": expected,
            "query_input": query_input,
            "rule": {
                "substitutions": rule.substitutions,
                "transform": rule.transform,
            },
            "difficulty": difficulty,
            "family": "string_rewriting",
            "seed": seed,
            "n_examples": n_examples,
        }


if __name__ == "__main__":
    gen = StringRewritingGenerator()
    for diff in ["easy", "medium", "hard"]:
        print(f"\n{'='*60}")
        print(f"DIFFICULTY: {diff}")
        print(f"{'='*60}")
        for s in range(5):
            result = gen.generate(seed=s, difficulty=diff)
            print(f"\nSeed {s} | Rule: {result['rule']}")
            print(result["prompt"])
            print(f"  [Expected: {result['expected']}]")
