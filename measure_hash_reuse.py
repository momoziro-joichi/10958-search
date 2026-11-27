"""Bounded reuse measurement for Fraction hashes at short lookup sites."""
import json
import resource
import signal
import sys
from collections import OrderedDict
from fractions import Fraction
import search

resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
def expired(*args): raise TimeoutError('30s budget')
signal.signal(signal.SIGALRM,expired)
signal.alarm(30)
original=Fraction.__hash__
recent=OrderedDict()
counts=dict(short_lookup_calls=0,recent_value_hits=0,large_bypasses=0)
def measured(value):
    frame=sys._getframe(1)
    try:
        if (frame.f_code.co_name=='can_make' and frame.f_code.co_filename==search.__file__
            and frame.f_locals['j']-frame.f_locals['i']<=frame.f_locals['lookup_digits']
            and not frame.f_locals['restricted_root']):
            counts['short_lookup_calls']+=1
            n,d=value.numerator,value.denominator
            if n.bit_length()+d.bit_length()<=256:
                key=(n,d)
                if key in recent:
                    counts['recent_value_hits']+=1
                    recent.move_to_end(key)
                else:
                    recent[key]=None
                    if len(recent)>1024:recent.popitem(last=False)
            else:counts['large_bypasses']+=1
    finally:del frame
    return original(value)
Fraction.__hash__=measured
try:
    result=search.make_solver('123456789',root_split=1,max_abs_exponent=5000)[1](0,9,Fraction(10958))
    assert result is None
    print(json.dumps(dict(status='not_found_bounded',split=1,cap=5000,
        counts=counts,recent_capacity=1024,input_bits=256,
        memory_budget_mib=768,time_budget_seconds=30)))
finally:
    Fraction.__hash__=original
    signal.alarm(0)
