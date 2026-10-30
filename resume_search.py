"""Checkpoint completed top-level splits; unfinished splits restart on resume."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from search import MAX_ABS_EXPONENT


def identity(digits, target, max_abs_exponent=MAX_ABS_EXPONENT):
    root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in ("search.py", "run_search.py", "resume_search.py"):
        digest.update(name.encode())
        digest.update((root / name).read_bytes())
    return {"schema": 2, "max_abs_exponent": max_abs_exponent, "digits": digits, "target": str(Fraction(target)),
            "solver_sha256": digest.hexdigest()}


def save(path, state):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            json.dump(state, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load(path, expected):
    if not Path(path).exists():
        return {"identity": expected, "partitions": {}}
    state = json.loads(Path(path).read_text())
    if state.get("identity") != expected:
        raise ValueError("Checkpoint input/version mismatch; use a new checkpoint path")
    if not isinstance(state.get("partitions"), dict):
        raise ValueError("Invalid checkpoint partitions")
    return state


def run(args):
    expected = identity(args.digits, args.target, args.max_abs_exponent)
    state = load(args.checkpoint, expected)
    partitions = state["partitions"]
    # Concatenation does not belong to a binary split.
    if Fraction(int(args.digits)) == Fraction(args.target):
        state.update(status="found", expression=args.digits)
        save(args.checkpoint, state)
        return state
    if state.get("status") == "found":
        return state
    deadline = time.monotonic() + args.seconds
    splits = sorted(range(1, len(args.digits)), key=lambda k: (
        partitions.get(str(k), {}).get("attempts", 0),
        abs(2 * k - len(args.digits)), k))
    for split in splits:
        previous = partitions.get(str(split), {})
        if previous.get("status") == "not_found_bounded":
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        budget = min(args.per_split_seconds, remaining)
        command = [sys.executable, str(Path(__file__).with_name("run_search.py")),
                   "--digits", args.digits, "--target", args.target,
                   "--split", str(split), "--seconds", str(budget),
                   "--memory-mib", str(args.memory_mib),
                   "--max-abs-exponent", str(args.max_abs_exponent)]
        # The inner parent owns/kills the worker. Allow cleanup/startup overhead.
        completed = subprocess.run(command, capture_output=True, text=True)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            result = {"status": "worker_error", "error": completed.stderr[-2000:]}
        result["attempts"] = previous.get("attempts", 0) + 1
        partitions[str(split)] = result
        if result["status"] == "found":
            state.update(status="found", expression=result["expression"])
        else:
            state["status"] = "incomplete"
        save(args.checkpoint, state)
        print(json.dumps({"split": split, **result}), flush=True)
        if state["status"] == "found":
            return state
    complete = all(partitions.get(str(k), {}).get("status") == "not_found_bounded"
                   for k in range(1, len(args.digits)))
    state["status"] = "not_found_bounded" if complete else "incomplete"
    save(args.checkpoint, state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digits", default="123456789")
    parser.add_argument("--target", default="10958")
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--per-split-seconds", type=float, default=15)
    parser.add_argument("--memory-mib", type=int, default=512)
    parser.add_argument("--max-abs-exponent", type=int, default=MAX_ABS_EXPONENT)
    parser.add_argument("--checkpoint", default="checkpoint.json")
    args = parser.parse_args()
    if args.max_abs_exponent < 0:
        parser.error("max-abs-exponent must be nonnegative")
    if not sys.platform.startswith("linux"):
        parser.error("Linux required for resource limits and checkpoint locking")
    if any(not math.isfinite(v) or v <= 0 for v in (args.seconds, args.per_split_seconds)):
        parser.error("Time budgets must be finite and positive")
    if args.memory_mib < 64:
        parser.error("memory-mib must be >= 64")
    if not args.digits or any(c not in "0123456789" for c in args.digits):
        parser.error("digits must be nonempty ASCII digits")
    try:
        Fraction(args.target)
    except (ValueError, ZeroDivisionError):
        parser.error("Invalid rational target")
    import fcntl
    with open(args.checkpoint + ".lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Checkpoint is in use by another process")
        try:
            state = run(args)
        except (ValueError, OSError) as error:
            parser.error(str(error))
    print(json.dumps({"status": state["status"], "checkpoint": args.checkpoint}))
    if state["status"] == "incomplete":
        sys.exit(2)


if __name__ == "__main__":
    main()
