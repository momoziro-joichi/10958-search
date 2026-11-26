import unittest
from collections import Counter
from strategy_probe import trees
from structural_subpartition import subtree_partition

class SubpartitionTests(unittest.TestCase):
    def test_disjoint_coverage(self):
        for tokens in [('1','2'),('12','3','45'),tuple('12345')]:
            combined=Counter()
            for split in range(1,len(tokens)):
                for op in '+-*/^':
                    part=Counter(subtree_partition(tokens,split,op))
                    self.assertFalse(combined.keys() & part.keys())
                    combined.update(part)
            self.assertEqual(combined,Counter(trees(tokens)))
    def test_invalid(self):
        for split,op in [(0,'+'),(2,'+'),(1,'**')]:
            with self.assertRaises(ValueError):
                list(subtree_partition(('1','2'),split,op))
