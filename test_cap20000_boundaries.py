"""Known witnesses at the production cap; no nine-digit search rerun."""
from fractions import Fraction
import unittest

from search import make_solver
from verify_expression import verify_expression


class Cap20000Boundaries(unittest.TestCase):
    def test_positive_and_negative_outer_power_boundary(self):
        for digits, known, target in (
            ('220000', '(2^20000)', Fraction(2**20000)),
            ('2020000', '(2^(0-20000))', Fraction(1, 2**20000)),
        ):
            verify_expression(known, digits, target, 20000, 1)
            for cap in (19999, 20000):
                with self.subTest(digits=digits, cap=cap):
                    dp, reverse = make_solver(digits, root_split=1,
                        lookup_digits=0, max_abs_exponent=cap)
                    try:
                        expression = reverse(0, len(digits), target)
                        self.assertEqual(expression is not None, cap == 20000)
                        if expression is not None:
                            verify_expression(expression, digits, target, cap, 1)
                    finally:
                        dp.cache_clear()
                        reverse.cache_clear()

    def test_verifier_checks_internal_power_caps_before_cancellation(self):
        for power in ('(2^20000)', '(2^(0-20000))'):
            expression = f'({power}-{power})'
            digits = ''.join(c for c in expression if c.isdigit())
            self.assertEqual(verify_expression(expression, digits, 0, 20000), 0)
            with self.assertRaises(ValueError):
                verify_expression(expression, digits, 0, 19999)


if __name__ == '__main__':
    unittest.main()
