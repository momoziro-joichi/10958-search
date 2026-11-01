"""Check the experimental cache against exact powers and memory admission."""
from fractions import Fraction
import unittest
from measure_root_cache import root_wrapper
from search import rational_nth_root_exact


class RootCacheTests(unittest.TestCase):
    def test_exact_powers_and_failures(self):
        root = root_wrapper(rational_nth_root_exact, 32)
        for numerator in range(-4, 5):
            for denominator in range(1, 5):
                base = Fraction(numerator, denominator)
                for exponent in range(1, 9):
                    value = base ** exponent
                    expected = abs(base) if exponent % 2 == 0 else base
                    self.assertEqual(root(value, exponent), expected)
                    self.assertEqual(root(value, exponent), expected)
        for value, exponent in ((Fraction(2),2),(Fraction(-1),2),(Fraction(2,3),3)):
            self.assertIsNone(root(value, exponent))
            self.assertIsNone(root(value, exponent))
        self.assertLessEqual(root.cache_info().currsize, 32)
        self.assertGreater(root.cache_info().hits, 0)

    def test_large_inputs_bypass_cache(self):
        root = root_wrapper(rational_nth_root_exact, 2)
        for value in (Fraction(1 << 300), Fraction(1, 1 << 300)):
            self.assertEqual(root(value, 2), rational_nth_root_exact(value, 2))
        self.assertEqual(root.cache_info().currsize, 0)
        for n in range(10): root(Fraction(n), 2)
        self.assertEqual(root.cache_info().currsize, 2)
