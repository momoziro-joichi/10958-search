"""Independent root-partition oracle for short-right inversion."""
from fractions import Fraction
import unittest
from search import make_solver
from test_oracle import expression_trees, tokenizations
from test_search import evaluate


def values(digits, cap):
    return {v for tokens in tokenizations(digits)
            for v, _ in expression_trees(tokens, cap)}


class RightInverseTests(unittest.TestCase):
    def test_partition_oracle(self):
        queries = 0
        for digits in ('12012', '01212', '12300', '12323', '00012'):
            for cap in (0, 3, 100, 2000):
                expected = {Fraction(int(digits))}
                for a in values(digits[:3], cap):
                    for b in values(digits[3:], cap):
                        expected.update((a+b, a-b, a*b))
                        if b: expected.add(a/b)
                        if b.denominator == 1 and abs(b) <= cap and not (a == 0 and b <= 0):
                            expected.add(a ** int(b))
                targets = expected | {Fraction(n, 7) for n in range(-20, 21)}
                for right_digits in (0, 2):
                    dp, reverse = make_solver(digits, root_split=3, lookup_digits=0,
                        edge_inversion=False, right_inversion_digits=right_digits,
                        exponent_lookup_digits=99, max_abs_exponent=cap)
                    for target in targets:
                        expression = reverse(0, 5, target)
                        queries += 1
                        self.assertEqual(expression is not None, target in expected,
                            (digits, cap, right_digits, target))
                        if expression is not None:
                            self.assertEqual(evaluate(expression, cap), target)
                            self.assertEqual(''.join(c for c in expression if c.isdigit()), digits)
                    dp.cache_clear(); reverse.cache_clear()
        print('Short-right oracle queries:', queries)

    def test_high_cap_exponent_queries(self):
        for digits, split, target in (
            ('122000', 2, Fraction(1, 2 ** 2000)),
            ('1202000', 2, Fraction(2 ** 2000)),
            ('12000', 2, Fraction(1)),
            ('00000', 2, Fraction(1)),
        ):
            for threshold in (0, 99):
                dp, reverse = make_solver(digits, root_split=split, lookup_digits=0,
                    edge_inversion=False, right_inversion_digits=0,
                    exponent_lookup_digits=threshold, max_abs_exponent=2000)
                expression = reverse(0, len(digits), target)
                self.assertEqual(expression is not None, digits != '00000')
                if expression is not None:
                    self.assertEqual(evaluate(expression, 2000), target)
                    self.assertEqual(''.join(c for c in expression if c.isdigit()), digits)
                dp.cache_clear(); reverse.cache_clear()
