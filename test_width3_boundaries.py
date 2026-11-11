import unittest
from fractions import Fraction
from search import make_solver
from verify_expression import verify_expression

class Width3Boundaries(unittest.TestCase):
    def test_power_witnesses(self):
        cases=[('1200999',Fraction(12**999)),('1200012',Fraction(1,12**12)),
               ('1200122',Fraction(1)),('0000123',Fraction(0)),
               ('1200000',Fraction(1)),('1200998',Fraction(1,12**89))]
        # Compare the existing left-table path with three-digit inversion.
        for digits,target in cases:
            results=[]
            for width in (0,3):
                dp,reverse=make_solver(digits,root_split=4,max_abs_exponent=20000,right_inversion_digits=width)
                expr=reverse(0,7,target);results.append(expr is not None)
                if expr: verify_expression(expr,digits,target,20000,4)
                dp.cache_clear();reverse.cache_clear()
            self.assertEqual(results[0],results[1])
