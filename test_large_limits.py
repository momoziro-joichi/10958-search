"""Independent high-cap checks; no nine-digit checkpoint is recomputed."""
from fractions import Fraction
import unittest

from search import make_solver
from test_oracle import expression_trees, tokenizations
from test_search import evaluate


class LargeExponentTests(unittest.TestCase):
    def assert_witness(self, digits, target, expression, cap):
        self.assertIsNotNone(expression)
        self.assertEqual(''.join(c for c in expression if c.isdigit()), digits)
        self.assertEqual(evaluate(expression, cap), target)

    def test_independent_large_cap_spaces(self):
        trees = queries = 0
        for cap in (200, 1000, 2000, 5000):
            for digits in ('2200', '2999', '1234', '0000'):
                expected = set()
                for tokens in tokenizations(digits):
                    for value, expression in expression_trees(tokens, cap):
                        self.assert_witness(digits, value, expression, cap)
                        expected.add(value)
                        trees += 1
                targets = expected | {Fraction(n, 2) for n in range(-5, 6)}
                for edges in (False, True):
                    forward, reverse = make_solver(
                        digits, lookup_digits=0, edge_inversion=edges,
                        max_abs_exponent=cap)
                    self.assertEqual(set(forward(0, len(digits))), expected)
                    for target in targets:
                        expression = reverse(0, len(digits), target)
                        queries += 1
                        self.assertEqual(expression is not None, target in expected,
                                         (digits, cap, edges, target))
                        if expression is not None:
                            self.assert_witness(digits, target, expression, cap)
                    forward.cache_clear()
                    reverse.cache_clear()
        print(f'High-cap oracle: {trees} syntax trees, {queries} reverse queries')

    def test_large_power_boundaries_and_rational_roots(self):
        for exponent in (200, 1000, 2000, 5000):
            # Restrict the outer split so other arithmetic cannot disguise an
            # excluded power. Expected values are computed independently.
            for digits, split, target in (
                ('2' + str(exponent), 1, Fraction(2 ** exponent)),
                ('20' + str(exponent), 1, Fraction(1, 2 ** exponent)),
                ('12' + str(exponent), 2, Fraction(1, 2 ** exponent)),
            ):
                for edges in (False, True):
                    for cap in (exponent - 1, exponent):
                        forward, reverse = make_solver(
                            digits, root_split=split, lookup_digits=0,
                            edge_inversion=edges, max_abs_exponent=cap)
                        expression = reverse(0, len(digits), target)
                        self.assertEqual(expression is not None, cap == exponent,
                                         (digits, cap, edges))
                        if expression is not None:
                            self.assert_witness(digits, target, expression, cap)
                        forward.cache_clear()
                        reverse.cache_clear()

    def test_evaluator_enforces_selected_cap_at_every_node(self):
        for exponent in (200, 1000, 2000, 5000):
            expression = f'((2^{exponent})-(2^{exponent}))'
            self.assertEqual(evaluate(expression, exponent), 0)
            with self.assertRaises(AssertionError):
                evaluate(expression, exponent - 1)
        for expression in ('(0^0)', '(0^(1-2))', '(2^(1/2))'):
            with self.assertRaises(AssertionError):
                evaluate(expression, 1000)


if __name__ == '__main__':
    unittest.main()
