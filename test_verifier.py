from argparse import Namespace
from contextlib import redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from resume_search import run
from search import make_solver
from verify_expression import verify_expression


class WitnessVerifierTests(unittest.TestCase):
    def test_exact_values_and_all_small_witnesses(self):
        for digits, expression, target, cap in (
            ('23', '(2^3)', 8, 3), ('001', '(00+1)', 1, 0),
            ('1234', '((1-23)^4)', 234256, 100),
            ('1234', '(((1/2)-3)^4)', Fraction(625, 16), 100),
            ('213', '(2^(1-3))', Fraction(1, 4), 2),
            ('22000', '(2^2000)', 2**2000, 2000),
        ):
            self.assertEqual(verify_expression(expression, digits, target, cap), target)
        for digits in ('0000', '1234', '12345'):
            forward, _ = make_solver(digits)
            for value, expression in forward(0, len(digits)).items():
                self.assertEqual(verify_expression(expression, digits, value, 100), value)

    def test_reject_invalid_witnesses(self):
        cases = [('23', '(2+3)', 8, 100), ('23', '(3^2)', 9, 100),
                 ('23', '(2^3)', 8, 2), ('00', '(0^0)', 1, 100),
                 ('012', '(0^(1-2))', 0, 100), ('10', '(1/0)', 0, 100),
                 ('212', '(2^(1/2))', 1, 100), ('23', '2+3', 5, 100),
                 ('23', '(2**3)', 8, 100), ('23', '(2|3)', 3, 100),
                 ('23', '(2^3)x', 8, 100), ('23', '(2^3', 8, 100)]
        for digits, expression, target, cap in cases:
            with self.subTest(expression=expression, cap=cap):
                with self.assertRaises(ValueError):
                    verify_expression(expression, digits, target, cap)
        with self.assertRaises(ValueError):
            verify_expression('(12+3)', '123', 15, 100, root_split=1)

    def test_worker_rejects_bad_solver_witness(self):
        from run_search import worker
        args = Namespace(digits='23', target='8', split=1, max_abs_exponent=100,
                         memory_mib=128, verify_expression=None)
        with patch('resource.setrlimit'), patch('search.make_solver',
                return_value=(None, lambda *args: '(2+3)')):
            output = io.StringIO()
            with redirect_stdout(output):
                worker(args)
        self.assertEqual(json.loads(output.getvalue())['status'], 'worker_error')

    def test_cli_verification_and_budget(self):
        for expression, seconds, expected in (
            ('(2^3)', '2', 'found'), ('(2+3)', '2', 'worker_error'),
            ('(2^3)', '0.000001', 'timeout'),
        ):
            result = subprocess.run([sys.executable, 'run_search.py', '--digits', '23',
                '--target', '8', '--verify-expression', expression, '--seconds', seconds,
                '--memory-mib', '128'], capture_output=True, text=True, timeout=5)
            self.assertEqual(json.loads(result.stdout)['status'], expected)
            self.assertEqual(result.returncode, 0 if expected == 'found' else 2)

    def test_resume_rechecks_found_value_without_search(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'checkpoint.json'
            args = Namespace(digits='23', target='8', seconds=2, per_split_seconds=1,
                             max_abs_exponent=100, memory_mib=128, checkpoint=str(path))
            self.assertEqual(run(args)['status'], 'found')
            self.assertEqual(run(args)['status'], 'found')
            state = json.loads(path.read_text())
            state['expression'] = state['partitions']['1']['expression'] = '(2+3)'
            path.write_text(json.dumps(state))
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'Saved witness verification'):
                run(args)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
