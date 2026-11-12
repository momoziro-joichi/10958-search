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


    def test_known_exact_witnesses(self):
        cases = [
            ('1202200', '(((1-2)*(0+2))^200)', Fraction(2**200)),
            ('1202201', '(((1-2)*(0+2))^201)', Fraction(-(2**201))),
            ('1200200', '(((1/2)+(0*0))^200)', Fraction(1,2**200)),
            ('1200012', '((12+(0*0))^(0-12))', Fraction(1,12**12)),
            ('1200000', '((12+(0*0))^((0+0)+0))', Fraction(1)),
            ('0000123', '(((0+0)+(0+0))^123)', Fraction(0)),
        ]
        for digits, known, target in cases:
            verify_expression(known, digits, target, 20000, 4)
            _, reverse = make_solver(digits, root_split=4,
                max_abs_exponent=20000, right_inversion_digits=3)
            expr = reverse(0, 7, target)
            self.assertIsNotNone(expr, digits)
            verify_expression(expr, digits, target, 20000, 4)

    def test_all_zero_cannot_make_one(self):
        _, reverse = make_solver('0000000', root_split=4,
            max_abs_exponent=20000, right_inversion_digits=3)
        self.assertIsNone(reverse(0, 7, Fraction(1)))
