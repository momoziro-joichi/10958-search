"""Necessary congruence checks for two defined nonzero rational powers.

False proves inequality; None does not decide equality. Never returns True.
No primality assumption: denominators must be units modulo each modulus.
"""
from fractions import Fraction
from math import gcd


def residue(base, exponent, modulus):
    base = Fraction(base)
    if type(exponent) is not int or type(modulus) is not int or modulus < 2:
        raise ValueError('integer exponent and modulus >=2 required')
    if base == 0 and exponent <= 0:
        raise ValueError('undefined power')
    n, d = base.numerator, base.denominator
    if exponent < 0:
        n, d, exponent = d, n, -exponent
    if gcd(d, modulus) != 1:
        return None
    return pow(n * pow(d, -1, modulus) % modulus, exponent, modulus)


def reject_pair(op, a, ea, b, eb, target, moduli=(5, 7, 11, 13, 17, 19)):
    if op not in ('+', '-', '*', '/'):
        return None
    if op == '/' and Fraction(b) == 0:
        return None  # caller must handle undefined arithmetic
    target = Fraction(target)
    for m in moduli:
        x, y, t = residue(a, ea, m), residue(b, eb, m), residue(target, 1, m)
        if x is None or y is None or t is None:
            continue
        # Cross multiplication avoids requiring y to be a modular unit.
        delta = {'+': lambda: x+y-t, '-': lambda: x-y-t,
                 '*': lambda: x*y-t, '/': lambda: x-t*y}[op]()
        if delta % m:
            return False
    return None
