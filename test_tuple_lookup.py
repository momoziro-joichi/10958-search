import unittest
from fractions import Fraction
from search import make_solver
from verify_expression import verify_expression


class TupleLookupTests(unittest.TestCase):
    def test_normalization_cleanup_and_rebuild(self):
        dp, reverse = make_solver("1234")
        target = Fraction(2, 6)
        expr = reverse(0, 4, target)
        self.assertIsNotNone(expr)
        verify_expression(expr, "1234", target, 100)
        self.assertEqual(reverse.lookup_cache_info().currsize, 1)
        self.assertEqual(expr, reverse(0, 4, Fraction(1, 3)))
        reverse.cache_clear()
        dp.cache_clear()
        self.assertEqual(reverse.lookup_cache_info().currsize, 0)
        self.assertEqual(reverse.cache_info().currsize, 0)
        self.assertEqual(dp.cache_info().currsize, 0)
        self.assertEqual(expr, reverse(0, 4, target))

    def test_integer_target(self):
        _, reverse = make_solver("23")
        verify_expression(reverse(0, 2, 8), "23", 8, 100)
