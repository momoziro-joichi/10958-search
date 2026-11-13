"""Isolated width comparison, 30s/768MiB per child, eight splits."""
import json
import subprocess
import sys
import resource
import time
from fractions import Fraction
from search import make_solver
from verify_expression import verify_expression

if len(sys.argv)>1:
    width,split=map(int,sys.argv[1:])
    resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
    t=time.perf_counter()
    dp,reverse=make_solver('123456789',root_split=split,max_abs_exponent=20000,right_inversion_digits=width)
    expr=reverse(0,9,Fraction(10958))
    if expr: verify_expression(expr,'123456789',10958,20000,split)
    print(json.dumps(dict(width=width,split=split,seconds=time.perf_counter()-t,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        status='found' if expr else 'not_found_bounded')))
else:
    rows=[]
    for split in range(1,9):
        for width in (2,3):
            p=subprocess.run([sys.executable,__file__,str(width),str(split)],capture_output=True,text=True,timeout=30)
            if p.returncode: raise RuntimeError(p.stderr)
            rows.append(json.loads(p.stdout))
    print(json.dumps(dict(cap=20000,child_seconds=30,memory_mib=768,total_budget_seconds=480,rows=rows),indent=2))
