"""Verify disjoint token-boundary partitions before adding resume."""
import unittest
from collections import Counter
from math import comb
from strategy_probe import all_trees, trees


def partition(digits, mask):
    if not 0 <= mask < 1 << (len(digits)-1):
        raise ValueError('invalid mask')
    tokens=[]
    start=0
    for k in range(1,len(digits)):
        if mask & (1 << (k-1)):
            tokens.append(digits[start:k]);start=k
    tokens.append(digits[start:])
    yield from trees(tokens)


def expected_count(mask):
    k=mask.bit_count()
    return comb(2*k,k)//(k+1)*5**k


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
