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

class CountTests(unittest.TestCase):
    def test_counts_and_sum(self):
        from structural_subpartition import expected_subtree_count
        from structural_checkpoint import expected_count
        for n in range(2,7):
            total=0
            for split in range(1,n):
                expected=expected_subtree_count(n,split)
                actual=sum(1 for _ in subtree_partition(tuple('123456'[:n]),split,'+'))
                self.assertEqual(actual,expected)
                total+=5*expected
            self.assertEqual(total,expected_count((1 << (n-1))-1))
    def test_invalid_counts(self):
        from structural_subpartition import expected_subtree_count
        for n,k in [(1,1),(3,0),(3,3),(True,1),(3,True),(3,1.0)]:
            with self.assertRaises(ValueError): expected_subtree_count(n,k)
