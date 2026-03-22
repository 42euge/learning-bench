"""Modular arithmetic task generator.

Tasks define novel operator symbols with modular arithmetic semantics. The model
must infer operator definitions from examples and evaluate new expressions.

Difficulty tiers:
- easy:   1 novel operator, single binary expression
- medium: 2 novel operators, expression uses both
- hard:   3 novel operators with precedence rules or nesting
"""

import random
from dataclasses import dataclass


# Unicode symbols that look like plausible math operators
OPERATOR_SYMBOLS = ["⊕", "⊗", "⊖", "⊘", "⊞", "⊠", "⊡", "⊛", "⊜", "⊝"]

# Underlying operations for operators
OPERATIONS = [
    ("add", lambda a, b, m: (a + b) % m),
    ("mul", lambda a, b, m: (a * b) % m),
    ("add_scaled", lambda a, b, m: (2 * a + b) % m),
    ("diff_abs", lambda a, b, m: abs(a - b) % m),
    ("sum_sq", lambda a, b, m: (a * a + b) % m),
    ("add_plus1", lambda a, b, m: (a + b + 1) % m),
]

# Human-readable descriptions of operations
OPERATION_DESCRIPTIONS = {
    "add": "({a} + {b}) mod {m}",
    "mul": "({a} × {b}) mod {m}",
    "add_scaled": "(2×{a} + {b}) mod {m}",
    "diff_abs": "|{a} - {b}| mod {m}",
    "sum_sq": "({a}² + {b}) mod {m}",
    "add_plus1": "({a} + {b} + 1) mod {m}",
}


@dataclass
class Operator:
    symbol: str
    op_name: str
    op_fn: callable
    modulus: int


@dataclass
class ArithmeticRule:
    operators: list[Operator]
    precedence: list[str] | None  # symbol order for hard mode, None otherwise


def _eval_expression(rule: ArithmeticRule, tokens: list[str | int]) -> int:
    """Evaluate a list of tokens [val, op, val, op, val, ...] respecting precedence."""
    # Convert to mutable list of values and operators
    values = [t for i, t in enumerate(tokens) if i % 2 == 0]
    ops = [t for i, t in enumerate(tokens) if i % 2 == 1]

    if rule.precedence:
        # Apply operators in precedence order (higher precedence first)
        for sym in rule.precedence:
            i = 0
            while i < len(ops):
                if ops[i] == sym:
                    op = next(o for o in rule.operators if o.symbol == sym)
                    result = op.op_fn(values[i], values[i + 1], op.modulus)
                    values[i] = result
                    values.pop(i + 1)
                    ops.pop(i)
                else:
                    i += 1
    else:
        # Left-to-right evaluation
        while ops:
            sym = ops.pop(0)
            op = next(o for o in rule.operators if o.symbol == sym)
            a = values.pop(0)
            b = values.pop(0)
            result = op.op_fn(a, b, op.modulus)
            values.insert(0, result)

    return values[0]


