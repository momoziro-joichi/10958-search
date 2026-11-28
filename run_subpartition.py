"""Isolated bounded root-subpartition worker, no checkpoint writes."""
import argparse
from fractions import Fraction
from functools import lru_cache
import json
import resource
import signal
import time
import strategy_probe as probe
from structural_subpartition import subtree_partition, expected_subtree_count


def run(tokens, split, op, target, seconds=5):
    if type(seconds) is not int or not 1 <= seconds <= 60:
        raise ValueError('seconds must be integer1..60')
    if not tokens or any(not isinstance(t,str) or not t or any(c not in '0123456789' for c in t) for t in tokens):
        raise ValueError('ASCII digit tokens required')
    expected=expected_subtree_count(len(tokens),split)
    if op not in ('+','-','*','/','^'): raise ValueError('invalid operator')
    target=Fraction(target)
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    def stop(*args): raise TimeoutError
    previous=signal.signal(signal.SIGALRM,stop)
    original=probe.evaluate
    probe.evaluate=lru_cache(maxsize=4096)(original)
    result=dict(status='complete',rejected=0,unresolved=0,candidate=None,
                expected=expected,tokens=tokens,split=split,op=op,target=str(target),
                budget_seconds=seconds,memory_mib=768)
    start=time.perf_counter();signal.alarm(seconds)
    try:
        for tree in subtree_partition(tokens,split,op):
            match=probe.matches_target(tree,target)
            if match is True:
                result.update(status='candidate_unverified',candidate=tree);break
            result['rejected' if match is False else 'unresolved']+=1
    except (TimeoutError,MemoryError) as exc:
        result['status']=type(exc).__name__
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        probe.evaluate.cache_clear();probe.evaluate=original
    if result['status']=='complete':
        result['status']='complete_rejected' if result['rejected']==expected else 'unresolved'
    result.update(seconds=time.perf_counter()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tokens',nargs='+',required=True)
    p.add_argument('--split',type=int,required=True);p.add_argument('--op',required=True)
    p.add_argument('--target',default='10958');p.add_argument('--seconds',type=int,default=5)
    a=p.parse_args();print(json.dumps(run(a.tokens,a.split,a.op,a.target,a.seconds),indent=2))
