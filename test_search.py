import ast
import itertools
import unittest
from fractions import Fraction

from search import (
    MAX_ABS_EXPONENT, integer_nth_root_exact,
    make_solver, rational_nth_root_exact,
)


def evaluate(expression):
    """Evaluate witnesses exactly, without eval or floating-point division."""
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return Fraction(node.value)
        if not isinstance(node, ast.BinOp):
            raise AssertionError(f"Unexpected expression: {expression}")
        a, b = visit(node.left), visit(node.right)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
        if isinstance(node.op, ast.Pow):
            assert b.denominator == 1
            assert abs(b) <= MAX_ABS_EXPONENT
            assert not (a == 0 and b <= 0)
            return a ** b.numerator
        raise AssertionError(expression)

    # Concatenations may contain leading zeroes; normalize numeric tokens.
    import re
    normalized = re.sub(r"[0-9]+", lambda m: str(int(m[0])), expression)
    return visit(ast.parse(normalized.replace("^", "**"), mode="eval").body)


class SearchTests(unittest.TestCase):
    def assert_witness(self, digits, target, expression):
        self.assertIsNotNone(expression, (digits, target))
        self.assertEqual("".join(c for c in expression if c.isdigit()), digits)
        self.assertEqual(evaluate(expression), target)

    def test_minimal_power(self):
        forward, reverse = make_solver("23", lookup_digits=0, edge_inversion=False)
        self.assertEqual(forward(0, 2)[Fraction(8)], "(2^3)")
        self.assertEqual(reverse(0, 2, Fraction(8)), "(2^3)")
        self.assertIsNone(reverse(0, 2, Fraction(7)))

    def test_leaf_queries_do_not_fill_cache(self):
        _, reverse = make_solver("23", lookup_digits=0, edge_inversion=False)
        for target in range(10000):
            self.assertEqual(reverse(0, 1, Fraction(target)),
                             "2" if target == 2 else None)
        self.assertEqual(reverse.cache_info().currsize, 0)
        self.assertEqual(reverse.cache_info().maxsize, 50000)

    def test_regressions(self):
        cases = [
            ("1234", Fraction(234256)),  # (1-23)^4
            ("1234", Fraction(625, 16)),  # ((1/2)-3)^4
            ("233", Fraction(1)),  # 2^(3-3)
            ("213", Fraction(1, 4)),  # 2^(1-3)
            ("123", Fraction(-1)),
            ("0012", Fraction(0)),
        ]
        for digits, target in cases:
            with self.subTest(digits=digits, target=target):
                forward, reverse = make_solver(digits, lookup_digits=0, edge_inversion=False)
                self.assert_witness(digits, target, forward(0, len(digits))[target])
                self.assert_witness(digits, target, reverse(0, len(digits), target))

    def test_exact_roots(self):
        for value, exponent, expected in [
            (Fraction(625, 16), 4, Fraction(5, 2)),
            (Fraction(-8, 27), 3, Fraction(-2, 3)),
            (Fraction(-4), 2, None), (Fraction(2), 2, None),
            (Fraction(0), 3, Fraction(0)),
            (Fraction(1), 0, None),
        ]:
            self.assertEqual(rational_nth_root_exact(value, exponent), expected)
        for exponent in range(1, 9):
            for root in range(21):
                self.assertEqual(integer_nth_root_exact(root ** exponent, exponent), root)
        self.assertEqual(integer_nth_root_exact(2 ** 10000, 100), 2 ** 100)
        self.assertIsNone(integer_nth_root_exact(2 ** 10000 + 1, 100))

    def test_small_spaces_and_witnesses(self):
        # Exhaust all three-digit strings over 0..3, including zero boundaries.
        cases = ["".join(p) for p in itertools.product("0123", repeat=3)]
        cases += ["1234", "12345"]
        for digits in cases:
            forward, reverse = make_solver(digits, lookup_digits=0, edge_inversion=False)
            values = forward(0, len(digits))
            for target, expression in values.items():
                self.assert_witness(digits, target, expression)
                self.assert_witness(digits, target, reverse(0, len(digits), target))
            for numerator in range(-10, 11):
                target = Fraction(numerator, 2)
                expression = reverse(0, len(digits), target)
                self.assertEqual(expression is not None, target in values)
                if expression is not None:
                    self.assert_witness(digits, target, expression)
            forward.cache_clear()
            reverse.cache_clear()


if __name__ == "__main__":
    unittest.main()
