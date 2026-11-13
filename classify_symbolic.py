"""Budgeted target comparison of previously unresolved small-input trees."""
import argparse
import json
import resource
import signal
import time
from functools import lru_cache
import strategy_probe as probe
from collections import Counter
from fractions import Fraction
from strategy_probe import all_trees, evaluate, LazyPower, UNKNOWN, matches_target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--digits', default='12345')
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--cache-size', type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.cache_size <= 16384:
        parser.error('cache size must be in0..16384')
    if not 1 <= args.seconds <= 600:
        parser.error('seconds must be between 1 and 600')
    if not args.digits or any(c not in '0123456789' for c in args.digits):
        parser.error('digits must be a nonempty ASCII digit string')
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    def interrupted(signum, frame):
        raise TimeoutError
    signal.signal(signal.SIGALRM, interrupted)
    start = time.perf_counter()
    cpu_start = time.process_time()
    original = probe.evaluate
    cached = lru_cache(maxsize=args.cache_size)(original) if args.cache_size else original
    cache_info = None
    counts = Counter()
    found = []
    unknown = []
    status = 'complete'
    signal.alarm(args.seconds)
    try:
        probe.evaluate = cached
        for tree in all_trees(args.digits):
            value = cached(tree)
            if isinstance(value, LazyPower) or value is UNKNOWN:
                counts['deferred_power' if isinstance(value, LazyPower) else 'parent_'+tree[0]] += 1
            result = matches_target(tree, Fraction(10958))
            counts['match' if result is True else 'reject' if result is False else 'unresolved'] += 1
            if result is True:
                found.append(tree)
            if result is None:
                if len(unknown) < 100:
                    unknown.append(tree)
    except TimeoutError:
        status = 'timeout'
    except MemoryError:
        status = 'memory_limit'
    finally:
        signal.alarm(0)
        probe.evaluate = original
        if args.cache_size:
            cache_info = cached.cache_info()._asdict()
            cached.cache_clear()
    enumeration_complete = status == 'complete'
    if enumeration_complete and counts['unresolved']:
        status = 'unresolved'
    print(json.dumps(dict(digits=args.digits, target=10958, exponent_cap=None,
                         status=status, enumeration_complete=enumeration_complete, time_budget_seconds=args.seconds,
                         memory_budget_mib=768, cache_size=args.cache_size, cache_info=cache_info,
                         cpu_seconds=time.process_time()-cpu_start,
                         counts=counts, witnesses=found, unresolved_tree_samples=unknown,
                         seconds=time.perf_counter()-start,
                         peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))


if __name__ == '__main__':
    main()
