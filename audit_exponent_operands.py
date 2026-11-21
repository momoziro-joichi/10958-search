"""Audit short exponent operands only; never claims whole-search completeness."""
import json
import hashlib
from pathlib import Path
import resource
import signal
import time
from fractions import Fraction
from search import make_solver
from verify_expression import verify_expression


def audit(digits='123456789', lower=10000, upper=20000, max_digits=4):
    rows = []
    for start in range(1, len(digits)):
        for end in range(start + 1, min(len(digits), start + max_digits) + 1):
            operand = digits[start:end]
            low_dp, low_reverse = make_solver(operand, max_abs_exponent=lower)
            high_dp, high_reverse = make_solver(operand, max_abs_exponent=upper)
            low = low_dp(0, len(operand))
            high = high_dp(0, len(operand))
            assert low.keys() <= high.keys()
            admitted = {int(v): expr for v, expr in high.items()
                        if v.denominator == 1 and lower < abs(v) <= upper}
            for value, expr in admitted.items():
                verify_expression(expr, operand, Fraction(value), upper)
            rows.append(dict(start=start, end=end, digits=operand,
                lower_value_count=len(low), upper_value_count=len(high),
                newly_reachable_values=len(high.keys() - low.keys()),
                newly_allowed_exponents=[dict(value=v, expression=admitted[v],
                    reachable_under_lower_cap=Fraction(v) in low)
                    for v in sorted(admitted)]))
            low_reverse.cache_clear(); high_reverse.cache_clear()
            low_dp.cache_clear(); high_dp.cache_clear()
    return dict(lower=lower, upper=upper, max_operand_digits=max_digits,
                scope='contiguous proper suffix-of-subexpression operands only', rows=rows)


def main():
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2,) * 2)
    def expired(*args):
        raise TimeoutError('60 second audit budget')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(60)
    started = time.perf_counter()
    cpu = time.process_time()
    result = audit()
    result.update(status='completed', seconds=time.perf_counter()-started,
        cpu_seconds=time.process_time()-cpu,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        time_budget_seconds=60, memory_budget_mib=768,
        source_sha256={name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                       for name in ('search.py', 'audit_exponent_operands.py')})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
