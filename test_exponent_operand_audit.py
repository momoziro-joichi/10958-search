import unittest
from fractions import Fraction
from audit_exponent_operands import audit
from test_oracle import tokenizations, expression_trees


class OperandAuditTests(unittest.TestCase):
    def test_independent_enumeration(self):
        result = audit()
        self.assertEqual(len(result['rows']), 26)
        for row in result['rows']:
            sets = []
            for cap in (10000, 20000):
                values = {v for tokens in tokenizations(row['digits'])
                          for v, expr in expression_trees(tokens, cap)}
                sets.append(values)
            low, high = sets
            self.assertEqual(row['lower_value_count'], len(low))
            self.assertEqual(row['upper_value_count'], len(high))
            self.assertEqual(row['newly_reachable_values'], len(high-low))
            self.assertEqual({x['value'] for x in row['newly_allowed_exponents']},
                             {int(v) for v in high if v.denominator == 1
                              and 10000 < abs(v) <= 20000})
            for item in row['newly_allowed_exponents']:
                self.assertEqual(item['reachable_under_lower_cap'],
                                 Fraction(item['value']) in low)
        row = next(x for x in result['rows'] if x['digits'] == '56')
        self.assertEqual(row['newly_allowed_exponents'][0]['value'], 15625)
