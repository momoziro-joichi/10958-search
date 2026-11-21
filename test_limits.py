from fractions import Fraction
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from resume_search import identity, load, save
from search import make_solver
from test_oracle import tokenizations, expression_trees
from test_search import evaluate


class ExponentLimitTests(unittest.TestCase):
    def test_nondefault_caps_against_oracle(self):
        for limit in (0, 1, 2, 3):
            for chars in itertools.product("0123", repeat=3):
                digits = "".join(chars)
                expected = {v for tokens in tokenizations(digits)
                            for v, _ in expression_trees(tokens, limit)}
                forward, reverse = make_solver(digits, lookup_digits=0,
                                               max_abs_exponent=limit)
                self.assertEqual(set(forward(0, 3)), expected, (digits, limit))
                for target in expected | {Fraction(17, 2)}:
                    expression = reverse(0, 3, target)
                    self.assertEqual(expression is not None, target in expected,
                                     (digits, limit, target))
                    if expression is not None:
                        self.assertEqual(evaluate(expression), target)

    def test_positive_negative_and_zero_boundaries(self):
        for limit in (100, 101):
            reverse = make_solver("2101", root_split=1, max_abs_exponent=limit)[1]
            expression = reverse(0, 4, Fraction(2**101))
            self.assertEqual(expression, "(2^101)" if limit == 101 else None)
        for limit in (1, 2):
            reverse = make_solver("213", root_split=1, max_abs_exponent=limit)[1]
            self.assertEqual(reverse(0, 3, Fraction(1, 4)) is not None, limit == 2)
        self.assertEqual(make_solver("20", max_abs_exponent=0)[1](0, 2, Fraction(1)), "(2^0)")
        for bad in (-1, 1.5, True, None):
            with self.assertRaises(ValueError):
                make_solver("23", max_abs_exponent=bad)

    def test_checkpoint_limit_is_part_of_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = load(path, identity("23", "8", 3))
            save(path, state)
            with self.assertRaises(ValueError):
                load(path, identity("23", "8", 2))

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux resource limits")
    def test_both_clis_propagate_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            for script in ("run_search.py", "resume_search.py"):
                for limit in (2, 3):
                    command = [sys.executable, str(Path(__file__).with_name(script)),
                               "--digits", "23", "--target", "8", "--seconds", "5",
                               "--max-abs-exponent", str(limit)]
                    if script.startswith("resume"):
                        command += ["--checkpoint", str(Path(directory) / f"cap{limit}.json")]
                    r = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    result = json.loads(r.stdout.splitlines()[-1])
                    self.assertEqual(result["status"], "found" if limit == 3 else "not_found_bounded")
                    if script.startswith("run"):
                        self.assertEqual(result["max_abs_exponent"], limit)


if __name__ == "__main__":
    unittest.main()
