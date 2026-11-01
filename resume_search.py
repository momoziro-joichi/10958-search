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
    for name in ("search.py", "run_search.py", "resume_search.py", "verify_expression.py"):
        digest.update(name.encode())
        digest.update((root / name).read_bytes())
    return {"schema": 3, "max_abs_exponent": max_abs_exponent, "digits": digits, "target": str(Fraction(target)),
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


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def validate_record(record, expected, split):
    if not isinstance(record, dict):
        raise ValueError("Invalid partition record")
    for key in ("digits", "target", "max_abs_exponent"):
        if type(record.get(key)) is not type(expected[key]) or record[key] != expected[key]:
            raise ValueError("Partition input mismatch: " + key)
    if type(record.get("root_split")) is not int or record["root_split"] != split:
        raise ValueError("Partition split mismatch")
    if type(record.get("attempts")) is not int or record["attempts"] < 1:
        raise ValueError("Invalid partition attempts")
    status = record.get("status")
    if status not in ("found", "not_found_bounded", "timeout", "memory_limit", "worker_error"):
        raise ValueError("Invalid partition status")
    for key in ("elapsed_seconds", "time_budget_seconds"):
        value = record.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid partition timing: " + key)
    if record["time_budget_seconds"] <= 0:
        raise ValueError("Invalid time budget")
    if type(record.get("memory_budget_mib")) is not int or record["memory_budget_mib"] < 64:
        raise ValueError("Invalid memory budget")
    if "max_rss_kib" in record:
        if type(record["max_rss_kib"]) is not int or record["max_rss_kib"] < 0:
            raise ValueError("Invalid RSS")
    expression = record.get("expression")
    if status == "found":
        if not isinstance(expression, str) or not expression:
            raise ValueError("Missing found expression")
        if "".join(c for c in expression if c in "0123456789") != expected["digits"]:
            raise ValueError("Found expression digit mismatch")
    elif expression is not None:
        raise ValueError("Unexpected expression for non-found result")
    if status == "not_found_bounded" and "expression" not in record:
        raise ValueError("Missing completed result expression field")


def load(path, expected):
    if not Path(path).exists():
        return {"identity": expected, "partitions": {}}
    state = json.loads(Path(path).read_text(), object_pairs_hook=unique_object)
    if not isinstance(state, dict) or state.get("identity") != expected:
        raise ValueError("Checkpoint input/version mismatch; use a new checkpoint path")
    if any(type(state["identity"].get(k)) is not type(v) for k, v in expected.items()):
        raise ValueError("Invalid checkpoint identity types")
    partitions = state.get("partitions")
    if not isinstance(partitions, dict):
        raise ValueError("Invalid checkpoint partitions")
    allowed = {str(k) for k in range(1, len(expected["digits"]))}
    if not partitions.keys() <= allowed:
        raise ValueError("Invalid checkpoint split keys")
    for key, record in partitions.items():
        validate_record(record, expected, int(key))
    status = state.get("status")
    if status not in (None, "found", "not_found_bounded", "incomplete"):
        raise ValueError("Invalid checkpoint status")
    if status is None and partitions:
        raise ValueError("Missing checkpoint status")
    found = [r["expression"] for r in partitions.values() if r["status"] == "found"]
    if status == "found":
        expression = state.get("expression")
        concat = (expression == expected["digits"] and
                  Fraction(int(expected["digits"])) == Fraction(expected["target"]))
        if not concat and expression not in found:
            raise ValueError("Found status lacks matching partition expression")
    elif found or state.get("expression") is not None:
        raise ValueError("Contradictory checkpoint expression/status")
    if status == "not_found_bounded":
        if set(partitions) != allowed or any(r["status"] != "not_found_bounded" for r in partitions.values()):
            raise ValueError("Incomplete partitions marked complete")
        if Fraction(int(expected["digits"])) == Fraction(expected["target"]):
            raise ValueError("Negative result contradicts concatenation")
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
        # Recheck saved witnesses in the same resource-limited worker. A
        # checkpoint flag is not evidence that the expression is valid.
        command = [sys.executable, str(Path(__file__).with_name("run_search.py")),
                   "--digits", args.digits, "--target", expected["target"],
                   "--max-abs-exponent", str(args.max_abs_exponent),
                   "--seconds", str(args.seconds), "--memory-mib", str(args.memory_mib),
                   "--verify-expression", state["expression"]]
        checked = subprocess.run(command, capture_output=True, text=True)
        try:
            result = json.loads(checked.stdout)
        except ValueError as error:
            raise ValueError("Saved witness verification produced invalid output") from error
        if checked.returncode or not isinstance(result, dict) or result.get("status") != "found":
            raise ValueError("Saved witness verification failed or exceeded its budget")
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
                   "--digits", args.digits, "--target", expected["target"],
                   "--split", str(split), "--seconds", str(budget),
                   "--memory-mib", str(args.memory_mib),
                   "--max-abs-exponent", str(args.max_abs_exponent)]
        # The inner parent owns/kills the worker. Allow cleanup/startup overhead.
        started = time.monotonic()
        completed = subprocess.run(command, capture_output=True, text=True)
        attempts = previous.get("attempts", 0) + 1
        try:
            result = json.loads(completed.stdout, object_pairs_hook=unique_object)
            if not isinstance(result, dict):
                raise ValueError("Worker result is not an object")
            result["attempts"] = attempts
            validate_record(result, expected, split)
            expected_exit = 0 if result["status"] in ("found", "not_found_bounded") else 2
            if completed.returncode != expected_exit:
                raise ValueError("Worker status/exit-code mismatch")
        except ValueError as error:
            # Invalid output must never become a reusable negative result.
            result = {"status": "worker_error", "error": str(error),
                      "expression": None, "attempts": attempts,
                      "digits": args.digits, "target": expected["target"],
                      "max_abs_exponent": args.max_abs_exponent, "root_split": split,
                      "elapsed_seconds": round(time.monotonic() - started, 6),
                      "time_budget_seconds": budget,
                      "memory_budget_mib": args.memory_mib}
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
