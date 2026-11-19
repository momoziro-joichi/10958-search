import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import structural_resume as runner


class ResumeTests(unittest.TestCase):
    def test_real_completion_and_skip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'checkpoint.json'
            result = runner.run('123', '10958', p, 10, 2)
            self.assertEqual(result['completed_masks'], 4)
            before = p.read_bytes()
            with patch.object(runner.subprocess, 'run', side_effect=AssertionError('must skip')):
                self.assertEqual(runner.run('123', '10958', p, 10, 2)['skipped_masks'], 4)
            self.assertEqual(before, p.read_bytes())
            with self.assertRaises(ValueError):
                runner.run('123', '10959', p, 10, 2)

    def test_incomplete_does_not_save(self):
        for result in (dict(counts={'rejected': 0, 'unresolved': 1}, candidate=None),
                       dict(counts={'rejected': 0, 'unresolved': 0}, candidate='1')):
            with tempfile.TemporaryDirectory() as d:
                p = Path(d)/'checkpoint.json'
                proc = subprocess.CompletedProcess([], 0, json.dumps(result))
                with patch.object(runner.subprocess, 'run', return_value=proc):
                    self.assertEqual(runner.run('1', '2', p, 2, 1)['completed_masks'], 0)
                self.assertFalse(p.exists())

    def test_timeout_preserves_completed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'checkpoint.json'
            ok = subprocess.CompletedProcess([], 0, json.dumps(dict(
                counts={'rejected': 1, 'unresolved': 0}, candidate=None)))
            with patch.object(runner.subprocess, 'run', side_effect=[ok, subprocess.TimeoutExpired('x', 1)]):
                result = runner.run('12', '10958', p, 2, 1)
            self.assertEqual(result['completed_masks'], 1)
            self.assertEqual(result['attempts'][-1]['status'], 'timeout')
            self.assertEqual(list(json.loads(p.read_text())['completed']), ['0'])

    def test_actual_candidate(self):
        result = runner.worker('23', '8', 1)
        self.assertEqual(result['candidate'], ('^', '2', '3'))


if __name__ == '__main__':
    unittest.main()
