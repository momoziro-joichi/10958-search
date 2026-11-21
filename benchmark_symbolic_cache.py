"""Isolated bounded evaluation-cache experiment; production unchanged."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import resource
import signal
import time
import strategy_probe as probe


def run(digits, size):
    original = probe.evaluate
    cached = lru_cache(maxsize=size)(original) if size else original
    counts = Counter()
    digest = hashlib.sha256()
    started = time.perf_counter()
    cpu_started = time.process_time()
    probe.evaluate = cached
    try:
        for tree in probe.all_trees(digits):
            result = probe.matches_target(tree, 10958)
            key = 'match' if result is True else 'reject' if result is False else 'unresolved'
            counts[key] += 1
            digest.update({'match': b'1', 'reject': b'0', 'unresolved': b'?'}[key])
        info = cached.cache_info()._asdict() if size else None
        return dict(digits=digits, cache_size=size, counts=counts,
                    ordered_result_sha256=digest.hexdigest(),
                    seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu_started, cache_info=info,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        probe.evaluate = original
        if size:
            cached.cache_clear()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--digits', default='123456')
    parser.add_argument('--cache-size', type=int, default=4096)
    args = parser.parse_args()
    if not args.digits or any(c not in '0123456789' for c in args.digits):
        parser.error('invalid digits')
    if not 0 <= args.cache_size <= 16384:
        parser.error('cache size must be in0..16384')
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    signal.alarm(60)
    print(json.dumps(run(args.digits,args.cache_size)))


if __name__ == '__main__':
    main()
