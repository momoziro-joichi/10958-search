"""Bounded diagnostic of Fraction power result sizes for partition6."""
import hashlib
import json
from pathlib import Path
import resource
import signal
from fractions import Fraction
from search import make_solver


def measure(cap):
    original = Fraction.__pow__
    calls = total_bits = largest = 0
    def counted(base, exponent):
        nonlocal calls, total_bits, largest
        result = original(base, exponent)
        if isinstance(result, Fraction):
            bits = result.numerator.bit_length() + result.denominator.bit_length()
            calls += 1
            total_bits += bits
            largest = max(largest, bits)
        return result
    Fraction.__pow__ = counted
    try:
        dp, reverse = make_solver('123456789', root_split=6, max_abs_exponent=cap)
        expression = reverse(0, 9, Fraction(10958))
        if expression is not None:
            from verify_expression import verify_expression
            verify_expression(expression, '123456789', 10958, cap, 6)
        return dict(cap=cap, status='found' if expression else 'not_found_bounded',
                    power_calls=calls, cumulative_result_bits=total_bits,
                    largest_result_bits=largest)
    finally:
        Fraction.__pow__ = original


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_AS, (768*1024**2,)*2)
    def expired(*args):
        raise TimeoutError('60 second budget')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(60)
    print(json.dumps(dict(results=[measure(10000), measure(20000)],
        time_budget_seconds=60, memory_budget_mib=768,
        source_sha256=hashlib.sha256(Path('search.py').read_bytes()).hexdigest()), indent=2))
