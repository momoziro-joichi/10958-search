import unittest
from fractions import Fraction
from strategy_probe import matches_target
from structural_resume import identity
from structural_checkpoint import load

class IntegrationTests(unittest.TestCase):
    def test_huge_pair(self):
        a=('^','12',('^','3','45'))
        b=('^','6',('^','7','89'))
        for op in '+-*/':
            self.assertIs(matches_target((op,a,b),10958),False)
        self.assertIsNone(matches_target(('^',a,b),10958))
    def test_equal_targets_not_rejected(self):
        a=('^','2','20');b=('^','3','20')
        x,y=Fraction(2)**20,Fraction(3)**20
        for op,t in [('+',x+y),('-',x-y),('*',x*y),('/',x/y)]:
            self.assertIsNot(matches_target((op,a,b),t,bits=8),False)
    def test_old_checkpoint_rejected(self):
        ident=identity('123456789','10958')
        self.assertIn('symbolic_residue.py',ident['sources_sha256'])
        with self.assertRaises(ValueError):
            load('structural_checkpoint_10958.json',ident)
