"""Artificial grammar task generator.

Tasks present strings labeled as valid or invalid according to a procedurally
generated context-free grammar. The model must infer the grammar from examples
and classify new strings.

Difficulty tiers:
- easy:   Simple grammar with 2-3 productions, no recursion
- medium: Grammar with recursion, deeper nesting possible
- hard:   Multiple productions with recursion and distractor patterns
"""

import random
from dataclasses import dataclass


@dataclass
class Grammar:
    """A context-free grammar defined by production rules."""
    productions: dict[str, list[list[str]]]  # nonterminal → list of alternatives (each a list of symbols)
    start: str
    terminals: set[str]
    nonterminals: set[str]
    max_depth: int  # limit for recursive derivations


def _derive(grammar: Grammar, symbol: str, rng: random.Random, depth: int = 0) -> str | None:
    """Derive a string from a grammar symbol. Returns None if depth exceeded."""
    if depth > grammar.max_depth:
        return None

    if symbol in grammar.terminals:
        return symbol

    if symbol not in grammar.productions:
        return None

    alternatives = grammar.productions[symbol]
    # Shuffle to get variety, but try all alternatives if needed
    order = list(range(len(alternatives)))
    rng.shuffle(order)

    for idx in order:
        alt = alternatives[idx]
        parts = []
        failed = False
        for s in alt:
            result = _derive(grammar, s, rng, depth + 1)
            if result is None:
                failed = True
                break
            parts.append(result)
        if not failed:
            return "".join(parts)

    return None


def _is_valid(grammar: Grammar, s: str) -> bool:
    """Check if string s is in the language of the grammar (CYK-style check via brute enumeration)."""
    # For our small grammars, we generate all valid strings up to the length
    # and check membership. This is tractable because max_depth is small.
    return s in _enumerate_valid(grammar, max_len=len(s) + 2)


def _enumerate_valid(grammar: Grammar, max_len: int = 15) -> set[str]:
    """Enumerate all valid strings up to max_len by exhaustive derivation."""
    valid = set()

    def _expand(symbol: str, depth: int) -> list[str]:
        if depth > grammar.max_depth:
            return []
        if symbol in grammar.terminals:
            return [symbol]
        if symbol not in grammar.productions:
            return []

        results = []
        for alt in grammar.productions[symbol]:
            # Expand each symbol in the alternative
            partial = [""]
            for s in alt:
                expanded = _expand(s, depth + 1)
                if not expanded:
                    partial = []
                    break
                new_partial = []
                for prefix in partial:
                    for suffix in expanded:
                        candidate = prefix + suffix
                        if len(candidate) <= max_len:
                            new_partial.append(candidate)
                partial = new_partial
            results.extend(partial)
        return results

    valid.update(_expand(grammar.start, 0))
    return valid


def _generate_invalid(grammar: Grammar, rng: random.Random, valid_strings: set[str]) -> str:
    """Generate a string that is NOT in the grammar's language but looks plausible."""
    terminals = sorted(grammar.terminals)
    if not valid_strings:
        # Fallback: random string of terminals
        length = rng.randint(2, 6)
        return "".join(rng.choices(terminals, k=length))

    # Strategy: take a valid string and mutate it
    base = rng.choice(sorted(valid_strings))
    strategies = ["swap", "insert", "delete", "replace"]
    rng.shuffle(strategies)

    for strategy in strategies:
        if strategy == "swap" and len(base) >= 2:
            i = rng.randint(0, len(base) - 2)
            candidate = base[:i] + base[i + 1] + base[i] + base[i + 2:]
        elif strategy == "insert":
            i = rng.randint(0, len(base))
            ch = rng.choice(terminals)
            candidate = base[:i] + ch + base[i:]
        elif strategy == "delete" and len(base) >= 2:
            i = rng.randint(0, len(base) - 1)
            candidate = base[:i] + base[i + 1:]
        elif strategy == "replace" and len(base) >= 1:
            i = rng.randint(0, len(base) - 1)
            ch = rng.choice(terminals)
            candidate = base[:i] + ch + base[i + 1:]
        else:
            continue

        if candidate not in valid_strings and candidate:
            return candidate

    # Last resort: random string
    length = rng.randint(2, 6)
    for _ in range(20):
        candidate = "".join(rng.choices(terminals, k=length))
        if candidate not in valid_strings:
            return candidate
    return "".join(rng.choices(terminals, k=length + 3))


