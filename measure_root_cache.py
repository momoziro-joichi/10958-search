"""Isolated bounded root-cache experiment; production/checkpoints unchanged."""
import argparse
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import resource
import signal
import time
import search
from verify_expression import verify_expression


def root_wrapper(original, size):
    # An entry bound alone does not bound bytes: bypass large rational inputs.
    cached = lru_cache(maxsize=size)(original)
    def root(value, exponent):
        if value.numerator.bit_length() + value.denominator.bit_length() > 256:
            return original(value, exponent)
        return cached(value, exponent)
    root.cache_info = cached.cache_info
    return root


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--size', type=int, choices=(0, 1024, 16384), default=0)
    p.add_argument('--split', type=int, choices=(1, 8), default=1)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    def expired(*args):
        raise TimeoutError('30-second budget exhausted')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(30)
    original = search.rational_nth_root_exact
    wrapper = root_wrapper(original, a.size)
    # Baseline calls the original directly (no wrapper overhead).
    if a.size:
        search.rational_nth_root_exact = wrapper
    started = time.perf_counter()
    result = dict(cache_size=a.size, root_split=a.split, max_abs_exponent=5000,
                  digits='123456789', target='10958', time_budget_seconds=30,
                  memory_budget_mib=768, input_bit_limit=256,
                  solver_sha256=hashlib.sha256(Path(search.__file__).read_bytes()).hexdigest())
    try:
        expr = search.make_solver('123456789', root_split=a.split,
                                  max_abs_exponent=5000)[1](0, 9, Fraction(10958))
        if expr is not None:
            verify_expression(expr, '123456789', Fraction(10958), 5000, a.split)
        result.update(status='found' if expr is not None else 'not_found_bounded', expression=expr)
    except TimeoutError:
        result.update(status='timeout', expression=None)
    except MemoryError:
        result.update(status='memory_limit', expression=None)
    finally:
        search.rational_nth_root_exact = original
        signal.alarm(0)
    result.update(seconds=time.perf_counter()-started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  cache=wrapper.cache_info()._asdict() if a.size else None)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
