"""Budgeted, reproducible cProfile report; never reads or writes checkpoints."""
import argparse
import cProfile
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import pstats
import subprocess
import sys
import time


def worker(args):
    import resource
    limit = args.memory_mib * 1024**2
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    from search import make_solver
    from verify_expression import verify_expression
    forward, reverse = make_solver(args.digits, root_split=args.split,
                                   max_abs_exponent=args.max_abs_exponent)
    profiler = cProfile.Profile()
    started = time.perf_counter()
    try:
        profiler.enable()
        expression = reverse(0, len(args.digits), Fraction(args.target))
    finally:
        profiler.disable()
    search_seconds = time.perf_counter() - started
    if expression is not None:
        verify_expression(expression, args.digits, args.target,
                          args.max_abs_exponent, args.split)
    stats = pstats.Stats(profiler)
    functions = []
    for (file, line, name), (primitive, total, own, cumulative, callers) in stats.stats.items():
        functions.append(dict(file=Path(file).name, line=line, name=name,
                              primitive_calls=primitive, total_calls=total,
                              own_seconds=own, cumulative_seconds=cumulative))
    functions.sort(key=lambda row: row['own_seconds'], reverse=True)
    print(json.dumps(dict(status='found' if expression is not None else 'not_found_bounded',
                          expression=expression, search_seconds=search_seconds,
                          total_calls=stats.total_calls, primitive_calls=stats.prim_calls,
                          functions=functions, forward_cache=forward.cache_info()._asdict(),
                          reverse_cache=reverse.cache_info()._asdict(),
                          max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--digits', default='123456789')
    parser.add_argument('--target', default='10958')
    parser.add_argument('--split', type=int, default=2)
    parser.add_argument('--max-abs-exponent', type=int, default=2000)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--memory-mib', type=int, default=768)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not sys.platform.startswith('linux'):
        parser.error('Linux required for the virtual-memory limit')
    if not args.digits or any(c not in '0123456789' for c in args.digits):
        parser.error('digits must be nonempty ASCII digits')
    if not 1 <= args.split < len(args.digits) or args.max_abs_exponent < 0:
        parser.error('Invalid split or exponent cap')
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.memory_mib < 64:
        parser.error('Positive finite seconds and memory-mib >= 64 required')
    try:
        args.target = str(Fraction(args.target))
    except (ValueError, ZeroDivisionError):
        parser.error('Invalid rational target')
    if args.worker:
        worker(args)
        return
    command = [sys.executable, str(Path(__file__).resolve()), '--worker',
               '--digits', args.digits, '--target', args.target, '--split', str(args.split),
               '--max-abs-exponent', str(args.max_abs_exponent),
               '--seconds', str(args.seconds), '--memory-mib', str(args.memory_mib)]
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=args.seconds)
        if completed.returncode:
            result = dict(status='worker_error', returncode=completed.returncode,
                          error=completed.stderr[-2000:])
        else:
            result = json.loads(completed.stdout)
    except subprocess.TimeoutExpired:
        result = dict(status='timeout')
    result.update(digits=args.digits, target=args.target, root_split=args.split,
                  max_abs_exponent=args.max_abs_exponent, time_budget_seconds=args.seconds,
                  memory_budget_mib=args.memory_mib, elapsed_seconds=time.perf_counter()-started,
                  python=platform.python_version(), platform=platform.platform(),
                  profile_includes_overhead=True)
    root = Path(__file__).resolve().parent
    result['source_sha256'] = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                               for name in ('search.py', 'verify_expression.py', 'profile_search.py')}
    print(json.dumps(result, indent=2, sort_keys=True))
    if result['status'] not in ('found', 'not_found_bounded'):
        sys.exit(2)


if __name__ == '__main__':
    main()
