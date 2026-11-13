"""Bounded comparison; production default and checkpoints stay unchanged."""
import json
import resource
import signal
import time
from fractions import Fraction
from search import make_solver
from test_right_inverse import values
from verify_expression import verify_expression


def run():
    queries = 0
    for digits in ('0001000', '1000001', '1200001', '1201231', '1021012'):
        cap = 3
        expected = {Fraction(int(digits))}
        for a in values(digits[:4],cap):
            for b in values(digits[4:],cap):
                expected.update((a+b,a-b,a*b))
                if b: expected.add(a/b)
                if b.denominator == 1 and abs(b)<=cap and not(a==0 and b<=0):
                    expected.add(a**int(b))
        dp, reverse = make_solver(digits,root_split=4,max_abs_exponent=cap,right_inversion_digits=3)
        for target in expected | {Fraction(n,7) for n in range(-10,11)}:
            expr=reverse(0,7,target)
            assert (expr is not None)==(target in expected)
            if expr: verify_expression(expr,digits,target,cap,4)
            queries+=1
        dp.cache_clear();reverse.cache_clear()
    rows=[]
    for width in (2,3):
        t=time.perf_counter()
        dp,reverse=make_solver('123456789',root_split=6,max_abs_exponent=20000,right_inversion_digits=width)
        expr=reverse(0,9,Fraction(10958))
        if expr: verify_expression(expr,'123456789',10958,20000,6)
        rows.append(dict(width=width,seconds=time.perf_counter()-t,status='found' if expr else 'not_found_bounded',dp_cache=dp.cache_info()._asdict()))
        dp.cache_clear();reverse.cache_clear()
    return dict(oracle_queries=queries,measurements=rows,time_budget_seconds=60,memory_budget_mib=768)

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    def expired(*args): raise TimeoutError('60s budget')
    signal.signal(signal.SIGALRM,expired);signal.alarm(60)
    print(json.dumps(run(),indent=2))
