import json
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux resource limits')
class ProfileTests(unittest.TestCase):
    def execute(self, *options):
        return subprocess.run([sys.executable, str(Path(__file__).with_name('profile_search.py')),
                               '--digits', '23', '--split', '1', '--seconds', '3',
                               '--memory-mib', '128', *options],
                              capture_output=True, text=True, timeout=6)

    def test_completed_profiles_and_canonical_target(self):
        for target, expected in (('16/2', 'found'), ('7', 'not_found_bounded')):
            process = self.execute('--target', target, '--max-abs-exponent', '3')
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result['status'], expected)
            self.assertGreater(result['total_calls'], 0)
            self.assertTrue(result['functions'])
            self.assertIn('search.py', result['source_sha256'])
            self.assertTrue(result['profile_includes_overhead'])
            self.assertEqual(result['target'], '8' if expected == 'found' else '7')
            if expected == 'found':
                self.assertEqual(result['expression'], '(2^3)')

    def test_timeout_is_incomplete_not_bounded_absence(self):
        process = self.execute('--seconds', '0.000001')
        self.assertEqual(process.returncode, 2)
        result = json.loads(process.stdout)
        self.assertEqual(result['status'], 'timeout')
        self.assertNotIn('functions', result)

    def test_invalid_arguments(self):
        for options in (('--seconds', 'nan'), ('--memory-mib', '0'),
                        ('--split', '0'), ('--max-abs-exponent', '-1')):
            process = self.execute(*options)
            self.assertEqual(process.returncode, 2)
            self.assertIn('error:', process.stderr)


if __name__ == '__main__':
    unittest.main()
