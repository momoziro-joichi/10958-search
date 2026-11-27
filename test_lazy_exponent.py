import unittest
from fractions import Fraction as F
from strategy_probe import matches_target

class LazyExponentTests(unittest.TestCase):
    def test_exact_small_powers(self):
        # Force lazy representation with a tiny allocation guard.
        for a in (2,3):
            for b in (2,3):
                for e in range(2,5):
                    tree=('^',str(a),('^',str(b),str(e)))
                    value=F(a)**(b**e)
                    self.assertIsNot(matches_target(tree,value,bits=1),False)
                    self.assertIs(matches_target(tree,10958,bits=1),False)
    def test_noninteger_exponent(self):
        tree=('^','2',('^',('/','1','2'),'20'))
        self.assertIs(matches_target(tree,10958,bits=1),False)
    def test_special_target_not_overrejected(self):
        tree=('^','1',('^','2','20'))
        self.assertIs(matches_target(tree,1,bits=1),True)
