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
