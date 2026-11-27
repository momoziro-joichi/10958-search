"""Disjoint root-split/operator subdivision of a fixed token list.

Enumeration only; persistence integration is intentionally separate.
"""
from strategy_probe import trees


def subtree_partition(tokens, split, op):
    if not 1 <= split < len(tokens) or op not in ('+', '-', '*', '/', '^'):
        raise ValueError('invalid root partition')
    for left in trees(tokens[:split]):
        for right in trees(tokens[split:]):
            yield op, left, right


def expected_subtree_count(token_count, split):
    """Count for ONE fixed root operator; all five operators have this size."""
    from math import comb
    if type(token_count) is not int or type(split) is not int or not 1 <= split < token_count:
        raise ValueError('invalid token count or split')
    def count(n):
        k = n-1
        return comb(2*k,k)//(k+1)*5**k
    return count(split)*count(token_count-split)