class ModularArithmeticGenerator:
    """Generates modular arithmetic tasks with seed-based determinism."""

    @staticmethod
    def generate_rule(seed: int, difficulty: str) -> ArithmeticRule:
        rng = random.Random(seed)

        if difficulty == "easy":
            n_ops = 1
        elif difficulty == "medium":
            n_ops = 2
        else:
            n_ops = 3

        # Pick operator symbols
        symbols = rng.sample(OPERATOR_SYMBOLS, n_ops)

        # Pick underlying operations (no repeats)
        ops_pool = list(OPERATIONS)
        rng.shuffle(ops_pool)
        chosen_ops = ops_pool[:n_ops]

        # Pick moduli (small primes for clean arithmetic)
        moduli_choices = [5, 7, 11, 13]

        operators = []
        for i in range(n_ops):
            mod = rng.choice(moduli_choices)
            op_name, op_fn = chosen_ops[i]
            operators.append(Operator(
                symbol=symbols[i],
                op_name=op_name,
                op_fn=op_fn,
                modulus=mod,
            ))

        # Hard mode gets explicit precedence
        precedence = None
        if difficulty == "hard":
            prec_symbols = [o.symbol for o in operators]
            rng.shuffle(prec_symbols)
            precedence = prec_symbols

        return ArithmeticRule(operators=operators, precedence=precedence)

    @staticmethod
    def _make_expression(rule: ArithmeticRule, rng: random.Random) -> tuple[list, str, int]:
        """Generate a random expression as tokens, string, and result."""
        n_ops = len(rule.operators)
        # Number of operators in expression matches difficulty
        n_expr_ops = n_ops

        # Generate operand values (0 to max_modulus - 1)
        max_mod = max(o.modulus for o in rule.operators)
        values = [rng.randint(0, max_mod - 1) for _ in range(n_expr_ops + 1)]

        # Pick which operators to use (one of each for coverage)
        if n_expr_ops == 1:
            expr_ops = [rule.operators[0].symbol]
        else:
            expr_ops = [o.symbol for o in rule.operators]
            rng.shuffle(expr_ops)
            expr_ops = expr_ops[:n_expr_ops]

        # Build token list
        tokens = []
        for i, v in enumerate(values):
            tokens.append(v)
            if i < len(expr_ops):
                tokens.append(expr_ops[i])

        # Build string representation
        parts = []
        for t in tokens:
            parts.append(str(t))
        expr_str = " ".join(parts)

        result = _eval_expression(rule, list(tokens))
        return tokens, expr_str, result

    @staticmethod
    def generate_examples(rule: ArithmeticRule, n: int, seed: int) -> list[tuple[str, int]]:
        rng = random.Random(seed)
        examples = []
        for _ in range(n):
            _, expr_str, result = ModularArithmeticGenerator._make_expression(rule, rng)
            examples.append((expr_str, result))
        return examples

    @staticmethod
    def generate_query(rule: ArithmeticRule, seed: int) -> tuple[str, int]:
        rng = random.Random(seed)
        _, expr_str, result = ModularArithmeticGenerator._make_expression(rule, rng)
        return expr_str, result

    @staticmethod
    def format_prompt(rule: ArithmeticRule, examples: list[tuple[str, int]], query_expr: str) -> str:
        # Build operator definition hints (just the symbols, not the rules — model must infer)
        op_list = ", ".join(o.symbol for o in rule.operators)
        lines = [
            f"The following expressions use novel operator(s): {op_list}",
            "Each operator performs a specific arithmetic operation.",
            "Study the examples to figure out what each operator does, then evaluate the final expression.\n",
        ]
        for expr, result in examples:
            lines.append(f"{expr} = {result}")
        lines.append("")

        if rule.precedence:
            prec_str = " > ".join(rule.precedence)
            lines.append(f"Operator precedence (highest first): {prec_str}")
            lines.append("")

        lines.append(f"{query_expr} =")
        return "\n".join(lines)

    def generate(self, seed: int, difficulty: str, n_examples: int = 4) -> dict:
        rule = self.generate_rule(seed, difficulty)
        examples = self.generate_examples(rule, n_examples, seed=seed + 1000)
        query_expr, expected = self.generate_query(rule, seed=seed + 2000)
        prompt = self.format_prompt(rule, examples, query_expr)

        # Serialize operator info for metadata
        op_meta = []
        for o in rule.operators:
            op_meta.append({
                "symbol": o.symbol,
                "operation": o.op_name,
                "modulus": o.modulus,
            })

        return {
            "prompt": prompt,
            "expected": str(expected),
            "query_expression": query_expr,
            "rule": {
                "operators": op_meta,
                "precedence": rule.precedence,
            },
            "difficulty": difficulty,
            "family": "modular_arithmetic",
            "seed": seed,
            "n_examples": n_examples,
        }


if __name__ == "__main__":
    gen = ModularArithmeticGenerator()
    for diff in ["easy", "medium", "hard"]:
        print(f"\n{'='*60}")
        print(f"DIFFICULTY: {diff}")
        print(f"{'='*60}")
        for s in range(5):
            result = gen.generate(seed=s, difficulty=diff)
            print(f"\nSeed {s} | Operators: {result['rule']['operators']}")
            if result['rule']['precedence']:
                print(f"  Precedence: {result['rule']['precedence']}")
            print(result["prompt"])
            print(f"  [Expected: {result['expected']}]")
