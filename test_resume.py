import argparse
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from resume_search import identity, load, run, save
from search import make_solver
from test_search import evaluate


class PartitionTests(unittest.TestCase):
    def test_partition_union_matches_full_space(self):
        for digits in ("23", "001", "1234"):
            forward, reference = make_solver(digits, lookup_digits=0)
            values = forward(0, len(digits))
            hybrid = make_solver(digits)[1]
            partitions = [make_solver(digits, root_split=k)[1]
                          for k in range(1, len(digits))]
            targets = set(values) | {Fraction(n, 2) for n in range(-10, 11)}
            for target in targets:
                witnesses = [p(0, len(digits), target) for p in partitions]
                self.assertEqual(any(e is not None for e in witnesses), target in values)
                self.assertEqual(reference(0, len(digits), target) is not None,
                                 hybrid(0, len(digits), target) is not None)
                for expression in witnesses:
                    if expression is not None:
                        self.assertEqual(evaluate(expression), target)
                        self.assertEqual("".join(c for c in expression if c.isdigit()), digits)

    def test_invalid_split(self):
        for split in (0, 2):
            with self.assertRaises(ValueError):
                make_solver("23", root_split=split)


class CheckpointTests(unittest.TestCase):
    def args(self, path):
        return argparse.Namespace(digits="23", target="7", seconds=5,
                                  per_split_seconds=1, memory_mib=128, max_abs_exponent=100,
                                  checkpoint=str(path))

    def test_atomic_round_trip_and_version_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            expected = identity("23", "7")
            state = load(path, expected)
            save(path, state)
            self.assertEqual(load(path, expected), state)
            with self.assertRaises(ValueError):
                load(path, identity("23", "8"))
            changed = dict(expected, solver_sha256="changed")
            with self.assertRaises(ValueError):
                load(path, changed)

    def test_incomplete_retried_completed_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.args(Path(directory) / "state.json")
            with patch("resume_search.subprocess.run") as execute:
                execute.return_value.stdout = json.dumps({"status": "timeout"})
                state = run(args)
                self.assertEqual(state["status"], "incomplete")
                execute.return_value.stdout = json.dumps({"status": "not_found_bounded"})
                state = run(args)
                self.assertEqual(state["status"], "not_found_bounded")
                self.assertEqual(state["partitions"]["1"]["attempts"], 2)
                run(args)
                self.assertEqual(execute.call_count, 2)

    def test_real_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.args(Path(directory) / "state.json")
            state = run(args)
            self.assertEqual(state["status"], "not_found_bounded")
            with patch("resume_search.subprocess.run") as execute:
                self.assertEqual(run(args)["status"], "not_found_bounded")
                execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
