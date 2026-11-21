"""Bounded unresolved-tree sampling; never writes completion checkpoints."""
import argparse
from fractions import Fraction
import json
import resource
import signal
import time
from structural_resume import partition, identity
from strategy_probe import matches_target


def sample(digits, target, mask, limit=5):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    result = dict(visited=0, samples=[], status='enumerated')
    for tree in partition(digits, mask):
        result['visited'] += 1
        if matches_target(tree, Fraction(target)) is None:
            result['samples'].append(tree)
            if len(result['samples']) == limit:
                result['status'] = 'sample_limit'
                break
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--digits', default='123456789')
    p.add_argument('--target', default='10958')
    p.add_argument('--mask', type=int, required=True)
    p.add_argument('--seconds', type=int, default=10)
    args = p.parse_args()
    if not 1 <= args.seconds <= 60:
        p.error('seconds must be 1..60')
    ident = identity(args.digits, args.target)
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    def stop(*unused):
        raise TimeoutError
    signal.signal(signal.SIGALRM, stop)
    signal.alarm(args.seconds)
    start = time.perf_counter()
    try:
        result = sample(args.digits, args.target, args.mask)
    except (TimeoutError, MemoryError) as exc:
        result = dict(status=type(exc).__name__, samples=[])
    finally:
        signal.alarm(0)
    result.update(identity=ident, mask=args.mask, seconds=time.perf_counter()-start,
                  memory_mib=768, budget_seconds=args.seconds,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
