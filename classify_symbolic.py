"""Budgeted target comparison of previously unresolved small-input trees."""
import argparse
import json
import resource
import signal
import time
from collections import Counter
from fractions import Fraction
from strategy_probe import all_trees, evaluate, LazyPower, UNKNOWN, matches_target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--digits', default='12345')
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600:
        parser.error('seconds must be between 1 and 600')
    if not args.digits or any(c not in '0123456789' for c in args.digits):
        parser.error('digits must be a nonempty ASCII digit string')
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    def interrupted(signum, frame):
        raise TimeoutError
    signal.signal(signal.SIGALRM, interrupted)
    start = time.perf_counter()
    counts = Counter()
    found = []
    unknown = []
    status = 'complete'
    signal.alarm(args.seconds)
    try:
        for tree in all_trees(args.digits):
            value = evaluate(tree)
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
    enumeration_complete = status == 'complete'
    if enumeration_complete and counts['unresolved']:
        status = 'unresolved'
    print(json.dumps(dict(digits=args.digits, target=10958, exponent_cap=None,
                         status=status, enumeration_complete=enumeration_complete, time_budget_seconds=args.seconds,
                         memory_budget_mib=768,
                         counts=counts, witnesses=found, unresolved_tree_samples=unknown,
                         seconds=time.perf_counter()-start,
                         peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))


if __name__ == '__main__':
    main()
