"""Run one bounded search in an isolated Linux worker; print a JSON result."""
import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from search import MAX_ABS_EXPONENT


def worker(args):
    import resource
    limit = args.memory_mib * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    from fractions import Fraction
    from search import make_solver
    from verify_expression import verify_expression
    try:
        expression = args.verify_expression
        if expression is None:
            _, search = make_solver(args.digits, root_split=args.split,
                                    max_abs_exponent=args.max_abs_exponent)
            expression = search(0, len(args.digits), Fraction(args.target))
        if expression is not None:
            verify_expression(expression, args.digits, args.target,
                              args.max_abs_exponent, args.split)
        result = {"status": "found" if expression is not None else "not_found_bounded",
                  "expression": expression}
    except (ValueError, RecursionError) as error:
        result = {"status": "worker_error", "expression": None,
                  "error": "Witness verification failed: " + str(error)}
    except MemoryError:
        result = {"status": "memory_limit", "expression": None}
    result["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digits", default="123456789")
    parser.add_argument("--target", default="10958")
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--memory-mib", type=int, default=512)
    parser.add_argument("--split", type=int, help="Only this top-level split (1-based)")
    parser.add_argument("--max-abs-exponent", type=int, default=MAX_ABS_EXPONENT)
    parser.add_argument("--verify-expression", help="Verify this witness without searching")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.max_abs_exponent < 0:
        parser.error("max-abs-exponent must be nonnegative")
    if not sys.platform.startswith("linux"):
        parser.error("Linux is required to enforce the memory budget with RLIMIT_AS")
    if not math.isfinite(args.seconds) or args.seconds <= 0 or args.memory_mib < 64:
        parser.error("seconds must be finite and positive; memory-mib must be >= 64")
    if not args.digits or any(c not in "0123456789" for c in args.digits):
        parser.error("digits must be a nonempty ASCII digit string")
    if args.split is not None and not 1 <= args.split < len(args.digits):
        parser.error("split must be inside the digit string")
    from fractions import Fraction
    try:
        Fraction(args.target)
    except (ValueError, ZeroDivisionError):
        parser.error("target must be an integer or a rational such as 1/4")
    if args.worker:
        worker(args)
        return
    command = [sys.executable, str(Path(__file__).resolve()), "--worker",
               "--digits", args.digits, "--target", args.target,
               "--seconds", str(args.seconds), "--memory-mib", str(args.memory_mib),
               "--max-abs-exponent", str(args.max_abs_exponent)]
    if args.split is not None:
        command += ["--split", str(args.split)]
    if args.verify_expression is not None:
        command += ["--verify-expression", args.verify_expression]
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=args.seconds)
        if completed.returncode:
            result = {"status": "worker_error", "returncode": completed.returncode,
                      "error": completed.stderr[-2000:]}
        else:
            try:
                result = json.loads(completed.stdout)
            except json.JSONDecodeError:
                result = {"status": "worker_error", "error": "Invalid worker JSON"}
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for the worker before raising.
        result = {"status": "timeout", "expression": None}
    result.update(digits=args.digits, target=args.target, root_split=args.split,
                  elapsed_seconds=round(time.perf_counter() - started, 6),
                  time_budget_seconds=args.seconds, memory_budget_mib=args.memory_mib,
                  max_abs_exponent=args.max_abs_exponent)
    print(json.dumps(result, sort_keys=True))
    if result["status"] not in ("found", "not_found_bounded"):
        sys.exit(2)


if __name__ == "__main__":
    main()
