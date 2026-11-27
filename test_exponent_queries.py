"""Force both exponent strategies against independently enumerated trees."""
from fractions import Fraction
import itertools
import unittest
from search import make_solver
from test_oracle import expression_trees, tokenizations
from test_search import evaluate

class ExponentQueryTests(unittest.TestCase):
    def test_partition_oracle(self):
        for digits in [''.join(x) for x in itertools.product('012', repeat=3)] + ['1234', '2200', '2999']:
            for cap in (0, 3, 10):
                for split in range(1, len(digits)):
                    expected = {Fraction(int(digits))}
                    # Restrict syntax trees to this root partition, plus concat.
                    for lt in tokenizations(digits[:split]):
                        for rt in tokenizations(digits[split:]):
                            for a, ea in expression_trees(lt, cap):
                                for b, eb in expression_trees(rt, cap):
                                    expected.update((a+b, a-b, a*b))
                                    if b: expected.add(a/b)
                                    if b.denominator == 1 and abs(b) <= cap and not (a == 0 and b <= 0):
                                        expected.add(a ** int(b))
                    for threshold in (0, 99):
                        dp, reverse = make_solver(digits, root_split=split, lookup_digits=0,
                            edge_inversion=False, max_abs_exponent=cap,
                            exponent_lookup_digits=threshold)
                        for target in expected | {Fraction(n, 2) for n in range(-9, 10)}:
                            expr = reverse(0, len(digits), target)
                            self.assertEqual(expr is not None, target in expected,
                                             (digits, split, cap, threshold, target))
                            if expr is not None:
                                self.assertEqual(evaluate(expr, cap), target)
                                self.assertEqual(''.join(c for c in expr if c.isdigit()), digits)
                        dp.cache_clear(); reverse.cache_clear()
