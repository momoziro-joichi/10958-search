"""Experimental power-cache measurement; does not modify solver/checkpoints."""
import argparse
from functools import lru_cache
from fractions import Fraction
import json
import resource
import signal
import time
from search import make_solver

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--size', type=int, default=0)
a = p.parse_args()
if a.size < 0:
    p.error('size must be nonnegative')
resource.setrlimit(resource.RLIMIT_AS, (768*1024**2, 768*1024**2))
def expired(*args):
    raise TimeoutError('60-second measurement budget exhausted')
signal.signal(signal.SIGALRM, expired)
signal.alarm(60)
original = Fraction.__pow__
cached = lru_cache(maxsize=a.size)(original)
Fraction.__pow__ = cached
started = time.perf_counter()
try:
    result = make_solver('123456789', root_split=2, max_abs_exponent=2000)[1](0, 9, Fraction(10958))
    print(json.dumps(dict(cache_size=a.size, status='found' if result else 'not_found_bounded',
        expression=result, seconds=time.perf_counter()-started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        cache=cached.cache_info()._asdict())))
finally:
    Fraction.__pow__ = original
    signal.alarm(0)
