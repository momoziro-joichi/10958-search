"""Measure exact-power costs by result bit length; isolated 60s/768MiB run."""
from collections import defaultdict
from fractions import Fraction
import json
import resource
import signal
import time
from search import make_solver

resource.setrlimit(resource.RLIMIT_AS, (768*1024**2, 768*1024**2))
def expired(*args):
    raise TimeoutError('measurement budget exhausted')
signal.signal(signal.SIGALRM, expired)
signal.alarm(60)
original = Fraction.__pow__
buckets = defaultdict(lambda: dict(calls=0, seconds=0.0, max_bits=0))
def measured(base, exponent):
    started = time.perf_counter()
    result = original(base, exponent)
    elapsed = time.perf_counter() - started
    bits = result.numerator.bit_length() + result.denominator.bit_length()
    ceiling = 1 << (max(1, bits)-1).bit_length()
    row = buckets[ceiling]
    row['calls'] += 1
    row['seconds'] += elapsed
    row['max_bits'] = max(row['max_bits'], bits)
    return result
Fraction.__pow__ = measured
started = time.perf_counter()
try:
    expression = make_solver('123456789', root_split=2, max_abs_exponent=2000)[1](0, 9, Fraction(10958))
    print(json.dumps(dict(status='found' if expression else 'not_found_bounded',
        expression=expression, seconds=time.perf_counter()-started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        buckets=dict(sorted(buckets.items()))), indent=2))
finally:
    Fraction.__pow__ = original
    signal.alarm(0)
