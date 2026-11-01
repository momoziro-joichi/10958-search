"""Bounded paired benchmark; does not read/write search checkpoints."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import resource
import signal
import time
import search
from verify_expression import verify_expression


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split',type=int,choices=(1,8),required=True)
    p.add_argument('--unbounded-candidates',action='store_true')
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    def expired(*args): raise TimeoutError('20-second deadline')
    signal.signal(signal.SIGALRM,expired);signal.alarm(20)
    original=search.target_exponent_candidates
    if a.unbounded_candidates:
        search.target_exponent_candidates=lambda target,limit: range(-limit,limit+1)
    result=dict(split=a.split,bounded_candidates=not a.unbounded_candidates,
                max_abs_exponent=5000,digits='123456789',target='10958',
                time_budget_seconds=20,memory_budget_mib=768,
                solver_sha256=hashlib.sha256(Path(search.__file__).read_bytes()).hexdigest())
    original_root=search.rational_nth_root_exact
    root_calls=0
    def counted_root(*args):
        nonlocal root_calls
        root_calls += 1
        return original_root(*args)
    search.rational_nth_root_exact=counted_root
    cpu_started=time.process_time()
    started=time.perf_counter()
    try:
        expr=search.make_solver('123456789',root_split=a.split,max_abs_exponent=5000)[1](0,9,Fraction(10958))
        if expr is not None: verify_expression(expr,'123456789',Fraction(10958),5000,a.split)
        result.update(status='found' if expr is not None else 'not_found_bounded',expression=expr)
    except TimeoutError: result.update(status='timeout',expression=None)
    except MemoryError: result.update(status='memory_limit',expression=None)
    finally:
        search.rational_nth_root_exact=original_root
        search.target_exponent_candidates=original
        signal.alarm(0)
    result.update(cpu_seconds=time.process_time()-cpu_started, root_calls=root_calls, seconds=time.perf_counter()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print(json.dumps(result))

if __name__=='__main__': main()
