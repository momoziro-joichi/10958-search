"""Experimental POSIX per-tokenization resume; candidates require verification."""
import argparse
from collections import Counter
from fractions import Fraction
from functools import lru_cache
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import strategy_probe as probe
from structural_checkpoint import expected_count, load, save
from structural_identity import build_identity
from structural_lock import checkpoint_lock


def partition(digits, mask):
    if not 0 <= mask < 1 << (len(digits)-1):
        raise ValueError('invalid mask')
    tokens, start = [], 0
    for k in range(1, len(digits)):
        if mask & (1 << (k-1)):
            tokens.append(digits[start:k])
            start = k
    tokens.append(digits[start:])
    yield from probe.trees(tokens)


def identity(digits, target):
    names = ('symbolic_residue.py', 'structural_resume.py', 'strategy_probe.py', 'structural_checkpoint.py',
             'structural_identity.py', 'structural_lock.py')
    return build_identity(digits, target, {n: Path(__file__).with_name(n) for n in names})


def worker(digits, target, mask):
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    start = time.perf_counter()
    original = probe.evaluate
    probe.evaluate = lru_cache(maxsize=4096)(original)
    counts = Counter(rejected=0, unresolved=0)
    candidate = None
    try:
        for tree in partition(digits, mask):
            result = probe.matches_target(tree, Fraction(target))
            if result is True:
                candidate = tree
                break
            counts['rejected' if result is False else 'unresolved'] += 1
    finally:
        probe.evaluate.cache_clear()
        probe.evaluate = original
    return dict(counts=counts, candidate=candidate, seconds=time.perf_counter()-start,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def run(digits, target, checkpoint, seconds=60, per_mask=5):
    if not 0 < seconds <= 600 or not 0 < per_mask <= seconds:
        raise ValueError('require 0 < per-mask <= seconds <= 600')
    ident = identity(digits, target)
    start = time.monotonic()
    deadline = start + seconds
    attempts = []
    path = Path(checkpoint)
    with checkpoint_lock(path):
        data = load(path, ident) if path.exists() else dict(schema=1, identity=ident, completed={})
        skipped = len(data['completed'])
        for mask in range(1 << (len(digits)-1)):
            if str(mask) in data['completed']:
                continue
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                break
            row = dict(mask=mask, status='worker_error')
            try:
                proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                    '--digits', digits, '--target', ident['target'], '--worker-mask', str(mask)],
                    capture_output=True, text=True, timeout=min(per_mask, remaining))
                if proc.returncode == 0:
                    result = json.loads(proc.stdout)
                    row.update(result)
                    counts = result['counts']
                    if result['candidate'] is not None:
                        row['status'] = 'candidate_unverified'
                    elif (type(counts.get('rejected')) is int and
                          counts['rejected'] == expected_count(mask) and
                          type(counts.get('unresolved')) is int and counts['unresolved'] == 0):
                        row['status'] = 'complete_rejected'
                        data['completed'][str(mask)] = {'rejected': counts['rejected']}
                        save(path, data, ident)
                    else:
                        row['status'] = 'unresolved'
            except subprocess.TimeoutExpired:
                row['status'] = 'timeout'
            except (ValueError, KeyError, TypeError):
                row['status'] = 'worker_error'
            attempts.append(row)
            if row['status'] == 'candidate_unverified':
                break
        complete = len(data['completed']) == 1 << (len(digits)-1)
    return dict(identity=ident, status='complete_rejected' if complete else 'incomplete',
                completed_masks=len(data['completed']), skipped_masks=skipped,
                attempts=attempts, seconds=time.monotonic()-start,
                time_budget_seconds=seconds, per_mask_seconds=per_mask, memory_budget_mib=768)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--digits', default='123456789')
    parser.add_argument('--target', default='10958')
    parser.add_argument('--checkpoint', default='structural_checkpoint_10958.json')
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--per-mask-seconds', type=float, default=5)
    parser.add_argument('--worker-mask', type=int)
    args = parser.parse_args()
    identity(args.digits, args.target)
    if args.worker_mask is not None:
        output = worker(args.digits, args.target, args.worker_mask)
    else:
        output = run(args.digits, args.target, args.checkpoint, args.seconds, args.per_mask_seconds)
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
