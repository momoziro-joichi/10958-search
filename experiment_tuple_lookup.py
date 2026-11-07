"""Compare production tuple lookup with the previous Fraction-key lookup."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import resource
import signal
import time
import types
import search
from verify_expression import verify_expression


def baseline_factory():
    """Reproduce the previous Fraction-key path without changing disk files."""
    source = Path(search.__file__).read_text()
    old = 'return tuple_table(i, j).get((target.numerator, target.denominator))'
    assert source.count(old) == 1
    source = source.replace(old, 'return full_dp(i, j).get(target)')
    module = types.ModuleType('fraction_baseline')
    exec(compile(source, 'fraction_baseline', 'exec'), module.__dict__)
    return module.make_solver


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tuple',action='store_true')
    p.add_argument('--validate',action='store_true')
    a=p.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    def expired(*args): raise TimeoutError('60s budget')
    signal.signal(signal.SIGALRM,expired);signal.alarm(60)
    factory=search.make_solver if a.tuple else baseline_factory()
    started=time.perf_counter()
    if a.validate:
        from test_oracle import oracle
        queries=0
        for digits in [''.join(x) for x in itertools.product('0123',repeat=3)]+['1234']:
            expected,_=oracle(digits)
            dp,reverse=factory(digits)
            for target in expected | {Fraction(n,7) for n in range(-10,11)}:
                expr=reverse(0,len(digits),target)
                assert (expr is not None)==(target in expected)
                if expr is not None: verify_expression(expr,digits,target,100)
                queries+=1
        result=dict(status='validated',queries=queries)
    else:
        expr=factory('123456789',root_split=1,max_abs_exponent=5000)[1](0,9,Fraction(10958))
        if expr is not None: verify_expression(expr,'123456789',10958,5000,1)
        result=dict(status='found' if expr is not None else 'not_found_bounded')
    result.update(tuple_keys=a.tuple,seconds=time.perf_counter()-started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        memory_budget_mib=768,time_budget_seconds=60,
        source_sha256=hashlib.sha256(Path(search.__file__).read_bytes()).hexdigest())
    print(json.dumps(result))

if __name__=='__main__':main()
