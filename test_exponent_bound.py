from fractions import Fraction
import unittest
from unittest.mock import patch
from search import make_solver, target_exponent_candidates
from test_search import evaluate

class ExponentBoundTests(unittest.TestCase):
    def test_all_generated_powers_retained(self):
        for n in range(-6, 7):
            for d in range(1, 7):
                a = Fraction(n, d)
                for e in range(-20, 21):
                    if a == 0 and e <= 0: continue
                    self.assertIn(e, target_exponent_candidates(a ** e, 20))
        for e in (100, 2000, 5000):
            for target in (Fraction(2**e), Fraction(1,2**e), Fraction(3**e,2**e)):
                self.assertIn(e, target_exponent_candidates(target, 5000))
                self.assertIn(-e, target_exponent_candidates(target, 5000))

    def test_bound_and_degenerate_cases(self):
        self.assertEqual(target_exponent_candidates(Fraction(10958),5000), range(-13,14))
        self.assertEqual(target_exponent_candidates(Fraction(8,81),5000), range(-3,4))
        for target in (0,1,-1):
            self.assertEqual(target_exponent_candidates(Fraction(target),5000),range(-5000,5001))
        self.assertEqual(target_exponent_candidates(Fraction(8),0),range(0,1))

    def test_against_unbounded_candidate_scan(self):
        for digits in ('12345','01212','00000'):
            answers = []
            for bounded in (False, True):
                strategy = target_exponent_candidates if bounded else lambda t,c: range(-c,c+1)
                with patch('search.target_exponent_candidates', strategy):
                    dp, reverse = make_solver(digits, root_split=2, lookup_digits=0,
                        exponent_lookup_digits=0, right_inversion_digits=0,
                        edge_inversion=False, max_abs_exponent=20)
                    found = []
                    for t in {Fraction(n,d) for n in range(-15,16) for d in (1,2,3)}:
                        expr = reverse(0,5,t)
                        found.append((t,expr is not None))
                        if expr is not None:
                            self.assertEqual(evaluate(expr,20),t)
                            self.assertEqual(''.join(c for c in expr if c.isdigit()),digits)
                    answers.append(found)
                    dp.cache_clear(); reverse.cache_clear()
            self.assertEqual(*answers)
