import json
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux resource limits")
class RunnerTests(unittest.TestCase):
    def run_case(self, *args):
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run_search.py")), *args],
            capture_output=True, text=True, timeout=10,
        )

    def test_found(self):
        result = self.run_case("--digits", "23", "--target", "8", "--seconds", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "found")
        self.assertEqual(data["expression"], "(2^3)")
        self.assertEqual(data["max_abs_exponent"], 100)

    def test_bounded_not_found(self):
        result = self.run_case("--digits", "23", "--target", "7", "--seconds", "5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "not_found_bounded")

    def test_timeout_is_not_not_found(self):
        result = self.run_case("--seconds", "0.000001")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "timeout")

    def test_invalid_budgets_and_target(self):
        for args in [("--seconds", "nan"), ("--memory-mib", "0"),
                     ("--target", "1/0"), ("--digits", "abc")]:
            result = self.run_case(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
