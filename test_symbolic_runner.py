import contextlib
import io
import json
import unittest
from unittest.mock import patch
import classify_symbolic as runner


class RunnerTests(unittest.TestCase):
    def run_case(self, trees):
        out=io.StringIO()
        with patch('sys.argv',['classify_symbolic.py','--digits','12','--cache-size','64']), \
             patch.object(runner.resource,'setrlimit'), \
             patch.object(runner.signal,'signal'), \
             patch.object(runner.signal,'alarm'), \
             patch.object(runner,'all_trees',return_value=trees), \
             contextlib.redirect_stdout(out):
            runner.main()
        self.assertIs(runner.probe.evaluate, runner.evaluate)
        result=json.loads(out.getvalue())
        self.assertLessEqual(result["cache_info"]["currsize"],64)
        return result

    def test_complete(self):
        r=self.run_case(iter(['12']))
        self.assertEqual(r['status'],'complete')
        self.assertEqual(r['counts']['reject'],1)

    def test_interruption_preserves_partial_counts(self):
        for error,status in [(TimeoutError,'timeout'),(MemoryError,'memory_limit')]:
            def trees():
                yield '12'
                raise error
            r=self.run_case(trees())
            self.assertEqual(r['status'],status)
            self.assertEqual(r['counts']['reject'],1)

    def test_sample_storage_is_bounded(self):
        with patch.object(runner,'matches_target',return_value=None):
            r=self.run_case(iter(['12']*105))
        self.assertEqual(r['status'],'unresolved')
        self.assertTrue(r['enumeration_complete'])
        self.assertEqual(r['counts']['unresolved'],105)
        self.assertEqual(len(r['unresolved_tree_samples']),100)


if __name__=='__main__':
    unittest.main()
