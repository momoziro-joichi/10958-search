from fractions import Fraction
import unittest

from search import digit_power_exponents


class DigitPowerTests(unittest.TestCase):
    def test_exhaustive_against_direct_powers(self):
        for cap in (0, 1, 2, 7, 20):
            for base in range(10):
                expected = {}
                for exponent in range(-cap, cap + 1):
                    if base == 0 and exponent <= 0:
                        continue
                    value = Fraction(base) ** exponent
                    expected.setdefault(value, []).append(exponent)
                targets = set(expected) | {Fraction(n, d) for n in range(-10, 30)
                                           for d in range(1, 9)}
                for target in targets:
                    self.assertEqual(list(digit_power_exponents(base, target, cap)),
                                     expected.get(target, []), (base, target, cap))

    def test_large_exact_powers_and_adjacent_nonpowers(self):
        for base in range(2, 10):
            for exponent in (100, 1000, 2000):
                value = base ** exponent
                for target, answer in ((Fraction(value), exponent),
                                       (Fraction(1, value), -exponent)):
                    self.assertEqual(tuple(digit_power_exponents(base, target, exponent)),
                                     (answer,))
                    self.assertEqual(tuple(digit_power_exponents(base, target, exponent - 1)), ())
                for n in (value - 1, value + 1):
                    self.assertEqual(tuple(digit_power_exponents(base, Fraction(n), exponent)), ())
                    self.assertEqual(tuple(digit_power_exponents(base, Fraction(1, n), exponent)), ())


if __name__ == '__main__':
    unittest.main()