class ArtificialGrammarGenerator:
    """Generates artificial grammar classification tasks."""

    @staticmethod
    def generate_rule(seed: int, difficulty: str) -> Grammar:
        rng = random.Random(seed)

        # Pick terminal symbols (lowercase letters, avoiding confusing ones)
        terminal_pool = list("abcdefghkmnpqrstuvwxyz")
        rng.shuffle(terminal_pool)

        if difficulty == "easy":
            # Simple grammar: S → t1 X t2, X → t3
            # e.g., S → a X b, X → c  → valid strings: "acb"
            # Add one more production for variety: X → t3 t4
            t = terminal_pool[:4]
            productions = {
                "S": [[t[0], "X", t[1]]],
                "X": [[t[2]], [t[3]]],
            }
            terminals = set(t[:4])
            nonterminals = {"S", "X"}
            max_depth = 4

        elif difficulty == "medium":
            # Recursive grammar: S → t1 X t2, X → t3 X t4 | t5
            t = terminal_pool[:5]
            productions = {
                "S": [[t[0], "X", t[1]]],
                "X": [[t[2], "X", t[3]], [t[4]]],
            }
            terminals = set(t[:5])
            nonterminals = {"S", "X"}
            max_depth = 5

        else:  # hard
            # More complex: S → t1 X t2 | t3 Y t4, X → t5 X t6 | t7, Y → t8 Y t5 | t9
            t = terminal_pool[:10]
            productions = {
                "S": [[t[0], "X", t[1]], [t[2], "Y", t[3]]],
                "X": [[t[4], "X", t[5]], [t[6]]],
                "Y": [[t[7], "Y", t[4]], [t[8]]],
            }
            terminals = set(t[:10])
            nonterminals = {"S", "X", "Y"}
            max_depth = 6

        return Grammar(
            productions=productions,
            start="S",
            terminals=terminals,
            nonterminals=nonterminals,
            max_depth=max_depth,
        )

    @staticmethod
    def generate_examples(rule: Grammar, n: int, seed: int) -> list[tuple[str, str]]:
        """Generate n labeled examples (string, 'valid'|'invalid')."""
        rng = random.Random(seed)
        valid_strings = _enumerate_valid(rule)

        examples = []
        # Aim for roughly balanced valid/invalid
        n_valid = (n + 1) // 2
        n_invalid = n - n_valid

        # Generate valid examples
        valid_list = sorted(valid_strings)
        if valid_list:
            chosen_valid = [valid_list[rng.randint(0, len(valid_list) - 1)] for _ in range(n_valid)]
        else:
            chosen_valid = []

        for s in chosen_valid:
            examples.append((s, "valid"))

        # Generate invalid examples
        for _ in range(n_invalid):
            inv = _generate_invalid(rule, rng, valid_strings)
            examples.append((inv, "invalid"))

        rng.shuffle(examples)
        return examples

    @staticmethod
    def generate_query(rule: Grammar, seed: int) -> tuple[str, str]:
        """Generate a query string and its classification."""
        rng = random.Random(seed)
        valid_strings = _enumerate_valid(rule)

        # Randomly decide if query is valid or invalid
        if rng.random() < 0.5 and valid_strings:
            valid_list = sorted(valid_strings)
            s = valid_list[rng.randint(0, len(valid_list) - 1)]
            return s, "valid"
        else:
            s = _generate_invalid(rule, rng, valid_strings)
            return s, "invalid"

    @staticmethod
    def format_prompt(examples: list[tuple[str, str]], query_string: str) -> str:
        lines = [
            "The following strings are classified as either \"valid\" or \"invalid\"",
            "according to a hidden rule. Study the examples and classify the final string.\n",
        ]
        for s, label in examples:
            lines.append(f'"{s}" → {label}')
        lines.append("")
        lines.append(f'"{query_string}" →')
        return "\n".join(lines)

    def generate(self, seed: int, difficulty: str, n_examples: int = 4) -> dict:
        rule = self.generate_rule(seed, difficulty)
        examples = self.generate_examples(rule, n_examples, seed=seed + 1000)
        query_string, expected = self.generate_query(rule, seed=seed + 2000)
        prompt = self.format_prompt(examples, query_string)

        # Serialize grammar for metadata
        grammar_meta = {}
        for nt, alts in rule.productions.items():
            grammar_meta[nt] = [" ".join(symbols) for symbols in alts]

        return {
            "prompt": prompt,
            "expected": expected,
            "query_string": query_string,
            "rule": {
                "productions": grammar_meta,
                "max_depth": rule.max_depth,
            },
            "difficulty": difficulty,
            "family": "artificial_grammar",
            "seed": seed,
            "n_examples": n_examples,
        }


if __name__ == "__main__":
    gen = ArtificialGrammarGenerator()
    for diff in ["easy", "medium", "hard"]:
        print(f"\n{'='*60}")
        print(f"DIFFICULTY: {diff}")
        print(f"{'='*60}")
        for s in range(5):
            result = gen.generate(seed=s, difficulty=diff)
            print(f"\nSeed {s} | Grammar: {result['rule']['productions']}")
            print(result["prompt"])
            print(f"  [Expected: {result['expected']}]")
