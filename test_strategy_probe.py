from fractions import Fraction as F
from itertools import product
import unittest
from strategy_probe import (rational_power_candidates, operate, LazyPower,
                            UNKNOWN, INVALID, enumerate_values)
from search import make_solver


class StrategyTests(unittest.TestCase):
    def test_cap_free_candidates(self):
        self.assertEqual(rational_power_candidates(10958), (-1, 1))
        self.assertEqual(rational_power_candidates(F(64,729)), (-6,-3,-2,-1,1,2,3,6))
        self.assertEqual(rational_power_candidates(-64), (-3,-1,1,3))
        for t in (0,1,-1):
            self.assertIsNone(rational_power_candidates(t))
        for n in range(-5,6):
            for d in range(1,6):
                a = F(n,d)
                for e in range(-8,9):
                    if a == 0 and e <= 0:
                        continue
                    t = a ** e
                    if t not in (0,1,-1):
                        self.assertIn(e, rational_power_candidates(t))

    def test_lazy_definedness_and_cancellation(self):
        p = operate('^', F(2), F(10**9), bits=64)
        self.assertIsInstance(p, LazyPower)
        self.assertEqual(operate('-',p,p), 0)
        self.assertEqual(operate('/',p,p), 1)
        self.assertIs(operate('+',p,F(1)), UNKNOWN)
        self.assertIs(operate('^',F(0),F(0)), INVALID)
        self.assertIs(operate('^',F(0),F(-1)), INVALID)
        self.assertIs(operate('^',F(2),F(1,2)), INVALID)
        self.assertIs(operate('-',INVALID,INVALID), INVALID)
        self.assertIsInstance(operate('^', F(-2,3), F(-1000), bits=64), LazyPower)

    def test_independent_structure_against_production(self):
        for digits in [''.join(c) for c in product('0123', repeat=3)] + ['1234']:
            values, stats = enumerate_values(digits, bits=100000, cap=100)
            self.assertEqual(stats['unresolved'],0)
            forward, reverse = make_solver(digits, lookup_digits=0)
            self.assertEqual(values,set(forward(0,len(digits))),digits)
            for v in values | {F(10958), F(17,19)}:
                self.assertEqual(reverse(0,len(digits),v) is not None,v in values)
            forward.cache_clear()
            reverse.cache_clear()

    def test_unknown_is_not_absence(self):
        _, stats = enumerate_values('234',bits=8)
        self.assertGreater(stats['unresolved'],0)


class SymbolicTargetTests(unittest.TestCase):
    def test_lazy_equality(self):
        from strategy_probe import lazy_equals
        for n in range(-4,5):
            for d in range(1,5):
                a=F(n,d)
                for e in range(-5,6):
                    if a == 0 and e <= 0:
                        continue
                    p=LazyPower(a,e)
                    self.assertTrue(lazy_equals(p,a**e))
                    self.assertFalse(lazy_equals(p,a**e+F(1,7)))

    def test_low_budget_against_direct_fraction(self):
        from strategy_probe import all_trees, evaluate, matches_target
        for digits in ('1234','1203','2301','0000'):
            for tree in all_trees(digits):
                value=evaluate(tree,bits=100000,cap=100)
                if not isinstance(value,F):
                    continue
                for target in (value, value+F(1,7)):
                    result=matches_target(tree,target,bits=8,cap=100)
                    if result is not None:
                        self.assertEqual(result,value==target,(tree,target))

    def test_all_95_resolved_for_target(self):
        from strategy_probe import all_trees, matches_target
        for tree in all_trees('12345'):
            self.assertIs(matches_target(tree,F(10958)),False,tree)

    def test_symbolic_exponent_integrality(self):
        from strategy_probe import matches_target
        self.assertTrue(matches_target(('^','1',('^','2','9999')),1))
        self.assertFalse(matches_target(('^','1',('^',('/','1','2'),'9999')),1))
        # With a finite cap the exponent must also be checked: remain unknown.
        self.assertIsNone(matches_target(('^','1',('^','2','9999')),1,cap=20000))


class NestedPowerTargetTests(unittest.TestCase):
    def test_zero_with_defined_large_power(self):
        from strategy_probe import matches_target
        for op in ('*', '/'):
            tree=(op,'0',('^','4',('^','5','6')))
            self.assertTrue(matches_target(tree,0))
            self.assertFalse(matches_target(tree,10958))

    def test_nested_unexpanded_powers(self):
        from strategy_probe import matches_target
        self.assertFalse(matches_target(('^','12',('^','3',('^','4','56'))),10958))
        tree=('^',('^','2','5'),'2')
        self.assertTrue(matches_target(tree,1024,bits=2))
        self.assertFalse(matches_target(tree,1025,bits=2))
        negative=('^',('-', '1','3'),'2')
        self.assertTrue(matches_target(negative,4,bits=1))
        reciprocal=('^',('^','2','5'),('-', '1','3'))
        self.assertTrue(matches_target(reciprocal,F(1,1024),bits=2))
        self.assertFalse(matches_target(tree,1024,bits=2,cap=1))


if __name__ == '__main__':
    unittest.main()
