import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from resume_search import identity, load, run, save


class RecordValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'state.json'
        self.expected = identity('23', '7')
        self.record = dict(status='not_found_bounded', expression=None, attempts=1,
                           digits='23', target='7', root_split=1, max_abs_exponent=100,
                           elapsed_seconds=0.1, time_budget_seconds=1, memory_budget_mib=128)
        self.state = dict(identity=self.expected, partitions={'1': self.record},
                          status='not_found_bounded')

    def check_rejected(self, state):
        save(self.path, state)
        with self.assertRaises(ValueError):
            load(self.path, self.expected)

    def test_missing_fields_and_bad_record_types(self):
        for key in self.record:
            state = copy.deepcopy(self.state)
            del state['partitions']['1'][key]
            self.check_rejected(state)
        for bad in (None, [], 'done', 1):
            self.check_rejected(dict(self.state, partitions={'1': bad}))
        for key, bad in (('attempts', True), ('attempts', 0), ('root_split', True),
                         ('max_abs_exponent', 200), ('digits', '32'), ('target', '8'),
                         ('status', 'done'), ('elapsed_seconds', float('nan')),
                         ('time_budget_seconds', 0), ('memory_budget_mib', 0),
                         ('expression', '(2+3)')):
            state = copy.deepcopy(self.state)
            state['partitions']['1'][key] = bad
            self.check_rejected(state)

    def test_top_level_consistency_and_duplicate_keys(self):
        for key in ('0', '2', '01'):
            self.check_rejected(dict(self.state, partitions={key: self.record}))
        self.check_rejected(dict(self.state, partitions={}))
        self.check_rejected(dict(self.state, status='found', expression='(2+3)'))
        self.check_rejected(dict(self.state, status='unknown'))
        self.check_rejected([])
        save(self.path, self.state)
        self.path.write_text(self.path.read_text().replace('"attempts": 1', '"attempts": 1, "attempts": 2'))
        with self.assertRaises(ValueError):
            load(self.path, self.expected)

    def test_completed_and_interrupted_round_trips(self):
        for status in ('not_found_bounded', 'incomplete'):
            state = dict(self.state, status=status)
            save(self.path, state)
            self.assertEqual(load(self.path, self.expected), state)
        # A crash after saving the last partition but before finalizing the
        # aggregate status must not force completed partitions to run again.
        args = argparse.Namespace(digits='23', target='7', max_abs_exponent=100,
                                  seconds=1, per_split_seconds=1, memory_mib=128,
                                  checkpoint=str(self.path))
        with patch('resume_search.subprocess.run') as execute:
            self.assertEqual(run(args)['status'], 'not_found_bounded')
            execute.assert_not_called()

    def test_found_records_and_canonical_target(self):
        expected = identity('23', '8')
        record = dict(self.record, target='8', status='found', expression='(2^3)')
        state = dict(identity=expected, partitions={'1': record},
                     status='found', expression='(2^3)')
        save(self.path, state)
        self.assertEqual(load(self.path, expected), state)
        for change in ({'expression': None}, {'expression': '(3^2)'},
                       {'status': 'not_found_bounded'}):
            broken = copy.deepcopy(state)
            broken['partitions']['1'].update(change)
            save(self.path, broken)
            with self.assertRaises(ValueError):
                load(self.path, expected)
        self.path.unlink()
        args = argparse.Namespace(digits='23', target='14/2', max_abs_exponent=100,
                                  seconds=2, per_split_seconds=1, memory_mib=128,
                                  checkpoint=str(self.path))
        result = run(args)
        self.assertEqual(result['status'], 'not_found_bounded')
        self.assertEqual(result['partitions']['1']['target'], '7')
        self.assertEqual(load(self.path, self.expected), result)

    def test_invalid_worker_output_is_retryable_error(self):
        args = argparse.Namespace(digits='23', target='7', max_abs_exponent=100,
                                  seconds=1, per_split_seconds=1, memory_mib=128,
                                  checkpoint=str(self.path))
        for output, returncode in (('[]', 0), ('bad json', 0),
                                  ('{"status":"not_found_bounded"}', 0),
                                  (json.dumps(self.record), 2)):
            self.path.unlink(missing_ok=True)
            with patch('resume_search.subprocess.run') as execute:
                execute.return_value.stdout = output
                execute.return_value.returncode = returncode
                state = run(args)
            self.assertEqual(state['status'], 'incomplete')
            self.assertEqual(state['partitions']['1']['status'], 'worker_error')
            self.assertEqual(load(self.path, self.expected), state)


if __name__ == '__main__':
    unittest.main()
