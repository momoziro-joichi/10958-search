"""Observe completed DP tables without retaining them or changing solver code."""
import json
import resource
import signal
import sys
import time
from fractions import Fraction
import search


def measure(cap):
    rows = []
    def observe(frame, event, value):
        if event == 'return' and frame.f_code.co_name == 'full_dp' and frame.f_code.co_filename == search.__file__ and isinstance(value, dict):
            largest = max(value, key=lambda v: v.numerator.bit_length()+v.denominator.bit_length())
            rows.append(dict(i=frame.f_locals['i'], j=frame.f_locals['j'], entries=len(value),
                integer_bytes=sum(sys.getsizeof(v.numerator)+sys.getsizeof(v.denominator) for v in value),
                largest_bits=largest.numerator.bit_length()+largest.denominator.bit_length(),
                largest_expression=value[largest]))
    previous = sys.getprofile()
    started = time.perf_counter()
    try:
        sys.setprofile(observe)
        dp, reverse = search.make_solver('123456789',root_split=6,max_abs_exponent=cap)
        expression = reverse(0,9,Fraction(10958))
    finally:
        sys.setprofile(previous)
    return dict(cap=cap,status='found' if expression else 'not_found_bounded',
                seconds=time.perf_counter()-started,
                rows=sorted(rows,key=lambda r:r['integer_bytes'],reverse=True))


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    def expired(*args): raise TimeoutError('60s budget')
    signal.signal(signal.SIGALRM,expired);signal.alarm(60)
    print(json.dumps(dict(results=[measure(10000),measure(20000)],
        memory_budget_mib=768,time_budget_seconds=60),indent=2))
