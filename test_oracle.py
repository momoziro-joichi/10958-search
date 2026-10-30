"""Independent small-space oracle: tokenize first, then enumerate syntax trees.

No production DP, root inversion, memoization, or value deduplication is used
while constructing expressions. Deduplication happens only at the final set.
"""
from fractions import Fraction
import itertools
import unittest

from search import MAX_ABS_EXPONENT, make_solver
from test_search import evaluate


def tokenizations(digits):
    for mask in range(1 << (len(digits) - 1)):
        tokens = []
        start = 0
        for boundary in range(1, len(digits)):
            if mask & (1 << (boundary - 1)):
                tokens.append(digits[start:boundary])
                start = boundary
        tokens.append(digits[start:])
        yield tokens


def expression_trees(tokens, exponent_limit=100):
    if len(tokens) == 1:
        yield Fraction(int(tokens[0])), tokens[0]
        return
    for boundary in range(1, len(tokens)):
        for left, left_text in expression_trees(tokens[:boundary], exponent_limit):
            for right, right_text in expression_trees(tokens[boundary:], exponent_limit):
                yield left + right, f"({left_text}+{right_text})"
                yield left - right, f"({left_text}-{right_text})"
                yield left * right, f"({left_text}*{right_text})"
                if right:
                    yield left / right, f"({left_text}/{right_text})"
                if right.denominator != 1 or abs(right) > exponent_limit:
                    continue
                if left == 0 and right <= 0:
                    continue
                yield left ** int(right), f"({left_text}^{right_text})"


def oracle(digits):
    values = set()
    expressions = 0
    for tokens in tokenizations(digits):
        for value, _ in expression_trees(tokens):
            values.add(value)
            expressions += 1
    return values, expressions


class IndependentOracleTests(unittest.TestCase):
    def test_oracle_examples_and_exponent_boundary(self):
        self.assertEqual(oracle("23")[0],
                         {Fraction(23), Fraction(5), Fraction(-1), Fraction(6),
                          Fraction(2, 3), Fraction(8)})
        self.assertEqual(oracle("00")[0], {Fraction(0)})
        self.assertEqual(oracle("20")[0], {Fraction(20), Fraction(2),
                                              Fraction(0), Fraction(1)})
        for exponent in (100, 101):
            values = {v for v, _ in expression_trees(["2", str(exponent)])}
            self.assertEqual(Fraction(2 ** exponent) in values, exponent == 100)
            values = {v for v, _ in expression_trees(["2", "0", str(exponent)])}
            self.assertEqual(Fraction(1, 2 ** exponent) in values, exponent == 100)

    def test_all_four_digit_strings(self):
        # Keep the independent oracle's rule explicit rather than importing
        # production pruning logic. Fail loudly if the default domain changes.
        self.assertEqual(MAX_ABS_EXPONENT, 100)
        total_expressions = total_values = total_queries = 0
        for chars in itertools.product("0123", repeat=4):
            digits = "".join(chars)
            expected, count = oracle(digits)
            total_expressions += count
            total_values += len(expected)
            forward, reverse = make_solver(digits, lookup_digits=0)
            self.assertEqual(set(forward(0, 4)), expected, digits)
            targets = expected | {Fraction(n, 2) for n in range(-12, 13)}
            for target in targets:
                total_queries += 1
                expression = reverse(0, 4, target)
                self.assertEqual(expression is not None, target in expected,
                                 (digits, target))
                if expression is not None:
                    self.assertEqual(evaluate(expression), target)
                    self.assertEqual("".join(c for c in expression if c.isdigit()), digits)
            forward.cache_clear()
            reverse.cache_clear()
        print(f"Oracle: 256 inputs, {total_expressions} syntax trees, "
              f"{total_values} per-input distinct values, {total_queries} queries")


if __name__ == "__main__":
    unittest.main()
