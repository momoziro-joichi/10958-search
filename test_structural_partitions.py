"""Verify disjoint token-boundary partitions before adding resume."""
import unittest
from collections import Counter
from math import comb
from strategy_probe import all_trees, trees


from structural_resume import partition
from structural_checkpoint import expected_count


class PartitionTests(unittest.TestCase):
    def test_disjoint_union_and_counts(self):
        for digits in ('0','12','123','1234','12345'):
            combined=Counter()
            for mask in range(1 << (len(digits)-1)):
                part=Counter(partition(digits,mask))
                self.assertEqual(sum(part.values()),expected_count(mask))
                self.assertFalse(combined.keys() & part.keys())
                combined.update(part)
            self.assertEqual(combined,Counter(all_trees(digits)))

    def test_invalid_mask(self):
        for mask in (-1,4):
            with self.assertRaises(ValueError):
                list(partition('123',mask))


if __name__=='__main__':
    unittest.main()
