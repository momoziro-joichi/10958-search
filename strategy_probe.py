"""Isolated experiments; no production solver/checkpoint changes.

No exponent cap is needed for rational_power_candidates. None means a
special target with infinitely many possible exponents, NOT no candidates.
Structural enumeration is finite; unresolved evaluation prevents an absence
claim. LazyPower stores only already-defined rational-base integer powers.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
import json
import resource
import time


def exact_root(n, e):
    lo, hi = 0, 1 << ((n.bit_length() + e - 1) // e)
    while lo <= hi:
        m = (lo + hi) // 2
        v = m ** e
        if v == n:
            return m
        if v < n:
            lo = m + 1
        else:
            hi = m - 1
    return None


def rational_power_candidates(t):
    """All integer e for which some rational a satisfies a**e=t.

    For t != 0,+/-1, each nonunit reduced component c must be an
    |e|-th power, implying |e| <= floor(log2(c)). Negative t requires
    odd e. Reciprocal bases give both signs. No factorization is required.
    """
    t = F(t)
    if t in (0, 1, -1):
        return None
    components = [c for c in (abs(t.numerator), t.denominator) if c > 1]
    bound = min(c.bit_length() - 1 for c in components)
    positive = [e for e in range(1, bound + 1)
                if (t > 0 or e % 2) and
                all(exact_root(c, e) is not None for c in components)]
    return tuple(sorted([-e for e in positive] + positive))


@dataclass(frozen=True)
class LazyPower:
    base: F
    exponent: int


UNKNOWN = object()
INVALID = object()


def operate(op, a, b, bits=4096, cap=None):
    if a is INVALID or b is INVALID:
        return INVALID
    if a is UNKNOWN or b is UNKNOWN:
        return UNKNOWN
    # Equal, defined nonzero symbolic powers can cancel exactly. Do not
    # simplify arbitrary unevaluated expressions: they might be undefined.
    if isinstance(a, LazyPower) or isinstance(b, LazyPower):
        if a == b and op in ('-', '/'):
            return F(0 if op == '-' else 1)
        return UNKNOWN
    if op == '^':
        if b.denominator != 1 or (a == 0 and b <= 0):
            return INVALID
        e = int(b)
        if cap is not None and abs(e) > cap:
            return INVALID
        if a in (0, 1, -1) or e == 0:
            return a ** e
        # Conservative allocation guard, not mathematical pruning.
        if abs(e) * max(abs(a.numerator).bit_length(), a.denominator.bit_length()) > bits:
            return LazyPower(a, e)
        return a ** e
    if op == '/' and b == 0:
        return INVALID
    return {'+': lambda: a+b, '-': lambda: a-b,
            '*': lambda: a*b, '/': lambda: a/b}[op]()


def trees(tokens):
    if len(tokens) == 1:
        yield tokens[0]
        return
    for k in range(1, len(tokens)):
        for a in trees(tokens[:k]):
            for b in trees(tokens[k:]):
                for op in '+-*/^':
                    yield (op, a, b)


def all_trees(digits):
    for mask in range(1 << (len(digits)-1)):
        tokens, start = [], 0
        for k in range(1, len(digits)):
            if mask & (1 << (k-1)):
                tokens.append(digits[start:k])
                start = k
        tokens.append(digits[start:])
        yield from trees(tokens)


def evaluate(tree, bits=4096, cap=None):
    if isinstance(tree, str):
        return F(int(tree))
    op, left, right = tree
    return operate(op, evaluate(left, bits, cap), evaluate(right, bits, cap), bits, cap)


def enumerate_values(digits, bits=4096, cap=None):
    values, unresolved, invalid, count = set(), 0, 0, 0
    for tree in all_trees(digits):
        count += 1
        v = evaluate(tree, bits, cap)
        if v is INVALID:
            invalid += 1
        elif not isinstance(v, F):
            unresolved += 1
        else:
            values.add(v)
    return values, dict(syntax_trees=count, unresolved=unresolved, invalid=invalid,
                       distinct_evaluated_values=len(values))


def main():
    import signal
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    signal.alarm(60)
    started = time.perf_counter()
    rows = {}
    for digits in ('123', '1234', '12345'):
        t = time.perf_counter()
        values, stats = enumerate_values(digits)
        stats.update(seconds=time.perf_counter()-t,
                     target_10958_found=F(10958) in values,
                     status='incomplete' if stats['unresolved'] else 'complete')
        rows[digits] = stats
    print(json.dumps(dict(exponent_candidates_10958=rational_power_candidates(10958),
                         exponent_cap=None, power_allocation_bits=4096,
                         rows=rows, seconds=time.perf_counter()-started,
                         peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), indent=2))


if __name__ == '__main__':
    main()
