"""Budgeted target comparison of previously unresolved small-input trees."""
import json
import resource
import signal
import time
from collections import Counter
from fractions import Fraction
from strategy_probe import all_trees, evaluate, LazyPower, UNKNOWN, matches_target


def main():
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    signal.alarm(60)
    start = time.perf_counter()
    counts = Counter()
    found = []
    unknown = []
    for tree in all_trees('12345'):
        value = evaluate(tree)
        if isinstance(value, LazyPower) or value is UNKNOWN:
            counts['deferred_power' if isinstance(value, LazyPower) else 'parent_'+tree[0]] += 1
        result = matches_target(tree, Fraction(10958))
        counts['match' if result is True else 'reject' if result is False else 'unresolved'] += 1
        if result is True:
            found.append(tree)
        if result is None:
            unknown.append(tree)
    print(json.dumps(dict(digits='12345', target=10958, exponent_cap=None,
                         counts=counts, witnesses=found, unresolved_trees=unknown,
                         seconds=time.perf_counter()-start,
                         peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))


if __name__ == '__main__':
    main()
