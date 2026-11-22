from fractions import Fraction as F
import unittest
from symbolic_residue import reject_pair, residue

class ResidueTests(unittest.TestCase):
    def test_exact_differential(self):
        bases=[F(-2),F(-1,2),F(1,3),F(2),F(3,2)]
        for a in bases:
            for b in bases:
                for ea in range(-3,4):
                    for eb in range(-3,4):
                        x,y=a**ea,b**eb
                        for op,v in [('+',x+y),('-',x-y),('*',x*y),('/',x/y)]:
                            self.assertIsNone(reject_pair(op,a,ea,b,eb,v))
                            for t in (F(0),F(10958),F(2,3)):
                                if reject_pair(op,a,ea,b,eb,t) is False:
                                    self.assertNotEqual(v,t)
    def test_nonunits_and_undefined(self):
        self.assertIsNone(residue(F(1,5),2,5))
        self.assertIsNone(residue(F(5),-2,5))
        with self.assertRaises(ValueError): residue(0,0,5)
    def test_observed_huge_pair(self):
        for op in '+-*/':
            self.assertIs(reject_pair(op,12,3**45,6,7**89,10958),False)
